from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import inspect

import goldswingtraderai.decisions.fusion as fusion_module
import goldswingtraderai.decisions.opportunity as opportunity_module
import goldswingtraderai.decisions.timing as timing_module
import goldswingtraderai.strategies.floor as strategy_module
from goldswingtraderai.decisions import (
    TimingAction,
    evaluate_entry_timing,
    fuse_decision,
    update_opportunity,
)
from goldswingtraderai.domain.enums import (
    AccountMode,
    DataQuality,
    ExtensionState,
    OpportunityStage,
    StrategyFamily,
    Timeframe,
)
from goldswingtraderai.domain.ids import new_snapshot_id
from goldswingtraderai.domain.market import (
    AccountFacts,
    Candle,
    CandleSeries,
    MarketSnapshot,
    Quote,
    SymbolSpec,
)
from goldswingtraderai.domain.models import MarketSnapshotMeta
from goldswingtraderai.intelligence.snapshot import (
    IntelligenceSnapshot,
    build_intelligence_snapshot,
)
from goldswingtraderai.strategies import (
    DirectionalFamilyCase,
    FamilyReport,
    StrategyFloorReport,
    evaluate_strategy_floor,
)


def _candles(end_utc: datetime, timeframe: Timeframe, count: int = 70) -> tuple[Candle, ...]:
    seconds = {
        Timeframe.H4: 14_400,
        Timeframe.H1: 3_600,
        Timeframe.M15: 900,
        Timeframe.M5: 300,
    }[timeframe]
    output: list[Candle] = []
    for index in range(count):
        when = end_utc - timedelta(seconds=seconds * (count - index))
        base = 3600.0 + index * 0.35
        pulse = (1.2, 0.5, -0.6, 0.8, -0.3)[index % 5]
        close = base + pulse
        output.append(
            Candle(
                time_utc=when,
                open=base,
                high=max(base, close) + 1.2,
                low=min(base, close) - 1.2,
                close=close,
                tick_volume=100 + index,
                spread_points=20,
            )
        )
    return tuple(output)


def _intelligence(as_of: datetime) -> IntelligenceSnapshot:
    timeframes = (Timeframe.H4, Timeframe.H1, Timeframe.M15, Timeframe.M5)
    series = tuple(
        CandleSeries(timeframe=timeframe, candles=_candles(as_of, timeframe))
        for timeframe in timeframes
    )
    market = MarketSnapshot(
        meta=MarketSnapshotMeta(
            snapshot_id=new_snapshot_id(),
            symbol="XAUUSDm",
            as_of_utc=as_of,
            timeframes=timeframes,
            data_complete=True,
        ),
        account=AccountFacts(
            login=123456,
            server="Broker-Demo",
            currency="USD",
            mode=AccountMode.DEMO,
            balance=100.0,
            equity=101.0,
            margin=5.0,
            margin_free=96.0,
            leverage=500,
        ),
        symbol_spec=SymbolSpec(
            symbol="XAUUSDm",
            digits=3,
            point=0.001,
            tick_size=0.001,
            tick_value=0.1,
            contract_size=100.0,
            volume_min=0.01,
            volume_max=200.0,
            volume_step=0.01,
            stops_level_points=0,
            freeze_level_points=0,
        ),
        quote=Quote(
            symbol="XAUUSDm",
            bid=3624.0,
            ask=3624.2,
            time_utc=as_of,
        ),
        series=series,
        quality=DataQuality.HEALTHY,
    )
    return build_intelligence_snapshot(market)


def _case(score: float, evidence: tuple[str, ...] = ()) -> DirectionalFamilyCase:
    return DirectionalFamilyCase(
        score=score,
        coverage=1.0,
        evidence=evidence,
        conflicts=(),
        structural_target=None,
        expansion_potential=0.8,
    )


def _floor(buy: float, sell: float) -> StrategyFloorReport:
    reports = tuple(
        FamilyReport(
            family=family,
            buy=_case(buy, ("STRUCTURE", "LOCATION")),
            sell=_case(sell, ("STRUCTURE", "LOCATION")),
            preferred_timing_profile="TEST",
        )
        for family in StrategyFamily
    )
    return StrategyFloorReport(families=reports)


def test_all_six_strategy_families_run_from_same_snapshot() -> None:
    intel = _intelligence(datetime(2026, 7, 1, 12, 30, tzinfo=timezone.utc))
    floor = evaluate_strategy_floor(intel)

    assert tuple(report.family for report in floor.families) == tuple(StrategyFamily)
    assert len(floor.families) == 6
    for report in floor.families:
        assert 0 <= report.buy.score <= 100
        assert 0 <= report.sell.score <= 100
        assert 0 <= report.buy.coverage <= 1
        assert 0 <= report.sell.coverage <= 1


def test_fusion_keeps_strong_opposition_visible_as_conflict() -> None:
    intel = _intelligence(datetime(2026, 7, 1, 12, 30, tzinfo=timezone.utc))
    conflicted = fuse_decision(_floor(88.0, 84.0), intel)
    clear = fuse_decision(_floor(88.0, 25.0), intel)

    assert conflicted.buy.score > conflicted.sell.score
    assert conflicted.conflict_score > clear.conflict_score
    assert "STRONG_OPPOSING_THESIS" in conflicted.red_team_objections
    assert "STRONG_OPPOSING_THESIS" not in clear.red_team_objections
    assert clear.directional_edge > conflicted.directional_edge


def test_severe_extension_waits_without_deleting_opportunity_identity() -> None:
    now = datetime(2026, 7, 1, 12, 30, tzinfo=timezone.utc)
    intel = _intelligence(now)
    board = fuse_decision(_floor(88.0, 25.0), intel)
    opportunity = update_opportunity(board, now)
    assert opportunity is not None
    assert opportunity.stage is OpportunityStage.ARMED

    frames = list(intel.frames)
    m5_index = next(index for index, frame in enumerate(frames) if frame.timeframe is Timeframe.M5)
    m5 = frames[m5_index]
    frames[m5_index] = replace(
        m5,
        quant=replace(m5.quant, extension_state=ExtensionState.SEVERELY_EXTENDED),
    )
    extended = replace(intel, frames=tuple(frames))

    waited = evaluate_entry_timing(opportunity, board, extended, now + timedelta(minutes=5))
    assert waited.action is TimingAction.WAIT
    assert waited.opportunity.stage is OpportunityStage.WAITING
    assert waited.opportunity.opportunity_id == opportunity.opportunity_id
    assert waited.opportunity.episode_id == opportunity.episode_id

    missed = evaluate_entry_timing(
        waited.opportunity,
        board,
        extended,
        now + timedelta(minutes=61),
    )
    assert missed.action is TimingAction.MISSED
    assert missed.opportunity.stage is OpportunityStage.MISSED
    assert missed.opportunity.opportunity_id == opportunity.opportunity_id


def test_strategy_and_decision_modules_have_no_broker_write_boundary() -> None:
    modules = (strategy_module, fusion_module, opportunity_module, timing_module)
    source = "\n".join(inspect.getsource(module) for module in modules)

    assert "order_send" not in source
    assert "MetaTrader5" not in source
