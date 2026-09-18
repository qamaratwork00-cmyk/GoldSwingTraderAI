# GoldSwingTraderAI — Research and Validation

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION  
**Version:** 0.5-implementation  
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
- manager-replay resolved Net R / average R / Profit Factor / drawdown, MFE/MAE, Capture Efficiency, profit-giveback and action counts where outcomes are unambiguous;
- confluence ablation using both initial-bracket outcomes and idealized Trade Manager outcomes;
- same-bar stop+target ambiguity preserved instead of favorably guessed;
- unresolved/open horizons preserved rather than coerced into wins/losses;
- actual trade/outcome versus counterfactual missed/blocked outcome separation;
- durable research episodes;
- StrategyMemory/bounded learning foundation;
- governed candidate discovery/invention/promotion state.

This remains a **software/research foundation**, not completed market validation. Broader historical XAU datasets, execution-friction stress, walk-forward/independent validation, untouched holdout and DEMO forward evidence remain required before claiming a strategy edge.

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
→ apply idealized accepted manager modification for following bar
→ advance time
```

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

## Trade Manager replay — implemented idealized model

`research/management_replay.py` reuses the production `evaluate_trade_manager()` and `apply_management_decision()` path.

For each READY historical Trade Plan:

```text
open research ManagedTrade at approved entry reference
→ for each later M5 bar:
   active current stop / current broker TP checked against bar high/low
   if neither closes trade:
       bar becomes completed
       rebuild chronological IntelligenceSnapshot
       run production Trade Manager
       record HOLD / PROTECT / TRAIL / RUNNER / EXIT
       idealize verified modify as effective from next bar
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

The current management replay is explicitly `BAR_CLOSE_IDEALIZED`. It assumes requested stop/TP modifications are accepted at the completed-bar boundary. It does **not** yet simulate:

- broker modify rejection/latency;
- fill slippage beyond the replay quote model;
- tick-level ordering inside an M5 candle;
- historical PRE_CLOSE schedule input inside this management replay;
- live reconciliation failures.

Therefore `resolved_net_r` from management replay is research evidence under this declared model, not actual broker P/L.

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
Trade Manager replay     BAR_CLOSE_IDEALIZED + active bar-high/low barriers
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

Decision-level ablation measures:

- Opportunity event frequency;
- ENTER / WAIT / MISSED / INVALID counts;
- BUY/SELL leading frequency;
- average Opportunity Score;
- average Conflict Score;
- signed deltas versus BASE;
- POC marginal effect through `ALL - DIRECTIONAL_COMBINED`.

A positive-only family bonus does **not** guarantee a higher final fused Opportunity Score: confluence can strengthen both BUY and SELL hypotheses and therefore increase conflict. Research measures the resulting signed effect rather than assuming every bonus helps.

Initial-bracket ablation may additionally compare:

- READY plan count;
- resolved coverage;
- resolved initial-bracket Net/Avg R, Profit Factor and drawdown;
- MFE / MAE;
- 2R / 3R / 4R reach rates.

Management ablation may additionally compare:

- managed-trade count;
- resolved management coverage;
- resolved management Net/Avg R, Profit Factor and drawdown;
- MFE / MAE;
- Capture Efficiency;
- profit giveback;
- HOLD / PROTECT / TRAIL / RUNNER / EXIT action mix.

These metrics remain tied to the declared replay realism. They are not broker-certified P/L.

Other ablations may later include:

- remove FVG support;
- remove RSI support;
- remove liquidity evidence;
- reduce duplicated/correlated features.

Ultimately evaluate not only headline win rate but also Net R under the declared model, Profit Factor, drawdown, Opportunity Recall, missed meaningful moves, large-move capture, trade frequency, Capture Efficiency and uncertainty/coverage.

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

This prevents strategy logic from being blamed for risk/execution/system failures.

The exact objective meaningful-move labeling method remains research calibration.

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

Exit research now has deterministic idealized production-manager replay support for:

- realized modeled R;
- MFE;
- Capture Efficiency;
- profit giveback;
- structural protection/trailing action mix;
- runner activation/target behavior;
- manager EXIT reason.

A winning trade may still be a poor exit if capture is consistently weak; a losing trade may still be a valid high-quality setup and normal statistical loss.

PRE_CLOSE historical replay, modify latency/failure and tick-level ordering remain additional realism work before full broker-parity claims.

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
- modify failure/latency;
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
- replay/outcome realism version;
- random seed where relevant.

The evidence package should state selection/validation/holdout periods, metrics, stress/ablation results, limitations and decision.

## Evidence claims

Use precise language such as:

- `positive on specified historical replay`;
- `resolved initial-bracket evidence under BAR_HIGH_LOW model`;
- `resolved management evidence under BAR_CLOSE_IDEALIZED model`;
- `passed independent validation`;
- `passed final holdout`;
- `positive DEMO forward evidence`.

Do not claim `proven profitable` from historical results alone, and do not describe idealized bar replay as broker-realized P/L.

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
- manager actions applied only after the bar that generated them, for following-bar barrier checks;
- management replay unresolved/ambiguous isolation from resolved Net R;
- confluence management-ablation delta accounting;
- actual/counterfactual isolation;
- outcome attribution and Opportunity Recall metrics;
- durable research episode feed;
- discovery liveness and independent-episode handling;
- one-shot holdout/promotion governance.

Still required for full research validation:

- broad historical XAU datasets across regimes;
- execution-friction/modify-failure/PRE_CLOSE stress scenarios;
- walk-forward/independent validation;
- final untouched holdout on locked candidates;
- Shadow/DEMO forward evidence;
- controlled broker comparison to quantify replay-versus-DEMO differences.

## Explicit non-goals

Research must not:

- directly send orders;
- silently mutate production;
- reuse final holdout as selection data while calling it untouched;
- treat counterfactual or unresolved modeled results as real P/L;
- resolve same-bar stop/target ambiguity in the favorable direction without adequate intrabar data;
- call idealized manager modifications broker-verified fills;
- overstate historical evidence;
- promote a popular indicator/confluence tool without measured value.

## Open questions

- exact data periods/sample requirements;
- exact Opportunity Recall labeling method;
- historical PRE_CLOSE/session integration into management replay;
- execution modification failure/latency model;
- walk-forward window design;
- Monte Carlo/bootstrap method;
- minimum robustness/stress thresholds;
- exact promotion evidence thresholds;
- final evidence threshold for keeping/removing each optional confluence feature.
