"""Persistent M5 runtime lifecycle around the governed live cycle."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
import logging
import time

from goldswingtraderai import __version__
from goldswingtraderai.app.cycle import GovernedRuntimeCycle, RuntimeCycleResult
from goldswingtraderai.app.dashboard import build_dashboard_data
from goldswingtraderai.app.recovery import RecoveryState, StartupRecoveryResult
from goldswingtraderai.app.runtime import LiveCycleFacts, LiveStartupRuntime
from goldswingtraderai.domain.enums import HardDecision
from goldswingtraderai.execution import ControllerStatus
from goldswingtraderai.operator import DashboardData
from goldswingtraderai.persistence import BackupRunResult, BackupPolicy, create_backup_if_due


_LOG = logging.getLogger("goldswingtraderai.app.loop")
HEARTBEAT_SECONDS = 10.0
M5_SECONDS = 5 * 60
M5_GRACE_SECONDS = 2.0
MARKET_DATA_WAIT_SECONDS = 30.0


class LoopStopReason(StrEnum):
    STOP_REQUESTED = "STOP_REQUESTED"
    MAX_CYCLES = "MAX_CYCLES"
    STARTUP_NOT_READY = "STARTUP_NOT_READY"
    CONTROLLER_LOST = "CONTROLLER_LOST"
    CYCLE_FAILED = "CYCLE_FAILED"
    INTERRUPTED = "INTERRUPTED"
    SHUTDOWN_FAILED = "SHUTDOWN_FAILED"


@dataclass(frozen=True, slots=True)
class RuntimeLoopResult:
    """Final lifecycle state returned after safe runtime shutdown."""

    startup: StartupRecoveryResult | None
    cycles_completed: int
    stop_reason: LoopStopReason
    last_cycle: RuntimeCycleResult | None = None
    last_backup: BackupRunResult | None = None
    error: str | None = None


class PersistentRuntimeLoop:
    """Keep one initialized runtime alive with M5 cadence and lease heartbeat."""

    def __init__(
        self,
        runtime: LiveStartupRuntime,
        *,
        cycle: GovernedRuntimeCycle | None = None,
        backup_policy: BackupPolicy | None = None,
        sleep: Callable[[float], None] | None = None,
        utc_now: Callable[[], datetime] | None = None,
        dashboard_sink: Callable[[DashboardData], None] | None = None,
        heartbeat_seconds: float = HEARTBEAT_SECONDS,
        m5_grace_seconds: float = M5_GRACE_SECONDS,
        market_data_wait_seconds: float = MARKET_DATA_WAIT_SECONDS,
    ) -> None:
        if heartbeat_seconds <= 0:
            raise ValueError("heartbeat interval must be positive")
        if m5_grace_seconds < 0:
            raise ValueError("M5 grace interval cannot be negative")
        if market_data_wait_seconds <= 0:
            raise ValueError("market-data wait interval must be positive")
        self.runtime = runtime
        self.cycle = cycle or GovernedRuntimeCycle(runtime)
        self.backup_policy = backup_policy or BackupPolicy()
        self._sleep = sleep or time.sleep
        self._utc_now = utc_now or (lambda: datetime.now(timezone.utc))
        self._dashboard_sink = dashboard_sink
        self.heartbeat_seconds = heartbeat_seconds
        self.m5_grace_seconds = m5_grace_seconds
        self.market_data_wait_seconds = market_data_wait_seconds
        self._stop_requested = False
        self.latest_dashboard: DashboardData | None = None
        self.latest_backup_error: str | None = None

    def request_stop(self) -> None:
        """Request a graceful stop at the next safe scheduler boundary."""

        self._stop_requested = True

    def run(
        self,
        *,
        start_now_utc: datetime | None = None,
        max_cycles: int | None = None,
        stop_requested: Callable[[], bool] | None = None,
        run_immediately: bool = True,
    ) -> RuntimeLoopResult:
        """Start, maintain and safely close one persistent runtime instance.

        ``max_cycles`` and injected clocks are deterministic-test controls. Live
        operation normally leaves both unset and stops through ``request_stop``
        or process interruption.
        """

        if max_cycles is not None and max_cycles <= 0:
            raise ValueError("max_cycles must be positive when provided")
        now = start_now_utc or self._utc_now()
        _require_utc(now)
        startup_result = None
        last_cycle = None
        last_backup = None
        cycles = 0
        stop_reason = LoopStopReason.CYCLE_FAILED
        error: str | None = None

        try:
            startup = self.runtime.start(now_utc=now)
            startup_result = startup.recovery
            while _standby_wait_required(self.runtime, startup_result):
                if self._stop_requested or (stop_requested and stop_requested()):
                    stop_reason = LoopStopReason.STOP_REQUESTED
                    break
                # An active PRIMARY owns the shared scope. Close this standby's
                # local MT5/controller handles before sleeping so the retry is a
                # fresh acquisition/recovery attempt after lease expiry.
                self.runtime.shutdown()
                self._sleep(self.heartbeat_seconds)
                now = self._utc_now()
                _require_utc(now)
                startup = self.runtime.start(now_utc=now)
                startup_result = startup.recovery

            if stop_reason is LoopStopReason.STOP_REQUESTED:
                pass
            elif _market_data_wait_required(startup_result):
                next_probe = now + timedelta(seconds=self.market_data_wait_seconds)
                next_heartbeat = now
                while _market_data_wait_required(startup_result):
                    current = self._utc_now()
                    _require_utc(current)
                    if self._stop_requested or (stop_requested and stop_requested()):
                        stop_reason = LoopStopReason.STOP_REQUESTED
                        break

                    if current >= next_heartbeat:
                        status = self.runtime.renew_controller()
                        if not _controller_healthy(status):
                            stop_reason = LoopStopReason.CONTROLLER_LOST
                            error = status.reason
                            break
                        next_heartbeat = current + timedelta(seconds=self.heartbeat_seconds)

                    if current >= next_probe:
                        _LOG.warning(
                            "persistent runtime waiting for fresh market data; no cycle or broker write",
                            extra={
                                "event": "RUNTIME_WAITING_FOR_MARKET_DATA",
                                "context": {
                                    "reason": startup_result.reason,
                                    "poll_seconds": self.market_data_wait_seconds,
                                },
                            },
                        )
                        facts = self.runtime.capture_cycle(now_utc=current)
                        startup_result = facts.startup.recovery
                        now = current
                        next_probe = current + timedelta(
                            seconds=self.market_data_wait_seconds
                        )

                    if not _market_data_wait_required(startup_result):
                        break
                    wait_seconds = min(
                        max(0.0, (next_probe - current).total_seconds()),
                        max(0.0, (next_heartbeat - current).total_seconds()),
                        self.heartbeat_seconds,
                    )
                    self._sleep(max(0.05, min(wait_seconds, self.heartbeat_seconds)))

            if stop_reason is LoopStopReason.STOP_REQUESTED:
                pass
            elif stop_reason in {
                LoopStopReason.CONTROLLER_LOST,
                LoopStopReason.CYCLE_FAILED,
            } and error is not None:
                pass
            elif startup_result.state is not RecoveryState.READY:
                stop_reason = LoopStopReason.STARTUP_NOT_READY
                error = startup_result.reason
            else:
                next_cycle = now if run_immediately else _next_m5_boundary(
                    now,
                    self.m5_grace_seconds,
                )
                next_heartbeat = now
                while True:
                    current = self._utc_now()
                    _require_utc(current)
                    if self._stop_requested or (stop_requested and stop_requested()):
                        stop_reason = LoopStopReason.STOP_REQUESTED
                        break

                    if current >= next_heartbeat:
                        status = self.runtime.renew_controller()
                        if not _controller_healthy(status):
                            stop_reason = LoopStopReason.CONTROLLER_LOST
                            error = status.reason
                            break
                        next_heartbeat = current + timedelta(seconds=self.heartbeat_seconds)

                    if current >= next_cycle:
                        facts = self.runtime.capture_cycle(now_utc=current)
                        last_cycle = self.cycle.run(facts)
                        cycles += 1
                        last_backup = self._backup(current)
                        if isinstance(facts, LiveCycleFacts):
                            self.latest_dashboard = build_dashboard_data(
                                self.runtime,
                                facts,
                                last_cycle,
                                backup=last_backup,
                                backup_error=self.latest_backup_error,
                            )
                            if self._dashboard_sink is not None:
                                self._dashboard_sink(self.latest_dashboard)
                        if max_cycles is not None and cycles >= max_cycles:
                            stop_reason = LoopStopReason.MAX_CYCLES
                            break
                        next_cycle = _next_m5_boundary(current, self.m5_grace_seconds)

                    wait_seconds = min(
                        max(0.0, (next_cycle - current).total_seconds()),
                        max(0.0, (next_heartbeat - current).total_seconds()),
                        self.heartbeat_seconds,
                    )
                    # A bounded sleep prevents busy-waiting while keeping lease loss
                    # detection comfortably inside the 30-second TTL.
                    self._sleep(max(0.05, min(wait_seconds, self.heartbeat_seconds)))
        except KeyboardInterrupt:
            stop_reason = LoopStopReason.INTERRUPTED
        except Exception as exc:
            stop_reason = LoopStopReason.CYCLE_FAILED
            error = f"{type(exc).__name__}: {exc}"
            _LOG.exception("persistent runtime loop failed")
        finally:
            try:
                self.runtime.shutdown()
            except Exception as exc:
                stop_reason = LoopStopReason.SHUTDOWN_FAILED
                error = f"{type(exc).__name__}: {exc}"
                _LOG.exception("persistent runtime shutdown failed")

        return RuntimeLoopResult(
            startup=startup_result,
            cycles_completed=cycles,
            stop_reason=stop_reason,
            last_cycle=last_cycle,
            last_backup=last_backup,
            error=error,
        )

    def _backup(self, now_utc: datetime) -> BackupRunResult | None:
        if self.runtime.store is None:
            return None
        try:
            result = create_backup_if_due(
                self.runtime.store,
                self.runtime.settings.state_dir / "backups",
                source_label="GoldSwingTraderAI runtime",
                source_version=__version__,
                policy=self.backup_policy,
                now_utc=now_utc,
            )
            self.latest_backup_error = None
            return result
        except Exception as exc:
            # Backup health is visible and degraded; deleting or inventing a
            # checkpoint would be more dangerous than continuing with the
            # verified live state and preserving the failure for operators.
            _LOG.error(
                "runtime backup failed",
                extra={
                    "event": "BACKUP_FAILED",
                    "context": {"error": str(exc), "error_type": type(exc).__name__},
                },
            )
            self.latest_backup_error = f"{type(exc).__name__}: {exc}"
            return None


def _controller_healthy(status: ControllerStatus) -> bool:
    return status.decision is HardDecision.PASS and status.lease is not None


def _standby_wait_required(runtime: LiveStartupRuntime, recovery: StartupRecoveryResult) -> bool:
    """Retry only the explicit active-primary contention state.

    Other startup failures remain terminal for this process. A standby may wait
    for the current lease to expire, but it must rebuild broker truth and rerun
    the complete recovery sequence before attempting to become READY.
    """

    mode = getattr(getattr(runtime, "settings", None), "runtime_mode", None)
    mode_value = getattr(mode, "value", mode)
    return mode_value == "STANDBY" and recovery.reason == "ANOTHER_ACTIVE_CONTROLLER"


def _market_data_wait_required(recovery: StartupRecoveryResult) -> bool:
    """Allow only freshness/warm-up states to remain alive before READY.

    Corrupt data, missing identity, unknown session/news, persistence faults and
    controller faults remain terminal or fail-closed. Stale market data is the
    one expected closed-market condition that can safely be re-probed without
    running a strategy or execution cycle.
    """

    return recovery.state is RecoveryState.RECONCILING and recovery.reason in {
        "MARKET_DATA_STALE",
        "MARKET_DATA_INSUFFICIENT",
        "MARKET_DATA_SPARSE",
    }


def _next_m5_boundary(now_utc: datetime, grace_seconds: float) -> datetime:
    epoch = now_utc.timestamp()
    next_epoch = (int(epoch) // M5_SECONDS + 1) * M5_SECONDS + grace_seconds
    return datetime.fromtimestamp(next_epoch, tz=timezone.utc)


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("loop timestamp must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("loop timestamp must be UTC")
