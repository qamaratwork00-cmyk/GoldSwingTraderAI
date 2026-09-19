"""Restore a verified runtime checkpoint into a new local database.

Restoration is migration context only. The command deliberately reports that
broker reconciliation is still required; it cannot grant trading authority.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from goldswingtraderai.persistence import (
    RuntimeCheckpointError,
    restore_runtime_checkpoint,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Restore a verified runtime checkpoint into a new database"
    )
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("database", type=Path)
    args = parser.parse_args(argv)

    try:
        result = restore_runtime_checkpoint(args.checkpoint, args.database)
    except (RuntimeCheckpointError, FileExistsError, FileNotFoundError, OSError, ValueError) as exc:
        print(f"RESTORE_FAILED: {exc}")
        return 2

    print(
        json.dumps(
            {
                "database": str(result.database_path),
                "checkpoint_sha256": result.checkpoint_sha256,
                "records_count": result.records_count,
                "events_count": result.events_count,
                "broker_reconciliation_required": result.broker_reconciliation_required,
                "trading_authority_granted": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
