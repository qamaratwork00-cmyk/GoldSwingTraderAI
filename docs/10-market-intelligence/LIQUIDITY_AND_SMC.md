# GoldSwingTraderAI — Liquidity and SMC

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Liquidity pools, equal-high/low clustering, sweeps, reclaim/acceptance, FVG, qualified Order Blocks, premium/discount and liquidity-path evidence.  
**Depends on:** `CANDLE_STRUCTURE.md`, `TECHNICAL_STRUCTURE_AND_LEVELS.md`, `MARKET_DATA_AND_HISTORY.md`

## Purpose

This document defines auditable liquidity/SMC-style market evidence. SMC terminology is treated as shorthand for observable price/liquidity behaviour, not as mystical or standalone authority.

Core rule:

> **Liquidity/SMC is evidence, not a universal trade gate. Post-liquidity behaviour matters more than the label itself.**

## Liquidity pools

Potential liquidity sources include:

- external/major confirmed swing highs/lows;
- protected structural highs/lows;
- equal-high/equal-low clusters;
- range highs/lows;
- session highs/lows;
- previous-day highs/lows;
- internal swings inside the active leg/range.

Each pool should have an ID, bounds, timeframe, source type, significance, freshness and lifecycle state.

## Internal vs external liquidity

`INTERNAL` liquidity describes local pools inside an active range/leg. `EXTERNAL` liquidity describes more meaningful structural objectives outside the current internal structure.

External liquidity generally carries stronger target/reversal significance, but this is soft evidence rather than an automatic rule.

## Equal highs/lows

Equal highs/lows must use volatility/tick-size-aware clustering rather than exact numerical equality. Close levels may be grouped into one pool when their separation is small relative to local volatility and timeframe context.

The engine must avoid counting several nearly identical levels as independent liquidity pools.

## Liquidity lifecycle

Provisional states:

```text
FORMING
CONFIRMED
UNTOUCHED
APPROACHED
PROBED
SWEPT
RECLAIMED
ACCEPTED_BEYOND
CONSUMED
STALE
```

A wick beyond a pool is not automatically a reversal.

## Sweep model

A meaningful sweep narrative typically contains:

1. a liquidity pool that existed before the event;
2. price trading beyond that pool;
3. failure to sustain acceptance beyond the pool;
4. reclaim/recovery into prior structure;
5. stronger quality when opposing displacement/MSS evidence follows.

The desk may expose graduated states such as:

```text
PROBE
SWEEP_CANDIDATE
CONFIRMED_SWEEP
ACCEPTED_BREAK
```

`ACCEPTED_BREAK` is continuation/breakout evidence, not sweep-reversal evidence.

## Sweep vs liquidity grab

`Liquidity grab` may be used as a descriptive subtype for a fast penetration/reclaim, but the production model should normalize both grab/sweep behaviour into one auditable liquidity-event framework unless research proves a useful distinction.

## Acceptance versus reclaim

This distinction is critical:

```text
liquidity taken + acceptance beyond + continuation
→ breakout/continuation evidence
```

```text
liquidity taken + failed acceptance + reclaim + opposite displacement
→ sweep/failed-breakout reversal evidence
```

The strategy floor decides which family consumes the event.

## Fair Value Gap (FVG)

FVG is a deterministic imbalance primitive associated with directional displacement. A common three-candle geometry may be used, but useful quality also depends on:

- source displacement quality;
- normalized gap size;
- structural/location context;
- freshness;
- mitigation depth;
- follow-through.

The engine should store at least:

- direction;
- timeframe;
- bounds;
- created/known time;
- source displacement/event ID;
- mitigation/fill percentage;
- quality;
- lifecycle state.

Provisional FVG states:

```text
FRESH
PARTIAL
MITIGATED
INVALID
STALE
```

FVG is supportive location/continuation evidence, not mandatory and not a standalone BUY/SELL signal.

## Qualified Order Block

The system must not label the last opposite candle before every move as an Order Block.

A qualified OB should normally be tied to a meaningful origin/base area that precedes credible displacement and a structural consequence such as a qualified break.

The engine should prefer a defensible origin **zone** over an arbitrary single-candle label.

Possible states:

```text
CANDIDATE
QUALIFIED
FRESH
TESTED
MITIGATED
WEAKENING
INVALIDATED
```

Quality may consider displacement produced, structure broken, freshness, penetration, repeated tests and higher-timeframe/location context.

## Correlation and double-counting

A sweep, rejection wick, MSS, FVG and OB may all describe one underlying market event. They must not be counted as five independent proofs.

Related evidence should be attached to a common liquidity/event or Market Episode identity with bounded synergy.

## Premium / discount

Premium/discount must be anchored to a meaningful active dealing range, not an arbitrary recent high/low window.

The dealing range should preserve identity and chronology, for example:

- range ID;
- anchor swings;
- created time;
- superseded time.

Equilibrium/50% is descriptive location context. Premium/discount is soft evidence and must not become `discount = BUY` or `premium = SELL` authority.

## Liquidity path

The desk should map meaningful liquidity ahead and behind current price, including nearest internal and external pools.

Outputs may describe:

```text
Immediate Liquidity
Primary External Liquidity
Next HTF Liquidity Objective
Path Quality: OPEN / MIXED / CROWDED
```

A liquidity pool is a potential objective/magnet, not a guaranteed target.

## Strategy relationships

Liquidity evidence typically supports:

- Trend Pullback: location/path context;
- Breakout Expansion: liquidity objective + acceptance;
- Breakout Retest: broken pool/structure + retest;
- Liquidity Sweep Reversal: primary family evidence;
- Failed Breakout Reversal: liquidity taken + failed acceptance;
- Compression Expansion: built-up pools and directional release.

No family requires every SMC primitive.

## Outputs

The desk should expose at least:

- BUY Liquidity Evidence;
- SELL Liquidity Evidence;
- nearest buy-side/sell-side pools;
- internal/external classification;
- pool quality/freshness/state;
- sweep/acceptance/reclaim state;
- FVG facts/quality;
- OB facts/quality;
- premium/discount context;
- liquidity-path quality;
- confidence/coverage and reasons/counter-evidence.

## Chronology and replay

All pools/primitives must preserve when they became knowable. A pool cannot be retroactively invented only because future price later swept it. FVG/OB/sweep states must be replayed using only contemporaneous evidence.

## Failure behaviour

Missing optional FVG/OB evidence returns absent/unknown support, not score zero. Invalid structural source data degrades the desk rather than inventing liquidity geometry.

## Dashboard visibility

Main dashboard should show compact facts, for example:

```text
Liquidity Bias     BUY
Nearest BSL        4348
Nearest SSL        4311
Sweep State        SSL SWEPT + RECLAIMED
Path               OPEN UPSIDE
```

## Tests required

- equal-high/low adaptive clustering;
- pool lifecycle and deduplication;
- sweep versus accepted-break classification;
- pool-existed-before-sweep chronology;
- FVG creation/mitigation lifecycle;
- qualified OB requirements;
- dealing-range versioning;
- correlated-event double-count protection;
- replay no-lookahead tests.

## Explicit non-goals

This engine must not:

- redefine BOS/MSS;
- treat every wick as a sweep;
- treat every opposite candle as an OB;
- require FVG/OB for every trade;
- claim liquidity objectives are guaranteed;
- directly grant broker authority.

## Open questions

- exact equal-high/low cluster tolerance;
- exact sweep penetration/reclaim quality bands;
- exact FVG minimum normalized size/quality;
- exact OB qualification/mitigation thresholds;
- exact liquidity-path scoring weights.