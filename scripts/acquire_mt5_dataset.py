"""Acquire a verified, read-only MT5 historical dataset bundle.

The command is intended for the controlled Windows/MT5 evidence step. It uses
the existing MT5Reader and research acquisition boundary, requires exact
completed-candle counts, and never calls a broker-write API.
"""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path

from goldswingtraderai.domain.enums import Timeframe
from goldswingtraderai.market_data import MT5Reader, MarketDataError
from goldswingtraderai.research.acquisition import (
    HistoricalAcquisitionError,
    HistoricalAcquisitionRequest,
    acquire_and_export_mt5_bundle,
)


_DEFAULT_COUNTS = {
    Timeframe.H4: 400,
    Timeframe.H1: 750,
    Timeframe.M15: 2000,
    Timeframe.M5: 4000,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Acquire exact completed MT5 candles into a verified research bundle"
    )
    parser.add_argument("destination", type=Path)
    parser.add_argument("--preferred-symbol", default="XAUUSDm")
    parser.add_argument("--aliases", default="XAUUSDm,XAUUSD")
    parser.add_argument("--count", action="append", default=[], metavar="TIMEFRAME=COUNT")
    parser.add_argument("--source-label", required=True)
    parser.add_argument("--source-version", required=True)
    parser.add_argument("--spread-price-override", type=_nonnegative_float)
    args = parser.parse_args(argv)

    reader = MT5Reader()
    try:
        counts = _parse_counts(args.count)
        request = HistoricalAcquisitionRequest(
            preferred_symbol=args.preferred_symbol,
            aliases=tuple(
                dict.fromkeys(
                    item.strip() for item in args.aliases.split(",") if item.strip()
                )
            ),
            counts=counts,
            source_label=args.source_label,
            source_version=args.source_version,
            spread_price_override=args.spread_price_override,
        )
        reader.initialize()
        result = acquire_and_export_mt5_bundle(reader, request, args.destination)
    except (
        HistoricalAcquisitionError,
        MarketDataError,
        FileExistsError,
        FileNotFoundError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"MT5_ACQUISITION_FAILED: {exc}")
        return 2
    finally:
        reader.shutdown()

    acquisition = result.acquisition
    print(
        json.dumps(
            {
                "destination": str(result.bundle.path),
                "symbol": acquisition.symbol,
                "source_label": acquisition.source_label,
                "source_version": acquisition.source_version,
                "spread_source": acquisition.spread_source.value,
                "spread_price": acquisition.dataset.spread_price,
                "requested_counts": {
                    timeframe.value: count
                    for timeframe, count in acquisition.requested_counts
                },
                "dataset_sha256": result.bundle.dataset_sha256,
                "manifest_sha256": result.bundle.manifest_sha256,
                "broker_write_performed": False,
            },
            sort_keys=True,
        )
    )
    return 0


def _parse_counts(values: list[str]) -> dict[Timeframe, int]:
    if not values:
        return dict(_DEFAULT_COUNTS)

    parsed: dict[Timeframe, int] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError("--count must use TIMEFRAME=COUNT")
        raw_timeframe, raw_count = raw.split("=", 1)
        try:
            timeframe = Timeframe(raw_timeframe.strip().upper())
        except ValueError as exc:
            raise ValueError(f"unsupported timeframe in --count: {raw_timeframe!r}") from exc
        if timeframe in parsed:
            raise ValueError(f"duplicate --count timeframe: {timeframe.value}")
        try:
            count = int(raw_count)
        except ValueError as exc:
            raise ValueError(f"invalid --count value: {raw_count!r}") from exc
        if count <= 0:
            raise ValueError("--count values must be positive")
        parsed[timeframe] = count

    missing = set(_DEFAULT_COUNTS) - set(parsed)
    if missing:
        names = ",".join(sorted(item.value for item in missing))
        raise ValueError(f"--count must include required timeframes: {names}")
    return parsed


def _nonnegative_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
