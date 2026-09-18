# GoldSwingTraderAI — Market Data and History

**Status:** PROVISIONAL — IMPLEMENTED BASELINE; LIVE MT5 DEMO EVIDENCE PENDING  
**Version:** 0.3-implementation  
**Authority:** Runtime market-history, normalized broker facts and candle-data handling

## Core principle

Historical candles are necessary for context, structure, timing and research, but raw candle history is not permanent decision authority. Runtime maintains enough rolling history to understand current market structure while deeper research history remains replaceable and refreshable.

> **One normalized verified market snapshot is built from the MT5 read boundary and reused downstream. Completed candles own structural chronology; the currently forming MT5 bar is never included as a completed structural candle.**

## Current implementation

The read boundary lives in:

```text
src/goldswingtraderai/domain/market.py
src/goldswingtraderai/market_data/mt5_reader.py
src/goldswingtraderai/market_data/snapshot.py
src/goldswingtraderai/app/main.py
```

Key contracts:

- `AccountFacts` — login/server/currency/account mode and account monetary facts;
- `SymbolSpec` — digits, point, tick size/value, contract size, volume limits/step and broker stop/freeze levels;
- `Quote` — Bid/Ask/timestamp and price spread;
- `Candle` / `CandleSeries` — UTC chronological completed OHLC data;
- `MarketSnapshot` — one account/symbol/quote/multi-timeframe snapshot plus data-quality state;
- `MT5Reader` — narrow read-only adapter around the official `MetaTrader5` module;
- `MarketSnapshotBuilder` — normalized H4/H1/M15/M5 snapshot construction.

`MT5Reader` deliberately contains no irreversible broker-write call. Raw create/modify/close writes are confined to `execution/mt5_writer.py` behind the centralized execution path.

The `MetaTrader5` import is lazy so deterministic Linux CI can run without a Windows MT5 terminal. Local terminal use still requires the official package and connected MT5 terminal.

## Positive DEMO fact

The read layer publishes account mode and can evaluate the V1 positive DEMO fact:

```text
positively verified DEMO → DEMO_GUARD PASS
anything else            → no PASS
```

This does not create a separate REAL policy. The implemented centralized Execution Permission Gate consumes the DEMO result together with all other hard authorities before any broker write.

Optional configured account login/server identity pins are compared by the app readiness path. A mismatch is surfaced explicitly and never becomes silent readiness.

## Gold symbol resolution

Current resolution order is deterministic:

```text
preferred symbol
→ configured aliases in order
→ explicit SYMBOL_NOT_FOUND if none exist
```

Default configuration prefers `XAUUSDm` and falls back to `XAUUSD`. Broker symbol selection is performed only when a discovered configured symbol is not already visible.

## Runtime timeframe windows

Initial V1 completed-candle windows:

| Timeframe | Initial window |
|---|---:|
| H4 | 400 |
| H1 | 750 |
| M15 | 2000 |
| M5 | 4000 |

These remain research-calibratable rather than market truth.

The builder accepts alternate window sizes for deterministic tests/replay; production defaults remain centralized in `market_data/snapshot.py` rather than scattered through strategies.

## Completed-candle authority

Structural decisions use completed candles unless a future explicit contract grants intrabar telemetry authority.

For MT5 positional rates:

```text
bar position 0 = currently forming candle
bar position 1 = most recent completed candle
```

Therefore the read adapter calls `copy_rates_from_pos(..., start_pos=1, count=...)` for completed history. Returned candles are normalized to UTC, sorted chronologically and rejected if duplicate/non-chronological or structurally corrupt.

## Snapshot reuse

Per market snapshot, normal analysis performs the required read pass once:

```text
account facts
→ Gold symbol resolution
→ symbol specification
→ current Bid/Ask quote
→ one completed-candle request per configured timeframe
→ normalized MarketSnapshot
```

Downstream intelligence/strategy code consumes this snapshot instead of repeating broker reads or equivalent calculations.

The implemented execution path performs fresh pre-write broker/quote/spec checks where execution safety requires them. Snapshot reuse never overrides execution freshness.

## Data-quality states

```text
HEALTHY
INSUFFICIENT
STALE
SPARSE
CORRUPT
UNKNOWN
```

Current checks include:

- quote freshness;
- requested versus returned completed-candle count;
- latest completed-candle age relative to timeframe;
- duplicate/non-chronological candles;
- recent large candle-time gaps;
- invalid/non-finite quote/spec/OHLC data.

Initial quote-age threshold is 10 seconds in the snapshot builder. It is an implementation baseline, not an execution spread/slippage substitute.

A completed candle timestamp represents bar-open time; stale detection therefore allows the most recent completed bar to be older than one timeframe without immediately declaring it invalid.

## Closure/reopen gaps

The market-data layer conservatively reports suspicious recent time gaps as `SPARSE` rather than pretending they are healthy.

Hard scheduled-close/reopen permission is implemented in `risk/permissions.py` and uses verified broker-session facts. The **production broker-session schedule sourcing adapter is still pending**, so market data does not invent whether a specific gap was scheduled.

## History roles

### Immediate context

Recent candles support entry timing, rejection/reclaim, displacement, chase detection and pullback health.

### Local structure

A wider window supports swing identification, BOS/MSS, compression/expansion, local liquidity and structural invalidation.

### Session context

Current/previous session history supports session ranges, highs/lows, sweep/continuation behaviour and intraday expansion analysis.

### Higher-timeframe context

H1/H4 history supports regime, major structure, important liquidity/targets and trend/range/transition context.

## Deep research history

Replay/research may use much deeper historical datasets or caches. These are replaceable research inputs, not permanent live-state truth.

Research must preserve chronology and may never use future bars/outcomes to improve the original historical decision.

## Permanent evidence versus temporary market data

Durable storage prioritizes:

- trade journal;
- opportunity/decision snapshots;
- entry/exit evidence summaries;
- risk/session state;
- order lifecycle/reconciliation state;
- strategy/research/discovery evidence;
- performance and validation results.

Large raw candle archives need not become the bot's primary permanent state.

## Failure behaviour

Explicit read-layer reasons include:

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

Critical missing/corrupt facts are never converted into zeros or fabricated healthy values.

## Holiday and session context

A calendar holiday does not automatically mean XAU is closed. Holiday information is context; actual broker tradeability, executable quotes, valid data and verified session facts own hard market permission.

## Tests / current evidence

Deterministic CI covers:

- MT5 reader initialization requirement;
- account fact normalization and positive DEMO semantics;
- non-DEMO cannot produce DEMO PASS;
- `XAUUSDm → XAUUSD` alias fallback;
- symbol-spec and Bid/Ask normalization;
- completed history begins at MT5 position `1`;
- candle chronology;
- multi-timeframe snapshot construction;
- stale quote classification;
- account identity mismatch handling;
- positive-DEMO readiness handling;
- market-data adapter contains no `order_send` path.

Downstream deterministic suites additionally exercise Intelligence, Risk, Session/News and Execution against normalized market facts.

## Verification status

**Deterministic implementation tests:** PASS in GitHub CI.  
**Actual connected MT5 DEMO terminal read evidence:** PENDING.  
**Downstream broker-write modules:** implemented deterministically, but controlled Windows MT5 DEMO write/reconciliation evidence is still PENDING.

Do not mark this document `VERIFIED` until the intended MT5 DEMO environment supplies real account/symbol/quote/history evidence and the relevant integration checks pass.
