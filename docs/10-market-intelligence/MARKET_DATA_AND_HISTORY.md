# GoldSwingTraderAI — Market Data and History

**Status:** PROVISIONAL — PHASE 2 IMPLEMENTED IN CODE; LIVE MT5 DEMO INTEGRATION PENDING  
**Version:** 0.2-implementation  
**Authority:** Runtime market-history, normalized broker facts and candle-data handling

## Core principle

Historical candles are necessary for context, structure, timing and research, but raw candle history is not permanent decision authority. Runtime maintains enough rolling history to understand current market structure while deeper research history remains replaceable and refreshable.

> **One normalized verified market snapshot is built from the MT5 read boundary and reused downstream. Completed candles own structural chronology; the currently forming MT5 bar is never included as a completed structural candle.**

## Current Phase 2 implementation

The read-only implementation currently lives in:

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
- `MarketSnapshotBuilder` — one normalized H4/H1/M15/M5 snapshot construction path.

`MT5Reader` deliberately contains no irreversible broker-write call. Create/modify/close belong to the later governed execution phase.

The `MetaTrader5` import is lazy so deterministic Linux CI can run without a Windows MT5 terminal. Production/local MT5 usage still requires the official package and connected terminal.

## Positive DEMO fact

The read layer publishes account mode and can evaluate the V1 positive DEMO fact:

```text
positively verified DEMO → DEMO_GUARD PASS
anything else            → no PASS
```

This does not create a separate REAL policy. Final broker-write permission remains owned by the later centralized execution gate.

Optional configured account login/server identity pins are compared by the app readiness path. A mismatch is surfaced explicitly and does not become silent readiness.

## Gold symbol resolution

Current resolution order is deterministic:

```text
preferred symbol
→ configured aliases in order
→ explicit SYMBOL_NOT_FOUND if none exist
```

Default configuration prefers `XAUUSDm` and falls back to `XAUUSD`. Broker symbol selection is performed only when a discovered configured symbol is not already visible.

## Runtime timeframe windows

Initial V1 implementation values are inside the previously designed ranges:

| Timeframe | Initial completed-candle window |
|---|---:|
| H4 | 400 |
| H1 | 750 |
| M15 | 2000 |
| M5 | 4000 |

These values remain research-calibratable rather than market truth.

The builder accepts explicit alternate window sizes for deterministic tests/replay work; production defaults remain centralized in `market_data/snapshot.py` rather than scattered through strategies.

## Completed-candle authority

Structural decisions use completed candles unless a future explicit contract grants intrabar telemetry authority.

For MT5 positional rates:

```text
bar position 0 = currently forming candle
bar position 1 = most recent completed candle
```

Therefore the read adapter calls `copy_rates_from_pos(..., start_pos=1, count=...)` for completed history. This exclusion is intentional and covered by tests.

Returned candles are normalized to UTC, sorted chronologically and rejected if duplicate/non-chronological or structurally corrupt.

## Snapshot reuse

Per snapshot, the current implementation performs the required read pass once:

```text
account facts
→ Gold symbol resolution
→ symbol specification
→ current Bid/Ask quote
→ one completed-candle request per configured timeframe
→ normalized MarketSnapshot
```

Downstream intelligence/strategy code should consume this snapshot rather than independently repeating the same broker reads or recalculating equivalent raw facts.

A later execution phase still performs fresh pre-write checks where the execution safety contract requires them; snapshot reuse never overrides execution freshness.

## Data-quality states

The current normalized vocabulary is:

```text
HEALTHY
INSUFFICIENT
STALE
SPARSE
CORRUPT
UNKNOWN
```

Current Phase 2 checks include:

- quote freshness;
- requested versus returned completed-candle count;
- latest completed-candle age relative to timeframe;
- recent duplicate/non-chronological candles;
- recent large candle-time gaps;
- invalid/non-finite quote/spec/OHLC data.

Initial quote-age threshold is 10 seconds in the snapshot builder. It is an implementation baseline, not a future execution spread/slippage substitute.

A completed candle timestamp represents bar-open time. Therefore the latest completed candle is not declared stale merely because it is older than one full timeframe; current conservative stale detection allows up to roughly two timeframe periods.

## Expected closure/reopen gaps

Phase 2 conservatively detects recent large gaps as `SPARSE`. Distinguishing an expected scheduled XAU closure gap from an abnormal open-market feed gap requires the verified broker session schedule and is integrated with the later Session/Risk phase.

Until that context exists, a suspicious gap must not be silently treated as healthy.

## History roles

### Immediate context

Recent candles support:

- entry timing;
- rejection/reclaim;
- displacement;
- chase detection;
- pullback health.

### Local structure

A wider recent window supports:

- swing identification;
- BOS/MSS;
- compression/expansion;
- local liquidity;
- structural invalidation.

### Session context

Current and previous session history supports:

- Asian/London/New York ranges;
- session highs/lows;
- sweep/continuation behaviour;
- intraday expansion analysis.

### Higher-timeframe context

H1/H4 history supports:

- regime;
- major structure;
- important liquidity/targets;
- trend/range/transition context.

## Deep research history

Replay/research may use much deeper historical datasets or caches. These datasets are not permanent live-state truth and may be rebuilt/updated when the data source changes.

Research must preserve chronology and avoid using outcomes or future bars that would not have been known at the historical decision time.

## Permanent evidence versus temporary market data

Permanent durable storage should prioritize:

- trade journal;
- opportunity/decision snapshots;
- entry and exit evidence summaries;
- risk/session state;
- order lifecycle/reconciliation state;
- strategy/research evidence;
- discovery/invention evidence;
- performance and validation results.

Large raw candle archives need not be the primary permanent state of the bot.

## Failure behaviour

Read-layer failures use explicit machine-readable reasons such as:

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

Critical missing/corrupt facts are not converted into zeros or fabricated healthy values.

## Holiday and session context

A calendar holiday does not automatically mean XAU is closed. Holiday information is context; actual broker tradeability, executable quotes and valid market data determine whether the market is open.

Full verified broker-session schedule interpretation belongs with the later session-safety implementation.

## Tests implemented

Deterministic CI currently covers:

- MT5 reader must be initialized before use;
- account fact normalization and positive DEMO guard semantics;
- non-DEMO account cannot produce DEMO PASS;
- `XAUUSDm → XAUUSD` alias fallback;
- symbol-spec and Bid/Ask normalization;
- completed history explicitly starts at MT5 position `1`;
- candle chronology;
- healthy multi-timeframe snapshot construction;
- stale quote classification;
- app account-identity mismatch handling;
- app positive-DEMO readiness handling;
- market-data adapter contains no `order_send` path;
- repository Ruff/Pytest/financial-secret CI.

## Verification status

**Deterministic implementation tests:** PASS in GitHub CI.  
**Actual connected MT5 DEMO terminal read test:** PENDING.  
**Irreversible broker execution:** NOT IMPLEMENTED in Phase 2.

Do not upgrade this document to full `VERIFIED` until the intended MT5 DEMO environment has supplied real account/symbol/quote/history evidence in addition to deterministic tests.
