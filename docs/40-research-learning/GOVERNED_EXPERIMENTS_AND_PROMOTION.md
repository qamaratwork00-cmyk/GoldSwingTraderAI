# GoldSwingTraderAI — Governed Experiments and Promotion

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Champion/challenger lifecycle, final-holdout use, stress, shadow, DEMO canary, promotion, rollback and production-policy versioning.  
**Depends on:** `RESEARCH_AND_VALIDATION.md`, `GOVERNED_STRATEGY_DISCOVERY.md`, `AUTONOMOUS_STRATEGY_INVENTION.md`

## Purpose

Research may discover promising changes, but production policy changes require staged evidence and a reversible governance path.

> **A candidate can recommend itself. It cannot promote itself.**

## Champion and Challenger

The currently approved policy/strategy is the `CHAMPION`. A proposed improvement is a `CHALLENGER`.

A Challenger must be evaluated against the approved baseline, not merely show positive standalone performance.

## Candidate types

A governed candidate may change:

- strategy parameters;
- scoring weights;
- entry timing policy;
- chase/extension policy;
- target/trailing policy;
- regime suitability;
- declarative strategy recipe.

Hard safety semantics are not ordinary experiment candidates.

## Promotion pipeline

Conceptual chronology:

```text
PROPOSED
→ RESEARCHING
→ VALIDATED
→ LOCKED
→ FINAL HOLDOUT
→ STRESS / ROBUSTNESS
→ SHADOW
→ DEMO CANARY
→ PROMOTION_READY
→ PROMOTED
```

Alternative terminal states include `REJECTED`, `ROLLED_BACK` and `DISABLED`.

Exact sample thresholds remain open.

## Locked candidate

After independent validation selects a candidate, its semantics/parameters/code version are locked before final holdout.

Any material tweak creates a new candidate/version and restarts the required evidence cycle.

## Final holdout

The final holdout is one-shot for the locked Challenger. Failure rejects that candidate. Trying multiple alternates on the same holdout destroys its untouched status and is prohibited as a final-holdout claim.

## Stress gate

A holdout-passing candidate must survive reasonable stress such as:

- worse spread/slippage;
- execution delay;
- parameter perturbation;
- multiple market regimes/directions;
- missing optional evidence where allowed.

Fragile performance may reject the candidate despite good headline return.

## Shadow stage

In Shadow, the Challenger evaluates live/forward market data but has **zero broker-write authority**.

Record:

- agreement/disagreement with Champion;
- hypothetical entries/exits;
- extra false entries/missed moves;
- AvgR/capture/drawdown counterfactuals;
- regime/family differences.

Shadow P/L is counterfactual and must remain separate from actual broker P/L.

## DEMO Canary

After successful Shadow evidence, a Challenger may receive bounded DEMO authority through the normal Risk/Execution path.

Canary is intended to prove real broker timing, spread, fill, slippage, restart and lifecycle behaviour that replay cannot fully prove.

It never bypasses safety/risk.

## Promotion decision

Promotion should consider multiple objectives, for example:

- Net/Avg R;
- drawdown;
- Profit Factor;
- Capture Efficiency;
- Opportunity Recall;
- entry/exit efficiency;
- loss streak/risk distribution;
- execution friction;
- complexity/stability.

Tiny numerical improvement is not automatically material improvement. Comparable performance should prefer the simpler/more stable policy.

## Evidence packet

Every promotion should retain:

- Candidate ID/version;
- previous Champion;
- exact changes;
- selection/validation evidence;
- final-holdout result;
- stress result;
- Shadow result;
- Canary result;
- known weaknesses/limitations;
- rollback target;
- approval/promotion timestamp.

## Policy versioning

Trades/research records should retain the production policy/strategy/risk/execution versions relevant to their decisions.

Existing open trades should not silently switch to a newly promoted management policy mid-trade unless explicit compatibility/migration semantics are frozen. Their original strategy/management context remains attributable.

## Rollback

Every promotion requires a known-good rollback target where feasible.

Critical invariant/software violations may automatically disable the candidate/fallback to safe baseline. Performance-based rollback should avoid reacting to ordinary short losing streaks without evidence of actual regression.

Rollback history is permanent and auditable.

## Safety violation

A Challenger that attempts to bypass frozen risk/account/execution invariants is immediately disabled/rejected. Safety violations are not treated as parameters to learn around.

## State/schema compatibility

Promotion that changes durable-state schema must include validated migration/rollback compatibility. Uncertain migration blocks promotion.

## Evidence isolation

Keep environments distinct:

```text
REPLAY
VALIDATION
FINAL_HOLDOUT
SHADOW
DEMO_CANARY
MAIN_DEMO
```

Do not merge all results into one misleading performance series.

## Permanent promotion history

Promotion, rejection and rollback events remain durable and portable across laptops. Failed candidates are retained as research evidence.

## Dashboard visibility

Compact example:

```text
Champion        GSW-1.3
Challenger      GSW-1.4-C03
Stage           SHADOW
Holdout         PASS
Stress          PASS
Broker Authority NONE
```

If rejected, show the primary reason such as `FINAL_HOLDOUT_FAILED` or `INSUFFICIENT_FORWARD_SAMPLE`.

## Tests required

- candidate cannot skip required lifecycle stages;
- final-holdout one-shot enforcement;
- Shadow has zero broker authority;
- Canary still passes normal risk/execution path;
- self-promotion denied;
- critical safety violation disables candidate;
- open-trade policy version preserved;
- promotion/rollback history survives restart/migration;
- schema migration blocks unsafe promotion.

## Explicit non-goals

Governance must not:

- promote on development profit alone;
- let AI/research self-promote;
- silently mutate open-trade semantics;
- erase failed/rolled-back history;
- treat a few losses as automatic strategy failure.

## Open questions

- exact minimum samples and material-improvement tests;
- Shadow duration/episode requirement;
- DEMO Canary scope/volume/duration;
- promotion approval mechanism in V1;
- automatic rollback triggers versus operator review.