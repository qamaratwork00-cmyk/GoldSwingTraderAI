"""Portable, integrity-checked replay dataset bundles for offline research.

A bundle is intentionally boring and inspectable: one canonical JSON manifest plus
one UTF-8 CSV per timeframe. Broker endpoint identifiers/credentials are not
exported. Import reconstructs a neutral offline AccountFacts endpoint and verifies
file hashes plus the content-addressed ReplayDataset identity before returning data.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from goldswingtraderai.domain.enums import AccountMode, Timeframe
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, SymbolSpec
from goldswingtraderai.research.evidence import identify_replay_dataset
from goldswingtraderai.research.replay import ReplayDataset, ReplayRealism


DATASET_BUNDLE_SCHEMA_VERSION = 1
_MANIFEST_NAME = "dataset_manifest.json"
_REQUIRED_TIMEFRAMES = frozenset({Timeframe.H4, Timeframe.H1, Timeframe.M15, Timeframe.M5})
_CSV_HEADER = (
    "time_utc",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread_points",
    "real_volume",
)


class DatasetBundleError(RuntimeError):
    """Base portable-dataset error."""


class DatasetBundleIntegrityError(DatasetBundleError):
    """Bundle bytes or recomputed identity do not match the manifest."""


class DatasetBundleVersionError(DatasetBundleError):
    """Bundle schema is unsupported."""


@dataclass(frozen=True, slots=True)
class ExportedDatasetBundle:
    path: Path
    dataset_sha256: str
    manifest_sha256: str


@dataclass(frozen=True, slots=True)
class ImportedDatasetBundle:
    dataset: ReplayDataset
    source_label: str
    source_version: str
    dataset_sha256: str
    manifest_sha256: str


def export_replay_dataset_bundle(
    dataset: ReplayDataset,
    destination: str | Path,
    *,
    source_label: str,
    source_version: str,
) -> ExportedDatasetBundle:
    """Export one immutable research bundle; existing destinations are not replaced."""

    target = Path(destination)
    if target.exists():
        raise FileExistsError(f"dataset bundle destination already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)

    identity = identify_replay_dataset(
        dataset,
        source_label=source_label,
        source_version=source_version,
    )
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.tmp-", dir=str(target.parent))
    )
    try:
        files: dict[str, dict[str, Any]] = {}
        for series in sorted(dataset.series, key=lambda item: item.timeframe.value):
            filename = f"{series.timeframe.value}.csv"
            filepath = temporary / filename
            _write_series_csv(series, filepath)
            files[series.timeframe.value] = {
                "file": filename,
                "sha256": _file_sha256(filepath),
                "bars": len(series.candles),
            }

        payload = {
            "schema_version": DATASET_BUNDLE_SCHEMA_VERSION,
            "source_label": identity.source_label,
            "source_version": identity.source_version,
            "dataset_sha256": identity.dataset_sha256,
            "symbol_spec_sha256": identity.symbol_spec_sha256,
            "account_context_sha256": identity.account_context_sha256,
            "realism": dataset.realism.value,
            "spread_price": dataset.spread_price,
            "symbol_spec": _symbol_spec_payload(dataset.symbol_spec),
            "account_context": _account_context_payload(dataset.account),
            "files": files,
        }
        manifest_sha256 = _payload_sha256(payload)
        manifest = {**payload, "manifest_sha256": manifest_sha256}
        (temporary / _MANIFEST_NAME).write_text(
            _canonical_json(manifest) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        temporary.rename(target)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    return ExportedDatasetBundle(
        path=target,
        dataset_sha256=identity.dataset_sha256,
        manifest_sha256=manifest_sha256,
    )


def import_replay_dataset_bundle(source: str | Path) -> ImportedDatasetBundle:
    """Load and verify a portable bundle before exposing a ReplayDataset."""

    root = Path(source)
    manifest_path = root / _MANIFEST_NAME
    if not root.is_dir() or not manifest_path.is_file() or manifest_path.is_symlink():
        raise DatasetBundleError("dataset bundle directory/manifest is missing or unsafe")

    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetBundleIntegrityError("dataset manifest is unreadable/invalid JSON") from exc
    if not isinstance(raw_manifest, dict):
        raise DatasetBundleIntegrityError("dataset manifest must be a JSON object")

    schema_version = raw_manifest.get("schema_version")
    if schema_version != DATASET_BUNDLE_SCHEMA_VERSION:
        raise DatasetBundleVersionError(
            f"unsupported dataset bundle schema: {schema_version!r}"
        )
    claimed_manifest_hash = _required_sha256(
        raw_manifest.get("manifest_sha256"),
        "manifest_sha256",
    )
    payload = dict(raw_manifest)
    payload.pop("manifest_sha256", None)
    if _payload_sha256(payload) != claimed_manifest_hash:
        raise DatasetBundleIntegrityError("dataset manifest checksum mismatch")

    source_label = _required_text(raw_manifest.get("source_label"), "source_label")
    source_version = _required_text(raw_manifest.get("source_version"), "source_version")
    claimed_dataset_hash = _required_sha256(
        raw_manifest.get("dataset_sha256"),
        "dataset_sha256",
    )
    claimed_symbol_hash = _required_sha256(
        raw_manifest.get("symbol_spec_sha256"),
        "symbol_spec_sha256",
    )
    claimed_account_hash = _required_sha256(
        raw_manifest.get("account_context_sha256"),
        "account_context_sha256",
    )

    symbol_spec = _symbol_spec_from_payload(_required_dict(raw_manifest, "symbol_spec"))
    account = _account_from_payload(_required_dict(raw_manifest, "account_context"))
    try:
        realism = ReplayRealism(_required_text(raw_manifest.get("realism"), "realism"))
    except ValueError as exc:
        raise DatasetBundleIntegrityError("dataset realism is unsupported") from exc
    spread_price = _required_nonnegative_float(raw_manifest.get("spread_price"), "spread_price")

    files_payload = _required_dict(raw_manifest, "files")
    parsed_files = _parse_file_entries(files_payload)
    present_timeframes = frozenset(parsed_files)
    if not _REQUIRED_TIMEFRAMES.issubset(present_timeframes):
        missing = sorted(frame.value for frame in _REQUIRED_TIMEFRAMES - present_timeframes)
        raise DatasetBundleIntegrityError(
            f"dataset manifest missing required timeframe files: {','.join(missing)}"
        )

    series: list[CandleSeries] = []
    seen_filenames: set[str] = set()
    for timeframe in sorted(parsed_files, key=lambda item: item.value):
        item = parsed_files[timeframe]
        filename = _required_text(item.get("file"), f"files.{timeframe.value}.file")
        expected_filename = f"{timeframe.value}.csv"
        if filename != expected_filename:
            raise DatasetBundleIntegrityError(
                f"dataset CSV filename must be canonical: {expected_filename}"
            )
        if filename in seen_filenames:
            raise DatasetBundleIntegrityError("dataset manifest repeats a CSV filename")
        seen_filenames.add(filename)

        filepath = root / filename
        if not filepath.is_file() or filepath.is_symlink():
            raise DatasetBundleIntegrityError(f"dataset CSV missing or unsafe: {filename}")
        claimed_file_hash = _required_sha256(
            item.get("sha256"),
            f"files.{timeframe.value}.sha256",
        )
        if _file_sha256(filepath) != claimed_file_hash:
            raise DatasetBundleIntegrityError(f"dataset CSV checksum mismatch: {filename}")
        loaded = _read_series_csv(timeframe, filepath)
        claimed_bars = item.get("bars")
        if not isinstance(claimed_bars, int) or isinstance(claimed_bars, bool) or claimed_bars <= 0:
            raise DatasetBundleIntegrityError(f"invalid bar count for {timeframe.value}")
        if len(loaded.candles) != claimed_bars:
            raise DatasetBundleIntegrityError(
                f"dataset CSV bar count mismatch: {timeframe.value}"
            )
        series.append(loaded)

    dataset = ReplayDataset(
        account=account,
        symbol_spec=symbol_spec,
        series=tuple(series),
        spread_price=spread_price,
        realism=realism,
    )
    identity = identify_replay_dataset(
        dataset,
        source_label=source_label,
        source_version=source_version,
    )
    if identity.dataset_sha256 != claimed_dataset_hash:
        raise DatasetBundleIntegrityError("recomputed dataset identity mismatch")
    if identity.symbol_spec_sha256 != claimed_symbol_hash:
        raise DatasetBundleIntegrityError("recomputed symbol-spec identity mismatch")
    if identity.account_context_sha256 != claimed_account_hash:
        raise DatasetBundleIntegrityError("recomputed account-context identity mismatch")

    return ImportedDatasetBundle(
        dataset=dataset,
        source_label=source_label,
        source_version=source_version,
        dataset_sha256=identity.dataset_sha256,
        manifest_sha256=claimed_manifest_hash,
    )


def _parse_file_entries(payload: dict[str, Any]) -> dict[Timeframe, dict[str, Any]]:
    parsed: dict[Timeframe, dict[str, Any]] = {}
    for raw_timeframe, raw_entry in payload.items():
        if not isinstance(raw_timeframe, str):
            raise DatasetBundleIntegrityError("dataset file timeframe key must be text")
        try:
            timeframe = Timeframe(raw_timeframe)
        except ValueError as exc:
            raise DatasetBundleIntegrityError(
                f"unsupported dataset timeframe file: {raw_timeframe}"
            ) from exc
        if not isinstance(raw_entry, dict):
            raise DatasetBundleIntegrityError(
                f"dataset file entry must be object: {raw_timeframe}"
            )
        parsed[timeframe] = raw_entry
    return parsed


def _write_series_csv(series: CandleSeries, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(_CSV_HEADER)
        for candle in series.candles:
            writer.writerow(
                (
                    candle.time_utc.isoformat(),
                    repr(candle.open),
                    repr(candle.high),
                    repr(candle.low),
                    repr(candle.close),
                    candle.tick_volume,
                    candle.spread_points,
                    candle.real_volume,
                )
            )


def _read_series_csv(timeframe: Timeframe, path: Path) -> CandleSeries:
    candles: list[Candle] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _CSV_HEADER:
                raise DatasetBundleIntegrityError(f"unexpected CSV header: {path.name}")
            for row_number, row in enumerate(reader, start=2):
                try:
                    candles.append(
                        Candle(
                            time_utc=datetime.fromisoformat(row["time_utc"]),
                            open=float(row["open"]),
                            high=float(row["high"]),
                            low=float(row["low"]),
                            close=float(row["close"]),
                            tick_volume=int(row["tick_volume"]),
                            spread_points=int(row["spread_points"]),
                            real_volume=int(row["real_volume"]),
                        )
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    raise DatasetBundleIntegrityError(
                        f"invalid candle row {row_number} in {path.name}"
                    ) from exc
    except OSError as exc:
        raise DatasetBundleIntegrityError(f"cannot read dataset CSV: {path.name}") from exc
    if not candles:
        raise DatasetBundleIntegrityError(f"dataset CSV is empty: {path.name}")
    return CandleSeries(timeframe=timeframe, candles=tuple(candles))


def _symbol_spec_payload(spec: SymbolSpec) -> dict[str, Any]:
    return {
        "symbol": spec.symbol,
        "digits": spec.digits,
        "point": spec.point,
        "tick_size": spec.tick_size,
        "tick_value": spec.tick_value,
        "contract_size": spec.contract_size,
        "volume_min": spec.volume_min,
        "volume_max": spec.volume_max,
        "volume_step": spec.volume_step,
        "stops_level_points": spec.stops_level_points,
        "freeze_level_points": spec.freeze_level_points,
    }


def _symbol_spec_from_payload(payload: dict[str, Any]) -> SymbolSpec:
    try:
        return SymbolSpec(
            symbol=str(payload["symbol"]),
            digits=int(payload["digits"]),
            point=float(payload["point"]),
            tick_size=float(payload["tick_size"]),
            tick_value=float(payload["tick_value"]),
            contract_size=float(payload["contract_size"]),
            volume_min=float(payload["volume_min"]),
            volume_max=float(payload["volume_max"]),
            volume_step=float(payload["volume_step"]),
            stops_level_points=int(payload["stops_level_points"]),
            freeze_level_points=int(payload["freeze_level_points"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetBundleIntegrityError("invalid symbol specification") from exc


def _account_context_payload(account: AccountFacts) -> dict[str, Any]:
    return {
        "currency": account.currency,
        "mode": account.mode.value,
        "balance": account.balance,
        "equity": account.equity,
        "margin": account.margin,
        "margin_free": account.margin_free,
        "leverage": account.leverage,
    }


def _account_from_payload(payload: dict[str, Any]) -> AccountFacts:
    try:
        return AccountFacts(
            # Neutral offline endpoint; dataset identity deliberately excludes these.
            login=1,
            server="RESEARCH_DATASET",
            currency=str(payload["currency"]),
            mode=AccountMode(str(payload["mode"])),
            balance=float(payload["balance"]),
            equity=float(payload["equity"]),
            margin=float(payload["margin"]),
            margin_free=float(payload["margin_free"]),
            leverage=int(payload["leverage"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DatasetBundleIntegrityError("invalid account research context") from exc


def _required_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise DatasetBundleIntegrityError(f"manifest field must be object: {key}")
    return value


def _required_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DatasetBundleIntegrityError(f"manifest field must be non-empty text: {name}")
    return value.strip()


def _required_sha256(value: Any, name: str) -> str:
    text = _required_text(value, name)
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise DatasetBundleIntegrityError(f"manifest field is not SHA-256 hex: {name}")
    return text


def _required_nonnegative_float(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise DatasetBundleIntegrityError(f"manifest field must be numeric: {name}") from exc
    if result < 0:
        raise DatasetBundleIntegrityError(f"manifest field cannot be negative: {name}")
    return result


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _payload_sha256(payload: Any) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
