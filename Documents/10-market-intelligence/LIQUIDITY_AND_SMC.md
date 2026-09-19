# GoldSwingTraderAI — Liquidity and SMC Evidence

**Status:** PROVISIONAL
**Version:** 0.1-liquidity
**Authority:** Pools, sweeps, acceptance, FVG, qualified OB and liquidity path

## Question answered

What observable liquidity existed before price interacted with it, and did the
interaction accept or reject beyond that liquidity?

## Causal pipeline

~~~mermaid
flowchart TB
    STRUCT["Confirmed swings + completed candles"] --> POOLS["Clustered buy-side/sell-side pools"]
    POOLS --> EVENTS["Probe, sweep or accepted break"]
    EVENTS --> FVG["Three-candle FVG lifecycle"]
    EVENTS --> OB["Break-tied qualified Order Block"]
    EVENTS --> PATH["Nearest liquidity and path quality"]
    FVG --> REPORT["LiquidityReport"]
    OB --> REPORT
    PATH --> REPORT
~~~

The pool must exist before a sweep. A qualified OB needs a structural
consequence. A label without the causal prerequisite is not accepted evidence.

## Pool and event states

Pools cluster nearby highs/lows using ATR/tick-aware tolerance so one area is not
double-counted. Sources can be internal or structural and carry significance.

~~~text
UNTOUCHED | APPROACHED | PROBED | SWEPT | RECLAIMED | ACCEPTED_BEYOND
~~~

Events:

- PROBE: price enters/takes a level without proven acceptance outcome;
- CONFIRMED_SWEEP: existing pool is penetrated and failed acceptance/reclaim
  evidence follows;
- ACCEPTED_BREAK: completed candles accept beyond the existing pool.

A wick alone is not a sweep.

## FVG and Order Block

FVG is a deterministic three-candle imbalance with direction, bounds,
created_at, fill fraction and:

~~~text
FRESH | PARTIAL | MITIGATED
~~~

An Order Block is a qualified origin zone tied to meaningful break evidence:

~~~text
FRESH | TESTED | INVALIDATED
~~~

FVG and OB are supporting primitives, not mandatory conditions for every
strategy family.

## Liquidity path

~~~text
OPEN | MIXED | CROWDED | UNKNOWN
~~~

Nearest buy-side/sell-side liquidity, density and intervening structure inform
target room and runner quality. A liquidity pool is a possible objective, not a
guaranteed target.

## Correlation rule

Sweep, rejection, MSS, FVG and OB can describe one market episode. Strategy
fusion must not add every label as independent certainty. The report carries
bounded evidence and provenance.

## Implementation and tests

| Source | Responsibility | Tests |
|---|---|---|
| intelligence/liquidity.py | pool clustering, events, FVG, OB and path | test_technical_liquidity.py |
| intelligence/snapshot.py | shared composition | test_intelligence_snapshot.py |
| strategies/floor.py | family-specific use | test_strategy_decisions.py |
| research/replay.py | chronological primitive states | test_research_validation.py |

Tests cover pool-before-sweep chronology, accepted versus rejected breaks, FVG
mitigation, qualified OB requirements, clustering and correlated evidence.

## Dashboard and replay

The dashboard may show nearest BSL/SSL, sweep/reclaim state and path. Replay
must not create a pool only because a later bar swept it. Missing optional
liquidity primitives reduce coverage, not by silently becoming bearish.

## Explicit non-goals

This desk does not redefine structure, create a standalone SMC strategy,
guarantee liquidity targets, size risk or touch the broker.

