from __future__ import annotations

from datetime import datetime, timedelta, timezone

import goldswingtraderai.intelligence.candle_structure as structure_module
from goldswingtraderai.domain.enums import AccountMode, DataQuality, Timeframe
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
from goldswingtraderai.intelligence.news import (
    EventTier,
    ProviderHealth,
    RawScheduledEvent,
    normalize_news_facts,
)
from goldswingtraderai.intelligence.session import SessionName, classify_session
from goldswingtraderai.intelligence.snapshot import build_intelligence_snapshot


def _candles(end_utc: datetime, timeframe: Timeframe, count: int = 60) -> tuple[Candle, ...]:
    seconds = {
        Timeframe.H4: 14_400,
        Timeframe.H1: 3_600,
        Timeframe.M15: 900,
        Timeframe.M5: 300,
    }[timeframe]
    output: list[Candle] = []
    for index in range(count):
        age = count - index
        when = end_utc - timedelta(seconds=seconds * age)
        base = 3650.0 + index * 0.20
        wave = 1.0 if index % 6 < 3 else -0.8
        close = base + wave
        output.append(
            Candle(
                time_utc=when,
                open=base,
                high=max(base, close) + 1.0,
                low=min(base, close) - 1.0,
                close=close,
                tick_volume=100 + index,
                spread_points=20,
            )
        )
    return tuple(output)


def _market(as_of_utc: datetime) -> MarketSnapshot:
    timeframes = (Timeframe.H4, Timeframe.H1, Timeframe.M15, Timeframe.M5)
    series = tuple(
        CandleSeries(timeframe=timeframe, candles=_candles(as_of_utc, timeframe))
        for timeframe in timeframes
    )
    return MarketSnapshot(
        meta=MarketSnapshotMeta(
            snapshot_id=new_snapshot_id(),
            symbol="XAUUSDm",
            as_of_utc=as_of_utc,
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
            bid=3661.000,
            ask=3661.200,
            time_utc=as_of_utc,
        ),
        series=series,
        quality=DataQuality.HEALTHY,
    )


def test_session_classification_is_dst_aware() -> None:
    summer = datetime(2026, 7, 1, 12, 30, tzinfo=timezone.utc)
    winter = datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)

    assert classify_session(summer) is SessionName.LONDON_NY_OVERLAP
    assert classify_session(winter) is SessionName.LONDON


def test_news_tiers_cluster_and_stale_health() -> None:
    base = datetime(2026, 9, 16, 18, 0, tzinfo=timezone.utc)
    raw = (
        RawScheduledEvent("fomc", "FOMC Rate Decision", "USD", base, "critical"),
        RawScheduledEvent(
            "powell",
            "Fed Chair Powell Press Conference",
            "USD",
            base + timedelta(minutes=30),
            "critical",
        ),
        RawScheduledEvent(
            "sales",
            "Retail Sales",
            "USD",
            base + timedelta(hours=3),
            "high",
        ),
    )
    facts = normalize_news_facts(
        raw,
        provider="fixture",
        provider_health=ProviderHealth.VERIFIED,
        fetched_at_utc=base - timedelta(minutes=1),
        as_of_utc=base,
    )

    assert facts.events[0].tier is EventTier.TIER_1
    assert facts.events[0].window_before_minutes == 15
    assert facts.events[2].tier is EventTier.TIER_2
    assert facts.events[2].window_before_minutes == 5
    assert facts.windows[0].event_ids == ("fomc", "powell")
    assert facts.windows[0].end_utc == base + timedelta(minutes=45)

    stale = normalize_news_facts(
        (),
        provider="fixture",
        provider_health=ProviderHealth.VERIFIED,
        fetched_at_utc=base - timedelta(hours=2),
        as_of_utc=base,
    )
    assert stale.health is ProviderHealth.STALE
    assert stale.required_event_truth_available is False


def test_intelligence_snapshot_reuses_precomputed_atr(monkeypatch) -> None:
    as_of = datetime(2026, 7, 1, 12, 30, tzinfo=timezone.utc)

    def forbidden_recompute(*args, **kwargs):
        raise AssertionError("structure attempted to recompute ATR")

    monkeypatch.setattr(structure_module, "atr_series", forbidden_recompute)
    result = build_intelligence_snapshot(_market(as_of))

    assert tuple(frame.timeframe for frame in result.frames) == (
        Timeframe.H4,
        Timeframe.H1,
        Timeframe.M15,
        Timeframe.M5,
    )
    assert result.for_timeframe(Timeframe.M15).quant.atr is not None
    assert result.session.current is SessionName.LONDON_NY_OVERLAP
