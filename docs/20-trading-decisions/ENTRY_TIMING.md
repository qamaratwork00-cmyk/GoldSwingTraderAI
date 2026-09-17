# GoldSwingTraderAI — Entry Timing

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Pre-entry timing behaviour

## Core rule

A good market opportunity and a good executable entry are different things. GoldSwingTraderAI must preserve a valid setup while waiting for a better entry instead of deleting the setup merely because the current M5 candle is late, extended or poorly located.

## Primary relationship

```text
M15 → opportunity / location / target context
M5  → executable timing / fine structure
```

## Parallel timing desks

The Entry Timing Board may consume parallel evidence from:

- Candle Timing
- Fine Structure / MSS / reclaim
- Retest Quality
- Momentum Phase
- Extension / Chase Risk
- Liquidity Timing
- Current Entry Location
- Volatility Regime
- Execution Timing / spread / quote freshness

## Timing outcomes

- `ENTER BUY`
- `ENTER SELL`
- `WAIT`
- `MISSED`
- `INVALID`
- `BLOCKED`

`WAIT` means the setup remains potentially valid. `MISSED` means the valid executable window passed without a justified fill. `INVALID` means the underlying trade thesis no longer survives. `BLOCKED` means hard safety/risk/execution authority prevents action.

## Setup persistence

A setup should have a lifecycle independent from its current timing decision. Provisional lifecycle:

```text
DISCOVERED → ARMED → READY → TRIGGERED
                 ↘ WAITING
                 ↘ MISSED → RE-ARMED
                 ↘ STALE
                 ↘ INVALIDATED
```

## Chase protection

Chase detection should consider more than distance from an EMA. It should evaluate, where relevant:

- distance from the structural base/retest level;
- movement relative to current M5 ATR and recent range distribution;
- number/quality of recent displacement candles;
- distance already travelled since breakout/pullback completion;
- remaining structural target room;
- current entry efficiency versus ideal location.

A strong thesis with poor current timing normally becomes `WAIT`, not `INVALID`.

## Momentum phases

Timing logic should distinguish at least:

- BUILDING
- EXPANDING
- EXHAUSTING

Strong momentum does not automatically mean good timing. A late expansion can have high momentum but poor entry efficiency.

## Strategy-aware timing

Different strategy families may use different preferred timing profiles.

Examples:

- Trend Pullback: corrective pullback → rejection/HL/LH → reclaim/continuation.
- Breakout Expansion: decisive close/acceptance with strict chase control; perfect retest is not mandatory.
- Breakout Retest: break → return → acceptance/rejection → continuation.
- Liquidity Sweep Reversal: sweep → reclaim → displacement/MSS.
- Failed Breakout Reversal: failed acceptance outside level → return inside → opposing confirmation.
- Compression Expansion: compression release → directional acceptance; optional shallow retest.

No single confirmation primitive is mandatory for every family.

## Second-chance entry

A missed first entry may be re-armed only when:

- the original thesis remains intact;
- target room remains acceptable;
- risk/stop geometry remains valid;
- a genuinely fresh structural/timing event appears.

Blind re-entry into unchanged structure is not a second-chance setup.

## Research requirements

The journal/research layer must distinguish at least:

- valid opportunity entered;
- valid opportunity waited;
- valid opportunity missed;
- invalidated opportunity;
- blocked opportunity.

This allows research to determine whether timing rules prevented bad entries or simply caused the system to miss large moves.
