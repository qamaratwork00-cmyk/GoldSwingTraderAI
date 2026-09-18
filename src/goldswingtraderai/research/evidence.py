"""Deterministic identities and manifests for reproducible research evidence.

The manifest records *what was tested* without granting any trading authority.
Dataset identity is content-addressed from replay-relevant market/account geometry,
not from a mutable filename. Evidence input fingerprints exclude generation time and
results so the same experiment inputs can be recognized across repeated runs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping

from goldswingtraderai.domain.enums import Timeframe
from goldswingtraderai.research.replay import ReplayDataset


EVIDENCE_SCHEMA_VERSION = 1

_FORBIDDEN_KEY_TOKENS = {
    "password",
    "passwd",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "private_key",
    "secret_key",
    "client_secret",
    "github_token",
    "broker_token",
}


@dataclass(frozen=True, slots=True)
class TimeframeDatasetIdentity:
    timeframe: Timeframe
    bars: int
    first_open_utc: datetime
    last_open_utc: datetime
    content_sha256: str

    def __post_init__(self) -> None:
        if self.bars <= 0:
            raise ValueError("dataset timeframe identity requires positive bar count")
        _require_utc(self.first_open_utc)
        _require_utc(self.last_open_utc)
        if self.last_open_utc < self.first_open_utc:
            raise ValueError("dataset timeframe range is invalid")
        _require_sha256(self.content_sha256, "timeframe content hash")


@dataclass(frozen=True, slots=True)
class ReplayDatasetIdentity:
    source_label: str
    source_version: str
    symbol: str
    realism: str
    spread_price: float
    dataset_sha256: str
    symbol_spec_sha256: str
    account_context_sha256: str
    timeframes: tuple[TimeframeDatasetIdentity, ...]

    def __post_init__(self) -> None:
        _required_text(self.source_label, "source label")
        _required_text(self.source_version, "source version")
        _required_text(self.symbol, "symbol")
        _required_text(self.realism, "realism")
        if self.spread_price < 0 or not isfinite(self.spread_price):
            raise ValueError("dataset identity spread must be finite and non-negative")
        _require_sha256(self.dataset_sha256, "dataset hash")
        _require_sha256(self.symbol_spec_sha256, "symbol-spec hash")
        _require_sha256(self.account_context_sha256, "account-context hash")
        if not self.timeframes:
            raise ValueError("dataset identity requires timeframe identities")
        frames = tuple(item.timeframe for item in self.timeframes)
        if frames != tuple(sorted(frames, key=lambda item: item.value)):
            raise ValueError("dataset timeframe identities must use canonical order")
        if len(frames) != len(set(frames)):
            raise ValueError("dataset timeframe identities cannot repeat")


@dataclass(frozen=True, slots=True)
class ResearchEvidenceManifest:
    schema_version: int
    evidence_kind: str
    generated_at_utc: datetime
    code_revision: str
    policy_version: str
    dataset: ReplayDatasetIdentity
    configuration: dict[str, Any]
    results: dict[str, Any]
    limitations: tuple[str, ...]
    input_fingerprint_sha256: str
    manifest_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != EVIDENCE_SCHEMA_VERSION:
            raise ValueError("unsupported research evidence schema version")
        _required_text(self.evidence_kind, "evidence kind")
        _require_utc(self.generated_at_utc)
        _required_text(self.code_revision, "code revision")
        _required_text(self.policy_version, "policy version")
        _require_sha256(self.input_fingerprint_sha256, "input fingerprint")
        _require_sha256(self.manifest_sha256, "manifest hash")
        if any(not item.strip() for item in self.limitations):
            raise ValueError("evidence limitations cannot contain blank entries")


def identify_replay_dataset(
    dataset: ReplayDataset,
    *,
    source_label: str,
    source_version: str,
) -> ReplayDatasetIdentity:
    """Create a deterministic content identity for replay-relevant dataset facts."""

    label = _required_text(source_label, "source label")
    version = _required_text(source_version, "source version")

    symbol_payload = {
        "symbol": dataset.symbol_spec.symbol,
        "digits": dataset.symbol_spec.digits,
        "point": dataset.symbol_spec.point,
        "tick_size": dataset.symbol_spec.tick_size,
        "tick_value": dataset.symbol_spec.tick_value,
        "contract_size": dataset.symbol_spec.contract_size,
        "volume_min": dataset.symbol_spec.volume_min,
        "volume_max": dataset.symbol_spec.volume_max,
        "volume_step": dataset.symbol_spec.volume_step,
        "stops_level_points": dataset.symbol_spec.stops_level_points,
        "freeze_level_points": dataset.symbol_spec.freeze_level_points,
    }
    # Login/server are intentionally excluded: they identify an account endpoint,
    # not the economic starting context required to reproduce replay calculations.
    account_payload = {
        "currency": dataset.account.currency,
        "mode": dataset.account.mode.value,
        "balance": dataset.account.balance,
        "equity": dataset.account.equity,
        "margin": dataset.account.margin,
        "margin_free": dataset.account.margin_free,
        "leverage": dataset.account.leverage,
    }

    timeframe_identities: list[TimeframeDatasetIdentity] = []
    canonical_series: list[dict[str, Any]] = []
    for series in sorted(dataset.series, key=lambda item: item.timeframe.value):
        candle_payload = [
            {
                "time_utc": candle.time_utc.isoformat(),
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "tick_volume": candle.tick_volume,
                "spread_points": candle.spread_points,
                "real_volume": candle.real_volume,
            }
            for candle in series.candles
        ]
        digest = _hash_payload(candle_payload)
        timeframe_identities.append(
            TimeframeDatasetIdentity(
                timeframe=series.timeframe,
                bars=len(series.candles),
                first_open_utc=series.candles[0].time_utc,
                last_open_utc=series.candles[-1].time_utc,
                content_sha256=digest,
            )
        )
        canonical_series.append(
            {
                "timeframe": series.timeframe.value,
                "candles": candle_payload,
            }
        )

    symbol_hash = _hash_payload(symbol_payload)
    account_hash = _hash_payload(account_payload)
    dataset_payload = {
        "source_label": label,
        "source_version": version,
        "realism": dataset.realism.value,
        "spread_price": dataset.spread_price,
        "symbol_spec": symbol_payload,
        "account_context": account_payload,
        "series": canonical_series,
    }
    return ReplayDatasetIdentity(
        source_label=label,
        source_version=version,
        symbol=dataset.symbol_spec.symbol,
        realism=dataset.realism.value,
        spread_price=dataset.spread_price,
        dataset_sha256=_hash_payload(dataset_payload),
        symbol_spec_sha256=symbol_hash,
        account_context_sha256=account_hash,
        timeframes=tuple(timeframe_identities),
    )


def build_research_evidence_manifest(
    dataset_identity: ReplayDatasetIdentity,
    *,
    evidence_kind: str,
    generated_at_utc: datetime,
    code_revision: str,
    policy_version: str,
    configuration: Mapping[str, Any],
    results: Mapping[str, Any],
    limitations: tuple[str, ...] = (),
) -> ResearchEvidenceManifest:
    """Build a deterministic, secret-rejecting research evidence manifest.

    ``input_fingerprint_sha256`` identifies the experiment inputs and therefore
    intentionally excludes generation time and results. ``manifest_sha256`` covers
    the complete evidence record except its own hash field.
    """

    _require_utc(generated_at_utc)
    kind = _required_text(evidence_kind, "evidence kind")
    revision = _required_text(code_revision, "code revision")
    policy = _required_text(policy_version, "policy version")
    config = _normalize_mapping(configuration, path="configuration")
    result_payload = _normalize_mapping(results, path="results")
    cleaned_limitations = tuple(_required_text(item, "limitation") for item in limitations)

    dataset_payload = _dataset_identity_payload(dataset_identity)
    input_payload = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "evidence_kind": kind,
        "code_revision": revision,
        "policy_version": policy,
        "dataset": dataset_payload,
        "configuration": config,
    }
    input_fingerprint = _hash_payload(input_payload)

    complete_payload = {
        **input_payload,
        "generated_at_utc": generated_at_utc.isoformat(),
        "results": result_payload,
        "limitations": list(cleaned_limitations),
        "input_fingerprint_sha256": input_fingerprint,
    }
    manifest_hash = _hash_payload(complete_payload)
    return ResearchEvidenceManifest(
        schema_version=EVIDENCE_SCHEMA_VERSION,
        evidence_kind=kind,
        generated_at_utc=generated_at_utc,
        code_revision=revision,
        policy_version=policy,
        dataset=dataset_identity,
        configuration=config,
        results=result_payload,
        limitations=cleaned_limitations,
        input_fingerprint_sha256=input_fingerprint,
        manifest_sha256=manifest_hash,
    )


def manifest_payload(manifest: ResearchEvidenceManifest) -> dict[str, Any]:
    """Return the canonical public-serializable representation of one manifest."""

    return {
        "schema_version": manifest.schema_version,
        "evidence_kind": manifest.evidence_kind,
        "generated_at_utc": manifest.generated_at_utc.isoformat(),
        "code_revision": manifest.code_revision,
        "policy_version": manifest.policy_version,
        "dataset": _dataset_identity_payload(manifest.dataset),
        "configuration": manifest.configuration,
        "results": manifest.results,
        "limitations": list(manifest.limitations),
        "input_fingerprint_sha256": manifest.input_fingerprint_sha256,
        "manifest_sha256": manifest.manifest_sha256,
    }


def canonical_manifest_json(manifest: ResearchEvidenceManifest) -> str:
    """Serialize a manifest reproducibly for checkpoint/export tooling."""

    return _canonical_json(manifest_payload(manifest))


def _dataset_identity_payload(identity: ReplayDatasetIdentity) -> dict[str, Any]:
    return {
        "source_label": identity.source_label,
        "source_version": identity.source_version,
        "symbol": identity.symbol,
        "realism": identity.realism,
        "spread_price": identity.spread_price,
        "dataset_sha256": identity.dataset_sha256,
        "symbol_spec_sha256": identity.symbol_spec_sha256,
        "account_context_sha256": identity.account_context_sha256,
        "timeframes": [
            {
                "timeframe": item.timeframe.value,
                "bars": item.bars,
                "first_open_utc": item.first_open_utc.isoformat(),
                "last_open_utc": item.last_open_utc.isoformat(),
                "content_sha256": item.content_sha256,
            }
            for item in identity.timeframes
        ],
    }


def _normalize_mapping(value: Mapping[str, Any], *, path: str) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for raw_key in sorted(value):
        if not isinstance(raw_key, str) or not raw_key.strip():
            raise ValueError(f"{path} keys must be non-empty strings")
        key = raw_key.strip()
        _reject_secret_key(key, path)
        normalized[key] = _normalize_value(value[raw_key], path=f"{path}.{key}")
    return normalized


def _normalize_value(value: Any, *, path: str) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{path} must not contain non-finite numbers")
        return value
    if isinstance(value, datetime):
        _require_utc(value)
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return _normalize_mapping(value, path=path)
    if isinstance(value, (tuple, list)):
        return [_normalize_value(item, path=f"{path}[]") for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return _normalize_mapping(asdict(value), path=path)
    raise TypeError(f"unsupported evidence value at {path}: {type(value).__name__}")


def _reject_secret_key(key: str, path: str) -> None:
    lowered = key.lower().replace("-", "_").replace(" ", "_")
    if any(token in lowered for token in _FORBIDDEN_KEY_TOKENS):
        raise ValueError(f"FINANCIAL_SECRET_DETECTED in evidence key {path}.{key}")


def _hash_payload(payload: Any) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _require_sha256(value: str, name: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be lowercase SHA-256 hex")


def _required_text(value: str, name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{name} cannot be empty")
    return cleaned


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("evidence timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("evidence timestamp must be UTC")
