# GoldSwingTraderAI — Session/News Provider Handoff

**Status:** PROVISIONAL
**Version:** 0.1-provider-boundary
**Authority:** Validated provider-neutral JSON handoff into session/news authorities

## Purpose

An external producer may publish one complete JSON snapshot. The bot validates
scope, schema and freshness, then delegates meaning to intelligence/news.py and
risk/permissions.py. The bot does not store provider credentials or select a
commercial vendor here.

## Handoff

~~~mermaid
flowchart TB
    PRODUCER["Accepted external producer"] --> FILE["Atomic JSON snapshot"]
    FILE --> ADAPTER["app/session_news.py"]
    ADAPTER --> FACTS["Scoped Session/News facts"]
    FACTS --> NEWS["intelligence/news.py"]
    FACTS --> SESSION["risk/permissions.py"]
    NEWS --> GATE["Recovery and execution authorities"]
    SESSION --> GATE
~~~

## Configuration

~~~text
GSTAI_SESSION_NEWS_FILE=.state/session-news.json
GSTAI_SESSION_NEWS_TTL_SECONDS=1800
~~~

The payload must be scoped to the exact account login, server and resolved
symbol. It contains schema_version 1, provider identity/health, fetched UTC,
session facts and an events array. Healthy empty events are valid only when the
producer positively knows there are no accepted events.

## Required semantics

Provider health is VERIFIED, DEGRADED, STALE, UNAVAILABLE or UNKNOWN. Timestamps
are timezone-aware UTC. Session fields include tradeable, schedule_verified,
next close, close kind, reopen facts, clean M5 count, execution normalization,
gap/reconciliation state and holiday context. Events include provider ID, title,
currency, scheduled UTC and impact.

The runtime derives tier and blackout policy from code; the file cannot override
the policy.

## Failure table

| Condition | Result |
|---|---|
| missing/unreadable/invalid JSON | UNKNOWN |
| file over bounded size | UNKNOWN |
| unsupported schema | UNKNOWN |
| wrong type or missing required field | UNKNOWN |
| account/server/symbol mismatch | UNKNOWN |
| future fetch timestamp | UNKNOWN |
| stale provider | NEWS_SAFETY_UNKNOWN |
| provider unavailable/unknown | NEWS_SAFETY_UNKNOWN |
| fresh healthy empty events | eligible for NEWS_CLEAR if session passes |

The runtime never turns an exception into an empty event list.

## Publication invariants

Producer writes a complete temporary file, flushes it and atomically replaces
the target. It preserves provider failure and keeps credentials outside the
payload/repository. Rewriting an old payload does not extend its real fetch
time.

## Source and tests

app/session_news.py owns parsing/scope/freshness. intelligence/news.py owns
event normalization. risk/permissions.py owns hard result. Tests are
test_session_news_provider.py, test_session_news_permissions.py and
test_live_startup_runtime.py.

## Explicit non-goals

No provider credentials, broker/session replacement, silent NEWS_CLEAR fallback,
or broker write authority.

