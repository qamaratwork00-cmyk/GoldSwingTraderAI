# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT  
**Version:** 1.2-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from the authoritative topic document. Code implements it. This guide tells you where implementation lives and what has actually been verified.**

Use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for sequencing/recovery and `60-engineering/CODING_STANDARD.md` for frozen engineering rules.

## Current implementation checkpoint — 2026-09-18

### Phase 1 — Foundation — IMPLEMENTED + deterministic CI green

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

### Phase 2 — MT5 read layer — IMPLEMENTED + deterministic CI green; live Windows DEMO proof pending

```text
domain/market.py
market_data/mt5_reader.py
market_data/snapshot.py
```

Completed H4/H1/M15/M5 candles only; forming bars are excluded. Positive DEMO verification exists.

### Phase 3 — Market intelligence — IMPLEMENTED + deterministic CI green

```text
intelligence/indicators.py
intelligence/candle_structure.py
intelligence/technical.py
intelligence/liquidity.py
intelligence/session.py
intelligence/news.py
intelligence/snapshot.py
```

One verified market snapshot feeds one shared intelligence derivation; duplicate indicator/ATR reads are avoided.

### Phase 4 — Strategies + fusion + Opportunity + Entry Timing — IMPLEMENTED + deterministic CI green

```text
strategies/floor.py
decisions/fusion.py
decisions/opportunity.py
decisions/timing.py
decisions/snapshot.py
```

Six families evaluate in parallel. Missing optional evidence is omitted/reweighted rather than zeroed. One strong family can lead. Poor timing normally yields WAIT rather than destroying a valid opportunity.

### Phase 5 — Trade Plan + Risk — IMPLEMENTED + deterministic CI green

```text
decisions/trade_plan.py
risk/engine.py
risk/state.py
```

Structural geometry precedes monetary sizing. SMALL is any positive UTC day-start equity below `$300`; there is no `$100` floor. Minimum lot is evaluated by actual all-in risk. Score never increases risk. Exact broker margin is authoritative when available.

### Phase 6 — Session/News Permission + Persistence — IMPLEMENTED + deterministic CI green

```text
risk/permissions.py
persistence/store.py
persistence/runtime_state.py
```

PRE_CLOSE/reopen/news safety are explicit hard authorities. Persistence uses standard-library SQLite + canonical JSON/checksum/schema/event records and restores critical state without silently defaulting corruption.

### Phase 7 — Execution + Reconciliation — IMPLEMENTED deterministic baseline + CI green

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
→ acknowledgement
→ broker reconciliation
```

A success-like MT5 ACK is not final truth until broker state verifies it. An Intent ID cannot be sent twice. Ambiguous acknowledgement is never blindly retried. Elevated spread/drift may pass after full revalidation; only frozen hard limits block.

Pending before failover/DEMO certification: production shared cross-laptop coordination backend and real Windows/MT5 execution evidence. In-memory coordination is test-only.

### Phase 8 — Trade Manager — IMPLEMENTED deterministic baseline + CI green

```text
management/models.py
management/manager.py
management/store.py
management/execution.py
```

HOLD / PROTECT / TRAIL / RUNNER / EXIT operates on verified bot-owned positions. Ordinary pullbacks do not force exit; small profit alone does not force breakeven; Primary is a checkpoint; runner needs fresh continuation + actual next objective; PRE_CLOSE overrides continuation. Durable trade state changes only after broker verification.

### Phase 9 — Dashboard / Operator presentation — IMPLEMENTED deterministic baseline + CI green

```text
operator/dashboard.py
operator/__init__.py
```

Pure-standard-library read-only renderer. It preserves requested GoldScalperAI visibility and consumes, rather than recreates, decision/risk/execution authority.

### Phase 10 — Replay / Learning / Discovery / Invention — IMPLEMENTED deterministic foundation + CI green

```text
research/replay.py
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
→ actual/counterfactual outcome metrics
→ durable research episodes
→ approved-primitive observations
→ recurring cluster detection
→ candidate creation OR explicit suppression reason
→ durable CandidateRegistry
→ governed validation/promotion lifecycle
```

Important implementation guarantees:
- replay is prefix-only and labeled `BAR_CLOSE`, never falsely claimed tick-perfect;
- actual broker P/L and counterfactual missed/blocked MFE stay separate;
- research measures Net R, drawdown, Capture Efficiency, 2R/3R/4R reach and Opportunity Recall rather than win rate alone;
- StrategyMemory is version/environment/context isolated and its initial adaptive influence is bounded;
- discovery requires independent episode IDs; duplicate records cannot fake sample size;
- candidate recipes use only audited declarative primitives, never arbitrary Python/eval/exec;
- recurring evidence can create a real durable `VARIANT`, `NEW_FAMILY`, `ENTRY_POLICY` or `EXIT_POLICY` candidate;
- substantially duplicate/rejected candidates are remembered and suppressed after restart;
- discovery liveness is explicit: eligible evidence must create a candidate or return a governed suppression reason;
- candidates cannot skip validation stages;
- locked candidate fingerprint must survive unchanged through one-shot final holdout;
- autonomous candidates cannot self-promote;
- research/promotion registries never grant direct broker authority.

Initial discovery sample/similarity/complexity values and learning influence remain research-calibratable baselines, not frozen profitability truth.

## Deterministic test ownership

Major suites include:

```text
tests/test_market_data.py
tests/test_intelligence_core.py
tests/test_intelligence_snapshot.py
tests/test_technical_liquidity.py
tests/test_strategy_decisions.py
tests/test_trade_plan_risk.py
tests/test_risk_state_regressions.py
tests/test_margin_authority.py
tests/test_session_news_permissions.py
tests/test_persistence_recovery.py
tests/test_execution_safety.py
tests/test_trade_manager.py
tests/test_management_execution.py
tests/test_dashboard.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

CI gates remain:

```text
ruff check .
pytest
financial-secret scan
```

Deterministic CI green is software evidence, not profitability proof or live DEMO certification.

## Feature ownership index

| Feature | Authority | Current owner |
|---|---|---|
| Market data/history | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | `market_data/` |
| Full market intelligence | `10-market-intelligence/*` | `intelligence/` |
| Strategy floor | `20-trading-decisions/STRATEGY_FLOOR.md` | `strategies/floor.py` |
| Fusion/Opportunity/Timing | `20-trading-decisions/*` | `decisions/` |
| Trade Plan | `20-trading-decisions/TRADE_PLAN.md` | `decisions/trade_plan.py` |
| Risk | `30-risk-execution/RISK_CONTRACT.md` | `risk/engine.py`, `risk/state.py` |
| Session/news hard permission | `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` | `risk/permissions.py` |
| Persistence | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | `persistence/` |
| Execution | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | `execution/` |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | `management/` |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | `operator/dashboard.py` |
| Replay/validation | `40-research-learning/RESEARCH_AND_VALIDATION.md` | `research/replay.py`, `metrics.py` |
| StrategyMemory | `40-research-learning/LEARNING_AND_AI_BOUNDARIES.md` | `research/learning.py` |
| Discovery/invention | `40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md`, `AUTONOMOUS_STRATEGY_INVENTION.md` | `research/episode_journal.py`, `discovery.py`, `invention.py` |
| Promotion lifecycle | `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md` | `research/promotion.py` |

## Coding invariants

- Python 3.11+; standard library first for production runtime;
- no lookahead;
- shared verified facts instead of duplicate MT5/calculation work;
- soft evidence must not become a pile of arbitrary hard filters;
- positive balance alone is not an eligibility restriction;
- raw broker writes live only in `execution/mt5_writer.py`;
- critical local state never pretends ambiguous broker action succeeded;
- dashboard/research/discovery have zero raw production broker authority;
- discovery must not be silently inert when eligible evidence exists;
- no unnecessary frameworks/factories/service-manager layers;
- financial-authority credentials never enter tracked project state.

## Next engineering work

Phase 10 still needs broader replay/fault/stress evidence and integration of research state into live operator status. After that, Phase 11 is controlled Windows/MT5 DEMO integration/certification.

Research tuning must optimize **accuracy + Net R + drawdown + opportunity recall + large-move capture + sensible trade frequency**, not win rate alone. A change that removes many good opportunities to improve a headline percentage is not automatically an improvement.

## Debugging order

```text
MarketSnapshot
→ IntelligenceSnapshot
→ StrategyFloor
→ Decision / Opportunity / Timing
→ TradePlan
→ Risk + Session/News
→ Execution / Reconciliation
→ ManagedTrade / Trade Manager
→ Dashboard
→ Replay / Metrics / Episode Journal
→ Discovery / Invention / Promotion
```
