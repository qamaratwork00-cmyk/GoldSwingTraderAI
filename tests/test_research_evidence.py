from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from goldswingtraderai.domain.enums import AccountMode, Timeframe
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, SymbolSpec
from goldswingtraderai.research.evidence import (
    build_research_evidence_manifest,
    canonical_manifest_json,
    identify_replay_dataset,
)
from goldswingtraderai.research.replay import ReplayDataset


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
_PERIODS = {
    Timeframe.H4: timedelta(hours=4),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.M5: timedelta(minutes=5),
}


def _series(timeframe: Timeframe, count: int = 4) -> CandleSeries:
    period = _PERIODS[timeframe]
    candles = []
    for index in range(count):
        close = 2300.0 + index + timeframe.value.count("M") * 0.01
        candles.append(
            Candle(
                time_utc=NOW - period * (count - index),
                open=close - 0.2,
                high=close + 0.5,
                low=close - 0.5,
                close=close,
                tick_volume=100 + index,
                spread_points=20,
                real_volume=index,
            )
        )
    return CandleSeries(timeframe=timeframe, candles=tuple(candles))


def _dataset() -> ReplayDataset:
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
        series=(
            _series(Timeframe.H4),
            _series(Timeframe.H1),
            _series(Timeframe.M15),
            _series(Timeframe.M5),
        ),
        spread_price=0.20,
    )


def _identity(dataset: ReplayDataset | None = None):
    return identify_replay_dataset(
        dataset or _dataset(),
        source_label="unit-fixture",
        source_version="v1",
    )


def test_dataset_identity_is_stable_and_series_order_independent() -> None:
    dataset = _dataset()
    first = _identity(dataset)
    reordered = replace(dataset, series=tuple(reversed(dataset.series)))
    second = _identity(reordered)

    assert first.dataset_sha256 == second.dataset_sha256
    assert first.symbol_spec_sha256 == second.symbol_spec_sha256
    assert tuple(item.timeframe for item in first.timeframes) == tuple(
        sorted((Timeframe.H4, Timeframe.H1, Timeframe.M15, Timeframe.M5), key=lambda x: x.value)
    )


def test_dataset_identity_changes_when_market_content_changes() -> None:
    dataset = _dataset()
    original = _identity(dataset)
    m5 = next(item for item in dataset.series if item.timeframe is Timeframe.M5)
    latest = m5.candles[-1]
    changed_latest = replace(
        latest,
        high=latest.high + 0.25,
        close=latest.close + 0.10,
    )
    changed_m5 = replace(m5, candles=(*m5.candles[:-1], changed_latest))
    changed = replace(
        dataset,
        series=tuple(changed_m5 if item.timeframe is Timeframe.M5 else item for item in dataset.series),
    )

    assert _identity(changed).dataset_sha256 != original.dataset_sha256


def test_account_endpoint_identity_is_not_part_of_replay_dataset_hash() -> None:
    dataset = _dataset()
    changed_account = replace(dataset.account, login=999999, server="Other-Demo")
    changed = replace(dataset, account=changed_account)

    assert _identity(changed).dataset_sha256 == _identity(dataset).dataset_sha256
    assert _identity(changed).account_context_sha256 == _identity(dataset).account_context_sha256


def test_manifest_input_fingerprint_is_reproducible_but_full_manifest_tracks_results() -> None:
    identity = _identity()
    first = build_research_evidence_manifest(
        identity,
        evidence_kind="WALK_FORWARD",
        generated_at_utc=NOW,
        code_revision="0480658f7604e8847047d59a8485c9efc158750a",
        policy_version="policy-v1",
        configuration={
            "development_events": 100,
            "validation_events": 25,
            "stress": {"enabled": True, "variants": ["BASE", "COMBINED"]},
        },
        results={"validation_events": 25, "resolved_net_r": 1.5},
        limitations=("BAR_CLOSE research",),
    )
    second = build_research_evidence_manifest(
        identity,
        evidence_kind="WALK_FORWARD",
        generated_at_utc=NOW + timedelta(minutes=1),
        code_revision="0480658f7604e8847047d59a8485c9efc158750a",
        policy_version="policy-v1",
        configuration={
            "stress": {"variants": ["BASE", "COMBINED"], "enabled": True},
            "validation_events": 25,
            "development_events": 100,
        },
        results={"validation_events": 25, "resolved_net_r": 2.0},
        limitations=("BAR_CLOSE research",),
    )

    assert first.input_fingerprint_sha256 == second.input_fingerprint_sha256
    assert first.manifest_sha256 != second.manifest_sha256
    payload = json.loads(canonical_manifest_json(first))
    assert payload["dataset"]["dataset_sha256"] == identity.dataset_sha256
    assert payload["input_fingerprint_sha256"] == first.input_fingerprint_sha256


def test_manifest_rejects_financial_secret_shaped_fields() -> None:
    identity = _identity()

    with pytest.raises(ValueError, match="FINANCIAL_SECRET_DETECTED"):
        build_research_evidence_manifest(
            identity,
            evidence_kind="STRESS",
            generated_at_utc=NOW,
            code_revision="abc123",
            policy_version="policy-v1",
            configuration={"broker_api_key": "must-not-be-recorded"},
            results={},
        )
