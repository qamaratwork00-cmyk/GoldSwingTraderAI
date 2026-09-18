# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 1.5-design  
**Authority:** Test taxonomy, executable proof requirements, replay/live parity, research data/evidence integrity, historical session-policy replay, portable runtime recovery, crash/restart, migration, learning-governance and release verification.  
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
→ Persistence / Runtime Checkpoint / Restore / Fault Injection
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

`StateStore` tests must prove:

- current record canonical JSON/checksum integrity;
- append-only event payload checksum/JSON/timestamp integrity;
- database schema-version enforcement;
- event ordering is durable;
- corruption never becomes empty/default runtime state;
- snapshot export includes all current records and ordered event history;
- snapshot restore requires an empty target store.

## Portable runtime checkpoint tests

`persistence/checkpoint.py` must prove:

- checkpoint uses exactly `checkpoint_manifest.json`, `records.jsonl`, `events.jsonl`;
- checkpoint destination is write-new and never overwritten;
- source `StateStore.integrity_check()` occurs before export;
- current records and append-only events both round-trip;
- record/event original checksums, timestamps and event IDs are preserved;
- file hashes and `checkpoint_sha256` detect tamper;
- file counts match manifest counts;
- unsupported schema/canonical filename/file-set/symlink violations fail;
- structured payload scan blocks authority-bearing password/token/key fields with `FINANCIAL_SECRET_DETECTED`;
- failed secret export leaves no completed checkpoint artifact;
- repository text scanner remains fixture-safe while structured artifact scanner is strict;
- restore requires a non-existing destination database;
- restore builds/validates a temporary StateStore before atomic handoff;
- restored database passes full integrity check;
- typed `RuntimeStateRepository` state remains readable after fresh-database restore;
- generic additional namespaces such as learning state survive without a second per-feature backup schema;
- restore result explicitly reports `broker_reconciliation_required=True`.

A deterministic checkpoint restore is **not** permission to trade. Real broker reconciliation must occur before READY.

## Risk / execution / session tests

Risk tests cover frozen bands, no `$100` floor, min-lot actual risk, daily lock/reset/cooldown and 0/1 capacity. Execution tests cover positive DEMO guard, central gate, exactly-one-send, ambiguous ACK reconciliation and controller fencing. Runtime session/news tests cover frozen blackout/PRE_CLOSE/reopen rules.

## Crash / broker reconciliation

Fault injection must prove unresolved send/modify/close states survive restart without duplicate exposure. Fresh-machine certification must combine restored local context with current broker positions/orders/deals and refuse stale replay of an old OPEN/Intent into a new order.

## Discovery / promotion

Discovery accepts audited declarative primitives and enforces candidate-or-suppression liveness. Promotion enforces stage order, locked fingerprint, one-shot final holdout, explicit approval and rollback. Neither gets raw broker authority.

## CI versus controlled broker evidence

Public CI is credential-free software evidence. Windows MT5 acquisition, real historical broker-session evidence, fresh-machine broker reconciliation, cross-machine coordination and DEMO execution need controlled environment evidence with credentials outside the repository.

## Evidence reporting

```text
Deterministic CI               PASS / count
StateStore record integrity    PASS
StateStore event integrity     PASS
Runtime checkpoint export      PASS / checkpoint SHA
Runtime checkpoint restore     PASS / fresh DB
Broker reconcile after restore PENDING/PASS
Historical PRE_CLOSE software  PASS
Research evidence packages     PASS
Windows MT5 real history       PENDING/PASS
Shared controller failover     PENDING/PASS
DEMO execution                 PENDING/PASS
```

Current deterministic checkpoint after portable runtime recovery foundation: **195 tests PASS**, Ruff PASS and financial-secret scan PASS.

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
- checkpoint manifest/file/record/event tamper accepted;
- financial-authority secret included in public checkpoint;
- stale checkpoint merged over live DB;
- restored local state treated as broker truth;
- centralized execution/DEMO guard bypass;
- duplicate/wrong-account broker write;
- split-brain controller write;
- autonomous self-promotion/broker bypass.

## Explicit non-goals

Software correctness is not profitability proof. Synthetic fixtures/schedules are not real-market validation. Portable checkpoints are not broker statements and do not grant execution authority.

## Open questions

- final CI coverage/static/security thresholds;
- automatic checkpoint cadence/retention tests;
- public-safe checkpoint publication/catalog tests;
- real fresh-machine + broker reconciliation certification matrix;
- production shared-controller failover matrix;
- controlled Windows/MT5 historical acquisition matrix;
- trustworthy historical broker-session source/version/coverage matrix;
- real-data walk-forward sample requirements;
- empirical execution-friction calibration;
- final DEMO certification/forward-evidence requirement.
