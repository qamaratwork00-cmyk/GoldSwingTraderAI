# GoldSwingTraderAI — Trading Floor Architecture

**Status:** PROVISIONAL  
**Version:** 0.2-design  
**Authority:** Specialist-desk ownership model

## Purpose

GoldSwingTraderAI is designed as a coordinated trading floor rather than one monolithic strategy function. Every desk has a bounded responsibility, structured output and explicit limit on authority.

## Core desks

### Market Data Desk

**Owns:** broker connection/read-only facts, symbol facts, quote freshness, candle retrieval, timeframe synchronization, data quality and broker tradeability facts.

**May:** publish validated immutable market snapshots and data-health state.

**May not:** create BUY/SELL authority, size risk or perform broker writes.

### Candle / Structure Desk

**Owns:** candle anatomy/sequences, swings, protected/external structure, BOS/MSS geometry, displacement, rejection, compression/expansion price-action evidence and exhaustion clues.

Detailed semantics are owned by `../10-market-intelligence/CANDLE_STRUCTURE.md`.

### Technical / Location Desk

**Owns:** generic support/resistance zones, ranges, role flips, location quality, target room and structural conflict zones.

It consumes Candle Structure geometry rather than redefining BOS/MSS.

### Liquidity / SMC Desk

**Owns:** meaningful liquidity pools, equal highs/lows, internal/external liquidity, sweeps/acceptance/reclaim, FVG context, qualified OB context, premium/discount and liquidity path.

FVG/OB are evidence primitives by default, not automatic strategies or universal entry requirements.

### Indicator / Quant Desk

**Owns:** EMA, RSI, ATR, volatility normalization, momentum/extension state, range statistics and other bounded quantitative context.

It may quantify compression/expansion/exhaustion, but the underlying candle behaviour remains owned by Candle Structure. A separate Expansion view may aggregate Candle + Quant outputs; it should not become a duplicate authority.

**May not:** hard-block a trade merely because one optional indicator is imperfect unless a later frozen contract explicitly grants a safety dependency.

### Fundamental / Macro Desk

**Owns:** soft macro/market opinion and provider-backed scheduled-event facts where reliable information exists.

It publishes two different kinds of information:

1. **Fundamental context opinion** — soft Gold/USD/rates/macro evidence.
2. **Event facts/provider health** — inputs consumed by hard news-safety policy.

It does **not** itself grant final broker-write permission. `../30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` owns hard `NEWS_CLEAR / NEWS_BLACKOUT / NEWS_SAFETY_UNKNOWN / POST_NEWS_WARMUP` permission state.

Holiday calendar information is context. Actual broker tradeability/live market facts remain execution authority.

### Session Context Desk

**Owns:** Asia/London/New York participation context, overlaps, session highs/lows and intraday session behaviour as market evidence.

It does not own hard OPEN/CLOSED/REOPEN risk-state semantics.

### Strategy Desks

Initial provisional families:

- Trend Pullback Continuation;
- Breakout Expansion;
- Breakout Retest Continuation;
- Liquidity Sweep Reversal;
- Failed Breakout Reversal;
- Compression Expansion.

All desks evaluate in parallel and may produce BUY, SELL or neutral evidence. One strong coherent family may be sufficient to create an opportunity; every primitive need not align.

### BUY Thesis Team

Builds the strongest coherent bullish case from specialist/family evidence. It does not suppress bearish evidence.

### SELL Thesis Team

Builds the strongest coherent bearish case independently from the same snapshot.

### Debate / Red Team

Challenges the leading thesis with concrete opposing evidence such as poor location/target room, late extension, failed breakout, credible opposite structure or duplicated/correlated support.

It may reduce confidence or recommend WAIT. It may not invent arbitrary blockers.

### Decision Fusion Board

Combines analytical evidence into:

- BUY Thesis;
- SELL Thesis;
- Directional Edge;
- Conflict Score;
- Opportunity Score;
- Entry Timing Score;
- Coverage/Confidence;
- operator-facing Final Trade Score;
- primary/supporting reasons and decision trace.

It does not override hard safety/risk authority.

### Entry Timing Desk

Owns the persistent setup lifecycle and M5 executable moment. It distinguishes ENTER, WAIT, MISSED and INVALID while preserving a valid opportunity when timing is temporarily poor.

### Trade Plan Desk

Owns the pre-risk structural plan:

- approved entry reference;
- structural invalidation/SL;
- volatility-aware stop buffer;
- immediate/primary/expansion/runner objectives;
- target room/RR;
- immutable original R basis.

It does not size volume or call the broker.

### Risk Desk

Owns monetary SL risk, dynamic lot sizing, min-lot affordability, margin policy, aggregate exposure, daily-loss state and risk locks.

Risk approval is binary/hard authority, not a popularity vote.

### Session / News / System Permission Layer

Owns hard permission states derived from broker market state, required event safety, risk state and critical system/data/order truth.

It consumes authoritative subsystem results rather than reimplementing them.

### Central Execution Permission Gate

This is the final auditable broker-write authorization boundary.

It consumes authoritative environment/account/data/news/risk/position/order/controller/fresh-execution results and returns conceptually:

```text
ALLOW / BLOCK / UNKNOWN
primary reason
secondary reasons
```

Initial release policy is DEMO-first. Future explicitly approved REAL execution uses this same gate/path rather than a separate live engine.

### Execution Desk

Receives only approved broker-write intents. It owns fresh executable price/spec checks, durable pre-submit intent requirement, broker pre-check, one governed irreversible request and reconciliation.

Create/modify/close actions all use the governed execution path. Ambiguous acknowledgements are never blind-retried.

### Trade Management Desk

Runs after entry. It evaluates continuation versus reversal and returns HOLD, PROTECT, TRAIL, RUNNER or EXIT within hard execution/risk constraints.

Its proposed modify/close actions still pass through the central broker-write permission/execution boundary.

### Persistence / Recovery Service

Owns durable order/trade/risk lifecycle, Strategy Registry storage, learning/research/promotion state persistence, schema integrity, restart recovery, backup/restore and laptop migration mechanics.

It stores state; it does not redefine strategy/risk semantics.

### Quant Research / Strategy Discovery Lab

Analyses completed trades plus missed, rejected/blocked and invalidated opportunities. It owns StrategyMemory, entry/exit learning, validation, strategy discovery, declarative invention and candidate evidence.

It may propose bounded candidates but may not directly deploy live authority, mutate hard risk or access raw broker writes.

### System Health / Diagnostics

Aggregates subsystem health, primary/secondary faults, trading impact and recovery state. It must distinguish normal market/risk decisions from actual system faults.

### Operator / Dashboard

Displays market/decision/setup/trade/risk/execution/learning/backup/health state using stable reason codes and concise explanations. It is presentation only.

## Standard analytical output

Where applicable, analytical desks should produce structured output similar to:

```text
BUY evidence
SELL evidence
confidence
coverage/state
primary reasons
conflicting reasons
freshness
source IDs/episode references where relevant
```

Hard-authority desks additionally return explicit PASS/BLOCK/UNKNOWN (or equivalent state) with stable reason codes.

## Dependency rule

The trading floor is intentionally asymmetric near the broker boundary:

```text
many analytical producers
        ↓
central decisions/plan/risk
        ↓
ONE final execution permission boundary
        ↓
ONE governed broker-write path
```

No strategy, dashboard, research or learning desk may bypass that final boundary.
