from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from goldswingtraderai.app.cycle import CycleAction, RuntimeCycleResult
from goldswingtraderai.app.loop import LoopStopReason, PersistentRuntimeLoop
from goldswingtraderai.app.recovery import RecoveryState
from goldswingtraderai.domain.enums import HardDecision


NOW = datetime(2026, 9, 18, 18, 30, tzinfo=timezone.utc)


class FakeClock:
    def __init__(self) -> None:
        self.current = NOW
        self.sleeps: list[float] = []

    def now(self) -> datetime:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.current += timedelta(seconds=seconds)


class FakeCycle:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, facts):
        self.calls += 1
        return RuntimeCycleResult(
            as_of_utc=facts.as_of_utc,
            action=CycleAction.WAIT,
            reason="TEST_WAIT",
            recovery_state=RecoveryState.READY,
            market=None,
        )


class FakeRuntime:
    def __init__(
        self,
        *,
        lose_controller_on: int | None = None,
        startup_state: RecoveryState = RecoveryState.READY,
        shutdown_error: bool = False,
    ) -> None:
        self.settings = SimpleNamespace(
            state_dir=Path(".state-test"),
            healthy_spread_baseline=None,
        )
        self.start_calls = 0
        self.capture_calls = 0
        self.renew_calls = 0
        self.shutdown_calls = 0
        self.lose_controller_on = lose_controller_on
        self.startup_state = startup_state
        self.shutdown_error = shutdown_error
        self.store = None

    def start(self, *, now_utc):
        self.start_calls += 1
        recovery = SimpleNamespace(
            state=self.startup_state,
            reason=(
                "STARTUP_RECOVERY_READY"
                if self.startup_state is RecoveryState.READY
                else "SESSION_NEWS_PROVIDER_UNCONFIGURED"
            ),
        )
        return SimpleNamespace(recovery=recovery)

    def renew_controller(self):
        self.renew_calls += 1
        if self.lose_controller_on == self.renew_calls:
            return SimpleNamespace(
                decision=HardDecision.UNKNOWN,
                reason="CONTROLLER_OWNERSHIP_UNKNOWN",
                lease=None,
            )
        return SimpleNamespace(
            decision=HardDecision.PASS,
            reason="CONTROLLER_PRIMARY",
            lease=object(),
        )

    def capture_cycle(self, *, now_utc):
        self.capture_calls += 1
        return SimpleNamespace(
            as_of_utc=now_utc,
            startup=SimpleNamespace(recovery=SimpleNamespace(state=RecoveryState.READY)),
        )

    def shutdown(self):
        self.shutdown_calls += 1
        if self.shutdown_error:
            raise RuntimeError("shutdown failed")


def test_persistent_loop_runs_cycle_renews_and_shuts_down_after_test_bound() -> None:
    runtime = FakeRuntime()
    cycle = FakeCycle()
    clock = FakeClock()

    result = PersistentRuntimeLoop(
        runtime,
        cycle=cycle,
        sleep=clock.sleep,
        utc_now=clock.now,
    ).run(start_now_utc=NOW, max_cycles=1)

    assert result.stop_reason is LoopStopReason.MAX_CYCLES
    assert result.cycles_completed == 1
    assert runtime.start_calls == 1
    assert runtime.capture_calls == 1
    assert runtime.renew_calls == 1
    assert cycle.calls == 1
    assert runtime.shutdown_calls == 1
    assert clock.sleeps == []


def test_controller_loss_stops_persistent_loop_before_next_cycle() -> None:
    runtime = FakeRuntime(lose_controller_on=2)
    cycle = FakeCycle()
    clock = FakeClock()

    result = PersistentRuntimeLoop(
        runtime,
        cycle=cycle,
        sleep=clock.sleep,
        utc_now=clock.now,
    ).run(start_now_utc=NOW)

    assert result.stop_reason is LoopStopReason.CONTROLLER_LOST
    assert result.error == "CONTROLLER_OWNERSHIP_UNKNOWN"
    assert result.cycles_completed == 1
    assert cycle.calls == 1
    assert runtime.shutdown_calls == 1
    assert clock.sleeps


def test_standby_waits_for_active_primary_then_restarts_recovery() -> None:
    runtime = FakeRuntime()
    runtime.settings.runtime_mode = SimpleNamespace(value="STANDBY")
    original_start = runtime.start

    def start_with_takeover(*, now_utc):
        if runtime.start_calls == 0:
            runtime.start_calls += 1
            return SimpleNamespace(
                recovery=SimpleNamespace(
                    state=RecoveryState.BLOCKED,
                    reason="ANOTHER_ACTIVE_CONTROLLER",
                )
            )
        return original_start(now_utc=now_utc)

    runtime.start = start_with_takeover
    clock = FakeClock()
    cycle = FakeCycle()

    result = PersistentRuntimeLoop(
        runtime,
        cycle=cycle,
        sleep=clock.sleep,
        utc_now=clock.now,
        heartbeat_seconds=1.0,
    ).run(start_now_utc=NOW, max_cycles=1)

    assert result.stop_reason is LoopStopReason.MAX_CYCLES
    assert result.cycles_completed == 1
    assert runtime.start_calls == 2
    assert runtime.shutdown_calls == 2
    assert clock.sleeps == [1.0]


def test_startup_not_ready_still_returns_after_safe_shutdown() -> None:
    runtime = FakeRuntime(startup_state=RecoveryState.RECONCILING)

    result = PersistentRuntimeLoop(runtime).run(start_now_utc=NOW)

    assert result.stop_reason is LoopStopReason.STARTUP_NOT_READY
    assert result.error == "SESSION_NEWS_PROVIDER_UNCONFIGURED"
    assert result.cycles_completed == 0
    assert runtime.shutdown_calls == 1


def test_shutdown_failure_overrides_startup_stop_result() -> None:
    runtime = FakeRuntime(
        startup_state=RecoveryState.RECONCILING,
        shutdown_error=True,
    )

    result = PersistentRuntimeLoop(runtime).run(start_now_utc=NOW)

    assert result.stop_reason is LoopStopReason.SHUTDOWN_FAILED
    assert result.error == "RuntimeError: shutdown failed"
    assert runtime.shutdown_calls == 1
