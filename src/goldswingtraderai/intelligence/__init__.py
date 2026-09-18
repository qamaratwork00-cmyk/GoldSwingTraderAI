"""Pure/typed market-intelligence engines consuming normalized snapshots."""

from goldswingtraderai.intelligence.candle_structure import StructureConfig, analyze_structure
from goldswingtraderai.intelligence.indicators import QuantConfig, analyze_quant

__all__ = ["QuantConfig", "StructureConfig", "analyze_quant", "analyze_structure"]
