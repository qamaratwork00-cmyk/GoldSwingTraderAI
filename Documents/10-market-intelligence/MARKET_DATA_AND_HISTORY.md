# GoldSwingTraderAI — Market Data and History

**Status:** PROVISIONAL
**Version:** 0.1-market-facts
**Authority:** Normalized MT5 facts, completed-candle chronology, data quality and current exposure reads

## Reader promise

This document explains how raw MT5 data becomes trusted typed facts. It does
not decide whether a setup is attractive, affordable or executable.

## One read boundary

~~~mermaid
flowchart TB
    MT5["MetaTrader5 terminal"] --> READER["market_data/mt5_reader.py"]
    READER --> ACCOUNT["AccountFacts + DEMO mode"]
    READER --> SYMBOL["SymbolSpec + resolved XAU symbol"]
    READER --> QUOTE["Bid/Ask + timestamp + spread"]
    READER --> BARS["Completed H4/H1/M15/M5 CandleSeries"]
    READER --> POS["OpenPositionFacts"]
    ACCOUNT --> SNAP["MarketSnapshot"]
    SYMBOL --> SNAP
    QUOTE --> SNAP
    BARS --> SNAP
    SNAP --> INTEL["IntelligenceSnapshot"]
    ACCOUNT --> RECOVER["app/recovery_mt5.py — MT5RecoveryTruth"]
    SYMBOL --> RECOVER
    POS --> RECOVER
~~~

There is one normal runtime MT5 read owner. Intelligence modules do not create
their own terminal client. Raw create/modify/close writes belong only to
execution/mt5_writer.py.

## Facts and owners

| Fact | Meaning | Missing/corrupt result |
|---|---|---|
| AccountFacts | login, server, currency, equity and account mode | unavailable or identity mismatch |
| SymbolSpec | digits, point, tick, contract, volume and stop rules | symbol/spec unknown |
| Quote | Bid, Ask, UTC capture and spread | stale/unavailable |
| Candle | UTC OHLC and volume for one completed bar | corrupt/sparse |
| CandleSeries | chronological completed window | insufficient/stale/sparse |
| OpenPositionFacts | current broker position ticket, side, volume, SL/TP | unavailable/corrupt; never invented zero |
| MarketSnapshot | one reusable cycle view | quality state reflects its weakest required input |

## Gold symbol resolution

Resolution order:

~~~text
preferred symbol
→ configured aliases in order
→ SYMBOL_NOT_FOUND
~~~

The normal configuration prefers XAUUSDm and can fall back to XAUUSD. The
resolved symbol is recorded in every recovery and execution scope.

## Completed-candle rule

MT5 position 0 is forming. Structural history begins at position 1. The reader
normalizes bars to timezone-aware UTC and chronological order. Duplicate,
non-finite, impossible or out-of-order bars are corrupt.

Initial windows:

| Series | Completed bars |
|---|---:|
| H4 | 400 |
| H1 | 750 |
| M15 | 2000 |
| M5 | 4000 |

These are implementation baselines, not profitability claims.

## Open-position truth

The reader distinguishes:

~~~text
positions_get returns [] → verified zero current positions
positions_get returns None → DATA_UNAVAILABLE
invalid direction/symbol/number/duplicate ticket → DATA_CORRUPT
MT5 SL/TP value 0 → explicit None
~~~

Normalized facts include ticket, symbol, BUY/SELL direction, volume, open price,
SL, TP, optional magic and comment. Tickets are sorted deterministically.
Broker facts do not prove bot ownership; durable lineage and scope do that.

## Data-quality states

~~~text
HEALTHY
INSUFFICIENT
STALE
SPARSE
CORRUPT
UNKNOWN
~~~

Retryable pre-READY conditions are normally STALE, INSUFFICIENT and SPARSE.
CORRUPT, identity failure, unknown DEMO or persistence/controller faults remain
fail-closed.

## Freshness and reuse

Normal analysis shares one snapshot per cycle. Execution/recovery may perform a
fresh broker read where the execution contract requires it. Snapshot reuse
never overrides a fresh pre-submit check.

## Recovery adapter

app/recovery_mt5.py composes:

~~~text
MT5Reader.account_facts()
→ resolve_symbol()
→ symbol_spec()
→ open_positions()
→ BrokerRecoverySnapshot + SymbolSpec
~~~

Price tolerance comes from one verified broker tick, SymbolSpec.tick_size. It
is never a hard-coded Gold number.

## History roles

- recent M5 history: timing, rejection and displacement;
- wider M5/M15 history: swings, breaks, liquidity and local path;
- H1/H4: regime, major structure and target context;
- deep portable history: offline research input, not permanent live state.

Large raw archives do not replace durable lifecycle evidence. Risk, Intents,
Trade Plans, ManagedTrades, opportunities and research records are the
important restart artifacts.

## Failure and operator meaning

| Failure | Operator meaning | Runtime action |
|---|---|---|
| MT5 unavailable/not initialized | terminal connection failed | no readiness |
| symbol not found | no permitted Gold symbol | blocked |
| quote stale | feed not advancing | visible wait; no strategy/write |
| candle insufficient | warm-up incomplete | visible wait |
| sparse/corrupt bars | chronology cannot be trusted | fail closed |
| unknown positions | exposure cannot be proven | recovery blocked |

The readiness monitor shows quote age, quality, counts and exact issues. It does
not label stale data as definitely “market closed.”

## Source and tests

| Code | Responsibility | Tests |
|---|---|---|
| market_data/mt5_reader.py | raw read normalization and no-write boundary | test_market_data.py |
| market_data/snapshot.py | multi-timeframe MarketSnapshot | test_market_data.py, test_intelligence_snapshot.py |
| domain/market.py | AccountFacts, SymbolSpec, Quote, Candle and positions | test_models.py |
| app/recovery_mt5.py | live recovery truth adapter | test_recovery_mt5.py |
| app/main.py | readiness capture and retry loop | test_app_readiness.py |

Deterministic tests prove mapping and failure semantics. Real Windows MT5
history, fresh quotes and connected exposure remain release evidence.

## Explicit non-goals

This layer does not decide strategy direction, risk sizing, news permission,
controller ownership, broker writes or profitability.

