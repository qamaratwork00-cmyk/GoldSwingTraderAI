"""Pure/typed market-intelligence engines consuming normalized snapshots."""

from goldswingtraderai.intelligence.candle_structure import StructureConfig, analyze_structure
from goldswingtraderai.intelligence.indicators import QuantConfig, analyze_quant
from goldswingtraderai.intelligence.liquidity import LiquidityConfig, analyze_liquidity
from goldswingtraderai.intelligence.technical import TechnicalConfig, analyze_technical

__all__ = [
    "LiquidityConfig",
    "QuantConfig",
    "StructureConfig",
    "TechnicalConfig",
    "analyze_liquidity",
    "analyze_quant",
    "analyze_structure",
    "analyze_technical",
]
