from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from goldswingtraderai.decisions.trade_plan import PlanTarget, TargetRole
from goldswingtraderai.domain.enums import (
    CandleSequenceState,
    Direction,
    MomentumPhase,
    StructureState,
    Timeframe,
    TradeManagerAction,
)
from goldswingtraderai.domain.ids import new_episode_id, new_opportunity_id, new_trade_id, new_trade_plan_id
from goldswingtraderai.domain.market import Quote
from goldswingtraderai.intelligence.liquidity import LiquidityPath
from goldswingtraderai.management import (
    ManagedTrade,
    ManagedTradeRepository,
    ObjectiveStage,
    TradeManagementDecision,
    apply_management_decision,
    evaluate_trade_manager,
)
from goldswingtraderai.persistence import StateStore


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
SYMBOL = "XAUUSDm"


class FakeIntelligence:
    def __init__(self, frames):
        self.frames = frames

    def for_timeframe(self, timeframe):
        if timeframe not in self.frames:
            raise KeyError(timeframe)
        return self.frames[timeframe]


def _target(role: TargetRole, price: float, rr: float) -> PlanTarget:
    return PlanTarget(role=role, price=price, quality=80.0, source=f"TEST:{role.value}", rr=rr)


def _trade(*, runner: bool = True, current_stop: float = 90.0) -> ManagedTrade:
    return ManagedTrade(
        trade_id=new_trade_id(),
        position_ticket=7001,
        plan_id=new_trade_plan_id(),
        opportunity_id=new_opportunity_id(),
        episode_id=new_episode_id(),
        symbol=SYMBOL,
        direction=Direction.BUY,
        volume=0.01,
        entry_price=100.0,
        original_stop=90.0,
        original_r_price=10.0,
        current_stop=current_stop,
        broker_tp=120.0,
        primary_target=_target(TargetRole.PRIMARY, 110.0, 1.0),
        expansion_target=_target(TargetRole.EXPANSION, 120.0, 2.0),
        runner_candidate=_target(TargetRole.RUNNER, 130.0, 3.0) if runner else None,
        active_runner_target=None,
        objective_stage=ObjectiveStage.EXPANSION,
        opened_at_utc=NOW,
        updated_at_utc=NOW,
    )


def _frame(
    timeframe: Timeframe,
    *,
    bullish: bool = True,
    latest_direction: Direction | None = None,
    protected_low: float | None = None,
    protected_high: float | None = None,
    path: LiquidityPath = LiquidityPath.OPEN,
):
    direction = Direction.BUY if bullish else Direction.SELL
    state = StructureState.BULLISH if bullish else StructureState.BEARISH
    sequence = CandleSequenceState.BULL_EXPANSION if bullish else CandleSequenceState.BEAR_EXPANSION
    latest = latest_direction or direction
    return SimpleNamespace(
        timeframe=timeframe,
        structure=SimpleNamespace(
            state=state,
            sequence=sequence,
            latest_candle=SimpleNamespace(direction=latest),
            protected_low=None if protected_low is None else SimpleNamespace(price=protected_low),
            protected_high=None if protected_high is None else SimpleNamespace(price=protected_high),
            bull_evidence=85.0 if bullish else 15.0,
            bear_evidence=15.0 if bullish else 85.0,
        ),
        quant=SimpleNamespace(
            trend_support=direction,
            momentum_phase=MomentumPhase.EXPANDING,
            atr=2.0,
        ),
        liquidity=SimpleNamespace(
            path_up=path if bullish else LiquidityPath.CROWDED,
            path_down=LiquidityPath.CROWDED if bullish else path,
        ),
    )


def _intelligence(*, bullish: bool = True, latest_m5: Direction | None = None):
    return FakeIntelligence(
        {
            Timeframe.H4: _frame(Timeframe.H4, bullish=bullish),
            Timeframe.H1: _frame(
                Timeframe.H1,
                bullish=bullish,
                protected_low=98.0 if bullish else None,
                protected_high=122.0 if not bullish else None,
            ),
            Timeframe.M15: _frame(
                Timeframe.M15,
                bullish=bullish,
                protected_low=102.0 if bullish else None,
                protected_high=118.0 if not bullish else None,
            ),
            Timeframe.M5: _frame(
                Timeframe.M5,
                bullish=bullish,
                latest_direction=latest_m5,
                protected_low=103.0 if bullish else None,
                protected_high=117.0 if not bullish else None,
            ),
        }
    )


def _market(bid: float, ask: float | None = None):
    return SimpleNamespace(
        meta=SimpleNamespace(symbol=SYMBOL),
        quote=Quote(symbol=SYMBOL, bid=bid, ask=ask or bid + 0.2, time_utc=NOW),
    )


def test_ordinary_pullback_does_not_force_exit_or_breakeven() -> None:
    decision = evaluate_trade_manager(
        _trade(),
        _market(104.0),
        _intelligence(bullish=True, latest_m5=Direction.SELL),
    )

    assert decision.action is TradeManagerAction.HOLD
    assert decision.proposed_stop is None
    assert decision.current_r == pytest.approx(0.4)


def test_structural_progress_earns_protection_without_fixed_breakeven_rule() -> None:
    decision = evaluate_trade_manager(_trade(), _market(107.0), _intelligence())

    assert decision.action is TradeManagerAction.PROTECT
    assert decision.proposed_stop is not None
    assert decision.proposed_stop > 90.0
    assert decision.proposed_stop != pytest.approx(100.0)


def test_primary_target_is_checkpoint_not_automatic_exit() -> None:
    decision = evaluate_trade_manager(_trade(), _market(110.5), _intelligence())

    assert decision.action is TradeManagerAction.TRAIL
    assert decision.reason == "STRUCTURAL_TRAIL_EARNED"
    assert decision.proposed_stop is not None


def test_runner_requires_continuation_and_objective_not_profit_alone() -> None:
    earned = evaluate_trade_manager(_trade(), _market(118.5), _intelligence())
    no_objective = evaluate_trade_manager(_trade(runner=False), _market(118.5), _intelligence())

    assert earned.action is TradeManagerAction.RUNNER
    assert earned.proposed_tp == pytest.approx(130.0)
    assert no_objective.action is not TradeManagerAction.RUNNER


def test_strong_opposing_structure_can_exit_thesis() -> None:
    decision = evaluate_trade_manager(_trade(), _market(106.0), _intelligence(bullish=False))

    assert decision.action is TradeManagerAction.EXIT
    assert decision.reason == "THESIS_REVERSAL_CONFIRMED"


def test_pre_close_flatten_overrides_healthy_runner() -> None:
    decision = evaluate_trade_manager(
        _trade(),
        _market(118.5),
        _intelligence(),
        pre_close_flatten=True,
    )

    assert decision.action is TradeManagerAction.EXIT
    assert decision.reason == "PRE_CLOSE_FLATTEN"


def test_stop_cannot_widen_beyond_original_risk() -> None:
    with pytest.raises(ValueError, match="may not widen"):
        _trade(current_stop=89.0)

    trade = _trade(current_stop=95.0)
    decision = TradeManagementDecision(
        action=TradeManagerAction.TRAIL,
        current_r=1.5,
        continuation_score=80.0,
        reversal_score=20.0,
        structure_integrity=80.0,
        path_quality=80.0,
        objective_stage=ObjectiveStage.EXPANSION,
        proposed_stop=93.0,
        proposed_tp=None,
        reason="TEST",
    )
    updated = apply_management_decision(trade, decision, NOW)
    assert updated.current_stop == pytest.approx(95.0)


def test_runner_update_activates_only_verified_candidate() -> None:
    trade = _trade()
    decision = evaluate_trade_manager(trade, _market(118.5), _intelligence())
    updated = apply_management_decision(trade, decision, NOW)

    assert updated.objective_stage is ObjectiveStage.RUNNER
    assert updated.active_runner_target == trade.runner_candidate
    assert updated.broker_tp == pytest.approx(130.0)
    assert updated.original_r_price == trade.original_r_price


def test_managed_trade_roundtrip_preserves_original_r_and_objectives(tmp_path) -> None:
    repository = ManagedTradeRepository(StateStore(tmp_path / "state.db"), "123456:XAUUSDm")
    trade = _trade()
    repository.save(trade, event_type="MANAGED_TRADE_OPENED")

    restored = repository.load()
    assert restored == trade
    assert restored is not None
    assert restored.original_r_price == pytest.approx(10.0)
    assert restored.runner_candidate is not None

    repository.clear_verified_closed()
    assert repository.load() is None
