# GoldSwingTraderAI — Candle Structure and Price Behaviour

**Status:** PROVISIONAL  
**Version:** 0.2-implementation-baseline  
**Authority:** Candle anatomy, candle-sequence behaviour, swing formation, protected structure, BOS/MSS classification, displacement, rejection, compression/expansion and exhaustion evidence.  
**Depends on:** `MARKET_DATA_AND_HISTORY.md`, `SYSTEM_CONTRACT.md`

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

## Phase 3 implementation checkpoint

Implemented in:

```text
src/goldswingtraderai/intelligence/candle_structure.py
```

Current implementation consumes completed chronological candles and a shared ATR series from the Quant desk during normal runtime. Standalone/replay calls may calculate ATR internally using the same baseline period.

Implemented typed outputs include:
- candle anatomy (`range`, body, wicks, body ratio, close position, range/ATR);
- candle-sequence state;
- confirmed causal swings with `pivot_time` and later `confirmed_at`;
- swing side/price/significance in ATR units;
- protected swing promotion after structural consequence;
- per-timeframe structure state;
- structural break events;
- bounded bull/bear evidence + coverage.

The current thresholds in `StructureConfig` are explicit initial implementation baselines intended for replay calibration. They are not immutable market truth.

## Candle-sequence states

Current typed baseline supports:

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

The architecture remains:

```text
CANDIDATE → CONFIRMED → PROTECTED → possible EXTERNAL/MAJOR interpretation
```

### Candidate

An emerging extreme. It may move as new completed candles arrive and is not structural authority.

### Confirmed

The Phase-3 baseline confirms a pivot only after a later completed candle moves sufficiently away from the candidate extreme using a configurable ATR-normalized reversal threshold.

Every confirmed swing preserves:

```text
pivot_time
confirmed_at
side
price
timeframe (through report)
significance_atr
```

A replay prefix ending before `confirmed_at` cannot see that confirmed swing.

### Protected

When a later accepted structural break proves that a prior opposite swing generated meaningful continuation, that swing may be promoted to `PROTECTED`. Protected structure may later support thesis invalidation and Trade Manager trailing, but this desk does not set the broker stop.

### External / major

Higher-level external/major interpretation remains a consumer/context concept. The current baseline exposes confirmed/protected geometry and significance so later Technical/Liquidity/strategy logic can rank it without inventing future knowledge.

## Structure state per timeframe

Current typed states:

```text
BULLISH
BEARISH
RANGE
TRANSITION
UNDETERMINED
```

Two recent confirmed highs/lows are used to establish directional structural geometry. Mixed higher-high/lower-low evidence produces transition rather than a forced trend label.

A fresh M5 shift cannot rewrite H1/H4 state because each report is built independently for its own timeframe.

## Break hierarchy

Current typed states:

```text
PROBE
QUALIFIED_BREAK
CONFIRMED_BOS
MSS_CANDIDATE
CONFIRMED_MSS
FAILED_BREAK
```

### PROBE

Price trades beyond a confirmed swing but the completed candle does not establish accepted close-through evidence.

### QUALIFIED_BREAK

A completed candle closes beyond a confirmed swing by a configurable ATR-normalized penetration amount.

### CONFIRMED_BOS

A qualified break consistent with the existing structural direction receives subsequent acceptance/follow-through.

### MSS_CANDIDATE / CONFIRMED_MSS

A counter-structure qualified break becomes an MSS candidate; subsequent acceptance may confirm MSS. Confirmed MSS means meaningful transition/opposing evidence, not an automatic opposite trade.

### FAILED_BREAK

A pending qualified break loses acceptance and closes back through the broken level in the opposite sense. This becomes useful evidence for the Failed Breakout Reversal strategy later.

## Avoiding over-restriction

The desk exposes graduated evidence rather than turning every uncertainty into a hard gate. `PROBE`, `QUALIFIED_BREAK`, `CONFIRMED_BOS`, `MSS_CANDIDATE` and `CONFIRMED_MSS` may all be useful to different strategy families at different maturity levels.

## Authority boundaries

This file does not own:
- liquidity pools/FVG/OB — `LIQUIDITY_AND_SMC.md`;
- technical zones/location — `TECHNICAL_STRUCTURE_AND_LEVELS.md`;
- EMA/RSI/ATR meaning — `INDICATORS_AND_VOLATILITY.md`;
- strategy family decisions — `../20-trading-decisions/STRATEGY_FLOOR.md`;
- Entry Timing — `../20-trading-decisions/ENTRY_TIMING.md`;
- Trade Plan SL/targets — `../20-trading-decisions/TRADE_PLAN.md`;
- broker/risk authority.

## Persistence/restart

Raw rolling candles may be reloaded and structure rebuilt deterministically. Any cache/persistence must preserve chronology and never expose a swing/event earlier after restart than a fresh chronological rebuild would.

## Runtime integration

```text
MarketSnapshot CandleSeries
→ IndicatorSeries once
→ shared ATR
→ StructureReport
→ Technical/Liquidity consumers
→ IntelligenceSnapshot
```

The Structure desk does not query MT5 independently.

## Replay requirements

Replay/live parity requires:
- completed-candle chronology;
- same ATR and structure config version;
- explicit swing `confirmed_at`;
- no future-confirmed pivot visibility;
- deterministic break classification;
- no final-bar hindsight upgrades.

## Dashboard visibility

Compact future example:

```text
CANDLE / STRUCTURE
Bull Evidence    84
Bear Evidence    31
M15 Structure    BULLISH
M5 Structure     TRANSITION
Latest Event     QUALIFIED_BREAK ↑
Protected Low    4312.40
```

## Tests required / current evidence

Required:
- no-lookahead pivot confirmation;
- candidate/confirmed chronology;
- protected-swing promotion;
- wick-only probe not BOS/MSS;
- completed close required for qualified break;
- BOS versus MSS distinction;
- timeframe independence;
- failed-break classification;
- volatility normalization;
- live/replay timestamp parity.

Phase-3 deterministic coverage exists in `tests/test_indicators_structure.py` and the shared-ATR integration test in `tests/test_intelligence_snapshot.py`. Full chronological replay parity remains a later Phase-10 verification gate.

## Explicit non-goals

This desk must not:
- force every candle into BUY/SELL;
- treat named patterns as strategies;
- use forming candles as structural proof;
- make every minor pivot equal;
- convert local MSS directly into H1/H4 reversal;
- hide future confirmation in replay;
- place orders.

## Open calibration questions

The implementation baseline still requires replay calibration for:
- swing reversal/prominence threshold;
- qualified-break penetration;
- follow-through/acceptance amount;
- expansion/compression/rejection thresholds;
- significance ranking and future external/major classification;
- how much early versus confirmed structure each strategy family should consume.
