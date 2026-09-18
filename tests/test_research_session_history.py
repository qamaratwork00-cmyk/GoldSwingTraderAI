from datetime import datetime, timedelta, timezone

import pytest

from goldswingtraderai.domain.enums import MarketState
from goldswingtraderai.research.session_history import (
    HistoricalSessionCoverageError,
    HistoricalSessionSchedule,
    HistoricalTradingInterval,
)
from goldswingtraderai.risk.permissions import ClosureKind


DAY = datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc)


def _schedule(kind: ClosureKind, close_minute: int = 120) -> HistoricalSessionSchedule:
    opened = DAY
    closed = DAY + timedelta(minutes=close_minute)
    return HistoricalSessionSchedule(
        source_label="verified-broker-schedule",
        source_version="2026-09-v1",
        coverage_start_utc=DAY,
        coverage_end_utc=DAY + timedelta(hours=4),
        intervals=(
            HistoricalTradingInterval(
                open_utc=opened,
                close_utc=closed,
                closure_kind=kind,
            ),
        ),
    )


def test_daily_schedule_reuses_frozen_preclose_thresholds() -> None:
    schedule = _schedule(ClosureKind.DAILY)

    no_entry = schedule.market_permission_at(DAY + timedelta(minutes=105))  # T-15
    flatten = schedule.market_permission_at(DAY + timedelta(minutes=115))  # T-5

    assert no_entry.state is MarketState.PRE_CLOSE
    assert not no_entry.new_entries_allowed
    assert not no_entry.flatten_required
    assert flatten.state is MarketState.PRE_CLOSE
    assert flatten.flatten_required


def test_weekend_schedule_reuses_wider_frozen_thresholds() -> None:
    schedule = _schedule(ClosureKind.WEEKEND)

    no_entry = schedule.market_permission_at(DAY + timedelta(minutes=75))  # T-45
    flatten = schedule.market_permission_at(DAY + timedelta(minutes=105))  # T-15

    assert no_entry.state is MarketState.PRE_CLOSE
    assert not no_entry.flatten_required
    assert flatten.flatten_required


def test_time_outside_tradeable_interval_is_closed_within_verified_coverage() -> None:
    schedule = _schedule(ClosureKind.DAILY)
    permission = schedule.market_permission_at(DAY + timedelta(minutes=150))

    assert permission.state is MarketState.CLOSED
    assert not permission.new_entries_allowed
    assert not permission.flatten_required


def test_schedule_refuses_unverified_time_outside_coverage() -> None:
    schedule = _schedule(ClosureKind.DAILY)

    with pytest.raises(HistoricalSessionCoverageError):
        schedule.market_permission_at(DAY - timedelta(minutes=1))


def test_schedule_rejects_overlapping_intervals() -> None:
    with pytest.raises(ValueError, match="cannot overlap"):
        HistoricalSessionSchedule(
            source_label="verified",
            source_version="v1",
            coverage_start_utc=DAY,
            coverage_end_utc=DAY + timedelta(hours=4),
            intervals=(
                HistoricalTradingInterval(
                    open_utc=DAY,
                    close_utc=DAY + timedelta(hours=2),
                    closure_kind=ClosureKind.DAILY,
                ),
                HistoricalTradingInterval(
                    open_utc=DAY + timedelta(hours=1),
                    close_utc=DAY + timedelta(hours=3),
                    closure_kind=ClosureKind.DAILY,
                ),
            ),
        )
