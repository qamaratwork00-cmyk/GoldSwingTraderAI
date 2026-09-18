from datetime import datetime, timedelta, timezone
import json

import pytest

from goldswingtraderai.domain.enums import AccountMode, Timeframe
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, SymbolSpec
from goldswingtraderai.research.datasets import (
    DatasetBundleIntegrityError,
    export_replay_dataset_bundle,
    import_replay_dataset_bundle,
)
from goldswingtraderai.research.evidence import identify_replay_dataset
from goldswingtraderai.research.replay import ReplayDataset


START = datetime(2026, 1, 5, 0, 0, tzinfo=timezone.utc)
_PERIODS = {
    Timeframe.H4: timedelta(hours=4),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.M5: timedelta(minutes=5),
    Timeframe.M1: timedelta(minutes=1),
}


def _series(timeframe: Timeframe, count: int) -> CandleSeries:
    period = _PERIODS[timeframe]
    candles = []
    for index in range(count):
        base = 2300.0 + index * 0.25
        candles.append(
            Candle(
                time_utc=START + period * index,
                open=base,
                high=base + 0.8,
                low=base - 0.6,
                close=base + 0.2,
                tick_volume=100 + index,
                spread_points=20 + index % 3,
                real_volume=50 + index,
            )
        )
    return CandleSeries(timeframe=timeframe, candles=tuple(candles))


def _dataset(*, include_m1: bool = False) -> ReplayDataset:
    series = [
        _series(Timeframe.H4, 8),
        _series(Timeframe.H1, 10),
        _series(Timeframe.M15, 12),
        _series(Timeframe.M5, 14),
    ]
    if include_m1:
        series.append(_series(Timeframe.M1, 16))
    return ReplayDataset(
        account=AccountFacts(
            login=987654,
            server="Broker-Demo-PrivateEndpoint",
            currency="USD",
            mode=AccountMode.DEMO,
            balance=100.0,
            equity=98.5,
            margin=4.0,
            margin_free=94.5,
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
        series=tuple(series),
        spread_price=0.20,
    )


def test_dataset_bundle_round_trip_preserves_content_identity_and_optional_m1(tmp_path) -> None:
    dataset = _dataset(include_m1=True)
    expected = identify_replay_dataset(
        dataset,
        source_label="fixture-xau",
        source_version="2026-01-v1",
    )
    target = tmp_path / "xau-bundle"

    exported = export_replay_dataset_bundle(
        dataset,
        target,
        source_label="fixture-xau",
        source_version="2026-01-v1",
    )
    imported = import_replay_dataset_bundle(target)

    assert exported.dataset_sha256 == expected.dataset_sha256
    assert imported.dataset_sha256 == expected.dataset_sha256
    assert imported.source_label == "fixture-xau"
    assert imported.source_version == "2026-01-v1"
    assert {item.timeframe for item in imported.dataset.series} == {
        Timeframe.H4,
        Timeframe.H1,
        Timeframe.M15,
        Timeframe.M5,
        Timeframe.M1,
    }
    assert imported.dataset.account.login == 1
    assert imported.dataset.account.server == "RESEARCH_DATASET"


def test_dataset_bundle_manifest_does_not_export_broker_endpoint_identity(tmp_path) -> None:
    target = tmp_path / "bundle"
    export_replay_dataset_bundle(
        _dataset(),
        target,
        source_label="public-research",
        source_version="v1",
    )

    raw = (target / "dataset_manifest.json").read_text(encoding="utf-8")
    manifest = json.loads(raw)

    assert "987654" not in raw
    assert "Broker-Demo-PrivateEndpoint" not in raw
    assert "login" not in manifest["account_context"]
    assert "server" not in manifest["account_context"]


def test_dataset_bundle_detects_csv_tampering_before_import(tmp_path) -> None:
    target = tmp_path / "bundle"
    export_replay_dataset_bundle(
        _dataset(),
        target,
        source_label="fixture-xau",
        source_version="v1",
    )
    m5 = target / "M5.csv"
    m5.write_text(m5.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")

    with pytest.raises(DatasetBundleIntegrityError, match="checksum mismatch"):
        import_replay_dataset_bundle(target)


def test_dataset_bundle_detects_manifest_tampering(tmp_path) -> None:
    target = tmp_path / "bundle"
    export_replay_dataset_bundle(
        _dataset(),
        target,
        source_label="fixture-xau",
        source_version="v1",
    )
    manifest_path = target / "dataset_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["source_version"] = "tampered-v2"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DatasetBundleIntegrityError, match="manifest checksum mismatch"):
        import_replay_dataset_bundle(target)


def test_dataset_bundle_export_never_overwrites_existing_destination(tmp_path) -> None:
    target = tmp_path / "bundle"
    export_replay_dataset_bundle(
        _dataset(),
        target,
        source_label="fixture-xau",
        source_version="v1",
    )

    with pytest.raises(FileExistsError):
        export_replay_dataset_bundle(
            _dataset(),
            target,
            source_label="fixture-xau",
            source_version="v2",
        )
