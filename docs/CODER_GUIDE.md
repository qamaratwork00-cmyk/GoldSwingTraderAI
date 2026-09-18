# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT  
**Version:** 0.8-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does not redefine trading behaviour.

## Core rule

> **Behaviour comes from the authoritative topic document. Code implements it. This guide only tells you where the real implementation lives.**

For project sequencing/recovery use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md`; for code-quality rules use `60-engineering/CODING_STANDARD.md`.

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

Positive DEMO requirement is a code invariant, tracked config is secret-free, and there is no irreversible broker-write implementation yet.

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

Primary files:

```text
decisions/trade_plan.py
risk/engine.py
risk/state.py
risk/__init__.py
```

Runtime boundary:

```text
DecisionSnapshot / READY Opportunity
→ structural Trade Plan
   Signal Price
   Approved Entry Reference
   structural invalidation
   volatility/noise buffer
   Initial SL
   Immediate / Primary / Expansion / Runner objectives
   immutable original-R price distance
   RR/path/plan quality
→ Risk Engine
   UTC risk-day profile
   target-size calculation
   broker volume-grid normalization
   min-lot evaluation
   all-in SL risk + friction exactly once
   daily lock / cooldown / episode re-entry / 0-of-1 capacity
   optional exact broker-margin fact
→ RiskEvaluation PASS / BLOCK / UNKNOWN
```

Phase-5 implementation invariants:
- Trade Plan defines market geometry before monetary sizing;
- BUY plans use Ask and SELL plans use Bid as the approved planning reference; Phase 7 still revalidates a fresh executable quote before broker write;
- a nearby low-quality internal obstacle may remain `Immediate Obstacle` instead of automatically becoming the Primary target and killing otherwise valid target room;
- frozen structural RR policy is enforced: `<1.20R` current plan degrades, `1.20–<1.50R` needs credible `~2R+` expansion path, `1.50R+` is acceptable subject to other geometry;
- fragile/noisy stop geometry becomes `DEGRADED/WAIT` rather than inventing a tighter stop;
- invalid plans contain explicit missing (`None`) stop geometry rather than fabricated placeholder SL/R values;
- score/Plan Quality never increases monetary risk;
- account profile is fixed from UTC risk-day start equity so floating P/L does not make profile boundaries oscillate intraday;
- SMALL raw size below broker minimum does not auto-block; actual `0.01` all-in risk is evaluated and may PASS in NORMAL or ELEVATED acceptable band;
- target sizing uses the midpoint of each frozen normal band only as an explicit implementation baseline: SMALL `3.75%`, MEDIUM `2.5%`, NORMAL `1.5%`;
- spread is not added twice when Bid/Ask planning geometry already embeds it; it remains visible as a diagnostic;
- current friction baseline is explicit/configurable (`2` ticks slippage reserve, commission supplied separately) and remains research/broker calibration work;
- heuristic `price × contract / leverage` margin is diagnostic only because Gold/CFD margin can be broker-specific;
- exact broker-required margin, when supplied, is authoritative and may block; Phase 7 must obtain/revalidate the broker margin fact before irreversible write;
- daily safety P/L, one-reset semantics, 3-loss cooldown and same-episode one-fresh-re-entry rules are executable pure state transitions ready for Phase-6 persistence.

Phase 5 still contains **zero broker writes**.

## Current deterministic test ownership

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
tests/test_trade_plan_risk.py
tests/test_risk_state_regressions.py
tests/test_margin_authority.py
```

Phase-5 tests protect BUY/SELL structural geometry, immediate-vs-primary target distinction, frozen RR guard, min-lot behaviour, no stop distortion, no score-leveraged risk, spread no-double-count, cash-flow-adjusted daily lock, one manual reset, 3-loss cooldown release, episode re-entry limit and exact broker-margin authority.

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
| Hard session/news state | `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` | **Phase 6 next** |
| Persistence/recovery | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | **Phase 6 next** |
| Execution gate/MT5 writes | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | Phase 7 |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | Phase 8 |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | Phase 9 |
| Replay/learning/research | `40-research-learning/*` | Phase 10 |

## Coding invariants

- Python 3.11+; standard library first;
- one normalized broker snapshot and one shared intelligence derivation;
- pure deterministic functions where practical;
- no decorative framework/inheritance layers;
- no raw broker writes from intelligence/strategies/decisions/risk/research/dashboard;
- no lookahead;
- hard safety never becomes a weighted strategy score;
- safety rules must not be multiplied into unnecessary filters that suppress valid opportunities;
- financial-authority credentials never enter tracked config/logs.

## Next implementation owner — Phase 6

Phase 6 builds two safety/state foundations without sending orders:

```text
A) hard session/news permission
   verified scheduled-close facts
   T-20/T-10 daily policy
   T-60/T-30 weekend policy
   Tier-1/Tier-2/Tier-3 news state
   reopen/post-news warmup

B) persistence/recovery
   lightweight durable store
   schema/version/integrity
   risk-day/cooldown/episode state
   Opportunity/TradePlan lifecycle
   unresolved execution/reconciliation state contracts
   startup recovery and broker-reconciliation inputs
```

Use the smallest safe persistence stack; standard-library SQLite is preferred unless an actual requirement proves it insufficient. Phase 6 must not add broker-write authority.

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

Do not weaken strategy or Trade Plan thresholds when the actual blocker belongs to data, state, margin or execution.

## Documentation rule

After each phase, update authoritative topic docs only where implementation choices/evidence matter, then update `60-engineering/MODULE_STRUCTURE.md`, this guide and relevant tests. Deterministic CI green is not the same as controlled DEMO certification.
