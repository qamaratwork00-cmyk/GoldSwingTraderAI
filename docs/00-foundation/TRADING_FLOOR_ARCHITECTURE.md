# GoldSwingTraderAI — Trading Floor Architecture

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Specialist-desk ownership model

## Purpose

GoldSwingTraderAI is designed as a coordinated trading floor rather than one monolithic strategy function. Every desk has a bounded responsibility, a standard evidence output and explicit limits on authority.

## Core desks

### Market Data Desk

**Owns:** broker connection, symbol facts, quote freshness, candle retrieval, timeframe synchronization, data quality and session availability facts.

**May:** publish validated market snapshots and data-health state.

**May not:** create BUY/SELL authority or modify risk.

### Candle Behaviour Desk

**Owns:** candle anatomy, body/wick ratios, close location, engulf/rejection/outside/inside behaviour, directional sequences, displacement, compression and exhaustion clues.

**Output:** BUY/SELL candle evidence, sequence quality, confidence and reasons.

### Structure Desk

**Owns:** swings, HH/HL/LH/LL, BOS, MSS, reclaim/loss of structure and structural invalidation.

### Liquidity Desk

**Owns:** meaningful liquidity pools, session extremes, sweeps, failed acceptance, FVG context, qualified OB context and premium/discount/location support.

FVG/OB are evidence primitives by default, not automatic strategies.

### Technical Context Desk

**Owns:** H4/H1 regime and directional structure, major support/resistance, range/transition context and important higher-timeframe levels.

### Indicator / Quant Desk

**Owns:** EMA, RSI, ATR, volatility normalization, range statistics and other bounded quantitative context.

**May not:** hard-block a trade merely because one indicator is imperfect unless a future frozen contract explicitly grants that authority.

### Fundamental / Macro Desk

**Owns:** macro/market context and scheduled event information where reliable data exists.

It has two conceptually separate outputs:

1. **Context opinion** — soft evidence for Gold/USD/rates/macro conditions.
2. **Event safety** — hard PASS/BLOCK/UNKNOWN when scheduled high-impact news policy applies.

A holiday calendar is context. Actual broker tradeability and live market data remain market-state authority.

### Expansion / Volatility Desk

**Owns:** compression, volatility release, expansion phase, directional impulse strength, late/exhausted move risk and remaining expansion potential.

### Strategy Desks

Initial provisional desks:

- Trend Pullback Continuation
- Breakout Expansion
- Breakout Retest Continuation
- Liquidity Sweep Reversal
- Failed Breakout Reversal
- Compression Expansion

All desks evaluate in parallel and may produce BUY, SELL or neutral evidence.

### BUY Thesis Team

Builds the strongest coherent bullish case from specialist evidence. It does not suppress bearish evidence.

### SELL Thesis Team

Builds the strongest coherent bearish case independently from the same snapshot.

### Debate / Red Team

Challenges the leading thesis with concrete opposing evidence. It asks whether the move is late, target room is poor, the breakout is failing, opposite structure is credible, or evidence is duplicated/correlated.

It may reduce confidence or recommend WAIT. It may not invent arbitrary blockers.

### Decision Fusion Board

Combines specialist evidence into:

- BUY Thesis
- SELL Thesis
- Directional Edge
- Conflict Score
- Opportunity Score
- Entry Timing Score
- Coverage/Confidence
- Final Trade Score

It does not override hard safety/risk authority.

### Risk Desk

Owns monetary SL risk, lot sizing, margin, aggregate exposure, daily-loss state and risk locks.

Risk approval is binary authority, not a popularity vote.

### Safety / Control Desk

Owns hard broker/account/data/news/session/order-integrity permission.

### Execution Desk

Receives only fully approved trade instructions. It owns fresh executable price checks, broker pre-check, one governed submit and reconciliation.

### Trade Management Desk

Runs after entry. It evaluates continuation versus reversal and returns HOLD, PROTECT, TRAIL, RUNNER or EXIT within hard execution/risk constraints.

### Quant Research / Strategy Discovery Lab

Analyses completed trades, missed moves, rejected opportunities, entry quality, exit quality, family performance and candidate strategies.

It may propose bounded candidates but may not directly deploy new live authority.

## Standard analytical output

Where applicable, desks should produce a structured result similar to:

```text
BUY evidence
SELL evidence
confidence
coverage/state
primary reasons
conflicting reasons
freshness
```

The exact data schema will be frozen before implementation.
