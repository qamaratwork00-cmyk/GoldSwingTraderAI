# GoldSwingTraderAI — Scoring and Decision Fusion

**Status:** PROVISIONAL  
**Version:** 0.3-implementation-baseline  
**Authority:** Analytical scoring, independent BUY/SELL thesis fusion, conflict handling and Red-Team attribution.  
**Depends on:** `STRATEGY_FLOOR.md`, `ENTRY_TIMING.md`, `TRADE_PLAN.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Core principle

Specialist/strategy desks operate in parallel. Final analytical quality is not a simple average and no single soft-evidence desk automatically kills a valid opportunity.

> **BUY and SELL are separate theses. Strong opposition means conflict, not hidden confidence. Hard safety/risk stays outside weighted scoring.**

## Phase 4 implementation checkpoint

Implemented in:

```text
src/goldswingtraderai/decisions/fusion.py
src/goldswingtraderai/decisions/snapshot.py
```

`fusion.py` publishes:
- independent `ThesisReport` for BUY and SELL;
- directional edge;
- conflict score;
- Opportunity score;
- evidence coverage;
- confidence;
- Red-Team objections.

`decisions/snapshot.py` is the coherent read-only Phase-4 orchestration path:

```text
IntelligenceSnapshot
→ StrategyFloorReport
→ DecisionBoard
→ Opportunity lifecycle
→ EntryTimingResult where applicable
→ DecisionSnapshot
```

This pipeline has no monetary risk or broker-write authority.

## Independent BUY and SELL theses

Each thesis is built from the same six family reports. Current baseline ranks family cases and combines the strongest three with bounded weights rather than summing all six.

Initial baseline:

```text
primary family     65%
secondary family   25%
tertiary family    10%
```

If two leading same-direction families are strong, a small bounded synergy may be added. If their named evidence substantially overlaps, that synergy is reduced to avoid pretending correlated facts are independent proof.

These weights/thresholds are calibratable implementation defaults, not frozen market truth.

## Conflict

`conflict_score` preserves the strength of the opposing thesis. A high BUY and high SELL case therefore remains visibly conflicted.

The baseline applies only a modest bounded analytical penalty when both sides are strong; it does not turn conflict into a universal hard blocker.

Example meaning:

```text
BUY 88 / SELL 25 → clear BUY edge
BUY 88 / SELL 84 → high conflict despite BUY leading
```

## Opportunity Score versus Entry Timing

Opportunity answers:

> Is the market idea worth pursuing?

Entry Timing separately answers:

> Is the current M5 moment efficient enough to enter?

Phase 4 keeps these separate. A strong Opportunity cannot magically convert a severely extended entry into ENTER; the setup normally remains alive as WAIT.

## Evidence coverage and UNKNOWN

Coverage tracks how much expected evidence was actually available. Optional missing inputs are omitted/reweighted where defined rather than automatically scoring zero.

Required hard truth such as future news-safety or account/order integrity is not represented here as weighted analytical evidence.

## Red Team

Current baseline objections include:

```text
STRONG_OPPOSING_THESIS
LOW_EVIDENCE_COVERAGE
LEADING_FAMILY_CONFLICTS
ENTRY_EXTENDED
CORRELATED_FAMILY_SUPPORT
NO_DIRECTIONAL_EDGE
```

These are analytical objections. They may lower confidence or explain WAIT, but they do not impersonate risk/execution hard blockers.

Future replay may refine Red-Team calibration while preserving this separation.

## Score bands

Conceptual human bands remain useful for interpretation:

```text
0–49   weak/no edge
50–64  developing/watch
65–74  valid/armable
75–84  strong
85–100 exceptional
```

They are not automatic broker-entry rules. Exact implementation thresholds are configuration baselines and must be validated through replay.

## Final action architecture

The full future system distinguishes:

```text
ENTER BUY
ENTER SELL
WAIT
MISSED
INVALID
BLOCKED
```

Phase 4 currently owns only analytical `ENTER/WAIT/MISSED/INVALID`. `BLOCKED` belongs to later hard safety/risk/execution authority.

This distinction is intentional: Decision Fusion must never invent a hard blocker it does not own.

## Would otherwise trade / hard blocker attribution

These remain later integration responsibilities once risk/session/news/execution authorities exist. The later centralized result will preserve:
- primary/secondary hard blockers;
- analytical DecisionSnapshot;
- `Would Otherwise Trade` counterfactual where meaningful.

Phase 4 does not fake those states before the owning subsystems exist.

## Persistence / research

Decision/family/opportunity IDs, scores, evidence, conflict and reasons will later be journaled with policy versions. Phase 4 already creates stable `opportunity_id` and `episode_id` contracts in memory; Phase 6 will make lifecycle state durable.

## Dashboard visibility

Future dashboard should show at least:

```text
BUY Thesis
SELL Thesis
Directional Edge
Conflict
Opportunity
Entry Timing
Coverage / Confidence
Red-Team objection
Final analytical action
```

Hard blocker display must come from its owning later subsystem.

## Tests / current evidence

`tests/test_strategy_decisions.py` currently proves:
- independent strong BUY/SELL conflict remains visible;
- bounded family fusion does not erase opposition;
- surviving opportunity identity remains stable;
- strategy/decision code has no broker-write boundary;
- coherent `DecisionSnapshot` can be built from one `IntelligenceSnapshot`.

Full replay ablation/calibration and persistence attribution remain later phases.

## Explicit non-goals

Decision Fusion must not:
- let score override hard risk/news/broker/data authority;
- convert every missing optional primitive into bearish/zero evidence;
- invent hard blockers;
- hide strong opposing evidence;
- treat counterfactual blocked trades as executed P/L;
- query MT5 directly.

## Open calibration questions

- family fusion weights;
- maximum synergy bonus;
- conflict penalty surface;
- Red-Team thresholds;
- minimum evidence coverage;
- Opportunity thresholds;
- later final-trade-score presentation once Trade Plan/risk/execution exist.
