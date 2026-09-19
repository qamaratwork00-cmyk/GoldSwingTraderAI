# GoldSwingTraderAI — Session Context

**Status:** PROVISIONAL
**Version:** 0.1-session
**Authority:** Timezone-safe session labels, ranges and participation context

## Question answered

What session and intraday range context was observable at the time, without
pretending that a holiday label or local clock proves broker tradeability?

## Context pipeline

~~~mermaid
flowchart TB
    UTC["Completed-candle UTC timestamps"] --> ZONE["zoneinfo — DST-safe conversion"]
    ZONE --> LABEL["ASIA / LONDON / NEW_YORK / OVERLAP / OFF_HOURS"]
    LABEL --> RANGE["Current and previous session high/low/range"]
    RANGE --> REPORT["SessionReport + coverage + holiday context"]
    REPORT --> INTEL["Technical, liquidity and strategy context"]
    REPORT -.-> HARD["Risk/permissions owns broker OPEN/CLOSED"]
~~~

## Session labels

~~~text
ASIA
LONDON
NEW_YORK
LONDON_NY_OVERLAP
OFF_HOURS
~~~

The initial baseline uses Asia 00:00–08:00 UTC, London 08:00–16:00
Europe/London local time and New York 08:00–17:00 America/New_York local time.
zoneinfo handles daylight saving changes.

## Published facts

- current session;
- overlap;
- current session high/low/range where known;
- previous session high/low where known;
- holiday context;
- evidence coverage.

Session context is soft evidence. Asia compression, London expansion or New
York continuation/reversal are observations, not universal rules.

## Hard boundary

This desk does not own broker OPEN/CLOSED, PRE_CLOSE, reopen warm-up, daily
loss, cooldown or news permission. Those belong to
30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md.

Holiday context does not equal closure. Broker tradeability and current quotes
remain authoritative.

## Implementation and tests

intelligence/session.py owns conversion and ranges. intelligence/snapshot.py
attaches the result to the shared snapshot. Tests are in
test_intelligence_snapshot.py and cover DST, overlap, chronological ranges and
holiday-not-closure semantics.

## Replay/dashboard

Replay uses the same UTC and zoneinfo path. The dashboard may show session,
overlap and range state as context. A session label must never be rendered as
an execution permission.

