"""Stage the newest verified runtime backup for explicit public publication.

The command performs local verification and secret scanning only. It never
authenticates to GitHub, writes credentials, commits, or pushes anything.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from goldswingtraderai.persistence import PublicationError, stage_verified_public_backup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage the newest verified backup for explicit public publication"
    )
    parser.add_argument("backup_root", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--published-at-utc",
        help="optional ISO-8601 UTC timestamp; defaults to the current UTC time",
    )
    args = parser.parse_args(argv)

    try:
        published_at = _parse_utc(args.published_at_utc) if args.published_at_utc else None
        result = stage_verified_public_backup(
            args.backup_root,
            args.destination,
            published_at_utc=published_at,
        )
    except (PublicationError, FileNotFoundError, OSError, ValueError) as exc:
        print(f"PUBLICATION_STAGE_FAILED: {exc}")
        return 2

    print(
        json.dumps(
            {
                "destination": str(result.destination),
                "checkpoint_name": result.checkpoint_name,
                "checkpoint_sha256": result.checkpoint_sha256,
                "catalog_sha256": result.catalog_sha256,
                "manifest": str(result.manifest_path),
                "secret_scan": "PASS",
                "push_performed": False,
            },
            sort_keys=True,
        )
    )
    return 0


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("--published-at-utc must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("--published-at-utc must include UTC timezone")
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("--published-at-utc must be UTC")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
