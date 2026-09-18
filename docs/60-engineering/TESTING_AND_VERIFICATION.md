# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 1.6-design  
**Authority:** Test taxonomy, executable proof requirements, replay/live parity, research data/evidence integrity, historical session-policy replay, portable runtime recovery, local backup catalog/retention, crash/restart, migration, learning-governance and release verification.  
**Depends on:** `../90-governance/DOCUMENTATION_STANDARD.md`, `../40-research-learning/RESEARCH_AND_VALIDATION.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`, `../30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md`

## Purpose

Testing must prove documented invariants. `VERIFIED` is reserved for behaviour that actually passed required executable validation against the exact implementation.

> **Software verification and strategy validation are separate.**

## Test layers

```text
Unit / Contract
→ Component
→ Deterministic Replay
→ Research Ablation / Outcomes / Manager / Historical Session / Stress / Walk-Forward
→ Dataset / Acquisition / Evidence / Package Integrity
→ Persistence / Runtime Checkpoint / Backup Catalog / Restore / Fault Injection
→ Controlled Windows MT5 / Fresh Machine / DEMO
→ Learning / Discovery / Promotion Governance
→ End-to-End DEMO Certification
```

## No-lookahead / strategy / lifecycle

Future data cannot leak into structure, confluence, decisions, Trade Plans, manager actions or earlier validation windows. Optional Trendline/Fib/POC remains bonus-only. WAIT/MISSED/INVALID, re-entry limits and immutable original-R semantics remain regression protected.

## Historical session / research replay

Historical schedules require explicit source/version/coverage; DAILY/WEEKEND PRE_CLOSE timing is reused from production permission. Out-of-coverage or verified CLOSED contradictions fail explicitly. Synthetic schedules prove software semantics only.

Research replay tests preserve same-bar ambiguity, production Trade Manager reuse, non-retroactive modifications, explicit friction assumptions, fixed-policy walk-forward boundaries, development-not-scored and final-holdout separation.

## Dataset / evidence / package integrity

Research tests cover content-addressed identities, portable dataset round-trip/tamper checks, exact-count MT5 acquisition, explicit spread provenance, immutable evidence packages and financial-secret-shaped evidence-field rejection.

## Runtime persistence integrity

`StateStore` tests prove current-record and append-only-event checksum/JSON/timestamp integrity, schema enforcement, durable event ordering, corruption fail-closed behaviour, deterministic snapshot export and empty-target-only snapshot restore.

## Portable runtime checkpoint tests

`persistence/checkpoint.py` must prove:

- exact canonical file set `checkpoint_manifest.json`, `records.jsonl`, `events.jsonl`;
- write-new/no-overwrite export;
- source integrity check before export;
- records/events round-trip preserving checksums/timestamps/event IDs;
- file hashes/counts/`checkpoint_sha256` tamper detection;
- schema/filename/file-set/symlink rejection;
- structured payload secret block with `FINANCIAL_SECRET_DETECTED`;
- failed secret export leaves no completed artifact;
- fresh non-existing restore destination only;
- temporary restore + integrity verification before atomic handoff;
- typed and generic namespaces remain readable after restore;
- restore reports `broker_reconciliation_required=True`.

A deterministic checkpoint restore is **not** permission to trade.

## Automatic local backup / catalog tests

`persistence/backup.py` must prove:

- first due backup creates a fully verified checkpoint + hashed catalog entry;
- a call before configured interval returns `SKIPPED_NOT_DUE` without creating a new checkpoint;
- at the exact due boundary a new checkpoint may be created;
- retention keeps only the configured newest count;
- pruning happens only after a new verified checkpoint and catalog exist;
- `backup_catalog.json` hash detects catalog tamper;
- catalog entries are chronological and checkpoint names cannot escape `checkpoints/`;
- catalog verification re-imports each referenced checkpoint and checks checkpoint SHA + record/event counts;
- tampering a referenced checkpoint makes `load_backup_catalog(..., verify_checkpoints=True)` fail closed;
- `latest_verified_checkpoint()` never returns a tampered/unverified checkpoint;
- a new backup that fails because of `FINANCIAL_SECRET_DETECTED` leaves the old catalog and previous known-good checkpoint unchanged;
- non-positive cadence/retention configuration is rejected.

Initial 15-minute / keep-96 values are a configurable engineering baseline. Tests protect configured semantics, not those values as trading-policy constants.

## Risk / execution / session tests

Risk tests cover frozen bands, no `$100` floor, min-lot actual risk, daily lock/reset/cooldown and 0/1 capacity. Execution tests cover positive DEMO guard, central gate, exactly-one-send, ambiguous ACK reconciliation and controller fencing. Runtime session/news tests cover frozen blackout/PRE_CLOSE/reopen rules.

## Crash / broker reconciliation

Fault injection must prove unresolved send/modify/close states survive restart without duplicate exposure. Fresh-machine certification must combine restored local context with current broker positions/orders/deals and refuse stale replay of an old OPEN/Intent into a new order.

## Discovery / promotion

Discovery accepts audited declarative primitives and enforces candidate-or-suppression liveness. Promotion enforces stage order, locked fingerprint, one-shot final holdout, explicit approval and rollback. Neither gets raw broker authority.

## CI versus controlled broker evidence

Public CI is credential-free software evidence. Authenticated GitHub backup publication, Windows MT5 acquisition, real historical broker-session evidence, fresh-machine broker reconciliation, cross-machine coordination and DEMO execution need controlled environments/credentials outside repository state.

## Evidence reporting

```text
Deterministic CI               PASS / count
StateStore integrity           PASS
Runtime checkpoint export      PASS / checkpoint SHA
Local backup catalog           PASS / catalog SHA / retained count
Latest verified checkpoint     PASS / path + checkpoint SHA
Runtime checkpoint restore     PASS / fresh DB
Remote backup publication      PENDING/PASS
Broker reconcile after restore PENDING/PASS
Historical PRE_CLOSE software  PASS
Research evidence packages     PASS
Shared controller failover     PENDING/PASS
DEMO execution                 PENDING/PASS
```

Current deterministic checkpoint after local backup cadence/retention/catalog: **202 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Release-blocking failures

At minimum:

- future-data leakage;
- optional confluence becoming hidden hard gate;
- favorable ambiguity guessing;
- stress rewriting structural geometry/original R;
- hidden walk-forward tuning or holdout bypass;
- historical session times guessed when PRE_CLOSE parity is claimed;
- dataset/evidence/package hash inconsistency accepted;
- historical acquisition silently shrinking sample or inventing spread;
- current-record or event-history corruption accepted;
- checkpoint/catalog tamper accepted;
- catalog points at an unverified/mismatched checkpoint;
- failed new backup destroys the previous known-good backup;
- financial-authority secret included in public checkpoint/catalog flow;
- stale checkpoint merged over live DB;
- restored local state treated as broker truth;
- centralized execution/DEMO guard bypass;
- duplicate/wrong-account broker write;
- split-brain controller write;
- autonomous self-promotion/broker bypass.

## Explicit non-goals

Software correctness is not profitability proof. Synthetic fixtures/schedules are not real-market validation. Checkpoints/catalogs are not broker statements and do not grant execution authority. Local backup tests do not prove remote GitHub publication or real-machine recovery.

## Open questions

- final CI coverage/static/security thresholds;
- authenticated public-safe GitHub publication test matrix;
- real fresh-machine + broker reconciliation certification matrix;
- production shared-controller failover matrix;
- controlled Windows/MT5 historical acquisition matrix;
- trustworthy historical broker-session source/version/coverage matrix;
- real-data walk-forward sample requirements;
- empirical execution-friction calibration;
- final DEMO certification/forward-evidence requirement.
