from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import sqlite3

import pytest

from goldswingtraderai.persistence import (
    RuntimeCheckpointError,
    RuntimeStateRepository,
    StateIntegrityError,
    StateStore,
    export_runtime_checkpoint,
    import_runtime_checkpoint,
    restore_runtime_checkpoint,
)
from goldswingtraderai.risk import CooldownState, new_risk_day


NOW = datetime(2026, 9, 18, 18, 0, tzinfo=timezone.utc)


def _seed_runtime(path):
    store = StateStore(path)
    repository = RuntimeStateRepository(store, "123456:XAUUSDm")
    risk_day = new_risk_day(NOW, 100.0, manual_reset_enabled=True)
    cooldown = CooldownState(
        consecutive_losses=3,
        triggered_at_utc=NOW - timedelta(minutes=5),
        cooldown_until_utc=NOW + timedelta(minutes=25),
    )
    repository.save_risk_day(risk_day)
    repository.save_cooldown(cooldown)
    store.save_record(
        "strategy_memory",
        "gold-v1",
        {"sample_count": 14, "quality": 0.71},
        event_type="STRATEGY_MEMORY_SAVED",
    )
    return store, risk_day, cooldown


def test_runtime_checkpoint_roundtrip_restores_typed_state_and_event_history(tmp_path) -> None:
    source, risk_day, cooldown = _seed_runtime(tmp_path / "source.db")
    checkpoint_path = tmp_path / "checkpoint"

    exported = export_runtime_checkpoint(
        source,
        checkpoint_path,
        source_label="laptop-a",
        source_version="runtime-2026-09-18",
        created_at_utc=NOW,
    )
    imported = import_runtime_checkpoint(checkpoint_path)

    assert exported.records_count == 3
    assert exported.events_count == 3
    assert imported.manifest.checkpoint_sha256 == exported.checkpoint_sha256
    assert {item.name for item in checkpoint_path.iterdir()} == {
        "checkpoint_manifest.json",
        "records.jsonl",
        "events.jsonl",
    }

    restored_path = tmp_path / "fresh-machine.db"
    restored = restore_runtime_checkpoint(checkpoint_path, restored_path)
    assert restored.broker_reconciliation_required
    assert restored.records_count == 3
    assert restored.events_count == 3

    fresh_store = StateStore(restored_path)
    fresh_repository = RuntimeStateRepository(fresh_store, "123456:XAUUSDm")
    bundle = fresh_repository.load_recovery_bundle()
    assert bundle.risk_day == risk_day
    assert bundle.cooldown == cooldown
    assert fresh_store.event_count() == source.event_count() == 3
    memory = fresh_store.load_record("strategy_memory", "gold-v1")
    assert memory is not None
    assert memory.payload == {"quality": 0.71, "sample_count": 14}


def test_checkpoint_export_blocks_financial_authority_secret_and_leaves_no_artifact(tmp_path) -> None:
    store = StateStore(tmp_path / "source.db")
    store.save_record(
        "bad_state",
        "one",
        {"password": "supersecret123"},
        event_type="BAD_SAVED",
    )
    destination = tmp_path / "checkpoint"

    with pytest.raises(RuntimeCheckpointError, match="FINANCIAL_SECRET_DETECTED"):
        export_runtime_checkpoint(
            store,
            destination,
            source_label="test",
            source_version="v1",
            created_at_utc=NOW,
        )

    assert not destination.exists()


def test_checkpoint_import_detects_records_tamper(tmp_path) -> None:
    source, _, _ = _seed_runtime(tmp_path / "source.db")
    checkpoint = tmp_path / "checkpoint"
    export_runtime_checkpoint(
        source,
        checkpoint,
        source_label="test",
        source_version="v1",
        created_at_utc=NOW,
    )

    records_path = checkpoint / "records.jsonl"
    text = records_path.read_text(encoding="utf-8")
    records_path.write_text(text.replace("0.71", "0.72", 1), encoding="utf-8")

    with pytest.raises(RuntimeCheckpointError, match="records hash mismatch"):
        import_runtime_checkpoint(checkpoint)


def test_checkpoint_import_detects_manifest_tamper(tmp_path) -> None:
    source, _, _ = _seed_runtime(tmp_path / "source.db")
    checkpoint = tmp_path / "checkpoint"
    export_runtime_checkpoint(
        source,
        checkpoint,
        source_label="test",
        source_version="v1",
        created_at_utc=NOW,
    )

    manifest_path = checkpoint / "checkpoint_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["records_count"] += 1
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")

    with pytest.raises(RuntimeCheckpointError, match="manifest hash mismatch"):
        import_runtime_checkpoint(checkpoint)


def test_checkpoint_export_and_restore_refuse_existing_destinations(tmp_path) -> None:
    source, _, _ = _seed_runtime(tmp_path / "source.db")
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()

    with pytest.raises(FileExistsError):
        export_runtime_checkpoint(
            source,
            checkpoint,
            source_label="test",
            source_version="v1",
            created_at_utc=NOW,
        )

    checkpoint.rmdir()
    export_runtime_checkpoint(
        source,
        checkpoint,
        source_label="test",
        source_version="v1",
        created_at_utc=NOW,
    )
    existing_database = tmp_path / "existing.db"
    StateStore(existing_database)

    with pytest.raises(FileExistsError):
        restore_runtime_checkpoint(checkpoint, existing_database)


def test_event_corruption_is_now_part_of_state_store_integrity(tmp_path) -> None:
    database = tmp_path / "state.db"
    store = StateStore(database)
    store.save_record("example", "one", {"value": 7}, event_type="SAVED")

    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE state_events SET payload_json=? WHERE event_id=1",
            ('{"value":8}',),
        )

    with pytest.raises(StateIntegrityError, match="event checksum mismatch"):
        store.integrity_check()
