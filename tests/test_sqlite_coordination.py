from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from goldswingtraderai.domain.ids import new_controller_id
from goldswingtraderai.execution import (
    ControllerLeaseManager,
    HardDecision,
    SQLiteCoordinationStore,
)


NOW = datetime(2026, 9, 18, 21, 0, tzinfo=timezone.utc)
TTL = timedelta(seconds=30)
SCOPE = "123456:XAUUSDm"


def test_independent_sqlite_stores_have_exactly_one_acquire_winner(tmp_path) -> None:
    database = tmp_path / "coordination.db"
    stores = [SQLiteCoordinationStore(database, lambda: NOW) for _ in range(8)]
    holders = [new_controller_id() for _ in stores]

    with ThreadPoolExecutor(max_workers=len(stores)) as pool:
        results = tuple(
            pool.map(
                lambda pair: pair[0].try_acquire(SCOPE, pair[1], TTL),
                zip(stores, holders, strict=True),
            )
        )

    winners = [lease for lease in results if lease is not None]
    assert len(winners) == 1
    assert winners[0].epoch == 1
    assert stores[0].read(SCOPE) == winners[0]


def test_epoch_remains_monotonic_after_release_and_store_reopen(tmp_path) -> None:
    database = tmp_path / "coordination.db"
    first_store = SQLiteCoordinationStore(database, lambda: NOW)
    first = first_store.try_acquire(SCOPE, new_controller_id(), TTL)
    assert first is not None
    assert first_store.release(first)

    reopened = SQLiteCoordinationStore(database, lambda: NOW)
    second = reopened.try_acquire(SCOPE, new_controller_id(), TTL)

    assert second is not None
    assert second.epoch == first.epoch + 1
    reopened.integrity_check()


def test_expiry_allows_new_epoch_and_stale_lease_cannot_renew_or_release(tmp_path) -> None:
    clock = [NOW]
    database = tmp_path / "coordination.db"
    first_store = SQLiteCoordinationStore(database, lambda: clock[0])
    second_store = SQLiteCoordinationStore(database, lambda: clock[0])

    first = first_store.try_acquire(SCOPE, new_controller_id(), TTL)
    assert first is not None
    assert second_store.try_acquire(SCOPE, new_controller_id(), TTL) is None

    clock[0] += timedelta(seconds=31)
    second = second_store.try_acquire(SCOPE, new_controller_id(), TTL)
    assert second is not None
    assert second.epoch > first.epoch
    assert first_store.renew(first, TTL) is None
    assert not first_store.release(first)
    assert second_store.read(SCOPE) == second


def test_renew_preserves_epoch_and_moves_expiry_forward(tmp_path) -> None:
    clock = [NOW]
    store = SQLiteCoordinationStore(tmp_path / "coordination.db", lambda: clock[0])
    lease = store.try_acquire(SCOPE, new_controller_id(), TTL)
    assert lease is not None

    clock[0] += timedelta(seconds=10)
    renewed = store.renew(lease, TTL)

    assert renewed is not None
    assert renewed.epoch == lease.epoch
    assert renewed.renewed_at_utc == clock[0]
    assert renewed.expires_at_utc == clock[0] + TTL
    store.integrity_check()


def test_controller_manager_uses_same_sqlite_store_contract(tmp_path) -> None:
    clock = [NOW]
    database = tmp_path / "coordination.db"
    first = ControllerLeaseManager(
        SQLiteCoordinationStore(database, lambda: clock[0]),
        SCOPE,
        new_controller_id(),
    )
    second = ControllerLeaseManager(
        SQLiteCoordinationStore(database, lambda: clock[0]),
        SCOPE,
        new_controller_id(),
    )

    assert first.acquire().decision is HardDecision.PASS
    blocked = second.acquire()
    assert blocked.decision is HardDecision.BLOCK
    assert blocked.reason == "ANOTHER_ACTIVE_CONTROLLER"

    clock[0] += timedelta(seconds=31)
    takeover = second.acquire()
    assert takeover.decision is HardDecision.PASS
    assert first.verify_write_authority(clock[0]).reason == "ANOTHER_ACTIVE_CONTROLLER"


def test_cross_machine_certification_is_explicit_and_false_by_default(tmp_path) -> None:
    database = tmp_path / "coordination.db"
    local = SQLiteCoordinationStore(database, lambda: NOW)
    asserted = SQLiteCoordinationStore(
        database,
        lambda: NOW,
        shared_locking_verified=True,
    )

    assert not local.cross_machine_certified
    assert asserted.cross_machine_certified
