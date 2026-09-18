# GoldSwingTraderAI — Technical Structure and Levels

**Status:** PROVISIONAL  
**Version:** 0.3-implementation-baseline  
**Authority:** Support/resistance zones, structural level lifecycle, range geometry, location quality, target-room context, causal trendlines, Fibonacci geometry and broker-local volume-profile POC.  
**Depends on:** `CANDLE_STRUCTURE.md`, `MARKET_DATA_AND_HISTORY.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

This document defines how confirmed market structure is converted into usable technical zones and optional confluence context. It does **not** redefine swing, BOS or MSS semantics.

> **Structure tells what the market is doing. Location/confluence tells where current price stands relative to meaningful geometry.**

> **Trendline, Fibonacci and POC are accuracy/confluence tools only. They are never universal entry requirements, never hard safety blockers, and missing/opposing confluence must not automatically invalidate an otherwise valid setup.**

## Implementation checkpoint

Implemented in:

```text
src/goldswingtraderai/intelligence/technical.py
src/goldswingtraderai/intelligence/confluence.py
```

The current baseline consumes existing `StructureReport` + `QuantReport`; it never re-runs candle structure or ATR itself.

It publishes:
- adaptive support/resistance zones derived from confirmed/protected swings;
- zone side/state/quality/source count/protected-source flag;
- compatible-zone merging to reduce double counting;
- nearest support/resistance;
- BUY and SELL location categories;
- BUY/SELL target-room distance;
- equilibrium where both sides exist;
- structural conflict flag;
- causal support/resistance trendlines from confirmed swings;
- trendline TOUCH / BREAK / RECLAIM events;
- Fibonacci retracement/extension geometry from confirmed impulse anchors;
- broker-local volume-profile Point of Control (POC);
- whether POC source is real volume or tick-volume approximation;
- evidence coverage.

Current numerical values in `TechnicalConfig` / `ConfluenceConfig` are initial implementation defaults for replay calibration, not frozen market truth.

## Zones, not exact lines

Support/resistance is represented as volatility/tick-aware zones rather than exact-price certainty. Baseline width uses:

```text
max(broker tick-size floor, ATR fraction)
```

Confirmed/protected swing geometry is the source. Future validated sources may include role-reversed break boundaries, session levels and displacement-origin zones without changing swing semantics here.

## Trendline context

Trendlines are generated only from already-confirmed structural swings. A pivot is never used before its `confirmed_at` time, so replay/live behaviour remains causal.

The desk may expose:

```text
SUPPORT trendline
RESISTANCE trendline
ASCENDING / DESCENDING / FLAT
TOUCH / BREAK / RECLAIM / NONE
projected current price
ATR-normalized distance
```

Natural family relationships:
- support/resistance trendline touch or reclaim may strengthen Trend Pullback Continuation;
- resistance break may strengthen BUY breakout families;
- support break may strengthen SELL breakout families;
- break/retest behaviour may strengthen Breakout Retest Continuation;
- a trendline by itself does not create broker authority.

Trendline evidence is **bonus-only in V1**. Absence or disagreement does not subtract score or hard-block a setup.

## Fibonacci context

Fibonacci is anchored only to a confirmed structural impulse pair, not arbitrary recent highs/lows and not future pivots.

Initial research geometry includes:

```text
Retracement: 0.382 / 0.500 / 0.618 / 0.786
Extension:   1.272 / 1.618 / 2.000
```

The desk exposes the anchor direction, anchor swings, nearest Fib level and whether price is in core/deep retracement context.

Fib is **confluence, not permission**. A valid setup does not require a Fib touch, golden pocket, or exact ratio.

## Volume profile / POC

POC is computed from a bounded recent candle window and is explicitly broker-local:

```text
real_volume if broker provides meaningful values
else tick_volume approximation
```

The system records the source so a tick-volume POC is never presented as centralized exchange-volume truth.

Current implementation distributes each candle's volume across the price bins crossed by that candle and reports the highest-volume bin midpoint as POC. It exposes:

```text
POC price
ABOVE / BELOW / NEAR
volume source
lookback bars
bin count
ATR-normalized distance
```

POC is intentionally direction-neutral by itself. `POC_NEAR` can strengthen an existing directional confluence but cannot manufacture a BUY/SELL thesis alone.

## Zone quality and lifecycle

Typed lifecycle baseline includes:

```text
ACTIVE
WEAKENING
BROKEN
RETEST_CANDIDATE
RECLAIMED
CONSUMED
STALE
```

The initial implementation focuses on current structural zones and bounded quality. Richer chronological transition/consumption logic remains a replay-calibration extension and must not be backfilled using future knowledge.

Quality is influenced by source significance, protected status and merged source count rather than treating many nearby levels as independent proof.

## Compatible zones and conflict

Nearby zones of the same side may be merged into a composite zone using ATR-aware tolerance. Opposing support/resistance is not blindly merged.

When price is effectively constrained by nearby meaningful structure on both sides, the report can expose structural conflict rather than manufacturing directional certainty.

## Location Engine

BUY and SELL location are evaluated independently using distance to supporting structure, opposing structure, ATR normalization and available target room.

Typed categories:

```text
EXCELLENT
GOOD
NEUTRAL
POOR
DANGEROUS
UNKNOWN
```

These are soft evidence. A poor location may matter strongly to a pullback family while a breakout family may interpret the same resistance area as its reference level.

## Target-room context

The desk publishes remaining room toward the nearest meaningful opposing structure. This is a factual input for strategy/Trade Plan and does not decide broker TP placement.

Future target hierarchy remains owned by `../20-trading-decisions/TRADE_PLAN.md`.

## Multi-timeframe hierarchy

Each timeframe produces its own report:

```text
H4  major context
H1  directional structural zones/confluence
M15 primary opportunity/location/confluence
M5  local/timing confluence
```

`intelligence/snapshot.py` keeps these reports separate inside one `IntelligenceSnapshot`; lower-timeframe facts do not overwrite higher-timeframe facts.

## Strategy influence rule

V1 uses confluence with a bounded positive-only strategy bonus:

```text
base family score
+ optional bounded Trendline/Fib/POC support
= adjusted family score
```

Hard guarantees:
- no confluence present → base score unchanged;
- opposing/missing confluence → base score is not penalized by this layer;
- correlated confluence cannot inflate score without bound;
- POC alone is not directional;
- no confluence item becomes a universal hard gate.

The exact bonus cap/weights remain replay-calibratable.

## Runtime integration

```text
StructureReport + QuantReport + completed candles + current mid price + tick size
→ TechnicalReport + ConfluenceReport
→ strategy/decision consumers
```

No MT5 query, risk sizing or execution permission exists here.

## Failure behaviour

If structure, ATR or volume evidence is unavailable, outputs degrade through empty/UNKNOWN/`None` semantics rather than inventing levels. Missing optional confluence is not negative evidence.

## Replay requirements

Zone creation, trendline anchors, Fib anchors and POC windows must remain chronological. Future richer lifecycle logic must preserve when each fact became knowable.

## Dashboard visibility

Compact future example:

```text
Location        GOOD BUY
Nearest Support 4312–4315
Nearest Resist  4346–4349
Trendline       SUPPORT TOUCH
Fib             0.618 near
POC             4328 TICK_VOLUME
Target Path     OPEN
Conflict        LOW
```

## Tests required / current evidence

Required:
- adaptive zone construction;
- compatible-zone merge/double-count protection;
- causal trendline anchors and projection;
- trendline touch/break/reclaim;
- causal Fibonacci anchors/levels;
- volume-profile POC source and price-bin calculation;
- missing confluence does not penalize strategy score;
- confluence can only add a bounded bonus;
- POC alone cannot create directional authority;
- multi-timeframe separation;
- conflict handling;
- target-room calculations;
- deterministic replay/rebuild.

Phase-3 deterministic zone coverage exists in `tests/test_technical_liquidity.py` and unified integration in `tests/test_intelligence_snapshot.py`. Confluence regressions are owned by `tests/test_technical_confluence.py`.

## Explicit non-goals

This desk must not:
- redefine BOS/MSS or swing confirmation;
- interpret FVG/OB/sweeps as its own concepts;
- place orders;
- make location, trendline, Fib or POC a universal hard gate;
- require a golden-ratio touch for entry;
- present broker tick volume as centralized exchange volume;
- convert premium/discount alone into BUY/SELL authority.

## Open calibration questions

- zone-width ATR fraction/tick floor;
- zone-quality weighting;
- merge tolerance;
- lifecycle consumption/decay rules;
- trendline proximity/break/reclaim tolerance;
- Fib impulse-quality threshold and useful ratios;
- POC lookback/binning and whether value-area metrics add out-of-sample value;
- family-specific confluence bonus size;
- whether any confluence source improves out-of-sample accuracy/opportunity recall enough to retain;
- whether additional level sources materially improve results without duplicate evidence.
