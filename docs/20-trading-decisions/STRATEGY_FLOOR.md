# GoldSwingTraderAI — Strategy Floor

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Production strategy-family architecture

## Core principle

Strategy families run in parallel against the same verified market snapshot. No family is evaluated only after another family fails. Each family is an independent market hypothesis built from shared audited market primitives.

## Provisional production families

### 1. TREND_PULLBACK_CONTINUATION

Directional H1/M15 structure remains intact, price corrects into a meaningful location, and M5 timing shows evidence that the correction is ending and continuation is resuming.

FVG/OB/liquidity/EMA context may improve the setup but are not all mandatory.

### 2. BREAKOUT_EXPANSION

A meaningful range/structure/compression resolves with decisive directional acceptance and enough remaining room to justify participation before a perfect retest occurs.

The family must distinguish genuine acceptance from a wick-only breakout and must control late-entry/chase risk.

### 3. BREAKOUT_RETEST_CONTINUATION

A meaningful structural break occurs, price returns to the broken area, and subsequent behaviour confirms acceptance/rejection consistent with continuation.

### 4. LIQUIDITY_SWEEP_REVERSAL

Meaningful liquidity is taken, price fails to accept beyond the level, reclaims, and develops credible opposing structural/candle evidence.

A long wick by itself is not sufficient.

### 5. FAILED_BREAKOUT_REVERSAL

Price attempts and appears to break an important area but cannot maintain acceptance, returns into the prior structure/range, and develops credible opposite-direction evidence.

This is related to liquidity reversal but is treated as a distinct market narrative.

### 6. COMPRESSION_EXPANSION

Volatility and structure contract, liquidity accumulates, then the market resolves with directional expansion/acceptance. The family does not predict direction before evidence appears; BUY and SELL release cases compete.

## Evidence primitives, not automatic strategies

Initially these are shared evidence primitives rather than guaranteed standalone production families:

- FVG
- qualified Order Block
- premium/discount
- session highs/lows
- liquidity pools
- EMA
- RSI
- ATR
- individual candle patterns
- support/resistance

A future governed research process may demonstrate that a primitive or newly discovered behaviour deserves its own production-family candidate.

## Standard family output

Each strategy desk should eventually return a structured contract containing at least:

```text
family
BUY score
SELL score
direction / neutral
family quality
freshness
stage
primary evidence
supporting evidence
conflicting evidence
preferred timing profile
invalidation
structural target
expansion potential
```

## Parallel consensus

Compatible families may support the same direction. Agreement can add a bounded consensus bonus but correlated evidence must not be counted as independent certainty multiple times.

Likewise, strong opposing families should increase conflict rather than be silently ignored.

## Market episode identity

Multiple strategy labels may describe different phases of the same underlying market move. A future `Market Episode` identity should allow the system to understand relationships such as:

```text
Compression Expansion
→ Breakout
→ Breakout Retest
→ Trend Continuation
```

This helps prevent duplicate entries, supports legitimate re-entry, and improves post-trade research.

## Frequency philosophy

The floor should maximize valid opportunity coverage, not raw trade count. A strategy is not penalized merely for being selective, but the overall system should not become so restrictive that it detects only a tiny fraction of objectively valid large-move opportunities.
