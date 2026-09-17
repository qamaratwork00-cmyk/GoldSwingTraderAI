# GoldSwingTraderAI — Market Data and History

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Runtime market-history and candle-data handling

## Core principle

Historical candles are necessary for context, structure, timing and research, but raw candle history is not permanent decision authority. The runtime should maintain enough rolling history to understand current market structure while deeper research history remains replaceable and refreshable.

## Runtime timeframe windows

Initial design ranges are provisional and will be calibrated for performance/coverage:

- H4: roughly 300–500 completed candles.
- H1: roughly 500–1000 completed candles.
- M15: roughly 1500–3000 completed candles.
- M5: roughly 3000–6000 completed candles.

The exact window sizes are implementation/research parameters, not market truth.

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

## Completed-candle authority

Structural decisions must use completed candles unless a specific future contract explicitly authorizes intrabar telemetry. No look-ahead or future pivot confirmation may leak into historical replay or live decisions.

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

## Data quality

The Market Data Desk must distinguish at least:

- healthy/continuous data;
- expected scheduled closure gap;
- reopen/warmup data;
- sparse/uncertain open-market feed;
- stale/corrupt data.

Data uncertainty that affects financial truth must fail closed for new entries.

## Holiday and session context

A calendar holiday does not automatically mean XAU is closed. Holiday information is context; actual broker tradeability, executable quotes and valid market data determine whether the market is open.
