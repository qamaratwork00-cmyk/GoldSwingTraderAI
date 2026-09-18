# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT  
**Version:** 0.7-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from the authoritative topic document. Code implements it. This guide only tells you where the real implementation lives.**

For whole-project sequencing/recovery use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md`; for code-quality rules use `60-engineering/CODING_STANDARD.md`.

## Current implementation checkpoint — 2026-09-18

### Phase 1 — Foundation — IMPLEMENTED + deterministic CI green

Primary owners:

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

Positive DEMO requirement is a code invariant, tracked config is secret-free, and there is still no irreversible broker-write implementation.

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

Primary files:

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
→ Opportunity create/update with stable opportunity_id/episode_id
→ M5 Entry Timing
→ DecisionSnapshot
```

Phase-4 invariants now executable:
- all six families evaluate from the same snapshot; no sequential filter chain;
- optional unavailable evidence is omitted/reweighted rather than forced to zero;
- strong opposition remains visible as conflict;
- Opportunity and Entry Timing are separate;
- severe extension normally becomes `WAIT`, not thesis deletion;
- MISSED re-arm requires a genuinely fresh event assertion;
- surviving setup keeps Opportunity/Episode identity;
- `ENTER_BUY/ENTER_SELL` means analytical readiness only, not broker permission;
- strategy/decision modules contain no MetaTrader5/order-send boundary.

Current strategy/fusion/timing numbers are research-calibratable implementation baselines, not frozen profitability truth.

## Current test ownership

```text
tests/test_settings.py
tests/test_domain.py
tests/test_mt5_reader.py
tests/test_market_snapshot.py
tests/test_app_readiness.py
tests/test_indicators_structure.py
tests/test_technical_liquidity.py
tests/test_intelligence_snapshot.py
tests/test_strategy_decisions.py
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
| Decision orchestration | supporting engineering owner | `decisions/snapshot.py` IMPLEMENTED |
| Trade Plan | `20-trading-decisions/TRADE_PLAN.md` | **Phase 5 next** |
| Monetary risk | `30-risk-execution/RISK_CONTRACT.md` | **Phase 5 next** |
| Hard session/news state | `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` | Phase 6 |
| Persistence/recovery | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | Phase 6 |
| Execution gate/MT5 writes | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | Phase 7 |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | Phase 8 |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | Phase 9 |
| Replay/learning/research | `40-research-learning/*` | Phase 10 |

## Coding invariants

- Python 3.11+; standard library first;
- one normalized broker snapshot and one shared intelligence derivation;
- pure deterministic functions where practical;
- no decorative framework/inheritance layers;
- no raw broker writes from intelligence/strategies/decisions/research/dashboard;
- no lookahead;
- hard safety never becomes a weighted strategy score;
- financial-authority credentials never enter tracked config/logs.

## Next implementation owner — Phase 5

Consume `DecisionSnapshot` and build:

```text
analytically ready Opportunity
→ structural Trade Plan
   signal/reference/executable-price separation
   structural invalidation + volatility buffer
   Primary / Expansion / Runner objectives
   original R immutable
→ broker-aware Risk Result
   SMALL/MEDIUM/NORMAL profile
   executable lot/min-lot handling
   all-in risk/ceiling/margin facts
   daily Account Safety P/L state inputs
```

Phase 5 still must not send orders. Hard session/news/controller/execution permission remains later.

## Debugging order

```text
MarketSnapshot
→ IntelligenceSnapshot
→ StrategyFloorReport
→ BUY/SELL DecisionBoard
→ Opportunity
→ EntryTiming
→ Trade Plan
→ Risk/session/news
→ Execution Gate
→ broker lifecycle
```

Do not weaken strategy when the actual problem belongs to risk/execution/data.

## Documentation rule

After each phase, update the authoritative topic docs, `60-engineering/MODULE_STRUCTURE.md`, this guide, relevant tests and operator docs only for functionality that actually exists. Deterministic CI green is not the same as live DEMO certification.
