# GoldSwingTraderAI — Governed Strategy Discovery

**Status:** PROVISIONAL
**Version:** 0.1-discovery
**Authority:** Evidence clustering, approved primitives, candidate creation and liveness

## Purpose

Discovery looks for recurring evidence that the current strategy floor explains
poorly. It creates bounded declarative candidates for governed evaluation.

## Liveness contract

~~~mermaid
flowchart TB
    EPISODES["Durable research episodes"] --> MAP["Approved primitive mapping"]
    MAP --> CLUSTER["Independent recurring cluster"]
    CLUSTER --> DECIDE{"Novel and eligible?"}
    DECIDE -->|"yes"| CANDIDATE["Durable CandidateRegistry entry"]
    DECIDE -->|"no"| SUPPRESS["Durable suppression reason"]
    CANDIDATE --> HEALTH["Discovery health"]
    SUPPRESS --> HEALTH
~~~

For every eligible cluster:

~~~text
candidate created
OR
explicit machine-readable suppression/rejection reason
~~~

If evidence disappears without either outcome, health is DEGRADED. Importing a
module is not discovery liveness.

## Discovery levels

1. Parameter discovery: bounded researchable values only.
2. Recipe discovery: combinations of approved declarative primitives.
3. Market-behaviour discovery: recurring patterns absent from the six families.

The search is evidence-driven, not unlimited random combinations.

## Approved primitive registry

The vocabulary includes structure trend/break/MSS, rejection, displacement,
compression, technical location, Trendline, Fibonacci, Volume Profile POC,
liquidity sweep, FVG, Order Block, EMA flow, RSI momentum, ATR volatility,
session context, target path and entry timing.

Trendline/Fibonacci/POC are research primitives, not mandatory production
filters. Unknown strings, executable code and hard-safety fields are rejected.

## Candidate discipline

Each candidate records typed ID, type VARIANT/NEW_FAMILY/ENTRY_POLICY/EXIT_POLICY,
parent family, trigger, required/optional primitives, regime, timing,
invalidation, target model, independent episode IDs, fingerprint, chronology
and current status.

Duplicate source IDs cannot inflate sample count. Similar candidates and
rejected candidates remain durable across restart.

## Complexity and safety

Recipes are bounded and prefer a small coherent pattern. Discovery cannot alter
DEMO, account, risk, no-lookahead, one-shot, controller, unknown-exposure or
original-R invariants.

## Source and tests

research/episode_journal.py maps durable evidence; discovery.py owns registry,
fingerprints and similarity; invention.py runs automatic clustering.

Tests: test_discovery_journal.py and test_discovery_invention.py.

## Dashboard/promotion boundary

Show IDLE, HEALTHY or DEGRADED, eligible cluster count, candidate count,
latest candidate, type/stage and suppression reason. Discovery only creates
PROPOSED candidates. Promotion owns later stages.

## Explicit non-goals

No arbitrary Python, production edit, hard-safety learning, self-promotion,
unlimited combinatorial search or silent confluence gating.

