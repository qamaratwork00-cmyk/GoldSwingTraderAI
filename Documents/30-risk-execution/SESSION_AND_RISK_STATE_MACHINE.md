# GoldSwingTraderAI — Session, News and Risk State Machine

**Status:** PROVISIONAL
**Version:** 0.1-permission-states
**Authority:** Hard market/session/news/risk/system permission composition

## Purpose

This document defines hard permission states between facts and the central
execution gate. It does not calculate strategy scores or select a provider.

## State families

~~~mermaid
flowchart TB
    MARKET["Market schedule"] --> COMPOSE["Permission composition"]
    NEWS["News safety"] --> COMPOSE
    RISK["Risk state"] --> COMPOSE
    SYSTEM["Data, account, position, controller"] --> COMPOSE
    COMPOSE --> DECISION{"Every required authority passes?"}
    DECISION -->|"yes"| ALLOW["Candidate may reach gate"]
    DECISION -->|"no/unknown"| BLOCK["New entry BLOCK/UNKNOWN"]
    MARKET --> MANAGE["Open-trade management"]
    NEWS --> MANAGE
    RISK --> MANAGE
~~~

## Market states

~~~text
OPEN
PRE_CLOSE
CLOSED
REOPEN_WARMUP
HOLIDAY_CAUTION
UNKNOWN
~~~

Verified broker schedule controls the transitions:

~~~text
Daily:   T-20m no entry, T-10m mandatory flatten
Weekend: T-60m no entry, T-30m mandatory flatten
~~~

After daily reopen, one clean completed M5 plus normalized execution/data is
required. After weekend reopen, gap assessment, normalized conditions and two
clean completed M5 candles are required. Holiday context never proves closure.

PRE_CLOSE flatten uses the normal gate, Intent, writer and reconciliation path.
If acknowledgement is ambiguous, exposure remains unresolved.

## News states

~~~text
NEWS_CLEAR
NEWS_BLACKOUT
NEWS_SAFETY_UNKNOWN
POST_NEWS_WARMUP
~~~

Tier 1 blocks -15/+15; Tier 2 blocks -5/+5; Tier 3 has no automatic hard
blackout. Scheduled news does not automatically close an existing trade.
Missing/stale provider truth is UNKNOWN, never clear.

## Risk/system states

~~~text
NORMAL
LOSS_LOCKED
COOLDOWN
BLOCKED
UNKNOWN
~~~

LOSS_LOCKED blocks new entries but safe management may continue. COOLDOWN after
three losses also requires fresh context, fresh opportunity and no unresolved
fault. Account identity mismatch, corrupt persistence, unknown exposure,
unknown controller or unresolved order lifecycle are hard BLOCK/UNKNOWN.

## Composition examples

| Conditions | New entry | Existing trade |
|---|---|---|
| OPEN + NEWS_CLEAR + NORMAL + all authorities pass | may reach ALLOW | normal management |
| PRE_CLOSE | blocked | mandatory flatten |
| CLOSED | blocked | reconcile unresolved exposure |
| REOPEN_WARMUP | blocked | safe management/reconcile |
| NEWS_BLACKOUT | blocked | not automatically closed |
| LOSS_LOCKED | blocked | management continues safely |
| unknown required truth | fail closed | preserve/reconcile |

## Implementation and tests

risk/permissions.py owns BrokerSessionFacts, MarketPermission,
NewsPermission and SessionNewsPermission. app/session_news.py supplies
validated provider facts. execution/gate.py composes them with account,
position, risk and controller traces.

Tests: test_session_news_permissions.py, test_session_news_provider.py,
test_execution_safety.py and test_live_startup_runtime.py.

## Dashboard/replay

Show market state, news state, countdown, risk lock/cooldown, reopen progress,
primary/secondary blocker and flatten status. Replay reuses the same policy and
must not guess an uncovered historical schedule.

## Explicit non-goals

This state machine does not source a commercial provider, create a strategy
veto, recalculate daily loss or perform broker writes.

