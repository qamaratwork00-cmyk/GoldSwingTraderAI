# GoldSwingTraderAI — Persistence, Restart and Recovery

**Status:** PROVISIONAL  
**Version:** 0.2-implementation  
**Authority:** Durable lifecycle state, crash recovery, restart reconciliation, portable strategy/learning state, machine migration and backup/restore integrity.  
**Depends on:** `EXECUTION_AND_BROKER_SAFETY.md`, `RISK_CONTRACT.md`, `../20-trading-decisions/TRADE_PLAN.md`, `../40-research-learning/LEARNING_AND_AI_BOUNDARIES.md`

## Purpose

The bot must survive process restart, laptop loss/change and controlled migration without forgetting active obligations, strategy lineage or learning history.

> **Restart is not a fresh trading day unless the actual risk/session rules say so. Machine replacement is not strategy amnesia.**

## Phase 6 implementation checkpoint

V1 persistence foundation now uses the Python standard-library `sqlite3` module. No ORM/service/database framework is required.

Implemented owners:

```text
src/goldswingtraderai/persistence/store.py
src/goldswingtraderai/persistence/runtime_state.py
src/goldswingtraderai/persistence/__init__.py
```

### `store.py`

Provides a small transactional `StateStore` with:

- SQLite durable records;
- canonical JSON payloads;
- SHA-256 checksums;
- explicit database and record schema versions;
- `PRAGMA quick_check` plus record-checksum integrity verification;
- `WAL` journal mode and `synchronous=FULL`;
- atomic transactional upsert/delete;
- optional append-only event records written in the same transaction as the current state update.

Corrupt JSON/checksum/schema state raises an explicit persistence error. It is never converted into an empty safe-looking runtime state.

### `runtime_state.py`

Provides typed round-trip adapters for the current critical V1 state:

- `RiskDayState`;
- `CooldownState`;
- `EpisodeRiskState`;
- active `Opportunity`;
- active `TradePlan`, including objective/original-R context.

`RuntimeStateRepository` scopes records by managed account/symbol identity supplied by the caller. `load_recovery_bundle()` validates storage integrity and cross-checks Opportunity, Market Episode and Trade Plan lineage before returning restart context.

Current deterministic tests prove process-restart round-trip, checksum-corruption failure, critical lineage recovery, identity-mismatch rejection and clearing active plan/opportunity without erasing durable risk-day history.

Execution Intent/order/trade lifecycle persistence is intentionally added with Phase 7 when those real types exist; it is not represented by speculative placeholder classes in Phase 6. Strategy Registry/learning/research persistence expands in their later implementation phases using the same durability principles.

## State categories

Durable state should be logically separated rather than stored as one opaque mutable blob. Categories include:

- risk state;
- runtime/system state;
- order lifecycle;
- trade lifecycle;
- Trade Plan/original R context;
- opportunity lifecycle;
- Market Episode identity;
- trade/opportunity journal;
- performance ledger;
- Strategy Registry;
- StrategyMemory/entry-exit learning;
- research/discovery/invention registry;
- promotion/rollback history;
- diagnostics/fault history;
- backup manifests/schema metadata.

The initial V1 storage engine choice is SQLite. Logical categories remain distinct namespaces/records instead of one opaque serialized application object.

## Daily risk persistence

Durable risk state must preserve at least:

- risk-day identity;
- day-start/cycle equity references and non-trading cash-flow adjustment;
- manual-reset enabled/count state;
- cooldown where applicable;
- Market Episode entry/loss/lock state.

A restart must not silently erase a daily loss lock or churn protection.

## Order lifecycle persistence

Once Phase 7 introduces Execution Intents, they must survive crashes, especially `SUBMITTING` and `ACCEPTED_UNKNOWN` states. Startup must reconcile these with broker truth before new entries become possible.

This is a Phase-7 extension of the implemented storage foundation, not a reason to invent order-state placeholders now.

## Open trade context

Broker position facts alone are insufficient to manage a trade intelligently after restart. Persist or deterministically recover:

- strategy/policy version;
- Opportunity/Episode IDs;
- signal/approved entry/actual fill identities;
- original SL and immutable original R;
- current broker SL/TP;
- primary/expansion/runner objectives;
- Trade Manager phase/context;
- relevant protected structure references.

Phase 6 already persists the pre-execution Trade Plan/original-R/objective context. Actual fill/current broker position fields arrive with the execution/trade lifecycle types.

## Opportunity and Market Episode state

A stored opportunity may be restored by identity but must be revalidated against fresh market state after downtime. Stale opportunities must not trigger orders merely because they were READY/ARMED before shutdown.

Market Episode identity survives restart to prevent duplicate entries and preserve legitimate re-entry lineage. Phase-6 persistence already preserves active Opportunity/Episode identity and Episode risk counters.

## Rebuildable versus durable market state

Rolling candles and much structural intelligence may be rebuilt from validated history. Rebuild must be deterministic and chronological.

Durable lifecycle/financial/order/learning evidence should not depend on a replaceable candle cache.

## State integrity

Persistent records use:

- database schema version;
- per-record schema version;
- update timestamp;
- canonical JSON;
- SHA-256 checksum;
- SQLite transactional durability;
- append-only transition/event rows where requested by the owning subsystem.

A corrupt critical state record must not silently fall back to safe-looking defaults.

## Atomic writes

SQLite transaction boundaries provide the V1 equivalent of the required atomic state update. Current record and requested audit event are committed together.

The implementation does not perform ad-hoc in-place JSON-file mutation.

## Schema versioning and migration

Database and record schema versions are explicit. Unsupported versions raise `StateVersionError`; critical state is not silently interpreted under different semantics.

Future migrations must be explicit and tested. Possible outcomes remain conceptually:

```text
MIGRATION_VERIFIED
STATE_VERSION_INCOMPATIBLE
MIGRATION_FAILED
```

## Broker versus local truth

Broker owns actual positions/orders/deals/account P&L. Local state owns strategy intent/context and historical lifecycle.

Conflicts require reconciliation, for example:

```text
local says OPEN
broker says no open position
→ inspect deals/history/account identity
→ resolve closure/manual action/data failure
```

Never simply delete the conflicting record.

## Startup sequence

Normal startup should conceptually perform:

```text
open/validate durable store
→ load RecoveryBundle
→ connect MT5
→ verify intended account
→ resolve symbol/specs
→ fetch positions/orders/deals
→ reconcile unresolved broker lifecycle
→ restore managed trades
→ restore/validate risk state
→ rebuild market intelligence
→ revalidate stored opportunities
→ load Strategy Registry/learning
→ acquire execution authority
→ READY
```

Open-position/order safety and reconciliation have priority over searching for new trades. Phase 6 implements durable loading/integrity; Phase 7 connects it to actual broker order/position reconciliation.

## Fault/recovery ledger

Persist meaningful incidents with:

- reason code;
- subsystem;
- severity;
- first/last seen;
- count;
- trading impact;
- recovery state/time.

The current generic event table is a durable foundation; richer diagnostic ownership may build on it without changing critical state semantics.

## Portable Strategy Registry

Strategy identity is machine-independent. The registry must preserve, where applicable:

- Strategy/Candidate ID;
- family/recipe/version;
- parameters;
- evidence/invalidation/timing/target semantics;
- status (`CHAMPION`, `CHALLENGER`, `SHADOW`, `CANARY`, `REJECTED`, etc.);
- genealogy/parent strategy;
- validation/promotion references;
- creation/promotion/rejection history.

Autonomous and governed strategies must survive process restart and machine replacement. This registry is implemented in the later research/learning phase, not faked in Phase 6.

## Learning portability

Entry learning, exit learning, StrategyMemory, candidate research and rejected-hypothesis memory should be durable/versioned so a new laptop does not restart learning from zero.

Production, shadow, canary and replay evidence must retain environment/version tags after migration.

## Public GitHub backup policy

The project may use the public GitHub repository as a disaster-recovery/versioned backup for non-financial-authority project intelligence, including:

- source code and docs;
- strategy definitions and learned parameters;
- Strategy Registry;
- autonomous candidates and genealogy;
- entry/exit learning summaries/state as implementation permits;
- research/promotion/rollback history;
- performance/evidence metadata;
- restore manifests.

The privacy rule is intentionally narrow: **credentials, tokens, private keys or other authentication material that can enable unauthorized financial action or direct paid-service cost must never be committed.**

Examples that must stay out of the public repository:

- MT5 trading passwords/authentication secrets;
- broker/private session tokens;
- paid API secrets;
- GitHub PAT/access tokens;
- private/signing/encryption keys;
- cloud/database credentials with financial/action authority.

Strategies/learning are not automatically treated as secrets under this project policy.

Live mutable SQLite database files are runtime state and should not be treated as mergeable source files. Portable checkpoint/export/manifest support can later publish the permitted recovery intelligence without exposing financial-authority secrets.

## Backup verification

A backup is not considered valid merely because files exist. A backup/checkpoint should verify, as applicable:

- required strategy/learning/research state is present;
- manifest/schema versions are valid;
- checksums/integrity checks pass;
- restore parsing succeeds;
- financial-authority secret scan passes;
- previous known-good backup is preserved on failure.

Meaningful checkpoints may be created after strategy promotion, important learning/research milestones, safe shutdown, upgrades and scheduled intervals. Exact retention/frequency remain open.

## Restore / machine migration

Controlled migration should follow:

```text
clone/install code
→ restore portable state/checkpoint
→ configure financial credentials separately
→ validate schema/integrity
→ connect intended MT5 account
→ broker reconciliation
→ rebuild market intelligence
→ acquire execution-controller authority
→ READY
```

A restored backup is context, not broker truth. Current positions/orders/deals must always be reconciled fresh.

## Multi-machine safety

Portable state does not grant multiple machines simultaneous broker-write authority. Execution controller ownership is governed by `EXECUTION_AND_BROKER_SAFETY.md`.

## Learning degradation

If optional learning state is unavailable/corrupt but the frozen baseline is independently valid, the system may operate in a documented degraded baseline mode while adaptive influence is disabled. Critical order/risk state cannot use this relaxed fallback.

## Dashboard visibility

Dashboard should expose compact persistence/backup facts such as:

```text
State Integrity     VERIFIED
Risk State          RESTORED
Opportunity/Plan    RESTORED / NONE
Broker Reconcile    PENDING / COMPLETE
Strategy Registry   RESTORED / NOT YET IMPLEMENTED
Backup              VERIFIED / STALE / FAILED
```

## Tests required

Implemented Phase-6 deterministic coverage:

- risk-day state survives process restart;
- cooldown and Episode risk state survive restart;
- Opportunity identity/lifecycle survives restart;
- Trade Plan/original-R/targets survive restart;
- checksum corruption fails closed;
- Opportunity/TradePlan identity mismatch fails closed;
- active plan/opportunity may be cleared without erasing risk-day history;
- SQLite integrity verification succeeds for healthy state.

Later required integration coverage:

- `SUBMITTING/ACCEPTED_UNKNOWN` recovery after Phase-7 order lifecycle exists;
- actual open-trade fill/current SL/TP recovery;
- schema migration/rollback fixtures when schema v2 exists;
- Strategy Registry/learning migration;
- fresh-machine restore drill;
- broker reconciliation after old backup restore;
- portable backup integrity/secret scan.

## Explicit non-goals

Persistence must not:

- treat stale backup as current broker truth;
- silently reset critical state after corruption;
- embed financial credentials inside strategy/learning backups;
- allow machine-specific IDs to redefine strategy identity;
- permit two restored laptops to trade the same managed account independently;
- add an ORM or service layer where SQLite + typed adapters already satisfy V1 requirements.

## Open questions

Resolved for initial V1 implementation:

- local durable runtime storage engine: **standard-library SQLite**;
- current record format: **canonical JSON + SHA-256 checksum inside SQLite**;
- current critical Phase-6 typed records: risk/cooldown/episode/opportunity/TradePlan.

Still open/later-phase:

- backup/checkpoint cadence and retention;
- exact Git-tracked portable state artifacts versus generated checkpoint/export artifacts;
- migration/rollback compatibility policy once a second schema version exists;
- execution-intent/order/trade persistence shape when Phase 7 real lifecycle types are implemented;
- execution-lease persistence/coordinator implementation;
- Strategy Registry/learning/research export shape.
