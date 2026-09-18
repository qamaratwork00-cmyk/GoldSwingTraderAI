"""GoldSwingTraderAI application bootstrap.

Phase 2 connects to MT5 for read-only account, Gold symbol, quote and completed-candle
facts. Irreversible broker writes are intentionally absent until the governed
execution phase.
"""

from __future__ import annotations

import logging

from goldswingtraderai import __version__
from goldswingtraderai.config import ConfigError, Settings
from goldswingtraderai.diagnostics.logging import configure_logging
from goldswingtraderai.domain.enums import HardDecision
from goldswingtraderai.domain.market import AccountFacts
from goldswingtraderai.market_data import MT5Reader, MarketDataError, MarketSnapshotBuilder

_LOG = logging.getLogger("goldswingtraderai.app")


def _identity_mismatches(settings: Settings, account: AccountFacts) -> tuple[str, ...]:
    """Return configured account-identity mismatches without inventing broker policy."""

    mismatches: list[str] = []
    if settings.allowed_account_login is not None and account.login != settings.allowed_account_login:
        mismatches.append("account login differs from configured identity")
    if settings.allowed_server is not None and account.server != settings.allowed_server:
        mismatches.append("account server differs from configured identity")
    return tuple(mismatches)


def run_readiness(settings: Settings, reader: MT5Reader) -> int:
    """Read one normalized MT5 snapshot and publish a concise readiness result.

    This function is intentionally injectable so deterministic CI can exercise the
    runtime path without requiring a Windows MT5 terminal.
    """

    try:
        reader.initialize()
        snapshot = MarketSnapshotBuilder(reader).build(
            preferred_symbol=settings.preferred_symbol,
            symbol_aliases=settings.symbol_aliases,
        )
        demo_guard = reader.demo_guard(snapshot.account)
        identity_mismatches = _identity_mismatches(settings, snapshot.account)

        _LOG.info(
            "MT5 market snapshot ready",
            extra={
                "event": "MARKET_SNAPSHOT_READY",
                "context": {
                    "version": __version__,
                    "symbol": snapshot.meta.symbol,
                    "account_mode": snapshot.account.mode,
                    "bid": snapshot.quote.bid,
                    "ask": snapshot.quote.ask,
                    "spread_price": snapshot.quote.spread_price,
                    "data_quality": snapshot.quality,
                    "timeframe_bars": {
                        item.timeframe.value: len(item.candles) for item in snapshot.series
                    },
                    "demo_guard": demo_guard.decision,
                    "identity_ok": not identity_mismatches,
                    "broker_write_implemented": False,
                },
            },
        )

        if identity_mismatches:
            _LOG.error(
                "configured MT5 account identity does not match connected account",
                extra={
                    "event": "ACCOUNT_IDENTITY_MISMATCH",
                    "context": {"reasons": identity_mismatches},
                },
            )
            return 3

        if demo_guard.decision is not HardDecision.PASS:
            _LOG.warning(
                "positive DEMO guard is not verified",
                extra={
                    "event": "DEMO_GUARD_NOT_VERIFIED",
                    "context": {
                        "account_mode": snapshot.account.mode,
                        "decision": demo_guard.decision,
                    },
                },
            )
            return 4

        if snapshot.issues:
            _LOG.warning(
                "market snapshot requires data warmup/review",
                extra={
                    "event": "MARKET_DATA_DEGRADED",
                    "context": {
                        "quality": snapshot.quality,
                        "issues": snapshot.issues,
                    },
                },
            )

        return 0
    except MarketDataError as exc:
        _LOG.error(
            "MT5 read-only readiness failed",
            extra={
                "event": exc.reason.value,
                "context": {"error": str(exc)},
            },
        )
        return 5
    finally:
        reader.shutdown()


def main() -> int:
    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        configure_logging("ERROR")
        _LOG.error(
            "configuration rejected",
            extra={"event": "CONFIG_INVALID", "context": {"error": str(exc)}},
        )
        return 2

    configure_logging(settings.logging_level)
    _LOG.info(
        "GoldSwingTraderAI starting read-only MT5 readiness",
        extra={
            "event": "PHASE_2_READINESS_START",
            "context": {
                "version": __version__,
                **settings.safe_summary(),
                "broker_write_implemented": False,
            },
        },
    )
    return run_readiness(settings, MT5Reader())


if __name__ == "__main__":
    raise SystemExit(main())
