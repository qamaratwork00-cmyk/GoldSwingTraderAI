"""Pure post-entry evidence derivation and HOLD/PROTECT/TRAIL/RUNNER/EXIT decisions."""

from __future__ import annotations

from dataclasses import dataclass

from goldswingtraderai.domain.enums import (
    CandleSequenceState,
    Direction,
    LiquidityPath if False else Direction,  # type: ignore[syntax]
)
