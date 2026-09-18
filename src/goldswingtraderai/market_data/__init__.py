"""Read-only MT5 market-data boundary and normalized snapshot builder."""

from goldswingtraderai.market_data.mt5_reader import MT5Reader, MarketDataError
from goldswingtraderai.market_data.snapshot import MarketSnapshotBuilder

__all__ = ["MT5Reader", "MarketDataError", "MarketSnapshotBuilder"]
