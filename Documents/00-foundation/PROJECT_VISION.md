# GoldSwingTraderAI — Project Vision

**Status:** PROVISIONAL
**Version:** 0.1-foundation
**Authority:** Product purpose, trading personality and non-goals

## Reader promise

After reading this document, a new contributor should understand what the bot is
trying to do, what “good” means, and why the project has separate intelligence,
decision, risk, execution, recovery and research layers.

## What we are building

GoldSwingTraderAI is a fresh XAUUSD/XAUUSDm system for meaningful intraday and
open-session directional moves. It is designed to participate in a healthy
move, not to scalp every small fluctuation and not to wait only for a perfect
checklist that almost never appears.

The system must:

1. read trustworthy MT5 and completed-candle facts;
2. understand structure, location, liquidity, volatility and session context;
3. let six independent strategy families propose BUY and SELL hypotheses;
4. separate opportunity quality from current M5 entry timing;
5. construct a structural Trade Plan before account sizing;
6. apply hard monetary, session/news, identity, controller and broker checks;
7. submit at most one governed broker operation and verify its outcome;
8. manage an open position around structure and objective progression;
9. preserve state, evidence and reasoning through restart and migration;
10. improve only through offline evidence and explicit promotion.

## Product philosophy

~~~mermaid
flowchart TB
    FACTS["Observe facts"] --> EVIDENCE["Explain behaviour"]
    EVIDENCE --> HYPOTHESES["Compare six hypotheses"]
    HYPOTHESES --> PLAN["Create structural plan"]
    PLAN --> SAFETY["Check hard authorities"]
    SAFETY --> ACTION["Act once if allowed"]
    ACTION --> MEMORY["Reconcile and learn"]
~~~

The product optimizes for:

- clear reasoning rather than opaque single scores;
- healthy valid-opportunity coverage rather than maximum filtering;
- structural invalidation rather than arbitrary fixed-pip stops;
- large-move capture rather than tiny-profit reflexes;
- fail-closed financial safety rather than optimistic defaults;
- recoverable state rather than process-local assumptions.

## Timeframe roles

| Timeframe | Role | Typical facts |
|---|---|---|
| H4 | broad regime | major structure, external liquidity, macro location |
| H1 | directional context | trend/transition, higher-timeframe structure and path |
| M15 | opportunity frame | location, target room, break/retest/sweep context |
| M5 | entry frame | trigger, reclaim, rejection, timing and chase control |
| M1 | diagnostic only | execution telemetry unless a later governed change promotes it |

Completed candles are the structural clock. A forming candle can be displayed
or used for explicitly documented live execution checks, but it cannot silently
become confirmed historical structure.

## What accuracy means here

Accuracy is not defined as “take fewer trades.” A valid improvement should be
judged using multiple measures:

- Net R and Average R;
- drawdown and loss-streak behaviour;
- Opportunity Recall and missed meaningful moves;
- entry efficiency and capture efficiency;
- premature-exit cost and runner quality;
- trade frequency and execution friction;
- robustness across regimes, directions and sessions.

A high win rate produced by removing most valid opportunities is not
automatically an improvement.

## Fixed product boundaries

The V1 product includes six families:

1. Trend Pullback Continuation.
2. Breakout Expansion.
3. Breakout Retest Continuation.
4. Liquidity Sweep Reversal.
5. Failed Breakout Reversal.
6. Compression Expansion.

Trendline, Fibonacci and broker-local POC are optional bonus/context evidence.
They are not a seventh mandatory family and cannot become universal hard gates
without a new governed decision.

The bot uses a structural objective hierarchy:

~~~text
Immediate Obstacle → Primary Target → Expansion Target → Runner Objective
~~~

There are no fixed 100/200/300-pip take-profit rules. A normal V1 position can
be managed with one indivisible broker-minimum volume; partial closes are not a
core dependency.

## Safety philosophy

Safety does not compete in the soft score:

~~~text
analysis → Trade Plan → risk/session/news → DEMO/account/controller
→ central gate → one intent → one MT5 write → reconciliation
~~~

V1 broker-write environment permission is positive DEMO verification only:

~~~text
Connected MT5 account is verified DEMO → DEMO_GUARD = PASS
~~~

No configuration flag may turn this guard off. V1 does not define a separate
REAL authorization workflow.

## Non-goals

- no profit, win-rate or future-return guarantee;
- no fixed daily trade quota;
- no martingale or averaging down to rescue a thesis;
- no arbitrary positive-account minimum balance floor;
- no hidden strategy-to-broker shortcut;
- no blind retry after an ambiguous broker acknowledgement;
- no automatic hedge/second independent Gold risk position in V1;
- no arbitrary generated executable strategy code;
- no autonomous research self-promotion;
- no silent reset of critical state after restart.

## Proof boundary

The vision is validated in layers:

| Evidence | Proves | Does not prove |
|---|---|---|
| deterministic tests | software contract and failure handling | broker conditions or profitability |
| chronological replay | declared historical simulation | future return |
| connected MT5 readiness | account/symbol/read boundary in that environment | write lifecycle |
| controlled DEMO lifecycle | exact broker/runtime scenario tested | all future environments |
| final release audit | evidence assembled for one build | permanent correctness |

The remaining documents explain how each layer is implemented and proven.

