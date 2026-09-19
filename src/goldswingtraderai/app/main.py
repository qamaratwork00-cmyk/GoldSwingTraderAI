"""GoldSwingTraderAI launcher and persistent runtime entry point."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

from goldswingtraderai import __version__
from goldswingtraderai.app.runtime import LiveStartupRuntime, SessionNewsProvider
from goldswingtraderai.app.loop import PersistentRuntimeLoop, RuntimeLoopResult
from goldswingtraderai.app.session_news import FileSessionNewsProvider
from goldswingtraderai.config import ConfigError, RuntimeMode, Settings
from goldswingtraderai.diagnostics.logging import configure_logging
from goldswingtraderai.domain.enums import HardDecision
from goldswingtraderai.domain.market import AccountFacts
from goldswingtraderai.execution import CoordinationError
from goldswingtraderai.market_data import MT5Reader, MarketDataError, MarketSnapshotBuilder
from goldswingtraderai.operator import DashboardData, render_dashboard
from goldswingtraderai.persistence import StateStoreError

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


def run_startup(
    settings: Settings,
    reader: MT5Reader,
    *,
    now_utc: datetime | None = None,
    session_news_provider: SessionNewsProvider | None = None,
) -> int:
    """Run one bounded startup/recovery diagnostic and release all authorities.

    The launcher uses :func:`run_persistent`; this helper remains useful for
    deterministic operator diagnostics and compatibility with one-cycle tests.
    """

    runtime = LiveStartupRuntime(
        settings,
        reader,
        session_news_provider=_resolve_session_news_provider(
            settings,
            session_news_provider,
        ),
    )
    exit_code = 5
    try:
        result = runtime.start(now_utc=now_utc or datetime.now(timezone.utc))
        traces = {
            trace.name: {
                "decision": trace.decision.value,
                "reason": trace.reason,
            }
            for trace in result.authorities.traces
        }
        _LOG.info(
            "integrated startup recovery evaluated",
            extra={
                "event": "STARTUP_RECOVERY_EVALUATED",
                "context": {
                    "scope": runtime.scope,
                    "symbol": result.recovery_truth.snapshot.symbol,
                    "recovery_state": result.recovery.state.value,
                    "recovery_reason": result.recovery.reason,
                    "authorities": traces,
                    "controller": (
                        None
                        if result.recovery.controller_status is None
                        else result.recovery.controller_status.reason
                    ),
                },
            },
        )
        exit_code = {
            "READY": 0,
            "RECONCILING": 6,
            "BLOCKED": 7,
        }[result.recovery.state.value]
    except (MarketDataError, StateStoreError, CoordinationError, ValueError, RuntimeError) as exc:
        _LOG.error(
            "integrated startup recovery failed",
            extra={
                "event": "STARTUP_RECOVERY_FAILED",
                "context": {"error": str(exc), "error_type": type(exc).__name__},
            },
        )
    finally:
        try:
            runtime.shutdown()
        except Exception as exc:  # shutdown must remain visible and fail closed
            _LOG.error(
                "runtime shutdown could not release every authority",
                extra={
                    "event": "RUNTIME_SHUTDOWN_FAILED",
                    "context": {"error": str(exc), "error_type": type(exc).__name__},
                },
            )
            exit_code = 8
    return exit_code


def run_persistent(
    settings: Settings,
    reader: MT5Reader,
    *,
    session_news_provider: SessionNewsProvider | None = None,
) -> RuntimeLoopResult:
    """Run the controller-gated persistent M5 runtime until it stops safely."""

    runtime = LiveStartupRuntime(
        settings,
        reader,
        session_news_provider=_resolve_session_news_provider(
            settings,
            session_news_provider,
        ),
    )
    return PersistentRuntimeLoop(runtime, dashboard_sink=_emit_dashboard).run()


def _emit_dashboard(data: DashboardData) -> None:
    """Render one authoritative read-only frame for the persistent terminal."""

    print(render_dashboard(data), flush=True)


def _resolve_session_news_provider(
    settings: Settings,
    provider: SessionNewsProvider | None,
) -> SessionNewsProvider | None:
    """Resolve the configured provider boundary without selecting a vendor."""

    if provider is not None or settings.session_news_file is None:
        return provider
    return FileSessionNewsProvider(
        settings.session_news_file,
        freshness_ttl=timedelta(seconds=settings.session_news_ttl_seconds),
    )


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
        "GoldSwingTraderAI starting",
        extra={
            "event": "RUNTIME_START",
            "context": {
                "version": __version__,
                **settings.safe_summary(),
            },
        },
    )
    if settings.runtime_mode is not RuntimeMode.READINESS:
        result = run_persistent(settings, MT5Reader())
        return {
            "STOP_REQUESTED": 0,
            "MAX_CYCLES": 0,
            "INTERRUPTED": 0,
            "STARTUP_NOT_READY": 6,
            "CONTROLLER_LOST": 7,
            "CYCLE_FAILED": 8,
            "SHUTDOWN_FAILED": 9,
        }[result.stop_reason.value]
    return run_readiness(settings, MT5Reader())


if __name__ == "__main__":
    raise SystemExit(main())
