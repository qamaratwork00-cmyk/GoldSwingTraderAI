# GoldSwingTraderAI — Trade Plan

**Status:** PROVISIONAL — IMPLEMENTED BASELINE  
**Version:** 0.4-implementation  
**Authority:** Pre-entry structural entry reference, invalidation, initial SL geometry, target hierarchy, original R, RR and plan quality.  
**Depends on:** `STRATEGY_FLOOR.md`, `ENTRY_TIMING.md`, `../10-market-intelligence/CANDLE_STRUCTURE.md`, `../10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md`, `../10-market-intelligence/LIQUIDITY_AND_SMC.md`

## Purpose

The Trade Plan converts a valid market opportunity into an executable market-structure plan before monetary sizing or broker submission.

> **Strategy decides whether the idea is worth pursuing. Trade Plan defines how that idea would be entered, invalidated and targeted. Risk then decides whether the account can safely afford it.**

## Current implementation checkpoint

Implemented in:

```text
src/goldswingtraderai/decisions/trade_plan.py
src/goldswingtraderai/persistence/runtime_state.py
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

Current calibration baselines are explicit, not frozen profitability truth:

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

The Trade Plan contains no monetary sizing or raw broker-write authority.

## Price identities

The system distinguishes:

- Signal Price;
- Approved Entry Reference;
- Executable Quote;
- Actual Fill Price.

Execution/broker components own the last two; they do not rewrite historical signal/plan fields.

The planning baseline uses snapshot Ask for BUY and snapshot Bid for SELL as the Approved Entry Reference. The centralized execution path then freshly revalidates executable quote, price drift, risk, target room and broker geometry immediately before any irreversible submit.

## Structural invalidation first

The initial stop starts from:

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

The initial broker SL is based on:

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

At plan/fill establishment, approved original risk distance defines `1R` for lifecycle and research accounting.

Once established, **original R is immutable** even if the stop later moves into profit.

Trade management may track current open risk separately, but it must never redefine historical R.

## Target hierarchy — V1 frozen direction

Targets are market objectives, not fixed 100/200/300-pip TPs.

The plan distinguishes:

- **Immediate Obstacle** — nearby opposing structure/liquidity that may affect path quality;
- **Primary Structural Target** — first meaningful structural objective and management checkpoint;
- **Expansion Target** — normal larger move objective when the path remains credible;
- **Runner Objective** — further objectively defined structural/liquidity objective used only when continuation earns extension.

The existence of multiple objectives does not require multiple broker TP orders or partial closes.

### Primary target is a checkpoint

Reaching Primary Structural Target does not by itself require full exit. Trade Manager evaluates acceptance/rejection, continuation, reversal evidence and remaining target room.

### Initial broker TP policy

V1 does not use a fixed-pip broker TP.

Where a valid Expansion Target exists, it is the default initial broker TP objective. If no valid Expansion Target exists but Primary itself passes the frozen RR/path-quality policy, Primary may be used.

A broker TP is a market-objective protection mechanism. Trade Manager may move the objective to a validated Runner Objective through the governed execution path when fresh continuation evidence justifies extension.

Profit alone cannot justify extension. Any extension requires a fresh objectively defined target and the rules in `TRADE_MANAGER_AND_EXIT.md`.

## Target quality and path quality

A target may expose quality context based on:

- structural significance;
- freshness;
- higher-timeframe relevance;
- liquidity concentration;
- distance;
- intervening opposing structure;
- clean/crowded path.

Target/path quality supports plan evaluation and post-entry management.

## Structural RR — V1 frozen initial guard

The plan calculates at least Primary RR, Expansion RR and Runner RR where available.

```text
Credible structural target room < 1.20R   → POOR / no new entry
1.20R to <1.50R                           → MARGINAL / conditional only
1.50R to <2.00R                           → GOOD
2.00R+                                    → STRONG
3.00R / 4.00R+                            → large-move / runner potential, not guaranteed
```

### Conditional `1.20R–<1.50R` plans

A marginal plan may proceed only when normal opportunity/timing requirements pass **and** there is a credible larger expansion path. Initial V1 expects roughly `2.0R+` Expansion Target room with acceptable path quality for this exception.

A plan below `1.20R` is rejected/degraded for the current entry geometry rather than rescued by a high strategy score.

RR is evaluated together with Stop Quality, Target Quality, Path Quality, entry location and freshness. High theoretical RR cannot rescue fragile stop geometry or an unrealistic path.

Higher RR/strategy score does **not** authorize higher monetary risk.

## Price drift and deterioration

A previously valid plan may degrade before submission.

Fresh executable price can reduce target room or increase risk:

```text
VALID → READY → DEGRADED
```

A degraded entry may return to `WAIT` while the Opportunity remains ARMED.

The implemented execution checks revalidate fresh quote, drift, risk, stop geometry and hard execution constraints. The decision/trade-plan path retains the original approved reference for attribution.

## Plan lifecycle

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

Execution records executable quote/fill/slippage separately without rewriting the original plan.

## Partial profit — V1 baseline

V1 core trading logic does **not** depend on partial closes. This is essential for minimum-lot accounts where `0.01` may be indivisible.

The full position is managed through HOLD/PROTECT/TRAIL/RUNNER/EXIT. Partial-profit policies may be researched later for larger divisible volumes but are not required for V1 correctness.

## Persistence and restart

`RuntimeStateRepository` persists the active TradePlan, objectives, original-R basis and Opportunity/Episode lineage. Recovery cross-validates those identities rather than silently accepting mismatched state.

For an actual open managed trade, `ManagedTradeRepository` carries forward broker position lineage, original/current SL/TP and objective stage. Broker positions/orders/deals remain current exposure truth.

A restored plan must be revalidated against fresh market/broker facts before it can produce a new execution.

## Trade Manager integration

The implemented Trade Manager consumes the structural objectives/original-R context from the plan and manages HOLD/PROTECT/TRAIL/RUNNER/EXIT. Primary is a checkpoint, Expansion is the normal initial objective, and runner extension requires fresh evidence plus a real next objective.

Management modifications/close actions still pass through the centralized one-shot execution and broker-verification path.

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

If degraded/rejected, show the exact reason such as `PRICE_DRIFT`, `STOP_FRAGILE_WAIT_FOR_BETTER_GEOMETRY` or `TARGET_ROOM_POOR`.

## Replay/research

Plan creation, degradation, objective progression and invalidation must remain chronological. Phase-10 replay/research can evaluate RR bands, stop quality, target path, missed opportunities and management capture without future leakage.

Calibration must optimize Net R/drawdown/capture/opportunity recall together rather than improving headline win rate by eliminating too many valid trades.

## Tests / current evidence

Deterministic coverage includes:

- structural BUY/SELL stop geometry;
- volatility-aware buffer baseline;
- broker stop constraint cannot silently redesign thesis;
- invalid plans expose missing geometry explicitly;
- Immediate Obstacle does not automatically become Primary;
- immutable original-R basis;
- `<1.20R` rejection/degradation;
- `1.20R–<1.50R` requires credible `~2R+` expansion path;
- `1.50R+` GOOD and `2R+` STRONG classification;
- Expansion Target selected as initial broker objective when valid;
- structural stop unchanged when risk/min-lot cannot afford plan;
- V1 logic does not require partial closes;
- TradePlan persistence/recovery lineage;
- fresh execution checks preserve the approved structural plan;
- Trade Manager objective progression and broker-verified modifications.

## Explicit non-goals

Trade Plan must not:

- size the account lot;
- move SL to fit desired risk;
- place raw orders;
- use fixed pip targets as market truth;
- force full exit merely because Primary was touched;
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
