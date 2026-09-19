from __future__ import annotations

from datetime import datetime, timezone
import json

from scripts.restore_runtime_checkpoint import main as restore_main
from scripts.stage_public_backup import main as stage_main

from goldswingtraderai.persistence import (
    BackupPolicy,
    StateStore,
    create_backup_if_due,
    export_runtime_checkpoint,
)


NOW = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)


def _backup_root(tmp_path):
    store = StateStore(tmp_path / "runtime.db")
    store.save_record("runtime", "gold", {"status": "READY"}, event_type="RUNTIME_SAVED")
    root = tmp_path / "backups"
    create_backup_if_due(
        store,
        root,
        source_label="test",
        source_version="v1",
        policy=BackupPolicy(interval_minutes=5),
        now_utc=NOW,
    )
    return root


def test_stage_public_backup_cli_reports_safe_boundary(tmp_path, capsys) -> None:
    root = _backup_root(tmp_path)
    destination = tmp_path / "public" / "runtime-backup"

    assert (
        stage_main(
            [
                str(root),
                str(destination),
                "--published-at-utc",
                "2026-09-18T20:00:00Z",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["secret_scan"] == "PASS"
    assert payload["push_performed"] is False
    assert destination.is_dir()


def test_restore_checkpoint_cli_reports_reconciliation_required(tmp_path, capsys) -> None:
    source = StateStore(tmp_path / "source.db")
    source.save_record("runtime", "gold", {"status": "READY"}, event_type="RUNTIME_SAVED")
    checkpoint = tmp_path / "checkpoint"
    export_runtime_checkpoint(
        source,
        checkpoint,
        source_label="test",
        source_version="v1",
        created_at_utc=NOW,
    )
    database = tmp_path / "fresh" / "runtime.db"

    assert restore_main([str(checkpoint), str(database)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["broker_reconciliation_required"] is True
    assert payload["trading_authority_granted"] is False
    assert database.is_file()
