# GoldSwingTraderAI — Indicators and Volatility

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** EMA/RSI/ATR evidence, volatility normalization, momentum phase, compression/expansion quantification, extension/chase and exhaustion metrics.  
**Depends on:** `CANDLE_STRUCTURE.md`, `MARKET_DATA_AND_HISTORY.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

Indicators support and normalize price behaviour; they do not replace structure or become standalone trade authority.

> **Indicators explain and quantify market behaviour. Structure remains primary market language.**

## Initial indicator set

Initial production-supporting indicators are provisionally:

- EMA20;
- EMA50;
- RSI;
- ATR.

Exact periods/thresholds may be calibrated later, but any change must preserve interpretability and avoid indicator filter soup.

## EMA evidence

EMA evidence may include:

- EMA20 versus EMA50 ordering;
- slopes;
- separation/compression;
- price distance from EMA20/EMA50;
- pullback depth relative to the active trend leg.

`EMA20 > EMA50` is not a BUY signal by itself. EMA may support trend flow but cannot override contrary structural evidence.

## RSI evidence

RSI should be used for momentum/pressure context, reset behaviour and deterioration—not rigid `>70 SELL` / `<30 BUY` logic.

Useful concepts may include:

```text
STRONG_BEAR
BEARISH
NEUTRAL
BULLISH
STRONG_BULL
EXTREME
```

Exact numeric bands remain open. Divergence may be researched as supporting evidence but is not standalone authority.

## ATR and normalization

ATR is a normalization tool for:

- candle strength;
- swing significance;
- zone width;
- displacement quality;
- extension/chase;
- stop-buffer context;
- target-distance context;
- volatility regime;
- spread quality.

ATR does not automatically set the final SL or TP.

## Volatility states

Provisional states:

```text
QUIET
NORMAL
BUILDING
EXPANDING
EXTREME
DISLOCATED
```

`EXTREME` may still be tradeable. `DISLOCATED` indicates market/data/execution quality may be unsafe and can feed hard safety elsewhere.

## Relative volatility

Absolute Gold movement is not sufficient. Quantification should prefer normalized facts such as:

- current range / ATR;
- current range / recent median range;
- body size / recent median body;
- ATR percentile over a rolling historical context.

Exact percentile bands remain open.

## Momentum

The desk should expose independent BUY and SELL momentum evidence from bounded, non-duplicative inputs such as:

- EMA slope;
- directional progress;
- body/range expansion;
- close efficiency;
- RSI pressure;
- persistence/follow-through.

Correlated features should be grouped/capped rather than counted as independent certainty.

## Momentum phase

Provisional momentum phases:

```text
BUILDING
EXPANDING
MATURE
EXHAUSTING
REVERSING
```

Strong momentum does not automatically mean good entry timing. A mature/extended move can have high momentum and poor entry efficiency.

## Extension / chase metrics

The desk computes raw extension facts for Entry Timing, including distance from:

- last structural base;
- breakout/retest level;
- recent M5/M15 pullback origin;
- EMA references where useful;
- current move size relative to ATR;
- remaining structural target room.

Human state may include:

```text
FRESH
NORMAL
EXTENDED
SEVERELY_EXTENDED
```

Chase risk should consider distance already travelled **relative to distance remaining**, not only EMA distance.

## Compression and expansion quantification

Quantitative compression evidence may include:

- falling ATR;
- shrinking median range/body;
- increasing overlap;
- narrowing local swing amplitude.

Expansion quality may include:

- normalized range/body expansion;
- close efficiency;
- directional progress;
- follow-through.

Candle Structure owns the underlying price-action definition; this desk owns quantitative normalization/support.

## Exhaustion risk

Potential inputs:

- extreme extension percentile;
- declining body efficiency;
- increasing opposite wick/rejection;
- RSI/momentum deterioration;
- reduced follow-through;
- target proximity.

Exhaustion remains evidence, not an automatic exit/reversal rule.

## Spread quality

The desk may expose descriptive spread quality using normalized measures such as spread/ATR or spread/expected move:

```text
GOOD
ELEVATED
POOR
```

Hard execution permission remains owned by risk/execution documents.

## Outputs

At minimum:

- BUY Trend Support;
- SELL Trend Support;
- BUY Momentum;
- SELL Momentum;
- Momentum Phase;
- Volatility State;
- ATR/volatility percentile context;
- Compression Score;
- Expansion Quality;
- Extension State;
- Exhaustion Risk;
- Spread Quality;
- confidence/coverage and reasons.

## Missing evidence

Unavailable optional indicators are `UNKNOWN`, not score zero. If a required normalization primitive such as ATR is unavailable, dependent outputs should become UNKNOWN/DEGRADED and affected downstream logic must not invent substitutes.

## Multi-timeframe use

Typical use:

```text
H4/H1  trend/context support
M15    opportunity/volatility context
M5     timing/momentum/extension
```

The system must not create an all-timeframe indicator veto matrix.

## Dashboard visibility

Compact example:

```text
EMA Flow        BUY
RSI             61 BULLISH
Volatility      EXPANDING
Momentum        BUILDING
Extension       NORMAL
Exhaustion      LOW
```

## Tests required

- indicator chronology/no future values;
- ATR normalization invariance;
- missing-indicator UNKNOWN handling;
- volatility-state transitions;
- extension versus target-room logic;
- correlated-feature double-count protection;
- quant/candle-structure ownership separation.

## Explicit non-goals

This desk must not:

- convert RSI overbought/oversold into automatic reversal;
- let EMA order override structure;
- set final structural stops;
- hard-block trades for one imperfect soft indicator;
- place orders.

## Open questions

- exact indicator periods at V1 freeze;
- exact RSI state boundaries;
- ATR percentile bands;
- compression/expansion/exhaustion calibration;
- exact extension/chase normalization.