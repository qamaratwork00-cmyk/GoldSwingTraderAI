# GoldSwingTraderAI — Indicators and Volatility

**Status:** PROVISIONAL — IMPLEMENTED BASELINE  
**Version:** 0.3-implementation  
**Authority:** EMA/RSI/ATR evidence, volatility normalization, momentum phase, compression/expansion quantification, extension/chase and exhaustion metrics.  
**Depends on:** `CANDLE_STRUCTURE.md`, `MARKET_DATA_AND_HISTORY.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

Indicators support and normalize price behaviour; they do not replace structure or become standalone trade authority.

> **Indicators explain and quantify market behaviour. Structure remains primary market language.**

## Current implementation checkpoint

Implemented in:

```text
src/goldswingtraderai/intelligence/indicators.py
src/goldswingtraderai/intelligence/snapshot.py
```

Current baseline periods:

```text
EMA fast   20
EMA slow   50
RSI        14 (Wilder)
ATR        14 (Wilder)
```

These are explicit implementation defaults, not frozen profitability assumptions. Replay/research may calibrate them without turning the system into indicator filter soup.

`IndicatorSeries` is chronological and uses `None` before enough completed history exists. The unified Intelligence snapshot computes each series once per timeframe and shares ATR with Candle Structure so equivalent deterministic facts are not redundantly recalculated.

## EMA evidence

EMA evidence includes:

- EMA20 versus EMA50 ordering;
- current trend-support direction;
- price distance from EMA20 for extension context.

`EMA20 > EMA50` is never a BUY signal by itself. Slope/separation/pullback-depth remain possible research refinements rather than mandatory V1 filters.

## RSI evidence

RSI is momentum/pressure context, not rigid `>70 SELL` / `<30 BUY` reversal logic.

Current momentum logic uses RSI as one supporting input alongside EMA flow, directional progress, candle body and extension.

Divergence remains a research candidate, not current production authority.

## ATR and normalization

ATR normalizes:

- candle strength;
- swing confirmation/significance;
- technical zone width;
- liquidity clustering;
- volatility regime;
- extension/chase context;
- structural stop/target context;
- execution-relative measurements such as drift/stop distance through downstream authorities.

ATR does not independently set final broker SL or TP.

## Volatility states

```text
UNKNOWN
QUIET
NORMAL
BUILDING
EXPANDING
EXTREME
DISLOCATED
```

The implementation compares current ATR with rolling ATR context. Baseline ratios live in `QuantConfig` and are research-calibratable.

`EXTREME` may still be tradeable. `DISLOCATED` is adverse market evidence consumed by downstream session/news/execution safety where appropriate; the Quant desk itself does not issue broker-write permission.

## Relative volatility

Prefer normalized facts such as:

- current ATR / recent median ATR;
- latest candle range / ATR;
- optional future percentile/distribution context if validated.

Absolute Gold movement alone is not stable market truth.

## Momentum

Current implementation exposes:

```text
UNKNOWN
BUILDING
EXPANDING
MATURE
EXHAUSTING
REVERSING
```

Momentum combines EMA flow, latest directional progress, body/ATR, RSI pressure and extension state.

Strong momentum does not automatically mean good entry timing.

## Extension / chase metrics

The current Quant baseline measures price distance from EMA20 in ATR units:

```text
UNKNOWN
FRESH
NORMAL
EXTENDED
SEVERELY_EXTENDED
```

This is only one extension primitive. The implemented Entry Timing and Trade Plan also consider structure, location and target room; the Execution layer separately checks fresh price drift. EMA distance alone is never final chase authority.

## Compression and expansion

Quant supplies volatility normalization. Candle Structure owns sequence-level compression/expansion classification. Strategy/Fusion consume these shared reports without counting one market event repeatedly as independent certainty.

## Exhaustion risk

The baseline can classify `EXHAUSTING` when a severely extended move loses normalized body efficiency. Additional rejection/follow-through/target-proximity features may be researched later.

Exhaustion remains evidence, not automatic exit/reversal authority. Open-trade action belongs to the Trade Manager.

## Spread quality

Hard spread permission is not owned here. Market Data publishes spread facts; `execution/checks.py` and `EXECUTION_AND_BROKER_SAFETY.md` own the implemented spread-ratio/stop-distance execution rules.

## Outputs

`QuantReport` publishes:

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

Unavailable indicators remain `None`/`UNKNOWN`; they are not silently converted to bullish/bearish score zero. Dependent consumers respect coverage.

## Multi-timeframe use

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
→ same ATR passed to Candle Structure
→ Technical/Liquidity/Confluence consume shared facts
→ reusable IntelligenceSnapshot
→ Strategy/Decision/Timing/Management consumers
```

No indicator module queries MT5 or performs broker writes.

## Replay/research

Phase-10 chronological replay reuses the same indicator/Intelligence semantics at completed-bar prefixes. Research can ablate/tune indicator parameters while monitoring Net R, drawdown, opportunity recall, capture and trade frequency—not just win rate.

## Dashboard visibility

Compact example:

```text
EMA Flow        BUY
RSI             61 BULLISH
Volatility      EXPANDING
Momentum        BUILDING
Extension       NORMAL
```

## Tests / current evidence

Deterministic coverage includes:

- indicator chronology/no future values;
- ATR normalization;
- missing-indicator UNKNOWN handling;
- volatility/extension states;
- shared ATR reuse with Candle Structure;
- no duplicate MT5 reads from indicator code;
- chronological replay prefix behaviour.

Relevant suites include `tests/test_indicators_structure.py` and `tests/test_intelligence_snapshot.py`, with Phase-10 replay exercising shared production semantics.

## Explicit non-goals

This desk must not:

- convert RSI overbought/oversold into automatic reversal;
- let EMA order override structure;
- set structural stops by itself;
- hard-block trades for one imperfect soft indicator;
- place orders.

## Open calibration questions

- whether EMA20/EMA50/RSI14/ATR14 remain best after replay;
- volatility-ratio bands;
- extension/chase thresholds;
- future RSI state labels/divergence value;
- whether percentile-based volatility adds useful information without unnecessary complexity.
