# GoldSwingTraderAI — Research and Validation

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Chronological replay, no-lookahead validation, holdouts, robustness/stress evidence, opportunity/entry/exit research metrics and evidence claims.  
**Depends on:** `../00-foundation/SYSTEM_CONTRACT.md`, `../10-market-intelligence/CANDLE_STRUCTURE.md`, `../20-trading-decisions/ENTRY_TIMING.md`, `../20-trading-decisions/TRADE_MANAGER_AND_EXIT.md`

## Purpose

Research must test the real documented trading semantics without future leakage, cherry-picking or exaggerated claims.

> **A positive backtest is evidence about a specified historical simulation, not proof of future profitability.**

## Replay principle

Where parity is claimed, historical replay should reuse the same core market-intelligence, strategy, timing, planning and management semantics as live operation, with different data/execution adapters only where necessary.

The system should avoid maintaining a simplified `backtest strategy` whose rules differ materially from production.

## Chronology and no-lookahead

Every event becomes available only when its required information existed historically. Examples:

- confirmed swing at `confirmed_at`, not pivot time;
- BOS/MSS only after required completed-candle evidence;
- FVG/OB/sweep only after their defining evidence exists;
- session high/low only as developed up to that time;
- news/macro facts only according to historical information availability.

Future candles may be used later to label outcomes for research, but never to improve the original decision.

## Event-driven replay

Preferred replay is chronological/event-driven:

```text
new completed candle/event
→ update validated snapshot
→ run production semantics
→ persist decision/outcome state
→ advance time
```

If forming-candle/intrabar features are later authorized, replay must use suitable lower-resolution/tick data or explicitly declare that parity is not available for that feature.

## Execution realism

Research should state the realism level used. Depending on available data, simulation may model:

- Bid/Ask/spread;
- price drift;
- slippage assumptions;
- tick/point normalization;
- min lot/volume step;
- SL/TP geometry;
- margin/risk constraints.

Bar-level simulation must not be described as tick-perfect execution.

## Evidence chronology

Candidate research should conceptually separate:

```text
DEVELOPMENT / SELECTION DATA
→ INDEPENDENT VALIDATION
→ LOCK ONE CANDIDATE
→ FINAL UNTOUCHED HOLDOUT
→ STRESS / WALK-FORWARD
→ SHADOW
→ DEMO CANARY
```

Exact sample sizes remain open.

## Final holdout rule

The final holdout is one-shot for the locked candidate. If that candidate fails, the system must not repeatedly try alternate parameters/candidates on the same data while still calling it untouched.

Consumed holdout identity/status should be persisted.

## Walk-forward and stability

Research should test multiple chronological periods/regimes rather than depend on one historical split. Parameter regions that remain useful across nearby values are preferred over fragile single-number optima.

## Ablation testing

Research should test whether evidence primitives genuinely add value. Examples:

- remove FVG support;
- remove RSI support;
- remove liquidity evidence;
- reduce duplicated/correlated features.

A primitive that does not improve relevant outcomes should not be retained merely because it is popular terminology.

## Core performance metrics

At minimum research should be able to report:

- trades;
- Net R;
- Average R;
- Profit Factor;
- drawdown/loss streak;
- MFE and MAE;
- hold time;
- Capture Efficiency;
- 2R/3R/4R+ reach rates;
- normalized 100/200/300+ pip-move reach/capture where meaningful;
- Opportunity Recall;
- missed-opportunity rate;
- Entry Efficiency / late-entry cost;
- Premature Exit Cost;
- runner capture.

Win rate is not sufficient by itself.

## Opportunity Recall and missed-move attribution

Research should evaluate not only trades taken but meaningful market episodes missed.

Missed outcomes should distinguish causes such as:

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

The definition of an objectively meaningful missed opportunity must be chronological and non-hindsight in decision reconstruction; exact labeling methodology remains open.

## Counterfactuals

Blocked/missed opportunities may be evaluated after the fact for hypothetical MFE/MAE, but these records must be explicitly labeled `COUNTERFACTUAL` and never added to actual broker P/L.

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

Research may propose family-specific entry-policy challengers but may not mutate production directly.

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

Monte Carlo or bootstrap analysis may be used for drawdown/loss-streak distributions, but methods must account for potential trade/regime dependence. Exact methodology remains open.

## Complexity discipline

More complex candidates require stronger evidence. Comparable performance should prefer the simpler, more stable policy.

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

Possible lifecycle states:

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

## Tests required

- deterministic replay chronology;
- no-lookahead swing/event tests;
- replay/live decision parity where claimed;
- holdout consumption enforcement;
- counterfactual P/L isolation;
- attribution correctness;
- research reproducibility;
- stress/ablation report integrity.

## Explicit non-goals

Research must not:

- directly send orders;
- silently mutate production;
- reuse final holdout as selection data while calling it untouched;
- treat counterfactual results as real P/L;
- overstate historical evidence.

## Open questions

- exact data periods/sample requirements;
- exact Opportunity Recall labeling method;
- walk-forward window design;
- Monte Carlo/bootstrap method;
- minimum robustness/stress thresholds;
- exact promotion evidence thresholds.