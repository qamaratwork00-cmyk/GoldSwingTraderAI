# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 0.5-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Purpose

This is the file-oriented map of the actual and planned package. Behaviour remains owned by the topic documents under `00-foundation/`, `10-market-intelligence/`, `20-trading-decisions/`, `30-risk-execution/` and `40-research-learning/`.

Core engineering rule:

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — implemented through Phase 3

```text
src/goldswingtraderai/
├── __init__.py
├── __main__.py
├── app/
│   └── main.py
├── config/
│   └── settings.py
├── diagnostics/
│   ├── logging.py
│   └── reasons.py
├── domain/
│   ├── enums.py
│   ├── ids.py
│   ├── market.py
│   └── models.py
├── market_data/
│   ├── mt5_reader.py
│   └── snapshot.py
└── intelligence/
    ├── indicators.py
    ├── candle_structure.py
    ├── technical.py
    ├── liquidity.py
    ├── session.py
    ├── news.py
    └── snapshot.py
```

Planned packages are created only when their real phase begins:

```text
strategies/     Phase 4
decisions/      Phase 4–5
risk/           Phase 5
persistence/    Phase 6
execution/      Phase 7
management/     Phase 8
operator/       Phase 9
research/       Phase 10
```

Do not create empty architecture merely to mirror this plan.

## Dependency direction now

```text
config/domain
    ↓
market_data/mt5_reader.py
    ↓
market_data/snapshot.py → MarketSnapshot
    ↓
intelligence/snapshot.py
    ├─ indicators.py
    ├─ candle_structure.py
    ├─ technical.py
    ├─ liquidity.py
    ├─ session.py
    └─ news.py (optional normalized external facts)
    ↓
IntelligenceSnapshot
    ↓
Phase 4 strategies/decisions
```

No intelligence module calls MT5 or owns broker-write permission.

## `app/`

Current owner: startup/readiness orchestration only.

`app/main.py` currently performs configuration load, MT5 read-only readiness, DEMO verification, optional account/server pinning and snapshot logging. It does not contain strategy, risk or order-send logic.

As later phases arrive, keep the coordinator thin; it should call owners rather than absorb their algorithms.

## `config/`

`config/settings.py` owns non-secret runtime settings.

Current important rule: V1 positive DEMO requirement is not exposed as a disableable configuration switch.

Credentials/tokens/private keys with financial authority stay outside tracked configuration.

## `domain/`

Domain objects are pure contracts with no MT5/network/database calls.

Current ownership:

- `enums.py` — stable states/vocabulary;
- `ids.py` — durable typed entity IDs;
- `models.py` — cross-subsystem contracts such as permission/demo/intent/controller structures;
- `market.py` — normalized account, symbol, quote, candle, series and MarketSnapshot types.

New domain types should be added only where they protect semantics across subsystem boundaries.

## `market_data/`

### `mt5_reader.py`

Read-only MetaTrader5 boundary for:
- terminal initialize/shutdown;
- account facts and account mode;
- positive DEMO verification;
- XAUUSDm/XAUUSD resolution;
- symbol specifications;
- Bid/Ask;
- completed candle retrieval.

Raw MT5 structures should not leak beyond this boundary.

### `snapshot.py`

Builds one normalized `MarketSnapshot` with H4/H1/M15/M5 completed candles and explicit data-quality state.

Forming candles are not structural history. Stale/insufficient/corrupt data remains explicit rather than silently repaired into healthy truth.

## `intelligence/`

All current intelligence functions operate on normalized completed-candle/MarketSnapshot facts and have zero broker authority.

### `indicators.py`

Owns lightweight chronological:
- EMA20/EMA50 baseline;
- RSI14 baseline;
- ATR14 baseline;
- volatility ratio/state;
- momentum phase;
- extension state.

`IndicatorSeries` is computed once per timeframe by the unified intelligence pipeline and reused.

### `candle_structure.py`

Owns:
- candle anatomy/sequence state;
- causal confirmed swings;
- distinct `pivot_time` and `confirmed_at`;
- protected swings;
- per-timeframe structure state;
- PROBE / QUALIFIED_BREAK / CONFIRMED_BOS / MSS_CANDIDATE / CONFIRMED_MSS / FAILED_BREAK events.

It accepts precomputed ATR so normal runtime does not duplicate the Quant desk calculation. Standalone/replay calls may still compute ATR internally.

### `technical.py`

Consumes Structure + Quant. Owns adaptive support/resistance zones, location category, target-room and structural conflict facts. It does not redefine BOS/MSS.

### `liquidity.py`

Consumes candles + Structure + Quant. Owns clustered liquidity pools, pool lifecycle/event interpretation, sweep versus accepted break, FVG, qualified OB and path evidence. Correlated facts remain bounded rather than automatically multiplied into certainty.

### `session.py`

Owns soft Asia/London/New York/overlap context using standard-library `zoneinfo`. London and New York classification is DST-aware. It does not own broker OPEN/CLOSED/PRE_CLOSE permission.

Current baseline local windows are implementation/research parameters, not hard execution safety.

### `news.py`

Provider-neutral scheduled-event fact normalization:
- provider health/freshness;
- TIER 1 / TIER 2 / TIER 3 baseline mapping;
- factual pre/post windows;
- linked/overlapping event-window merging;
- explicit unavailable/stale truth.

It does not output `NEWS_BLACKOUT` permission; that belongs to the later hard state machine.

Production provider credentials/mapping remain future configuration work.

### `snapshot.py`

Primary Phase-3 orchestration owner.

```text
MarketSnapshot
→ IndicatorSeries once per timeframe
→ QuantReport
→ StructureReport using shared ATR
→ TechnicalReport
→ LiquidityReport
→ SessionReport from M5
→ optional NewsFacts
→ IntelligenceSnapshot
```

Later strategy code should consume this snapshot rather than independently recomputing market facts.

## Future `strategies/` — Phase 4

Own the six strategy-family desks from `20-trading-decisions/STRATEGY_FLOOR.md`. Each should consume audited intelligence and emit bounded BUY/SELL family evidence. No MT5 reads/writes and no monetary sizing.

## Future `decisions/` — Phase 4–5

Own BUY thesis, SELL thesis, Red Team/conflict, evidence coverage, Opportunity lifecycle, Entry Timing and later structural Trade Plan.

## Future `risk/`, `persistence/`, `execution/`

These remain intentionally absent until their phases. Their exact behaviour is already documented in `30-risk-execution/`; implementation must not be pre-empted by scattered helper logic in current modules.

All irreversible create/modify/close calls must eventually exist behind one governed execution path only.

## Runtime efficiency rule

Normal direction is:

```text
one broker read snapshot
→ one shared intelligence derivation
→ many read-only consumers
```

Do not re-read MT5 or recalculate EMA/RSI/ATR/structure independently inside each strategy.

Fresh execution-time revalidation is a deliberate later exception where safety requires current quote/account/controller facts.

## Current test map

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

Current deterministic CI gates:

```text
ruff
pytest
financial-secret scanner
```

The latest Phase-3 unified intelligence batch passed all three gates. This does not substitute for future live MT5/DEMO certification.

## Prohibited dependencies

```text
intelligence → raw MT5 order_send       NO
strategy     → raw MT5 order_send       NO
research     → raw MT5 order_send       NO
dashboard    → raw MT5 order_send       NO
market_data  → strategy decision        NO
news facts   → self-owned hard blackout NO
```

## Phase completion update rule

At the end of each large phase, update this file to show actual created modules and dependency paths; remove speculative names that were not used. Keep behaviour/value authority in the topic docs rather than copying competing versions here.
