# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 0.6-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — implemented through Phase 4

```text
src/goldswingtraderai/
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
├── intelligence/
│   ├── indicators.py
│   ├── candle_structure.py
│   ├── technical.py
│   ├── liquidity.py
│   ├── session.py
│   ├── news.py
│   └── snapshot.py
├── strategies/
│   └── floor.py
└── decisions/
    ├── fusion.py
    ├── opportunity.py
    ├── timing.py
    └── snapshot.py
```

Planned packages are created only when their real phase starts:

```text
risk/           Phase 5
persistence/    Phase 6
execution/      Phase 7
management/     Phase 8
operator/       Phase 9
research/       Phase 10
```

`decisions/` will gain Trade Plan ownership in Phase 5.

## Dependency direction now

```text
config/domain
→ market_data/mt5_reader.py
→ market_data/snapshot.py → MarketSnapshot
→ intelligence/snapshot.py → IntelligenceSnapshot
→ strategies/floor.py → StrategyFloorReport
→ decisions/fusion.py → DecisionBoard
→ decisions/opportunity.py
→ decisions/timing.py
→ decisions/snapshot.py → DecisionSnapshot
→ Phase 5 Trade Plan / Risk
```

No current strategy/decision/intelligence module calls MT5 or owns broker-write permission.

## Existing ownership

### `market_data/`

`mt5_reader.py` is the read-only MetaTrader5 boundary. `snapshot.py` converts broker facts into normalized `MarketSnapshot` with completed H4/H1/M15/M5 chronology and explicit data quality.

### `intelligence/`

`indicators.py` owns chronological EMA/RSI/ATR and quant states. `candle_structure.py` owns causal swings/structure/break hierarchy. `technical.py` owns adaptive zones/location/target room. `liquidity.py` owns pools/sweeps/FVG/qualified OB/path. `session.py` owns soft timezone-safe session context. `news.py` normalizes supplied scheduled-event facts. `intelligence/snapshot.py` computes/reuses these once per market snapshot.

### `strategies/floor.py`

Owns six direct family evaluators. Every family consumes the same `IntelligenceSnapshot` and publishes BUY + SELL `DirectionalFamilyCase`. There is no inheritance/factory framework and no sequential “try next strategy if previous fails” chain.

### `decisions/fusion.py`

Owns independent BUY/SELL thesis fusion, bounded top-family synergy, conflict, evidence coverage/confidence and Red-Team analytical objections. Hard safety/risk are excluded.

### `decisions/opportunity.py`

Owns in-memory Opportunity/Episode identity and allowed lifecycle transitions. A surviving thesis preserves IDs. MISSED re-arm requires a fresh structural/timing event assertion. Phase 6 will add durable persistence.

### `decisions/timing.py`

Owns M5 analytical timing: `ENTER_BUY/ENTER_SELL/WAIT/MISSED/INVALID`. Strong opportunity with severe current extension becomes WAIT rather than thesis deletion. It does not own hard `BLOCKED`.

### `decisions/snapshot.py`

Thin Phase-4 orchestration owner:

```text
IntelligenceSnapshot
→ StrategyFloor
→ Fusion
→ Opportunity
→ Timing
→ DecisionSnapshot
```

It must stay read-only and must not absorb Trade Plan, risk or execution algorithms.

## Phase 5 planned ownership

### `decisions/trade_plan.py`

Should own structural entry reference, invalidation/SL, target hierarchy, immutable original R and plan geometry. It consumes an analytically ready `DecisionSnapshot` plus existing market/intelligence facts; it must not size monetary risk.

### `risk/`

Should own account profile, all-in monetary risk, lot sizing, min-lot affordability, margin facts, daily Account Safety P/L and frozen risk bands/ceilings. It consumes Trade Plan + broker/account specs but never calls `order_send`.

## Runtime efficiency rule

```text
one broker snapshot
→ one shared intelligence derivation
→ parallel strategy family consumers
→ one fusion/lifecycle/timing derivation
→ later plan/risk consumers
```

Do not re-read MT5 or recalculate indicators/structure independently inside strategy or risk code. Fresh execution-time revalidation is a deliberate later exception.

## Current tests

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

`test_strategy_decisions.py` protects six-family parallel evaluation, BUY/SELL conflict visibility, Opportunity identity, WAIT/MISSED/re-arm semantics, coherent DecisionSnapshot and absence of raw broker-write access.

CI gates remain Ruff, Pytest and financial-secret scan. The Phase-4 code/test checkpoint passed all three; live MT5/DEMO certification is a later separate gate.

## Prohibited dependencies

```text
intelligence → order_send                   NO
strategies   → MT5/order_send/risk reset    NO
decisions    → MT5/order_send               NO
news facts   → self-owned hard blackout     NO
risk         → order_send                    NO (future)
research/UI  → raw broker write              NO (future)
```

## Phase completion rule

After each large phase, replace planned names with the files actually created, record the real dependency path/tests, and keep behavioural/value authority in the topic docs rather than duplicating competing rules here.
