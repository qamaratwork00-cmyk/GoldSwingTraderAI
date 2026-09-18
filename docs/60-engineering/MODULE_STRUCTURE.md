# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 2.7-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — Phase 10 + Phase 11 recovery foundation

```text
src/goldswingtraderai/
├── app/
│   ├── main.py
│   ├── recovery.py
│   └── recovery_mt5.py
├── config/
├── diagnostics/
├── domain/
│   └── market.py
├── market_data/
│   ├── mt5_reader.py
│   └── snapshot.py
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
└── research/
```

## Dependency direction

```text
domain/config
→ market_data
→ intelligence
→ strategies
→ decisions
→ risk/persistence
→ execution
→ management
→ operator

MT5Reader
→ normalized Account/Symbol/Quote/Candles/OpenPosition facts
→ app/recovery_mt5
→ app/recovery

StateStore → checkpoint → backup → restored StateStore → app/recovery
CoordinationStore → ControllerLeaseManager → recovery takeover gate → execution
```

The execution package remains the only raw irreversible MT5-write owner.

## Ownership

### `domain/market.py`
Shared normalized broker/market DTOs. `OpenPositionFacts` is read-only current exposure truth and does not confer bot ownership.

### `market_data/mt5_reader.py`
Single narrow runtime MetaTrader5 read boundary for account facts, symbol resolution/specification, quote, completed candles and current open positions.

`open_positions(symbol)` rules:

- empty broker collection = verified empty current exposure;
- `None`/missing getter = `DATA_UNAVAILABLE`, not zero exposure;
- invalid direction/symbol/geometry/duplicate ticket = `DATA_CORRUPT`;
- MT5 zero SL/TP = explicit `None`;
- deterministic ticket ordering.

No `order_send` belongs here.

### `app/recovery_mt5.py`
Read-only adapter that composes existing `MT5Reader` facts into `MT5RecoveryTruth`:

```text
BrokerRecoverySnapshot
+ verified SymbolSpec
+ price_tolerance = tick_size
```

It never imports/calls raw MetaTrader5 directly and cannot create a second broker read authority.

### `app/recovery.py`
Startup recovery sequencing owner: persistence integrity, Intent/ManagedTrade recovery, hard authorities and controller takeover completion. No raw broker writes.

### `persistence/`
Local durable state, portable checkpoint and verified local rolling-backup/catalog.

### `execution/`
Central permission, one-shot intents, controller/fencing, raw broker-write boundary and reconciliation.

### `management/`
Trade Manager decisions + managed-trade persistence. No raw MT5 writes.

### `research/`
Chronological replay/evidence/learning/discovery. No production broker writes.

## Prohibited dependency directions

```text
market_data        → raw broker write                   NO
recovery_mt5       → raw MetaTrader5 import/client      NO
recovery_mt5       → broker write                       NO
app/recovery       → broker write                       NO
unknown positions  → empty exposure                     NO
broker position    → automatic bot ownership            NO
hard-coded XAU tick→ recovery tolerance                 NO
checkpoint restore → broker truth / write authority     NO
new fencing epoch  → immediate write authority          NO
backup.py          → embedded publication credentials   NO
research/operator  → production broker write            NO
```

## Current deterministic tests

Important later suites:

```text
tests/test_market_data.py
tests/test_recovery_mt5.py
tests/test_startup_recovery.py
tests/test_persistence_recovery.py
tests/test_runtime_checkpoint.py
tests/test_backup_catalog.py
tests/test_execution_safety.py
tests/test_sqlite_coordination.py
tests/test_research_*.py
```

Current verified checkpoint: **226 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Remaining Phase-11 work

- final startup service composing MT5 initialization/recovery truth with persisted recovery;
- authoritative runtime construction of RecoveryAuthorities;
- operator-visible recovery/controller status;
- real fresh-machine broker reconciliation drill;
- controlled cross-laptop failover proof;
- authenticated external backup publication.

## External release work

- real Windows MT5 read/write evidence;
- trustworthy historical session coverage;
- broad real-XAU validation/holdout/DEMO forward evidence;
- final runtime/dashboard/release integration.

## Phase completion rule

Every coherent code checkpoint updates authoritative topic docs, this map, `docs/CODER_GUIDE.md`, testing contract and open-question ledger before moving on.
