"""Verified historical broker-session facts for chronological research.

The model never guesses a broker clock. Callers supply explicit tradeable intervals
from a named/versioned source. Frozen PRE_CLOSE thresholds are delegated to the
production risk permission evaluator so research does not duplicate timing policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from goldswingtraderai.risk.permissions import (
    BrokerSessionFacts,
    ClosureKind,
    MarketPermission,
    evaluate_market_permission,
)


class HistoricalSessionCoverageError(RuntimeError):
    """Requested replay time is outside verified schedule coverage."""


@dataclass(frozen=True, slots=True)
class HistoricalTradingInterval:
    open_utc: datetime
    close_utc: datetime
    closure_kind: ClosureKind

    def __post_init__(self) -> None:
        _require_utc(self.open_utc)
        _require_utc(self.close_utc)
        if self.close_utc <= self.open_utc:
            raise ValueError("historical trading interval close must follow open")


@dataclass(frozen=True, slots=True)
class HistoricalSessionSchedule:
    source_label: str
    source_version: str
    coverage_start_utc: datetime
    coverage_end_utc: datetime
    intervals: tuple[HistoricalTradingInterval, ...]

    def __post_init__(self) -> None:
        if not self.source_label.strip() or not self.source_version.strip():
            raise ValueError("historical session source label/version cannot be empty")
        _require_utc(self.coverage_start_utc)
        _require_utc(self.coverage_end_utc)
        if self.coverage_end_utc <= self.coverage_start_utc:
            raise ValueError("historical session coverage range is invalid")
        if not self.intervals:
            raise ValueError("historical session schedule requires trading intervals")
        previous_close: datetime | None = None
        for interval in self.intervals:
            if (
                interval.open_utc < self.coverage_start_utc
                or interval.close_utc > self.coverage_end_utc
            ):
                raise ValueError("historical trading interval is outside verified coverage")
            if previous_close is not None and interval.open_utc < previous_close:
                raise ValueError("historical trading intervals cannot overlap")
            previous_close = interval.close_utc
        opens = tuple(item.open_utc for item in self.intervals)
        if opens != tuple(sorted(opens)):
            raise ValueError("historical trading intervals must be chronological")

    def market_permission_at(self, now_utc: datetime) -> MarketPermission:
        """Evaluate production market permission from explicit historical intervals."""

        _require_utc(now_utc)
        if not self.coverage_start_utc <= now_utc <= self.coverage_end_utc:
            raise HistoricalSessionCoverageError(
                "historical replay time is outside verified session coverage"
            )

        interval = self._active_interval(now_utc)
        if interval is None:
            return evaluate_market_permission(
                BrokerSessionFacts(
                    tradeable=False,
                    schedule_verified=True,
                    next_close_utc=None,
                    next_close_kind=None,
                ),
                now_utc,
            )

        return evaluate_market_permission(
            BrokerSessionFacts(
                tradeable=True,
                schedule_verified=True,
                next_close_utc=interval.close_utc,
                next_close_kind=interval.closure_kind,
            ),
            now_utc,
        )

    def flatten_required_at(self, now_utc: datetime) -> bool:
        """Return only the production PRE_CLOSE mandatory-flatten decision."""

        return self.market_permission_at(now_utc).flatten_required

    def _active_interval(self, now_utc: datetime) -> HistoricalTradingInterval | None:
        for interval in self.intervals:
            # Close instant itself belongs to the closed side; mandatory flatten
            # must have occurred while the broker was still tradeable before it.
            if interval.open_utc <= now_utc < interval.close_utc:
                return interval
        return None


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("historical session timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("historical session timestamp must be UTC")
