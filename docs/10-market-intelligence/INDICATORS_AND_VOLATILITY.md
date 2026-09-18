# GoldSwingTraderAI — Indicators and Volatility

**Status:** PROVISIONAL  
**Version:** 0.2-implementation-baseline  
**Authority:** EMA/RSI/ATR evidence, volatility normalization, momentum phase, compression/expansion quantification, extension/chase and exhaustion metrics.  
**Depends on:** `CANDLE_STRUCTURE.md`, `MARKET_DATA_AND_HISTORY.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

Indicators support and normalize price behaviour; they do not replace structure or become standalone trade authority.

> **Indicators explain and quantify market behaviour. Structure remains primary market language.**

## Phase 3 implementation checkpoint

Implemented in:

```text
src/goldswingtraderai/intelligence/indicators.py
```

Current baseline periods are:

```text
EMA fast   20
EMA slow   50
RSI        14 (Wilder)
ATR        14 (Wilder)
```

These are initial implementation defaults, not permanently frozen profitability assumptions. Research/replay may calibrate them later without turning the system into indicator filter soup.

`IndicatorSeries` is chronological and uses `None` before enough completed history exists. The unified `intelligence/snapshot.py` computes the series once per timeframe and shares ATR with Candle Structure so the same deterministic fact is not redundantly recalculated in normal runtime.

## EMA evidence

EMA evidence includes:

- EMA20 versus EMA50 ordering;
- current trend-support direction;
- price distance from the fast EMA for extension context.

Future bounded improvements may add slope/separation/pullback-depth detail. `EMA20 > EMA50` is never a BUY signal by itself.

## RSI evidence

RSI is used for momentum/pressure context, not rigid `>70 SELL` / `<30 BUY` reversal logic.

The Phase-3 momentum phase uses RSI as one supporting input alongside EMA flow, directional progress, candle body and extension.

Divergence remains a future research primitive and is not production authority.

## ATR and normalization

ATR normalizes:

- candle strength;
- swing confirmation/significance;
- technical zone width;
- liquidity clustering;
- volatility regime;
- extension/chase context;
- future stop/target/spread context.

ATR does not automatically set final broker SL or TP.

## Volatility states

Current typed states are:

```text
UNKNOWN
QUIET
NORMAL
BUILDING
EXPANDING
EXTREME
DISLOCATED
```

The implementation compares current ATR with the median of a rolling ATR context. Baseline ratios are explicit configuration values inside `QuantConfig` so replay/research can calibrate them.

`EXTREME` may still be tradeable. `DISLOCATED` is evidence that later market-data/execution safety may need to block/revalidate.

## Relative volatility

The desk prefers normalized facts such as:

- current ATR / recent median ATR;
- latest candle range / ATR through Candle Structure;
- future percentile/distribution context where validated.

Absolute Gold movement alone is not treated as stable market truth.

## Momentum

Phase-3 implementation exposes a bounded momentum phase from:

- EMA flow;
- latest directional progress;
- body size normalized by ATR;
- RSI pressure;
- extension state.

Typed phases:

```text
UNKNOWN
BUILDING
EXPANDING
MATURE
EXHAUSTING
REVERSING
```

Strong momentum does not automatically mean good entry timing.

## Extension / chase metrics

The current Quant baseline measures price distance from EMA20 in ATR units and classifies:

```text
UNKNOWN
FRESH
NORMAL
EXTENDED
SEVERELY_EXTENDED
```

This is only one extension primitive. Later Entry Timing must also consider structural base, breakout/retest location and remaining target room before deciding whether an entry is chased.

## Compression and expansion

Quant supplies volatility normalization. Candle Structure owns candle-sequence compression/expansion classification. Technical/Strategy consumers may combine those reports but must not double-count the same market event as independent certainty.

## Exhaustion risk

Current baseline can classify `EXHAUSTING` when a severely extended move loses normalized body efficiency. Future validated inputs may include rejection, follow-through deterioration and target proximity.

Exhaustion remains evidence, not automatic exit/reversal authority.

## Spread quality

Hard spread permission is not implemented in this desk. Market-data provides live spread facts; the later execution layer owns the frozen spread-ratio and stop-distance safety rules.

## Outputs

`QuantReport` currently publishes:

- timeframe;
- EMA fast/slow;
- RSI;
- ATR;
- trend support direction;
- volatility state + ratio;
- momentum phase;
- extension state + ATR-normalized extension;
- evidence coverage.

## Missing evidence

Unavailable indicators remain `None`/`UNKNOWN`; they are not silently converted to bearish/bullish score zero. Dependent consumers must respect coverage.

## Multi-timeframe use

Typical use remains:

```text
H4/H1  trend/context support
M15    opportunity/volatility context
M5     timing/momentum/extension
```

The system must not create an all-timeframe indicator veto matrix.

## Runtime integration

```text
completed CandleSeries
→ compute IndicatorSeries once
→ QuantReport
→ same ATR series passed to Candle Structure
→ Technical/Liquidity consume QuantReport
→ reusable IntelligenceSnapshot
```

No indicator module queries MT5 directly.

## Dashboard visibility

Compact future example:

```text
EMA Flow        BUY
RSI             61 BULLISH
Volatility      EXPANDING
Momentum        BUILDING
Extension       NORMAL
```

## Tests required / current evidence

Required:
- indicator chronology/no future values;
- ATR normalization invariance;
- missing-indicator UNKNOWN handling;
- volatility-state transitions;
- extension logic;
- correlated-feature double-count protection;
- quant/candle-structure ownership separation.

Phase-3 tests cover chronological EMA/RSI/ATR, no-future prefix behaviour and shared ATR reuse in `tests/test_indicators_structure.py` and `tests/test_intelligence_snapshot.py`.

## Explicit non-goals

This desk must not:

- convert RSI overbought/oversold into automatic reversal;
- let EMA order override structure;
- set final structural stops;
- hard-block trades for one imperfect soft indicator;
- place orders.

## Open calibration questions

- whether EMA20/EMA50/RSI14/ATR14 remain best after replay;
- volatility-ratio bands;
- extension/chase thresholds;
- future RSI state labels/divergence value;
- whether percentile-based volatility adds useful information without complexity.
