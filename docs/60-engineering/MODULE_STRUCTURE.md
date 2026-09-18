# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 0.7-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — implemented through Phase 5

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
└── risk/
    ├── __init__.py
    ├── engine.py
    └── state.py
```

Planned packages are created only when their real phase starts:

```text
persistence/    Phase 6
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
→ risk/engine.py + risk/state.py → RiskEvaluation / durable-state contracts
→ Phase 6 hard session/news permission + persistence
```

No current intelligence/strategy/decision/risk module can send an MT5 order.

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

Owns Opportunity/Episode identity and lifecycle transitions. A surviving thesis preserves IDs. MISSED re-arm requires fresh structural/timing evidence. Phase 6 will persist this state.

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

It remains read-only and does not absorb risk or execution algorithms.

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

It deliberately separates a small/noisy Immediate Obstacle from a meaningful Primary target so a minor internal level does not automatically suppress an otherwise valid large-move setup.

A broker stop constraint that materially changes the structural thesis makes the plan invalid; this module never shifts the stop merely to make an account or broker constraint fit.

INVALID plans keep unavailable geometry as `None`; they do not fabricate fake SL/R numbers.

Current buffer/quality/target-significance thresholds are explicit research-calibratable baselines. Frozen structural RR policy remains owned by `20-trading-decisions/TRADE_PLAN.md`.

### `risk/state.py`

Pure state transitions for later persistence:

- UTC risk-day reference and cash-flow-adjusted Account Safety P/L;
- active-cycle loss percentage/budget;
- governed one-reset-per-day semantics;
- consecutive-loss state;
- minimum 30-minute three-loss cooldown with fresh-M15/fresh-opportunity release requirements;
- Market Episode initial entry + at most one genuinely fresh re-entry;
- second same-episode loss lock.

A winning close resets the consecutive-loss counter but cannot erase a cooldown that was already triggered and whose release conditions have not passed.

### `risk/engine.py`

Owns Phase-5 monetary evaluation:

- frozen SMALL/MEDIUM/NORMAL profile bands/ceilings/daily locks;
- profile fixed from UTC risk-day start equity;
- target-size baseline from normal-band midpoint;
- broker min/max/step volume normalization;
- practical minimum-lot evaluation;
- structural risk plus explicit slippage/commission reserve exactly once;
- spread diagnostic without double-counting Bid/Ask geometry;
- daily loss lock/cooldown/episode/capacity/external-exposure checks;
- optional exact broker-required margin authority.

A generic `price × contract / leverage` margin figure is diagnostic only because Gold/CFD broker margin modes vary. An exact broker margin fact, when supplied, is authoritative. Phase 7 must obtain/revalidate that fact before irreversible execution.

Risk never changes Trade Plan SL and never increases risk because a strategy/plan score is high.

## Runtime efficiency rule

```text
one broker snapshot
→ one shared intelligence derivation
→ parallel strategy family consumers
→ one fusion/lifecycle/timing derivation
→ one structural Trade Plan
→ one monetary RiskEvaluation
```

Do not re-read MT5 or recalculate indicators/structure in strategy/plan/risk code. Fresh execution-time quote/spec/account/margin/controller checks are deliberate later exceptions where safety requires current broker truth.

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
tests/test_trade_plan_risk.py
tests/test_risk_state_regressions.py
tests/test_margin_authority.py
```

Phase-5 suites protect:
- BUY/SELL structural stop/target parity;
- Immediate-versus-Primary target distinction;
- frozen RR guard;
- no SL distortion;
- raw size below `0.01` not automatically blocked;
- elevated minimum-lot acceptance within frozen band;
- hard-ceiling rejection;
- no score-leveraged monetary risk;
- no spread double-count;
- cash-flow-adjusted daily lock/manual reset;
- cooldown/episode re-entry semantics;
- heuristic margin not becoming a false hard block;
- exact broker margin remaining authoritative.

CI gates remain Ruff, Pytest and financial-secret scan. The current Phase-5 checkpoint passed all three. This is deterministic software evidence, not live DEMO certification.

## Phase 6 planned ownership

### Hard session/news authority

A narrow owner should consume existing Session/News facts plus verified broker schedule data and produce hard new-entry state such as:

```text
CLEAR
NEWS_BLACKOUT
NEWS_SAFETY_UNKNOWN
PRE_CLOSE
REOPEN_WARMUP
```

It must not duplicate the soft market-intelligence desks.

### `persistence/`

Use the smallest safe durable stack. Standard-library SQLite is preferred unless a concrete requirement proves otherwise.

It must persist and recover at least:
- risk-day/reset/cooldown/episode state;
- Opportunity identity/lifecycle;
- Trade Plan/original-R/objective context;
- unresolved execution/reconciliation lifecycle contracts;
- schema/version/integrity metadata.

Broker truth will later reconcile positions/orders/deals; corrupt critical state must never silently become an empty safe state.

## Prohibited dependencies

```text
intelligence → order_send                   NO
strategies   → MT5/order_send/risk reset    NO
decisions    → MT5/order_send               NO
risk         → order_send                   NO
news facts   → self-owned hard blackout     NO
research/UI  → raw broker write              NO (future)
```

## Phase completion rule

At the end of each large phase, replace planned names with files actually created, record real dependency paths/tests, and keep behavioural/value authority in topic docs rather than copying competing versions here.
