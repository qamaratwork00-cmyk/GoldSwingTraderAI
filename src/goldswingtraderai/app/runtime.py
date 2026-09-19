"""Live startup composition for the governed GoldSwingTraderAI runtime.

This module owns dependency assembly only. Strategy/decision execution is still
downstream of the startup result. A missing session/news provider remains an
explicit UNKNOWN authority; startup never invents a safe market schedule.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from goldswingtraderai.app.recovery import StartupRecoveryCoordinator
from goldswingtraderai.app.recovery_mt5 import MT5RecoveryTruth, build_mt5_recovery_truth
from goldswingtraderai.app.session_news import SessionNewsObservation
from goldswingtraderai.app.startup import (
    StartupRecoveryService,
    StartupRuntimeResult,
)
from goldswingtraderai.config import RuntimeStateMode, Settings
from goldswingtraderai.domain.enums import HardDecision, MarketState, NewsSafetyState
from goldswingtraderai.domain.ids import EntityId, new_controller_id
from goldswingtraderai.domain.market import MarketSnapshot
from goldswingtraderai.execution import (
    ControllerLeaseManager,
    ControllerStatus,
    ExecutionIntentRepository,
    ExecutionService,
    MT5Reconciler,
    MT5Writer,
    MT5WriteConfig,
    SQLiteCoordinationStore,
)
from goldswingtraderai.intelligence.news import NewsFacts
from goldswingtraderai.management import ManagedTradeRepository
from goldswingtraderai.market_data import MT5Reader, MarketSnapshotBuilder
from goldswingtraderai.persistence import (
    RuntimeStateRepository,
    StateStore,
    restore_runtime_checkpoint,
)
from goldswingtraderai.risk.permissions import (
    MarketPermission,
    NewsPermission,
    SessionNewsPermission,
)
from goldswingtraderai.risk.state import new_risk_day


SessionNewsProvider = Callable[
    [MarketSnapshot, MT5RecoveryTruth, datetime],
    "SessionNewsObservation | SessionNewsPermission",
]


@dataclass(frozen=True, slots=True)
class LiveCycleFacts:
    """One fresh market/recovery/session fact set consumed by the cycle owner."""

    startup: StartupRuntimeResult
    session_news: SessionNewsPermission
    news: NewsFacts | None
    holiday_context: bool


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    """Durable paths used by one account/symbol runtime instance."""

    state_database: Path
    coordination_database: Path


class LiveStartupRuntime:
    """Compose live broker, persistence, recovery and controller owners.

    `start()` leaves the MT5 bridge and controller lease active for the caller's
    management loop. `shutdown()` must be called by the process owner and safely
    releases the lease before closing the shared MT5 bridge.
    """

    def __init__(
        self,
        settings: Settings,
        reader: MT5Reader,
        *,
        session_news_provider: SessionNewsProvider | None = None,
        controller_id: EntityId | None = None,
        snapshot_builder: MarketSnapshotBuilder | None = None,
    ) -> None:
        self.settings = settings
        self.reader = reader
        self.session_news_provider = session_news_provider
        self.controller_id = controller_id or new_controller_id()
        self.snapshot_builder = snapshot_builder or MarketSnapshotBuilder(reader)

        self.paths = RuntimePaths(
            state_database=settings.state_dir / "runtime.db",
            coordination_database=settings.state_dir / "coordination.db",
        )
        self.scope: str | None = None
        self.store: StateStore | None = None
        self.runtime_repository: RuntimeStateRepository | None = None
        self.intent_repository: ExecutionIntentRepository | None = None
        self.managed_trade_repository: ManagedTradeRepository | None = None
        self.writer: MT5Writer | None = None
        self.execution_service: ExecutionService | None = None
        self.coordination_store: SQLiteCoordinationStore | None = None
        self.controller: ControllerLeaseManager | None = None
        self.coordinator: StartupRecoveryCoordinator | None = None
        self.startup_service: StartupRecoveryService | None = None
        self.result: StartupRuntimeResult | None = None
        self._started = False

    def start(
        self,
        *,
        now_utc: datetime,
        allow_verified_not_created: bool = False,
    ) -> StartupRuntimeResult:
        """Initialize MT5, acquire/fence the controller and run governed recovery."""

        _require_utc(now_utc)
        if self._started:
            raise RuntimeError("live startup runtime is already started")

        self.reader.initialize()
        market = self.snapshot_builder.build(
            preferred_symbol=self.settings.preferred_symbol,
            symbol_aliases=self.settings.symbol_aliases,
            now_utc=now_utc,
        )
        recovery_truth = build_mt5_recovery_truth(
            self.reader,
            preferred_symbol=self.settings.preferred_symbol,
            symbol_aliases=self.settings.symbol_aliases,
            captured_at_utc=now_utc,
        )

        self.scope = _runtime_scope(recovery_truth)
        self._assemble_dependencies()
        assert self.runtime_repository is not None
        assert self.intent_repository is not None
        assert self.managed_trade_repository is not None
        assert self.controller is not None
        assert self.coordinator is not None

        self._initialize_first_risk_day(
            self.runtime_repository,
            self.intent_repository,
            self.managed_trade_repository,
            recovery_truth,
            now_utc,
        )

        # A valid lease is required even on the first epoch. An expired lease is
        # intentionally returned as takeover-blocked and is completed only by
        # StartupRecoveryCoordinator after broker/state reconciliation.
        self.controller.acquire()
        session_news = self._session_news_observation(
            market,
            recovery_truth,
            now_utc,
        ).permission
        assert self.startup_service is not None
        result = self.startup_service.recover_from_facts(
            market=market,
            recovery_truth=recovery_truth,
            session_news_permission=session_news,
            now_utc=now_utc,
            allow_verified_not_created=allow_verified_not_created,
        )
        self.result = result
        self._started = True
        return self.result

    def capture_cycle(self, *, now_utc: datetime) -> LiveCycleFacts:
        """Capture fresh facts and re-run recovery authorities while staying live.

        The loop must not reuse startup quotes or position truth for a later
        write. This method intentionally rebuilds one normalized market snapshot,
        one broker recovery snapshot and one authoritative session/news result,
        then runs the same recovery coordinator before analysis or management.
        """

        _require_utc(now_utc)
        if not self._started or self.startup_service is None:
            raise RuntimeError("live startup runtime is not started")
        market = self.snapshot_builder.build(
            preferred_symbol=self.settings.preferred_symbol,
            symbol_aliases=self.settings.symbol_aliases,
            now_utc=now_utc,
        )
        recovery_truth = build_mt5_recovery_truth(
            self.reader,
            preferred_symbol=self.settings.preferred_symbol,
            symbol_aliases=self.settings.symbol_aliases,
            captured_at_utc=now_utc,
        )
        observation = self._session_news_observation(market, recovery_truth, now_utc)
        result = self.startup_service.recover_from_facts(
            market=market,
            recovery_truth=recovery_truth,
            session_news_permission=observation.permission,
            now_utc=now_utc,
        )
        self.result = result
        return LiveCycleFacts(
            startup=result,
            session_news=observation.permission,
            news=observation.news,
            holiday_context=observation.holiday_context,
        )

    def renew_controller(self) -> ControllerStatus:
        """Renew the active lease for the future persistent runtime loop."""

        if not self._started or self.controller is None:
            raise RuntimeError("live startup runtime is not started")
        return self.controller.renew()

    def shutdown(self) -> None:
        """Release controller authority and close the shared MT5 bridge."""

        release_error: Exception | None = None
        try:
            if self.controller is not None:
                self.controller.release()
        except Exception as exc:  # preserve MT5 shutdown even if coordination is degraded
            release_error = exc
        finally:
            self.reader.shutdown()
            self._started = False

        if release_error is not None:
            raise release_error

    def _assemble_dependencies(self) -> None:
        assert self.scope is not None
        self._prepare_state_database()
        state_store = StateStore(self.paths.state_database)
        runtime_repository = RuntimeStateRepository(state_store, self.scope)
        intent_repository = ExecutionIntentRepository(state_store, self.scope)
        managed_trade_repository = ManagedTradeRepository(state_store, self.scope)

        write_config = _write_config(self.settings)
        coordination_store = SQLiteCoordinationStore(
            self.paths.coordination_database
        )
        controller = ControllerLeaseManager(
            coordination_store,
            self.scope,
            self.controller_id,
        )
        broker_module = self.reader.broker_module()
        reconciler = MT5Reconciler(broker_module, write_config)
        writer = MT5Writer(broker_module, write_config)
        coordinator = StartupRecoveryCoordinator(
            state_store,
            runtime_repository,
            intent_repository,
            managed_trade_repository,
            controller,
            reconciler,
        )

        self.store = state_store
        self.runtime_repository = runtime_repository
        self.intent_repository = intent_repository
        self.managed_trade_repository = managed_trade_repository
        self.coordination_store = coordination_store
        self.controller = controller
        self.writer = writer
        self.coordinator = coordinator
        self.startup_service = StartupRecoveryService(
            self.settings,
            self.reader,
            self.snapshot_builder,
            coordinator,
            runtime_repository,
            managed_trade_repository,
        )
        self.execution_service = ExecutionService(
            intent_repository,
            writer,
            controller,
            reconciler,
        )

    def _prepare_state_database(self) -> None:
        if self.settings.state_mode is not RuntimeStateMode.RESTORE:
            return
        checkpoint = self.settings.restore_checkpoint
        if checkpoint is None:
            raise ValueError("restore checkpoint is required for RESTORE state mode")
        if self.paths.state_database.exists():
            raise FileExistsError(
                f"restore target already exists; refusing to overwrite {self.paths.state_database}"
            )
        restore_runtime_checkpoint(checkpoint, self.paths.state_database)

    def _initialize_first_risk_day(
        self,
        runtime_repository: RuntimeStateRepository,
        intent_repository: ExecutionIntentRepository,
        managed_trade_repository: ManagedTradeRepository,
        recovery_truth: MT5RecoveryTruth,
        now_utc: datetime,
    ) -> None:
        self._rollover_risk_day_if_safe(
            runtime_repository,
            intent_repository,
            managed_trade_repository,
            recovery_truth,
            now_utc,
        )
        bundle = runtime_repository.load_recovery_bundle()
        intent = intent_repository.load()
        trade = managed_trade_repository.load()
        if bundle.risk_day is not None:
            return
        if self.settings.state_mode is not RuntimeStateMode.INITIALIZE:
            return
        if self.store is None or not self.store.is_empty():
            # Unknown namespaces/events are still durable lifecycle state. Do
            # not overwrite that evidence with a new risk-day baseline.
            return
        if any(
            value is not None
            for value in (
                bundle.cooldown,
                bundle.active_opportunity,
                bundle.trade_plan,
                bundle.episode_risk,
                intent,
                trade,
            )
        ):
            # A partially populated state store is not a fresh installation. It
            # must be reconciled rather than silently receiving a new risk clock.
            return
        runtime_repository.save_risk_day(
            new_risk_day(
                now_utc,
                recovery_truth.snapshot.account.equity,
                manual_reset_enabled=self.settings.manual_reset_enabled,
            )
        )

    def _rollover_risk_day_if_safe(
        self,
        runtime_repository: RuntimeStateRepository,
        intent_repository: ExecutionIntentRepository,
        managed_trade_repository: ManagedTradeRepository,
        recovery_truth: MT5RecoveryTruth,
        now_utc: datetime,
    ) -> None:
        """Start a new UTC risk day only when lifecycle truth is unambiguous.

        The previous day's record remains in the append-only event history. An
        open managed trade or unresolved Intent prevents an automatic reset:
        the runtime must reconcile/flatten that lifecycle first instead of
        hiding it behind a fresh risk baseline.
        """

        state = runtime_repository.load_risk_day()
        if state is None or state.utc_day >= now_utc.date():
            return
        intent = intent_repository.load()
        trade = managed_trade_repository.load()
        if intent is not None and not intent.lifecycle_clear_for_new_intent:
            return
        if trade is not None:
            return
        if recovery_truth.snapshot.account.equity <= 0:
            return
        runtime_repository.save_risk_day(
            new_risk_day(
                now_utc,
                recovery_truth.snapshot.account.equity,
                manual_reset_enabled=self.settings.manual_reset_enabled,
            )
        )

    def _session_news_observation(
        self,
        market: MarketSnapshot,
        recovery_truth: MT5RecoveryTruth,
        now_utc: datetime,
    ) -> SessionNewsObservation:
        if self.session_news_provider is None:
            return SessionNewsObservation(
                unknown_session_news_permission("SESSION_NEWS_PROVIDER_UNCONFIGURED")
            )
        try:
            result = self.session_news_provider(market, recovery_truth, now_utc)
        except Exception as exc:
            return SessionNewsObservation(
                unknown_session_news_permission(
                    f"SESSION_NEWS_PROVIDER_FAILED:{type(exc).__name__}"
                )
            )
        if isinstance(result, SessionNewsObservation):
            return result
        if isinstance(result, SessionNewsPermission):
            return SessionNewsObservation(result)
        return SessionNewsObservation(
            unknown_session_news_permission("SESSION_NEWS_PROVIDER_INVALID")
        )


def unknown_session_news_permission(reason: str) -> SessionNewsPermission:
    """Return explicit fail-closed session/news truth when no provider exists."""

    market = MarketPermission(
        decision=HardDecision.UNKNOWN,
        state=MarketState.OPEN,
        reason=reason,
        new_entries_allowed=False,
        flatten_required=False,
    )
    news = NewsPermission(
        decision=HardDecision.UNKNOWN,
        state=NewsSafetyState.NEWS_SAFETY_UNKNOWN,
        reason="NEWS_SAFETY_UNKNOWN",
    )
    return SessionNewsPermission(
        decision=HardDecision.UNKNOWN,
        reasons=(reason, news.reason),
        flatten_required=False,
        market=market,
        news=news,
    )


def _runtime_scope(recovery_truth: MT5RecoveryTruth) -> str:
    account = recovery_truth.snapshot.account
    return f"{account.login}:{recovery_truth.snapshot.symbol}"


def _write_config(settings: Settings) -> MT5WriteConfig:
    if settings.mt5_magic is None or settings.mt5_deviation_points is None:
        raise ValueError("MT5 write configuration is required for live startup mode")
    return MT5WriteConfig(
        magic=settings.mt5_magic,
        deviation_points=settings.mt5_deviation_points,
        comment_prefix=settings.mt5_comment_prefix,
    )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("runtime timestamps must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("runtime timestamps must be UTC")
