# GoldSwingTraderAI — Technical Structure and Levels

**Status:** PROVISIONAL  
**Version:** 0.2-implementation-baseline  
**Authority:** Support/resistance zones, structural level lifecycle, range geometry, location quality and target-room context.  
**Depends on:** `CANDLE_STRUCTURE.md`, `MARKET_DATA_AND_HISTORY.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

This document defines how confirmed market structure is converted into usable technical zones and location context. It does **not** redefine swing, BOS or MSS semantics.

> **Structure tells what the market is doing. Location tells where current price stands relative to meaningful structure.**

## Phase 3 implementation checkpoint

Implemented in:

```text
src/goldswingtraderai/intelligence/technical.py
```

The current baseline consumes an existing `StructureReport` + `QuantReport`; it never re-runs candle structure or ATR itself.

It publishes:
- adaptive support/resistance zones derived from confirmed/protected swings;
- zone side/state/quality/source count/protected-source flag;
- compatible-zone merging to reduce double counting;
- nearest support/resistance;
- BUY and SELL location categories;
- BUY/SELL target-room distance;
- equilibrium where both sides exist;
- structural conflict flag;
- evidence coverage.

Current numerical values in `TechnicalConfig` are initial implementation defaults for replay calibration, not frozen market truth.

## Zones, not exact lines

Support/resistance is represented as volatility/tick-aware zones rather than exact-price certainty. Baseline width uses:

```text
max(broker tick-size floor, ATR fraction)
```

Confirmed/protected swing geometry is the source. Future validated sources may include role-reversed break boundaries, session levels and displacement-origin zones without changing swing semantics here.

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
H1  directional structural zones
M15 primary opportunity/location
M5  local/timing location
```

`intelligence/snapshot.py` keeps these reports separate inside one `IntelligenceSnapshot`; lower-timeframe zones do not overwrite higher-timeframe zones.

## Runtime integration

```text
StructureReport + QuantReport + current mid price + tick size
→ TechnicalReport
→ strategy/decision consumers
```

No MT5 query, risk sizing or execution permission exists here.

## Failure behaviour

If structure or ATR evidence is unavailable, outputs degrade through empty/UNKNOWN/coverage semantics rather than inventing levels. Missing optional zones are not automatically negative evidence.

## Replay requirements

Zone creation/merge/transition must remain chronological. Future richer lifecycle logic must preserve when each source swing or broken level became knowable.

## Dashboard visibility

Compact future example:

```text
Location        GOOD BUY
Nearest Support 4312–4315
Nearest Resist  4346–4349
Target Path     OPEN
Conflict        LOW
```

## Tests required / current evidence

Required:
- adaptive zone construction;
- compatible-zone merge/double-count protection;
- role reversal/lifecycle when implemented;
- repeated-test weakening/consumption when implemented;
- multi-timeframe separation;
- conflict handling;
- target-room calculations;
- deterministic replay/rebuild.

Phase-3 deterministic baseline coverage exists in `tests/test_technical_liquidity.py` and unified integration in `tests/test_intelligence_snapshot.py`.

## Explicit non-goals

This desk must not:
- redefine BOS/MSS or swing confirmation;
- interpret FVG/OB/sweeps as its own concepts;
- place orders;
- make location a universal hard gate;
- convert premium/discount alone into BUY/SELL authority.

## Open calibration questions

- zone-width ATR fraction/tick floor;
- zone-quality weighting;
- merge tolerance;
- lifecycle consumption/decay rules;
- family-specific location influence;
- whether additional level sources materially improve results without duplicate evidence.
