from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

import pytest

from goldswingtraderai.persistence import (
    BackupCatalogError,
    BackupPolicy,
    BackupRunStatus,
    RuntimeCheckpointError,
    StateStore,
    create_backup_if_due,
    latest_verified_checkpoint,
    load_backup_catalog,
)


NOW = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)


def _store(path) -> StateStore:
    store = StateStore(path)
    store.save_record(
        "runtime",
        "gold",
        {"status": "READY", "counter": 1},
        event_type="RUNTIME_SAVED",
    )
    return store


def _create(store: StateStore, root, when: datetime, policy: BackupPolicy):
    return create_backup_if_due(
        store,
        root,
        source_label="laptop-a",
        source_version="runtime-v1",
        policy=policy,
        now_utc=when,
    )


def test_backup_cadence_creates_then_skips_until_due(tmp_path) -> None:
    store = _store(tmp_path / "runtime.db")
    root = tmp_path / "backups"
    policy = BackupPolicy(interval_minutes=15, keep_latest=4)

    first = _create(store, root, NOW, policy)
    early = _create(store, root, NOW + timedelta(minutes=14, seconds=59), policy)
    due = _create(store, root, NOW + timedelta(minutes=15), policy)

    assert first.status is BackupRunStatus.CREATED
    assert early.status is BackupRunStatus.SKIPPED_NOT_DUE
    assert early.entry is None
    assert due.status is BackupRunStatus.CREATED
    assert len(due.catalog.entries) == 2
    assert due.catalog.entries[-1].created_at_utc == NOW + timedelta(minutes=15)


def test_backup_retention_keeps_only_newest_verified_checkpoints(tmp_path) -> None:
    store = _store(tmp_path / "runtime.db")
    root = tmp_path / "backups"
    policy = BackupPolicy(interval_minutes=10, keep_latest=2)

    _create(store, root, NOW, policy)
    _create(store, root, NOW + timedelta(minutes=10), policy)
    third = _create(store, root, NOW + timedelta(minutes=20), policy)

    catalog = load_backup_catalog(root)
    assert catalog == third.catalog
    assert len(catalog.entries) == 2
    assert [item.created_at_utc for item in catalog.entries] == [
        NOW + timedelta(minutes=10),
        NOW + timedelta(minutes=20),
    ]

    checkpoint_dirs = sorted(
        path.name for path in (root / "checkpoints").iterdir() if path.is_dir()
    )
    assert checkpoint_dirs == sorted(item.name for item in catalog.entries)


def test_latest_verified_checkpoint_returns_newest_catalogued_entry(tmp_path) -> None:
    store = _store(tmp_path / "runtime.db")
    root = tmp_path / "backups"
    policy = BackupPolicy(interval_minutes=5, keep_latest=3)

    _create(store, root, NOW, policy)
    second = _create(store, root, NOW + timedelta(minutes=5), policy)

    latest = latest_verified_checkpoint(root)
    assert latest is not None
    assert second.entry is not None
    assert latest.name == second.entry.name
    assert latest.parent == root / "checkpoints"


def test_backup_catalog_tamper_is_detected(tmp_path) -> None:
    store = _store(tmp_path / "runtime.db")
    root = tmp_path / "backups"
    _create(store, root, NOW, BackupPolicy(interval_minutes=15, keep_latest=4))

    catalog_path = root / "backup_catalog.json"
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    payload["entries"][0]["records_count"] += 1
    catalog_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    with pytest.raises(BackupCatalogError, match="catalog hash mismatch"):
        load_backup_catalog(root)


def test_tampered_catalogued_checkpoint_fails_verification(tmp_path) -> None:
    store = _store(tmp_path / "runtime.db")
    root = tmp_path / "backups"
    created = _create(store, root, NOW, BackupPolicy(interval_minutes=15, keep_latest=4))
    assert created.entry is not None

    records_path = root / "checkpoints" / created.entry.name / "records.jsonl"
    text = records_path.read_text(encoding="utf-8")
    records_path.write_text(text.replace('"counter":1', '"counter":2', 1), encoding="utf-8")

    with pytest.raises(BackupCatalogError, match="invalid catalogued checkpoint"):
        load_backup_catalog(root, verify_checkpoints=True)
    with pytest.raises(BackupCatalogError, match="invalid catalogued checkpoint"):
        latest_verified_checkpoint(root)


def test_failed_secret_backup_preserves_previous_known_good_catalog(tmp_path) -> None:
    store = _store(tmp_path / "runtime.db")
    root = tmp_path / "backups"
    policy = BackupPolicy(interval_minutes=15, keep_latest=4)
    first = _create(store, root, NOW, policy)
    assert first.entry is not None

    original_catalog = (root / "backup_catalog.json").read_text(encoding="utf-8")
    original_checkpoint = root / "checkpoints" / first.entry.name
    assert original_checkpoint.is_dir()

    store.save_record(
        "bad_state",
        "credential",
        {"password": "supersecret123"},
        event_type="BAD_STATE_SAVED",
    )

    with pytest.raises(RuntimeCheckpointError, match="FINANCIAL_SECRET_DETECTED"):
        _create(store, root, NOW + timedelta(minutes=15), policy)

    assert (root / "backup_catalog.json").read_text(encoding="utf-8") == original_catalog
    assert original_checkpoint.is_dir()
    catalog = load_backup_catalog(root)
    assert [entry.name for entry in catalog.entries] == [first.entry.name]


def test_backup_policy_rejects_nonpositive_values() -> None:
    with pytest.raises(ValueError):
        BackupPolicy(interval_minutes=0)
    with pytest.raises(ValueError):
        BackupPolicy(keep_latest=0)
