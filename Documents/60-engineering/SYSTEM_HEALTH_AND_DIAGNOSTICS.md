# GoldSwingTraderAI — System Health and Diagnostics

**Status:** CANDIDATE FOR ADOPTION  
**Version:** 0.1-health-contract  
**Authority:** Operational visibility, reason semantics and diagnostic boundaries

## 1. Why this document exists

Health is not a trading signal. Health answers a different question:

> Can the system currently trust the information, the account identity, the
> durable state and the authority required for the next safe action?

This distinction matters. A market can look attractive while the broker
connection is unavailable. A process can be alive while its data is stale. A
controller can be running while it no longer owns the write authority. The
system must show these facts separately instead of compressing them into one
misleading green light.

The health contract is used by the runtime, dashboard, structured logs,
recovery flow and release evidence.

## 2. Health topology

~~~mermaid
flowchart TB
    PROC["Process heartbeat"] --> HEALTH["Health snapshot"]
    BROKER["MT5 connection and identity"] --> HEALTH
    DATA["Market freshness and completeness"] --> HEALTH
    STATE["SQLite state and checkpoint"] --> HEALTH
    AUTH["Controller lease and fencing"] --> HEALTH
    PROVIDERS["Session/news provider health"] --> HEALTH
    HEALTH --> DASH["Dashboard and reasons"]
    HEALTH --> LOG["Structured logs"]
    HEALTH --> GATE["Execution gate input"]
    HEALTH --> RECOVERY["Recovery decision"]
~~~

The health snapshot describes conditions. The execution gate remains the
authority that decides whether a broker write may happen.

## 3. Health dimensions

| Dimension | Healthy means | Degraded or blocked means | Safe response |
|---|---|---|---|
| Process | The loop is alive and its heartbeat advances | The loop is late, stopped or cannot complete a cycle | Keep broker writes disabled and investigate |
| MT5 | The terminal is initialized and the expected account/server is known | Terminal unavailable, identity mismatch or symbol unavailable | Block all writes; retain the reason |
| Market data | Quote and required completed candles satisfy freshness rules | STALE, INSUFFICIENT, SPARSE, CORRUPT or UNKNOWN | Continue a visible wait when configured; never trade on guessed freshness |
| Persistence | SQLite opens, integrity checks pass and schemas decode | Corrupt state, failed transaction or incompatible record | Enter recovery; do not replace truth with empty state |
| Authority | The runtime has the correct role and a valid lease/fence | Another controller is active, coordination is unknown or lease is expired | Remain standby/recovering; no broker write |
| Provider | Session/news inputs are valid for the configured policy | Missing, stale or contradictory provider data | Apply the hard session/news state |
| Reconciliation | Local Intent, managed trade state and broker truth agree | Acknowledgement is unknown or reconciliation failed | Reconcile before any next write |
| Research | Evidence identity and data lineage are known | Dataset, code fingerprint or holdout lineage is missing | Research output cannot promote a live rule |

## 4. Do not confuse these states

The project deliberately has several vocabularies. They answer different
questions.

| Vocabulary | Question answered | Examples |
|---|---|---|
| DataQuality | Can the market facts be used? | HEALTHY, STALE, SPARSE, CORRUPT |
| MarketState | What is the broker/session calendar state? | OPEN, PRE_CLOSE, CLOSED, REOPEN_WARMUP |
| NewsSafetyState | Is event risk clear? | NEWS_CLEAR, NEWS_BLACKOUT, NEWS_SAFETY_UNKNOWN |
| RiskState | Is monetary risk allowed? | NORMAL, LOSS_LOCKED, COOLDOWN, BLOCKED |
| ExecutionState | Can the execution subsystem act? | READY, DEGRADED, RECONCILING, BLOCKED |
| RuntimeRole | What role does this process hold? | PRIMARY, STANDBY, OBSERVER, RECOVERING |
| ReasonCode | Why did a state or decision occur? | DATA_STALE, MARGIN_INSUFFICIENT, RECONCILIATION_FAILED |

For example, CLOSED is not the same as DATA_STALE. The market may be closed
with a perfectly valid last completed candle. A stale quote during an open
session is a different problem.

## 5. Reason semantics

Every operator-visible block or degradation should carry:

1. a stable machine-readable ReasonCode;
2. a short human-readable explanation;
3. the relevant scope, such as symbol, account, episode or Intent;
4. the observed value and the threshold when that comparison matters;
5. the next safe action, if one exists;
6. the timestamp of the observation.

Good diagnostic message:

> DATA_STALE — XAUUSDm quote age is 47,298 seconds; maximum is 10 seconds.
> Entry writes remain disabled. Refresh MT5 history and verify the terminal
> clock/feed.

Bad diagnostic message:

> Something went wrong.

Reason codes are part of the public operational contract. Renaming a reason
requires updating code, tests, dashboard mappings, documentation and release
evidence together.

## 6. Health snapshot lifecycle

~~~mermaid
sequenceDiagram
    participant LOOP as Runtime loop
    participant READ as MT5 read boundary
    participant STORE as State store
    participant AUTH as Authority service
    participant DTO as Dashboard DTO
    LOOP->>READ: collect account, quote, candles and positions
    LOOP->>STORE: verify durable state and latest checkpoint
    LOOP->>AUTH: read role, lease and fencing status
    READ-->>LOOP: facts plus data-quality result
    STORE-->>LOOP: integrity and restore status
    AUTH-->>LOOP: authority status
    LOOP->>DTO: compose health and reason facts
    DTO-->>LOOP: renderable operator snapshot
~~~

The loop may collect independent facts in parallel, but the final health
snapshot is assembled in a deterministic order so a dashboard frame can be
explained and replayed.

## 7. Runtime health rules

- A live process is not proof of a live trading system.
- A successful MT5 read is not proof that the data is fresh.
- A DEMO account identity is not proof that the write path is enabled.
- A valid local checkpoint is not proof that broker truth matches it.
- A healthy dashboard render is not proof that a broker write is permitted.
- UNKNOWN is never silently converted to PASS.
- Missing diagnostics are themselves a health defect.
- Health must degrade visibly before it becomes a safety block when that is
  possible; the final broker gate still applies the hard boundary.

## 8. Logging and redaction

Structured logs are for event reconstruction, not for dumping objects.

Each important lifecycle event should include an event name, UTC timestamp,
scope, stable IDs, state transition and reason codes. It must not include
passwords, access tokens, account credentials, full connection strings or
unredacted financial secrets.

Recommended event families include:

- RUNTIME_START, RUNTIME_HEARTBEAT and RUNTIME_STOP;
- MARKET_SNAPSHOT_READY and MARKET_DATA_DEGRADED;
- RECOVERY_STARTED, RECOVERY_BLOCKED and RECOVERY_COMPLETE;
- CONTROLLER_ACQUIRED, CONTROLLER_RENEWED and CONTROLLER_LOST;
- INTENT_CREATED, INTENT_SENT, INTENT_ACK_UNKNOWN and INTENT_RECONCILED;
- DASHBOARD_FRAME_READY;
- BACKUP_CREATED and BACKUP_PUBLIC_STAGED.

## 9. Failure handling

| Failure | Diagnostic truth | Runtime response |
|---|---|---|
| MT5 init fails | MT5_UNAVAILABLE or MT5_NOT_INITIALIZED | Retry only under the startup policy; no writes |
| Account/server mismatch | ACCOUNT_IDENTITY_MISMATCH | Hard block; operator must correct configuration |
| Freshness fails | DATA_STALE | Keep the runtime visible; wait or recover according to mode |
| SQLite integrity fails | STATE_CORRUPT | Enter recovery; do not create a new empty state silently |
| Controller lease disappears | CONTROLLER_OWNERSHIP_UNKNOWN or ANOTHER_ACTIVE_CONTROLLER | Fence this process and stop writes |
| Broker acknowledgement is unclear | ORDER_ACK_UNKNOWN | Reconcile broker truth before retry |
| Provider input is missing | NEWS_SAFETY_UNKNOWN or SESSION_SCHEDULE_UNKNOWN | Apply the configured hard safety state |
| Dashboard mapping fails | Diagnostic/rendering failure | Preserve the underlying safety state and log the mapping error |

## 10. Source and proof map

| Concern | Implementation | Main proof |
|---|---|---|
| Stable states | domain/enums.py | tests/test_models.py |
| Stable reasons | diagnostics/reasons.py | tests/test_logging.py |
| Redacted structured logs | diagnostics/logging.py | tests/test_logging.py, tests/test_secret_scanner.py |
| Market freshness | market_data/mt5_reader.py and market_data/snapshot.py | tests/test_market_data.py |
| Runtime health mapping | app/dashboard.py and operator/dashboard.py | tests/test_app_readiness.py, tests/test_dashboard.py |
| Recovery health | app/recovery.py and app/recovery_mt5.py | tests/test_startup_recovery.py, tests/test_recovery_mt5.py |
| Authority health | execution/controller.py and execution/sqlite_coordination.py | tests/test_sqlite_coordination.py |
| Intent/reconciliation health | execution/service.py and execution/reconcile.py | tests/test_execution_safety.py |

The health document describes the diagnostic contract; it does not authorize
changing the safety policy. Policy changes belong in the relevant domain
contract and the design decision ledger.
