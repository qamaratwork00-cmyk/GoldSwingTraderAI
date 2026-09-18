# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT  
**Version:** 0.6-implementation-map  
**Authority:** Feature-oriented developer navigation and implementation map. It does **not** redefine trading behaviour.

## Purpose

Use this file to find the real code owner for a feature and to trace a change across the system without creating duplicate authority.

Core rule:

> **Behaviour comes from the authoritative topic document. Code implements it. This guide tells you where to look; it does not invent another version of the rule.**

For whole-project phase sequencing/recovery use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md`. For code-quality rules use `60-engineering/CODING_STANDARD.md`.

## Authority/change path

For trading-affecting work, follow only the layers that actually apply:

```text
authoritative design contract
→ config/domain facts
→ market-data snapshot
→ market intelligence
→ strategy/decision/timing
→ Trade Plan
→ risk/session/news authority
→ centralized execution permission
→ governed broker write
→ persistence/reconciliation
→ operator/research/tests
```

Do not fix a cross-cutting issue only in the dashboard or most visible file.

## Current implementation checkpoint — 2026-09-18

### Phase 1 — Foundation — IMPLEMENTED + deterministic CI green

Primary files:

```text
src/goldswingtraderai/config/settings.py
src/goldswingtraderai/domain/enums.py
src/goldswingtraderai/domain/ids.py
src/goldswingtraderai/domain/models.py
src/goldswingtraderai/diagnostics/reasons.py
src/goldswingtraderai/diagnostics/logging.py
src/goldswingtraderai/app/main.py
scripts/scan_financial_secrets.py
.github/workflows/ci.yml
```

Implemented facts:
- immutable/typed baseline domain contracts;
- local secret-free configuration pattern;
- positive DEMO requirement is a code invariant, not a user-disableable switch;
- structured logging foundation;
- financial-secret scanner in CI;
- no broker-write implementation.

### Phase 2 — MT5 read layer + MarketSnapshot — IMPLEMENTED, live Windows DEMO evidence still pending

Primary files:

```text
src/goldswingtraderai/domain/market.py
src/goldswingtraderai/market_data/mt5_reader.py
src/goldswingtraderai/market_data/snapshot.py
src/goldswingtraderai/app/main.py
```

Runtime path:

```text
Settings
→ MT5Reader.initialize()
→ account facts + positive DEMO verification
→ optional account/server pin check
→ XAUUSDm/XAUUSD resolution
→ SymbolSpec + Bid/Ask
→ completed H4/H1/M15/M5 candles
→ data-quality evaluation
→ MarketSnapshot
```

Important implementation facts:
- read layer contains no irreversible order-send path;
- forming bar is excluded from completed-candle history;
- downstream code consumes normalized domain types, not raw MT5 named-tuples;
- broker/account/symbol facts are read once per snapshot scope where practical;
- real Windows/MetaTrader5 DEMO-terminal forward verification must still be recorded before Phase 2 is called externally VERIFIED.

### Phase 3 — Market intelligence — IMPLEMENTED + deterministic CI green

Primary files:

```text
src/goldswingtraderai/intelligence/indicators.py
src/goldswingtraderai/intelligence/candle_structure.py
src/goldswingtraderai/intelligence/technical.py
src/goldswingtraderai/intelligence/liquidity.py
src/goldswingtraderai/intelligence/session.py
src/goldswingtraderai/intelligence/news.py
src/goldswingtraderai/intelligence/snapshot.py
```

Unified runtime path:

```text
MarketSnapshot
→ per-timeframe IndicatorSeries computed once
→ QuantReport
→ StructureReport using the same precomputed ATR
→ TechnicalReport
→ LiquidityReport
→ M5 SessionReport
→ optional normalized NewsFacts
→ IntelligenceSnapshot
```

Implemented intelligence boundaries:
- `indicators.py`: EMA20/EMA50, RSI14, ATR14 baseline plus volatility/momentum/extension facts;
- `candle_structure.py`: completed-candle facts, causal confirmed swings with separate `pivot_time`/`confirmed_at`, structure state, break hierarchy and protected swings;
- `technical.py`: adaptive zones, location and target-room facts from existing structure/ATR;
- `liquidity.py`: clustered liquidity pools, sweep vs accepted-break facts, FVG and structurally-qualified OB primitives;
- `session.py`: timezone-safe Asia/London/New York/overlap context using standard-library `zoneinfo`;
- `news.py`: provider-neutral scheduled-event normalization, TIER 1/2/3 facts, event windows, cluster merging and provider freshness state;
- `snapshot.py`: one reusable multi-timeframe intelligence object for later strategies.

The market-intelligence package has **zero broker authority**. Session/news here are facts/context only; hard permission remains under `30-risk-execution/`.

## Current deterministic test ownership

Important suites include:

```text
tests/test_settings.py
tests/test_domain.py
tests/test_mt5_reader.py
tests/test_market_snapshot.py
tests/test_app_readiness.py
tests/test_indicators_structure.py
tests/test_technical_liquidity.py
tests/test_intelligence_snapshot.py
```

CI currently runs:

```text
ruff check .
pytest
financial-secret scan
```

Do not weaken these gates to make a build green.

## Feature ownership index

| Feature | Behaviour authority | Primary code owner/current state |
|---|---|---|
| Global invariants | `00-foundation/SYSTEM_CONTRACT.md` | domain/config + later coordinator |
| Market data/history | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | `market_data/` IMPLEMENTED |
| Candle/structure | `10-market-intelligence/CANDLE_STRUCTURE.md` | `intelligence/candle_structure.py` IMPLEMENTED baseline |
| EMA/RSI/ATR/volatility | `10-market-intelligence/INDICATORS_AND_VOLATILITY.md` | `intelligence/indicators.py` IMPLEMENTED baseline |
| S/R/location/target room | `10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md` | `intelligence/technical.py` IMPLEMENTED baseline |
| Liquidity/FVG/OB | `10-market-intelligence/LIQUIDITY_AND_SMC.md` | `intelligence/liquidity.py` IMPLEMENTED baseline |
| Session context | `10-market-intelligence/SESSION_CONTEXT.md` | `intelligence/session.py` IMPLEMENTED baseline |
| Scheduled news facts | `10-market-intelligence/FUNDAMENTAL_AND_NEWS.md` | `intelligence/news.py` IMPLEMENTED baseline; production provider TBD |
| Strategy families | `20-trading-decisions/STRATEGY_FLOOR.md` | Phase 4 |
| BUY/SELL fusion + Red Team | `20-trading-decisions/SCORING_AND_DECISION_FUSION.md` | Phase 4 |
| Opportunity/entry timing | `20-trading-decisions/ENTRY_TIMING.md` | Phase 4 |
| Trade Plan | `20-trading-decisions/TRADE_PLAN.md` | Phase 5 |
| Monetary risk | `30-risk-execution/RISK_CONTRACT.md` | Phase 5 |
| Hard session/news state | `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` | Phase 6 |
| Persistence/recovery | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | Phase 6 |
| Execution gate/MT5 writes | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | Phase 7 |
| Trade Manager | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | Phase 8 |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | Phase 9 |
| Replay/learning/research | `40-research-learning/*` | Phase 10 |

## Coding invariants

Keep these implementation rules visible while coding:

- Python 3.11+;
- standard library first, minimal runtime dependencies;
- pure functions for deterministic calculations where practical;
- classes only for genuine lifecycle/state/resource ownership;
- one verified snapshot and shared derived facts instead of repeated MT5 reads/calculations;
- no giant all-in-one `bot.py` and no decorative Service/Manager/Factory framework;
- no raw MT5 write from intelligence/strategy/research/dashboard;
- unknown critical broker/risk/order/controller state must not become implicit permission;
- no lookahead in live/replay chronology;
- financial-authority credentials never enter tracked config/templates/logs.

The exact safety/trading values are owned by their authoritative topic docs, not this guide.

## Next implementation owner — Phase 4

Phase 4 should consume only `IntelligenceSnapshot` and build:

```text
six strategy-family reports in parallel
→ independent BUY thesis
→ independent SELL thesis
→ conflict / evidence coverage / Red Team
→ Opportunity lifecycle
→ M5 Entry Timing: ENTER / WAIT / MISSED / INVALID
```

It must not query MT5 directly, size lots, place orders, or turn every soft imperfection into a hard filter.

## Debugging order

When later runtime says no trade, inspect in authority order:

```text
market/account/data truth
→ intelligence evidence
→ strategy family reports
→ BUY/SELL fusion/conflict
→ opportunity state
→ entry timing
→ Trade Plan/target room
→ risk/session/news permission
→ execution freshness/gate
→ broker lifecycle/reconciliation
```

Do not weaken strategy thresholds when the actual blocker belongs to data, risk or execution.

## Documentation rule after every large phase

After each phase:
1. update the authoritative topic docs only where implementation choices/evidence matter;
2. update `60-engineering/MODULE_STRUCTURE.md` with real files/dependencies;
3. update this guide with real call paths/tests;
4. update operator docs only for functionality that actually exists;
5. record verification honestly — deterministic CI green is not the same as live MT5/DEMO certification.
