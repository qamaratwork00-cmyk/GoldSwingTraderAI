# GoldSwingTraderAI — Learning and AI Boundaries

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** StrategyMemory, entry/exit learning, bounded adaptive influence, ML/AI limits, evidence isolation and baseline-degradation behaviour.  
**Depends on:** `RESEARCH_AND_VALIDATION.md`, `GOVERNED_STRATEGY_DISCOVERY.md`, `GOVERNED_EXPERIMENTS_AND_PROMOTION.md`, `../30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md`

## Purpose

Learning should improve opportunity ranking, entry timing and trade management from verified experience without turning production into an unstable self-mutating system.

> **Learning may observe, remember, research and propose. Production changes only through governed promotion.**

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
- fault/system-health attribution.

Counterfactual outcomes must remain labeled separately from actual P/L.

## StrategyMemory

Each production family may maintain version-aware performance memory across broad interpretable contexts such as:

- BUY versus SELL;
- trend/range/transition regime;
- volatility regime;
- session/context;
- relevant liquidity/location states.

Small samples must produce low confidence. The system should not treat `3 wins from 3 trades` as strong proof.

## Recency versus long-term evidence

Memory may combine recent, medium-term and longer-term version-specific evidence. Recent deterioration may reduce confidence without instantly deleting a historically valid strategy.

Exact windows/weighting remain open.

## Bounded adaptive influence

Validated StrategyMemory may eventually provide a bounded scoring/ranking adjustment. It should nudge—not dominate—the explicit market model.

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

## Entry learning

Entry learning should study, by strategy family where meaningful:

- ideal structural entry zone;
- approved entry versus actual fill;
- early/optimal/late/chased classification;
- MAE/MFE after entry;
- pullback/retest depth;
- breakout acceptance timing;
- chase/extension blocks;
- second-chance outcomes;
- missed-entry cost.

Recurring evidence may create an Entry Policy Challenger. It must not directly alter production timing thresholds.

## Exit learning

Exit learning should study:

- MFE versus realized R;
- Capture Efficiency;
- Premature Exit Cost;
- structural trail quality;
- runner capture;
- profit given back;
- regime/timeframe effects on M5/M15/H1 management.

A profitable trade can still reveal poor capture. A losing trade can still be a valid setup and normal statistical loss.

Recurring evidence may create an Exit/Trade-Management Challenger; production remains unchanged until promotion.

## Attribution before adaptation

Learning must distinguish whether a poor result belongs to:

- strategy/opportunity;
- entry timing;
- Trade Plan/stop geometry;
- execution/slippage;
- exit/trailing;
- system fault;
- normal statistical variance.

Do not reduce a strategy score because execution was faulty, or loosen exits because one valid trade lost normally.

## Learning authority levels

Conceptual levels:

```text
L0 Observation only
L1 Research recommendation
L2 Validated bounded scoring adjustment
L3 Shadow Challenger
L4 DEMO Canary
L5 Approved production policy
```

No candidate may jump levels outside governance.

## ML usage

ML may be researched for bounded tasks such as:

- opportunity ranking;
- regime classification;
- probability estimates;
- clustering/pattern discovery;
- feature importance.

V1 production authority should remain interpretable. A black-box model score alone must not become broker authority.

## AI supervisor boundaries

AI may help explain:

- why BUY/SELL/WAIT/BLOCK occurred;
- what failed;
- what patterns research found;
- candidate hypotheses.

AI must not directly call broker execution, alter risk limits, or self-promote policies.

## Hard prohibitions

Learning/AI must never automatically:

- martingale or increase risk after losses/wins;
- bypass daily loss/news/account/broker safety;
- redefine original R;
- treat unknown broker state as safe;
- generate and execute arbitrary Python strategy code;
- change production because of a tiny recent sample;
- self-promote a Challenger.

## Baseline degradation

Optional learning is an enhancement, not the only source of valid strategy semantics.

If learning state/model is unavailable but the frozen baseline remains independently valid, the system may enter a documented degraded mode:

```text
Learning: DEGRADED/OFFLINE
Adaptive influence: DISABLED
Baseline policy: ACTIVE
```

Critical risk/order/persistence corruption does not receive this fallback.

## Persistence and portability

StrategyMemory, entry/exit learning, candidates, genealogy, promotion history and rejected-hypothesis memory are durable machine-independent state. Laptop migration must preserve identities and evidence versions.

Under current project policy, these strategy/learning artifacts may be backed up in the public repository; only credentials/keys/tokens that enable unauthorized financial action or direct paid-service cost are excluded.

## Evidence isolation

Do not silently combine evidence from:

```text
REPLAY
SHADOW
DEMO_CANARY
MAIN_DEMO
```

or materially different strategy versions.

## Dashboard visibility

Compact example:

```text
Strategy Memory   READY
Entry Learning    ACTIVE
Exit Learning     ACTIVE
Champion          GSW-1.3
Challenger        EXIT-v1.4-C02
Stage             SHADOW
Adaptive Impact   BOUNDED / OFF
```

## Tests required

- small-sample confidence suppression;
- version/environment evidence isolation;
- bounded adaptive adjustment;
- entry/exit challenger creation without production mutation;
- wrong-subsystem attribution prevention;
- learning outage baseline-degradation behaviour;
- hard-safety/risk mutation attempts denied;
- persistence/migration of learning state.

## Explicit non-goals

Learning/AI must not:

- promise self-improving profitability;
- replace explicit hard safety;
- make every recent pattern a new rule;
- hide why a learned adjustment exists;
- require retraining from zero after laptop change.

## Open questions

- exact StrategyMemory windows/confidence model;
- maximum bounded adaptive influence;
- which ML tasks, if any, reach V1 production;
- exact minimum samples for entry/exit learning;
- exact model/version storage formats.