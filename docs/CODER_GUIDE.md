# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT  
**Version:** 1.0-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from the authoritative topic document. Code implements it. This guide tells you where the implementation lives and what is actually verified.**

Use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for sequencing/recovery and `60-engineering/CODING_STANDARD.md` for frozen code-quality rules.

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

Completed H4/H1/M15/M5 candles only; forming bars are excluded. Positive DEMO verification exists. Real terminal evidence is still required before external VERIFIED status.

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

One shared `MarketSnapshot` becomes one reusable `IntelligenceSnapshot`; ATR/indicators are reused rather than recalculated by every strategy.

### Phase 4 — Strategies / BUY-SELL fusion / Opportunity / Timing — IMPLEMENTED + deterministic CI green

```text
strategies/floor.py
decisions/fusion.py
decisions/opportunity.py
decisions/timing.py
decisions/snapshot.py
```

Six families evaluate in parallel. Missing optional evidence is omitted/reweighted, one strong family can lead, conflict remains visible, and poor timing normally creates WAIT instead of deleting a valid setup.

### Phase 5 — Trade Plan + Risk — IMPLEMENTED + deterministic CI green

```text
decisions/trade_plan.py
risk/engine.py
risk/state.py
```

Important implementation invariants:
- structural SL/objectives before monetary sizing;
- no fake stop geometry;
- frozen RR guard without becoming a high-RR-only bot;
- score never increases monetary risk;
- SMALL = any positive UTC day-start equity below `$300`; no `$100` floor;
- broker minimum volume is evaluated by actual all-in risk;
- exact broker margin is authoritative when available;
- daily lock/cooldown/episode state is explicit and restart-ready.

### Phase 6 — Hard Session/News Permission + Persistence — IMPLEMENTED + deterministic CI green

```text
risk/permissions.py
persistence/store.py
persistence/runtime_state.py
```

Hard permissions implement PRE_CLOSE/reopen and Tier-1/Tier-2 news policy without turning ordinary market evidence into extra filters.

Persistence uses standard-library SQLite with canonical JSON, checksums, schema versioning and transactional state/event rows. Risk day, cooldown, episode, Opportunity and TradePlan state round-trip with integrity validation.

### Phase 7 — Centralized Execution + Reconciliation — IMPLEMENTED deterministic baseline + CI green

```text
execution/models.py
execution/intent_store.py
execution/gate.py
execution/checks.py
execution/controller.py
execution/mt5_writer.py
execution/service.py
execution/reconcile.py
execution/__init__.py
```

Execution flow:

```text
hard authorities
→ Execution Permission Gate
→ durable ExecutionIntent
→ broker pre-check
→ fresh controller/fencing verification
→ persist SUBMITTING
→ exactly ONE order_send
→ acknowledgement classification
→ broker positions/orders/deals reconciliation
```

Key guarantees:
- one Intent ID can never be submitted twice;
- pre-check failure consumes zero send attempts;
- ambiguous acknowledgement blocks further writes and is never blindly retried;
- even successful MT5 acknowledgement requires broker-truth verification before `ACCEPTED_VERIFIED`;
- OPEN/MODIFY/CLOSE use the same narrow writer path;
- elevated spread/drift may still pass after full revalidation; only frozen hard limits block;
- stale fencing epoch cannot write.

**Still pending before DEMO certification:** production shared cross-laptop coordination backend and real Windows/MT5 execution evidence. The in-memory coordination backend is deterministic test infrastructure only and is not sufficient cross-machine authority.

### Phase 8 — Trade Manager / Runner / Exit — IMPLEMENTED deterministic baseline + CI green

```text
management/models.py
management/manager.py
management/store.py
management/execution.py
management/__init__.py
```

Management flow:

```text
verified bot-owned ManagedTrade
+ fresh MarketSnapshot / IntelligenceSnapshot
→ continuation vs reversal evidence
→ HOLD / PROTECT / TRAIL / RUNNER / EXIT
→ optional governed ExecutionIntent
→ broker verification
→ only then update/clear durable ManagedTrade state
```

Implemented behaviour:
- Primary target is a checkpoint, not automatic exit;
- an ordinary pullback or one opposite M5 candle does not force exit;
- no fixed small-profit/breakeven trigger;
- protection/trailing requires a confirmed structural reference and positive progress;
- stop can tighten but cannot widen beyond original approved risk;
- Expansion-to-Runner needs strong continuation, limited reversal, adequate structure/path and a real next target;
- profit alone cannot extend TP;
- PRE_CLOSE flatten overrides a healthy runner;
- local SL/TP/closed state changes only after broker result is verified;
- original R and objectives persist through restart.

Current management score/R thresholds are **explicit research-calibratable baselines**, not frozen profitability truth.

## Current deterministic test ownership

Important suites include:

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
```

CI gates:

```text
ruff check .
pytest
financial-secret scan
```

Passing deterministic CI is software evidence, not live DEMO certification or profitability proof.

## Feature ownership index

| Feature | Authority | Current owner |
|---|---|---|
| Market data/history | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | `market_data/` |
| Candle/quant/technical/liquidity/session/news | `10-market-intelligence/*` | `intelligence/` |
| Strategy families | `20-trading-decisions/STRATEGY_FLOOR.md` | `strategies/floor.py` |
| Fusion + Opportunity + Timing | `20-trading-decisions/*` | `decisions/fusion.py`, `opportunity.py`, `timing.py` |
| Trade Plan | `20-trading-decisions/TRADE_PLAN.md` | `decisions/trade_plan.py` |
| Risk | `30-risk-execution/RISK_CONTRACT.md` | `risk/engine.py`, `risk/state.py` |
| Session/news hard permission | `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` | `risk/permissions.py` |
| Persistence | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | `persistence/` |
| Execution | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | `execution/` |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | `management/` |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | Phase 9 next |
| Replay/learning/research | `40-research-learning/*` | Phase 10 |

## Coding invariants

- Python 3.11+; standard library first;
- shared verified facts instead of duplicate MT5 reads/calculations;
- no lookahead;
- soft evidence is not multiplied into unnecessary hard filters;
- positive balance alone is not a trade restriction;
- raw broker writes exist only in the narrow execution boundary;
- critical local state never pretends a broker write succeeded before reconciliation;
- no decorative framework/service-manager/factory architecture;
- financial-authority credentials never enter tracked config/logs/state exports.

## Next implementation owner — Phase 9

Build the compact operator/dashboard layer from authoritative state rather than duplicating decision logic. Preserve the useful GoldScalperAI facts the user requested and add Decision, Execution, Learning, Backup and Health visibility.

Phase 9 must remain presentation/operation only: dashboard code cannot create trading authority or call raw MT5 writes.

## Debugging order

```text
MarketSnapshot
→ IntelligenceSnapshot
→ StrategyFloorReport
→ DecisionBoard
→ Opportunity / EntryTiming
→ TradePlan
→ Risk + Session/News
→ Execution Gate / Intent / Reconciliation
→ ManagedTrade / Trade Manager
→ Dashboard
```

Do not weaken strategy/TradePlan rules when the actual problem belongs to broker data, state, risk or execution.
