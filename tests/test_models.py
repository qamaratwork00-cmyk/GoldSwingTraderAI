from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from goldswingtraderai.diagnostics.reasons import ReasonCode
from goldswingtraderai.domain.enums import AccountMode, Direction, HardDecision, Timeframe
from goldswingtraderai.domain.ids import EntityId
from goldswingtraderai.domain.models import (
    ControllerLease,
    DemoGuardResult,
    ExecutionIntent,
    MarketSnapshotMeta,
    PermissionResult,
    Reason,
)


def _id(kind: str, digit: str) -> EntityId:
    return EntityId(kind, digit * 32)


def test_permission_block_requires_reason() -> None:
    with pytest.raises(ValueError, match="requires a primary reason"):
        PermissionResult(HardDecision.BLOCK)


def test_permission_pass_rejects_blocking_reason() -> None:
    reason = Reason(ReasonCode.DATA_STALE)
    with pytest.raises(ValueError, match="PASS permission"):
        PermissionResult(HardDecision.PASS, primary_reason=reason)


def test_demo_guard_pass_only_for_demo() -> None:
    DemoGuardResult(HardDecision.PASS, AccountMode.DEMO)

    with pytest.raises(ValueError, match="only for positively verified DEMO"):
        DemoGuardResult(HardDecision.PASS, AccountMode.OTHER)


def test_nonpassing_demo_guard_requires_reason() -> None:
    with pytest.raises(ValueError, match="requires a reason"):
        DemoGuardResult(HardDecision.UNKNOWN, AccountMode.UNKNOWN)


def test_snapshot_requires_utc_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        MarketSnapshotMeta(
            snapshot_id=_id("SNAP", "1"),
            symbol="XAUUSDm",
            as_of_utc=datetime(2026, 1, 1),
            timeframes=(Timeframe.H4, Timeframe.H1, Timeframe.M15, Timeframe.M5),
            data_complete=True,
        )


def test_controller_lease_epoch_and_expiry() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    lease = ControllerLease(
        holder_instance_id=_id("CTRL", "2"),
        epoch=3,
        last_renewed_at_utc=now,
        expires_at_utc=now + timedelta(seconds=30),
    )

    assert lease.is_valid_at(now + timedelta(seconds=10)) is True
    assert lease.is_valid_at(now + timedelta(seconds=30)) is False


def test_buy_execution_intent_geometry() -> None:
    intent = ExecutionIntent(
        intent_id=_id("INTENT", "3"),
        opportunity_id=_id("OPP", "4"),
        episode_id=_id("EP", "5"),
        created_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        direction=Direction.BUY,
        volume=0.01,
        approved_entry_reference=4300.0,
        structural_sl=4290.0,
        broker_tp=4320.0,
        controller_epoch=1,
    )

    assert intent.volume == 0.01


def test_buy_execution_intent_rejects_wrong_side_stop() -> None:
    with pytest.raises(ValueError, match="BUY structural SL"):
        ExecutionIntent(
            intent_id=_id("INTENT", "6"),
            opportunity_id=_id("OPP", "7"),
            episode_id=_id("EP", "8"),
            created_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
            direction=Direction.BUY,
            volume=0.01,
            approved_entry_reference=4300.0,
            structural_sl=4310.0,
        )
