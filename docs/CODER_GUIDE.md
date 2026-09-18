# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT — IMPLEMENTATION MAP CURRENT  
**Version:** 1.9-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from authoritative topic docs. Code implements it. This guide tells you where implementation lives and what has actually been verified.**

Use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for sequencing/recovery and `60-engineering/CODING_STANDARD.md` for frozen engineering rules.

## Current checkpoint — 2026-09-18

Deterministic core implementation exists through the current **Phase-10 research foundation including chronological replay, Trade Manager outcomes, execution stress, fixed-policy walk-forward validation, and content-addressed evidence manifests**. The normal `goldswing` launcher remains read-only MT5 readiness; final persistent orchestration/live DEMO certification are not complete.

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

One verified market snapshot feeds shared derived facts. `intelligence/confluence.py` owns causal confirmed-swing Trendlines, Fibonacci geometry and broker-local Volume Profile/POC.

### Phase 4 — Strategies / Fusion / Opportunity / Timing — implemented / deterministic CI

```text
strategies/floor.py
strategies/confluence.py
decisions/fusion.py
decisions/opportunity.py
decisions/timing.py
decisions/snapshot.py
```

Six families evaluate in parallel. Optional Trendline/Fib/POC confluence is bounded positive-only and production defaults all implemented sources ON.

### Phase 5 — Trade Plan + Risk — implemented / deterministic CI

```text
decisions/trade_plan.py
risk/engine.py
risk/state.py
```

Structural geometry precedes monetary sizing. SMALL is any positive UTC day-start equity below `$300`; no `$100` floor. Score never increases monetary risk.

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

Success-like ACK is not final exposure truth. Ambiguous acknowledgement is never blind-retried. Production shared cross-laptop coordination remains pending.

### Phase 8 — Trade Manager — implemented deterministic baseline / CI

```text
management/models.py
management/manager.py
management/store.py
management/execution.py
```

HOLD / PROTECT / TRAIL / RUNNER / EXIT. Primary is a checkpoint; runner needs fresh continuation + next objective; PRE_CLOSE overrides. Durable local trade state changes only after broker verification.

### Phase 9 — Dashboard — implemented deterministic renderer / CI

```text
operator/dashboard.py
operator/__init__.py
```

Pure-stdlib read-only presentation. Final runtime DTO builder/refresh and some research/discovery visibility remain integration work.

### Phase 10 — Replay / Research / Learning / Discovery — implemented deterministic foundation + evidence tooling / CI

```text
research/replay.py
research/ablation.py
research/outcomes.py
research/management_replay.py
research/stress.py
research/validation.py
research/evidence.py
research/metrics.py
research/learning.py
research/episode_journal.py
research/discovery.py
research/invention.py
research/promotion.py
```

Research flow:

```text
chronological completed-candle replay
→ production Intelligence + Decision semantics
→ controlled confluence ablation
→ historical production Trade Plan reconstruction
→ ambiguity-safe bracket outcomes
→ chronological production Trade Manager replay
→ declared execution-friction stress
→ fixed-policy walk-forward validation
→ content-addressed dataset/evidence identity
→ metrics / learning / durable episodes
→ discovery / invention
→ governed promotion lifecycle
```

`research/ablation.py` compares BASE / TRENDLINE / FIBONACCI / DIRECTIONAL_COMBINED / ALL under identical event chronology.

`research/outcomes.py` provides historical Trade Plan reconstruction plus explicit `TARGET_FIRST / STOP_FIRST / BOTH_TOUCHED_AMBIGUOUS / HORIZON_UNRESOLVED` semantics.

`research/management_replay.py` reuses production Trade Manager logic. Active stop/TP is checked before each completed-bar management decision. Optional assumptions model adverse fill, executable-side spread, M5 modify delay and deterministic modify rejection without rewriting structural geometry/original R.

`research/stress.py` holds the analytical run fixed and compares declared execution friction against BASE. Default probes remain 1.50x spread, 0.10R adverse entry, one-M5 modify delay, every-second modify rejection and combined stress. They are calibration baselines only.

`research/validation.py` owns `FIXED_POLICY_WALK_FORWARD`:

```text
DEVELOPMENT CONTEXT
→ later non-overlapping VALIDATION SLICE
```

Development history reconstructs state but is not scored; validation data is clipped at the validation boundary; no optimizer/tuning exists; the final one-shot holdout is not consumed.

`research/evidence.py` owns reproducibility identity/manifest logic:

- `identify_replay_dataset()` creates canonical SHA-256 identity from source label/version, replay realism/spread, symbol geometry, economic account context and every candle field;
- every timeframe gets bar count, first/last time and content hash;
- timeframe tuple order is normalized;
- broker endpoint `login/server` are excluded from the economic replay hash;
- `build_research_evidence_manifest()` records code revision, policy version, dataset identity, normalized config/results, limitations and hashes;
- `input_fingerprint_sha256` identifies experiment inputs independently of result values/generation time;
- `manifest_sha256` identifies the complete evidence record;
- canonical JSON is stable across mapping insertion order;
- financial-secret-shaped manifest fields raise `FINANCIAL_SECRET_DETECTED`.

The evidence module has no trading or promotion authority. It is intended to let future real-XAU replay/walk-forward evidence be audited and reproduced instead of relying on mutable filenames/screenshots.

Other Phase-10 guarantees:

- no lookahead and honest realism labels;
- actual broker P/L vs counterfactual modeled evidence stays separate;
- unresolved/ambiguous/open outcomes stay outside resolved P/L;
- StrategyMemory is bounded/context-version isolated;
- discovery uses approved declarative primitives only;
- eligible discovery evidence creates a candidate or explicit suppression reason;
- locked fingerprint + one-shot final holdout enforced;
- candidates cannot self-promote or gain broker authority.

## Deterministic test ownership

Major later suites include:

```text
tests/test_execution_safety.py
tests/test_trade_manager.py
tests/test_management_execution.py
tests/test_management_replay.py
tests/test_dashboard.py
tests/test_research_ablation.py
tests/test_research_outcomes.py
tests/test_research_stress.py
tests/test_research_validation.py
tests/test_research_evidence.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Latest verified evidence-manifest checkpoint: **168 tests PASS**, Ruff PASS and financial-secret scan PASS. Deterministic CI is software evidence, not profitability proof or controlled DEMO certification.

## Feature ownership index

| Feature | Authority | Current owner |
|---|---|---|
| Market data/history | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | `market_data/` |
| Candle/structure | `10-market-intelligence/CANDLE_STRUCTURE.md` | `intelligence/candle_structure.py` |
| Technical/confluence | `10-market-intelligence/*` | `intelligence/technical.py`, `intelligence/confluence.py`, `strategies/confluence.py` |
| Strategy/fusion/timing | `20-trading-decisions/*` | `strategies/`, `decisions/` |
| Trade Plan | `20-trading-decisions/TRADE_PLAN.md` | `decisions/trade_plan.py` |
| Risk/session/news | `30-risk-execution/*` | `risk/` |
| Persistence | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | `persistence/` + typed repositories |
| Execution | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | `execution/` |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | `management/` |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | `operator/dashboard.py` |
| Replay/validation/stress/evidence | `40-research-learning/RESEARCH_AND_VALIDATION.md` | `research/replay.py`, `ablation.py`, `outcomes.py`, `management_replay.py`, `stress.py`, `validation.py`, `evidence.py`, `metrics.py` |
| StrategyMemory | `40-research-learning/LEARNING_AND_AI_BOUNDARIES.md` | `research/learning.py` |
| Discovery/invention | `40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md`, `AUTONOMOUS_STRATEGY_INVENTION.md` | `episode_journal.py`, `discovery.py`, `invention.py` |
| Promotion | `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md` | `research/promotion.py` |

## Coding invariants

- Python 3.11+; standard library first for production runtime;
- no lookahead;
- one authoritative owner per responsibility;
- raw broker writes only in execution boundary;
- ambiguous broker/replay outcomes never guessed favorably;
- stress assumptions explicit and separate from production safety thresholds;
- adverse research fill never rewrites structural geometry/original R;
- walk-forward development context is never counted as validation;
- later-window data cannot resolve earlier validation outcomes;
- validation cannot consume the final governed holdout;
- serious evidence uses dataset/content identity rather than mutable filename alone;
- evidence manifests reject authority-bearing secret-shaped fields;
- dashboard/research/discovery have zero raw broker authority;
- financial-authority credentials never enter tracked/public project state.

## Current integration gaps / next engineering work

Do **not** redesign implemented core unnecessarily. Main remaining work:

1. add real historical XAU dataset ingestion/export around the new content-addressed identity contract;
2. package persisted evidence manifests/results for repeatable walk-forward studies;
3. run broad regime-diverse real-data walk-forward/independent validation and calibrate stress;
4. add historical PRE_CLOSE/session-policy integration where trustworthy schedule data exists;
5. integrate research/discovery state into dashboard runtime DTO;
6. Phase 11 portable backup/checkpoint + fresh-machine recovery + shared cross-laptop controller proof;
7. Phase 12 final persistent runtime orchestrator and controlled Windows/MT5 DEMO certification;
8. final docs/release audit based on actual evidence.

The current `app/main.py` remains a read-only readiness launcher until final runtime orchestration.

## Debugging order

```text
MarketSnapshot
→ IntelligenceSnapshot
→ Strategy / Decision / Opportunity / Timing
→ TradePlan
→ Risk + Session/News
→ Execution / Reconciliation
→ ManagedTrade / Trade Manager
→ Dashboard
→ Replay / Ablation / Outcomes / Management / Stress / Walk-Forward
→ Dataset/Evidence Identity
→ Metrics / Episode Journal
→ Discovery / Invention / Promotion
```
