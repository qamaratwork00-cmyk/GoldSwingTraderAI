"""Startup service that assembles recovery authorities from existing owners.

Recovery readiness means state/broker truth is understood well enough for the
runtime to resume governed operation. It does not mean a fresh entry is allowed:
a known daily lock, PRE_CLOSE or news blackout remains enforced later by its normal
execution authority without being misclassified here as corrupt/unknown recovery.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isclose

from goldswingtraderai.app.recovery import (
    RecoveryAuthorities,
    StartupRecoveryCoordinator,
    StartupRecoveryResult,
)
from goldswingtraderai.app.recovery_mt5 import MT5RecoveryTruth, build_mt5_recovery_truth
from goldswingtraderai.config import Settings
from goldswingtraderai.domain.enums import AccountMode, DataQuality, HardDecision
from goldswingtraderai.domain.market import MarketSnapshot
from goldswingtraderai.execution.models import AuthorityTrace
from goldswingtraderai.management import ManagedTrade, ManagedTradeRepository
from goldswingtraderai.market_data import MT5Reader, MarketSnapshotBuilder
from goldswingtraderai.persistence import RuntimeStateRepository
from goldswingtraderai.risk.engine import profile_policy, resolve_account_profile
from goldswingtraderai.risk.permissions import SessionNewsPermission
from goldswingtraderai.risk.state import risk_day_metrics


@dataclass(frozen=True, slots=True)
class StartupRuntimeResult:
    market_snapshot: MarketSnapshot
    recovery_truth: MT5RecoveryTruth
    authorities: RecoveryAuthorities
    recovery: StartupRecoveryResult


class StartupRecoveryService:
    """Initialize the shared MT5 read boundary and run governed recovery.

    The reader intentionally remains initialized after `run()` so a successful or
    recovering runtime can continue read-only observation. The owner must call
    `shutdown()` during process shutdown.
    """

    def __init__(
        self,
        settings: Settings,
        reader: MT5Reader,
        snapshot_builder: MarketSnapshotBuilder,
        coordinator: StartupRecoveryCoordinator,
        runtime_repository: RuntimeStateRepository,
        managed_trade_repository: ManagedTradeRepository,
    ) -> None:
        self.settings = settings
        self.reader = reader
        self.snapshot_builder = snapshot_builder
        self.coordinator = coordinator
        self.runtime_repository = runtime_repository
        self.managed_trade_repository = managed_trade_repository

    def run(
        self,
        *,
        session_news_permission: SessionNewsPermission,
        now_utc: datetime,
        allow_verified_not_created: bool = False,
    ) -> StartupRuntimeResult:
        _require_utc(now_utc)
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
        return self.recover_from_facts(
            market=market,
            recovery_truth=recovery_truth,
            session_news_permission=session_news_permission,
            now_utc=now_utc,
            allow_verified_not_created=allow_verified_not_created,
        )

    def recover_from_facts(
        self,
        *,
        market: MarketSnapshot,
        recovery_truth: MT5RecoveryTruth,
        session_news_permission: SessionNewsPermission,
        now_utc: datetime,
        allow_verified_not_created: bool = False,
    ) -> StartupRuntimeResult:
        """Run the same governed recovery sequence over one captured fact set."""

        _require_utc(now_utc)
        authorities = build_recovery_authorities(
            settings=self.settings,
            market=market,
            recovery_truth=recovery_truth,
            session_news_permission=session_news_permission,
            runtime_repository=self.runtime_repository,
            managed_trade_repository=self.managed_trade_repository,
            now_utc=now_utc,
        )
        recovery = self.coordinator.recover(
            recovery_truth.snapshot,
            authorities,
            now_utc,
            price_tolerance=recovery_truth.price_tolerance,
            allow_verified_not_created=allow_verified_not_created,
        )
        return StartupRuntimeResult(
            market_snapshot=market,
            recovery_truth=recovery_truth,
            authorities=authorities,
            recovery=recovery,
        )

    def shutdown(self) -> None:
        self.reader.shutdown()


def build_recovery_authorities(
    *,
    settings: Settings,
    market: MarketSnapshot,
    recovery_truth: MT5RecoveryTruth,
    session_news_permission: SessionNewsPermission,
    runtime_repository: RuntimeStateRepository,
    managed_trade_repository: ManagedTradeRepository,
    now_utc: datetime,
) -> RecoveryAuthorities:
    """Translate existing subsystem truth into startup-recovery hard authorities."""

    _require_utc(now_utc)
    trade = managed_trade_repository.load()
    return RecoveryAuthorities(
        account_identity=_account_identity_authority(settings, market, recovery_truth),
        market_data=_market_data_authority(market, recovery_truth),
        session_news=_session_news_truth_authority(session_news_permission),
        risk=_risk_state_authority(runtime_repository, recovery_truth, now_utc),
        position_capacity=_position_state_authority(recovery_truth, trade),
        execution_environment=_execution_environment_authority(recovery_truth),
    )


def _account_identity_authority(
    settings: Settings,
    market: MarketSnapshot,
    recovery_truth: MT5RecoveryTruth,
) -> AuthorityTrace:
    live = recovery_truth.snapshot.account
    snapshot_account = market.account
    if (
        snapshot_account.login != live.login
        or snapshot_account.server != live.server
        or snapshot_account.mode is not live.mode
    ):
        return AuthorityTrace(
            "account_identity",
            HardDecision.BLOCK,
            "BROKER_ACCOUNT_CHANGED_DURING_STARTUP",
        )
    if market.meta.symbol != recovery_truth.snapshot.symbol:
        return AuthorityTrace(
            "account_identity",
            HardDecision.BLOCK,
            "BROKER_SYMBOL_CHANGED_DURING_STARTUP",
        )
    if settings.allowed_account_login is not None and live.login != settings.allowed_account_login:
        return AuthorityTrace(
            "account_identity",
            HardDecision.BLOCK,
            "ACCOUNT_IDENTITY_MISMATCH",
        )
    if settings.allowed_server is not None and live.server != settings.allowed_server:
        return AuthorityTrace(
            "account_identity",
            HardDecision.BLOCK,
            "ACCOUNT_IDENTITY_MISMATCH",
        )
    return AuthorityTrace("account_identity", HardDecision.PASS, "ACCOUNT_IDENTITY_VERIFIED")


def _market_data_authority(
    market: MarketSnapshot,
    recovery_truth: MT5RecoveryTruth,
) -> AuthorityTrace:
    if market.meta.symbol != recovery_truth.snapshot.symbol:
        return AuthorityTrace("market_data", HardDecision.BLOCK, "MARKET_SYMBOL_MISMATCH")
    if market.quality is DataQuality.HEALTHY:
        return AuthorityTrace("market_data", HardDecision.PASS, "MARKET_DATA_HEALTHY")
    if market.quality is DataQuality.CORRUPT:
        return AuthorityTrace("market_data", HardDecision.BLOCK, "MARKET_DATA_CORRUPT")
    return AuthorityTrace(
        "market_data",
        HardDecision.UNKNOWN,
        f"MARKET_DATA_{market.quality.value}",
    )


def _session_news_truth_authority(permission: SessionNewsPermission) -> AuthorityTrace:
    """Require known safety truth, not permission for a new entry right now.

    Known PRE_CLOSE/news blackout is valid recovery truth. The normal execution
    gate still consumes the original BLOCK later and therefore cannot open a trade.
    """

    if permission.decision is HardDecision.UNKNOWN:
        reason = permission.reasons[0] if permission.reasons else "SESSION_NEWS_UNKNOWN"
        return AuthorityTrace("session_news", HardDecision.UNKNOWN, reason)
    if permission.decision is HardDecision.BLOCK:
        reason = permission.reasons[0] if permission.reasons else "SESSION_NEWS_KNOWN_BLOCK"
        return AuthorityTrace(
            "session_news",
            HardDecision.PASS,
            f"SESSION_NEWS_TRUTH_KNOWN:{reason}",
        )
    return AuthorityTrace("session_news", HardDecision.PASS, "SESSION_NEWS_TRUTH_KNOWN")


def _risk_state_authority(
    runtime_repository: RuntimeStateRepository,
    recovery_truth: MT5RecoveryTruth,
    now_utc: datetime,
) -> AuthorityTrace:
    """Verify durable daily-risk truth without turning a known lock into corruption."""

    state = runtime_repository.load_risk_day()
    if state is None:
        return AuthorityTrace("risk", HardDecision.UNKNOWN, "RISK_DAY_STATE_MISSING")
    if state.utc_day != now_utc.date():
        return AuthorityTrace("risk", HardDecision.UNKNOWN, "RISK_DAY_ROLLOVER_REQUIRED")
    profile = resolve_account_profile(state.day_start_equity)
    if profile is None or recovery_truth.snapshot.account.equity <= 0:
        return AuthorityTrace("risk", HardDecision.UNKNOWN, "RISK_STATE_INVALID")
    policy = profile_policy(profile)
    try:
        metrics = risk_day_metrics(
            state,
            recovery_truth.snapshot.account.equity,
            policy.daily_lock_pct,
        )
    except ValueError:
        return AuthorityTrace("risk", HardDecision.UNKNOWN, "RISK_STATE_INVALID")
    reason = "RISK_STATE_VALID_LOSS_LOCKED" if metrics.loss_locked else "RISK_STATE_VALID"
    return AuthorityTrace("risk", HardDecision.PASS, reason)


def _position_state_authority(
    recovery_truth: MT5RecoveryTruth,
    trade: ManagedTrade | None,
) -> AuthorityTrace:
    """Verify exposure truth/ownership context, not fresh-entry capacity itself."""

    positions = recovery_truth.snapshot.positions
    if trade is None:
        reason = "POSITION_STATE_CLEAR" if not positions else "EXTERNAL_GOLD_EXPOSURE_KNOWN"
        return AuthorityTrace("position_capacity", HardDecision.PASS, reason)

    matches = tuple(position for position in positions if position.ticket == trade.position_ticket)
    if len(matches) != 1:
        return AuthorityTrace(
            "position_capacity",
            HardDecision.UNKNOWN,
            "BOT_MANAGED_POSITION_RECONCILIATION_REQUIRED",
        )
    position = matches[0]
    if position.symbol != trade.symbol or position.direction is not trade.direction:
        return AuthorityTrace(
            "position_capacity",
            HardDecision.BLOCK,
            "BOT_MANAGED_POSITION_IDENTITY_MISMATCH",
        )
    if not isclose(position.volume, trade.volume, rel_tol=0.0, abs_tol=1e-8):
        return AuthorityTrace(
            "position_capacity",
            HardDecision.BLOCK,
            "BOT_MANAGED_POSITION_VOLUME_MISMATCH",
        )
    reason = (
        "BOT_MANAGED_POSITION_RECONCILED"
        if len(positions) == 1
        else "BOT_MANAGED_WITH_EXTERNAL_EXPOSURE_KNOWN"
    )
    return AuthorityTrace("position_capacity", HardDecision.PASS, reason)


def _execution_environment_authority(recovery_truth: MT5RecoveryTruth) -> AuthorityTrace:
    mode = recovery_truth.snapshot.account.mode
    if mode is AccountMode.DEMO:
        return AuthorityTrace(
            "execution_environment",
            HardDecision.PASS,
            "DEMO_ENVIRONMENT_VERIFIED",
        )
    if mode is AccountMode.OTHER:
        return AuthorityTrace(
            "execution_environment",
            HardDecision.BLOCK,
            "DEMO_GUARD_NOT_VERIFIED",
        )
    return AuthorityTrace(
        "execution_environment",
        HardDecision.UNKNOWN,
        "DEMO_GUARD_UNKNOWN",
    )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("startup time must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("startup time must be UTC")
