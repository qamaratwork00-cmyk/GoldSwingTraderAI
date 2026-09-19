"""Run fixed-policy walk-forward validation from a verified dataset bundle.

This command is deliberately an offline research boundary. It verifies the
portable dataset before replay, never touches MT5, never tunes production
parameters, and emits an immutable evidence package whose dataset identity is
bound to the supplied bundle.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from goldswingtraderai.domain.enums import Timeframe
from goldswingtraderai.research.datasets import (
    DatasetBundleError,
    ImportedDatasetBundle,
    import_replay_dataset_bundle,
)
from goldswingtraderai.research.evidence import (
    ReplayDatasetIdentity,
    build_research_evidence_manifest,
    identify_replay_dataset,
)
from goldswingtraderai.research.packages import (
    EvidencePackageError,
    export_research_evidence_package,
)
from goldswingtraderai.research.validation import (
    build_walk_forward_windows,
    run_walk_forward_validation,
)


_DEFAULT_LIMITATIONS = (
    "BAR_CLOSE_RESEARCH_MODEL_NOT_TICK_EXECUTION",
    "HISTORICAL_SESSION_SCHEDULE_NOT_SUPPLIED",
    "FINAL_HOLDOUT_NOT_CONSUMED_BY_THIS_RUN",
    "DEMO_FORWARD_EVIDENCE_NOT_INCLUDED",
    "BROKER_EXECUTION_CERTIFICATION_NOT_INCLUDED",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run fixed-policy walk-forward validation on a verified dataset bundle"
    )
    parser.add_argument("dataset_bundle", type=Path)
    parser.add_argument("evidence_package", type=Path)
    parser.add_argument("--development-events", type=_positive_int, required=True)
    parser.add_argument("--validation-events", type=_positive_int, required=True)
    parser.add_argument("--step-events", type=_positive_int)
    parser.add_argument("--max-windows", type=_positive_int)
    parser.add_argument("--horizon-m5-bars", type=_positive_int, default=96)
    parser.add_argument(
        "--minimum-bars",
        action="append",
        default=[],
        metavar="TIMEFRAME=COUNT",
        help="minimum completed bars, repeat for H4/H1/M15/M5/M1",
    )
    parser.add_argument("--start-utc", help="optional ISO-8601 UTC event boundary")
    parser.add_argument("--end-utc", help="optional ISO-8601 UTC event boundary")
    parser.add_argument(
        "--without-stress",
        action="store_true",
        help="omit declared execution-stress replay from the evidence report",
    )
    parser.add_argument("--code-revision", required=True)
    parser.add_argument("--policy-version", required=True)
    parser.add_argument(
        "--generated-at-utc",
        help="optional ISO-8601 UTC timestamp; defaults to current UTC time",
    )
    args = parser.parse_args(argv)

    try:
        minimum_bars = _parse_minimum_bars(args.minimum_bars)
        start_utc = _parse_utc(args.start_utc, "--start-utc") if args.start_utc else None
        end_utc = _parse_utc(args.end_utc, "--end-utc") if args.end_utc else None
        generated_at = (
            _parse_utc(args.generated_at_utc, "--generated-at-utc")
            if args.generated_at_utc
            else datetime.now(timezone.utc)
        )
        imported = import_replay_dataset_bundle(args.dataset_bundle)
        windows = build_walk_forward_windows(
            imported.dataset,
            development_events=args.development_events,
            validation_events=args.validation_events,
            step_events=args.step_events,
            minimum_bars=minimum_bars,
            start_utc=start_utc,
            end_utc=end_utc,
            max_windows=args.max_windows,
        )
        report = run_walk_forward_validation(
            imported.dataset,
            windows,
            minimum_bars=minimum_bars,
            horizon_m5_bars=args.horizon_m5_bars,
            include_stress=not args.without_stress,
        )
        evidence = build_research_evidence_manifest(
            _imported_identity(imported),
            evidence_kind=report.mode.value,
            generated_at_utc=generated_at,
            code_revision=args.code_revision,
            policy_version=args.policy_version,
            configuration={
                "dataset_bundle_manifest_sha256": imported.manifest_sha256,
                "development_events": args.development_events,
                "validation_events": args.validation_events,
                "step_events": args.step_events,
                "max_windows": args.max_windows,
                "horizon_m5_bars": args.horizon_m5_bars,
                "minimum_bars": {
                    timeframe.value: count for timeframe, count in minimum_bars.items()
                },
                "start_utc": start_utc,
                "end_utc": end_utc,
                "include_stress": not args.without_stress,
            },
            results={"walk_forward_report": report},
            limitations=_DEFAULT_LIMITATIONS,
        )
        exported = export_research_evidence_package(
            evidence,
            args.evidence_package,
            dataset_bundle=args.dataset_bundle,
        )
    except (
        DatasetBundleError,
        EvidencePackageError,
        FileExistsError,
        FileNotFoundError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"WALK_FORWARD_FAILED: {exc}")
        return 2

    print(
        json.dumps(
            {
                "evidence_package": str(exported.path),
                "package_sha256": exported.package_sha256,
                "evidence_manifest_sha256": exported.evidence_manifest_sha256,
                "dataset_sha256": exported.dataset_sha256,
                "dataset_source_label": imported.source_label,
                "dataset_source_version": imported.source_version,
                "mode": report.mode.value,
                "windows": len(report.evaluations),
                "validation_events": report.validation_events,
                "enter_signals": report.enter_signals,
                "resolved_management_net_r": report.resolved_management_net_r,
                "trading_authority_granted": False,
            },
            sort_keys=True,
        )
    )
    return 0


def _imported_identity(imported: ImportedDatasetBundle) -> ReplayDatasetIdentity:
    """Return the identity already verified by the portable bundle importer."""

    return identify_replay_dataset(
        imported.dataset,
        source_label=imported.source_label,
        source_version=imported.source_version,
    )


def _parse_minimum_bars(values: list[str]) -> dict[Timeframe, int]:
    parsed: dict[Timeframe, int] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError("--minimum-bars must use TIMEFRAME=COUNT")
        raw_timeframe, raw_count = raw.split("=", 1)
        try:
            timeframe = Timeframe(raw_timeframe.strip().upper())
        except ValueError as exc:
            raise ValueError(f"unsupported timeframe in --minimum-bars: {raw_timeframe!r}") from exc
        if timeframe in parsed:
            raise ValueError(f"duplicate --minimum-bars timeframe: {timeframe.value}")
        try:
            parsed[timeframe] = _positive_int(raw_count)
        except argparse.ArgumentTypeError as exc:
            raise ValueError(f"invalid --minimum-bars count: {raw_count!r}") from exc
    return parsed


def _parse_utc(value: str, option: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{option} must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{option} must include UTC timezone")
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{option} must be UTC")
    return parsed


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
