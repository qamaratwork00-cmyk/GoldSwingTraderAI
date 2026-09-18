# GoldSwingTraderAI — Persistence, Restart and Recovery

**Status:** PROVISIONAL — IMPLEMENTED FOUNDATION  
**Version:** 0.3-implementation  
**Authority:** Durable lifecycle state, crash recovery, restart reconciliation, portable strategy/learning state, machine migration and backup/restore integrity.  
**Depends on:** `EXECUTION_AND_BROKER_SAFETY.md`, `RISK_CONTRACT.md`, `../20-trading-decisions/TRADE_PLAN.md`, `../40-research-learning/LEARNING_AND_AI_BOUNDARIES.md`

## Purpose

The bot must survive process restart, laptop loss/change and controlled migration without forgetting active obligations, strategy lineage or learning history.

> **Restart is not a fresh trading day unless the actual risk/session rules say so. Machine replacement is not strategy amnesia.**

## Current implementation checkpoint

Initial V1 local persistence uses Python standard-library `sqlite3`. No ORM/service/database framework is required.

Core storage owners:

```text
src/goldswingtraderai/persistence/store.py
src/goldswingtraderai/persistence/runtime_state.py
src/goldswingtraderai/persistence/__init__.py
```

Subsystem repositories/adapters now also persist their own typed state on top of the same `StateStore` durability model, including execution intents, managed-trade state, research episodes, candidate registry and promotion lifecycle.

### `store.py`

Provides a transactional `StateStore` with:

- SQLite durable records;
- canonical JSON payloads;
- SHA-256 checksums;
- explicit database/record schema versions;
- `PRAGMA quick_check` plus record-checksum integrity verification;
- WAL journal mode and `synchronous=FULL`;
- atomic transactional upsert/delete;
- optional append-only event records written in the same transaction as current-state update.

Corrupt JSON/checksum/schema state raises an explicit persistence error. It is never converted into an empty safe-looking runtime state.

### `runtime_state.py`

Typed round-trip adapters currently cover:

- `RiskDayState`;
- `CooldownState`;
- `EpisodeRiskState`;
- active `Opportunity`;
- active `TradePlan`, including objective/original-R context.

`RuntimeStateRepository` scopes records by managed account/symbol identity supplied by caller. `load_recovery_bundle()` validates storage integrity and cross-checks Opportunity, Market Episode and Trade Plan lineage.

### Later-phase typed persistence now implemented

The Phase-6 foundation has since been extended by real later subsystem types rather than speculative placeholders:

- durable `ExecutionIntent` lifecycle/history through execution intent storage;
- managed open-trade state through management storage;
- durable research episodes through `ResearchEpisodeRepository`;
- durable candidate/rejected memory through `CandidateRegistry`;
- durable promotion lifecycle/holdout/rollback state through `PromotionRegistry`.

These states survive process restart in deterministic tests. They still require final whole-runtime startup orchestration and controlled broker/fresh-machine evidence before release verification.

## State categories

Durable state is logically separated rather than stored as one opaque mutable blob:

- risk state;
- runtime/system state;
- execution intent/order lifecycle;
- managed trade lifecycle;
- Trade Plan/original R context;
- Opportunity lifecycle;
- Market Episode identity;
- trade/opportunity/research journal;
- performance/learning evidence;
- Strategy/Candidate Registry;
- StrategyMemory/entry-exit learning where persisted;
- research/discovery/invention state;
- promotion/rollback history;
- diagnostics/fault history;
- backup manifests/schema metadata.

## Daily risk persistence

Durable risk state preserves at least:

- risk-day identity;
- day-start/cycle equity references and non-trading cash-flow adjustment;
- manual-reset enabled/count state;
- cooldown state;
- Market Episode entry/loss/lock state.

Restart must not silently erase a daily loss lock or churn protection.

## Execution Intent persistence

Execution intent persistence is now implemented. Critical one-shot states such as `SUBMITTING` and `ACCEPTED_UNKNOWN` survive restart.

Startup/recovery rule:

```text
restored SUBMITTING / ACCEPTED_UNKNOWN
→ DO NOT RESEND
→ query broker truth
→ reconcile positions/orders/deals/action state
→ classify VERIFIED / FAILED / still UNKNOWN
→ only then may a fresh governed Intent be considered
```

An already-consumed Intent ID can never be recreated in memory to obtain another irreversible send allowance.

## Open-trade context

Broker position facts alone are insufficient to manage a trade intelligently after restart. Durable/recoverable context includes, as applicable:

- strategy/policy version;
- Opportunity/Episode/Trade IDs;
- signal/approved entry/actual fill identities;
- original SL and immutable original R;
- current verified broker SL/TP;
- Primary/Expansion/Runner objectives;
- Trade Manager phase/context;
- relevant protected structure references.

Managed-trade persistence exists deterministically. Current broker SL/TP/position truth must still be reconciled fresh after restart.

## Opportunity and Market Episode state

A stored opportunity may be restored by identity but must be revalidated against fresh market state after downtime. Stale READY/ARMED state cannot trigger an order merely because it was persisted.

Market Episode identity survives restart to prevent duplicate entries and preserve legitimate re-entry lineage.

## Research / discovery / promotion persistence

Phase-10 research state is now real rather than a future placeholder.

Durable pieces include:

- outcome-labelled research episodes;
- Candidate IDs/recipes/fingerprints;
- rejected/duplicate candidate memory;
- promotion stage;
- locked fingerprint;
- final-holdout identity/consumed state;
- rejection/rollback/promotion metadata.

Discovery restart behaviour must preserve liveness semantics: eligible recurring evidence after restart must still be able to produce a candidate or explicit governed suppression reason rather than forgetting prior evidence.

## Rebuildable versus durable market state

Rolling candles and structural/technical intelligence may be rebuilt from validated history. Rebuild must be deterministic and chronological.

Durable financial/order/trade/learning evidence should not depend on a replaceable candle cache.

## State integrity and atomicity

Persistent records use:

- database schema version;
- per-record schema version;
- canonical JSON;
- SHA-256 checksum;
- SQLite transaction boundaries;
- append-only transition/event rows where requested by owner.

A corrupt critical state record must not silently fall back to defaults.

## Schema versioning and migration

Unsupported database/record versions raise explicit version errors. Critical state is not silently interpreted under changed semantics.

Future schema migrations must be explicit and tested. Until schema v2+ exists, migration mechanics remain release-engineering work rather than speculative framework code.

## Broker versus local truth

Broker owns current positions/orders/deals/account P&L. Local persistence owns intent, context and lifecycle history.

Example conflict:

```text
local says OPEN
broker says no open position
→ inspect deals/history/account identity
→ reconcile closure/manual action/data failure
→ do not simply delete the local record
```

## Final startup/recovery sequence

The target integrated startup is:

```text
open + integrity-check SQLite
→ load critical recovery records
→ connect intended MT5 DEMO account
→ verify account/symbol
→ fetch positions/orders/deals
→ reconcile unresolved ExecutionIntents
→ reconcile managed trades
→ restore/validate risk state
→ rebuild market intelligence chronologically
→ revalidate stored opportunities
→ load research/candidate/promotion/learning state
→ acquire current controller lease/epoch
→ evaluate hard permissions
→ READY
```

The individual persistence/reconciliation components exist, but this complete persistent startup orchestration remains a final integration task.

## Fault/recovery ledger

Meaningful incidents should preserve:

- reason code;
- subsystem;
- severity;
- first/last seen;
- occurrence count;
- trading impact;
- recovery state/time.

The generic event table provides a durable base; richer diagnostics can build on it without redefining critical state semantics.

## Public GitHub backup policy

The public repository may back up non-financial-authority project intelligence:

- source/docs;
- strategy definitions/learned parameters;
- Candidate/Strategy Registry;
- autonomous candidates/genealogy/rejected memory;
- entry/exit learning summaries where export permits;
- research/promotion/rollback history;
- performance/evidence metadata;
- restore manifests/checkpoints.

Never publish authority-bearing credentials/tokens/keys capable of unauthorized financial action/authenticated account control/direct paid-service cost.

Live mutable SQLite DB files are runtime state, not mergeable source artifacts. Phase-11 portable export/checkpoint work should package permitted recovery intelligence deliberately rather than treating the live DB as a Git merge target.

## Backup verification

A backup is not valid merely because files exist. Verify as applicable:

- required strategy/learning/research state exists;
- manifest/schema versions valid;
- checksums/integrity pass;
- restore parsing succeeds;
- financial-secret scan passes;
- previous known-good backup preserved on failure.

Exact backup cadence/retention remain Phase-11 implementation choices.

## Restore / machine migration

```text
clone/install code
→ restore portable checkpoint
→ configure financial credentials separately
→ validate schema/integrity
→ connect intended MT5 DEMO
→ broker reconciliation
→ restore/rebuild runtime intelligence
→ acquire fresh controller authority
→ READY only after hard checks pass
```

A restored backup is context, not broker truth.

## Multi-machine safety

Portable state does not grant multiple machines broker-write authority. Controller ownership remains governed by `EXECUTION_AND_BROKER_SAFETY.md`.

The deterministic in-memory coordination backend is test-only; real shared atomic coordination is still required before cross-laptop failover certification.

## Learning degradation

If genuinely optional learning/adaptive state is unavailable while frozen baseline semantics remain independently valid, the system may expose documented degraded baseline operation where its authority permits it.

Critical risk/order/trade state cannot use that relaxed fallback.

## Dashboard visibility

Compact persistence/recovery facts should include, as available:

```text
State Integrity       VERIFIED / FAILED
Risk State            RESTORED / MISSING
Execution Intents     CLEAR / RECONCILING
Managed Trade         RESTORED / NONE / RECONCILING
Opportunity/Plan      RESTORED / NONE
Candidate Registry    RESTORED
Promotion Registry    RESTORED
Broker Reconcile      PENDING / COMPLETE
Backup                VERIFIED / STALE / FAILED / PENDING
```

## Tests required / current evidence

Deterministic coverage exists for:

- risk-day/cooldown/Episode restart;
- Opportunity/TradePlan lineage restart;
- checksum corruption fail-closed;
- active plan/opportunity clear without erasing risk history;
- ExecutionIntent one-shot history/restart semantics;
- unresolved intent reconciliation paths;
- managed-trade state persistence;
- research episode restart;
- Candidate/rejected-memory restart;
- promotion/holdout/rollback restart.

Still required before release verification:

- fully integrated startup/recovery path;
- real broker open-position/SL/TP restart reconciliation;
- schema migration/rollback fixtures once a second schema exists;
- portable checkpoint/export integrity;
- fresh-machine restore drill;
- old-backup + live-broker reconciliation drill;
- production shared-controller failover recovery.

## Explicit non-goals

Persistence must not:

- treat stale backup as current broker truth;
- silently reset critical state after corruption;
- embed financial credentials in backups;
- allow machine-specific IDs to redefine strategy identity;
- permit two restored laptops to trade the same managed account independently;
- add an ORM/service layer where SQLite + typed adapters satisfy V1.

## Open / later implementation items

Resolved for V1:

- local durable runtime engine: **standard-library SQLite**;
- record shape: **canonical JSON + SHA-256 checksum in SQLite**;
- typed repositories/adapters for current critical runtime/execution/management/research state.

Still pending:

- backup/checkpoint cadence/retention;
- portable export/manifest format;
- migration/rollback compatibility when schema v2+ exists;
- production shared execution-controller coordinator;
- final integrated startup/shutdown/recovery orchestration;
- fresh-machine restore certification.
