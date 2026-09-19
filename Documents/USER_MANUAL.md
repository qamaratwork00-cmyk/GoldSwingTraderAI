# GoldSwingTraderAI — User Manual

**Status:** CANDIDATE FOR ADOPTION
**Version:** 0.1-user
**Authority:** Plain-language operator behaviour and status interpretation

## Daily workflow

1. Open MT5 and connect the intended DEMO account.
2. Start the bot in READINESS.
3. Confirm symbol, DEMO Guard, identity and data quality.
4. Use PRIMARY only after state/provider/recovery configuration is ready.
5. Watch reasons, not just colours.
6. Let the bot manage through the governed path.
7. Use safe shutdown; do not delete critical state.

## If the market is closed

The bot should remain visible but inactive:

~~~text
stale/insufficient/sparse data
→ monitor remains alive
→ strategy not run
→ broker writes disabled
→ bounded poll
→ fresh data
~~~

This is safe waiting, not a signal. Corrupt data, identity mismatch, DEMO
failure, unknown session/news or persistence/controller faults require review
instead of endless permissive retry.

## What a normal cycle means

~~~mermaid
flowchart TB
    START["Startup READY"] --> MARKET["Fresh market and session/news facts"]
    MARKET --> IDEA["Intelligence + six families + BUY/SELL"]
    IDEA --> PLAN["Trade Plan"]
    PLAN --> SAFETY["Risk, permission, DEMO and controller"]
    SAFETY --> ACTION{"Result"}
    ACTION -->|"WAIT/BLOCK/INVALID"| REASON["No broker write; reason remains visible"]
    ACTION -->|"ENTER"| WRITE["One governed broker action and verification"]
    WRITE --> MANAGE["HOLD/PROTECT/TRAIL/RUNNER/EXIT"]
~~~

## Main status meanings

| Status | Meaning |
|---|---|
| ENTER BUY/SELL | analytical and hard authorities allowed the current action |
| WAIT | idea may survive; current timing/geometry is not good enough |
| MISSED | executable window passed; no blind chase |
| INVALID | thesis/structure failed |
| BLOCKED | hard authority prevents action |
| OPEN TRADE | Trade Manager owns a verified bot position |

## Common no-trade reasons

| Reason | Plain meaning |
|---|---|
| ENTRY_EXTENDED | idea may be valid, current entry is late |
| TARGET_ROOM_POOR | structural path does not offer enough room |
| NEWS_BLACKOUT | scheduled safety window |
| SESSION_PRE_CLOSE | known XAU close is near |
| MIN_LOT_UNAFFORDABLE | broker minimum makes this plan too risky |
| SPREAD_TOO_HIGH | current friction is excessive |
| PRICE_DRIFT | quote moved too far from approved reference |
| POSITION_CAPACITY_FULL | one V1 Gold risk position already exists |
| EXTERNAL_GOLD_EXPOSURE | manual/foreign position is unresolved |
| DATA_STALE | required market facts are not fresh |
| ANOTHER_ACTIVE_CONTROLLER | another runtime owns write authority |

A normal policy block is not automatically a software fault.

## DEMO Guard

Writes require:

~~~text
DEMO account verified
+ account/symbol identity correct
+ risk/session/news/data/position/controller pass
+ central gate ALLOW
~~~

READINESS is read-only even when DEMO Guard passes.

## Strategy and confluence

Six families evaluate independently. One coherent family may lead. Trendline,
Fibonacci and POC are optional confluence; missing confluence is not a failure
and POC is not a direction signal alone.

## Risk and open trades

Risk profiles are SMALL positive below 300, MEDIUM 300–999.99 and NORMAL 1000+.
There is no 100-dollar floor. Daily loss lock stops new entries; safe
management may continue. One ordinary loss does not create global cooldown.

Open-trade actions are HOLD, PROTECT, TRAIL, RUNNER and EXIT. Small profit or
one opposite candle does not automatically close a healthy move. PRE_CLOSE
flatten is mandatory when the verified schedule requires it.

## Backups and laptop change

Restore context, configure credentials separately, connect the intended DEMO
terminal and reconcile current broker truth before new writes. A backup cannot
prove that the broker has no open position.

## Never do manually

Do not edit Intent, risk lock, managed trade, promotion, controller or critical
SQLite records to make a screen look healthy. Use the governed recovery path.

## Evidence boundary

Tests prove software. Replay proves a declared simulation. Only the final audit
can report what connected MT5 DEMO, restart and failover drills actually proved.

