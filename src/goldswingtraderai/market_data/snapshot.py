"""Normalized H4/H1/M15/M5 market snapshot construction."""

from __future__ import annotations

from datetime import datetime, timezone

from goldswingtraderai.domain.enums import DataQuality, Timeframe
from goldswingtraderai.domain.ids import new_snapshot_id
from goldswingtraderai.domain.market import CandleSeries, MarketSnapshot
from goldswingtraderai.domain.models import MarketSnapshotMeta
from goldswingtraderai.market_data.mt5_reader import MT5Reader


DEFAULT_HISTORY_BARS: dict[Timeframe, int] = {
    Timeframe.H4: 400,
    Timeframe.H1: 750,
    Timeframe.M15: 2000,
    Timeframe.M5: 4000,
}

_TIMEFRAME_SECONDS: dict[Timeframe, int] = {
    Timeframe.H4: 4 * 60 * 60,
    Timeframe.H1: 60 * 60,
    Timeframe.M15: 15 * 60,
    Timeframe.M5: 5 * 60,
    Timeframe.M1: 60,
}


class MarketSnapshotBuilder:
    """Build one reusable verified snapshot from a single MT5 read pass."""

    def __init__(
        self,
        reader: MT5Reader,
        *,
        history_bars: dict[Timeframe, int] | None = None,
        max_quote_age_seconds: float = 10.0,
    ) -> None:
        self._reader = reader
        self._history_bars = dict(history_bars or DEFAULT_HISTORY_BARS)
        self._max_quote_age_seconds = float(max_quote_age_seconds)
        if self._max_quote_age_seconds <= 0:
            raise ValueError("max_quote_age_seconds must be positive")
        if not self._history_bars:
            raise ValueError("history_bars cannot be empty")
        if any(count <= 0 for count in self._history_bars.values()):
            raise ValueError("history bar counts must be positive")

    def build(
        self,
        *,
        preferred_symbol: str,
        symbol_aliases: tuple[str, ...],
        now_utc: datetime | None = None,
    ) -> MarketSnapshot:
        now = now_utc or datetime.now(timezone.utc)
        if now.tzinfo is None or now.utcoffset() != timezone.utc.utcoffset(now):
            raise ValueError("now_utc must be UTC and timezone-aware")

        account = self._reader.account_facts()
        symbol = self._reader.resolve_symbol(preferred_symbol, symbol_aliases)
        symbol_spec = self._reader.symbol_spec(symbol)
        quote = self._reader.quote(symbol)

        series = tuple(
            self._reader.completed_candles(symbol, timeframe, count)
            for timeframe, count in self._history_bars.items()
        )
        quality, issues = self._assess_quality(series, quote_age=quote.age_seconds(now), now_utc=now)

        meta = MarketSnapshotMeta(
            snapshot_id=new_snapshot_id(),
            symbol=symbol,
            as_of_utc=now,
            timeframes=tuple(item.timeframe for item in series),
            data_complete=quality is DataQuality.HEALTHY,
        )
        return MarketSnapshot(
            meta=meta,
            account=account,
            symbol_spec=symbol_spec,
            quote=quote,
            series=series,
            quality=quality,
            issues=issues,
        )

    def _assess_quality(
        self,
        series: tuple[CandleSeries, ...],
        *,
        quote_age: float,
        now_utc: datetime,
    ) -> tuple[DataQuality, tuple[str, ...]]:
        issues: list[str] = []
        quality = DataQuality.HEALTHY

        if quote_age > self._max_quote_age_seconds:
            quality = DataQuality.STALE
            issues.append(f"quote age {quote_age:.1f}s exceeds {self._max_quote_age_seconds:.1f}s")

        for item in series:
            requested = self._history_bars[item.timeframe]
            if len(item.candles) < requested:
                if quality is DataQuality.HEALTHY:
                    quality = DataQuality.INSUFFICIENT
                issues.append(
                    f"{item.timeframe} returned {len(item.candles)}/{requested} completed candles"
                )

            period = _TIMEFRAME_SECONDS[item.timeframe]
            latest_age = (now_utc - item.latest.time_utc).total_seconds()
            # Candle timestamps represent bar-open time. A completed bar may be almost
            # two full periods old near the end of the currently-forming candle.
            if latest_age > 2 * period:
                quality = DataQuality.STALE
                issues.append(f"latest {item.timeframe} completed candle is stale")

            recent = item.candles[-5:]
            if len(recent) > 1:
                recent_gaps = [
                    (right.time_utc - left.time_utc).total_seconds()
                    for left, right in zip(recent, recent[1:])
                ]
                if any(gap > 1.5 * period for gap in recent_gaps):
                    if quality is DataQuality.HEALTHY:
                        quality = DataQuality.SPARSE
                    issues.append(f"recent {item.timeframe} candle gap detected")

        return quality, tuple(issues)
