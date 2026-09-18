# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT — IMPLEMENTATION MAP CURRENT  
**Version:** 1.8-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from authoritative topic docs. Code implements it. This guide tells you where implementation lives and what has actually been verified.**

Use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for sequencing/recovery and `60-engineering/CODING_STANDARD.md` for frozen engineering rules.

## Current checkpoint — 2026-09-18

Deterministic core implementation exists through the current **Phase-10 research foundation plus chronological decision/Trade Plan/Trade Manager, execution-stress and fixed-policy walk-forward evidence tooling**. The normal `goldswing` launcher remains read-only MT5 readiness; final persistent orchestration/live DEMO certification are not complete.

### Phase 1 — Foundation — implemented / deterministic CI

```text
config/settings.py
domain/enums.py
domain/ids.py
domain/models.py
diagnostics/reasons.py
diagnostics/logging.py
app/main.py
scripts/scan_financial_secrets.py
.github/workflows/ci.yml
```

### Phase 2 — MT5 read layer — implemented / deterministic CI; live Windows evidence pending

```text
domain/market.py
market_data/mt5_reader.py
market_data/snapshot.py
```

Completed H4/H1/M15/M5 candles only; forming bars excluded. Positive DEMO verification exists in read path.

### Phase 3 — Market intelligence — implemented / deterministic CI

```text
intelligence/indicators.py
intelligence/candle_structure.py
intelligence/technical.py
intelligence/liquidity.py
intelligence/session.py
intelligence/news.py
intelligence/confluence.py
intelligence/snapshot.py
```

One verified market snapshot feeds shared derived facts; duplicate indicator/ATR work is avoided. `intelligence/confluence.py` owns causal confirmed-swing Trendlines, Fibonacci geometry and broker-local Volume Profile/POC. Real volume is preferred when available; tick-volume fallback is explicit.

### Phase 4 — Strategies / Fusion / Opportunity / Timing — implemented / deterministic CI

```text
strategies/floor.py
strategies/confluence.py
decisions/fusion.py
decisions/opportunity.py
decisions/timing.py
decisions/snapshot.py
```

Six families evaluate in parallel. One strong family can lead. Missing optional evidence is omitted/reweighted instead of zeroed. Poor timing normally yields WAIT rather than destroying a valid opportunity.

`strategies/confluence.py` is **positive-only**: Trendline/Fib/POC can add a small capped uplift to a compatible existing family; they cannot lower base family score or become mandatory gates. `ConfluenceBonusConfig` defaults all implemented sources ON and exists so research can disable individual sources for controlled ablation without changing production semantics.

### Phase 5 — Trade Plan + Risk — implemented / deterministic CI

```text
decisions/trade_plan.py
risk/engine.py
risk/state.py
```

Structural geometry precedes monetary sizing. SMALL is any positive UTC day-start equity below `$300`; no `$100` floor. Minimum lot is evaluated by actual all-in risk. Score never increases monetary risk. Exact broker margin is authoritative when available.

### Phase 6 — Session/News Permission + Persistence — implemented / deterministic CI

```text
risk/permissions.py
persistence/store.py
persistence/runtime_state.py
```

PRE_CLOSE/reopen/news safety are hard authorities. Local persistence is standard-library SQLite + canonical JSON/checksum/schema/event records + typed adapters.

### Phase 7 — Execution + Reconciliation — implemented deterministic baseline / CI

```text
execution/models.py
execution/intent_store.py
execution/gate.py
execution/checks.py
execution/controller.py
execution/mt5_writer.py
execution/service.py
execution/reconcile.py
```

```text
hard authorities
→ centralized gate
→ durable ExecutionIntent
→ broker pre-check
→ fresh lease/fencing verification
→ persist SUBMITTING
→ exactly one order_send
→ broker acknowledgement
→ broker reconciliation
```

Success-like ACK is not final exposure truth. An Intent ID cannot send twice for its lifetime. Ambiguous acknowledgement is never blind-retried. In-memory coordination is deterministic-test-only; production shared cross-laptop coordination remains pending.

### Phase 8 — Trade Manager — implemented deterministic baseline / CI

```text
management/models.py
management/manager.py
management/store.py
management/execution.py
```

HOLD / PROTECT / TRAIL / RUNNER / EXIT. Ordinary pullbacks do not force exit; small profit alone does not force breakeven; Primary is a checkpoint; runner needs fresh continuation + next objective; PRE_CLOSE overrides. Durable local trade state changes only after broker verification.

### Phase 9 — Dashboard — implemented deterministic renderer / CI

```text
operator/dashboard.py
operator/__init__.py
```

Pure-stdlib read-only presentation. Final runtime DTO builder, Discovery Health fields, compact Trendline/Fib/POC display and in-place live refresh remain integration/polish work.

### Phase 10 — Replay / Research / Learning / Discovery — implemented deterministic foundation + evidence tooling / CI

```text
research/replay.py
research/ablation.py
research/outcomes.py
research/management_replay.py
research/stress.py
research/validation.py
research/metrics.py
research/learning.py
research/episode_journal.py
research/discovery.py
research/invention.py
research/promotion.py
```

Research flow now includes:

```text
chronological completed-candle replay
→ production Intelligence + Decision semantics
→ controlled confluence ablation
→ production Trade Plan reconstruction for historical ENTER events
→ ambiguity-safe initial stop/target path labeling
→ chronological production Trade Manager replay
→ declared execution-friction stress scenarios
→ fixed-policy chronological walk-forward validation
→ managed-trade / validation evidence metrics
→ research episodes / learning
→ approved-primitive discovery / invention
→ governed promotion lifecycle
```

`research/ablation.py` runs identical event chronology under:

```text
BASE
TRENDLINE
FIBONACCI
DIRECTIONAL_COMBINED  # Trendline + Fibonacci
ALL                   # Trendline + Fibonacci + POC
```

Decision-level ablation reports Opportunity/ENTER/WAIT/MISSED/frequency/score/conflict deltas and does not invent P/L.

`research/outcomes.py` owns historical production Trade Plan reconstruction and initial bracket evidence under explicit `BAR_HIGH_LOW` semantics:

```text
TARGET_FIRST
STOP_FIRST
BOTH_TOUCHED_AMBIGUOUS
HORIZON_UNRESOLVED
```

Same-bar stop+target is never resolved favorably without intrabar evidence. Ambiguous/unresolved cases do not enter resolved bracket Net R.

`research/management_replay.py` reuses production `evaluate_trade_manager()` and `apply_management_decision()`. Each M5 first tests the **currently active** stop/TP; surviving completed bars then feed fresh intelligence to HOLD/PROTECT/TRAIL/RUNNER/EXIT for the following bar.

The default manager replay remains `BAR_CLOSE_IDEALIZED`. Optional `ManagementReplayAssumptions` support research-only adverse entry slippage, executable-side spread approximation, completed-M5 modify delay and deterministic every-Nth modify rejection. Structural stop/targets and immutable original R are not rewritten to hide adverse fills.

`research/stress.py` owns scenario orchestration around a **fixed analytical ReplayRun**. Default transparent V1 probes are:

```text
BASE
WIDER_SPREAD        1.50x dataset spread
ADVERSE_ENTRY       0.10R adverse fill
MODIFY_DELAY        1 completed M5
MODIFY_REJECTION    every 2nd submitted modify rejected
COMBINED            all four assumptions together
```

These are calibration baselines only, not production thresholds or historical broker claims.

`research/validation.py` owns `FIXED_POLICY_WALK_FORWARD` validation. Its rules are intentionally strict:

```text
DEVELOPMENT CONTEXT
→ later non-overlapping VALIDATION SLICE
```

- development history may reconstruct production Opportunity state but is not scored as validation;
- validation slices cannot overlap;
- the production policy/config remains fixed; there is no optimizer or automatic parameter search;
- outcome/management data is truncated at each validation-end boundary, so later-window candles cannot resolve an earlier validation trade;
- validation trades near the boundary may honestly remain `HORIZON_OPEN`;
- optional declared execution stress may be attached to the validation slice;
- this path never consumes the one-shot final holdout owned by `research/promotion.py`.

Exact development/validation window sizes remain evidence-calibratable. The current code supplies the chronology/scaffold, not a claim that the synthetic test windows prove edge.

Other Phase-10 guarantees:

- replay is prefix-only and labelled honestly by realism level;
- actual broker P/L and counterfactual missed/blocked outcomes remain separate;
- same-bar active stop+TP ambiguity is never favorably guessed;
- unresolved/open modeled trades remain outside resolved Net R;
- StrategyMemory influence is bounded/context-version isolated;
- independent episode IDs prevent fake sample inflation;
- candidate recipes use audited declarative primitives only;
- rejected/duplicate memory survives restart;
- eligible discovery evidence must create a candidate or explicit governed suppression reason;
- candidate stages cannot be skipped;
- locked fingerprint + one-shot holdout enforced;
- candidates cannot self-promote or gain raw broker authority.

Approved discovery primitives explicitly include:

```text
TRENDLINE
FIBONACCI
VOLUME_PROFILE_POC
```

## Deterministic test ownership

Major suites include:

```text
tests/test_market_data.py
tests/test_intelligence_core.py
tests/test_intelligence_snapshot.py
tests/test_technical_liquidity.py
tests/test_technical_confluence.py
tests/test_strategy_decisions.py
tests/test_trade_plan_risk.py
tests/test_risk_state_regressions.py
tests/test_margin_authority.py
tests/test_session_news_permissions.py
tests/test_persistence_recovery.py
tests/test_execution_safety.py
tests/test_trade_manager.py
tests/test_management_execution.py
tests/test_management_replay.py
tests/test_dashboard.py
tests/test_research_ablation.py
tests/test_research_outcomes.py
tests/test_research_stress.py
tests/test_research_validation.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Latest verified walk-forward checkpoint: **163 tests PASS**, Ruff PASS and financial-secret scan PASS. Deterministic CI is software evidence, not profitability proof or controlled DEMO certification.

## Feature ownership index

| Feature | Authority | Current owner |
|---|---|---|
| Market data/history | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | `market_data/` |
| Candle/structure | `10-market-intelligence/CANDLE_STRUCTURE.md` | `intelligence/candle_structure.py` |
| Technical zones/location | `10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md` | `intelligence/technical.py` |
| Trendline/Fibonacci/POC | `10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md` | `intelligence/confluence.py`, `strategies/confluence.py` |
| Liquidity/SMC | `10-market-intelligence/LIQUIDITY_AND_SMC.md` | `intelligence/liquidity.py` |
| Indicators/volatility | `10-market-intelligence/INDICATORS_AND_VOLATILITY.md` | `intelligence/indicators.py` |
| Strategy floor | `20-trading-decisions/STRATEGY_FLOOR.md` | `strategies/` |
| Fusion/Opportunity/Timing | `20-trading-decisions/*` | `decisions/` |
| Trade Plan | `20-trading-decisions/TRADE_PLAN.md` | `decisions/trade_plan.py` |
| Risk | `30-risk-execution/RISK_CONTRACT.md` | `risk/engine.py`, `risk/state.py` |
| Session/news permission | `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` | `risk/permissions.py` |
| Persistence | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | `persistence/` + typed subsystem repositories |
| Execution | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | `execution/` |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | `management/` |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | `operator/dashboard.py` |
| Replay/validation/stress | `40-research-learning/RESEARCH_AND_VALIDATION.md` | `research/replay.py`, `ablation.py`, `outcomes.py`, `management_replay.py`, `stress.py`, `validation.py`, `metrics.py` |
| StrategyMemory | `40-research-learning/LEARNING_AND_AI_BOUNDARIES.md` | `research/learning.py` |
| Discovery/invention | `40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md`, `AUTONOMOUS_STRATEGY_INVENTION.md` | `episode_journal.py`, `discovery.py`, `invention.py` |
| Promotion | `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md` | `research/promotion.py` |

## Coding invariants

- Python 3.11+; standard library first for production runtime;
- no lookahead;
- shared verified facts instead of duplicate reads/calculations;
- soft evidence must not become arbitrary hard-filter soup;
- raw broker writes live only in `execution/mt5_writer.py`;
- critical local state never pretends ambiguous broker action succeeded;
- research outcome/replay layers must not favorably resolve unknown intrabar order;
- stress assumptions must be explicit, reproducible and separate from frozen production safety thresholds;
- adverse research fill does not rewrite structural stop/target or immutable original R;
- walk-forward development context cannot be counted as validation evidence;
- later-window data cannot resolve an earlier validation slice;
- walk-forward code cannot consume the final governed holdout;
- dashboard/research/discovery have zero raw broker authority;
- discovery must not be silently inert when eligible evidence exists;
- financial-authority credentials never enter tracked project state.

## Current integration gaps / next engineering work

Do **not** redesign the already-implemented core unnecessarily. Main remaining work is integration/evidence:

1. add dataset identity/versioning and reproducible evidence manifests so broader XAU studies can be audited and reproduced;
2. run sufficiently broad real historical XAU walk-forward/independent validation and calibrate stress assumptions from evidence;
3. add historical PRE_CLOSE/session-policy integration where trustworthy schedule data exists;
4. integrate authoritative research/discovery/confluence state into dashboard DTO/runtime status;
5. Phase 11: portable backup/checkpoint + fresh-machine recovery drill + production shared cross-laptop coordination proof;
6. Phase 12: final persistent runtime orchestrator composing Market → Intelligence → Strategy/Decision → TradePlan → Risk/Permissions → Execution → Management → Journal/Research;
7. controlled Windows/MT5 DEMO integration/fault/restart/failover certification;
8. final docs/release audit sync based on actual evidence.

The current `app/main.py` remains a read-only readiness launcher until the final runtime orchestrator replaces/extends it.

## Debugging order

```text
MarketSnapshot
→ IntelligenceSnapshot + optional Trendline/Fib/POC
→ StrategyFloor + bounded confluence
→ Decision / Opportunity / Timing
→ TradePlan
→ Risk + Session/News
→ Execution / Reconciliation
→ ManagedTrade / Trade Manager
→ Dashboard
→ Replay / Ablation / Outcomes / Management Replay / Stress / Walk-Forward / Metrics
→ Episode Journal
→ Discovery / Invention / Promotion
```
