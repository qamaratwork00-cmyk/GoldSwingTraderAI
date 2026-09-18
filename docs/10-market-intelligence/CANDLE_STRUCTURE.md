# GoldSwingTraderAI — Candle Structure and Price Behaviour

**Status:** PROVISIONAL — IMPLEMENTED BASELINE  
**Version:** 0.3-implementation  
**Authority:** Candle anatomy, sequence behaviour, swing formation, protected structure, BOS/MSS classification, displacement, rejection, compression/expansion and exhaustion evidence.  
**Depends on:** `MARKET_DATA_AND_HISTORY.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

This document defines how GoldSwingTraderAI interprets completed price behaviour before strategy, timing, management or risk consume it.

The Candle/Structure desk is market intelligence only. It never sizes lots, grants broker permission or sends orders.

## Core principles

1. **Completed candles own structural proof.**
2. **Sequences matter more than named candlestick labels.**
3. **Volatility normalization is required.**
4. **Swing pivot time and confirmation time are different.**
5. **Each timeframe owns its own structure state.**
6. **Candidate/early evidence is distinct from confirmed/protected authority.**
7. **No lookahead.** Replay cannot expose a swing/event before it became knowable.

## Current implementation checkpoint

Implemented in:

```text
src/goldswingtraderai/intelligence/candle_structure.py
src/goldswingtraderai/intelligence/snapshot.py
```

Normal runtime consumes completed chronological candles and a shared ATR series computed once by the Quant desk. Standalone/replay calls may calculate ATR internally using the same configured period.

Typed outputs include:

- candle anatomy (`range`, body, wicks, body ratio, close position, range/ATR);
- candle-sequence state;
- confirmed causal swings with `pivot_time` and later `confirmed_at`;
- swing side/price/significance in ATR units;
- protected swing promotion after structural consequence;
- per-timeframe structure state;
- structural break events;
- bounded bull/bear evidence + coverage.

Thresholds in `StructureConfig` are explicit implementation baselines intended for replay calibration, not immutable market truth.

## Candle-sequence states

```text
BULL_CONTINUATION
BEAR_CONTINUATION
BULL_EXPANSION
BEAR_EXPANSION
BULL_REJECTION
BEAR_REJECTION
COMPRESSION
MIXED
```

Expansion uses normalized range/body/close quality. Compression uses normalized recent ranges plus overlap. Rejection uses wick/body and close-location evidence.

These are evidence labels, not trade commands.

## Swing model

```text
CANDIDATE → CONFIRMED → PROTECTED → possible EXTERNAL/MAJOR interpretation
```

### Candidate

An emerging extreme. It may move as new completed candles arrive and is not structural authority.

### Confirmed

A pivot becomes confirmed only after later completed-candle movement satisfies the configured ATR-normalized reversal requirement.

Every confirmed swing preserves:

```text
pivot_time
confirmed_at
side
price
timeframe
significance_atr
```

A replay prefix ending before `confirmed_at` cannot see that confirmed swing.

### Protected

When later accepted structure proves that a prior opposite swing generated meaningful continuation, that swing may be promoted to `PROTECTED`. Consumers may use protected geometry for invalidation/trailing, but this desk does not set broker stops.

### External / major

Higher-level external/major interpretation remains contextual. Current reports expose confirmed/protected geometry and significance so downstream consumers can rank it without future knowledge.

## Structure state per timeframe

```text
BULLISH
BEARISH
RANGE
TRANSITION
UNDETERMINED
```

Recent confirmed highs/lows establish directional geometry. Mixed HH/LL evidence produces transition rather than a forced trend label.

M5 cannot silently rewrite H1/H4 state because each timeframe report is built independently.

## Break hierarchy

```text
PROBE
QUALIFIED_BREAK
CONFIRMED_BOS
MSS_CANDIDATE
CONFIRMED_MSS
FAILED_BREAK
```

### PROBE

Price trades beyond a confirmed swing but completed-candle acceptance is insufficient.

### QUALIFIED_BREAK

A completed candle closes beyond a confirmed swing by the configured ATR-normalized penetration amount.

### CONFIRMED_BOS

A qualified break consistent with existing structural direction receives subsequent acceptance/follow-through.

### MSS_CANDIDATE / CONFIRMED_MSS

A counter-structure qualified break becomes an MSS candidate; later acceptance may confirm MSS. Confirmed MSS means meaningful transition/opposing evidence, not automatic opposite trade authority.

### FAILED_BREAK

A pending qualified break loses acceptance and closes back through the broken level. This becomes useful evidence for reversal families.

## Avoiding over-restriction

The desk exposes graduated evidence rather than turning every uncertainty into a hard gate. PROBE, QUALIFIED_BREAK, BOS and MSS maturity may all matter differently to different strategy families.

## Authority boundaries

This file does not own:

- liquidity pools/FVG/OB — `LIQUIDITY_AND_SMC.md`;
- technical zones/location/confluence — `TECHNICAL_STRUCTURE_AND_LEVELS.md`;
- EMA/RSI/ATR meaning — `INDICATORS_AND_VOLATILITY.md`;
- strategy family decisions — `../20-trading-decisions/STRATEGY_FLOOR.md`;
- Entry Timing — `../20-trading-decisions/ENTRY_TIMING.md`;
- Trade Plan SL/targets — `../20-trading-decisions/TRADE_PLAN.md`;
- broker/risk authority.

## Persistence/restart

Raw rolling candles may be reloaded and structure rebuilt deterministically. Persistence/recovery must never expose a swing/event earlier after restart than a fresh chronological rebuild would.

## Runtime integration

```text
MarketSnapshot CandleSeries
→ IndicatorSeries once
→ shared ATR
→ StructureReport
→ Technical/Liquidity/Confluence consumers
→ IntelligenceSnapshot
→ Strategy/Decision/Management consumers
```

The Structure desk does not query MT5 independently.

## Replay requirements and current foundation

Phase-10 bar-close replay reuses production Intelligence/Decision semantics on chronological prefixes. Structure parity requires:

- completed-candle chronology;
- same ATR/structure config version;
- explicit swing `confirmed_at`;
- no future-confirmed pivot visibility;
- deterministic break classification;
- no final-bar hindsight upgrades.

The current replay foundation is implemented, while broader historical calibration and live-vs-replay evidence remain ongoing Phase-10/release work.

## Dashboard visibility

Compact example:

```text
CANDLE / STRUCTURE
Bull Evidence    84
Bear Evidence    31
M15 Structure    BULLISH
M5 Structure     TRANSITION
Latest Event     QUALIFIED_BREAK ↑
Protected Low    4312.40
```

## Tests / current evidence

Deterministic coverage includes:

- no-lookahead pivot confirmation;
- candidate/confirmed chronology;
- protected-swing promotion;
- wick-only probe not BOS/MSS;
- completed close required for qualified break;
- BOS versus MSS distinction;
- timeframe independence;
- failed-break classification;
- volatility normalization;
- shared-ATR integration;
- chronological replay prefix behaviour.

## Explicit non-goals

This desk must not:

- force every candle into BUY/SELL;
- treat named patterns as standalone strategies;
- use forming candles as structural proof;
- make every minor pivot equal;
- convert local MSS directly into H1/H4 reversal;
- hide future confirmation in replay;
- place orders.

## Open calibration questions

- swing reversal/prominence threshold;
- qualified-break penetration;
- follow-through/acceptance amount;
- expansion/compression/rejection thresholds;
- significance ranking and external/major classification;
- how much early versus confirmed structure each strategy family should consume.
