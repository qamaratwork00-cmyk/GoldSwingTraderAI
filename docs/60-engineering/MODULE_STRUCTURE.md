# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 2.3-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — Phase 10 + Phase 11 checkpoint foundation

```text
src/goldswingtraderai/
├── app/
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
│   └── checkpoint.py
├── execution/
├── management/
├── operator/
├── security/
│   └── financial_secrets.py
└── research/
    ├── replay.py
    ├── ablation.py
    ├── outcomes.py
    ├── management_replay.py
    ├── session_history.py
    ├── stress.py
    ├── validation.py
    ├── evidence.py
    ├── datasets.py
    ├── acquisition.py
    ├── packages.py
    ├── metrics.py
    ├── learning.py
    ├── episode_journal.py
    ├── discovery.py
    ├── invention.py
    └── promotion.py
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

security → repository/checkpoint artifact validation only

StateStore
→ StoreSnapshot
→ persistence/checkpoint
→ fresh local StateStore
→ broker reconciliation required

read-only MT5 history or offline source
→ acquisition / portable dataset / dataset identity
→ replay / outcomes / management
→ optional verified historical session schedule
→ PRE_CLOSE-aware management / stress / walk-forward
→ evidence manifest / package
→ learning / discovery / promotion
```

The execution package remains the only raw irreversible MT5-write owner.

## Key ownership

### `market_data/`
Read-only account/symbol/quote/completed-candle authority. Research acquisition reuses `MT5Reader.completed_candles()`.

### `intelligence/`
Shared causal structure/quant/technical/liquidity/session/news/confluence facts. No broker authority.

### `strategies/` + `decisions/`
Parallel strategy floor, BUY/SELL fusion, Opportunity/Timing and structural Trade Plan. Optional Trendline/Fib/POC remains bounded bonus-only.

### `risk/`
Monetary sizing plus hard session/news/risk authority.

### `persistence/store.py`
Primary owner of local SQLite durability and canonical record/event integrity.

New Phase-11 responsibilities:

- `StoreSnapshot` model;
- deterministic export of all current records + ordered append-only events;
- integrity verification of event history, not only current records;
- restore of verified snapshot only into an empty initialized store;
- explicit WAL checkpoint helper for safe fresh-DB handoff.

### `persistence/checkpoint.py`
Primary owner of portable runtime checkpoint packaging and fresh-database restore.

```text
checkpoint_manifest.json
records.jsonl
events.jsonl
```

Rules:

- write-new destination only;
- canonical JSONL records/events;
- source label/version + schema versions + UTC creation time;
- file SHA-256 + `checkpoint_sha256`;
- strict filenames/file-set/symlink checks;
- structured + text financial-secret rejection;
- no raw SQLite database publication as portable state;
- restore only to a non-existing local DB;
- temporary restore + integrity check + WAL checkpoint + atomic move;
- restore result explicitly says broker reconciliation is required.

### `security/financial_secrets.py`
Shared credential detection owner.

Repository scanning uses text semantics suitable for source/tests. Structured checkpoint scanning recursively checks real payload keys/values, so a serialized authority-bearing `password`, token, private/recovery key or client secret cannot pass merely because JSON quoted the key.

No trading authority.

### `execution/`
Single raw broker-write authority: centralized permission gate, durable intent, writer, reconciliation and controller/fencing semantics.

### `management/`
Verified open-trade HOLD/PROTECT/TRAIL/RUNNER/EXIT decisions. No raw MT5 writes.

### `operator/`
Read-only presentation.

### `research/session_history.py`
Explicit historical broker-session facts. Reuses production PRE_CLOSE permission; no guessed session clock.

### Other research modules
`replay.py` chronological decisions; `ablation.py` controlled variants; `outcomes.py` Trade Plan paths; `management_replay.py` production manager; `stress.py` declared friction; `validation.py` fixed-policy walk-forward; `datasets.py` portable replay inputs; `acquisition.py` read-only MT5 history; `evidence.py` content identity; `packages.py` immutable evidence packages; metrics/learning/discovery/invention/promotion own governed improvement lifecycle.

## Prohibited dependency directions

```text
intelligence       → order_send                    NO
strategies         → order_send/risk reset         NO
decisions          → raw order_send                NO
management         → raw order_send                NO
operator           → trading authority             NO
research           → production broker write       NO
acquisition        → duplicate raw MT5 client      NO
session_history    → guessed/default broker clock  NO
checkpoint restore → broker-write authority        NO
checkpoint restore → overwrite/merge live DB       NO
security scanner   → trading policy                NO
invention          → arbitrary Python/eval/exec    NO
candidate          → self-promotion                NO
stress             → production safety mutation    NO
validation         → hidden tuning/final holdout   NO
```

## Current deterministic tests

Later suites include:

```text
tests/test_persistence_recovery.py
tests/test_runtime_checkpoint.py
tests/test_management_replay.py
tests/test_research_ablation.py
tests/test_research_outcomes.py
tests/test_research_stress.py
tests/test_research_validation.py
tests/test_research_evidence.py
tests/test_research_datasets.py
tests/test_research_acquisition.py
tests/test_research_packages.py
tests/test_research_session_history.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Current verified checkpoint: **195 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Remaining Phase-11 work

- automatic checkpoint cadence/retention;
- public-safe publication/catalog workflow;
- controlled fresh-machine restore + real broker reconciliation drill;
- production shared cross-laptop atomic controller backend/failover proof;
- integrated startup recovery orchestration.

## Remaining external research/release work

- controlled Windows/MT5 real-history evidence;
- trustworthy historical broker-session source/coverage;
- broad real-XAU validation/holdout/DEMO evidence;
- empirical execution-friction calibration;
- final runtime/dashboard/release integration.

## Phase completion rule

Every coherent code checkpoint must update the authoritative topic doc, this map, `docs/CODER_GUIDE.md`, testing contract and open-question ledger before moving on.
