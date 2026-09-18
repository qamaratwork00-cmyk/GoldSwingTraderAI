# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT  
**Version:** 1.1-implementation-map  
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

PRE_CLOSE/reopen/news safety are explicit hard authorities. Persistence uses standard-library SQLite + canonical JSON/checksum/schema/event records and restores risk/cooldown/episode/Opportunity/TradePlan state without silently defaulting corrupted critical data.

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

A success-like MT5 ACK is not treated as final truth until broker state verifies it. An Intent ID cannot be sent twice. Ambiguous acknowledgement is never blindly retried. Elevated spread/drift may pass after full revalidation; only frozen hard limits block.

Pending before failover/DEMO certification: production shared cross-laptop coordination backend and real Windows/MT5 execution evidence. In-memory coordination is test-only.

### Phase 8 — Trade Manager — IMPLEMENTED deterministic baseline + CI green

```text
management/models.py
management/manager.py
management/store.py
management/execution.py
```

The manager owns HOLD / PROTECT / TRAIL / RUNNER / EXIT for verified bot-owned positions. Ordinary pullbacks do not force exit; small profit alone does not force breakeven; Primary is a checkpoint; runner needs fresh continuation + actual next objective; PRE_CLOSE overrides continuation. Durable trade state changes only after broker verification.

Numeric management thresholds remain research-calibratable baselines.

### Phase 9 — Dashboard / Operator presentation — IMPLEMENTED deterministic baseline + CI green

```text
operator/dashboard.py
operator/__init__.py
```

Current terminal renderer is pure standard library and read-only. It displays already-authoritative facts and preserves requested GoldScalperAI visibility: symbol/account/DEMO/role, Bid/Ask/spread/M5 timer, structure, EMA20/50, RSI, ATR, decision/reason/scores, risk/lot/day P&L/limits, position/loss streak/cooldown, execution/controller/reconciliation, open-trade SL/TP/objectives/R/manager, Learning/Backup/Health summaries.

It provides emoji + plain-text fallback and concise Roman-Urdu reason explanations. It does not call MetaTrader5, Risk Engine or Execution Gate. Runtime state-builder/in-place live refresh remain later integration work.

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
| Replay/learning/research | `40-research-learning/*` | **Phase 10 next** |

## Coding invariants

- Python 3.11+; standard library first for production runtime;
- no lookahead;
- shared verified facts instead of duplicate MT5/calculation work;
- soft evidence must not become a pile of arbitrary hard filters;
- positive balance alone is not an eligibility restriction;
- raw broker writes live only in `execution/mt5_writer.py`;
- critical local state never pretends ambiguous broker action succeeded;
- dashboard/research have zero production broker authority;
- no unnecessary frameworks/factories/service-manager layers;
- financial-authority credentials never enter tracked project state.

## Next implementation owner — Phase 10

Build chronological replay, journals/performance metrics, entry/exit learning, large-move recall and governed bounded strategy research/invention.

Phase 10 must optimize for **accuracy plus opportunity recall**, not win rate alone. It must measure missed valid moves and capture efficiency so research does not make the bot progressively over-restrictive.

Research may create/evaluate declarative candidates but cannot change hard risk/execution rules, call the broker, use future data, execute generated Python or silently promote itself into production.

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
→ Replay / Research / Learning
```
