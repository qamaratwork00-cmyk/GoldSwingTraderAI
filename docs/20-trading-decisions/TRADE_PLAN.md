# GoldSwingTraderAI — Trade Plan

**Status:** PROVISIONAL  
**Version:** 0.2-design  
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

A plan with credible target room below `1.20R` is rejected for the current entry geometry rather than accepted merely because strategy score is high.

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

If degraded or rejected, show the exact reason such as `PRICE_DRIFT` or `TARGET_ROOM_POOR`.

## Replay and persistence

Plan creation, degradation, objective extension and invalidation must be chronological. Active/open-trade plan context, original R and objective identities must survive restart through the persistence contract.

## Tests required

- family-specific invalidation geometry;
- volatility-aware buffer;
- broker normalization cannot silently redesign the thesis;
- Stop Quality noise checks;
- immutable original R;
- Primary/Expansion/Runner RR;
- target room `<1.20R` rejected;
- `1.20R–<1.50R` conditional plan requires credible larger expansion path;
- `1.50R+` good classification and `2.0R+` strong classification;
- Primary target is not automatically forced full exit;
- Expansion Target is default initial broker TP when valid;
- objective extension requires a validated Runner Objective rather than profit-only TP movement;
- price-drift degradation;
- opportunity remains ARMED when only timing/plan entry degrades;
- V1 remains correct with indivisible `0.01` position/no partial closes;
- restart persistence of original plan/objective context.

## Explicit non-goals

Trade Plan must not:

- size the account lot;
- move SL to fit desired risk;
- place orders;
- use fixed pip targets as market truth;
- force full exit merely because Primary Target was touched;
- endlessly extend targets without new structural evidence;
- redefine original R after trailing.

## Open questions

- exact family-specific invalidation models at V1 freeze;
- exact volatility-buffer formula;
- exact acceptable Stop Quality thresholds;
- family/regime-specific refinements to the frozen initial RR guard after research;
- exact objective-quality thresholds for runner progression.