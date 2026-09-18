# GoldSwingTraderAI — Trade Plan

**Status:** PROVISIONAL — IMPLEMENTED BASELINE  
**Version:** 0.3-implementation  
**Authority:** Pre-entry structural entry reference, invalidation, initial SL geometry, target hierarchy, original R, RR and plan quality.  
**Depends on:** `STRATEGY_FLOOR.md`, `ENTRY_TIMING.md`, `../10-market-intelligence/CANDLE_STRUCTURE.md`, `../10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md`, `../10-market-intelligence/LIQUIDITY_AND_SMC.md`

## Purpose

The Trade Plan converts a valid market opportunity into an executable market-structure plan before monetary sizing or broker submission.

> **Strategy decides whether the idea is worth pursuing. Trade Plan defines how that idea would be entered, invalidated and targeted. Risk then decides whether the account can safely afford it.**

## Current implementation checkpoint

Phase 5 implements this authority in:

```text
src/goldswingtraderai/decisions/trade_plan.py
```

Implemented deterministic flow:

```text
READY Opportunity
→ Signal Price + Approved Entry Reference
→ family-aware structural invalidation
→ ATR/noise buffer + outward tick normalization
→ Initial SL + Stop Quality
→ Immediate / Primary / Expansion / Runner objectives
→ frozen structural RR guard
→ READY / DEGRADED / INVALID TradePlan
```

Current implementation/calibration baselines are explicit, not frozen profitability truth:

```text
ATR stop buffer            0.12 ATR, minimum 4 ticks
Fragile risk distance      <0.20 ATR
Acceptable-risk threshold  0.45 ATR
Fragile buffer             <0.06 ATR
Robust-buffer threshold    0.10 ATR
Meaningful target quality  55/100
Target merge tolerance     0.06 ATR
Marginal path quality      55/100
```

These values remain `CALIBRATE IN RESEARCH` under `../90-governance/OPEN_QUESTIONS.md`. The frozen `1.20R / 1.50R / 2.00R` economics below are unchanged.

A nearby low-quality internal objective may be retained as **Immediate Obstacle** while a farther meaningful structural/liquidity objective becomes **Primary Target**. This prevents a minor internal level from automatically killing an otherwise valid large-move setup while still exposing the obstacle to timing/management.

If structural invalidation or required ATR geometry cannot be defined, an `INVALID` plan carries missing stop geometry explicitly as `None`; it never fabricates placeholder SL/R values. Risk/execution cannot treat such a plan as ready.

The implementation contains no monetary sizing or broker-write call.

## Price identities

The system must distinguish:

- Signal Price;
- Approved Entry Reference;
- Executable Quote;
- Actual Fill Price.

Execution/broker documents own the last two; they must not overwrite historical signal/plan fields.

The current Phase-5 implementation uses snapshot Ask for a BUY planning reference and snapshot Bid for a SELL planning reference. This is **not** the final executable quote; Phase 7 must freshly revalidate quote, drift, risk and broker geometry before any irreversible submit.

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

Current baseline gives reversal families finer M5-first invalidation preference, while continuation/breakout families prefer M15 first; both may fall back through confirmed/protected structure and meaningful technical zones. Exact family refinements remain research-calibratable.

## Initial SL

The initial broker SL should be based on:

```text
structural invalidation
+ volatility/noise-aware buffer
+ broker-valid normalization
```

The buffer may consider ATR, wick/noise distribution, zone width and symbol tick/point precision. ATR assists; it does not replace structure.

If broker constraints would materially distort the structural plan, the plan becomes `INVALID/UNEXECUTABLE` rather than silently inventing a new thesis or widening/tightening the stop.

## Stop quality

States:

```text
ROBUST
ACCEPTABLE
FRAGILE
INVALID
```

Stop quality considers whether ordinary market noise can hit the SL while the underlying thesis remains intact.

A very tight SL with attractive theoretical RR is not automatically a good plan. In the current baseline, `FRAGILE` geometry degrades the entry to WAIT/rebuild rather than invalidating the underlying opportunity by itself.

## Account independence

The Trade Plan must not tighten/widen its structural SL to make the account's desired lot size fit. Account affordability belongs to `../30-risk-execution/RISK_CONTRACT.md`.

## Original R

At plan/fill establishment, the approved original risk distance defines `1R` for lifecycle and research accounting.

Once established, **original R is immutable** even if the stop later moves into profit.

Trade management may track current open risk separately, but it must never redefine historical R.

## Target hierarchy — V1 frozen direction

Targets are market objectives, not fixed 100/200/300-pip TPs.

The plan distinguishes:

- **Immediate Obstacle** — nearby opposing structure/liquidity that may affect path quality;
- **Primary Structural Target** — first meaningful structural objective and management checkpoint;
- **Expansion Target** — the normal larger move objective when the path remains credible;
- **Runner Objective** — a further objectively defined structural/liquidity objective used only when continuation earns extension.

The existence of multiple objectives does not require multiple broker TP orders or partial closes.

### Primary target is a checkpoint, not an automatic full exit

Reaching the Primary Structural Target does not by itself require the whole position to close. Trade Manager evaluates acceptance/rejection, continuation, reversal evidence and remaining target room.

### Initial broker TP policy

V1 does not use a fixed-pip broker TP.

Where a valid Expansion Target exists, it is the default initial broker TP objective. If no valid Expansion Target exists but the Primary Structural Target itself passes the frozen RR/path-quality policy, the Primary Target may be used as the initial broker TP.

A broker TP is a market-objective protection mechanism; it does not prevent Trade Manager from moving the objective to a validated Runner Objective before price reaches it when fresh continuation evidence justifies extension.

The manager may not remove/extend a TP merely because price is profitable. Any extension requires a fresh objectively defined next target and the post-entry rules in `TRADE_MANAGER_AND_EXIT.md`.

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

## Structural RR — V1 frozen initial guard

The plan calculates at least:

- Primary RR;
- Expansion RR;
- Runner RR where a runner objective exists.

Initial V1 target-room classification is:

```text
Credible structural target room < 1.20R   → POOR / no new entry
1.20R to <1.50R                           → MARGINAL / conditional only
1.50R to <2.00R                           → GOOD
2.00R+                                    → STRONG
3.00R / 4.00R+                            → large-move / runner potential, not guaranteed
```

### Conditional `1.20R–<1.50R` plans

A marginal plan may proceed only when the normal opportunity/timing requirements pass **and** there is a credible larger expansion path rather than merely a nearby small target. Initial V1 expects the Expansion Target to provide at least about `2.0R` room with acceptable path quality for this exception.

A plan with credible target room below `1.20R` is rejected/degraded for the current entry geometry rather than accepted merely because strategy score is high.

RR is still evaluated with Stop Quality, Target Quality, Path Quality, entry location and freshness. High theoretical RR cannot rescue a fragile stop or unrealistic path.

A larger RR/strategy score does **not** authorize higher monetary risk; monetary sizing remains independently owned by Risk Contract.

## Price drift and deterioration

A previously valid plan may degrade before submission.

Before execution, fresh price may materially reduce target room or increase risk. Possible state transition:

```text
VALID → READY → DEGRADED
```

A degraded entry may return to `WAIT` while the opportunity remains ARMED.

Execution must revalidate fresh quote, RR, target room, stop geometry and chase state before sending.

## Plan lifecycle

States:

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

A TradePlan retains as applicable:

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
- initial broker TP objective/type;
- original risk distance/R basis;
- Primary/Expansion/Runner RR;
- Target/Path/Plan quality;
- created time/freshness/expiry;
- reason and invalidation reason.

Execution later appends executable quote/fill/slippage without rewriting the original plan.

## Partial profit — V1 baseline

V1 core trading logic does **not depend on partial closes**. This is essential for minimum-lot accounts where `0.01` may be indivisible.

The baseline position is managed as one risk-bearing position using HOLD/PROTECT/TRAIL/RUNNER/EXIT. Future research/version work may add partial-profit behaviour for larger executable volumes, but it is not required for V1 correctness and may not be assumed by strategy/exit logic.

## Dashboard visibility

Compact example:

```text
Entry Ref       4322.40
SL              4313.10  ROBUST
Primary         4336.50   1.52R
Expansion       4348.00   2.75R
Runner          4364.50   4.52R
Broker TP       EXPANSION
Plan Quality    88
```

If degraded or rejected, show the exact reason such as `PRICE_DRIFT`, `STOP_FRAGILE_WAIT_FOR_BETTER_GEOMETRY` or `TARGET_ROOM_POOR`.

## Replay and persistence

Plan creation, degradation, objective extension and invalidation must be chronological. Active/open-trade plan context, original R and objective identities must survive restart through the persistence contract.

Phase 6 adds durable persistence; Phase 5 currently provides the immutable typed plan contract/state only.

## Tests required / current evidence

Current deterministic tests cover:

- structural BUY/SELL stop geometry;
- volatility-aware buffer baseline;
- broker stop constraint cannot silently redesign the thesis;
- invalid plans expose missing geometry explicitly;
- Immediate Obstacle does not automatically become Primary target;
- immutable plan R basis;
- target room `<1.20R` degraded/rejected for current entry;
- `1.20R–<1.50R` requires credible `~2R+` expansion path;
- `1.50R+` GOOD and `2R+` STRONG classification;
- Expansion Target selected as initial broker objective when valid;
- structural stop remains unchanged when risk/min-lot cannot afford the plan;
- V1 logic does not require partial closes.

Later phases still must test fresh price-drift revalidation, persistence/restart and Trade Manager objective extension.

## Explicit non-goals

Trade Plan must not:

- size the account lot;
- move SL to fit desired risk;
- place orders;
- use fixed pip targets as market truth;
- force full exit merely because Primary Target was touched;
- endlessly extend targets without new structural evidence;
- redefine original R after trailing;
- turn every nearby internal level into a hard trade veto.

## Open calibration work

- family-specific invalidation refinements;
- volatility-buffer formula/thresholds;
- Stop Quality thresholds;
- target-significance/merge/path-quality thresholds;
- family/regime-specific refinements to the frozen initial RR guard after research;
- objective-quality thresholds for runner progression.
