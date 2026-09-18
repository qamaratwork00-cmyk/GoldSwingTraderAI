# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT — IMPLEMENTATION MAP CURRENT  
**Version:** 2.1-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from authoritative topic docs. Code implements it. This guide tells you where implementation lives and what has actually been verified.**

Use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for sequencing/recovery and `60-engineering/CODING_STANDARD.md` for frozen engineering rules.

## Current checkpoint — 2026-09-18

Deterministic core implementation exists through the current **Phase-10 research foundation including chronological replay, Trade Manager outcomes, execution stress, fixed-policy walk-forward validation, content-addressed evidence, portable replay datasets and read-only MT5 historical acquisition**. The normal `goldswing` launcher remains read-only MT5 readiness; final persistent orchestration/live DEMO certification are not complete.

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

Completed H4/H1/M15/M5 candles only; forming bars excluded. Positive DEMO verification exists in live-write readiness; ordinary reads remain read-only.

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

One verified market snapshot feeds shared derived facts. Trendline/Fibonacci/POC are causal, optional and bounded positive-only.

### Phase 4 — Strategies / Fusion / Opportunity / Timing — implemented / deterministic CI

```text
strategies/floor.py
strategies/confluence.py
decisions/fusion.py
decisions/opportunity.py
decisions/timing.py
decisions/snapshot.py
```

Six families evaluate in parallel; optional confluence cannot become hidden filter soup.

### Phase 5 — Trade Plan + Risk — implemented / deterministic CI

```text
decisions/trade_plan.py
risk/engine.py
risk/state.py
```

Structural geometry precedes sizing. SMALL is any positive UTC day-start equity below `$300`; no `$100` floor. Score never increases monetary risk.

### Phase 6 — Session/News Permission + Persistence — implemented / deterministic CI

```text
risk/permissions.py
persistence/store.py
persistence/runtime_state.py
```

Hard session/news safety plus standard-library SQLite durable state.

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

Durable one-shot ExecutionIntent, central gate, fresh fencing check, exactly one `order_send`, and reconciliation. Production cross-laptop atomic coordination remains pending.

### Phase 8 — Trade Manager — implemented deterministic baseline / CI

```text
management/models.py
management/manager.py
management/store.py
management/execution.py
```

HOLD / PROTECT / TRAIL / RUNNER / EXIT. PRE_CLOSE overrides and local state changes only after broker verification.

### Phase 9 — Dashboard — implemented deterministic renderer / CI

```text
operator/dashboard.py
operator/__init__.py
```

Pure-stdlib read-only presentation. Final runtime DTO/live refresh/research visibility remain integration work.

### Phase 10 — Replay / Research / Learning / Discovery — implemented deterministic foundation + evidence tooling / CI

```text
research/replay.py
research/ablation.py
research/outcomes.py
research/management_replay.py
research/stress.py
research/validation.py
research/evidence.py
research/datasets.py
research/acquisition.py
research/metrics.py
research/learning.py
research/episode_journal.py
research/discovery.py
research/invention.py
research/promotion.py
```

Research flow:

```text
read-only historical source / portable dataset
→ content identity
→ chronological production replay
→ ablation / Trade Plan outcomes / Trade Manager replay
→ declared execution stress
→ fixed-policy walk-forward
→ evidence manifest
→ metrics / learning / discovery / governed promotion
```

`research/replay.py` is prefix-only BAR_CLOSE production Decision replay.

`research/ablation.py` compares BASE / TRENDLINE / FIBONACCI / DIRECTIONAL_COMBINED / ALL under identical chronology.

`research/outcomes.py` reconstructs historical production Trade Plans and preserves target/stop same-bar ambiguity.

`research/management_replay.py` reuses production Trade Manager logic; active stop/TP is checked before each completed-bar management decision.

`research/stress.py` holds analytical decisions fixed and tests declared spread/adverse-fill/modify-delay/modify-rejection assumptions without rewriting original R.

`research/validation.py` owns fixed-policy chronological walk-forward with non-overlapping validation slices, no hidden optimizer and no final-holdout authority.

`research/evidence.py` owns canonical dataset/evidence SHA-256 identity and secret-shaped-field rejection.

`research/datasets.py` owns portable offline bundles:

```text
dataset_manifest.json
H4.csv / H1.csv / M15.csv / M5.csv
[optional M1.csv etc.]
```

Bundles are write-new, hash-verified, content-reverified on import and exclude broker endpoint login/server.

`research/acquisition.py` reuses the **existing** `MT5Reader`; do not build a second MT5 adapter. It owns research-only historical acquisition:

```text
HistoricalAcquisitionRequest
→ resolve Gold symbol/aliases through MT5Reader
→ AccountFacts + SymbolSpec
→ exact completed-candle count per requested timeframe
→ reject partial history
→ historical spread provenance
→ ReplayDataset
→ optional acquire_and_export_mt5_bundle()
```

Acquisition rules:

- request must include H4/H1/M15/M5 positive counts; optional M1 may be requested;
- completed candles only; existing reader already excludes forming bar position 0;
- actual returned count must equal requested count;
- default replay spread = median positive M5 historical `spread_points × point`;
- if historical spread points are unavailable, require explicit non-negative override;
- never silently substitute zero or current live spread;
- source label/version are explicit research provenance;
- read-only acquisition has no broker-write authority and no duplicate MT5 client.

Software adapter is deterministic-tested; actual Windows/MT5 broker-history acquisition remains controlled integration evidence, not yet VERIFIED.

### Discovery/invention guarantees

- approved declarative primitives only;
- independent episode IDs prevent fake sample inflation;
- eligible evidence → candidate or explicit suppression reason;
- rejected/duplicate memory persists;
- locked fingerprint + one-shot holdout;
- no self-promotion and no broker authority.

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
tests/test_research_datasets.py
tests/test_research_acquisition.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Latest verified historical-acquisition checkpoint: **178 tests PASS**, Ruff PASS and financial-secret scan PASS. Deterministic CI is software evidence, not profitability proof or controlled Windows/MT5 evidence.

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
| Replay/research/evidence/data acquisition | `40-research-learning/RESEARCH_AND_VALIDATION.md` | `research/replay.py`, `ablation.py`, `outcomes.py`, `management_replay.py`, `stress.py`, `validation.py`, `evidence.py`, `datasets.py`, `acquisition.py`, `metrics.py` |
| StrategyMemory | `40-research-learning/LEARNING_AND_AI_BOUNDARIES.md` | `research/learning.py` |
| Discovery/invention | `40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md`, `AUTONOMOUS_STRATEGY_INVENTION.md` | `episode_journal.py`, `discovery.py`, `invention.py` |
| Promotion | `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md` | `research/promotion.py` |

## Coding invariants

- Python 3.11+; standard library first for production runtime;
- no lookahead;
- one authoritative owner per responsibility;
- no duplicate MT5 research client: reuse `MT5Reader`;
- raw broker writes only in execution boundary;
- ambiguous broker/replay outcomes never guessed favorably;
- partial historical samples never silently shrink declared evidence;
- missing historical spread is explicit UNKNOWN/override-required, never hidden zero/live substitution;
- serious evidence uses dataset/content identity rather than mutable filename alone;
- portable research bundles verify manifest/file/content identity before use;
- financial-authority credentials never enter tracked/public project state.

## Current integration gaps / next engineering work

Do **not** redesign implemented core unnecessarily. Main remaining work:

1. run controlled Windows/MT5 acquisition against real XAU history and freeze source/version convention only from observed evidence;
2. package evidence manifests/results beside immutable dataset identities for repeatable studies;
3. run broad regime-diverse real-data walk-forward/independent validation and calibrate stress;
4. add historical PRE_CLOSE/session-policy integration where trustworthy schedule data exists;
5. integrate research/discovery state into dashboard runtime DTO;
6. Phase 11 portable runtime-state backup/checkpoint + fresh-machine recovery + shared cross-laptop controller proof;
7. Phase 12 final persistent runtime orchestrator and controlled Windows/MT5 DEMO certification;
8. final docs/release audit based on actual evidence.

The current `app/main.py` remains a read-only readiness launcher until final runtime orchestration.

## Debugging order

```text
MarketSnapshot / MT5Reader
→ Historical Acquisition / Portable Dataset / Dataset Identity
→ IntelligenceSnapshot
→ Strategy / Decision / Opportunity / Timing
→ TradePlan
→ Risk + Session/News
→ Execution / Reconciliation
→ ManagedTrade / Trade Manager
→ Dashboard
→ Replay / Ablation / Outcomes / Management / Stress / Walk-Forward
→ Evidence Manifest / Metrics / Episode Journal
→ Discovery / Invention / Promotion
```
