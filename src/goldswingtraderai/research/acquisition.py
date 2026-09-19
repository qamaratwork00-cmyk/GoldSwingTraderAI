"""Read-only MT5 acquisition for reproducible historical research datasets.

This module reuses the production MT5Reader. It never calls raw broker writes and
never invents a zero-spread historical model. Required H4/H1/M15/M5 bar counts are
explicit; optional supported timeframes such as M1 may be requested as well.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from statistics import median
from typing import Mapping

from goldswingtraderai.domain.enums import Timeframe
from goldswingtraderai.market_data.mt5_reader import MT5Reader
from goldswingtraderai.research.datasets import (
    ExportedDatasetBundle,
    export_replay_dataset_bundle,
)
from goldswingtraderai.research.replay import ReplayDataset


_REQUIRED_TIMEFRAMES = frozenset({Timeframe.H4, Timeframe.H1, Timeframe.M15, Timeframe.M5})


class HistoricalSpreadSource(StrEnum):
    M5_MEDIAN_SPREAD_POINTS = "M5_MEDIAN_SPREAD_POINTS"
    EXPLICIT_OVERRIDE = "EXPLICIT_OVERRIDE"


class HistoricalAcquisitionError(RuntimeError):
    """Historical data is incomplete or cannot form a declared replay dataset."""


@dataclass(frozen=True, slots=True)
class HistoricalAcquisitionRequest:
    preferred_symbol: str
    aliases: tuple[str, ...]
    counts: Mapping[Timeframe, int]
    source_label: str
    source_version: str
    spread_price_override: float | None = None

    def __post_init__(self) -> None:
        if not self.preferred_symbol.strip():
            raise ValueError("preferred symbol cannot be empty")
        if not self.source_label.strip() or not self.source_version.strip():
            raise ValueError("historical source label/version cannot be empty")
        normalized = dict(self.counts)
        missing = _REQUIRED_TIMEFRAMES - set(normalized)
        if missing:
            names = ",".join(sorted(item.value for item in missing))
            raise ValueError(f"historical acquisition missing required counts: {names}")
        for timeframe, count in normalized.items():
            if not isinstance(timeframe, Timeframe):
                raise TypeError("historical acquisition count keys must be Timeframe")
            if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
                raise ValueError(f"historical count must be positive: {timeframe.value}")
        if self.spread_price_override is not None and (
            not isfinite(self.spread_price_override) or self.spread_price_override < 0
        ):
            raise ValueError("historical spread override cannot be negative")


@dataclass(frozen=True, slots=True)
class AcquiredReplayDataset:
    dataset: ReplayDataset
    symbol: str
    source_label: str
    source_version: str
    spread_source: HistoricalSpreadSource
    requested_counts: tuple[tuple[Timeframe, int], ...]


@dataclass(frozen=True, slots=True)
class AcquiredDatasetBundle:
    acquisition: AcquiredReplayDataset
    bundle: ExportedDatasetBundle


def acquire_mt5_replay_dataset(
    reader: MT5Reader,
    request: HistoricalAcquisitionRequest,
) -> AcquiredReplayDataset:
    """Acquire one exact-count completed-candle dataset through the read-only MT5 API."""

    symbol = reader.resolve_symbol(request.preferred_symbol, request.aliases)
    account = reader.account_facts()
    symbol_spec = reader.symbol_spec(symbol)

    requested_counts = tuple(sorted(request.counts.items(), key=lambda item: item[0].value))
    series = []
    for timeframe, requested_count in requested_counts:
        loaded = reader.completed_candles(symbol, timeframe, requested_count)
        actual = len(loaded.candles)
        if actual != requested_count:
            raise HistoricalAcquisitionError(
                f"historical {timeframe.value} count mismatch: requested={requested_count} actual={actual}"
            )
        series.append(loaded)

    m5 = next(item for item in series if item.timeframe is Timeframe.M5)
    spread_price, spread_source = _resolve_spread_price(
        m5_spread_points=tuple(candle.spread_points for candle in m5.candles),
        point=symbol_spec.point,
        override=request.spread_price_override,
    )
    dataset = ReplayDataset(
        account=account,
        symbol_spec=symbol_spec,
        series=tuple(series),
        spread_price=spread_price,
    )
    return AcquiredReplayDataset(
        dataset=dataset,
        symbol=symbol,
        source_label=request.source_label.strip(),
        source_version=request.source_version.strip(),
        spread_source=spread_source,
        requested_counts=requested_counts,
    )


def acquire_and_export_mt5_bundle(
    reader: MT5Reader,
    request: HistoricalAcquisitionRequest,
    destination: str | Path,
) -> AcquiredDatasetBundle:
    """Acquire completed MT5 history then export an integrity-checked offline bundle."""

    acquisition = acquire_mt5_replay_dataset(reader, request)
    bundle = export_replay_dataset_bundle(
        acquisition.dataset,
        destination,
        source_label=acquisition.source_label,
        source_version=acquisition.source_version,
    )
    return AcquiredDatasetBundle(acquisition=acquisition, bundle=bundle)


def _resolve_spread_price(
    *,
    m5_spread_points: tuple[int, ...],
    point: float,
    override: float | None,
) -> tuple[float, HistoricalSpreadSource]:
    if override is not None:
        return float(override), HistoricalSpreadSource.EXPLICIT_OVERRIDE

    observed = tuple(value for value in m5_spread_points if value > 0)
    if not observed:
        raise HistoricalAcquisitionError(
            "historical M5 spread_points unavailable; provide explicit spread_price_override"
        )
    return float(median(observed)) * point, HistoricalSpreadSource.M5_MEDIAN_SPREAD_POINTS
