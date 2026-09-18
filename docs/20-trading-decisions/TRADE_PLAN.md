# GoldSwingTraderAI — Trade Plan

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Pre-entry structural entry reference, invalidation, initial SL geometry, target hierarchy, original R, RR and plan quality.  
**Depends on:** `STRATEGY_FLOOR.md`, `ENTRY_TIMING.md`, `../10-market-intelligence/CANDLE_STRUCTURE.md`, `../10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md`, `../10-market-intelligence/LIQUIDITY_AND_SMC.md`

## Purpose

The Trade Plan converts a valid market opportunity into an executable market-structure plan before monetary sizing or broker submission.

> **Strategy decides whether the idea is worth pursuing. Trade Plan defines how that idea would be entered, invalidated and targeted. Risk then decides whether the account can safely afford it.**

## Price identities

The system must distinguish:

- Signal Price;
- Approved Entry Reference;
- Executable Quote;
- Actual Fill Price.

Execution/broker documents own the last two; they must not overwrite historical signal/plan fields.

## Structural invalidation first

The initial stop starts from the market question:

> **What price behaviour would prove this trade thesis no longer valid?**

Possible family-specific invalidation references include:

- protected pullback swing;
- breakout/retest failure boundary;
- sweep extreme/reclaim failure;
- failed-breakout extreme;
- range boundary;
- displacement origin/base where the family contract requires it.

The strategy family provides invalidation semantics. Trade Plan turns them into deterministic price geometry.

## Initial SL

The initial broker SL should be based on:

```text
structural invalidation
+ volatility/noise-aware buffer
+ broker-valid normalization
```

The buffer may consider ATR, wick/noise distribution, zone width and symbol tick/point precision. ATR assists; it does not replace structure.

If broker constraints would materially distort the structural plan, the plan becomes `UNEXECUTABLE` rather than silently inventing a new thesis.

## Stop quality

Suggested states:

```text
ROBUST
ACCEPTABLE
FRAGILE
INVALID
```

Stop quality considers whether ordinary market noise can hit the SL while the underlying thesis remains intact.

A very tight SL with attractive theoretical RR is not automatically a good plan.

## Account independence

The Trade Plan must not tighten/widen its structural SL to make the account's desired lot size fit. Account affordability belongs to `../30-risk-execution/RISK_CONTRACT.md`.

## Original R

At plan/fill establishment, the approved original risk distance defines `1R` for lifecycle and research accounting.

Once established, **original R is immutable** even if the stop later moves into profit.

Trade management may track current open risk separately, but it must never redefine historical R.

## Target hierarchy

Targets are market objectives, not fixed 100/200/300-pip TPs.

The plan should distinguish:

- Immediate Obstacle;
- Primary Structural Target;
- Expansion Target;
- Runner Objective.

These may use meaningful opposing structure, external liquidity, range boundaries and higher-timeframe objectives.

The existence of multiple objectives does not require multiple broker TP orders or partial closes.

## Target quality and path quality

A target should expose quality context based on factors such as:

- structural significance;
- freshness;
- higher-timeframe relevance;
- liquidity concentration;
- distance;
- intervening opposing structure;
- clean/crowded path.

Target/path quality supports plan evaluation and trade management.

## Structural RR

The plan should calculate at least:

- Primary RR;
- Expansion RR;
- Runner RR where a runner objective exists.

RR is evaluated together with Stop Quality, Target Quality, Path Quality, entry location and freshness. A universal arbitrary RR floor is not yet frozen.

## Price drift and deterioration

A previously valid plan may degrade before submission.

Before execution, fresh price may materially reduce target room or increase risk. Possible state transition:

```text
VALID → READY → DEGRADED
```

A degraded entry may return to `WAIT` while the opportunity remains ARMED.

Execution must revalidate fresh quote, RR, target room, stop geometry and chase state before sending.

## Plan lifecycle

Provisional states:

```text
DRAFT
VALID
READY
DEGRADED
EXPIRED
INVALID
EXECUTED
```

`DEGRADED` does not necessarily mean the underlying opportunity is invalid.

## Plan quality

A bounded Plan Quality score may combine:

- Stop Quality;
- Target Quality;
- Primary/Expansion RR;
- entry location;
- target-path quality;
- freshness;
- structural clarity.

Hard risk/broker safety remains outside this soft plan-quality score.

## Output contract

A TradePlan should retain at least:

- Trade Plan ID;
- Opportunity ID;
- Market Episode ID;
- strategy family/version;
- direction;
- signal price;
- approved entry reference/zone;
- invalidation type/level;
- initial SL and buffer;
- Stop Quality;
- Immediate Obstacle;
- Primary Target;
- Expansion Target;
- Runner Objective;
- original risk distance/R basis;
- Primary/Expansion/Runner RR;
- Target/Path/Plan quality;
- created time/freshness/expiry;
- reason and invalidation reason.

Execution later appends executable quote/fill/slippage without rewriting the original plan.

## Partial profit

The plan must remain complete for a single indivisible minimum-lot position. Partials may be added later when broker volume permits, but they are not a dependency of the core architecture.

## Dashboard visibility

Compact example:

```text
Entry Ref       4322.40
SL              4313.10  ROBUST
Primary         4348.00
Expansion       4364.50
Primary RR      2.75R
Plan Quality    88
```

If degraded, show the exact reason such as `PRICE_DRIFT` or `TARGET_ROOM_POOR`.

## Replay and persistence

Plan creation, degradation and invalidation must be chronological. Active/open-trade plan context, original R and objective identities must survive restart through the persistence contract.

## Tests required

- family-specific invalidation geometry;
- volatility-aware buffer;
- broker normalization cannot silently redesign the thesis;
- Stop Quality noise checks;
- immutable original R;
- Primary/Expansion/Runner RR;
- price-drift degradation;
- opportunity remains ARMED when only timing/plan entry degrades;
- restart persistence of original plan context.

## Explicit non-goals

Trade Plan must not:

- size the account lot;
- move SL to fit desired risk;
- place orders;
- use fixed pip targets as market truth;
- endlessly extend targets without new structural evidence;
- redefine original R after trailing.

## Open questions

- exact family-specific invalidation models at V1 freeze;
- exact volatility-buffer formula;
- exact acceptable Stop Quality thresholds;
- minimum structural RR by family, if any;
- initial broker TP policy versus managed objective-only approach;
- partial-profit support.