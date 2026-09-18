# GoldSwingTraderAI — Trade Manager and Exit

**Status:** PROVISIONAL  
**Version:** 0.2-design  
**Authority:** Post-entry position-management behaviour

## Core principle

Open positions are managed by a second parallel decision floor. The system should not close a high-quality large move merely because a small profit threshold has been reached. Exit and protection decisions are driven primarily by structure, continuation, reversal evidence and remaining target opportunity while the market remains safely tradeable.

V1 intentionally avoids carrying bot-managed Gold positions through a known scheduled XAU market closure. Large-move capture is therefore intraday/open-session capture, not scheduled-gap exposure.

## Core management outputs

The trade manager exposes at least:

- Continuation Score
- Reversal Score
- Structure Integrity
- Candle Health
- Momentum / Expansion Health
- Target Remaining / Liquidity Path
- Protection Need
- Session/Pre-Close Exit Requirement

The final management action is one of:

- `HOLD`
- `PROTECT`
- `TRAIL`
- `RUNNER`
- `EXIT`

## HOLD

Use when the original thesis remains healthy and no better protective structure has been earned. Small opposite candles or ordinary pullbacks are not sufficient reason to exit a swing/intraday expansion trade.

`HOLD` is not permitted to override a mandatory PRE_CLOSE flatten requirement.

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

A trade may continue beyond its initial structural target while the market remains open and safely executable when:

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

A runner still must be flattened before the scheduled XAU closure according to the Session/Risk State Machine. The bot does not intentionally carry a runner through the daily market break or weekend in V1.

## EXIT

Exit should normally require meaningful evidence that the original thesis has failed or that the intended move has reached a terminal condition.

Examples include combinations of:

- material M15 structural break;
- failed reclaim;
- strong opposing displacement;
- credible opposite MSS/reversal structure;
- major target reached with continuation collapse;
- severe execution/session safety requirement.

A single RSI reading or one opposite candle is not sufficient by itself.

### Mandatory pre-close exit

`PRE_CLOSE_FLATTEN` is an explicit session-safety exit and does not require reversal evidence. When the Session/Risk State Machine enters the frozen pre-close flatten window, any bot-managed Gold position must be closed through the normal governed execution path while the broker remains tradeable.

This policy exists because the reopen price is not guaranteed to match the prior close and a market gap can jump beyond an intended SL.

If close acknowledgement is ambiguous or the broker becomes unavailable before flatten completes, the system must preserve the unresolved exposure and reconcile it; it must not mark the position closed merely because the session ended.

## Original R and lifecycle

Original risk distance and original R definition must remain immutable for analytics and restart recovery even after stops move. Trailing/protection cannot redefine historical risk to make performance appear better.

A PRE_CLOSE exit is journaled as a session-policy exit so research can separately measure how much favorable movement, if any, was forgone by the no-carry policy.

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
- normalized 100/200/300+ pip move capture where meaningful;
- PRE_CLOSE exit frequency and foregone/avoided gap exposure where measurable without lookahead abuse.

The aim is to improve both downside control and the system's ability to remain in large directional moves during tradeable market hours.
