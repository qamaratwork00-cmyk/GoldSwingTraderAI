# GoldSwingTraderAI — Technical Structure and Levels

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Support/resistance zones, structural level lifecycle, range geometry, location quality and target-room context.  
**Depends on:** `CANDLE_STRUCTURE.md`, `MARKET_DATA_AND_HISTORY.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

This document defines how confirmed market structure is converted into usable technical zones and location context. It does **not** redefine swing, BOS or MSS semantics; those remain owned by `CANDLE_STRUCTURE.md`.

Core distinction:

> **Structure tells what the market is doing. Location tells where current price stands relative to meaningful structure.**

## Zones, not exact lines

Support/resistance should be represented as adaptive price zones rather than single-price certainties. Zone width may use:

- volatility/ATR;
- swing geometry;
- reaction-candle range;
- clustering of repeated reactions;
- displacement origin;
- broker tick/point precision.

A fixed-dollar or fixed-pip width is not the intended design.

## Technical level types

The Technical Structure engine may publish:

- confirmed/protected/external swing zones;
- prior qualified-break/BOS boundaries;
- failed-break boundaries;
- range high, range low and equilibrium;
- prior-day/session high/low as technical reference facts;
- repeated support/resistance reaction zones;
- displacement-origin reaction areas.

Liquidity-specific interpretations such as equal highs/lows, sweep zones, FVG and qualified Order Blocks are owned by `LIQUIDITY_AND_SMC.md`.

## Zone quality

Each zone should expose bounded quality evidence such as:

- structural significance;
- timeframe relevance;
- freshness;
- number and quality of reactions;
- displacement produced from the zone;
- whether it caused or supported a qualified break;
- penetration/consumption history;
- higher-timeframe overlap;
- current validity.

Exact weights are not frozen.

## Freshness and consumption

A zone is not strengthened indefinitely by repeated touches. The engine should consider:

- depth of penetration;
- number of meaningful tests;
- time spent inside the zone;
- completed closes through it;
- quality of recovery/rejection;
- whether newer structure supersedes it.

Repeated use may weaken or consume a level.

## Zone lifecycle

Provisional states:

```text
ACTIVE
WEAKENING
BROKEN
RETEST_CANDIDATE
RECLAIMED
CONSUMED
STALE
```

A broken level should not simply disappear. Role-transition examples include:

```text
RESISTANCE → BROKEN_UP → RETEST_CANDIDATE → ACCEPTED_AS_SUPPORT
```

or:

```text
RESISTANCE → BROKEN_UP → FAILED_BREAK → RESISTANCE_RECLAIMED
```

The exact transition criteria remain research/calibration items.

## Composite zones and conflict

Compatible overlapping zones may be represented as one composite zone to reduce double-counting, for example:

```text
H1 support + M15 support + BOS retest
→ COMPOSITE SUPPORT
```

Opposing zones must not be merged blindly. Meaningful overlap between support and resistance may be reported as a `STRUCTURAL_CONFLICT_ZONE`.

## Location Engine

The Location Engine should evaluate BUY and SELL location independently.

Typical BUY questions:

- Is price near meaningful support/protected structure?
- Is price inside a valid retest/reclaim area?
- How much room remains to opposing structure?
- Is the entry extended/chased relative to the active leg?
- Is price directly below a major target/resistance area?

SELL logic is the directional inverse.

Suggested outputs:

- BUY Location Score;
- SELL Location Score;
- nearest meaningful support;
- nearest meaningful resistance;
- target-room estimate;
- extension state;
- structural-conflict state;
- concise reasons/counter-reasons.

Human-facing location categories may include:

```text
EXCELLENT
GOOD
NEUTRAL
POOR
DANGEROUS
```

These are soft market evidence, not universal hard gates.

## Range context

The engine should identify usable range geometry when appropriate:

- range high;
- range low;
- equilibrium/mid-area;
- internal rotations;
- breakout boundaries.

The middle of a mature range is usually low-quality location, while range edges may support family-specific reversal or breakout logic.

## Target-room context

Location should publish remaining structural room toward:

- the nearest material obstacle;
- the primary structural objective;
- the next higher-timeframe/external objective where known.

These facts support the Trade Plan and Target Desk. This document does not decide broker TP placement.

## Strategy-aware interpretation

The same zone can mean different things for different families.

Example: a major resistance zone may be:

- poor BUY location for `TREND_PULLBACK_CONTINUATION`;
- useful breakout reference for `BREAKOUT_EXPANSION` if acceptance occurs beyond it;
- strong SELL context for `FAILED_BREAKOUT_REVERSAL` if acceptance fails.

Therefore the Location Engine publishes facts/quality; strategy families apply family semantics.

## Multi-timeframe hierarchy

Typical context:

```text
H4  major macro zones / external boundaries
H1  directional structural zones
M15 working opportunity/location zones
M5  execution/local zones
```

Higher-timeframe zones provide stronger context but are not automatic vetoes for all strategies.

## Outputs

The Technical Structure / Location desk should expose at least:

- active zones with IDs, bounds, type, timeframe and state;
- zone quality/freshness/consumption;
- current range state where applicable;
- BUY/SELL Location scores;
- nearest opposing/supporting structure;
- target-room facts;
- extension/chase context supplied to timing;
- structural-conflict flags;
- reasons/counter-evidence.

## Failure behaviour

If required structural source data is invalid, the desk returns UNKNOWN/DEGRADED rather than inventing levels. Missing optional zones do not become zero score by default.

## Replay and persistence

Zone creation, break, reclaim and stale transitions must be chronological and reproducible from information available at the time. Rebuilt state after restart must not expose future-confirmed structure early.

## Dashboard visibility

The main dashboard should show only compact location information, for example:

```text
Location       GOOD BUY
Nearest Support 4312–4315
Nearest Resist  4346–4349
Target Path     OPEN
Conflict        LOW
```

Detailed zone maps belong in diagnostics/research.

## Tests required

- zone lifecycle transitions;
- role reversal after qualified breaks;
- repeated-test weakening/consumption;
- multi-timeframe zone separation;
- composite-zone double-count protection;
- conflict-zone handling;
- target-room calculations;
- deterministic replay/rebuild.

## Explicit non-goals

This engine must not:

- redefine BOS/MSS or swing confirmation;
- interpret FVG/OB/sweeps as its own concepts;
- place orders;
- make location a universal hard trade gate;
- convert premium/discount alone into BUY/SELL authority.

## Open questions

- exact zone-width normalization;
- exact zone-quality weights;
- exact consumption/decay thresholds;
- exact family-specific location influence;
- exact composite-zone merge tolerance.