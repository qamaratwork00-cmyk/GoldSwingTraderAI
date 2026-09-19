# GoldSwingTraderAI — Entry Timing and Opportunity Lifecycle

**Status:** PROVISIONAL
**Version:** 0.1-timing
**Authority:** Opportunity persistence and current M5 entry timing

## Two questions

Opportunity asks: “Is this market idea worth keeping?”

Entry Timing asks: “Is this M5 moment efficient enough to enter?”

They must remain separate so a valid idea survives a temporarily late or
extended candle.

## Lifecycle

~~~mermaid
stateDiagram-v2
    [*] --> DISCOVERED
    DISCOVERED --> ARMED: thesis passes opportunity threshold
    ARMED --> WAITING: timing weak or extended
    WAITING --> READY: fresh M5 evidence and plan quality
    ARMED --> READY: trigger appears
    READY --> TRIGGERED: governed execution verified
    READY --> MISSED: window expires
    MISSED --> ARMED: genuinely fresh event
    ARMED --> INVALIDATED: thesis fails
    WAITING --> STALE: lifecycle age/conditions expire
~~~

READY means analytically ready. It does not mean Risk, Session/News, DEMO,
Controller and Execution Gate have passed.

## State meanings

| State | Meaning | Durable obligation |
|---|---|---|
| DISCOVERED | first coherent episode | create identity |
| ARMED | worth monitoring | preserve thesis/episode |
| WAITING | idea survives, current entry does not | do not delete |
| READY | analytical trigger is present | still run hard gate |
| MISSED | the executable window passed | no blind re-entry |
| INVALIDATED | thesis no longer survives | preserve reason |
| TRIGGERED | broker outcome is verified | link to Intent/trade |

## Timing inputs

M5 structure, candle sequence, momentum, extension, location, liquidity and
M15 target room are the baseline. Optional Trendline/Fibonacci/POC arrives
upstream as bounded confluence; timing does not require it.

SEVERELY_EXTENDED normally becomes WAIT. A long-lived unchanged missed setup
may become MISSED rather than chase indefinitely.

## Fresh re-arm rule

MISSED may re-arm only when:

- the thesis still survives;
- current Trade Plan/risk geometry remains valid;
- a genuinely new structural or timing event is proven.

rearm_missed_opportunity with fresh_structural_event=false must reject the
operation. Risk separately limits same-episode re-entry.

## Implementation and tests

| Source | Role | Tests |
|---|---|---|
| decisions/opportunity.py | identity and lifecycle | test_strategy_decisions.py |
| decisions/timing.py | M5 timing output | test_strategy_decisions.py |
| decisions/snapshot.py | analytical snapshot | test_strategy_decisions.py |
| persistence/runtime_state.py | restart lineage | test_persistence_recovery.py |

## Dashboard/research boundary

The dashboard distinguishes WAIT, MISSED, INVALID and BLOCKED. Research keeps
taken, waited, missed, invalidated and blocked outcomes separate so a safety
block is not called a strategy miss.

## Explicit non-goals

Timing does not size, gate or write. It does not rebuild a thesis merely because
the current candle is late.

