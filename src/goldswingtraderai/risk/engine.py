"""Broker-aware V1 monetary risk evaluation.

The engine sizes from account equity and the already-approved structural Trade Plan.
It never tightens the stop, never uses strategy score to raise risk, and evaluates
broker minimum volume rather than rejecting a raw size merely because it is <0.01.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import ceil, floor

from goldswingtraderai.decisions.trade_plan import PlanState, TradePlan
from goldswingtraderai.domain.enums import HardDecision
from goldswingtraderai.domain.market import MarketSnapshot
from goldswingtraderai.risk.state import (
    CooldownDecision,
    EpisodeRiskState,
    RiskDayMetrics,
    RiskDayState,
    can_enter_episode,
    risk_day_metrics,
)


class AccountProfile(StrEnum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    NORMAL = "NORMAL"


class RiskBand(StrEnum):
    CONSERVATIVE = "CONSERVATIVE"
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    EXCESSIVE = "EXCESSIVE"
    UNKNOWN = "UNKNOWN"


class SizingMode(StrEnum):
    MINIMUM_LOT = "MINIMUM_LOT"
    STEPPED_DYNAMIC = "STEPPED_DYNAMIC"
    DYNAMIC = "DYNAMIC"


@dataclass(frozen=True, slots=True)
class ProfilePolicy:
    profile: AccountProfile
    normal_low_pct: float
    normal_high_pct: float
    elevated_high_pct: float
    hard_ceiling_pct: float
    daily_lock_pct: float
    sizing_mode: SizingMode

    @property
    def target_pct(self) -> float:
        return (self.normal_low_pct + self.normal_high_pct) / 2.0


@dataclass(frozen=True, slots=True)
class RiskFriction:
    """Explicit V1 execution-friction reserve.

    Spread is diagnostic only here because Trade Plan entry uses the correct side
    of Bid/Ask, so entry-to-stop monetary geometry already includes it once.
    """

    slippage_reserve_ticks: float = 2.0
    commission_per_lot: float = 0.0

    def __post_init__(self) -> None:
        if self.slippage_reserve_ticks < 0 or self.commission_per_lot < 0:
            raise ValueError("risk friction cannot be negative")


@dataclass(frozen=True, slots=True)
class ExposureSnapshot:
    bot_gold_positions: int = 0
    external_gold_exposure: bool = False
    ownership_known: bool = True

    def __post_init__(self) -> None:
        if self.bot_gold_positions < 0:
            raise ValueError("position count cannot be negative")


@dataclass(frozen=True, slots=True)
class RiskContext:
    risk_day: RiskDayState
    cooldown: CooldownDecision
    episode: EpisodeRiskState
    fresh_structural_event: bool
    exposure: ExposureSnapshot = ExposureSnapshot()
    friction: RiskFriction = RiskFriction()


@dataclass(frozen=True, slots=True)
class RiskEvaluation:
    decision: HardDecision
    reason: str
    profile: AccountProfile | None
    sizing_mode: SizingMode | None
    risk_band: RiskBand
    target_risk_pct: float | None
    hard_ceiling_pct: float | None
    volume: float | None
    structural_risk_money: float | None
    friction_risk_money: float | None
    all_in_risk_money: float | None
    all_in_risk_pct: float | None
    spread_money_diagnostic: float | None
    estimated_margin: float | None
    day: RiskDayMetrics | None

    @property
    def passed(self) -> bool:
        return self.decision is HardDecision.PASS


_POLICIES = {
    AccountProfile.SMALL: ProfilePolicy(
        profile=AccountProfile.SMALL,
        normal_low_pct=3.0,
        normal_high_pct=4.5,
        elevated_high_pct=6.5,
        hard_ceiling_pct=7.0,
        daily_lock_pct=12.0,
        sizing_mode=SizingMode.MINIMUM_LOT,
    ),
    AccountProfile.MEDIUM: ProfilePolicy(
        profile=AccountProfile.MEDIUM,
        normal_low_pct=2.0,
        normal_high_pct=3.0,
        elevated_high_pct=4.5,
        hard_ceiling_pct=5.0,
        daily_lock_pct=9.0,
        sizing_mode=SizingMode.STEPPED_DYNAMIC,
    ),
    AccountProfile.NORMAL: ProfilePolicy(
        profile=AccountProfile.NORMAL,
        normal_low_pct=1.0,
        normal_high_pct=2.0,
        elevated_high_pct=3.5,
        hard_ceiling_pct=4.0,
        daily_lock_pct=7.0,
        sizing_mode=SizingMode.DYNAMIC,
    ),
}


def resolve_account_profile(equity: float) -> AccountProfile | None:
    """Resolve frozen V1 profiles; below-$100 policy remains explicitly deferred."""

    if equity >= 1000.0:
        return AccountProfile.NORMAL
    if equity >= 300.0:
        return AccountProfile.MEDIUM
    if equity >= 100.0:
        return AccountProfile.SMALL
    return None


def profile_policy(profile: AccountProfile) -> ProfilePolicy:
    return _POLICIES[profile]


def evaluate_risk(
    plan: TradePlan,
    market: MarketSnapshot,
    context: RiskContext,
) -> RiskEvaluation:
    """Return monetary PASS/BLOCK/UNKNOWN without broker-write side effects."""

    if plan.state is not PlanState.READY:
        return _result(HardDecision.BLOCK, "TRADE_PLAN_NOT_READY")
    if market.account.equity <= 0:
        return _result(HardDecision.UNKNOWN, "ACCOUNT_EQUITY_INVALID")

    # Profile is fixed for the UTC risk day instead of changing with intraday
    # floating P/L. This keeps daily-lock semantics stable near profile boundaries.
    profile = resolve_account_profile(context.risk_day.day_start_equity)
    if profile is None:
        return _result(HardDecision.UNKNOWN, "ACCOUNT_PROFILE_BELOW_100_DEFERRED")
    policy = profile_policy(profile)

    if context.risk_day.utc_day != market.meta.as_of_utc.date():
        return _result(
            HardDecision.UNKNOWN,
            "RISK_DAY_STATE_STALE",
            profile=profile,
            policy=policy,
        )
    day = risk_day_metrics(context.risk_day, market.account.equity, policy.daily_lock_pct)
    if day.loss_locked:
        return _result(
            HardDecision.BLOCK,
            "DAILY_LOSS_LIMIT_REACHED",
            profile=profile,
            policy=policy,
            day=day,
        )
    if context.cooldown is CooldownDecision.COOLDOWN:
        return _result(
            HardDecision.BLOCK,
            "LOSS_COOLDOWN_ACTIVE",
            profile=profile,
            policy=policy,
            day=day,
        )
    if context.episode.episode_id != plan.episode_id:
        return _result(
            HardDecision.UNKNOWN,
            "EPISODE_RISK_STATE_MISMATCH",
            profile=profile,
            policy=policy,
            day=day,
        )
    if not can_enter_episode(
        context.episode,
        fresh_structural_event=context.fresh_structural_event,
    ):
        return _result(
            HardDecision.BLOCK,
            "EPISODE_REENTRY_LIMIT",
            profile=profile,
            policy=policy,
            day=day,
        )

    exposure = context.exposure
    if not exposure.ownership_known:
        return _result(
            HardDecision.UNKNOWN,
            "POSITION_OWNERSHIP_UNKNOWN",
            profile=profile,
            policy=policy,
            day=day,
        )
    if exposure.external_gold_exposure:
        return _result(
            HardDecision.BLOCK,
            "EXTERNAL_GOLD_EXPOSURE",
            profile=profile,
            policy=policy,
            day=day,
        )
    if exposure.bot_gold_positions >= 1:
        return _result(
            HardDecision.BLOCK,
            "POSITION_CAPACITY_FULL",
            profile=profile,
            policy=policy,
            day=day,
        )

    spec = market.symbol_spec
    entry = plan.approved_entry_reference
    stop = plan.initial_stop
    stop_ticks = abs(entry - stop) / spec.tick_size
    if stop_ticks <= 0 or spec.tick_value <= 0:
        return _result(
            HardDecision.UNKNOWN,
            "SYMBOL_RISK_VALUE_UNKNOWN",
            profile=profile,
            policy=policy,
            day=day,
        )

    structural_per_lot = stop_ticks * spec.tick_value
    friction_per_lot = (
        context.friction.slippage_reserve_ticks * spec.tick_value
        + context.friction.commission_per_lot
    )
    all_in_per_lot = structural_per_lot + friction_per_lot
    if all_in_per_lot <= 0:
        return _result(
            HardDecision.UNKNOWN,
            "ALL_IN_RISK_UNAVAILABLE",
            profile=profile,
            policy=policy,
            day=day,
        )

    target_money = market.account.equity * policy.target_pct / 100.0
    raw_volume = target_money / all_in_per_lot
    volume, band = _choose_volume(raw_volume, all_in_per_lot, market.account.equity, spec, policy)
    if volume is None:
        min_risk_pct = all_in_per_lot * spec.volume_min / market.account.equity * 100.0
        reason = (
            "MIN_LOT_UNAFFORDABLE"
            if min_risk_pct > policy.hard_ceiling_pct
            else "RISK_ABOVE_ACCEPTABLE_BAND"
        )
        return _result(
            HardDecision.BLOCK,
            reason,
            profile=profile,
            policy=policy,
            day=day,
            risk_band=RiskBand.EXCESSIVE,
        )

    structural_money = structural_per_lot * volume
    friction_money = friction_per_lot * volume
    all_in_money = structural_money + friction_money
    risk_pct = all_in_money / market.account.equity * 100.0
    if risk_pct > policy.hard_ceiling_pct + 1e-9:
        return _result(
            HardDecision.BLOCK,
            "NEW_ENTRY_RISK_CEILING_EXCEEDED",
            profile=profile,
            policy=policy,
            day=day,
            risk_band=RiskBand.EXCESSIVE,
            volume=volume,
            structural_money=structural_money,
            friction_money=friction_money,
            all_in_money=all_in_money,
            all_in_pct=risk_pct,
        )

    estimated_margin = entry * spec.contract_size * volume / market.account.leverage
    if estimated_margin > market.account.margin_free + 1e-9:
        return _result(
            HardDecision.BLOCK,
            "ESTIMATED_MARGIN_INSUFFICIENT",
            profile=profile,
            policy=policy,
            day=day,
            risk_band=band,
            volume=volume,
            structural_money=structural_money,
            friction_money=friction_money,
            all_in_money=all_in_money,
            all_in_pct=risk_pct,
            estimated_margin=estimated_margin,
        )

    spread_ticks = market.quote.spread_price / spec.tick_size
    spread_money = spread_ticks * spec.tick_value * volume
    return _result(
        HardDecision.PASS,
        "RISK_PASS",
        profile=profile,
        policy=policy,
        day=day,
        risk_band=band,
        volume=volume,
        structural_money=structural_money,
        friction_money=friction_money,
        all_in_money=all_in_money,
        all_in_pct=risk_pct,
        spread_money=spread_money,
        estimated_margin=estimated_margin,
    )


def _choose_volume(
    raw_volume: float,
    all_in_per_lot: float,
    equity: float,
    spec,
    policy: ProfilePolicy,
) -> tuple[float | None, RiskBand]:
    candidates = _volume_candidates(raw_volume, spec.volume_min, spec.volume_max, spec.volume_step)
    scored = []
    for volume in candidates:
        risk_pct = all_in_per_lot * volume / equity * 100.0
        scored.append((volume, risk_pct, abs(risk_pct - policy.target_pct)))

    normal = [item for item in scored if item[1] <= policy.normal_high_pct + 1e-9]
    if normal:
        volume, risk_pct, _ = min(normal, key=lambda item: item[2])
        band = RiskBand.NORMAL if risk_pct >= policy.normal_low_pct else RiskBand.CONSERVATIVE
        return volume, band

    elevated = [item for item in scored if item[1] <= policy.elevated_high_pct + 1e-9]
    if elevated:
        volume, _, _ = min(elevated, key=lambda item: item[2])
        return volume, RiskBand.ELEVATED
    return None, RiskBand.EXCESSIVE


def _volume_candidates(
    raw_volume: float,
    volume_min: float,
    volume_max: float,
    volume_step: float,
) -> tuple[float, ...]:
    if raw_volume <= volume_min:
        return (round(volume_min, 8),)
    if raw_volume >= volume_max:
        return (round(volume_max, 8),)

    steps = (raw_volume - volume_min) / volume_step
    lower = volume_min + floor(steps) * volume_step
    upper = volume_min + ceil(steps) * volume_step
    values = {
        round(volume_min, 8),
        round(max(volume_min, min(volume_max, lower)), 8),
        round(max(volume_min, min(volume_max, upper)), 8),
    }
    return tuple(sorted(values))


def _result(
    decision: HardDecision,
    reason: str,
    *,
    profile: AccountProfile | None = None,
    policy: ProfilePolicy | None = None,
    day: RiskDayMetrics | None = None,
    risk_band: RiskBand = RiskBand.UNKNOWN,
    volume: float | None = None,
    structural_money: float | None = None,
    friction_money: float | None = None,
    all_in_money: float | None = None,
    all_in_pct: float | None = None,
    spread_money: float | None = None,
    estimated_margin: float | None = None,
) -> RiskEvaluation:
    return RiskEvaluation(
        decision=decision,
        reason=reason,
        profile=profile,
        sizing_mode=policy.sizing_mode if policy is not None else None,
        risk_band=risk_band,
        target_risk_pct=policy.target_pct if policy is not None else None,
        hard_ceiling_pct=policy.hard_ceiling_pct if policy is not None else None,
        volume=volume,
        structural_risk_money=structural_money,
        friction_risk_money=friction_money,
        all_in_risk_money=all_in_money,
        all_in_risk_pct=all_in_pct,
        spread_money_diagnostic=spread_money,
        estimated_margin=estimated_margin,
        day=day,
    )
