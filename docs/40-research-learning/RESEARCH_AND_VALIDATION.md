# GoldSwingTraderAI — Research and Validation

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION  
**Version:** 0.3-implementation  
**Authority:** Chronological replay, no-lookahead validation, holdouts, robustness/stress evidence, opportunity/entry/exit research metrics and evidence claims.  
**Depends on:** `../00-foundation/SYSTEM_CONTRACT.md`, `../10-market-intelligence/CANDLE_STRUCTURE.md`, `../20-trading-decisions/ENTRY_TIMING.md`, `../20-trading-decisions/TRADE_MANAGER_AND_EXIT.md`

## Purpose

Research must test the real documented trading semantics without future leakage, cherry-picking or exaggerated claims.

> **A positive backtest is evidence about a specified historical simulation, not proof of future profitability.**

## Current implementation checkpoint — Phase 10 foundation

Implemented owners include:

```text
research/replay.py
research/metrics.py
research/learning.py
research/episode_journal.py
research/discovery.py
research/invention.py
research/promotion.py
```

The current replay foundation is chronological completed-bar / `BAR_CLOSE` realism. It reuses production Intelligence + Decision semantics rather than maintaining a separate simplified backtest strategy.

Current deterministic research infrastructure already supports:

- prefix-only/no-lookahead replay of production analytical semantics;
- actual trade/outcome versus counterfactual missed/blocked outcome separation;
- Net R / average R / drawdown-style research metrics where supplied;
- MFE/MAE, Capture Efficiency and Opportunity Recall attribution;
- durable research episodes;
- StrategyMemory/bounded learning foundation;
- governed candidate discovery/invention/promotion state.

This is a **software/research foundation**, not completed market validation. Broader historical datasets, realistic execution assumptions, ablation/stress/walk-forward, independent validation/holdout and DEMO forward evidence remain required before claiming a strategy edge.

## Replay principle

Where parity is claimed, historical replay should reuse the same core market-intelligence, strategy, timing, planning and management semantics as live operation, with different data/execution adapters only where necessary.

The system must not maintain a simplified `backtest strategy` whose rules differ materially from production.

## Chronology and no-lookahead

Every event becomes available only when required information existed historically. Examples:

- confirmed swing at `confirmed_at`, not pivot time;
- BOS/MSS only after required completed-candle evidence;
- FVG/OB/sweep only after defining evidence exists;
- trendline only from swings already confirmed at that replay point;
- Fibonacci anchor pair only from already-confirmed structural swings;
- Volume Profile/POC only from volume/candle history available up to that replay point;
- session high/low only as developed up to that time;
- news/macro facts only according to historical information availability.

Future candles may be used later to label outcomes for research, but never to improve the original decision.

## Event-driven replay

```text
new completed candle/event
→ update validated snapshot
→ run production semantics
→ persist decision/outcome state
→ advance time
```

If forming-candle/intrabar features are later authorized, replay must use suitable lower-resolution/tick data or explicitly declare that parity is unavailable for that feature.

## Execution realism

Research states its realism level. Depending on available data, simulation may model:

- Bid/Ask/spread;
- price drift;
- slippage assumptions;
- tick/point normalization;
- min lot/volume step;
- SL/TP geometry;
- margin/risk constraints.

Bar-level simulation must not be described as tick-perfect execution.

## Evidence chronology

```text
DEVELOPMENT / SELECTION DATA
→ INDEPENDENT VALIDATION
→ LOCK ONE CANDIDATE
→ FINAL UNTOUCHED HOLDOUT
→ STRESS / WALK-FORWARD
→ SHADOW
→ DEMO CANARY
```

Exact sample sizes remain research-calibratable.

## Final holdout rule

The final holdout is one-shot for the locked candidate. If that candidate fails, the system must not repeatedly try alternate parameters/candidates on the same data while still calling it untouched.

Consumed holdout identity/status is durable under the promotion registry.

## Walk-forward and stability

Research should test multiple chronological periods/regimes rather than depend on one historical split. Parameter regions that remain useful across nearby values are preferred over fragile single-number optima.

## Ablation testing

Research should prove whether optional evidence actually adds value.

Examples:

- remove FVG support;
- remove RSI support;
- remove liquidity evidence;
- remove Trendline bonus;
- remove Fibonacci bonus;
- remove POC/volume-profile bonus;
- remove all three technical-confluence bonuses together;
- reduce duplicated/correlated features.

For Trendline/Fibonacci/POC specifically, compare at least:

```text
base strategy only
vs
base + individual confluence
vs
base + bounded combined confluence
```

Evaluate not only headline win rate but also:

- Net R;
- Profit Factor;
- drawdown;
- average R;
- Opportunity Recall;
- missed meaningful moves;
- large-move capture;
- trade frequency;
- Capture Efficiency.

A feature that slightly raises accuracy by eliminating a large share of good opportunities is not automatically an improvement. Optional confluence exists to improve quality, not to recreate filter soup.

A primitive that does not improve relevant outcomes should not be retained merely because it is popular terminology.

## Core performance metrics

At minimum research should report:

- trades;
- Net R;
- Average R;
- Profit Factor;
- drawdown/loss streak;
- MFE and MAE;
- hold time;
- Capture Efficiency;
- 2R/3R/4R+ reach rates;
- normalized 100/200/300+ move reach/capture where meaningful;
- Opportunity Recall;
- missed-opportunity rate;
- Entry Efficiency / late-entry cost;
- Premature Exit Cost;
- runner capture;
- trade-frequency change versus baseline when a new filter/confluence rule is tested.

Win rate is not sufficient by itself.

## Opportunity Recall and missed-move attribution

Research evaluates not only trades taken but meaningful market episodes missed.

Missed outcomes distinguish causes such as:

```text
NO_OPPORTUNITY
ENTRY_WAIT
ENTRY_MISSED
SAFETY_BLOCKED
RISK_BLOCKED
EXECUTION_BLOCKED
SYSTEM_FAULT
```

This prevents strategy logic from being blamed for risk/execution/system failures.

The definition of an objectively meaningful missed opportunity must be chronological and non-hindsight in decision reconstruction; exact labeling methodology remains research calibration.

## Counterfactuals

Blocked/missed opportunities may be evaluated after the fact for hypothetical MFE/MAE, but these records remain explicitly counterfactual and never become actual broker P/L.

Hard safety rules are not automatically weakened because some blocked trades would have won.

## Entry research

Entry analysis should compare, where available:

- ideal structural zone;
- planned/approved entry;
- actual fill;
- MAE/MFE after entry;
- early/optimal/late/chased classification;
- lost RR from delay/drift/slippage;
- missed-entry outcomes.

Research may propose family-specific Entry Policy Challengers but cannot mutate production directly.

## Exit research

Exit research should compare:

- realized R;
- MFE;
- Capture Efficiency;
- Premature Exit Cost;
- profit given back;
- trail quality;
- runner objective quality;
- structural state after exit.

A winning trade may still be a poor exit if capture is consistently weak; a losing trade may still be a valid high-quality setup and normal statistical loss.

## Attribution

Poor outcomes should be attributed among at least:

- opportunity/strategy quality;
- optional confluence contribution;
- entry timing;
- Trade Plan/stop quality;
- execution/slippage;
- trade management/exit;
- news/market shock;
- system fault;
- normal statistical loss.

Learning should not modify the wrong subsystem.

## Robustness/stress

Candidate stress may include:

- worse spread/slippage;
- execution delay;
- slightly worse entries;
- parameter perturbation;
- missing optional evidence;
- multiple regimes/directions/sessions;
- different starting dates.

The goal is to identify fragile edges that disappear under small realistic friction.

## Monte Carlo / path risk

Monte Carlo or bootstrap analysis may be used for drawdown/loss-streak distributions, but methods must account for possible trade/regime dependence. Exact methodology remains open.

## Complexity discipline

More complex candidates require stronger evidence. Comparable performance should prefer the simpler, more stable policy.

This applies especially to multi-confluence recipes: Trendline + Fibonacci + POC must not become a mandatory checklist merely because all are available in the codebase.

## Versioning and reproducibility

Every serious research result should identify, as applicable:

- code version;
- strategy/policy version;
- configuration version;
- data version/period;
- replay engine version;
- random seed where relevant.

The evidence package should state selection/validation/holdout periods, metrics, stress/ablation results, limitations and decision.

## Evidence claims

Use precise language such as:

- `positive on specified historical replay`;
- `passed independent validation`;
- `passed final holdout`;
- `positive DEMO forward evidence`.

Do not claim `proven profitable` from historical results alone.

## Research states

```text
DRAFT
RESEARCHING
VALIDATING
LOCKED_CANDIDATE
HOLDOUT_PASSED
HOLDOUT_FAILED
STRESS_PASSED
SHADOW
DEMO_CANARY
PROMOTED
REJECTED
```

Promotion authority is owned by `GOVERNED_EXPERIMENTS_AND_PROMOTION.md`.

## Tests / current evidence

Deterministic coverage includes:

- chronological/prefix-only replay;
- no-lookahead structure/confluence semantics through production Intelligence;
- actual/counterfactual isolation;
- outcome attribution and Opportunity Recall metrics;
- durable research episode feed;
- discovery liveness and independent-episode handling;
- one-shot holdout/promotion governance.

Still required for full research validation:

- broad historical XAU datasets across regimes;
- execution-friction/stress scenarios;
- walk-forward/independent validation;
- confluence ablation report;
- final untouched holdout on locked candidates;
- Shadow/DEMO forward evidence.

## Explicit non-goals

Research must not:

- directly send orders;
- silently mutate production;
- reuse final holdout as selection data while calling it untouched;
- treat counterfactual results as real P/L;
- overstate historical evidence;
- promote a popular indicator/confluence tool without measured value.

## Open questions

- exact data periods/sample requirements;
- exact Opportunity Recall labeling method;
- walk-forward window design;
- Monte Carlo/bootstrap method;
- minimum robustness/stress thresholds;
- exact promotion evidence thresholds;
- final evidence threshold for keeping/removing each optional confluence feature.
