# GoldSwingTraderAI — Persistence, Restart and Recovery

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Durable lifecycle state, crash recovery, restart reconciliation, portable strategy/learning state, machine migration and backup/restore integrity.  
**Depends on:** `EXECUTION_AND_BROKER_SAFETY.md`, `RISK_CONTRACT.md`, `../20-trading-decisions/TRADE_PLAN.md`, `../40-research-learning/LEARNING_AND_AI_BOUNDARIES.md`

## Purpose

The bot must survive process restart, laptop loss/change and controlled migration without forgetting active obligations, strategy lineage or learning history.

> **Restart is not a fresh trading day unless the actual risk/session rules say so. Machine replacement is not strategy amnesia.**

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

Exact filenames/storage engines are implementation decisions.

## Daily risk persistence

Durable risk state must preserve at least:

- risk-day identity;
- LOSS_LOCKED state;
- manual-reset count/reference;
- cooldown where applicable;
- audit timestamps.

A restart must not silently erase a daily loss lock.

## Order lifecycle persistence

Execution intent must survive crashes, especially `SUBMITTING` and `ACCEPTED_UNKNOWN` states. Startup must reconcile these with broker truth before new entries become possible.

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

## Opportunity and Market Episode state

A stored opportunity may be restored by identity but must be revalidated against fresh market state after downtime. Stale opportunities must not trigger orders merely because they were ARMED before shutdown.

Market Episode identity should survive restart to prevent duplicate entries and preserve legitimate re-entry lineage.

## Rebuildable versus durable market state

Rolling candles and much structural intelligence may be rebuilt from validated history. Rebuild must be deterministic and chronological.

Durable lifecycle/financial/order/learning evidence should not depend on a replaceable candle cache.

## State integrity

Persistent records should use suitable protections such as:

- schema version;
- creation/update timestamp;
- checksums/hashes where appropriate;
- atomic writes;
- immutable event records for critical transitions;
- validated backups.

A corrupt critical state file must not silently fall back to safe-looking defaults.

## Atomic writes

Critical state should use a safe pattern equivalent to:

```text
write temporary
→ validate
→ flush/close
→ atomic replace
```

Exact platform implementation may vary, but partial writes must not become authoritative state.

## Schema versioning and migration

State schema changes require explicit compatibility/migration handling. Old state must not be silently interpreted under new semantics.

Possible outcomes:

```text
MIGRATION_VERIFIED
STATE_VERSION_INCOMPATIBLE
MIGRATION_FAILED
```

Incompatible critical state blocks affected authority until resolved.

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
load/validate durable state
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

Open-position safety/reconciliation has priority over searching for new trades.

## Fault/recovery ledger

Persist meaningful incidents with:

- reason code;
- subsystem;
- severity;
- first/last seen;
- count;
- trading impact;
- recovery state/time.

Transient faults may auto-recover. Deterministic integrity/account mismatches should not be hidden by endless retries.

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

Autonomous and governed strategies must survive process restart and machine replacement.

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
→ restore portable state
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
Strategy Registry  RESTORED
Learning Memory    RESTORED
Broker Reconcile   COMPLETE
Backup             VERIFIED / STALE / FAILED
```

## Tests required

- daily loss lock survives restart;
- original R/open-trade context survives restart;
- `SUBMITTING/ACCEPTED_UNKNOWN` recovery;
- atomic-write interruption;
- corrupt/checksum/schema mismatch handling;
- opportunity revalidation after downtime;
- portable Strategy Registry identity/genealogy;
- entry/exit learning migration;
- fresh-machine restore drill;
- broker reconciliation after old backup restore;
- financial-authority secret scan;
- backup integrity/restore verification.

## Explicit non-goals

Persistence must not:

- treat stale backup as current broker truth;
- silently reset critical state after corruption;
- embed financial credentials inside strategy/learning backups;
- allow machine-specific IDs to redefine strategy identity;
- permit two restored laptops to trade the same managed account independently.

## Open questions

- final storage engines/formats;
- backup cadence and retention;
- exact Git-tracked state artifacts versus generated checkpoint artifacts;
- exact secret-scanner rules/tooling;
- state migration/rollback compatibility policy;
- execution-lease persistence implementation.