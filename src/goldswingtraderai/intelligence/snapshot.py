"""Build one reusable multi-timeframe intelligence snapshot from market truth."""

from __future__ import annotations

from dataclasses import dataclass

from goldswingtraderai.domain.enums import Timeframe
from goldswingtraderai.domain.ids import EntityId
from goldswingtraderai.domain.market import MarketSnapshot
from goldswingtraderai.intelligence.candle_structure import (
    StructureConfig,
    StructureReport,
    analyze_structure,
)
from goldswingtraderai.intelligence.indicators import (
    QuantConfig,
    QuantReport,
    analyze_quant,
    compute_indicator_series,
)
from goldswingtraderai.intelligence.liquidity import (
    LiquidityConfig,
    LiquidityReport,
    analyze_liquidity,
)
from goldswingtraderai.intelligence.news import NewsFacts
from goldswingtraderai.intelligence.session import SessionConfig, SessionReport, analyze_session
from goldswingtraderai.intelligence.technical import (
    TechnicalConfig,
    TechnicalReport,
    analyze_technical,
)


@dataclass(frozen=True, slots=True)
class TimeframeIntelligence:
    timeframe: Timeframe
    quant: QuantReport
    structure: StructureReport
    technical: TechnicalReport
    liquidity: LiquidityReport


@dataclass(frozen=True, slots=True)
class IntelligenceSnapshot:
    market_snapshot_id: EntityId
    frames: tuple[TimeframeIntelligence, ...]
    session: SessionReport
    news: NewsFacts | None

    def for_timeframe(self, timeframe: Timeframe) -> TimeframeIntelligence:
        for frame in self.frames:
            if frame.timeframe is timeframe:
                return frame
        raise KeyError(f"timeframe not present: {timeframe}")


@dataclass(frozen=True, slots=True)
class IntelligenceConfig:
    quant: QuantConfig = QuantConfig()
    structure: StructureConfig = StructureConfig()
    technical: TechnicalConfig = TechnicalConfig()
    liquidity: LiquidityConfig = LiquidityConfig()
    session: SessionConfig = SessionConfig()

    def __post_init__(self) -> None:
        if self.quant.atr_period != self.structure.atr_period:
            raise ValueError("Quant and Structure must share one ATR period")


def build_intelligence_snapshot(
    market: MarketSnapshot,
    *,
    news: NewsFacts | None = None,
    holiday_context: bool = False,
    config: IntelligenceConfig | None = None,
) -> IntelligenceSnapshot:
    """Compute reusable market intelligence without broker/order authority."""

    cfg = config or IntelligenceConfig()
    price = (market.quote.bid + market.quote.ask) / 2.0
    frames: list[TimeframeIntelligence] = []

    for candle_series in market.series:
        candles = candle_series.candles
        indicators = compute_indicator_series(candles, cfg.quant)
        quant = analyze_quant(
            candles,
            candle_series.timeframe,
            cfg.quant,
            series=indicators,
        )
        structure = analyze_structure(
            candles,
            candle_series.timeframe,
            cfg.structure,
            atr_values=indicators.atr,
        )
        technical = analyze_technical(
            structure,
            quant,
            current_price=price,
            tick_size=market.symbol_spec.tick_size,
            config=cfg.technical,
        )
        liquidity = analyze_liquidity(
            candles,
            structure,
            quant,
            current_price=price,
            tick_size=market.symbol_spec.tick_size,
            config=cfg.liquidity,
        )
        frames.append(
            TimeframeIntelligence(
                timeframe=candle_series.timeframe,
                quant=quant,
                structure=structure,
                technical=technical,
                liquidity=liquidity,
            )
        )

    try:
        m5_candles = market.candles(Timeframe.M5)
    except KeyError:
        m5_candles = market.series[-1].candles
    session = analyze_session(
        m5_candles,
        market.meta.as_of_utc,
        holiday_context=holiday_context,
        config=cfg.session,
    )

    return IntelligenceSnapshot(
        market_snapshot_id=market.snapshot_id,
        frames=tuple(frames),
        session=session,
        news=news,
    )
