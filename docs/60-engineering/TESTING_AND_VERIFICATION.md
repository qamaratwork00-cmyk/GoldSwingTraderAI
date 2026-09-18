# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 1.8-design  
**Authority:** Test taxonomy, executable proof requirements, replay/live parity, research evidence integrity, portable recovery, backup/catalog integrity, controller fencing, governed startup recovery and release verification.  
**Depends on:** `../90-governance/DOCUMENTATION_STANDARD.md`, `../40-research-learning/RESEARCH_AND_VALIDATION.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`, `../30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md`

## Purpose

Testing must prove documented invariants. `VERIFIED` is reserved for behaviour that passed required executable validation against the exact implementation.

> **Software verification and strategy validation are separate.**

## Test layers

```text
Unit / Contract
→ Component
→ Deterministic Replay
→ Research / Historical Session / Stress / Walk-Forward
→ Dataset / Acquisition / Evidence / Package Integrity
→ Persistence / Checkpoint / Backup Catalog / Restore / Fault Injection
→ Controller Contention / Fencing / Takeover Recovery
→ Governed Startup Recovery
→ Controlled Windows MT5 / Fresh Machine / Cross-Laptop / DEMO
→ End-to-End DEMO Certification
```

## Core chronology / research invariants

Future data cannot leak into structure, confluence, decisions, Trade Plans, Trade Manager actions or earlier validation windows. Historical PRE_CLOSE schedules must be explicit/versioned; synthetic schedules prove software semantics only.

## Persistence / checkpoint / backup

Tests protect current-record + event integrity, schema enforcement, deterministic `StoreSnapshot`, immutable public-safe checkpoint export/import, fresh-DB-only restore, financial-secret blocking, automatic due/skip cadence, retention, hashed catalog integrity, latest-verified selection and previous-known-good preservation after failed backup.

## Controller coordination / fencing

Tests prove:

- one winner under independent SQLite-store contention;
- monotonic fencing epoch across expiry/release/reopen;
- stale renew/release denial;
- `shared_locking_verified` false by default;
- valid holder blocks contenders;
- expired-lease takeover obtains higher epoch but remains `CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED`;
- renewal does not clear takeover block;
- explicit completion requires fresh same-holder/same-epoch authority;
- authority loss during recovery prevents completion;
- `ExecutionService` checks controller ID + fencing epoch immediately before send.

These prove software semantics on correctly locking SQLite storage, not arbitrary network filesystem safety.

## Governed startup recovery tests

`app/recovery.py` must prove:

- StateStore integrity is checked before READY;
- clean current DEMO recovery can reach READY;
- non-DEMO broker context blocks;
- persisted account/server/symbol mismatch blocks;
- incomplete broker position truth remains RECONCILING;
- `APPROVED` pre-submit Intent may be safely cancelled to FAILED with zero send attempts;
- `CREATED` Intent does not become an implicit send;
- `SUBMITTING` / `ACCEPTED_UNKNOWN` route through existing broker reconciler;
- unresolved reconciliation stays RECONCILING and never blind-resends;
- verified OPEN without durable ManagedTrade context cannot become READY;
- ManagedTrade requires exact ticket/symbol/direction/volume identity;
- missing broker position remains RECONCILING;
- SL/TP mismatch outside explicit tolerance remains RECONCILING;
- duplicate/identity/volume conflict blocks;
- every supplied hard RecoveryAuthority must PASS;
- UNKNOWN authority remains RECONCILING and BLOCK authority blocks;
- a takeover controller remains fenced until the full recovery sequence passes;
- only then may startup call `complete_takeover_reconciliation()`;
- takeover completion is rechecked against the current holder/epoch;
- recovery performs no raw broker write.

The caller-supplied price tolerance must come from verified broker geometry; tests must not hide a hard-coded Gold tolerance inside recovery logic.

## Risk / execution / session tests

Risk tests cover frozen bands, min-lot actual risk, daily lock/reset/cooldown and 0/1 capacity. Execution tests cover positive DEMO guard, central gate, exactly-one-send, ambiguous ACK reconciliation and controller fencing. Runtime session/news tests cover frozen blackout/PRE_CLOSE/reopen rules.

## Fresh-machine / broker reconciliation

Deterministic startup recovery is necessary but not sufficient. Controlled certification must combine a restored checkpoint with a real current MT5 account/symbol/positions/orders/deals snapshot, prove no stale order replay and verify current controller authority before broker writes.

Cross-laptop certification additionally requires real shared-storage/network failure tests and stale-primary denial.

## Evidence reporting

```text
Deterministic CI                PASS / count
StateStore/checkpoint integrity PASS
Local backup catalog            PASS
SQLite controller fencing       PASS
Startup recovery coordinator    PASS
Live MT5 recovery snapshot      PENDING/PASS
Fresh-machine broker reconcile  PENDING/PASS
Cross-laptop coordination       PENDING/PASS
Remote backup publication       PENDING/PASS
Historical PRE_CLOSE software   PASS
Research evidence packages      PASS
DEMO execution                  PENDING/PASS
```

Current deterministic checkpoint after startup recovery integration: **219 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Release-blocking failures

At minimum:

- future-data leakage;
- optional confluence becoming hidden hard gate;
- favorable ambiguity guessing;
- hidden walk-forward tuning/holdout bypass;
- guessed historical session truth;
- dataset/evidence/checkpoint/catalog tamper accepted;
- secret included in public backup flow;
- failed backup destroys previous known-good state;
- stale checkpoint merged into live DB;
- restored local state treated as broker truth;
- blind resend of unresolved Intent;
- verified OPEN accepted without management context;
- startup READY with account/symbol/ManagedTrade mismatch;
- startup READY with any required hard authority UNKNOWN/BLOCK;
- takeover completion before governed recovery passes;
- non-monotonic fencing / split-brain write;
- centralized execution/DEMO guard bypass;
- autonomous self-promotion/broker bypass.

## Explicit non-goals

Deterministic CI is not profitability proof, real broker proof, remote publication proof or cross-laptop filesystem certification. Checkpoints and recovery DTOs do not grant execution authority by themselves.

## Open questions / controlled evidence still required

- live MT5 recovery-position adapter test matrix;
- real fresh-machine + broker reconciliation certification matrix;
- exact shared-storage/cross-laptop failover environment;
- authenticated public-safe GitHub publication matrix;
- controlled Windows/MT5 historical acquisition/session evidence;
- real-data walk-forward/holdout requirements;
- empirical execution-friction calibration;
- final DEMO certification/forward-evidence requirement.
