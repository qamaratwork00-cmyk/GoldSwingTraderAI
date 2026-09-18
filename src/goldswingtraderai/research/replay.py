"""Chronological bar-close replay that reuses production analysis semantics.

The adapter exposes only candles that were completed at each historical event time.
It intentionally labels its quote model BAR_CLOSE; it is not tick-perfect execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from goldswingtraderai.decisions.opportunity import Opportunity
from goldswingtraderai.decisions.snapshot import DecisionConfig, DecisionSnapshot, build_decision_snapshot
from goldswingtraderai.domain.enums import DataQuality, OpportunityStage, Timeframe
from goldswingtraderai.domain.ids import EntityId, new_snapshot_id
from goldswingtraderai.domain.market import (
    AccountFacts,
    CandleSeries,
    MarketSnapshot,
    Quote,
    SymbolSpec,
)
from goldswingtraderai.domain.models import MarketSnapshotMeta
from goldswingtraderai.intelligence.snapshot import (
    IntelligenceConfig,
    build_intelligence_snapshot,
)


_TIMEFRAME_SECONDS: dict[Timeframe, int] = {
    Timeframe.H4: 4 * 60 * 60,
    Timeframe.H1: 60 * 60,
    Timeframe.M15: 15 * 60,
    Timeframe.M5: 5 * 60,
    Timeframe.M1: 60,
}


class ReplayRealism(StrEnum):
    BAR_CLOSE = "BAR_CLOSE"


@dataclass(frozen=True, slots=True)
class ReplayDataset:
    account: AccountFacts
    symbol_spec: SymbolSpec
    series: tuple[CandleSeries, ...]
    spread_price: float
    realism: ReplayRealism = ReplayRealism.BAR_CLOSE

    def __post_init__(self) -> None:
        if self.spread_price < 0:
            raise ValueError("replay spread cannot be negative")
        timeframes = tuple(item.timeframe for item in self.series)
        required = {Timeframe.H4, Timeframe.H1, Timeframe.M15, Timeframe.M5}
        if not required.issubset(set(timeframes)):
            raise ValueError("replay dataset requires H4/H1/M15/M5 series")
        if len(timeframes) != len(set(timeframes)):
            raise ValueError("replay dataset cannot contain duplicate timeframes")
        if any(not item.candles for item in self.series):
            raise ValueError("replay candle series cannot be empty")

    def event_times(self) -> tuple[datetime, ...]:
        """Return M5 completion times; decisions occur only after each M5 closes."""

        m5 = self._series(Timeframe.M5)
        period = timedelta(seconds=_TIMEFRAME_SECONDS[Timeframe.M5])
        return tuple(candle.time_utc + period for candle in m5.candles)

    def snapshot_at(
        self,
        as_of_utc: datetime,
        *,
        minimum_bars: dict[Timeframe, int] | None = None,
    ) -> MarketSnapshot | None:
        """Build one prefix-only snapshot; future/open candles are inaccessible."""

        _require_utc(as_of_utc)
        minimum = minimum_bars or {
            Timeframe.H4: 55,
            Timeframe.H1: 70,
            Timeframe.M15: 80,
            Timeframe.M5: 100,
        }
        visible: list[CandleSeries] = []
        for item in self.series:
            period = timedelta(seconds=_TIMEFRAME_SECONDS[item.timeframe])
            candles = tuple(
                candle for candle in item.candles if candle.time_utc + period <= as_of_utc
            )
            if len(candles) < minimum.get(item.timeframe, 1):
                return None
            visible.append(CandleSeries(timeframe=item.timeframe, candles=candles))

        m5 = next(item for item in visible if item.timeframe is Timeframe.M5)
        mid = m5.latest.close
        half_spread = self.spread_price / 2.0
        quote = Quote(
            symbol=self.symbol_spec.symbol,
            bid=max(self.symbol_spec.tick_size, mid - half_spread),
            ask=mid + half_spread,
            time_utc=as_of_utc,
        )
        ordered = tuple(visible)
        return MarketSnapshot(
            meta=MarketSnapshotMeta(
                snapshot_id=new_snapshot_id(),
                symbol=self.symbol_spec.symbol,
                as_of_utc=as_of_utc,
                timeframes=tuple(item.timeframe for item in ordered),
                data_complete=True,
            ),
            account=self.account,
            symbol_spec=self.symbol_spec,
            quote=quote,
            series=ordered,
            quality=DataQuality.HEALTHY,
            issues=("REPLAY_BAR_CLOSE_QUOTE_MODEL",),
        )

    def _series(self, timeframe: Timeframe) -> CandleSeries:
        for item in self.series:
            if item.timeframe is timeframe:
                return item
        raise KeyError(timeframe)


@dataclass(frozen=True, slots=True)
class ReplayDecision:
    as_of_utc: datetime
    market_snapshot_id: EntityId
    decision: DecisionSnapshot


@dataclass(frozen=True, slots=True)
class ReplayRun:
    realism: ReplayRealism
    decisions: tuple[ReplayDecision, ...]
    first_event_utc: datetime | None
    last_event_utc: datetime | None


def run_decision_replay(
    dataset: ReplayDataset,
    *,
    start_utc: datetime | None = None,
    end_utc: datetime | None = None,
    minimum_bars: dict[Timeframe, int] | None = None,
    intelligence_config: IntelligenceConfig | None = None,
    decision_config: DecisionConfig | None = None,
) -> ReplayRun:
    """Replay production intelligence/decision semantics in strict chronology."""

    if start_utc is not None:
        _require_utc(start_utc)
    if end_utc is not None:
        _require_utc(end_utc)
    if start_utc is not None and end_utc is not None and end_utc < start_utc:
        raise ValueError("replay end cannot precede start")

    previous: Opportunity | None = None
    output: list[ReplayDecision] = []
    for event_time in dataset.event_times():
        if start_utc is not None and event_time < start_utc:
            continue
        if end_utc is not None and event_time > end_utc:
            break

        market = dataset.snapshot_at(event_time, minimum_bars=minimum_bars)
        if market is None:
            continue
        intelligence = build_intelligence_snapshot(
            market,
            config=intelligence_config,
        )
        # A completed terminal episode is archived before the next independent
        # market episode; its ID is never recycled into the new opportunity.
        if previous is not None and previous.stage in {
            OpportunityStage.TRIGGERED,
            OpportunityStage.MISSED,
            OpportunityStage.STALE,
            OpportunityStage.INVALIDATED,
        }:
            previous = None
        decision = build_decision_snapshot(
            intelligence,
            event_time,
            previous_opportunity=previous,
            config=decision_config,
        )
        previous = decision.opportunity
        output.append(
            ReplayDecision(
                as_of_utc=event_time,
                market_snapshot_id=market.snapshot_id,
                decision=decision,
            )
        )

    decisions = tuple(output)
    return ReplayRun(
        realism=dataset.realism,
        decisions=decisions,
        first_event_utc=decisions[0].as_of_utc if decisions else None,
        last_event_utc=decisions[-1].as_of_utc if decisions else None,
    )


def visible_candle_count(
    series: CandleSeries,
    as_of_utc: datetime,
) -> int:
    """Public test/helper proving the replay visibility boundary."""

    _require_utc(as_of_utc)
    period = timedelta(seconds=_TIMEFRAME_SECONDS[series.timeframe])
    return sum(1 for candle in series.candles if candle.time_utc + period <= as_of_utc)


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("replay timestamps must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("replay timestamps must be UTC")
