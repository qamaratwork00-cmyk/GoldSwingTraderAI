# GoldSwingTraderAI — Research and Validation

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION  
**Version:** 0.6-implementation  
**Authority:** Chronological replay, no-lookahead validation, holdouts, robustness/stress evidence, opportunity/entry/exit research metrics and evidence claims.  
**Depends on:** `../00-foundation/SYSTEM_CONTRACT.md`, `../10-market-intelligence/CANDLE_STRUCTURE.md`, `../20-trading-decisions/ENTRY_TIMING.md`, `../20-trading-decisions/TRADE_MANAGER_AND_EXIT.md`

## Purpose

Research must test the real documented trading semantics without future leakage, cherry-picking or exaggerated claims.

> **A positive backtest is evidence about a specified historical simulation, not proof of future profitability.**

## Current implementation checkpoint — Phase 10

Implemented owners include:

```text
research/replay.py
research/ablation.py
research/outcomes.py
research/management_replay.py
research/stress.py
research/metrics.py
research/learning.py
research/episode_journal.py
research/discovery.py
research/invention.py
research/promotion.py
```

The current replay foundation is chronological completed-bar research. It reuses production Intelligence, Decision, Trade Plan and Trade Manager semantics rather than maintaining a separate simplified backtest strategy.

Current deterministic research infrastructure supports:

- prefix-only/no-lookahead replay of production analytical semantics;
- controlled same-chronology confluence ablation across BASE, Trendline, Fibonacci, Trendline+Fibonacci and ALL sources;
- decision-level Opportunity/ENTER/WAIT/MISSED/conflict/frequency deltas without inventing P/L;
- post-hoc production Trade Plan reconstruction for historical ENTER decisions;
- explicit `BAR_HIGH_LOW` initial stop/initial broker-target path labeling;
- chronological production Trade Manager replay at completed M5 boundaries;
- active trailing stop / active broker TP checking before each new management decision;
- HOLD / PROTECT / TRAIL / RUNNER / EXIT action histories from the production manager;
- resolved management Net R / average R / Profit Factor / drawdown, MFE/MAE, Capture Efficiency, profit-giveback and action counts where outcomes are unambiguous;
- confluence ablation using both initial-bracket outcomes and Trade Manager outcomes;
- deterministic declared execution-friction stress around fixed analytical decisions;
- adverse entry-slippage, executable-side spread, manager-modify delay/rejection probes;
- manager-modify request/applied/rejected/suppressed/pending audit counts;
- same-bar stop+target ambiguity preserved instead of favorably guessed;
- unresolved/open horizons preserved rather than coerced into wins/losses;
- actual trade/outcome versus counterfactual missed/blocked outcome separation;
- durable research episodes;
- StrategyMemory/bounded learning foundation;
- governed candidate discovery/invention/promotion state.

This remains a **software/research foundation**, not completed market validation. Broader historical XAU datasets, empirical stress calibration, walk-forward/independent validation, untouched holdout and DEMO forward evidence remain required before claiming a strategy edge.

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
→ run production analytical semantics
→ build production Trade Plan when ENTER is reached
→ if modeled trade survives active stop/TP during next M5
   run production Trade Manager on that completed bar
→ apply only the execution model's verified-style manager state transition
→ advance time
```

The default manager execution model is idealized. A stress run may instead declare spread, adverse fill, modify delay and deterministic modify rejection assumptions.

If forming-candle/intrabar features are later authorized, replay must use suitable lower-resolution/tick data or explicitly declare that parity is unavailable for that feature.

## Outcome-labeling boundary

A historical decision and its later outcome are separate stages:

```text
historical information available at T
→ production analytical decision at T
→ production Trade Plan reconstructed at T
→ freeze decision/plan facts
→ inspect only candles after T for outcome/management research
```

The outcome label may know what happened later; the original decision may not.

Initial bracket semantics:

```text
target touched before stop → TARGET_FIRST
stop touched before target → STOP_FIRST
both touched in same M5    → BOTH_TOUCHED_AMBIGUOUS
neither within horizon     → HORIZON_UNRESOLVED
```

Ambiguous/unresolved cases do not enter resolved bracket Net R. Research reports coverage so incomplete certainty cannot be hidden.

## Trade Manager replay — implemented

`research/management_replay.py` reuses production `evaluate_trade_manager()` and `apply_management_decision()`.

Default flow for each READY historical Trade Plan:

```text
open research ManagedTrade at approved entry reference
→ for each later M5 bar:
   active current stop / current broker TP checked
   if neither closes trade:
       bar becomes completed
       rebuild chronological IntelligenceSnapshot
       run production Trade Manager
       record HOLD / PROTECT / TRAIL / RUNNER / EXIT
       apply idealized verified modify for following bar
```

Management outcomes are:

```text
PLAN_NOT_READY
STOP_FILLED
TARGET_FILLED
MANAGER_EXIT
BOTH_TOUCHED_AMBIGUOUS
HORIZON_OPEN
```

A trailing stop can therefore realize positive R, and a runner TP can become the active broker objective when the production manager earns it.

The default is explicitly `BAR_CLOSE_IDEALIZED`. It assumes requested manager stop/TP modifications become verified at the completed-bar boundary. It remains suitable as a clean baseline, not broker-certified P/L.

## Declared execution-stress model — implemented foundation

`ManagementReplayAssumptions` can add research-only friction without changing production strategy or Trade Manager logic:

```text
adverse_entry_slippage_r
barrier_spread_price
modify_delay_bars
reject_every_nth_modify
```

Rules:

- adverse entry slippage is measured against the production plan's immutable `original_r_price`;
- adverse fill does **not** move the structural stop or target;
- adverse fill does **not** redefine original R to make the outcome look better;
- positive barrier spread treats candle OHLC as a mid-price proxy, with BUY exits evaluated on Bid and SELL exits on Ask;
- a manager PROTECT/TRAIL/RUNNER request may be delayed by completed M5 bars;
- while one synthetic modify is unresolved, later manager modify submissions are suppressed until it resolves;
- every-Nth modify rejection is deterministic/reproducible, not random hidden noise;
- rejected modify leaves the current broker-state stop/TP unchanged;
- manager EXIT is still modeled at the completed-bar decision price; separate close-order failure/slippage requires additional evidence if later needed;
- same-bar active stop+TP remains ambiguous.

`research/stress.py` holds the analytical `ReplayRun` fixed and compares execution/Trade Plan sensitivity against a clean BASE. It therefore answers: **would the same analytical opportunities remain economically robust under declared friction?** It does not silently reselect strategies to fit each stress case.

Default transparent V1 probes are:

```text
BASE                no added friction
WIDER_SPREAD        1.50x dataset spread
ADVERSE_ENTRY       0.10R adverse fill
MODIFY_DELAY        1 completed M5
MODIFY_REJECTION    every 2nd submitted modify rejected
COMBINED            all four together
```

These numbers are **research calibration baselines only**. They are not frozen broker assumptions, not changes to production spread/drift safety rules and not claims about actual Exness distributions.

Stress reports include signed deltas versus BASE for:

- managed trade / non-ready Trade Plan counts;
- resolved coverage;
- resolved Net R / Average R;
- resolved max drawdown;
- Capture Efficiency;
- profit giveback;
- manager modify request/applied/rejected/suppressed/pending counts.

The current stress layer does **not** claim full Execution Permission Gate, margin, order-book, variable intrabar spread, close-order failure, PRE_CLOSE historical schedule or tick-ordering parity.

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

Current layers are:

```text
Decision replay          BAR_CLOSE
Initial bracket outcomes BAR_HIGH_LOW
Trade Manager replay     BAR_CLOSE_IDEALIZED + active barriers
Execution stress         BAR_CLOSE_EXECUTION_STRESS + declared assumptions
```

None is a claim of tick-perfect broker execution.

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

The implemented confluence ablation compares identical historical event chronology under:

```text
BASE                   no Trendline/Fibonacci/POC bonus
TRENDLINE              Trendline bonus only
FIBONACCI              Fibonacci bonus only
DIRECTIONAL_COMBINED   Trendline + Fibonacci
ALL                    Trendline + Fibonacci + POC
```

Production defaults keep all implemented confluence sources enabled; research toggles are experiment controls, not live safety switches.

Decision-level ablation measures Opportunity/ENTER/WAIT/MISSED/INVALID frequency, BUY/SELL leadership, Opportunity/Conflict scores, signed deltas versus BASE and POC marginal effect through `ALL - DIRECTIONAL_COMBINED`.

A positive-only family bonus does **not** guarantee a higher final fused Opportunity Score: confluence can strengthen both BUY and SELL hypotheses and therefore increase conflict. Research measures the resulting signed effect rather than assuming every bonus helps.

Initial-bracket ablation may additionally compare READY plans, resolved coverage, bracket Net/Avg R, Profit Factor, drawdown, MFE/MAE and 2R/3R/4R reach.

Management ablation may compare managed-trade count, resolved management Net/Avg R, Profit Factor, drawdown, MFE/MAE, Capture Efficiency, giveback and HOLD/PROTECT/TRAIL/RUNNER/EXIT action mix.

Execution stress is a different axis from confluence ablation: confluence changes optional analytical evidence, while stress holds analytical decisions fixed and changes declared execution friction. Do not mix the two concepts in reporting.

Other ablations may later include FVG/RSI/liquidity evidence removal or correlated-feature reduction.

A feature that slightly raises accuracy by eliminating a large share of good opportunities is not automatically an improvement. Optional confluence exists to improve quality, not to recreate filter soup.

## Core performance metrics

At minimum research should report, when the required outcome realism exists:

- modeled/resolved trades;
- Net R;
- Average R;
- Profit Factor;
- drawdown/loss streak;
- MFE and MAE;
- hold time;
- Capture Efficiency;
- profit giveback;
- HOLD/PROTECT/TRAIL/RUNNER/EXIT distribution where management is replayed;
- manager modify request/applied/rejected/pending evidence under stress;
- 2R/3R/4R+ reach rates;
- normalized 100/200/300+ move reach/capture where meaningful;
- Opportunity Recall;
- missed-opportunity rate;
- Entry Efficiency / late-entry cost;
- Premature Exit Cost;
- runner capture;
- trade-frequency change versus baseline;
- ambiguity/unresolved/open coverage.

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

This prevents strategy logic from being blamed for risk/execution/system failures. The exact objective meaningful-move labeling method remains research calibration.

## Counterfactuals

Blocked/missed opportunities may be evaluated after the fact for hypothetical MFE/MAE, but these records remain explicitly counterfactual and never become actual broker P/L.

Hard safety rules are not automatically weakened because some blocked trades would have won.

## Entry research

Entry analysis should compare, where available:

- ideal structural zone;
- planned/approved entry;
- actual or modeled stressed fill;
- MAE/MFE after entry;
- early/optimal/late/chased classification;
- lost RR from delay/drift/slippage;
- missed-entry outcomes.

Research may propose family-specific Entry Policy Challengers but cannot mutate production directly.

## Exit research

Exit research has deterministic production-manager replay support for:

- realized modeled R;
- MFE;
- Capture Efficiency;
- profit giveback;
- structural protection/trailing action mix;
- runner activation/target behavior;
- manager EXIT reason;
- declared stop/TP-modify delay/rejection sensitivity.

A winning trade may still be a poor exit if capture is consistently weak; a losing trade may still be a valid high-quality setup and normal statistical loss.

Historical PRE_CLOSE integration, variable intrabar spread, tick ordering and real broker modification/fill distributions remain additional realism work before broker-parity claims.

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

The deterministic execution-stress foundation is implemented. It currently tests wider spread, adverse fill, manager-modify delay/rejection and a combined case while preserving the same analytical decisions.

Future/calibration stress may additionally include:

- empirically sampled spread/slippage by broker/session/volatility;
- execution/close delays where reliable data exists;
- parameter perturbation;
- missing optional evidence;
- multiple regimes/directions/sessions;
- different starting dates;
- PRE_CLOSE/session-specific behavior once trustworthy historical schedule data is available.

The goal is to identify fragile edges that disappear under small realistic friction. A stress scenario is evidence only if its assumptions are visible and reproducible.

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
- replay/outcome/stress realism version;
- explicit stress scenario values;
- random seed where relevant.

The evidence package should state selection/validation/holdout periods, metrics, stress/ablation results, limitations and decision.

## Evidence claims

Use precise language such as:

- `positive on specified historical replay`;
- `resolved initial-bracket evidence under BAR_HIGH_LOW model`;
- `resolved management evidence under BAR_CLOSE_IDEALIZED model`;
- `execution-stress result under declared scenario assumptions`;
- `passed independent validation`;
- `passed final holdout`;
- `positive DEMO forward evidence`.

Do not claim `proven profitable` from historical results alone, and do not describe idealized/stressed bar replay as broker-realized P/L.

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
- controlled confluence toggles defaulting ON in production;
- same-chronology BASE/Trendline/Fibonacci/combined/ALL decision ablation;
- signed final-score/frequency delta reporting rather than assumed confluence benefit;
- Trade Plan path TARGET_FIRST / STOP_FIRST symmetry;
- same-bar stop+target ambiguity preserved rather than favorably guessed;
- unresolved outcome horizon isolation;
- resolved bracket metrics exclude ambiguous/unresolved cases;
- active trailing-stop R realization;
- production Trade Manager composition over chronological completed bars;
- manager actions applied only after the bar that generated them;
- management replay unresolved/ambiguous isolation from resolved Net R;
- confluence management-ablation delta accounting;
- executable-side spread barrier semantics;
- adverse-fill original-R immutability;
- explicit stress-scenario validation and fixed analytical-run reuse;
- modification audit counters under stress assumptions;
- actual/counterfactual isolation;
- outcome attribution and Opportunity Recall metrics;
- durable research episode feed;
- discovery liveness and independent-episode handling;
- one-shot holdout/promotion governance.

Current deterministic CI after the execution-stress foundation: **159 tests PASS**, Ruff PASS and financial-secret scan PASS.

Still required for full research validation:

- broad historical XAU datasets across regimes;
- empirical calibration of stress assumptions against broker/DEMO evidence;
- historical PRE_CLOSE/session integration;
- walk-forward/independent validation;
- final untouched holdout on locked candidates;
- Shadow/DEMO forward evidence;
- controlled replay-versus-DEMO comparison.

## Explicit non-goals

Research must not:

- directly send orders;
- silently mutate production;
- reuse final holdout as selection data while calling it untouched;
- treat counterfactual or unresolved modeled results as real P/L;
- resolve same-bar stop/target ambiguity in the favorable direction without adequate intrabar data;
- call idealized or stressed manager modifications broker-verified fills;
- hide stress assumptions;
- rewrite structural stop/target or original R to make adverse-fill outcomes look better;
- overstate historical evidence;
- promote a popular indicator/confluence tool without measured value.

## Open questions

- exact data periods/sample requirements;
- exact Opportunity Recall labeling method;
- historical PRE_CLOSE/session integration into management replay;
- empirical spread/slippage/modify-failure distributions by broker/session/volatility;
- variable-spread/tick-order modeling where data supports it;
- walk-forward window design;
- Monte Carlo/bootstrap method;
- minimum robustness/stress thresholds;
- exact promotion evidence thresholds;
- final evidence threshold for keeping/removing each optional confluence feature.
