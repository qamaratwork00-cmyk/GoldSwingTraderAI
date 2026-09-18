# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 2.4-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — Phase 10 + Phase 11 local backup foundation

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
│   ├── checkpoint.py
│   └── backup.py
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
→ checkpoint
→ backup catalog / retention
→ selected verified checkpoint
→ fresh local StateStore
→ broker reconciliation required

read-only MT5 history/offline source
→ research acquisition/dataset identity
→ replay/session/stress/walk-forward
→ evidence manifest/package
→ learning/discovery/promotion
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
Local SQLite durability, canonical record/event integrity, deterministic `StoreSnapshot`, empty-store restore and WAL checkpoint helper.

### `persistence/checkpoint.py`
Portable public-safe runtime checkpoint packaging and fresh-database restore.

```text
checkpoint_manifest.json
records.jsonl
events.jsonl
```

Write-new only; canonical hashes/counts; strict layout/symlink checks; structured + text financial-secret rejection; fresh DB restore only; broker reconciliation explicitly required.

### `persistence/backup.py`
Primary owner of local automatic checkpoint cadence, count-based retention and verified backup catalog.

Layout:

```text
backup_catalog.json
checkpoints/
  runtime-YYYYMMDDTHHMMSSZ-<sha12>/
```

Responsibilities:

- configurable `BackupPolicy` with initial 15-minute / keep-96 baseline;
- verify existing catalog and every referenced checkpoint before use;
- skip creation when not yet due;
- create checkpoint in hidden staging path;
- immediately verify new checkpoint before publication to local catalog;
- atomically install new checkpoint and catalog;
- prune only after new known-good catalog exists;
- verify `catalog_sha256`, chronology, counts and referenced checkpoint SHA/content;
- return latest checkpoint only after full verification;
- reject checkpoint names that can escape the managed directory;
- preserve previous known-good catalog/checkpoint when a new backup fails.

This module has **no remote authentication/publication responsibility**. GitHub/cloud publication belongs to external authenticated tooling with credentials kept outside repository/checkpoint state.

### `security/financial_secrets.py`
Shared credential detection. Source scanning remains fixture-safe; structured checkpoint payload scanning is stricter. No trading authority.

### `execution/`
Single raw broker-write authority: centralized permission gate, durable intent, writer, reconciliation and controller/fencing semantics.

### `management/`
Verified open-trade HOLD/PROTECT/TRAIL/RUNNER/EXIT decisions. No raw MT5 writes.

### `operator/`
Read-only presentation.

### `research/`
Chronological replay, historical session facts, stress/walk-forward, portable data/evidence and governed learning/discovery/promotion. No production broker-write authority.

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
backup.py          → embedded GitHub/cloud token   NO
backup catalog     → execution authority           NO
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
tests/test_backup_catalog.py
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

Current verified checkpoint: **202 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Remaining Phase-11 work

- authenticated public-safe GitHub publication workflow for already-verified artifacts;
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
