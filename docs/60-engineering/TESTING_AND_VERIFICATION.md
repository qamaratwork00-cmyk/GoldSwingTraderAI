# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 1.9-design  
**Authority:** Test taxonomy, executable proof requirements, replay/live parity, recovery/broker-read integrity, controller fencing and release verification.  
**Depends on:** `../90-governance/DOCUMENTATION_STANDARD.md`, `../10-market-intelligence/MARKET_DATA_AND_HISTORY.md`, `../40-research-learning/RESEARCH_AND_VALIDATION.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`, `../30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md`

## Purpose

Testing must prove documented invariants. `VERIFIED` is reserved for behaviour that passed required executable validation against the exact implementation.

> **Software verification and strategy validation are separate.**

## Test layers

```text
Unit / Contract
→ Component
→ Deterministic Replay / Research
→ Dataset / Evidence Integrity
→ Persistence / Checkpoint / Backup / Restore
→ Controller Fencing / Startup Recovery
→ Live-Read MT5 Recovery Adapter
→ Controlled Windows MT5 / Fresh Machine / Cross-Laptop / DEMO
→ End-to-End DEMO Certification
```

## Core deterministic invariants

No future leakage; no hidden confluence hard gate; explicit historical session truth; checkpoint/catalog integrity; financial-secret blocking; one-shot execution; broker reconciliation; monotonic fencing; takeover recovery; restored state never equals broker truth.

## Live MT5 recovery read tests

`MT5Reader.open_positions()` and `app/recovery_mt5.py` must prove:

- current positions come through the existing `MT5Reader` boundary;
- no duplicate raw MetaTrader5 recovery client exists;
- BUY and SELL types normalize correctly;
- result ordering is deterministic by broker ticket;
- MT5 SL/TP `0` normalize to explicit `None`;
- optional magic/comment are preserved as read facts;
- a positive empty broker collection becomes complete empty exposure;
- `positions_get() is None` is `DATA_UNAVAILABLE`, never empty exposure;
- invalid direction/wrong symbol/invalid geometry fail `DATA_CORRUPT`;
- duplicate broker position ticket fails closed;
- recovery adapter resolves configured symbol aliases;
- adapter includes current `AccountFacts` and verified `SymbolSpec`;
- `BrokerRecoverySnapshot.positions_complete=True` is emitted only after successful position read;
- recovery SL/TP comparison tolerance comes from verified `SymbolSpec.tick_size`;
- no hard-coded XAU tick/price tolerance is hidden in recovery code.

## Governed startup recovery tests

Startup recovery tests prove persistent integrity first, current DEMO/account/server/symbol consistency, unresolved Intent reconciliation, ManagedTrade/current-position matching, required hard authorities and controller takeover completion only at the successful end.

## Persistence / backup / controller tests

Checkpoint/backup tests protect canonical records/events, secret blocking, no-overwrite restore, due/skip cadence, retention/catalog integrity and last-known-good preservation.

Controller tests protect one-winner contention, monotonic epochs, stale-holder denial and reconciliation-gated takeover. Local deterministic SQLite tests do not certify arbitrary network filesystems.

## Controlled evidence boundary

Public CI can verify the read adapter with fake MT5 modules, but cannot prove the intended Windows terminal/broker actually returns equivalent account/symbol/open-position facts. That evidence remains controlled external work.

Fresh-machine certification must use a real restored checkpoint plus current broker positions/orders/deals and prove no stale replay before READY.

## Evidence reporting

```text
Deterministic CI                PASS / count
Market read contracts           PASS
Live-recovery adapter software  PASS
State/checkpoint/backup         PASS
Controller/startup recovery     PASS
Real Windows MT5 recovery read  PENDING/PASS
Fresh-machine broker reconcile  PENDING/PASS
Cross-laptop coordination       PENDING/PASS
Remote backup publication       PENDING/PASS
DEMO execution                  PENDING/PASS
```

Current deterministic checkpoint after live MT5 recovery adapter: **226 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Release-blocking failures

At minimum:

- future-data leakage;
- unknown broker position read accepted as zero exposure;
- corrupt/duplicate broker position accepted;
- recovery hard-codes a guessed Gold tolerance instead of verified geometry;
- duplicate raw MT5 recovery client bypasses read boundary;
- checkpoint/catalog tamper or financial secret accepted;
- stale restore treated as broker truth;
- blind resend of unresolved Intent;
- ManagedTrade mismatch accepted as READY;
- hard recovery authority UNKNOWN/BLOCK accepted as READY;
- takeover completion before recovery passes;
- non-monotonic fencing/split-brain write;
- centralized execution/DEMO guard bypass.

## Explicit non-goals

Fake MT5 tests are software evidence, not real broker certification. Passing deterministic recovery does not prove profitability, broker behavior, cross-laptop filesystem safety or DEMO execution correctness.

## Pending controlled matrix

- Windows MT5 account/symbol/open-position recovery read;
- fresh-machine + broker reconciliation;
- shared-storage/cross-laptop failover;
- authenticated public backup publication;
- real history/session evidence;
- final DEMO forward/fault certification.
