# GoldSwingTraderAI — Indicators and Volatility

**Status:** PROVISIONAL
**Version:** 0.1-quant
**Authority:** EMA, RSI, ATR, volatility, momentum, extension and normalization

## Question answered

How can indicators quantify price behaviour without replacing structure or
becoming a hidden universal filter?

## Shared calculation pipeline

~~~mermaid
flowchart TB
    BARS["Completed CandleSeries"] --> SERIES["EMA20, EMA50, RSI14, ATR14"]
    SERIES --> NORMALIZE["ATR-normalized range, momentum, volatility and extension"]
    NORMALIZE --> REPORT["QuantReport"]
    REPORT --> STRUCT["Candle Structure"]
    REPORT --> TECH["Technical and Liquidity desks"]
    REPORT --> DECISION["Strategies, timing and Trade Manager"]
~~~

Each required series is calculated once per timeframe in the shared snapshot.
The quant desk does not query MT5 or write orders.

## Baseline indicators

| Indicator | V1 role | Missing history |
|---|---|---|
| EMA20/EMA50 | flow and directional support | None/UNKNOWN until enough bars |
| RSI14 Wilder | momentum pressure context | UNKNOWN; never forced to 50 |
| ATR14 Wilder | volatility normalization | UNKNOWN; never replaced by fixed pips |

EMA order alone is not a BUY/SELL command. RSI overbought/oversold alone is
not a reversal command.

## Volatility and momentum states

Volatility:

~~~text
UNKNOWN | QUIET | NORMAL | BUILDING | EXPANDING | EXTREME | DISLOCATED
~~~

Momentum:

~~~text
UNKNOWN | BUILDING | EXPANDING | MATURE | EXHAUSTING | REVERSING
~~~

Momentum combines EMA flow, directional progress, body/ATR, RSI pressure and
extension context. Strong momentum can still be a poor entry if it is late.

## Extension and chase

Distance from EMA20 is normalized in ATR units:

~~~text
UNKNOWN | FRESH | NORMAL | EXTENDED | SEVERELY_EXTENDED
~~~

SEVERELY_EXTENDED normally makes Entry Timing WAIT while the opportunity can
remain alive. It is not by itself an exit, reversal or broker block.

## Shared ATR rule

ATR supports:

- candle strength;
- swing significance;
- zone width;
- liquidity clustering;
- stop/target context;
- extension and execution-relative measurements.

ATR does not choose a final broker stop. Structural invalidation belongs to
Trade Plan; spread/drift permission belongs to execution checks.

## Implementation and tests

| Source | Responsibility | Tests |
|---|---|---|
| intelligence/indicators.py | chronological indicator series and QuantReport | test_intelligence_core.py |
| intelligence/snapshot.py | one shared calculation per cycle | test_intelligence_snapshot.py |
| decisions/timing.py | use of extension/momentum for WAIT | test_strategy_decisions.py |
| management/manager.py | use of momentum for management | test_trade_manager.py |

Tests cover chronology, missing values, ATR normalization, states, shared
calculation and no MT5 access from indicator code.

## Research and dashboard

Replay uses the same indicator semantics at each completed-bar prefix.
Calibration monitors Net R, drawdown, recall, capture and trade frequency, not
only headline win rate. The dashboard shows EMA flow, RSI, ATR, volatility,
momentum and extension as context.

## Explicit non-goals

No indicator may independently create a strategy, hard-block a trade, change
structural SL/TP, close a trade or call MT5.

