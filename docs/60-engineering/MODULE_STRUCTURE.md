# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 2.6-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — Phase 10 + Phase 11 recovery foundation

```text
src/goldswingtraderai/
├── app/
│   ├── main.py
│   └── recovery.py
├── config/
├── diagnostics/
├── domain/
├── market_data/
├── intelligence/
├── strategies/
├── decisions/
├── risk/
├── persistence/
│   ├── store.py
│   ├── runtime_state.py
│   ├── checkpoint.py
│   └── backup.py
├── execution/
│   ├── controller.py
│   ├── sqlite_coordination.py
│   ├── gate.py
│   ├── intent_store.py
│   ├── mt5_writer.py
│   ├── reconcile.py
│   └── service.py
├── management/
├── operator/
├── security/
│   └── financial_secrets.py
└── research/
```

## Dependency direction

```text
config/domain
→ market_data
→ intelligence
→ strategies
→ decisions
→ risk/persistence
→ execution
→ management
→ operator

StateStore
→ StoreSnapshot
→ checkpoint
→ backup catalog / retention
→ fresh local StateStore
→ app/recovery

broker read truth + persistent recovery context + hard authorities
→ app/recovery
→ controller takeover completion only after reconciliation
→ runtime READY

controller CoordinationStore
→ atomic lease/fencing backend
→ ControllerLeaseManager
→ ExecutionService pre-write verification
```

The execution package remains the only raw irreversible MT5-write owner.

## Ownership

### `market_data/`
Read-only account/symbol/quote/completed-candle authority. Future live recovery position reads must extend/reuse this boundary instead of adding a second MetaTrader5 read client.

### `intelligence/`
Shared causal structure/quant/technical/liquidity/session/news/confluence facts. No broker authority.

### `strategies/` + `decisions/`
Parallel strategy floor, BUY/SELL fusion, Opportunity/Timing and structural Trade Plan.

### `risk/`
Monetary sizing plus hard session/news/risk authority.

### `persistence/store.py`
SQLite durability, canonical record/event integrity, deterministic `StoreSnapshot`, empty-store restore and WAL checkpoint helper.

### `persistence/checkpoint.py`
Public-safe immutable runtime checkpoint packaging and fresh-DB restore.

### `persistence/backup.py`
Local automatic checkpoint cadence, retention and verified catalog. No remote credentials/publication authority.

### `execution/controller.py`
Lease/fencing policy, fresh ownership verification and reconciliation-gated takeover state.

### `execution/sqlite_coordination.py`
Transactional durable coordination implementation with monotonic epoch ledger. Real cross-laptop suitability remains deployment-evidence dependent.

### `app/recovery.py`
Primary owner of startup recovery sequencing. It composes existing persistence/execution/management contracts instead of recreating them.

Responsibilities:

- full `StateStore` integrity before recovery;
- typed runtime bundle load;
- current `ExecutionIntent` recovery through existing `MT5Reconciler`;
- current `ManagedTrade` versus normalized broker position comparison;
- DEMO/account/server/symbol consistency;
- hard `RecoveryAuthorities` aggregation;
- controller takeover completion only at the final successful recovery boundary;
- explicit READY / RECONCILING / BLOCKED output.

It has **no `order_send` authority** and cannot treat restored state as broker truth.

### other `execution/`
Central gate, durable Intent, raw MT5 writer and broker reconciliation. `ExecutionService` freshly verifies controller ID + fencing epoch immediately before send.

### `management/`
Trade Manager decisions and typed managed-trade persistence. No raw broker writes.

### `operator/`
Read-only presentation.

### `research/`
Chronological replay, historical session facts, stress/walk-forward, portable data/evidence and governed learning/discovery/promotion.

## Prohibited dependency directions

```text
intelligence       → order_send                         NO
strategies         → order_send/risk reset              NO
decisions          → raw order_send                     NO
management         → raw order_send                     NO
operator           → trading authority                  NO
research           → production broker write            NO
recovery           → raw broker write                   NO
recovery           → blind resend uncertain Intent      NO
recovery           → invent missing ManagedTrade        NO
recovery           → clear takeover before checks PASS  NO
checkpoint restore → broker-write authority             NO
checkpoint restore → overwrite/merge live DB            NO
backup.py          → embedded GitHub/cloud token        NO
new fencing epoch  → immediate write authority          NO
security scanner   → trading policy                     NO
```

## Current deterministic tests

Key later suites:

```text
tests/test_persistence_recovery.py
tests/test_runtime_checkpoint.py
tests/test_backup_catalog.py
tests/test_execution_safety.py
tests/test_sqlite_coordination.py
tests/test_startup_recovery.py
tests/test_management_replay.py
tests/test_research_*.py
tests/test_discovery_*.py
tests/test_promotion_governance.py
```

Current verified checkpoint: **219 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Remaining Phase-11 work

- add live read-only MT5 recovery-position snapshot via existing `MT5Reader` boundary;
- wire live startup authorities into `StartupRecoveryCoordinator`;
- controlled fresh-machine + broker reconciliation drill;
- controlled shared-storage/cross-laptop failover proof;
- authenticated external GitHub publication for verified backup artifacts;
- operator-visible recovery/controller health.

## Remaining external research/release work

- controlled Windows/MT5 real-history evidence;
- trustworthy historical broker-session coverage;
- broad real-XAU validation/holdout/DEMO evidence;
- empirical execution-friction calibration;
- final live runtime/dashboard/release integration.

## Phase completion rule

Every coherent code checkpoint updates the authoritative topic doc, this map, `docs/CODER_GUIDE.md`, testing contract and open-question ledger before moving on.
