"""Technical zones, location and target-room context from confirmed structure.

This desk consumes structural/quant facts; it does not redefine swing or BOS/MSS
semantics and does not grant trading permission.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from goldswingtraderai.domain.enums import SwingRole, SwingSide, Timeframe
from goldswingtraderai.intelligence.candle_structure import StructureReport, SwingPoint
from goldswingtraderai.intelligence.indicators import QuantReport


class ZoneSide(StrEnum):
    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"


class ZoneState(StrEnum):
    ACTIVE = "ACTIVE"
    WEAKENING = "WEAKENING"
    BROKEN = "BROKEN"
    RETEST_CANDIDATE = "RETEST_CANDIDATE"
    RECLAIMED = "RECLAIMED"
    CONSUMED = "CONSUMED"
    STALE = "STALE"


class LocationCategory(StrEnum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    NEUTRAL = "NEUTRAL"
    POOR = "POOR"
    DANGEROUS = "DANGEROUS"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class TechnicalConfig:
    zone_atr_fraction: float = 0.15
    min_zone_ticks: int = 4
    merge_tolerance_atr: float = 0.10
    max_source_swings: int = 16
    excellent_distance_atr: float = 0.20
    good_distance_atr: float = 0.45
    dangerous_target_room_atr: float = 0.25

    def __post_init__(self) -> None:
        if self.zone_atr_fraction <= 0 or self.merge_tolerance_atr < 0:
            raise ValueError("zone normalization must be positive")
        if self.min_zone_ticks <= 0 or self.max_source_swings <= 0:
            raise ValueError("zone counts must be positive")
        if not 0 <= self.excellent_distance_atr <= self.good_distance_atr:
            raise ValueError("location-distance thresholds are invalid")
        if self.dangerous_target_room_atr < 0:
            raise ValueError("target-room threshold cannot be negative")


@dataclass(frozen=True, slots=True)
class TechnicalZone:
    side: ZoneSide
    timeframe: Timeframe
    lower: float
    upper: float
    state: ZoneState
    quality: float
    source_count: int
    protected_source: bool

    @property
    def midpoint(self) -> float:
        return (self.lower + self.upper) / 2.0

    def contains(self, price: float) -> bool:
        return self.lower <= price <= self.upper


@dataclass(frozen=True, slots=True)
class TechnicalReport:
    timeframe: Timeframe
    zones: tuple[TechnicalZone, ...]
    nearest_support: TechnicalZone | None
    nearest_resistance: TechnicalZone | None
    buy_location: LocationCategory
    sell_location: LocationCategory
    buy_target_room: float | None
    sell_target_room: float | None
    equilibrium: float | None
    conflict: bool
    coverage: float


def analyze_technical(
    structure: StructureReport,
    quant: QuantReport,
    *,
    current_price: float,
    tick_size: float,
    config: TechnicalConfig | None = None,
) -> TechnicalReport:
    """Convert confirmed structural pivots into adaptive zones/location facts."""

    if current_price <= 0 or tick_size <= 0:
        raise ValueError("price and tick size must be positive")
    if structure.timeframe is not quant.timeframe:
        raise ValueError("structure and quant timeframes must match")

    cfg = config or TechnicalConfig()
    atr = quant.atr
    raw = tuple(
        _zone_from_swing(swing, structure.timeframe, atr, tick_size, cfg)
        for swing in structure.swings[-cfg.max_source_swings :]
    )
    zones = _merge_compatible(raw, atr, cfg)
    support = _nearest_support(zones, current_price)
    resistance = _nearest_resistance(zones, current_price)

    buy_room = None if resistance is None else max(0.0, resistance.lower - current_price)
    sell_room = None if support is None else max(0.0, current_price - support.upper)
    buy_location = _location(
        current_price,
        support,
        buy_room,
        atr,
        cfg,
        positive_side=ZoneSide.SUPPORT,
    )
    sell_location = _location(
        current_price,
        resistance,
        sell_room,
        atr,
        cfg,
        positive_side=ZoneSide.RESISTANCE,
    )

    recent_high = next(
        (swing.price for swing in reversed(structure.swings) if swing.side is SwingSide.HIGH),
        None,
    )
    recent_low = next(
        (swing.price for swing in reversed(structure.swings) if swing.side is SwingSide.LOW),
        None,
    )
    equilibrium = (
        (recent_high + recent_low) / 2.0
        if recent_high is not None and recent_low is not None and recent_high > recent_low
        else None
    )
    conflict = any(
        left.side is not right.side
        and max(left.lower, right.lower) <= min(left.upper, right.upper)
        for index, left in enumerate(zones)
        for right in zones[index + 1 :]
    )

    coverage_parts = (
        bool(zones),
        atr is not None,
        support is not None or resistance is not None,
    )
    return TechnicalReport(
        timeframe=structure.timeframe,
        zones=zones,
        nearest_support=support,
        nearest_resistance=resistance,
        buy_location=buy_location,
        sell_location=sell_location,
        buy_target_room=buy_room,
        sell_target_room=sell_room,
        equilibrium=equilibrium,
        conflict=conflict,
        coverage=sum(coverage_parts) / len(coverage_parts),
    )


def _zone_from_swing(
    swing: SwingPoint,
    timeframe: Timeframe,
    atr: float | None,
    tick_size: float,
    cfg: TechnicalConfig,
) -> TechnicalZone:
    half_width = max(
        tick_size * cfg.min_zone_ticks,
        (atr or tick_size) * cfg.zone_atr_fraction,
    )
    role_bonus = 15.0 if swing.role is SwingRole.PROTECTED else 0.0
    quality = min(100.0, 35.0 + swing.significance_atr * 15.0 + role_bonus)
    return TechnicalZone(
        side=ZoneSide.RESISTANCE if swing.side is SwingSide.HIGH else ZoneSide.SUPPORT,
        timeframe=timeframe,
        lower=swing.price - half_width,
        upper=swing.price + half_width,
        state=ZoneState.ACTIVE,
        quality=quality,
        source_count=1,
        protected_source=swing.role is SwingRole.PROTECTED,
    )


def _merge_compatible(
    zones: tuple[TechnicalZone, ...],
    atr: float | None,
    cfg: TechnicalConfig,
) -> tuple[TechnicalZone, ...]:
    if not zones:
        return ()
    tolerance = (atr or 0.0) * cfg.merge_tolerance_atr
    merged: list[TechnicalZone] = []
    for zone in sorted(zones, key=lambda item: (item.side.value, item.lower)):
        if not merged:
            merged.append(zone)
            continue
        previous = merged[-1]
        compatible = previous.side is zone.side and zone.lower <= previous.upper + tolerance
        if not compatible:
            merged.append(zone)
            continue
        merged[-1] = TechnicalZone(
            side=previous.side,
            timeframe=previous.timeframe,
            lower=min(previous.lower, zone.lower),
            upper=max(previous.upper, zone.upper),
            state=ZoneState.ACTIVE,
            quality=min(100.0, max(previous.quality, zone.quality) + 5.0),
            source_count=previous.source_count + zone.source_count,
            protected_source=previous.protected_source or zone.protected_source,
        )
    return tuple(sorted(merged, key=lambda item: item.midpoint))


def _nearest_support(zones: tuple[TechnicalZone, ...], price: float) -> TechnicalZone | None:
    candidates = [zone for zone in zones if zone.side is ZoneSide.SUPPORT and zone.lower <= price]
    return max(candidates, key=lambda zone: zone.midpoint, default=None)


def _nearest_resistance(zones: tuple[TechnicalZone, ...], price: float) -> TechnicalZone | None:
    candidates = [zone for zone in zones if zone.side is ZoneSide.RESISTANCE and zone.upper >= price]
    return min(candidates, key=lambda zone: zone.midpoint, default=None)


def _location(
    price: float,
    supportive_zone: TechnicalZone | None,
    target_room: float | None,
    atr: float | None,
    cfg: TechnicalConfig,
    *,
    positive_side: ZoneSide,
) -> LocationCategory:
    if atr is None or atr <= 0:
        return LocationCategory.UNKNOWN
    if target_room is not None and target_room / atr < cfg.dangerous_target_room_atr:
        return LocationCategory.DANGEROUS
    if supportive_zone is None:
        return LocationCategory.NEUTRAL

    if supportive_zone.contains(price):
        distance_atr = 0.0
    elif positive_side is ZoneSide.SUPPORT:
        distance_atr = max(0.0, price - supportive_zone.upper) / atr
    else:
        distance_atr = max(0.0, supportive_zone.lower - price) / atr

    if distance_atr <= cfg.excellent_distance_atr:
        return LocationCategory.EXCELLENT
    if distance_atr <= cfg.good_distance_atr:
        return LocationCategory.GOOD
    if distance_atr <= 1.0:
        return LocationCategory.NEUTRAL
    return LocationCategory.POOR
