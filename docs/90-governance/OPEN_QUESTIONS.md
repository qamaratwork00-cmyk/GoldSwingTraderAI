# GoldSwingTraderAI — Open Questions / Freeze Matrix

**Status:** LIVING LEDGER  
**Version:** 3.3-design

This file separates remaining items so implementation is not delayed by values that should be learned from evidence or ordinary engineering choices.

```text
FIX BEFORE BUILD       = required architecture/safety decision still missing
CALIBRATE IN RESEARCH  = explicit deterministic baseline, tune only with chronological evidence
IMPLEMENTATION CHOICE  = coder may choose implementation preserving frozen contract
DEFER LATER            = not required for V1
```

At behavioural-contract level there are currently **no known `FIX BEFORE BUILD` items**.

## Current implementation status

Deterministic core exists through Phase 10 plus current Phase-11 recovery foundation:

```text
1–9  production architecture foundations
10   research replay/session/stress/walk-forward/data/evidence/learning
11   StateStore snapshot + portable checkpoint
     + fresh-local-DB restore
     + automatic local backup/catalog/retention
     + durable SQLite coordination / monotonic fencing
     + reconciliation-gated takeover
     + governed startup recovery
     + read-only live MT5 recovery truth adapter
```

Current deterministic checkpoint: **226 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Live MT5 recovery read gap — CLOSED at deterministic software level

The existing `MT5Reader` now owns current open-position reads. `app/recovery_mt5.py` composes those facts into `MT5RecoveryTruth`.

Frozen semantics now implemented:

- no second raw MetaTrader5 recovery client;
- positive empty `positions_get` result = verified empty current exposure;
- `positions_get() is None` = `DATA_UNAVAILABLE`, never zero exposure;
- invalid direction/symbol/geometry/duplicate ticket = `DATA_CORRUPT`;
- current position facts normalize ticket/symbol/direction/volume/open-price/SL/TP/magic/comment;
- MT5 zero SL/TP becomes explicit `None`;
- recovery snapshot is marked complete only after successful position read;
- recovery price tolerance comes from verified broker `tick_size`, not a guessed XAU constant;
- broker position facts do not independently prove bot ownership.

Real connected Windows MT5 evidence remains pending.

## Startup recovery — software gap CLOSED

`app/recovery.py` owns:

```text
persistence integrity
→ runtime bundle
→ Intent reconciliation
→ ManagedTrade reconciliation
→ DEMO/account/server/symbol checks
→ hard RecoveryAuthorities
→ fresh controller authority
→ takeover completion if required
→ READY
```

Unknown broker truth, unresolved Intent, missing management context, ManagedTrade mismatch or any hard UNKNOWN/BLOCK prevents READY.

## Backup / publication

Closed deterministically:

- portable checkpoint;
- financial-secret blocking;
- fresh-DB restore;
- configurable local backup cadence/retention;
- hashed verified catalog;
- latest known-good selection;
- failure preserves previous known-good backup.

Still pending:

- authenticated publication of already-verified public-safe artifacts;
- external credential handling that never serializes PAT/tokens into repo/checkpoint state;
- remote failure/retention semantics.

## Controller / failover

Closed deterministically:

- transactional SQLite coordination;
- one-winner contention;
- monotonic durable epoch;
- stale renew/release denial;
- takeover blocked until governed recovery completion.

Still controlled evidence pending:

- selected shared storage across two real machines;
- simultaneous contention;
- primary loss + TTL expiry;
- higher-epoch standby takeover;
- stale-primary denial;
- network/storage interruption fail-closed behavior;
- no split-brain.

If actual storage cannot prove SQLite semantics, replace the backend rather than weaken fencing.

## Next implementation choices

- create final startup service that initializes the existing MT5Reader, builds `MT5RecoveryTruth` and invokes `StartupRecoveryCoordinator`;
- construct `RecoveryAuthorities` from real authoritative market/risk/session/execution owners instead of test-supplied traces;
- decide explicit runtime mode/config for restore-vs-existing-local-state startup without silently overwriting either;
- operator DTO for backup/recovery/controller state;
- external authenticated backup publication adapter/workflow.

## Controlled evidence pending

- real Windows MT5 recovery read facts;
- real fresh-machine checkpoint restore;
- old backup + newer broker-truth conflict drill;
- unresolved Intent/current deals reconciliation;
- cross-laptop fencing/failover proof;
- controlled DEMO write/modify/close/restart evidence.

## Research calibration still pending

Market intelligence/scoring/timing/trailing thresholds, confluence retention, real-data periods/sample sizes, walk-forward stepping, friction distributions, promotion/Shadow/Canary thresholds, StrategyMemory/discovery thresholds and Monte Carlo/regime-aware methodology remain evidence-calibrated work.

## Governance conclusion

No major behavioural redesign item is known. Next code work is **final startup service + authoritative recovery-authority wiring**, followed by operator visibility, external publication and controlled real-machine/DEMO evidence.
