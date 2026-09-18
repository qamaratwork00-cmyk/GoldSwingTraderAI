# GoldSwingTraderAI — Entry Timing

**Status:** PROVISIONAL  
**Version:** 0.2-implementation-baseline  
**Authority:** Pre-entry timing behaviour and Opportunity timing lifecycle

## Core rule

A good market opportunity and a good executable entry are different things. GoldSwingTraderAI preserves a valid setup while waiting for a better M5 entry instead of deleting it merely because the current candle is late, extended or poorly located.

```text
M15 → opportunity / location / target context
M5  → executable timing / fine structure
```

## Phase 4 implementation checkpoint

Implemented in:

```text
src/goldswingtraderai/decisions/opportunity.py
src/goldswingtraderai/decisions/timing.py
src/goldswingtraderai/decisions/snapshot.py
```

### Opportunity lifecycle

`Opportunity` currently preserves:
- `opportunity_id`;
- `episode_id`;
- BUY/SELL direction;
- lifecycle stage;
- created/updated UTC timestamps;
- Opportunity/Thesis score;
- source strategy families.

A surviving same-direction thesis preserves its identity across later decision cycles.

Implemented lifecycle uses the existing typed stages:

```text
DISCOVERED
→ ARMED
→ WAITING / READY
→ TRIGGERED later when execution lifecycle exists

MISSED → RE_ARMED only with a genuinely fresh structural/timing event
STALE / INVALIDATED are terminal for that Opportunity instance
```

Blind re-entry into an unchanged missed setup is explicitly rejected.

Persistence across process restart is not yet implemented; Phase 6 owns durable lifecycle storage.

## Entry Timing inputs

Current M5 timing baseline consumes bounded evidence from:
- M5 structure;
- M5 candle sequence;
- M5 momentum phase;
- M5 location;
- M5 liquidity evidence;
- M15 remaining target room.

No single confirmation primitive is mandatory for every family. Current score weights and thresholds are replay-calibratable implementation baselines.

## Timing outcomes

Phase 4 owns:

```text
ENTER_BUY
ENTER_SELL
WAIT
MISSED
INVALID
```

Future hard `BLOCKED` is **not** invented here; it belongs to risk/session/news/execution authority.

### WAIT

The thesis/opportunity survives but current entry efficiency is not good enough. Opportunity identity is preserved.

### MISSED

The setup was valid/armed but the executable window has passed. Initial baseline may classify a long-lived severely extended setup as MISSED rather than chase it forever.

### INVALID

The underlying direction/thesis no longer survives. This is different from a temporary timing problem.

### ENTER

The Opportunity is sufficiently developed and current M5 timing reaches the configured analytical entry threshold. This means **analytically ready**, not permission to place an order. Phase 5 Trade Plan/Risk and later hard safety/execution must still pass.

## Chase protection

Current baseline explicitly treats `SEVERELY_EXTENDED` M5 state as WAIT while the setup remains recoverable. After a configurable age window, a still-severely-extended armed setup may become MISSED.

This is deliberately different from `INVALID`.

Later Entry Timing/Trade Plan integration should enrich chase evaluation with:
- distance from structural base/retest;
- breakout progress;
- remaining structural target room/RR;
- executable price drift.

EMA distance alone is not final chase authority.

## Momentum phases

Timing consumes the Quant desk's typed phases:

```text
BUILDING
EXPANDING
MATURE
EXHAUSTING
REVERSING
UNKNOWN
```

Strong momentum can still be poor timing if price is overextended.

## Strategy-aware timing

The Strategy Floor publishes a preferred timing profile per family, including pullback/reclaim, break acceptance, retest continuation, sweep reclaim, failed acceptance reversal and compression release.

The current generic timing board uses shared M5 facts; future replay may justify small family-specific timing adjustments without creating six completely duplicated timing engines.

## Second-chance entry

A MISSED Opportunity may be re-armed only when:
- original thesis remains relevant;
- later Trade Plan/risk geometry remains valid;
- a genuinely fresh structural/timing event is explicitly proven.

`rearm_missed_opportunity(..., fresh_structural_event=False)` rejects the re-arm.

## Runtime path

```text
IntelligenceSnapshot
→ StrategyFloorReport
→ DecisionBoard
→ update/create Opportunity
→ evaluate M5 Entry Timing
→ DecisionSnapshot
```

Risk sizing and broker execution are not called from this path.

## Research requirements

Journal/replay must later distinguish:
- valid opportunity entered;
- valid opportunity waited;
- valid opportunity missed;
- invalidated opportunity;
- blocked opportunity by later hard authority.

This allows research to detect whether timing avoids bad entries or merely misses large moves.

## Tests / current evidence

`tests/test_strategy_decisions.py` proves:
- severe extension becomes WAIT rather than deleting a valid Opportunity;
- Opportunity/Episode IDs survive WAIT and MISSED transitions;
- surviving repeated thesis keeps the same IDs;
- MISSED cannot blindly re-arm without a fresh-event assertion;
- DecisionSnapshot remains read-only with no broker-write boundary.

Full chronological replay calibration remains Phase 10 work.

## Open calibration questions

- initial ENTER threshold;
- Opportunity arm/maintain thresholds;
- exact late-entry/MISSED age rule;
- family-specific timing adjustments;
- richer structural chase/entry-efficiency metrics;
- exact fresh-event definition for production re-arm.
