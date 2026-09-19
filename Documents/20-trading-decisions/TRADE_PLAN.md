# GoldSwingTraderAI — Structural Trade Plan

**Status:** PROVISIONAL
**Version:** 0.1-trade-plan
**Authority:** Entry reference, invalidation, SL, objectives, RR and original R

## Purpose

The Trade Plan freezes market geometry before account affordability enters the
calculation.

~~~mermaid
flowchart TB
    OPPORTUNITY["Analytically ready opportunity"] --> ENTRY["Approved Entry Reference"]
    ENTRY --> INVALID["Structural invalidation"]
    INVALID --> STOP["Initial SL + volatility/tick buffer"]
    STOP --> OBJECTIVES["Obstacle, Primary, Expansion, Runner"]
    OBJECTIVES --> QUALITY["Stop, path, target and RR quality"]
    QUALITY --> PLAN["TradePlan — READY / DEGRADED / INVALID"]
    PLAN --> RISK["Risk Engine"]
~~~

## Four price identities

| Identity | Meaning | Owner |
|---|---|---|
| Signal Price | price at analytical observation | decision/trade plan |
| Approved Entry Reference | intended entry zone/price used for drift | decision/trade plan |
| Executable Quote | fresh broker price before submit | execution |
| Actual Fill | broker result | execution/reconciliation |

Execution must not rewrite the original plan to make slippage look harmless.

## Structural invalidation and initial SL

The first question is: what price behaviour proves the thesis wrong?

Possible references are protected pullback swing, breakout failure boundary,
sweep extreme/reclaim failure, failed-break extreme, range boundary or
displacement origin. The family supplies semantics; Trade Plan produces
deterministic geometry.

Initial SL:

~~~text
structural invalidation
+ ATR/noise-aware buffer
+ broker tick/stop normalization
~~~

If broker constraints would materially redesign the geometry, the plan becomes
DEGRADED/INVALID. It is not silently rescued by moving the stop.

## Target hierarchy

~~~text
Immediate Obstacle
→ Primary Structural Target
→ Expansion Target
→ Runner Objective
~~~

Primary is normally a management checkpoint. A valid Expansion Target is the
normal initial broker TP. Runner extension requires fresh continuation and a
new objective. No fixed-pip target is used.

## RR guard

~~~text
below 1.20R            → reject current geometry
1.20R to below 1.50R   → conditional; credible roughly 2R expansion needed
1.50R to below 2.00R   → good
2.00R or more          → strong
3R/4R or more          → potential, not guarantee
~~~

RR never increases monetary risk. Stop quality, path, location and freshness
matter alongside arithmetic.

## Original R and lifecycle

Original approved risk distance establishes 1R once. It never changes after
trailing or protection. Plan states include DRAFT, VALID, READY, DEGRADED,
EXPIRED, INVALID and EXECUTED.

TradePlan stores IDs, direction, family/version, reference, invalidation, SL,
buffer, stop quality, objectives, broker TP objective, original risk/R,
Primary/Expansion/Runner RR, quality, freshness and reasons.

## Implementation and tests

decisions/trade_plan.py owns plan construction. persistence/runtime_state.py
stores the active plan and lineage. Tests are in test_trade_plan_risk.py and
management/replay suites.

## Dashboard, research and failure

The dashboard shows entry reference, SL/quality, objectives, RR and exact
degradation reason. Replay creates plans chronologically and keeps signal,
quote and fill identities separate. Missing structural geometry returns
explicit None/INVALID, never placeholder prices.

## Explicit non-goals

Trade Plan does not size lot, decide account affordability, call MT5, force full
exit at Primary or extend objectives merely because price is profitable.

