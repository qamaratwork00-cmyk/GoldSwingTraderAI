# GoldSwingTraderAI — Candle Structure

**Status:** PROVISIONAL
**Version:** 0.1-structure
**Authority:** Candle anatomy, sequences, causal swings, BOS/MSS and price-action states

## Question answered

What has price actually done on completed candles, and when did that fact
become knowable?

## Causal pipeline

~~~mermaid
flowchart TB
    BARS["Completed chronological bars"] --> ANATOMY["Range, body, wick and close position"]
    ANATOMY --> SEQUENCE["Continuation, rejection, compression or expansion"]
    SEQUENCE --> SWING["Candidate → confirmed → protected swing"]
    SWING --> BREAK["Probe → qualified break → BOS/MSS or failed break"]
    BREAK --> REPORT["StructureReport with evidence, coverage and timestamps"]
~~~

Structure is intelligence only. It cannot size risk or send an order.

## Core chronology

- forming candles are not structural proof;
- pivot_time is the extreme’s candle time;
- confirmed_at is the later time when reversal evidence made the swing known;
- replay cannot expose a confirmed swing before confirmed_at;
- each timeframe has an independent report;
- candidate evidence is not the same as confirmed/protected authority.

## Candle and sequence states

~~~text
BULL_CONTINUATION | BEAR_CONTINUATION
BULL_EXPANSION    | BEAR_EXPANSION
BULL_REJECTION    | BEAR_REJECTION
COMPRESSION       | MIXED
~~~

Ranges, bodies, wicks, close location and ATR-normalized size combine into
these descriptive states. A state is evidence, not a trade instruction.

## Swing lifecycle

~~~mermaid
stateDiagram-v2
    [*] --> CANDIDATE
    CANDIDATE --> CONFIRMED: later completed reversal evidence
    CONFIRMED --> PROTECTED: accepted structural consequence
    PROTECTED --> EXTERNAL: higher significance context
    CANDIDATE --> [*]: invalidated before confirmation
~~~

A confirmed swing records pivot_time, confirmed_at, side, price, timeframe and
ATR-normalized significance. Protected geometry may inform invalidation/trailing
but this desk does not place the stop.

## Break lifecycle

~~~text
PROBE
→ QUALIFIED_BREAK
→ CONFIRMED_BOS or CONFIRMED_MSS
→ FAILED_BREAK when acceptance is lost
~~~

- PROBE: price trades through a level but acceptance is not proven.
- QUALIFIED_BREAK: completed candle closes beyond a confirmed swing by the
  configured normalized amount.
- BOS: break accepted in the existing structural direction.
- MSS: counter-structure break that challenges the current direction; it is a
  transition signal, not automatic opposite trend authority.
- FAILED_BREAK: attempted acceptance closes back through the level.

## Implementation

intelligence/candle_structure.py owns anatomy, swings, structure state and
break classification. intelligence/snapshot.py passes shared ATR and attaches
the report to the IntelligenceSnapshot.

States per timeframe:

~~~text
BULLISH | BEARISH | RANGE | TRANSITION | UNDETERMINED
~~~

## Failure/replay behaviour

Insufficient history returns coverage/UNKNOWN rather than a guessed trend.
Restart rebuilds structure from the same chronological completed bars; it must
not promote a swing earlier than a fresh replay would.

## Source and tests

| Source | Tests |
|---|---|
| intelligence/candle_structure.py | test_intelligence_core.py |
| intelligence/snapshot.py | test_intelligence_snapshot.py |
| research/replay.py | test_research_validation.py |

The tests cover no-lookahead confirmation, protected swings, probes versus
breaks, BOS/MSS, failed breaks, timeframe independence and shared ATR.

## Dashboard and research

The dashboard may show structure state, latest event, bull/bear evidence and
protected levels. Replay must preserve confirmation timestamps and never use
future-bar outcomes to upgrade the earlier report.

## Explicit non-goals

No named candle pattern is a standalone strategy. This desk does not own
liquidity, generic zones, indicators, entry timing, risk or execution.

