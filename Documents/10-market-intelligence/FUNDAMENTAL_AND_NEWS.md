# GoldSwingTraderAI — Fundamental and News Intelligence

**Status:** PROVISIONAL
**Version:** 0.1-news-facts
**Authority:** Macro context, scheduled-event facts, tiering and provider health

## Two products, not one

Macro opinion and event-safety truth have different jobs:

~~~mermaid
flowchart TB
    PROVIDER["External producer or validated file"] --> HANDOFF["app/session_news.py — scope, schema and freshness"]
    HANDOFF --> NORMALIZE["intelligence/news.py — event identity, tier and window"]
    NORMALIZE --> CONTEXT["NewsFacts and macro context"]
    NORMALIZE --> PERMISSION["risk/permissions.py — hard news permission"]
    CONTEXT --> DECISION["Strategy and explanation"]
    PERMISSION --> GATE["Central execution gate"]
~~~

The intelligence layer never turns a provider file into a broker write.

## Macro context

Possible soft inputs include USD/DXY, Treasury yields, rate expectations, Fed
policy, inflation/labour data, risk sentiment and geopolitical stress. These
are context; price/structure remains primary. Missing macro opinion is not the
same as missing required event-safety truth.

## Event tiers

Tier 1 baseline concepts include FOMC/rate decisions, Fed Chair communication,
CPI and NFP/Core PCE concepts. Window: 15 minutes before through 15 minutes
after. Linked critical events merge through the final item.

Tier 2 includes PPI, Retail Sales, GDP, ISM, JOLTS, ADP and jobless/unemployment
claims where accepted as high impact. Window: 5 minutes before through 5
minutes after.

Tier 3 is contextual and has no automatic hard blackout in V1.

## Provider health

~~~text
VERIFIED | DEGRADED | STALE | UNAVAILABLE | UNKNOWN
~~~

No fetch time, stale required data or provider failure becomes
NEWS_SAFETY_UNKNOWN. A healthy fresh empty events list is different: it means
the provider positively reported no accepted events.

## Implementation and tests

| Source | Responsibility | Tests |
|---|---|---|
| intelligence/news.py | normalize events, tier and windows | test_intelligence_snapshot.py, test_session_news_permissions.py |
| app/session_news.py | provider-neutral JSON handoff | test_session_news_provider.py |
| risk/permissions.py | hard NEWS_CLEAR/BLACKOUT/UNKNOWN/WARMUP | test_session_news_permissions.py |

## Hard handoff

The risk/session authority owns:

~~~text
NEWS_CLEAR
NEWS_BLACKOUT
NEWS_SAFETY_UNKNOWN
POST_NEWS_WARMUP
~~~

Scheduled news blocks new entries but does not automatically close an open
managed trade. Severe post-event dislocation requires normalized execution
conditions and a clean completed M5 before new entry resumes.

## Replay and operator boundary

Historical replay uses event facts as knowable at decision time, preserving
mapping version and provider assumptions. The dashboard shows event title,
tier/countdown, provider health and hard permission from risk; it does not
recreate permission in the UI.

## Explicit non-goals

This document does not select a commercial provider, store credentials,
replace MT5 session truth, guarantee breaking-news awareness or force-close
positions merely because a calendar event is scheduled.

