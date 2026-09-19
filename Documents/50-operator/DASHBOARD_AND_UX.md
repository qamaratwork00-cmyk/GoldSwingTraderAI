# GoldSwingTraderAI — Dashboard and UX

**Status:** PROVISIONAL
**Version:** 0.1-dashboard
**Authority:** Operator visibility, DTO mapping and terminal presentation

## Purpose

The dashboard answers “what is happening, why, and what should I understand
next?” It observes authoritative state. It never creates strategy, risk or
broker permission.

## Presentation flow

~~~mermaid
flowchart TB
    AUTHORITIES["Market, decision, risk, execution, recovery and research facts"] --> DTO["app/dashboard.py — typed DTO mapping"]
    DTO --> RENDER["operator/dashboard.py — pure renderer"]
    RENDER --> SCREEN["Terminal display"]
    SCREEN -.-> ACTION["Safe operator workflow only"]
~~~

The mapper may format or select values. It must not recalculate risk, infer a
blocker, invoke MT5 or trigger a decision.

## Readiness frame

Before a governed cycle exists, the screen uses a separate frame:

~~~mermaid
flowchart TB
    SNAP["MarketSnapshot"] --> MAP["build_readiness_dashboard_data"]
    MAP --> FRAME["ReadinessDashboardData"]
    FRAME --> VIEW["render_readiness_dashboard"]
~~~

It shows project, symbol, account mode, DEMO Guard, identity, UTC time,
Bid/Ask/spread, quote age, DataQuality, H4/H1/M15/M5 completed counts, exact
issues, next poll, STRATEGY NOT RUN and BROKER WRITES DISABLED.

It does not invent score, risk, session/news permission or execution state.

## Full-cycle panels

| Panel | Must show |
|---|---|
| Market | symbol, Bid/Ask, spread, timer, H4/H1/M15/M5 structure, EMA/RSI/ATR, session/news |
| Decision | BUY, SELL, edge, conflict, opportunity, timing, coverage, family and reason |
| Trade Plan | entry reference, invalidation/SL, targets, RR, original R |
| Risk | profile, lot, all-in risk, ceiling, day safety P/L, lock, cooldown, capacity |
| Execution | DEMO, controller/epoch, gate result, Intent, reconciliation and reason |
| Open trade | direction, entry/current price, original/current SL/TP, objectives, R, manager action |
| Learning | memory, entry/exit learning, Champion/Challenger, discovery health |
| State/backup | integrity, checkpoint, catalog, restore/reconciliation |
| Health | overall state, primary/secondary fault and recovery action |

Useful prior Gold observability must remain: account mode, DEMO, XAU symbol,
Bid/Ask, spread, M5 countdown, structure, EMA20/50, RSI, ATR, reason,
risk/lot, day P/L, position count, loss streak and open-trade context.

## Meaning of colours/reasons

Stable machine reason codes are primary. Human explanations may be concise
English or Roman Urdu, but must not change the code’s meaning.

~~~text
WAIT      → analytical idea may survive
BLOCKED   → hard authority prevents action
DEGRADED  → optional/system capability is limited
ERROR     → component failure needs recovery
~~~

NEWS_BLACKOUT, LOSS_LOCKED and PRE_CLOSE are not automatically software faults.

## Optional confluence

Display Trendline/Fibonacci/POC compactly and label POC source:

~~~text
Trendline M15 SUPPORT TOUCH | Fib BUY 0.618 | POC NEAR (tick-volume)
~~~

Missing confluence displays as unavailable context, not a red mandatory gate.

## Runtime roles

Show PRIMARY, STANDBY, OBSERVER, RESEARCH and RECOVERING/RECONCILING. Only
controller/execution authorities decide write capability.

## Operator controls

Keep the main screen read-only. Governed controls may include safe shutdown,
manual-loss-reset confirmation where enabled, export and restore workflows.
Do not add casual “force entry”, “ignore safety” or “promote candidate” buttons.

## Source and tests

app/dashboard.py maps runtime facts. operator/dashboard.py renders full and
readiness DTOs. operator/__init__.py exposes the presentation API.

Tests: test_dashboard.py and test_app_readiness.py. Source-level tests ensure
the renderer does not import raw broker/risk/execution authority.

## Explicit non-goals

No second policy, raw MT5 call, risk recalculation, hidden blocker, mandatory
confluence gate or UI framework without a real requirement.

