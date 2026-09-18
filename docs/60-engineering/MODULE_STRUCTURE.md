# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 0.8-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — implemented through Phase 6

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
├── decisions/
│   ├── fusion.py
│   ├── opportunity.py
│   ├── timing.py
│   ├── snapshot.py
│   └── trade_plan.py
├── risk/
│   ├── __init__.py
│   ├── engine.py
│   ├── state.py
│   └── permissions.py
└── persistence/
    ├── __init__.py
    ├── store.py
    └── runtime_state.py
```

Planned packages are created only when their real phase starts:

```text
execution/      Phase 7
management/     Phase 8
operator/       Phase 9
research/       Phase 10
```

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
→ decisions/trade_plan.py → TradePlan
→ risk/engine.py + risk/state.py → RiskEvaluation / risk lifecycle
→ risk/permissions.py → hard session/news permission
→ persistence/ → durable critical context
→ Phase 7 centralized execution gate + broker lifecycle
```

No current intelligence/strategy/decision/risk/persistence module can send an MT5 order.

## Existing ownership

### `market_data/`

`mt5_reader.py` is the read-only MetaTrader5 boundary. `snapshot.py` converts broker facts into normalized `MarketSnapshot` with completed H4/H1/M15/M5 chronology and explicit data quality.

### `intelligence/`

`indicators.py` owns chronological EMA/RSI/ATR and quant states. `candle_structure.py` owns causal swings/structure/break hierarchy. `technical.py` owns adaptive zones/location/target room. `liquidity.py` owns pools/sweeps/FVG/qualified OB/path. `session.py` owns soft timezone-safe session context. `news.py` normalizes supplied scheduled-event facts. `intelligence/snapshot.py` computes/reuses these once per market snapshot.

### `strategies/floor.py`

Owns six direct family evaluators. Every family consumes the same `IntelligenceSnapshot` and publishes BUY + SELL evidence. There is no inheritance/factory framework and no sequential “try next strategy if previous fails” chain.

### `decisions/fusion.py`

Owns independent BUY/SELL thesis fusion, bounded top-family synergy, conflict, evidence coverage/confidence and Red-Team analytical objections. Hard safety/risk are excluded.

### `decisions/opportunity.py`

Owns Opportunity/Episode identity and lifecycle transitions. A surviving thesis preserves IDs. MISSED re-arm requires fresh structural/timing evidence. Phase 6 persistence now stores the active Opportunity identity rather than recreating it after restart.

### `decisions/timing.py`

Owns M5 analytical timing: `ENTER_BUY/ENTER_SELL/WAIT/MISSED/INVALID`. Strong opportunity with severe current extension becomes WAIT rather than thesis deletion. It does not own hard `BLOCKED`.

### `decisions/snapshot.py`

Thin read-only orchestration owner:

```text
IntelligenceSnapshot
→ StrategyFloor
→ Fusion
→ Opportunity
→ Timing
→ DecisionSnapshot
```

### `decisions/trade_plan.py`

Owns pre-risk structural geometry only:

- Signal Price and Approved Entry Reference;
- family-aware structural invalidation;
- volatility/noise buffer and broker tick normalization;
- Initial SL and Stop Quality;
- Immediate / Primary / Expansion / Runner objectives;
- frozen RR classification and marginal-expansion exception;
- immutable original-R price distance;
- Plan Quality and READY/DEGRADED/INVALID state.

A low-quality nearby obstacle may remain `Immediate Obstacle` instead of automatically killing meaningful target room. INVALID plans use explicit `None` geometry instead of fake SL/R numbers.

### `risk/state.py`

Pure state transitions for:

- UTC risk-day reference and cash-flow-adjusted Account Safety P/L;
- manual reset semantics;
- consecutive-loss cooldown;
- Market Episode entry/re-entry/loss lock.

### `risk/engine.py`

Owns monetary evaluation:

- SMALL = any positive day-start equity below `$300`; MEDIUM `$300–$999.99`; NORMAL `$1,000+`;
- frozen target/elevated bands, hard ceilings and daily locks;
- broker min/max/step volume normalization;
- practical minimum-lot evaluation;
- structural risk plus slippage/commission reserve exactly once;
- spread diagnostic without double-counting Bid/Ask geometry;
- capacity/external-exposure checks;
- optional exact broker-required margin authority.

A generic margin estimate is diagnostic only. Phase 7 must obtain/revalidate exact broker margin before irreversible execution.

### `risk/permissions.py`

Owns hard market-session/news permission, not soft market scoring.

Inputs/outputs:

```text
BrokerSessionFacts → MarketPermission
NewsFacts + NewsRecoveryFacts → NewsPermission
MarketPermission + NewsPermission → SessionNewsPermission
```

It implements daily/weekend PRE_CLOSE, reopen warmup, holiday caution, news blackout, required-news-truth unknown and post-news warmup. It has no broker-write authority.

### `persistence/store.py`

Small standard-library SQLite state store. It owns:

- canonical JSON records;
- SHA-256 checksums;
- database/record schema versions;
- `WAL` + `synchronous=FULL` durability;
- transactional current-state updates;
- optional append-only event rows;
- integrity verification.

No ORM/service framework is used.

### `persistence/runtime_state.py`

Owns explicit typed adapters for current critical restart state:

- `RiskDayState`;
- `CooldownState`;
- `EpisodeRiskState`;
- active `Opportunity`;
- active `TradePlan`.

`RecoveryBundle` validates Opportunity/Market-Episode/Trade-Plan lineage. Broker order/position truth is not invented here; Phase 7 reconciliation consumes this local context.

## Runtime efficiency rule

```text
one broker snapshot
→ one shared intelligence derivation
→ parallel strategy consumers
→ one decision/timing derivation
→ one structural Trade Plan
→ one monetary RiskEvaluation
→ one session/news permission result
→ later one centralized execution gate
```

Do not re-read MT5 or recalculate indicators/structure in strategy/plan/risk code. Fresh execution-time quote/spec/account/margin/controller checks are deliberate Phase-7 exceptions where safety requires current broker truth.

## Current tests

Phase-6 additions:

```text
tests/test_session_news_permissions.py
tests/test_persistence_recovery.py
```

They add coverage for:

- daily `T-20/T-10` and weekend `T-60/T-30` PRE_CLOSE rules;
- one/two clean-M5 reopen requirements;
- holiday caution not becoming a fake closure;
- required session/news truth fail-safe behaviour;
- Tier-1/Tier-2 blackout and post-news severe-dislocation recovery;
- SQLite round-trip and event journal;
- checksum corruption rejection;
- restart-safe risk/cooldown/episode/opportunity/TradePlan state;
- lineage mismatch rejection;
- active-plan cleanup without erasing risk history.

Earlier phase suites continue protecting no-lookahead, six-family parallel logic, Trade Plan/RR rules, practical minimum-lot risk, positive SMALL balances below `$100`, daily lock/cooldown and exact broker-margin authority.

CI gates remain Ruff, Pytest and financial-secret scan. Current Phase-6 deterministic checkpoint passes all three; this is not live DEMO certification.

## Phase 7 planned ownership

### `execution/`

Phase 7 will add the only irreversible broker-write boundary and must consume, not duplicate, the existing authorities:

```text
positive DEMO guard
+ account identity
+ fresh data/quote/specs
+ RiskEvaluation
+ SessionNewsPermission
+ position ownership/capacity
+ durable Execution Intent/order lifecycle
+ controller lease/fencing ownership
+ exact broker margin/order validation
→ centralized ALLOW / BLOCK / UNKNOWN
→ one governed MT5 write
→ reconciliation
```

Execution must persist intent before send, never blind-retry ambiguous acknowledgement and must not allow strategy/dashboard/research code direct write access.

## Prohibited dependencies

```text
intelligence → order_send                   NO
strategies   → MT5/order_send/risk reset    NO
decisions    → MT5/order_send               NO
risk         → order_send                    NO
persistence  → trading decision/order_send  NO
news facts   → self-owned hard blackout     NO
research/UI  → raw broker write              NO (future)
```

## Phase completion rule

At the end of each large phase, replace planned names with files actually created, record real dependency paths/tests, and keep behavioural/value authority in topic docs rather than copying competing versions here.
