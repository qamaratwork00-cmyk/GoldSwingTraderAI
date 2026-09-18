# GoldSwingTraderAI — Market Data and History

**Status:** PROVISIONAL — IMPLEMENTED BASELINE + RECOVERY POSITION READS; LIVE MT5 DEMO EVIDENCE PENDING  
**Version:** 0.4-implementation  
**Authority:** Runtime market history, normalized broker read facts, current position facts and candle-data handling

## Core principle

Historical candles are necessary for context, structure, timing and research, but raw candle history is not permanent decision authority.

> **One narrow verified MT5 read boundary owns account, symbol, quote, completed candles and current open-position facts. Completed candles own structural chronology; unknown broker exposure is never converted into zero exposure.**

## Current implementation

```text
src/goldswingtraderai/domain/market.py
src/goldswingtraderai/market_data/mt5_reader.py
src/goldswingtraderai/market_data/snapshot.py
src/goldswingtraderai/app/recovery_mt5.py
src/goldswingtraderai/app/main.py
```

Key contracts:

- `AccountFacts` — login/server/currency/account mode and monetary facts;
- `SymbolSpec` — digits, point, tick size/value, contract size, volume limits and broker stop/freeze levels;
- `OpenPositionFacts` — normalized read-only current broker position facts;
- `Quote` — Bid/Ask/timestamp and spread;
- `Candle` / `CandleSeries` — UTC chronological completed OHLC;
- `MarketSnapshot` — reusable account/symbol/quote/multi-timeframe snapshot;
- `MT5Reader` — narrow read-only adapter around official `MetaTrader5`;
- `MarketSnapshotBuilder` — normalized H4/H1/M15/M5 construction;
- `build_mt5_recovery_truth()` — recovery adapter built on `MT5Reader`, not a second raw MT5 client.

`MT5Reader` contains no irreversible broker-write call. Raw create/modify/close writes remain confined to `execution/mt5_writer.py` behind the centralized execution path.

## Positive DEMO and account facts

The read layer publishes account mode. Positively verified DEMO may produce DEMO PASS; anything else cannot. Optional configured login/server pins are checked by application/runtime authorities rather than silently ignored.

## Gold symbol resolution

```text
preferred symbol
→ configured aliases in order
→ explicit SYMBOL_NOT_FOUND
```

Default configuration prefers `XAUUSDm` and falls back to `XAUUSD`.

## Current open-position truth — implemented

`MT5Reader.open_positions(symbol)` calls the official read-only `positions_get(symbol=...)` through the existing boundary and normalizes each row to `OpenPositionFacts`:

```text
ticket
symbol
direction BUY / SELL
volume
price_open
stop_loss / None
take_profit / None
magic / optional
comment / optional
```

Rules:

- a positive MT5 return of an empty collection means complete current zero-position truth for that symbol;
- `positions_get(...) is None` is `DATA_UNAVAILABLE`, **not** an empty tuple;
- missing read capability is `DATA_UNAVAILABLE`;
- unsupported position direction, invalid numeric geometry, wrong returned symbol or duplicate position ticket is `DATA_CORRUPT`;
- MT5 SL/TP value `0` is normalized to explicit `None`;
- returned positions are sorted deterministically by ticket;
- these facts describe broker exposure; they do not by themselves prove bot ownership.

This closes the software gap where recovery needed current position facts without creating another MetaTrader5 client.

## Live recovery truth adapter

`app/recovery_mt5.py` composes only read-layer facts:

```text
initialized MT5Reader
→ account_facts()
→ resolve_symbol()
→ symbol_spec()
→ open_positions()
→ BrokerRecoverySnapshot + SymbolSpec
```

The returned `MT5RecoveryTruth.price_tolerance` is **one verified broker tick (`SymbolSpec.tick_size`)**. Startup recovery therefore does not guess a hard-coded Gold SL/TP tolerance.

If current position truth cannot be read completely, snapshot creation raises through the market-data boundary; it never marks `positions_complete=True` with invented empty exposure.

## Runtime timeframe windows

Initial completed-candle windows remain:

| Timeframe | Initial window |
|---|---:|
| H4 | 400 |
| H1 | 750 |
| M15 | 2000 |
| M5 | 4000 |

These are research-calibratable implementation baselines.

## Completed-candle authority

MT5 bar position `0` is forming; position `1` is the most recent completed bar. Structural history therefore uses `copy_rates_from_pos(..., start_pos=1, count=...)`.

Returned candles are UTC-normalized, chronological and rejected when duplicate/corrupt.

## Snapshot reuse and execution freshness

Normal analysis reuses one normalized market snapshot rather than repeating broker reads. Execution/recovery may perform fresh broker reads where safety requires them; snapshot reuse never overrides execution freshness.

## Data-quality states

```text
HEALTHY
INSUFFICIENT
STALE
SPARSE
CORRUPT
UNKNOWN
```

Critical missing/corrupt broker facts are never converted into zeros or fabricated healthy values.

## Closure/reopen gaps

Market data reports suspicious gaps conservatively. Hard scheduled-close/reopen permission belongs to `risk/permissions.py` using verified session facts; market data does not invent a broker schedule.

## History roles

Recent history supports timing/rejection/displacement; wider local history supports swings/BOS/MSS/liquidity; H1/H4 supports regime/major structure/targets; deep research history is replaceable chronological research input.

## Permanent evidence versus temporary market data

Durable storage prioritizes trade/opportunity/risk/order/learning/research evidence. Large raw candle archives do not need to become primary permanent runtime state. Current broker exposure is always refreshed from broker truth during recovery.

## Failure reasons

```text
MT5_UNAVAILABLE
MT5_NOT_INITIALIZED
SYMBOL_NOT_FOUND
DATA_UNAVAILABLE
DATA_INSUFFICIENT
DATA_STALE
DATA_SPARSE
DATA_CORRUPT
```

## Tests / current evidence

Deterministic CI covers account/DEMO normalization, symbol alias/spec/quote facts, completed-candle chronology, snapshot quality, read-only boundary confinement, BUY/SELL open-position normalization, zero SL/TP → None, positive empty exposure, unknown position read fail-closed, invalid direction rejection, duplicate ticket rejection and live recovery snapshot/tick-tolerance construction.

Current repository checkpoint after live recovery read integration: **226 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Verification status

**Deterministic implementation tests:** PASS.  
**Actual connected Windows MT5 DEMO account/symbol/quote/history/open-position evidence:** PENDING.  
**Controlled broker-write/reconciliation evidence:** PENDING.

Do not mark this document VERIFIED until intended MT5 DEMO environment supplies real read evidence and integration checks pass.
