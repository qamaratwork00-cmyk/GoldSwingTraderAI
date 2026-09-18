# GoldSwingTraderAI — Open Questions / Freeze Matrix

**Status:** LIVING LEDGER  
**Version:** 3.2-design

This file separates remaining items so implementation is not delayed by values that should be learned from evidence or ordinary engineering choices.

```text
FIX BEFORE BUILD       = required architecture/safety decision still missing
CALIBRATE IN RESEARCH  = explicit deterministic baseline, tune only with chronological evidence
IMPLEMENTATION CHOICE  = coder may choose implementation preserving frozen contract
DEFER LATER            = not required for V1
```

At behavioural-contract level there are currently **no known `FIX BEFORE BUILD` items**.

## Current implementation status

Deterministic core exists through Phase 10 plus current Phase-11 recovery/controller foundation:

```text
1  Foundation/config/domain/CI
2  MT5 read layer + market snapshots
3  Market intelligence + Trendline/Fibonacci/POC
4  Strategies/fusion/Opportunity/Entry Timing
5  Trade Plan + Risk
6  Session/news permission + SQLite persistence
7  Execution intent/gate/controller/writer/reconciliation
8  Trade Manager + execution bridge
9  Dashboard renderer
10 Research replay/session/stress/walk-forward
   + portable datasets / MT5 history acquisition
   + evidence packages / learning/discovery/promotion
11 StateStore snapshot + portable checkpoint
   + fresh-local-DB restore
   + automatic local checkpoint cadence/catalog/retention
   + durable SQLite coordination + monotonic fencing
   + reconciliation-gated controller takeover
   + governed startup recovery coordinator
```

Live DEMO release and real-data validation are not complete. Final live MT5 recovery adapter/runtime orchestration, authenticated remote publication, controlled cross-laptop proof, fresh-machine broker drill and DEMO certification remain pending.

## Frozen trading principles still in force

- completed candles own structural confirmation;
- Trendline/Fibonacci/POC remain optional bonus-only confluence;
- six production strategy families remain parallel;
- structural RR/target/runner policy remains frozen;
- SMALL is any positive day-start equity below `$300`;
- Gold capacity is `0/1` independently risk-bearing position;
- daily/session/news/execution safety stays separate from soft scoring;
- verified connected DEMO is required for V1 broker-write permission.

## Persistence / backup — deterministic software gaps closed

Implemented:

- canonical StateStore current-record + append-only-event integrity;
- portable public-safe runtime checkpoint;
- financial-secret blocking;
- fresh-DB-only restore;
- automatic local 15-minute / keep-96 configurable baseline;
- verified hashed backup catalog and latest-known-good selection;
- failed-backup preservation;
- remote-auth separation.

Remote authenticated publication remains pending and must keep PAT/token credentials outside repository/checkpoint state.

## Controller / failover — software semantics closed, deployment proof pending

Implemented:

- transactional SQLite coordination backend;
- one-winner deterministic contention;
- durable monotonic epoch ledger;
- stale renew/release denial;
- explicit shared-locking deployment assertion default false;
- takeover obtains higher epoch but stays BLOCKED;
- `CONTROLLER_TAKEOVER_RECONCILIATION_REQUIRED` survives lease renewal;
- only fresh same-holder/same-epoch verification can clear takeover after recovery.

Still controlled-evidence pending:

- exact shared storage across two real machines;
- simultaneous startup contention;
- machine/process loss + TTL expiry;
- standby higher-epoch takeover;
- stale primary restart denial;
- network/storage interruption fail-closed behavior;
- no split brain.

If real storage cannot prove SQLite locking/durability, replace the backend rather than weaken fencing.

## Startup recovery — deterministic software gap CLOSED

`app/recovery.py` now owns the governed READY sequence.

Implemented:

```text
StateStore integrity
→ typed runtime recovery bundle
→ current ExecutionIntent
→ current ManagedTrade
→ DEMO + persisted account/server/symbol consistency
→ unresolved Intent reconciliation
→ ManagedTrade vs broker position reconciliation
→ all hard RecoveryAuthorities PASS
→ fresh controller verification
→ takeover completion only at the successful end
→ READY
```

Key frozen recovery semantics:

- restored state is context, never broker truth;
- APPROVED pre-submit Intent may be cancelled safely because no send allowance was consumed;
- CREATED requires explicit recovery review;
- SUBMITTING/ACCEPTED_UNKNOWN never blind resend;
- VERIFIED OPEN without ManagedTrade context stays RECONCILING;
- missing/mismatched broker position prevents READY;
- broker-position ticket/symbol/direction/volume identity is hard;
- SL/TP mismatch requires reconciliation;
- price tolerance comes from verified broker geometry, not a guessed Gold constant;
- any hard authority UNKNOWN/BLOCK prevents READY;
- takeover controller cannot self-clear before the governed sequence passes.

Current deterministic evidence: **219 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Phase 11 remaining implementation choices

- extend/reuse existing `MT5Reader` for current open-position recovery facts; no duplicate raw MT5 read client;
- adapter that builds `BrokerRecoverySnapshot` from initialized live read boundary;
- final runtime owner that supplies authoritative `RecoveryAuthorities` from risk/session/data/execution owners;
- operator recovery/controller DTO;
- authenticated publication mechanism for already verified backup artifacts.

## Phase 11 controlled evidence pending

- restore a real checkpoint on another machine;
- verify intended MT5 DEMO account/server/symbol;
- fetch real positions/orders/deals;
- reconcile unresolved Intent/open ManagedTrade;
- old backup + newer broker-truth conflict drill;
- no stale order replay;
- real cross-laptop coordination/fencing proof.

## Schema migration

DEFER until schema v2 actually exists. Current code correctly rejects unsupported schemas; speculative transforms are not required.

## Research calibration still pending

- market-intelligence/scoring/timing/trailing thresholds;
- optional-confluence retention;
- real-data periods/sample sizes;
- walk-forward window sizes/stepping;
- stress/broker-friction distributions;
- promotion/Shadow/Canary thresholds;
- StrategyMemory/discovery thresholds;
- Monte Carlo/block/regime-aware methodology.

## Operator / runtime / release pending

- live recovery snapshot + authoritative startup wiring;
- dashboard backup/recovery/controller/Discovery Health visibility;
- authenticated public backup publication;
- real cross-laptop controller proof;
- controlled Windows/MT5 DEMO lifecycle/fault/restart certification;
- broad real-XAU validation/holdout/forward evidence;
- final docs/release audit.

## Governance conclusion

No major behavioural redesign item is known. Next implementation work is **live read-only MT5 recovery truth**, then complete startup/runtime integration, external backup publication and controlled fresh-machine/cross-laptop/DEMO evidence.
