# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT  
**Version:** 0.9-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from the authoritative topic document. Code implements it. This guide only tells you where the real implementation lives.**

For project sequencing/recovery use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md`; for code-quality rules use `60-engineering/CODING_STANDARD.md`.

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

Positive DEMO requirement is a code invariant, tracked config is secret-free, and irreversible broker writes are still absent.

### Phase 2 — MT5 read layer — IMPLEMENTED + deterministic CI green; live Windows DEMO proof pending

```text
domain/market.py
market_data/mt5_reader.py
market_data/snapshot.py
app/main.py
```

Runtime:

```text
Settings
→ MT5 read-only connection/account facts + DEMO verification
→ Gold symbol/spec/quote
→ completed H4/H1/M15/M5 history
→ data-quality evaluation
→ MarketSnapshot
```

Forming bars are excluded. Raw MT5 structures stay at the boundary. Real MetaTrader5 DEMO-terminal evidence is still required before calling this externally VERIFIED.

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

Runtime:

```text
MarketSnapshot
→ IndicatorSeries once/timeframe
→ QuantReport
→ StructureReport using shared ATR
→ TechnicalReport
→ LiquidityReport
→ SessionReport + optional NewsFacts
→ IntelligenceSnapshot
```

Market intelligence has zero broker authority. News/session here are facts/context, not hard permission.

### Phase 4 — Strategies + fusion + Opportunity + Entry Timing — IMPLEMENTED + deterministic CI green

```text
strategies/floor.py
decisions/fusion.py
decisions/opportunity.py
decisions/timing.py
decisions/snapshot.py
```

Runtime:

```text
IntelligenceSnapshot
→ six strategy families in parallel, each BUY + SELL
→ StrategyFloorReport
→ independent BUY Thesis + SELL Thesis
→ bounded correlation/synergy + conflict + Red Team
→ Opportunity lifecycle with stable IDs
→ M5 Entry Timing
→ DecisionSnapshot
```

Important behaviour:
- all six families evaluate the same snapshot; no sequential filter chain;
- optional unavailable evidence is omitted/reweighted rather than forced to zero;
- one strong family may lead; all-six consensus is not required;
- strong opposition remains visible as conflict rather than arbitrary veto;
- Opportunity and Entry Timing are separate;
- severe extension normally becomes `WAIT`, not thesis deletion;
- MISSED re-arm requires genuinely fresh structural/timing evidence;
- current scores/weights are explicit research-calibratable baselines, not frozen profitability truth.

### Phase 5 — Trade Plan + Risk Engine — IMPLEMENTED + deterministic CI green

```text
decisions/trade_plan.py
risk/engine.py
risk/state.py
```

Runtime:

```text
READY Opportunity
→ structural Trade Plan
→ broker-aware monetary RiskEvaluation
```

Phase-5 invariants:
- structural invalidation/SL/objectives exist before monetary sizing;
- low-quality nearby obstacles do not automatically become the Primary target;
- frozen RR guard is implemented without becoming a high-RR-only trade filter;
- invalid plans use explicit missing geometry rather than fake SL/R values;
- strategy/Plan Quality never increases monetary risk;
- SMALL is **any positive UTC day-start equity below $300**; there is no `$100` minimum-account floor;
- practical broker minimum volume such as `0.01` is evaluated from actual all-in risk rather than raw fractional-lot theory;
- heuristic margin is diagnostic only; exact broker margin is authoritative when supplied;
- daily safety P/L, one-reset semantics, 3-loss cooldown and same-episode re-entry rules are executable state transitions.

### Phase 6 — Hard Session/News Permission + Persistence — IMPLEMENTED + deterministic CI green

Primary files:

```text
risk/permissions.py
persistence/store.py
persistence/runtime_state.py
persistence/__init__.py
diagnostics/reasons.py
```

Permission flow:

```text
BrokerSessionFacts
→ MarketPermission

NewsFacts + NewsRecoveryFacts
→ NewsPermission

MarketPermission + NewsPermission
→ SessionNewsPermission
```

Implemented safety behaviour:
- daily PRE_CLOSE `T-20m` no-new-entry and `T-10m` flatten;
- weekend `T-60m` / `T-30m`;
- daily reopen requires one clean completed M5 plus normalized conditions;
- weekend reopen requires two clean M5 candles plus gap assessment and normalized conditions;
- holiday context is caution, not a fake market closure;
- required session schedule/news truth missing → `UNKNOWN`, never invented clear;
- Tier-1/Tier-2 hard windows and post-news severe-dislocation recovery are explicit;
- scheduled-news blackout does not itself force-close an existing managed trade.

Persistence flow:

```text
critical typed runtime state
→ RuntimeStateRepository
→ StateStore
→ SQLite canonical JSON + checksum + schema version + event rows
→ RecoveryBundle
```

Phase-6 persistence currently round-trips:
- `RiskDayState`;
- `CooldownState`;
- `EpisodeRiskState`;
- active `Opportunity`;
- active `TradePlan` with target/original-R context.

Recovery validates checksum/database integrity and Opportunity/Episode/TradePlan identity. Corrupt or mismatched critical state raises an explicit error instead of silently becoming blank state.

Execution Intent/order/trade persistence is deliberately not faked before those Phase-7 types exist.

## Current deterministic test ownership

Core suites now include:

```text
tests/test_settings.py
tests/test_market_data.py
tests/test_app_readiness.py
tests/test_intelligence_core.py
tests/test_intelligence_snapshot.py
tests/test_technical_liquidity.py
tests/test_strategy_decisions.py
tests/test_trade_plan_risk.py
tests/test_risk_state_regressions.py
tests/test_margin_authority.py
tests/test_session_news_permissions.py
tests/test_persistence_recovery.py
```

CI gates remain:

```text
ruff check .
pytest
financial-secret scan
```

Do not weaken a safety/regression test merely to make CI green.

## Feature ownership index

| Feature | Authority | Current owner |
|---|---|---|
| Market data/history | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | `market_data/` IMPLEMENTED |
| Candle/structure | `10-market-intelligence/CANDLE_STRUCTURE.md` | `intelligence/candle_structure.py` IMPLEMENTED baseline |
| Quant/volatility | `10-market-intelligence/INDICATORS_AND_VOLATILITY.md` | `intelligence/indicators.py` IMPLEMENTED baseline |
| Technical/location | `10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md` | `intelligence/technical.py` IMPLEMENTED baseline |
| Liquidity/SMC | `10-market-intelligence/LIQUIDITY_AND_SMC.md` | `intelligence/liquidity.py` IMPLEMENTED baseline |
| Session context | `10-market-intelligence/SESSION_CONTEXT.md` | `intelligence/session.py` IMPLEMENTED baseline |
| Scheduled news facts | `10-market-intelligence/FUNDAMENTAL_AND_NEWS.md` | `intelligence/news.py` baseline; production provider TBD |
| Strategy families | `20-trading-decisions/STRATEGY_FLOOR.md` | `strategies/floor.py` IMPLEMENTED baseline |
| BUY/SELL fusion + Red Team | `20-trading-decisions/SCORING_AND_DECISION_FUSION.md` | `decisions/fusion.py` IMPLEMENTED baseline |
| Opportunity/Entry Timing | `20-trading-decisions/ENTRY_TIMING.md` | `decisions/opportunity.py`, `timing.py` IMPLEMENTED baseline |
| Trade Plan | `20-trading-decisions/TRADE_PLAN.md` | `decisions/trade_plan.py` IMPLEMENTED baseline |
| Monetary risk | `30-risk-execution/RISK_CONTRACT.md` | `risk/engine.py`, `risk/state.py` IMPLEMENTED baseline |
| Hard session/news state | `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` | `risk/permissions.py` IMPLEMENTED baseline |
| Persistence/recovery | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | `persistence/` IMPLEMENTED foundation |
| Execution gate/MT5 writes | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | **Phase 7 next** |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | Phase 8 |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | Phase 9 |
| Replay/learning/research | `40-research-learning/*` | Phase 10 |

## Coding invariants

- Python 3.11+; standard library first;
- one normalized broker snapshot and shared derived facts;
- pure deterministic functions where practical;
- no decorative framework/inheritance layers;
- no lookahead;
- hard safety never becomes weighted strategy scoring;
- soft evidence must not be multiplied into unnecessary hard filters;
- positive account balance alone is not an artificial minimum-balance trade restriction;
- no raw broker writes from intelligence/strategies/decisions/risk/persistence/research/dashboard;
- financial-authority credentials never enter tracked config/logs/state exports.

## Next implementation owner — Phase 7

Phase 7 introduces the **only irreversible MT5 write path**.

Build in this order:

```text
1. Execution Intent + order lifecycle types
2. persist intent/lifecycle before write
3. broker position/order/deal reconciliation
4. controller lease + monotonic fencing ownership
5. fresh execution quote/spread/drift/spec/margin validation
6. centralized Execution Permission Gate
7. one-shot governed MT5 create/modify/close adapter
8. acknowledgement classification + reconcile; never blind retry
```

The gate consumes existing authorities rather than re-implementing them:

```text
positive DEMO guard
account identity
fresh data/quote
RiskEvaluation
SessionNewsPermission
position ownership/capacity
controller ownership
order/reconciliation state
exact broker checks
→ ALLOW / BLOCK / UNKNOWN
```

Phase 7 must remain compact. No strategy/scoring/dashboard module may gain raw MT5 write access.

## Debugging order

```text
MarketSnapshot
→ IntelligenceSnapshot
→ StrategyFloorReport
→ BUY/SELL DecisionBoard
→ Opportunity
→ EntryTiming
→ Trade Plan
→ Risk
→ Session/News Permission
→ Persistence/Recovery
→ Execution Gate
→ broker lifecycle
```

Do not weaken strategy or Trade Plan thresholds when the actual blocker belongs to data, state, margin or execution.

## Documentation rule

After each phase, update authoritative topic docs only where implementation choices/evidence matter, then update `60-engineering/MODULE_STRUCTURE.md`, this guide and relevant tests. Deterministic CI green is not the same as controlled DEMO certification.
