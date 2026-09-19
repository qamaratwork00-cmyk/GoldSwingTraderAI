from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from goldswingtraderai.app.recovery import RecoveryState
from goldswingtraderai.app.cycle import GovernedRuntimeCycle
from goldswingtraderai.app.dashboard import build_dashboard_data
from goldswingtraderai.app.runtime import LiveStartupRuntime
from goldswingtraderai.config import RuntimeMode, RuntimeStateMode, Settings
from goldswingtraderai.domain.enums import HardDecision, Timeframe
from goldswingtraderai.intelligence.news import NewsFacts, ProviderHealth
from goldswingtraderai.market_data import MT5Reader, MarketSnapshotBuilder
from goldswingtraderai.persistence import (
    RuntimeStateRepository,
    StateStore,
    export_runtime_checkpoint,
)
from goldswingtraderai.risk import (
    BrokerSessionFacts,
    ClosureKind,
    combine_session_news_permission,
    evaluate_market_permission,
    evaluate_news_permission,
    new_risk_day,
)


NOW = datetime(2026, 9, 18, 18, 30, tzinfo=timezone.utc)


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1
    TIMEFRAME_H4 = 14_400
    TIMEFRAME_H1 = 3_600
    TIMEFRAME_M15 = 900
    TIMEFRAME_M5 = 300

    def __init__(self) -> None:
        self.initialized = False

    def initialize(self) -> bool:
        self.initialized = True
        return True

    def shutdown(self) -> None:
        self.initialized = False

    def account_info(self):
        return SimpleNamespace(
            login=123456,
            server="Broker-Demo",
            currency="USD",
            trade_mode=self.ACCOUNT_TRADE_MODE_DEMO,
            balance=100.0,
            equity=101.0,
            margin=0.0,
            margin_free=101.0,
            leverage=500,
        )

    def symbol_info(self, symbol: str):
        if symbol != "XAUUSD":
            return None
        return SimpleNamespace(
            visible=True,
            digits=2,
            point=0.01,
            trade_tick_size=0.01,
            trade_tick_value=1.0,
            trade_contract_size=100.0,
            volume_min=0.01,
            volume_max=200.0,
            volume_step=0.01,
            trade_stops_level=0,
            trade_freeze_level=0,
        )

    def symbol_info_tick(self, symbol: str):
        assert symbol == "XAUUSD"
        return SimpleNamespace(
            bid=3650.10,
            ask=3650.30,
            time=int(NOW.timestamp()),
            time_msc=int(NOW.timestamp() * 1000),
        )

    def copy_rates_from_pos(self, symbol: str, timeframe: int, start_pos: int, count: int):
        assert symbol == "XAUUSD"
        assert start_pos == 1
        rows = []
        for index in range(count, 0, -1):
            timestamp = int(NOW.timestamp()) - timeframe * index
            price = 3600.0 + index
            rows.append(
                {
                    "time": timestamp,
                    "open": price,
                    "high": price + 2.0,
                    "low": price - 2.0,
                    "close": price + 0.5,
                    "tick_volume": 100,
                    "spread": 20,
                    "real_volume": 0,
                }
            )
        return rows

    def positions_get(self, *, symbol: str):
        assert symbol == "XAUUSD"
        return ()

    def orders_get(self, *, symbol: str):
        assert symbol == "XAUUSD"
        return ()

    def history_deals_get(self, start, end):
        assert start.tzinfo is not None and end.tzinfo is not None
        return ()


def _settings(
    tmp_path: Path,
    *,
    state_mode: RuntimeStateMode,
    restore_checkpoint: Path | None = None,
) -> Settings:
    return Settings(
        environment="test",
        preferred_symbol="XAUUSD",
        symbol_aliases=("XAUUSD",),
        manual_reset_enabled=False,
        state_dir=tmp_path,
        log_level="INFO",
        runtime_mode=RuntimeMode.PRIMARY,
        state_mode=state_mode,
        mt5_magic=26091801,
        mt5_deviation_points=20,
        restore_checkpoint=restore_checkpoint,
    )


def _session_news_provider(market, recovery_truth, now_utc):
    assert market.meta.symbol == recovery_truth.snapshot.symbol
    market_permission = evaluate_market_permission(
        BrokerSessionFacts(
            tradeable=True,
            schedule_verified=True,
            next_close_utc=now_utc + timedelta(hours=2),
            next_close_kind=ClosureKind.DAILY,
        ),
        now_utc,
    )
    news_permission = evaluate_news_permission(
        NewsFacts(
            provider="test",
            health=ProviderHealth.VERIFIED,
            fetched_at_utc=now_utc,
            mapping_version="test",
            events=(),
            windows=(),
            required_event_truth_available=True,
        ),
        now_utc,
    )
    return combine_session_news_permission(market_permission, news_permission)


def _runtime(
    tmp_path: Path,
    *,
    state_mode: RuntimeStateMode,
    restore_checkpoint: Path | None = None,
) -> LiveStartupRuntime:
    reader = MT5Reader(FakeMT5())
    builder = MarketSnapshotBuilder(
        reader,
        history_bars={
            Timeframe.H4: 3,
            Timeframe.H1: 3,
            Timeframe.M15: 3,
            Timeframe.M5: 3,
        },
    )
    return LiveStartupRuntime(
        _settings(
            tmp_path,
            state_mode=state_mode,
            restore_checkpoint=restore_checkpoint,
        ),
        reader,
        session_news_provider=_session_news_provider,
        snapshot_builder=builder,
    )


def test_live_startup_assembles_real_recovery_authorities_and_initializes_explicit_state(
    tmp_path: Path,
) -> None:
    runtime = _runtime(tmp_path, state_mode=RuntimeStateMode.INITIALIZE)

    result = runtime.start(now_utc=NOW)

    assert result.recovery.state is RecoveryState.READY
    assert result.recovery.reason == "STARTUP_RECOVERY_READY"
    assert runtime.scope == "123456:XAUUSD"
    assert runtime.runtime_repository is not None
    assert runtime.runtime_repository.load_risk_day() is not None
    assert all(trace.decision is HardDecision.PASS for trace in result.authorities.traces)

    runtime.shutdown()
    assert runtime.reader._initialized is False


def test_missing_session_news_provider_remains_unknown_and_blocks_ready(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, state_mode=RuntimeStateMode.INITIALIZE)
    runtime.session_news_provider = None

    result = runtime.start(now_utc=NOW)

    assert result.recovery.state is RecoveryState.RECONCILING
    assert result.recovery.reason == "SESSION_NEWS_PROVIDER_UNCONFIGURED"
    runtime.shutdown()


def test_existing_state_mode_does_not_silently_create_missing_risk_day(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, state_mode=RuntimeStateMode.EXISTING)

    result = runtime.start(now_utc=NOW)

    assert result.recovery.state is RecoveryState.RECONCILING
    assert result.recovery.reason == "RISK_DAY_STATE_MISSING"
    runtime.shutdown()


def test_existing_state_mode_rolls_utc_risk_day_only_from_clear_lifecycle(
    tmp_path: Path,
) -> None:
    store = StateStore(tmp_path / "runtime.db")
    repository = RuntimeStateRepository(store, "123456:XAUUSD")
    repository.save_risk_day(new_risk_day(NOW - timedelta(days=1), 99.0))

    runtime = _runtime(tmp_path, state_mode=RuntimeStateMode.EXISTING)
    result = runtime.start(now_utc=NOW)

    assert result.recovery.state is RecoveryState.READY
    assert runtime.runtime_repository is not None
    state = runtime.runtime_repository.load_risk_day()
    assert state is not None
    assert state.utc_day == NOW.date()
    assert state.day_start_equity == 101.0
    runtime.shutdown()


def test_initialize_mode_does_not_overwrite_partially_unknown_state(tmp_path: Path) -> None:
    StateStore(tmp_path / "runtime.db").save_record(
        "future_namespace",
        "future_key",
        {"preserve": True},
    )
    runtime = _runtime(tmp_path, state_mode=RuntimeStateMode.INITIALIZE)

    result = runtime.start(now_utc=NOW)

    assert result.recovery.state is RecoveryState.RECONCILING
    assert result.recovery.reason == "RISK_DAY_STATE_MISSING"
    assert runtime.runtime_repository is not None
    assert runtime.runtime_repository.load_risk_day() is None
    runtime.shutdown()


def test_restore_mode_uses_verified_checkpoint_without_overwriting_target(tmp_path: Path) -> None:
    source_store = StateStore(tmp_path / "source.db")
    source_runtime = RuntimeStateRepository(source_store, "123456:XAUUSD")

    source_runtime.save_risk_day(new_risk_day(NOW, 101.0))
    checkpoint = tmp_path / "checkpoint"
    export_runtime_checkpoint(
        source_store,
        checkpoint,
        source_label="test",
        source_version="test",
        created_at_utc=NOW,
    )

    runtime = _runtime(
        tmp_path / "restored",
        state_mode=RuntimeStateMode.RESTORE,
        restore_checkpoint=checkpoint,
    )
    result = runtime.start(now_utc=NOW)

    assert result.recovery.state is RecoveryState.READY
    assert runtime.paths.state_database.exists()
    runtime.shutdown()


def test_second_live_runtime_cannot_take_over_active_controller(tmp_path: Path) -> None:
    first = _runtime(tmp_path, state_mode=RuntimeStateMode.INITIALIZE)
    second = _runtime(tmp_path, state_mode=RuntimeStateMode.INITIALIZE)

    first_result = first.start(now_utc=NOW)
    second_result = second.start(now_utc=NOW)

    assert first_result.recovery.state is RecoveryState.READY
    assert second_result.recovery.state is RecoveryState.BLOCKED
    assert second_result.recovery.reason == "ANOTHER_ACTIVE_CONTROLLER"

    second.shutdown()
    first.shutdown()


def test_live_dashboard_maps_cycle_and_recovery_authorities_without_recomputing_them(
    tmp_path: Path,
) -> None:
    runtime = _runtime(tmp_path, state_mode=RuntimeStateMode.INITIALIZE)
    runtime.start(now_utc=NOW)

    facts = runtime.capture_cycle(now_utc=NOW)
    cycle = GovernedRuntimeCycle(runtime).run(facts)
    dashboard = build_dashboard_data(runtime, facts, cycle)

    assert dashboard.demo_guard == HardDecision.PASS.value
    assert dashboard.runtime_role == RuntimeMode.PRIMARY.value
    assert dashboard.broker_reconcile == "STARTUP_RECOVERY_READY"
    assert dashboard.discovery_state == "PENDING"
    assert dashboard.backup_state == "PENDING"

    runtime.shutdown()
