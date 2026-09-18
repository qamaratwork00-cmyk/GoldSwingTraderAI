# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT — IMPLEMENTATION MAP CURRENT  
**Version:** 1.7-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from authoritative topic docs. Code implements it. This guide tells you where implementation lives and what has actually been verified.**

Use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for sequencing/recovery and `60-engineering/CODING_STANDARD.md` for frozen engineering rules.

## Current checkpoint — 2026-09-18

Deterministic core implementation exists through the current **Phase-10 research foundation plus chronological decision/Trade Plan/Trade Manager evidence and execution-stress tooling**. The normal `goldswing` launcher remains read-only MT5 readiness; final persistent orchestration/live DEMO certification are not complete.

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

One verified market snapshot feeds shared derived facts; duplicate indicator/ATR work is avoided.

`intelligence/confluence.py` owns causal confirmed-swing Trendlines, Fibonacci geometry and broker-local Volume Profile/POC. Real volume is preferred when available; tick-volume fallback is explicit.

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
→ managed-trade capture/giveback/action/modify metrics
→ research metrics / durable episodes
→ approved-primitive mapping
→ recurring cluster detection
→ candidate OR explicit suppression reason
→ durable CandidateRegistry
→ governed validation/promotion lifecycle
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

`research/outcomes.py` owns historical production Trade Plan reconstruction and initial bracket evidence. It inspects later M5 bars under explicit `BAR_HIGH_LOW` semantics:

```text
TARGET_FIRST
STOP_FIRST
BOTH_TOUCHED_AMBIGUOUS
HORIZON_UNRESOLVED
```

Same-bar stop+target is never resolved favorably without intrabar evidence. Ambiguous/unresolved cases do not enter resolved bracket Net R. The summary exposes coverage, resolved initial-bracket Net/Avg R, Profit Factor, drawdown, MFE/MAE and 2R/3R/4R reach rates.

`research/management_replay.py` reuses the real production `evaluate_trade_manager()` and `apply_management_decision()` path. For each later M5 bar it first tests the **currently active** stop and broker TP. If the trade survives that bar, the completed bar builds fresh intelligence and the production manager emits HOLD/PROTECT/TRAIL/RUNNER/EXIT for the following bar.

Current manager-replay outcomes:

```text
PLAN_NOT_READY
STOP_FILLED
TARGET_FILLED
MANAGER_EXIT
BOTH_TOUCHED_AMBIGUOUS
HORIZON_OPEN
```

The default manager replay remains `BAR_CLOSE_IDEALIZED`. Optional `ManagementReplayAssumptions` now support research-only:

```text
adverse entry slippage in immutable original-R units
executable-side Bid/Ask barrier spread approximation
completed-M5 modify delay
 deterministic every-Nth manager-modify rejection
```

An unresolved synthetic modify blocks later modify submissions until it resolves, matching the production reconciliation principle. Structural stop/targets are never moved merely to hide adverse fill slippage. Same-bar active stop+TP ambiguity remains unresolved.

`research/stress.py` owns scenario orchestration. The analytical `ReplayRun` is held fixed while Trade Plan / fill / exit-side spread / manager-write assumptions change. Default transparent V1 research probes are:

```text
BASE
WIDER_SPREAD        1.50x dataset spread
ADVERSE_ENTRY       0.10R adverse fill
MODIFY_DELAY        1 completed M5
MODIFY_REJECTION    every 2nd submitted modify rejected
COMBINED            all four assumptions together
```

Those values are **calibration baselines only**. They are not frozen broker assumptions, production risk thresholds or profitability claims. The stress report exposes signed deltas versus BASE for managed-plan count, plan rejection, resolved coverage, Net/Avg R, drawdown, Capture Efficiency and giveback, plus modify request/applied/rejected/pending counts from manager replay.

Other Phase-10 guarantees:

- replay is prefix-only and labelled honestly by realism level;
- actual broker P/L and counterfactual missed/blocked outcomes remain separate;
- same-bar active stop+TP ambiguity is never favorably guessed;
- unresolved/open modeled trades remain outside resolved Net R;
- StrategyMemory influence is bounded/context-version isolated;
- independent episode IDs prevent fake sample inflation;
- candidate recipes use audited declarative primitives only;
- durable candidates may be VARIANT / NEW_FAMILY / ENTRY_POLICY / EXIT_POLICY;
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

`episode_journal.py` maps corresponding durable evidence labels into these primitives so confluence genuinely participates in discovery/research rather than being only a production-score decoration.

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
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Latest verified stress-research checkpoint contained **159 passing tests** plus Ruff and financial-secret scan PASS. Deterministic CI is software evidence, not profitability proof or controlled DEMO certification.

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
| Replay/validation/stress | `40-research-learning/RESEARCH_AND_VALIDATION.md` | `research/replay.py`, `ablation.py`, `outcomes.py`, `management_replay.py`, `stress.py`, `metrics.py` |
| StrategyMemory | `40-research-learning/LEARNING_AND_AI_BOUNDARIES.md` | `research/learning.py` |
| Discovery/invention | `40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md`, `AUTONOMOUS_STRATEGY_INVENTION.md` | `episode_journal.py`, `discovery.py`, `invention.py` |
| Promotion | `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md` | `research/promotion.py` |

## Coding invariants

- Python 3.11+; standard library first for production runtime;
- no lookahead;
- shared verified facts instead of duplicate reads/calculations;
- soft evidence must not become arbitrary hard-filter soup;
- Trendline/Fibonacci/POC are optional bonus-only confluence unless governed evidence explicitly changes that design;
- any positive balance below `$300` is SMALL; no arbitrary `$100` gate;
- raw broker writes live only in `execution/mt5_writer.py`;
- critical local state never pretends ambiguous broker action succeeded;
- research outcome/replay layers must not favorably resolve unknown intrabar order;
- stress assumptions must be explicit, reproducible and separate from frozen production safety thresholds;
- adverse research fill does not rewrite structural stop/target or immutable original R;
- pending manager modify stress cannot silently permit overlapping broker writes;
- dashboard/research/discovery have zero raw broker authority;
- discovery must not be silently inert when eligible evidence exists;
- no unnecessary frameworks/factories/service-manager layers;
- financial-authority credentials never enter tracked project state.

## Current integration gaps / next engineering work

Do **not** redesign the already-implemented core unnecessarily. Main remaining work is integration/evidence:

1. calibrate execution-stress assumptions on broader historical/controlled DEMO evidence and add more realism only where evidence justifies it;
2. add historical PRE_CLOSE/session-policy integration to management replay where verified schedules/data permit it;
3. run broader real historical XAU datasets, walk-forward and independent validation rather than synthetic regression fixtures;
4. integrate authoritative research/discovery/confluence state into dashboard DTO/runtime status;
5. Phase 11: portable backup/checkpoint + fresh-machine recovery drill + production shared cross-laptop coordination proof;
6. Phase 12: build final persistent runtime orchestrator composing Market → Intelligence → Strategy/Decision → TradePlan → Risk/Permissions → Execution → Management → Journal/Research;
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
→ Replay / Ablation / Initial Outcomes / Management Replay / Stress / Metrics
→ Episode Journal
→ Discovery / Invention / Promotion
```