# GoldSwingTraderAI — Learning and AI Boundaries

**Status:** PROVISIONAL
**Version:** 0.1-learning
**Authority:** StrategyMemory, bounded adaptation, AI limits and evidence separation

## Purpose

Learning may remember verified experience and recommend bounded changes. It
cannot become an unstable self-mutating broker authority.

## One-way influence

~~~mermaid
flowchart TB
    OUTCOMES["Actual, counterfactual and fault-labelled outcomes"] --> MEMORY["Versioned StrategyMemory"]
    MEMORY --> INFLUENCE["Bounded ranking/timing influence"]
    INFLUENCE --> CHALLENGER["Durable challenger/candidate"]
    CHALLENGER --> PROMOTION["Validation → holdout → stress → shadow → canary"]
    PROMOTION --> APPROVAL["Explicit governed approval"]
    APPROVAL --> POLICY["Versioned runtime policy"]
    SAFETY["Hard risk/news/account/controller safety"] -.-> POLICY
~~~

Hard safety never becomes a learned-away feature.

## Evidence separation

Keep separate:

- actual broker outcomes;
- counterfactual missed/waited outcomes;
- blocked/rejected outcomes;
- system faults and execution friction;
- policy/version/dataset identity.

Otherwise learning may punish a strategy for a broker fault or treat an
unexecuted move as real P/L.

## StrategyMemory

Memory may summarize BUY/SELL, regime, volatility, session, location,
liquidity, confluence and family context. Small samples have low confidence;
three wins from three trades are not proof.

Recent, medium and long-term evidence can be combined, but windows and weights
must be versioned. A validated bounded influence may nudge a score; it may not
create a hard block or multiply monetary risk.

## Entry and exit learning

Entry learning measures approved-versus-fill quality, early/optimal/late
classification, MAE/MFE, pullback/retest depth, chase blocks, second chances
and confluence contribution.

Exit learning measures MFE versus realized R, Capture Efficiency, premature-exit
cost, structural trail quality, runner capture and target progression.

These observations may create Entry Policy or Exit Policy challengers. They do
not edit production thresholds directly.

## AI boundaries

AI may explain BUY/SELL/WAIT/BLOCK, summarize evidence and propose hypotheses.
It may not call a broker, change risk limits, treat unknown as safe, generate
and execute arbitrary Python or self-promote a challenger.

ML may be researched for ranking, regime classification, clustering or feature
importance. V1 production authority remains interpretable and bounded.

## Baseline degradation

If optional learning is unavailable but deterministic baseline remains valid:

~~~text
Learning DEGRADED/OFFLINE
→ adaptive influence DISABLED
→ baseline policy ACTIVE
~~~

The same principle applies to optional Trendline/Fibonacci/POC. Critical
financial/order/persistence uncertainty does not receive this fallback.

## Source and tests

research/metrics.py, learning.py, outcomes.py and episode_journal.py own
metrics, memory and labelled records. Tests are test_research_outcomes.py,
test_research_evidence.py, test_discovery_journal.py and promotion suites.

## Dashboard and research

Show StrategyMemory state, adaptive influence BOUNDED/OFF, Entry/Exit Learning,
Champion/Challenger and discovery health. Research evidence must identify the
policy and dataset version that produced each learning result.

## Explicit non-goals

No promise of self-improving profit, hard-safety replacement, tiny-sample rule
change, hidden learned block, arbitrary code generation or self-promotion.

