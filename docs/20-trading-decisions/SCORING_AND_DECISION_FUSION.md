# GoldSwingTraderAI — Scoring and Decision Fusion

**Status:** PROVISIONAL  
**Version:** 0.2-design  
**Authority:** Analytical scoring, BUY/SELL thesis fusion, conflict handling and final decision/blocker attribution.  
**Depends on:** `STRATEGY_FLOOR.md`, `ENTRY_TIMING.md`, `TRADE_PLAN.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Core principle

Specialist desks operate in parallel. Final trade quality is not a simple average and no single soft-evidence desk should automatically kill a valid opportunity.

Safety/risk are excluded from weighted market scoring and retain separate hard authority.

## Core analytical outputs

The fusion system maintains at least:

- BUY Thesis;
- SELL Thesis;
- Directional Edge;
- Conflict Score;
- Red-Team Objection;
- Opportunity Score;
- Entry Timing Score;
- Evidence Coverage;
- Confidence;
- Final Trade Score for operator visibility.

## Independent BUY and SELL theses

BUY and SELL are scored independently from the same verified market snapshot.

Example:

```text
BUY Thesis   86
SELL Thesis  34
Edge         +52 BUY
```

This is materially different from:

```text
BUY Thesis   84
SELL Thesis  80
Edge         +4 BUY
```

A high leading score with equally strong opposition is conflict, not conviction.

## Evidence groups

To reduce double-counting, related evidence should be grouped conceptually:

- Price Action: candle behaviour, structure, displacement;
- Location: technical zones, liquidity, FVG/OB, premium/discount, session/HTF levels;
- Momentum/Expansion: volatility state, expansion phase, bounded indicators;
- Context: H4/H1, session, macro/fundamental context;
- Strategy: production-family hypotheses;
- Timing: retest/reclaim, entry structure, chase, immediate momentum/location.

Correlated evidence may add bounded synergy but must not be counted repeatedly as independent certainty.

## Opportunity Score

Answers: **Is this market idea worth pursuing?**

Typical components:

- structure quality;
- location quality;
- expansion potential;
- target/path quality;
- strategy evidence;
- liquidity context;
- HTF/regime suitability.

Timing is intentionally separate.

## Entry Timing Score

Answers: **Is now a good executable moment?**

Typical components:

- M5 candle sequence;
- retest/reclaim quality;
- fine structure confirmation;
- current location;
- momentum phase;
- chase/extension risk;
- freshness/executability context.

## Unknown evidence

Unavailable optional evidence must not automatically become `0`.

Examples:

- optional macro opinion unavailable → `UNKNOWN`, reduce coverage/reweight as defined;
- required scheduled-news safety unavailable → hard block outside the score engine;
- missing optional FVG/OB → absent/unknown support, not automatic strategy failure.

## Conflict and Red Team

The system explicitly measures contradiction. Red Team challenges the leading thesis with concrete evidence such as:

- credible opposite structure;
- failed-breakout risk;
- late/chased entry;
- insufficient target room;
- exhaustion/reversal evidence;
- duplicated/correlated support.

Red Team may lower confidence or recommend WAIT but may not invent arbitrary blockers.

## Score bands

Exact thresholds remain open to calibration. Initial conceptual bands:

- 0–49: weak/no edge;
- 50–64: developing/watch;
- 65–74: valid/armable;
- 75–84: strong;
- 85–100: exceptional.

These are not automatic entry rules.

## Dynamic decision surface

Opportunity and timing interact without collapsing into one hidden number.

A very strong Opportunity may tolerate merely acceptable timing, while poor timing must not be rescued by a high Opportunity score. Exact decision surface remains open.

## Evidence coverage and confidence

Coverage reports how much expected analytical evidence is trustworthy. Confidence describes how trustworthy a directional/quality score is. They are not the same as score.

A high score with very low coverage is not equivalent to the same score with broad verified evidence.

## Final Trade Score

The operator-facing Final Trade Score may summarize opportunity, timing and directional clarity with bounded conflict/synergy adjustments. It must not hide the component scores or become sole internal authority.

Exact weights/family thresholds are intentionally not frozen and should be calibrated through replay, ablation and forward evidence.

## Final action and authority trace

The final system decision should distinguish at least:

```text
ENTER BUY
ENTER SELL
WAIT
MISSED
INVALID
BLOCKED
```

The system must also record the authority path that led to the action. A compact conceptual trace:

```text
Data
Market / Strategy
Entry Timing
Trade Plan
News Safety
Risk
Execution
```

Each stage should report a result such as `PASS`, `WAIT`, `BLOCK`, `NOT_READY`, `NOT_EVALUATED` or `NOT_REACHED` as appropriate.

## Why-no-trade / blocker attribution

Every final non-entry must have a stable machine-readable reason code plus concise human explanation.

Examples:

```text
MARKET_NO_EDGE
DIRECTION_CONFLICT
OPPORTUNITY_WEAK
ENTRY_NOT_READY
ENTRY_EXTENDED
TARGET_ROOM_POOR
SETUP_INVALIDATED
NEWS_BLACKOUT
DAILY_LOSS_LIMIT_REACHED
MIN_LOT_UNAFFORDABLE
SPREAD_TOO_HIGH
QUOTE_STALE
PRICE_DRIFT_TOO_HIGH
POSITION_CAPACITY_FULL
ORDER_STATE_UNKNOWN
DATA_STALE
```

The owning subsystem defines the semantics of hard risk/execution/system codes. Decision Fusion records and exposes them; it does not redefine them.

## Primary and secondary blockers

If multiple hard blockers exist, record a primary blocker according to authority/severity while preserving secondary blockers.

Example:

```text
Primary: DAILY_LOSS_LIMIT_REACHED
Secondary: NEWS_BLACKOUT, SPREAD_TOO_HIGH
```

Do not hide additional relevant blockers simply because one already prevents entry.

## Would otherwise trade?

Where the decision state supports a valid counterfactual, record whether all market/timing/plan conditions had otherwise qualified before the hard block.

Example:

```text
Opportunity     87
Entry           82
Trade Plan      PASS
Risk            BLOCK
Would otherwise trade? YES
```

This is useful for research attribution but does not bypass the blocker and must not be treated as actual P/L.

If the market thesis itself is weak, `Would otherwise trade? NO`.

## Decision versus system fault

A normal `WAIT`, `MISSED`, `OPPORTUNITY_WEAK` or expected `NEWS_BLACKOUT` is not automatically a system fault.

System-health incidents such as stale data, account mismatch or unresolved broker state are reported by the owning subsystem and aggregated by `../60-engineering/SYSTEM_HEALTH_AND_DIAGNOSTICS.md`.

## Persistence / research

Decision traces, reason codes, blockers and `Would otherwise trade?` attribution should be journaled with Opportunity/Episode/strategy/policy versions. This allows research to distinguish strategy, timing, risk, execution and system-health causes.

## Dashboard visibility

The dashboard should show BUY/SELL theses, Opportunity, Entry, Conflict/Coverage, final action, primary reason and a compact authority trace. It must never reduce all non-trades to generic `NO TRADE`.

## Tests required

- independent BUY/SELL thesis conflict cases;
- optional UNKNOWN evidence not zero;
- correlation/synergy caps;
- Opportunity vs Entry separation;
- WAIT cannot be rescued by high Opportunity when timing is truly poor;
- reason-code attribution by authority;
- primary/secondary blockers;
- `Would otherwise trade?` correctness;
- normal WAIT not labeled system fault;
- decision trace persistence/research attribution.

## Explicit non-goals

Decision Fusion must not:

- let score override hard risk/news/broker/data authority;
- convert every missing optional primitive into bearish/zero evidence;
- invent hard blockers;
- silently hide the subsystem that stopped a trade;
- treat a counterfactual blocked trade as actual execution/P&L.

## Open questions

- initial desk/group weights;
- maximum synergy bonus;
- conflict penalty formula;
- Red-Team calibration;
- minimum evidence coverage for executable decision;
- exact Opportunity/Entry decision surface;
- final reason-code taxonomy/precedence for primary blockers.