from datetime import datetime, timedelta, timezone
import json

import pytest

from goldswingtraderai.domain.enums import AccountMode, Timeframe
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, SymbolSpec
from goldswingtraderai.research.datasets import export_replay_dataset_bundle
from goldswingtraderai.research.evidence import (
    build_research_evidence_manifest,
    identify_replay_dataset,
)
from goldswingtraderai.research.packages import (
    EvidencePackageIntegrityError,
    export_research_evidence_package,
    import_research_evidence_package,
)
from goldswingtraderai.research.replay import ReplayDataset


START = datetime(2026, 1, 5, 0, 0, tzinfo=timezone.utc)
_PERIODS = {
    Timeframe.H4: timedelta(hours=4),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.M5: timedelta(minutes=5),
}


def _series(timeframe: Timeframe, count: int, *, offset: float = 0.0) -> CandleSeries:
    candles = []
    for index in range(count):
        base = 2300.0 + offset + index * 0.2
        candles.append(
            Candle(
                time_utc=START + _PERIODS[timeframe] * index,
                open=base,
                high=base + 0.7,
                low=base - 0.5,
                close=base + 0.1,
                tick_volume=100 + index,
                spread_points=20,
            )
        )
    return CandleSeries(timeframe=timeframe, candles=tuple(candles))


def _dataset(*, offset: float = 0.0) -> ReplayDataset:
    return ReplayDataset(
        account=AccountFacts(
            login=123456,
            server="Demo-Server",
            currency="USD",
            mode=AccountMode.DEMO,
            balance=100.0,
            equity=100.0,
            margin=0.0,
            margin_free=100.0,
            leverage=500,
        ),
        symbol_spec=SymbolSpec(
            symbol="XAUUSDm",
            digits=3,
            point=0.001,
            tick_size=0.001,
            tick_value=0.01,
            contract_size=100.0,
            volume_min=0.01,
            volume_max=200.0,
            volume_step=0.01,
            stops_level_points=0,
            freeze_level_points=0,
        ),
        series=tuple(
            _series(timeframe, 8, offset=offset)
            for timeframe in (Timeframe.H4, Timeframe.H1, Timeframe.M15, Timeframe.M5)
        ),
        spread_price=0.20,
    )


def _evidence(dataset: ReplayDataset):
    identity = identify_replay_dataset(
        dataset,
        source_label="fixture-xau",
        source_version="v1",
    )
    return build_research_evidence_manifest(
        identity,
        evidence_kind="FIXED_POLICY_WALK_FORWARD",
        generated_at_utc=datetime(2026, 9, 18, 17, 0, tzinfo=timezone.utc),
        code_revision="abc123",
        policy_version="policy-v1",
        configuration={"development_events": 100, "validation_events": 25},
        results={"windows": 4, "resolved_net_r": 2.5},
        limitations=("BAR_CLOSE research model",),
    )


def test_evidence_package_round_trip_binds_verified_dataset_bundle(tmp_path) -> None:
    dataset = _dataset()
    bundle = export_replay_dataset_bundle(
        dataset,
        tmp_path / "dataset",
        source_label="fixture-xau",
        source_version="v1",
    )
    evidence = _evidence(dataset)

    exported = export_research_evidence_package(
        evidence,
        tmp_path / "evidence",
        dataset_bundle=bundle.path,
    )
    imported = import_research_evidence_package(
        exported.path,
        dataset_bundle=bundle.path,
    )

    assert imported.dataset_sha256 == evidence.dataset.dataset_sha256
    assert imported.evidence_manifest_sha256 == evidence.manifest_sha256
    assert imported.input_fingerprint_sha256 == evidence.input_fingerprint_sha256
    assert imported.dataset_bundle_manifest_sha256 == bundle.manifest_sha256
    assert imported.evidence_payload["results"]["resolved_net_r"] == 2.5


def test_evidence_package_can_reference_dataset_identity_without_copying_bundle(tmp_path) -> None:
    evidence = _evidence(_dataset())
    exported = export_research_evidence_package(evidence, tmp_path / "evidence")
    imported = import_research_evidence_package(exported.path)

    assert imported.dataset_sha256 == evidence.dataset.dataset_sha256
    assert imported.dataset_bundle_manifest_sha256 is None
    assert not (exported.path / "dataset").exists()


def test_evidence_package_rejects_mismatched_dataset_bundle(tmp_path) -> None:
    evidence = _evidence(_dataset())
    other = _dataset(offset=10.0)
    bundle = export_replay_dataset_bundle(
        other,
        tmp_path / "other-dataset",
        source_label="fixture-xau",
        source_version="v1",
    )

    with pytest.raises(EvidencePackageIntegrityError, match="does not match evidence dataset"):
        export_research_evidence_package(
            evidence,
            tmp_path / "evidence",
            dataset_bundle=bundle.path,
        )


def test_evidence_package_detects_evidence_file_tampering(tmp_path) -> None:
    exported = export_research_evidence_package(_evidence(_dataset()), tmp_path / "evidence")
    path = exported.path / "evidence_manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["results"]["resolved_net_r"] = 999.0
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(EvidencePackageIntegrityError, match="file checksum mismatch"):
        import_research_evidence_package(exported.path)


def test_evidence_package_detects_package_manifest_tampering_and_no_overwrite(tmp_path) -> None:
    evidence = _evidence(_dataset())
    exported = export_research_evidence_package(evidence, tmp_path / "evidence")

    with pytest.raises(FileExistsError):
        export_research_evidence_package(evidence, exported.path)

    path = exported.path / "package_manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["dataset_sha256"] = "0" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(EvidencePackageIntegrityError, match="package manifest checksum mismatch"):
        import_research_evidence_package(exported.path)
