# GoldSwingTraderAI — Strategy Floor

**Status:** PROVISIONAL  
**Version:** 0.2-implementation-baseline  
**Authority:** Production strategy-family architecture

## Core principle

Strategy families run in parallel against the same verified `IntelligenceSnapshot`. No family waits for another family to fail. Each family is an independent market hypothesis built from shared audited primitives.

> **Parallel hypotheses, bounded evidence, no sequential filter soup.**

## Phase 4 implementation checkpoint

Implemented in:

```text
src/goldswingtraderai/strategies/floor.py
```

The implementation evaluates all six families in one call to `evaluate_strategy_floor()` and returns independent BUY and SELL cases for every family.

Each `DirectionalFamilyCase` currently includes:
- score;
- evidence coverage;
- supporting evidence names;
- conflicting evidence names;
- nearest structural target where available;
- normalized expansion potential.

Each `FamilyReport` includes:
- family identity;
- BUY case;
- SELL case;
- preferred timing profile;
- derived leading direction/quality for operator/research convenience.

The numerical feature weights and score mappings in `StrategyFloorConfig` / helper functions are **initial implementation baselines for replay calibration**, not frozen profitability assumptions.

Missing optional evidence is omitted/reweighted rather than silently converted to zero.

## Production families

### 1. TREND_PULLBACK_CONTINUATION

Current baseline consumes bounded evidence from:
- H4 context;
- H1/M15 structure;
- M15 location;
- M5 resumption sequence;
- M15 EMA flow;
- remaining target room.

FVG/OB/liquidity primitives are not mandatory.

### 2. BREAKOUT_EXPANSION

Current baseline consumes:
- H1 context;
- M15 qualified/confirmed break evidence;
- M15/M5 directional expansion/acceptance;
- M5 momentum;
- volatility state;
- accepted liquidity break where present;
- remaining target room.

A wick-only probe is weaker than accepted break evidence. Perfect retest is not mandatory.

### 3. BREAKOUT_RETEST_CONTINUATION

Current baseline consumes:
- prior meaningful break;
- M15 location/retest context;
- M5 rejection/continuation;
- local structure;
- liquidity acceptance where present;
- target room.

### 4. LIQUIDITY_SWEEP_REVERSAL

Current baseline consumes:
- M15/M5 confirmed sweep evidence;
- M5 rejection;
- M5 MSS/structure-shift evidence;
- M15 location;
- non-hostile H1 context;
- target room.

A long wick without an existing liquidity pool/reclaim narrative is not sufficient.

### 5. FAILED_BREAKOUT_REVERSAL

Current baseline consumes:
- M15/M5 `FAILED_BREAK` evidence in the attempted opposite direction;
- M5 opposing response/MSS;
- M15 location;
- non-hostile H1 context;
- target room.

This remains distinct from the liquidity-sweep family even when the same market episode supplies related evidence.

### 6. COMPRESSION_EXPANSION

Current baseline consumes:
- M15 compression;
- M5 directional release;
- M15 break evidence;
- M5 momentum/volatility build;
- H1 context;
- liquidity path;
- target room.

The family does not guess release direction before evidence appears; BUY and SELL cases are evaluated independently.

## Shared evidence primitives, not standalone automatic strategies

These remain shared inputs unless governed research later promotes a new family:

- FVG;
- qualified Order Block;
- premium/discount;
- session highs/lows;
- liquidity pools;
- EMA;
- RSI;
- ATR;
- individual candle patterns;
- support/resistance.

## Correlation / consensus

Multiple family labels may describe the same underlying market event. Raw family scores are therefore not summed as independent certainty.

`decisions/fusion.py` owns bounded cross-family synergy/conflict. This document only requires that family output preserves enough evidence labels/coverage for correlation handling.

## Market Episode identity

Phase 4 implements durable-style `episode_id` and `opportunity_id` in `decisions/opportunity.py`.

A surviving thesis preserves those IDs across WAIT/READY lifecycle updates. A missed opportunity may be re-armed only when a caller proves a genuinely fresh structural/timing event; blind unchanged re-entry is rejected.

Later persistence will make these identities durable across restart.

## Frequency philosophy

The floor should maximize valid opportunity coverage, not raw trade count and not ultra-rare perfection. Soft imperfections remain scores/conflicts; true hard safety remains outside strategy scoring.

## Runtime path

```text
IntelligenceSnapshot
→ evaluate six strategy families in parallel
→ StrategyFloorReport
→ independent BUY/SELL thesis fusion
```

Strategy code has no MT5, lot sizing, reset, broker-write or execution-permission authority.

## Tests / evidence

Phase-4 deterministic tests in `tests/test_strategy_decisions.py` prove:
- all six families execute from the same shared snapshot;
- BUY/SELL family outputs remain bounded;
- strategy/decision modules contain no `order_send`/MetaTrader5 boundary;
- downstream fusion preserves strong opposition as conflict rather than hiding it.

Full profitability/threshold calibration remains Phase-10 replay/research work.

## Open calibration questions

- family feature weights;
- evidence-score mappings;
- minimum useful family coverage;
- family-specific target-room influence;
- correlated-evidence grouping/synergy strength;
- which early versus confirmed structure maturity each family should prefer.
