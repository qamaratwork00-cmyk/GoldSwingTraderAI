# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 1.0-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — implemented through Phase 8

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
│   ├── engine.py
│   ├── state.py
│   └── permissions.py
├── persistence/
│   ├── store.py
│   └── runtime_state.py
├── execution/
│   ├── models.py
│   ├── intent_store.py
│   ├── gate.py
│   ├── checks.py
│   ├── controller.py
│   ├── mt5_writer.py
│   ├── service.py
│   └── reconcile.py
└── management/
    ├── models.py
    ├── manager.py
    ├── store.py
    └── execution.py
```

Planned packages are created only when their phase starts:

```text
operator/       Phase 9
research/       Phase 10
```

## Dependency direction

```text
config/domain
→ market_data → MarketSnapshot
→ intelligence → IntelligenceSnapshot
→ strategies → StrategyFloorReport
→ decisions/fusion → DecisionBoard
→ decisions/opportunity + timing → DecisionSnapshot
→ decisions/trade_plan → TradePlan
→ risk engine/state + hard session/news permissions
→ persistence for critical local state
→ execution gate / intent / broker write / reconciliation
→ management for verified bot-owned open trades
→ operator/dashboard next
```

The execution package is the only code allowed to contain irreversible raw MT5 writes.

## Responsibility ownership

### `market_data/`
Read-only MetaTrader5 boundary plus normalized completed-candle/account/symbol/quote snapshots.

### `intelligence/`
Shared causal market facts: EMA/RSI/ATR, structure, technical zones/location, liquidity/SMC, session and normalized news facts. No broker authority.

### `strategies/`
Six direct parallel strategy-family evaluators. No sequential fallback pipeline and no hard safety ownership.

### `decisions/`
BUY/SELL thesis fusion, Opportunity lifecycle, M5 timing and structural Trade Plan. Trade Plan owns structural invalidation/SL/objectives and immutable original-R price distance before monetary sizing.

### `risk/`
`engine.py` owns monetary sizing/actual minimum-lot affordability/profile limits/capacity. `state.py` owns daily-loss/cooldown/episode transitions. `permissions.py` owns hard PRE_CLOSE/reopen/news entry permission.

SMALL covers any positive day-start equity below `$300`; no arbitrary `$100` eligibility floor exists.

### `persistence/`
Standard-library SQLite only for current V1 foundation. Canonical JSON, checksums, schema versions, transactional writes and event rows. Critical corruption does not silently become blank state.

### `execution/`
Single irreversible broker-write authority.

```text
ExecutionPermission Gate
→ durable ExecutionIntent
→ order_check/pre-submit validation
→ fresh controller/fencing check
→ persist SUBMITTING
→ one order_send only
→ classify ACK
→ broker reconciliation
```

Ownership details:
- `models.py` — action/lifecycle/permission contracts;
- `intent_store.py` — durable intent identity/history and lifecycle clearance;
- `gate.py` — all hard authorities composed as PASS/BLOCK/UNKNOWN;
- `checks.py` — fresh spread/drift/quote execution checks;
- `controller.py` — lease/fencing contract and deterministic test backend;
- `mt5_writer.py` — **only raw MT5 irreversible write adapter**;
- `service.py` — persist-before-send one-shot orchestration;
- `reconcile.py` — broker positions/orders/deals reconciliation.

Known boundary: the current in-memory coordination backend is test infrastructure only. A production shared cross-laptop backend satisfying atomic lease + authoritative expiry + fencing is still required before failover certification.

### `management/`
Second decision floor for verified bot-owned open trades.

- `models.py` — durable ManagedTrade/original-R/objective state and management result contracts;
- `manager.py` — pure continuation/reversal scoring plus HOLD/PROTECT/TRAIL/RUNNER/EXIT selection;
- `store.py` — restart-safe managed-trade persistence;
- `execution.py` — maps management actions to governed MODIFY/CLOSE ExecutionIntents and updates local state only after broker verification.

Management does **not** call raw MT5 directly. Primary target remains a checkpoint. Structural protection/trailing requires a valid protected swing; profit alone cannot create a runner or breakeven move. PRE_CLOSE can force EXIT through the governed execution path.

## Runtime efficiency rule

```text
one broker snapshot
→ one shared intelligence derivation
→ parallel strategy consumers
→ one decision/timing derivation
→ one structural Trade Plan
→ one RiskEvaluation + hard permission set
→ one centralized execution path when needed
→ one post-entry management decision per fresh management cycle
```

No subsystem should reread MT5 or recompute indicators merely to reproduce an already verified shared fact. Fresh broker checks immediately before irreversible writes are intentional safety exceptions.

## Prohibited dependency directions

```text
intelligence → order_send                  NO
strategies   → order_send/risk reset       NO
decisions    → raw order_send              NO
risk         → raw order_send              NO
persistence  → trading decision            NO
management   → raw order_send              NO
operator/UI  → raw order_send              NO
research     → production broker write     NO
```

`management/execution.py` may create governed `ExecutionIntent` values and consume verified execution outcomes; only `execution/mt5_writer.py` owns the raw terminal call.

## Current deterministic tests

Major suites now include:

```text
tests/test_session_news_permissions.py
tests/test_persistence_recovery.py
tests/test_execution_safety.py
tests/test_trade_manager.py
tests/test_management_execution.py
```

Together with earlier phase suites they protect:
- no-lookahead market intelligence;
- non-restrictive parallel strategy logic;
- structural Trade Plan/RR rules;
- positive SMALL balances below `$100` remaining eligible for risk evaluation;
- daily-loss/cooldown/episode state;
- session/news hard permissions;
- durable critical state;
- one-shot execution and ambiguity reconciliation;
- stale fencing rejection;
- Primary target not auto-exiting;
- structure-earned protection/trailing;
- runner needing continuation + real objective;
- no local stop/TP/close mutation before broker verification.

CI gates remain Ruff, Pytest and financial-secret scan. Current Phase-8 deterministic checkpoint passes all three; this is not live DEMO certification or profitability proof.

## Next package — `operator/`

Phase 9 owns compact dashboard/operator presentation. It may consume authoritative runtime states but must not recreate strategy/risk/execution decisions or gain raw broker-write access.

## Phase completion rule

At each large phase exit, record the actual files/dependencies/tests here and in `docs/CODER_GUIDE.md`. Behavioural thresholds remain owned by their authoritative topic documents.
