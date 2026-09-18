# GoldSwingTraderAI — Learning and AI Boundaries

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION  
**Version:** 0.2-implementation  
**Authority:** StrategyMemory, entry/exit learning, bounded adaptive influence, ML/AI limits, evidence isolation and baseline-degradation behaviour.  
**Depends on:** `RESEARCH_AND_VALIDATION.md`, `GOVERNED_STRATEGY_DISCOVERY.md`, `GOVERNED_EXPERIMENTS_AND_PROMOTION.md`, `../30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md`

## Purpose

Learning should improve opportunity ranking, entry timing and trade management from verified experience without turning production into an unstable self-mutating system.

> **Learning may observe, remember, research and propose. Production changes only through governed promotion.**

## Current implementation checkpoint

Implemented research owners include:

```text
research/metrics.py
research/learning.py
research/episode_journal.py
research/discovery.py
research/invention.py
research/promotion.py
```

Current deterministic foundation provides:

- actual/counterfactual outcome separation;
- MFE/MAE/realized-R/capture/opportunity metrics;
- version/context-aware StrategyMemory summaries;
- bounded adaptive scoring influence;
- durable research episode feed;
- candidate creation/suppression, rejected memory and promotion governance.

This is software behaviour, not proof that any learned adjustment improves future profitability. Wider replay/ablation and DEMO forward evidence remain required.

## Evidence sources

Learning may consume versioned records for:

- taken trades;
- missed opportunities;
- rejected/blocked opportunities;
- invalidated opportunities;
- entry/exit decisions;
- MFE/MAE/capture metrics;
- strategy/session/regime context;
- execution/slippage data;
- optional technical-confluence evidence such as Trendline/Fibonacci/POC;
- fault/system-health attribution.

Counterfactual outcomes remain separately labelled from actual P/L.

## StrategyMemory

Each production family may maintain version-aware performance memory across interpretable contexts such as:

- BUY versus SELL;
- trend/range/transition regime;
- volatility regime;
- session/context;
- liquidity/location states;
- optional confluence states where enough evidence exists.

Small samples produce low confidence. `3 wins from 3 trades` is not strong proof.

## Recency versus long-term evidence

Memory may combine recent, medium and longer-term version-specific evidence. Recent deterioration may reduce confidence without instantly deleting a historically valid strategy.

Exact windows/weighting remain research calibration.

## Bounded adaptive influence

Validated StrategyMemory may provide a bounded scoring/ranking adjustment. It nudges rather than dominates explicit market structure.

Example:

```text
base opportunity 78
validated memory support +3
```

Not:

```text
historically weak session → universal hard block
```

Hard safety/risk is never learned away.

The same principle applies to Trendline/Fibonacci/POC: learning may discover that particular confluence is more/less useful in certain contexts, but it may not silently turn optional confluence into universal mandatory gating.

## Entry learning

Entry learning studies, by family/context where meaningful:

- ideal structural entry zone;
- approved entry versus actual fill;
- early/optimal/late/chased classification;
- MAE/MFE after entry;
- pullback/retest depth;
- breakout acceptance timing;
- Trendline/Fib/POC contribution where present;
- chase/extension blocks;
- second-chance outcomes;
- missed-entry cost.

Recurring evidence may create an Entry Policy Challenger. It must not directly alter production timing thresholds.

## Exit learning

Exit learning studies:

- MFE versus realized R;
- Capture Efficiency;
- Premature Exit Cost;
- structural trail quality;
- runner capture;
- profit given back;
- regime/timeframe effects on M5/M15/H1 management.

A profitable trade can still reveal poor capture. A losing trade can still be a valid setup and normal statistical loss.

Recurring evidence may create an Exit/Trade-Management Challenger; production remains unchanged until governed promotion.

## Attribution before adaptation

Learning must distinguish whether a poor result belongs to:

- strategy/opportunity;
- optional confluence contribution;
- entry timing;
- Trade Plan/stop geometry;
- execution/slippage;
- exit/trailing;
- system fault;
- normal statistical variance.

Do not reduce strategy score because execution was faulty, loosen exits because one valid trade lost normally, or remove many opportunities because a popular confluence feature happened to correlate with a small sample.

## Learning authority levels

```text
L0 Observation only
L1 Research recommendation
L2 Validated bounded scoring adjustment
L3 Shadow Challenger
L4 DEMO Canary
L5 Approved production policy
```

No candidate may jump levels outside promotion governance.

## ML usage

ML may be researched for bounded tasks such as opportunity ranking, regime classification, probability estimates, clustering/pattern discovery and feature importance.

V1 production authority remains interpretable. A black-box model score alone must not become broker authority.

## AI supervisor boundaries

AI may help explain why BUY/SELL/WAIT/BLOCK occurred, what failed, what research found and candidate hypotheses.

AI must not directly call broker execution, alter risk limits, or self-promote policies.

## Hard prohibitions

Learning/AI must never automatically:

- martingale/increase risk after losses or wins;
- bypass daily loss/news/account/broker safety;
- redefine original R;
- treat unknown broker state as safe;
- generate/execute arbitrary Python strategy code;
- turn optional Trendline/Fibonacci/POC into universal hard requirements without governed evidence;
- change production because of tiny sample;
- self-promote a Challenger.

## Baseline degradation

Learning is an enhancement, not the only source of strategy semantics.

If optional learning state is unavailable but frozen baseline remains independently valid:

```text
Learning: DEGRADED/OFFLINE
Adaptive influence: DISABLED
Baseline policy: ACTIVE
```

Likewise, failure/unavailability of optional Trendline/Fib/POC confluence should not disable the base strategy floor unless an unrelated critical data-integrity issue exists.

Critical risk/order/persistence corruption does not receive this fallback.

## Persistence and portability

StrategyMemory, entry/exit learning, candidates, genealogy, promotion history and rejected-hypothesis memory are durable machine-independent state as their repositories/adapters implement them.

Laptop migration must preserve identities/evidence versions. Current project policy allows strategy/learning artifacts in public recovery backups; authority-bearing credentials/keys/tokens remain excluded.

## Evidence isolation

Do not silently combine evidence from:

```text
REPLAY
SHADOW
DEMO_CANARY
MAIN_DEMO
```

or materially different strategy/policy versions.

Confluence ablation must also distinguish base-strategy evidence from base+confluence evidence so research can measure actual marginal value.

## Dashboard visibility

Compact target:

```text
Strategy Memory   READY
Entry Learning    ACTIVE
Exit Learning     ACTIVE
Discovery Health  IDLE / HEALTHY / DEGRADED
Champion          ...
Challenger        ...
Stage             ...
Adaptive Impact   BOUNDED / OFF
```

## Tests required / current evidence

Deterministic tests cover bounded StrategyMemory behaviour, evidence/context isolation, discovery liveness, candidate governance and persistence in the relevant research suites.

Still required for full validation:

- larger historical replay samples;
- confluence ablation with Opportunity Recall/trade-frequency impact;
- entry/exit challenger evidence across regimes;
- Shadow/DEMO forward evidence;
- migration/recovery integration in final runtime.

## Explicit non-goals

Learning/AI must not:

- promise self-improving profitability;
- replace explicit hard safety;
- make every recent pattern a new rule;
- hide why a learned adjustment exists;
- require retraining from zero after laptop change;
- maximize headline accuracy by silently suppressing too many valid trades.

## Open questions / calibration

- exact StrategyMemory windows/confidence model;
- maximum bounded adaptive influence;
- which ML tasks, if any, reach V1 production;
- exact minimum samples for entry/exit learning;
- exact persisted StrategyMemory/export schema beyond current implementation;
- context-specific value of Trendline/Fibonacci/POC after ablation.
