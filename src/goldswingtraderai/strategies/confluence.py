"""Positive-only strategy confluence bonuses.

Trendline, Fibonacci and POC context may strengthen an already-existing strategy
hypothesis, but they never reduce a family score, become mandatory evidence, or
grant risk/execution permission.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from goldswingtraderai.domain.enums import Direction, StrategyFamily, Timeframe
from goldswingtraderai.intelligence.confluence import LineEvent, PocRelation
from goldswingtraderai.intelligence.snapshot import IntelligenceSnapshot, TimeframeIntelligence
from goldswingtraderai.strategies.floor import (
    DirectionalFamilyCase,
    FamilyReport,
    StrategyFloorReport,
)


_MAX_SCORE_BONUS = 6.0


@dataclass(frozen=True, slots=True)
class ConfluenceBonusConfig:
    """Enable individual soft-confluence sources without changing their semantics.

    Production defaults keep every implemented source enabled. Research may disable
    sources for ablation; disabling a source can only remove its positive bonus and
    can never create a penalty or hard gate.
    """

    trendline: bool = True
    fibonacci: bool = True
    poc: bool = True


def apply_optional_confluence(
    report: StrategyFloorReport,
    intelligence: IntelligenceSnapshot,
    config: ConfluenceBonusConfig | None = None,
) -> StrategyFloorReport:
    """Apply bounded positive-only confluence without creating a new hard filter."""

    cfg = config or ConfluenceBonusConfig()
    m15 = intelligence.for_timeframe(Timeframe.M15)
    m5 = intelligence.for_timeframe(Timeframe.M5)
    families = tuple(_boost_family(family, m15, m5, cfg) for family in report.families)
    return StrategyFloorReport(families=families)


def _boost_family(
    report: FamilyReport,
    m15: TimeframeIntelligence,
    m5: TimeframeIntelligence,
    config: ConfluenceBonusConfig,
) -> FamilyReport:
    return replace(
        report,
        buy=_boost_case(report.family, Direction.BUY, report.buy, m15, m5, config),
        sell=_boost_case(report.family, Direction.SELL, report.sell, m15, m5, config),
    )


def _boost_case(
    family: StrategyFamily,
    direction: Direction,
    case: DirectionalFamilyCase,
    m15: TimeframeIntelligence,
    m5: TimeframeIntelligence,
    config: ConfluenceBonusConfig,
) -> DirectionalFamilyCase:
    supports = _support_labels(family, direction, m15, config) + _support_labels(
        family,
        direction,
        m5,
        config,
    )
    if not supports:
        return case

    unique = tuple(dict.fromkeys(supports))
    # One valid confluence source is useful, while stacking several correlated
    # technical tools cannot inflate a strategy by more than six score points.
    bonus = min(_MAX_SCORE_BONUS, 2.5 + 1.25 * (len(unique) - 1))
    return replace(
        case,
        score=min(100.0, case.score + bonus),
        evidence=tuple(dict.fromkeys((*case.evidence, *unique))),
    )


def _support_labels(
    family: StrategyFamily,
    direction: Direction,
    frame: TimeframeIntelligence,
    config: ConfluenceBonusConfig,
) -> tuple[str, ...]:
    confluence = frame.confluence
    if confluence is None:
        return ()

    output: list[str] = []
    support = confluence.support_trendline
    resistance = confluence.resistance_trendline

    if config.trendline and family is StrategyFamily.TREND_PULLBACK_CONTINUATION:
        if direction is Direction.BUY and support is not None and support.event in {
            LineEvent.TOUCH,
            LineEvent.RECLAIM,
        }:
            output.append("TRENDLINE_PULLBACK_SUPPORT")
        if direction is Direction.SELL and resistance is not None and resistance.event in {
            LineEvent.TOUCH,
            LineEvent.RECLAIM,
        }:
            output.append("TRENDLINE_PULLBACK_RESISTANCE")

    if config.trendline and family in {
        StrategyFamily.BREAKOUT_EXPANSION,
        StrategyFamily.BREAKOUT_RETEST_CONTINUATION,
        StrategyFamily.COMPRESSION_EXPANSION,
    }:
        if direction is Direction.BUY and resistance is not None and resistance.event is LineEvent.BREAK:
            output.append("TRENDLINE_BREAK_BUY")
        if direction is Direction.SELL and support is not None and support.event is LineEvent.BREAK:
            output.append("TRENDLINE_BREAK_SELL")

    fib = confluence.fibonacci
    if config.fibonacci and fib is not None and fib.direction is direction:
        if fib.in_core_retracement:
            output.append("FIB_CORE_RETRACEMENT")
        elif fib.in_deep_retracement:
            output.append("FIB_DEEP_RETRACEMENT")

    # POC is direction-neutral. It only joins an already-directional technical
    # confluence label so "price near POC" cannot manufacture a thesis by itself.
    profile = confluence.volume_profile
    if config.poc and output and profile is not None and profile.relation is PocRelation.NEAR:
        output.append("POC_LOCATION_CONFLUENCE")

    return tuple(output)
