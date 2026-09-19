# GoldSwingTraderAI — Technical Structure, Levels and Confluence

**Status:** PROVISIONAL
**Version:** 0.1-technical
**Authority:** Zones, location, target room and optional Trendline/Fibonacci/POC

## Question answered

Where is price relative to meaningful structural geometry, and does optional
confluence support an already coherent hypothesis?

## Two outputs, two meanings

~~~mermaid
flowchart TB
    STRUCT["Confirmed/protected StructureReport"] --> ZONES["ATR/tick-aware support and resistance zones"]
    ZONES --> LOCATION["BUY/SELL location, conflict and target room"]
    STRUCT --> TL["Causal Trendline geometry"]
    STRUCT --> FIB["Confirmed impulse Fibonacci geometry"]
    BARS["Completed bars + broker-local volume"] --> POC["Volume Profile / POC"]
    LOCATION --> REPORT["TechnicalReport"]
    TL --> CONFLUENCE["ConfluenceReport"]
    FIB --> CONFLUENCE
    POC --> CONFLUENCE
~~~

Technical location can influence opportunity quality. Confluence can add only a
bounded positive bonus. Neither output grants broker permission.

## Zones and location

Zones are ranges, not exact lines. The baseline width uses the greater of a
broker tick floor and an ATR fraction. Compatible nearby sources may merge so
one cluster is not counted as many independent confirmations.

Location categories:

~~~text
EXCELLENT | GOOD | NEUTRAL | POOR | DANGEROUS | UNKNOWN
~~~

The report includes nearest support/resistance, BUY/SELL location, opposing
conflict, equilibrium and ATR-normalized target room. A breakout family may
interpret nearby resistance differently from a pullback family; location is not
a universal veto.

## Trendline

Trendlines use already confirmed swings. The report may expose support/
resistance, ascending/descending/flat, projected price, distance and:

~~~text
TOUCH | BREAK | RECLAIM | NONE
~~~

No trendline is known before its anchor swings are confirmed.

## Fibonacci

Fibonacci uses a confirmed structural impulse pair, never arbitrary future
high/low selection. Initial context includes retracement 0.382, 0.500, 0.618,
0.786 and extension 1.272, 1.618, 2.000. A Fib touch supports an existing
narrative; it cannot create one.

## Broker-local POC

POC is calculated from a bounded recent candle window. Real volume is preferred;
otherwise tick-volume approximation is labelled. The report records price,
source, lookback, bins, relation ABOVE/BELOW/NEAR and normalized distance.
POC is direction-neutral by itself.

## V1 confluence rule

~~~text
supportive confluence → capped positive family bonus
missing confluence    → base score unchanged
opposed confluence    → visible context/conflict; no automatic hard block
POC alone             → cannot manufacture BUY/SELL authority
~~~

This is an accuracy tool, not filter soup.

## Implementation and tests

| Source | Responsibility | Tests |
|---|---|---|
| intelligence/technical.py | zones, location, target room | test_technical_liquidity.py |
| intelligence/confluence.py | Trendline, Fibonacci and POC | test_technical_confluence.py |
| strategies/confluence.py | bounded positive-only bonus | test_technical_confluence.py, test_strategy_decisions.py |
| intelligence/snapshot.py | shared report composition | test_intelligence_snapshot.py |

Tests cover causal anchors, zone merge, POC source labelling, missing
confluence, bounded bonus, timeframe separation and no double counting.

## Failure/replay/operator boundary

Missing structure, ATR or volume returns UNKNOWN/empty coverage, not fabricated
levels. Replay builds zones and confluence chronologically. The dashboard
labels POC source and shows absent confluence as unavailable context, not an
error or mandatory red gate.

## Explicit non-goals

This layer does not redefine BOS/MSS, liquidity events, strategy decisions,
risk, broker permission or stop placement.

