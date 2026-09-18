# GoldSwingTraderAI — System Health and Diagnostics

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Cross-subsystem health aggregation, fault severity, trading impact, recovery state and operator diagnostics.  
**Depends on:** `../00-foundation/SYSTEM_CONTRACT.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`, `../30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md`, `../20-trading-decisions/SCORING_AND_DECISION_FUSION.md`

## Purpose

This document defines how the bot reports its own health. It does **not** redefine the underlying subsystem rules that generate a fault.

Core requirement:

> **Every material system fault must identify its source, severity, trading impact and recovery state.**

This is separate from normal market decisions such as `WAIT`, `MISSED` or `OPPORTUNITY_WEAK`.

## Health states

Provisional subsystem/overall states:

```text
OK
WARN
DEGRADED
BLOCKED
ERROR
```

Suggested semantics:

- `OK` — operating normally;
- `WARN` — issue exists but material behaviour remains available;
- `DEGRADED` — optional capability/evidence is unavailable or limited;
- `BLOCKED` — safe trading authority cannot continue;
- `ERROR` — component failure; trading impact depends on the affected authority.

## Health ownership

Each subsystem defines its own failure conditions. System Health aggregates and explains them.

Examples:

- Market Data defines `DATA_STALE`;
- Risk defines `DAILY_PNL_UNKNOWN`/risk blocks;
- Execution defines `ACCOUNT_IDENTITY_MISMATCH`, `ORDER_ACK_UNKNOWN`;
- Persistence defines `STATE_CORRUPT`, backup/restore failures;
- Learning defines optional learning/model health.

This document must not create competing definitions of those faults.

## Trading impact

Every active issue should state its impact, for example:

```text
Trading impact: none
Trading impact: fundamental evidence excluded
Trading impact: new entries paused
Trading impact: all broker writes blocked pending reconciliation
```

A component can be in `ERROR` while baseline trading remains available if the component is genuinely optional and frozen contracts allow degradation.

## No silent fallback

A failed optional component must become visible as `UNKNOWN/DEGRADED`; it must not silently substitute neutral/default evidence.

Critical broker/financial/order uncertainty must fail closed according to the owning contract.

## Fault record

Fault history should retain at least:

- fault/reason code;
- subsystem;
- severity/health state;
- first seen;
- last seen;
- occurrence count;
- trading impact;
- auto-recovery/operator-action state;
- recovery timestamp/result.

## Primary and secondary issues

When multiple faults exist, the system may nominate a primary blocker by authority/severity while preserving secondary active issues.

Example:

```text
Primary: ACCOUNT_IDENTITY_MISMATCH
Secondary: QUOTE_STALE, NEWS_PROVIDER_TIMEOUT
```

The first blocker must not hide additional diagnostics.

## Recovery states

Useful recovery metadata may include:

```text
ACTIVE
RECOVERING
RECOVERED
ACTION_REQUIRED
```

Transient network/provider failures may auto-recover. Deterministic account/state-integrity mismatches should not be hidden by endless retries.

## Decision block versus system fault

Examples of normal trading decisions, **not system faults**:

- `OPPORTUNITY_WEAK`;
- `ENTRY_EXTENDED`;
- `TARGET_ROOM_POOR`;
- `NEWS_BLACKOUT` when expected policy is functioning;
- `DAILY_LOSS_LOCK` when risk policy is functioning.

Examples of system/operational faults:

- `DATA_STALE` during expected-open market;
- `ACCOUNT_IDENTITY_MISMATCH`;
- `ORDER_ACK_UNKNOWN`/reconciliation failure;
- `STATE_CORRUPT`;
- required provider unavailable/unknown safety;
- backup/restore integrity failure;
- another active execution controller when this instance expected to execute.

Final trade-decision attribution remains owned by `SCORING_AND_DECISION_FUSION.md` and the relevant risk/execution authority.

## Backup and migration health

Persistence may publish health such as:

```text
BACKUP_VERIFIED
BACKUP_STALE
BACKUP_FAILED
RESTORE_VERIFIED
RESTORE_FAILED
STATE_VERSION_INCOMPATIBLE
```

A stale/failed backup may be warning/degraded while trading continues if critical runtime state is healthy, but it must remain visible because disaster-recovery protection is reduced.

## Multi-instance health

Expose instance/controller state such as:

```text
PRIMARY_EXECUTOR
OBSERVER
RESEARCH
ANOTHER_ACTIVE_CONTROLLER
LEASE/CONTROLLER_UNKNOWN
```

Unknown controller ownership that risks duplicate writes is blocking.

## Dashboard contract

Compact healthy example:

```text
🩺 SYSTEM HEALTH
Overall          ✅ HEALTHY
MT5              ✅
Data             ✅
Risk             ✅
Execution        ✅
Persistence      ✅
Learning         ✅
Backup           ✅ VERIFIED
Critical Issues  0
Warnings         0
```

Degraded example:

```text
Overall          ⚠ DEGRADED
Macro Provider   ⚠ OFFLINE
Trading Impact   Fundamental opinion excluded
Event Safety     ✅ VERIFIED
```

Blocked example:

```text
Overall          🔴 BLOCKED
Issue            ORDER_ACK_UNKNOWN
Impact           New entries disabled
Recovery         Broker reconciliation in progress
```

Emojis are presentation markers only and must never drive logic.

## Reason consistency

Reason/fault codes should remain consistent across:

- dashboard;
- logs;
- journal;
- research attribution;
- tests.

Human explanations may be English/Roman-Urdu, but the machine-readable code remains stable.

## Tests required

- correct overall health aggregation;
- optional DEGRADED component does not falsely block baseline;
- critical broker/order uncertainty blocks;
- primary/secondary issue preservation;
- fault recovery history;
- normal WAIT is not labeled system fault;
- backup/controller health mapping;
- dashboard reason consistency;
- emoji rendering fallback does not affect logic.

## Explicit non-goals

System Health must not:

- redefine risk/execution/market rules;
- convert every losing trade into a system error;
- hide secondary faults;
- silently clear unresolved critical incidents;
- use dashboard presentation as authority.

## Open questions

- exact overall health aggregation precedence;
- fault-retention/rotation period;
- notification channels for critical incidents;
- exact operator-action/escalation wording standard.