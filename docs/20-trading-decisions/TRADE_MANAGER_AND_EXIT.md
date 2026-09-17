# GoldSwingTraderAI — Trade Manager and Exit

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Post-entry position-management behaviour

## Core principle

Open positions are managed by a second parallel decision floor. The system should not close a high-quality large move merely because a small profit threshold has been reached. Exit and protection decisions are driven primarily by structure, continuation, reversal evidence and remaining target opportunity.

## Core management outputs

The trade manager exposes at least:

- Continuation Score
- Reversal Score
- Structure Integrity
- Candle Health
- Momentum / Expansion Health
- Target Remaining / Liquidity Path
- Protection Need

The final management action is one of:

- `HOLD`
- `PROTECT`
- `TRAIL`
- `RUNNER`
- `EXIT`

## HOLD

Use when the original thesis remains healthy and no better protective structure has been earned. Small opposite candles or ordinary pullbacks are not sufficient reason to exit a swing/intraday expansion trade.

## PROTECT

Use when enough progress and confirmed structure justify reducing risk without suffocating the trade. Protection should be based on a proven new structural reference rather than a fixed small-profit trigger alone.

## TRAIL

Trailing should primarily follow confirmed market structure with volatility-aware buffering.

For a BUY trade the hierarchy may evolve from:

```text
original structural stop
→ confirmed M5 protected swing when appropriate
→ confirmed M15 higher low
→ M15 continuation structure
→ H1 runner structure for extended moves
```

The exact precedence and eligibility thresholds remain open to research/freeze.

The stop may tighten but must never intentionally widen beyond the original approved risk.

## RUNNER

A trade may continue beyond its initial structural target when:

- the original target is being accepted/broken rather than strongly rejected;
- directional structure remains intact;
- continuation evidence remains credible;
- reversal evidence remains limited;
- a next objective is objectively defined.

The system should distinguish:

- Primary Structural Target
- Expansion Target
- Runner Objective

TP must not be moved endlessly just because price moves in the trade's favour.

## EXIT

Exit should require meaningful evidence that the original thesis has failed or that the intended move has reached a terminal condition.

Examples include combinations of:

- material M15 structural break;
- failed reclaim;
- strong opposing displacement;
- credible opposite MSS/reversal structure;
- major target reached with continuation collapse;
- severe execution/session safety requirement.

A single RSI reading or one opposite candle is not sufficient by itself.

## Original R and lifecycle

Original risk distance and original R definition must remain immutable for analytics and restart recovery even after stops move. Trailing/protection cannot redefine historical risk to make performance appear better.

## Partial profit

Partial-profit logic is not frozen. The design must remain complete without relying on partial closes because minimum-lot accounts may not support meaningful partial reduction.

## Research requirements

Post-trade research should measure at least:

- MFE / MAE;
- realized R;
- move-capture efficiency;
- premature-exit cost;
- profit given back after runner decisions;
- structural trail quality;
- 2R / 3R / 4R reach rates;
- normalized 100/200/300+ pip move capture where meaningful.

The aim is to improve both downside control and the system's ability to remain in large directional moves.
