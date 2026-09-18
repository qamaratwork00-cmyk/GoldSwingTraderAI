# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 1.1-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — implemented through Phase 9

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
├── management/
│   ├── models.py
│   ├── manager.py
│   ├── store.py
│   └── execution.py
└── operator/
    └── dashboard.py
```

Planned package:

```text
research/       Phase 10
```

## Dependency direction

```text
config/domain
→ market_data → MarketSnapshot
→ intelligence → IntelligenceSnapshot
→ strategies → StrategyFloorReport
→ decisions → DecisionSnapshot / TradePlan
→ risk → monetary + hard session/news authority
→ persistence → durable critical state
→ execution → gate / intent / broker write / reconciliation
→ management → open-trade decision floor
→ operator → read-only presentation
→ research next → offline/replay evidence only
```

The execution package is the only package allowed to contain irreversible raw MT5 writes.

## Ownership highlights

### `market_data/`
Read-only broker/account/symbol/quote/completed-candle boundary.

### `intelligence/`
Shared causal structure/quant/technical/liquidity/session/news facts. No broker authority.

### `strategies/` + `decisions/`
Parallel strategy families, BUY/SELL fusion, Opportunity/Entry Timing, structural Trade Plan. Soft evidence remains separate from hard safety.

### `risk/`
Monetary sizing/profile/min-lot/capacity plus daily/cooldown/episode state and hard session/news permission. SMALL includes any positive day-start equity below `$300`.

### `persistence/`
Standard-library SQLite with canonical JSON, checksums, schema versions, transactions and event rows. Corrupt critical state never silently becomes empty/default.

### `execution/`
Single raw irreversible broker-write authority.

```text
hard authorities
→ ExecutionPermission
→ durable ExecutionIntent
→ order_check
→ fresh lease/fencing
→ persist SUBMITTING
→ one order_send only
→ broker reconciliation
```

A success-like ACK still requires broker-truth verification. The in-memory coordination backend is tests only; production cross-laptop shared coordination remains required before failover certification.

### `management/`
Second decision floor for verified bot-owned open trades. HOLD/PROTECT/TRAIL/RUNNER/EXIT. Structural protection/trailing, immutable original R, Primary checkpoint, earned runner, PRE_CLOSE override. Management produces governed ExecutionIntents but cannot call raw MT5.

### `operator/`
`dashboard.py` is a pure read-only stdlib renderer over flattened authoritative facts. It preserves requested market/decision/risk/execution/open-trade visibility plus Learning/Backup/Health placeholders. It contains no MetaTrader5, Risk Engine or Execution Gate invocation.

## Runtime efficiency rule

```text
one verified broker snapshot
→ one shared intelligence derivation
→ parallel strategies
→ one decision/timing derivation
→ one TradePlan
→ one RiskEvaluation + hard permission set
→ one centralized execution path if needed
→ one Trade Manager cycle for open trade
→ one presentation frame
```

Do not reread MT5 or recompute already-verified facts except fresh pre-write checks that are deliberately required for safety.

## Prohibited dependency directions

```text
intelligence → order_send                  NO
strategies   → order_send/risk reset       NO
decisions    → raw order_send              NO
risk         → raw order_send              NO
persistence  → trading decision            NO
management   → raw order_send              NO
operator     → MT5/risk/gate authority     NO
research     → production broker write     NO
```

## Current deterministic tests

Later-phase suites:

```text
tests/test_session_news_permissions.py
tests/test_persistence_recovery.py
tests/test_execution_safety.py
tests/test_trade_manager.py
tests/test_management_execution.py
tests/test_dashboard.py
```

Together with earlier suites they protect no-lookahead, non-restrictive strategy fusion, structural RR/risk, no minimum-balance floor, hard session/news state, restart integrity, one-shot execution, reconciliation, structural trade management and read-only dashboard rendering.

CI gates remain Ruff, Pytest and financial-secret scan. Phase-9 deterministic checkpoint passes all three; this is not live DEMO certification or profitability proof.

## Next package — `research/`

Phase 10 should own replay, trade/opportunity outcome measurement, Entry/Exit Learning, large-move recall and bounded declarative strategy experiments.

It must remain downstream/offline from broker-write authority. Research may consume production decisions/events but cannot directly change hard risk/execution policy or send orders.

## Phase completion rule

At each phase exit, record actual files/dependencies/tests here and in `docs/CODER_GUIDE.md`. Behavioural thresholds remain owned by authoritative topic documents.
