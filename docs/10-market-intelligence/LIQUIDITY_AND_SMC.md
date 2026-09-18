# GoldSwingTraderAI — Liquidity and SMC

**Status:** PROVISIONAL  
**Version:** 0.2-implementation-baseline  
**Authority:** Liquidity pools, equal-high/low clustering, sweeps, reclaim/acceptance, FVG, qualified Order Blocks, premium/discount and liquidity-path evidence.  
**Depends on:** `CANDLE_STRUCTURE.md`, `TECHNICAL_STRUCTURE_AND_LEVELS.md`, `MARKET_DATA_AND_HISTORY.md`

## Purpose

This document defines auditable liquidity/SMC-style market evidence. SMC terminology is shorthand for observable price/liquidity behaviour, not standalone authority.

> **Liquidity/SMC is evidence, not a universal trade gate. Post-liquidity behaviour matters more than the label itself.**

## Phase 3 implementation checkpoint

Implemented in:

```text
src/goldswingtraderai/intelligence/liquidity.py
```

The baseline consumes completed candles plus existing `StructureReport` and `QuantReport`; it does not independently recalculate swing structure or ATR.

Implemented outputs include:
- volatility/tick-aware clustered liquidity pools;
- buy-side/sell-side and internal/structural scope;
- pool state/significance/source count;
- pool events distinguishing probe/sweep/accepted break;
- deterministic three-candle FVG primitives with fill/mitigation state;
- structurally-qualified Order Block origin zones tied to meaningful break evidence;
- nearest buy-side/sell-side liquidity;
- directional path quality and bounded BUY/SELL liquidity evidence;
- coverage.

Current thresholds in `LiquidityConfig` are implementation baselines for replay calibration, not frozen market truth.

## Liquidity pools

Current source geometry is primarily confirmed/protected swings from Candle Structure. Nearby highs/lows are clustered with ATR/tick-aware tolerance so several nearly identical levels are not counted as separate liquidity pools.

Potential future sources remain:
- session highs/lows;
- prior-day highs/lows;
- range boundaries;
- richer external/major structure.

Any future source must preserve when the pool became knowable.

## Internal vs structural liquidity

The implementation distinguishes local/internal pools from stronger structural pools based on source structure/significance. This is soft target/reversal context, not an automatic trade rule.

## Liquidity lifecycle

Current typed baseline states include:

```text
UNTOUCHED
APPROACHED
PROBED
SWEPT
RECLAIMED
ACCEPTED_BEYOND
```

Future richer `FORMING/CONFIRMED/CONSUMED/STALE` lifecycle can be added when chronological replay tests justify it.

## Sweep model

A meaningful reversal-style sweep requires a pool that existed before the event plus failed acceptance/reclaim behaviour. A wick through a level is not automatically a reversal.

The current event types are:

```text
PROBE
CONFIRMED_SWEEP
ACCEPTED_BREAK
```

Conceptually:

```text
liquidity taken + acceptance beyond
→ breakout/continuation evidence

liquidity taken + failed acceptance/reclaim
→ sweep/failed-breakout reversal evidence
```

Strategy families decide how to use these facts.

## Fair Value Gap

The baseline uses deterministic three-candle imbalance geometry and stores:
- direction;
- timeframe;
- bounds;
- `created_at`;
- fill fraction;
- lifecycle state.

Current states:

```text
FRESH
PARTIAL
MITIGATED
```

FVG remains supporting location/continuation evidence and is never mandatory for every trade.

## Qualified Order Block

The code does not label every last opposite candle as an OB. A baseline OB must be tied to a meaningful structural break event and searches a bounded lookback for a defensible opposite-candle origin zone.

Current states:

```text
FRESH
TESTED
INVALIDATED
```

Future quality/lifecycle refinement may add weakening/mitigation detail after replay evidence.

## Correlation and double counting

A sweep, rejection, MSS, FVG and OB may describe one underlying market episode. The desk therefore publishes a bounded combined report; later scoring/fusion must not simply add every label as independent certainty.

This remains a critical architecture rule.

## Premium / discount

Premium/discount remains part of the authority design but is not yet a full production primitive in the Phase-3 baseline. When implemented, it must use a versioned meaningful dealing range rather than arbitrary recent high/low and remain soft location evidence.

## Liquidity path

Current typed path quality includes:

```text
OPEN
MIXED
CROWDED
UNKNOWN
```

Nearest liquidity and ATR-normalized pool density contribute to path context. A liquidity pool is a possible objective/magnet, never a guaranteed target.

## Strategy relationships

Liquidity evidence may support:
- Trend Pullback Continuation — location/path context;
- Breakout Expansion — liquidity objective + acceptance;
- Breakout Retest Continuation — broken pool/structure + retest;
- Liquidity Sweep Reversal — primary family evidence;
- Failed Breakout Reversal — liquidity taken + failed acceptance;
- Compression Expansion — built-up pools + release path.

No family requires every SMC primitive.

## Runtime integration

```text
completed candles + StructureReport + QuantReport
→ LiquidityReport
→ IntelligenceSnapshot
→ strategy-family consumers
```

The desk has no direct MT5, risk or broker-write access.

## Chronology and replay

All pools/primitives must preserve when they became knowable. A pool cannot be retroactively created only because future price later sweeps it. FVG/OB/sweep state must be replayed from contemporaneous completed candles.

## Failure behaviour

Missing optional FVG/OB evidence is absent support, not score zero. Missing structural/ATR prerequisites degrade coverage rather than invent geometry.

## Dashboard visibility

Compact future example:

```text
Liquidity Bias     BUY
Nearest BSL        4348
Nearest SSL        4311
Sweep State        SSL SWEPT + RECLAIMED
Path               OPEN UPSIDE
```

## Tests required / current evidence

Required:
- adaptive pool clustering/deduplication;
- pool existed before sweep;
- sweep versus accepted-break distinction;
- FVG creation/mitigation chronology;
- qualified OB requirements;
- correlated-event double-count protection;
- dealing-range versioning when premium/discount is implemented;
- replay no-lookahead.

Phase-3 deterministic baseline coverage exists in `tests/test_technical_liquidity.py` and unified integration in `tests/test_intelligence_snapshot.py`.

## Explicit non-goals

This desk must not:
- redefine BOS/MSS;
- treat every wick as a sweep;
- treat every opposite candle as an OB;
- require FVG/OB for every trade;
- claim liquidity targets are guaranteed;
- directly grant broker authority.

## Open calibration questions

- pool clustering tolerance;
- sweep penetration/reclaim quality;
- FVG minimum normalized size/quality;
- OB qualification/mitigation thresholds;
- liquidity-path weights;
- premium/discount dealing-range implementation;
- additional session/prior-day liquidity sources.
