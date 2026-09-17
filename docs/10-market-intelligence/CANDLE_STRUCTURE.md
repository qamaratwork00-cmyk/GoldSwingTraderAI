# GoldSwingTraderAI — Candle Structure and Price Behaviour

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Candle anatomy, candle-sequence behaviour, swing formation, protected structure, BOS/MSS classification, displacement, rejection, compression/expansion and exhaustion evidence.  
**Depends on:** `MARKET_DATA_AND_HISTORY.md`, `SYSTEM_CONTRACT.md`

## 1. Purpose

This document defines how GoldSwingTraderAI interprets raw price behaviour before strategy, timing, trade-management or risk modules consume it.

The candle/structure engine is a **market-intelligence provider**, not a trade sender. Its job is to answer questions such as:

- Is BUY or SELL pressure strengthening?
- Is a pullback corrective or destructive?
- Is price compressing, expanding, rejecting or exhausting?
- Which swings are only emerging, which are confirmed, and which have structural importance?
- Did price merely probe a level, or did it create a qualified structural break?
- Is the current change continuation (BOS), transition (MSS candidate/confirmed) or failed acceptance?

A single candlestick pattern must never become independent trade authority.

## 2. Core principles

1. **Completed candles own structural proof.** A forming candle may inform executable-market state, but it cannot confirm a swing, BOS, MSS, rejection sequence or structural transition.
2. **Sequences matter more than labels.** `bullish engulfing`, `pin bar`, etc. may be descriptive features, but the engine reasons primarily from price behaviour across multiple completed candles.
3. **Volatility normalization is mandatory.** Candle and swing strength are judged relative to ATR/recent distribution/local structure rather than fixed dollar distances.
4. **Swing confirmation and swing timestamp are different concepts.** A pivot can occur earlier than the time at which the system is allowed to know it is confirmed.
5. **Lower-timeframe change cannot silently rewrite higher-timeframe structure.** Each timeframe keeps its own state.
6. **Early evidence and authoritative evidence are separated.** Candidate structure may support soft scoring; only confirmed/protected structure can become structural authority.
7. **No look-ahead.** Replay must expose every structure event only from the time at which the required confirming candles were actually available.

## 3. Inputs

The engine consumes validated completed OHLC candles for:

- H4 — macro price behaviour and major external structure;
- H1 — directional structural map;
- M15 — primary opportunity structure;
- M5 — local/timing structure.

Optional live facts such as current Bid/Ask, spread and current forming-candle range may be provided to other desks, but they are not structural-confirmation inputs here.

## 4. Candle anatomy

For every completed candle, the engine should derive normalized facts including:

- direction;
- full range;
- body size;
- body/range ratio;
- upper-wick and lower-wick size;
- close position inside the range;
- range relative to ATR/recent median range;
- body relative to recent median body;
- overlap with prior candles;
- directional progress versus recent closes;
- abnormal-gap/discontinuity metadata supplied by market-data validation.

These facts are evidence, not standalone strategy signals.

## 5. Candle-sequence behaviour

The engine should classify behaviour over rolling completed-candle sequences rather than relying only on the latest candle.

### Continuation

Typical characteristics:

- directional closes progress in the same direction;
- corrective candles make limited counter-progress;
- bodies/close locations remain supportive;
- new displacement follows correction.

### Rejection

Rejection quality depends on:

- penetration of a meaningful structural area;
- inability to sustain price beyond that area;
- wick/body relationship;
- quality of the close back toward the accepted side;
- subsequent completed-candle response.

A large wick in the middle of random range conditions is weak evidence.

### Compression

Typical characteristics:

- shrinking or contained ranges;
- increasing overlap;
- reduced directional progress;
- tightening local swing geometry.

Compression itself does not predict release direction. It increases expansion potential; BUY and SELL release evidence remain separate.

### Expansion / displacement

Typical characteristics:

- range/body expansion relative to local volatility;
- strong directional close;
- meaningful price progress;
- reduced opposing wick/failed rejection;
- follow-through or acceptance where required.

### Exhaustion

Typical characteristics may include:

- extreme extension relative to recent volatility/structure;
- worsening close quality despite large ranges;
- increased opposite rejection;
- falling follow-through efficiency;
- repeated inability to progress toward the next objective.

Exhaustion is evidence for the debate/management floor; it is not an automatic reversal trade.

## 6. Swing model

GoldSwingTraderAI should not rely on a single rigid `N-left/N-right` pivot rule as its complete structure model. The architecture distinguishes four swing states/roles.

### 6.1 Candidate swing

An emerging local extreme that has begun to show sufficient prominence/reaction to be tracked.

A candidate swing:

- is **not yet structural authority**;
- may still move/repaint as new completed candles arrive;
- may support soft timing/context evidence;
- cannot by itself confirm BOS/MSS or become the sole trailing-stop reference.

### 6.2 Confirmed swing

A candidate becomes confirmed only after later completed price action provides enough evidence that price has meaningfully moved away from the extreme.

Confirmation may use a volatility-normalized reversal/excursion threshold, persistence, or another deterministic rule, but the exact numeric calibration remains open.

Every confirmed swing must retain at least:

- `pivot_time` — when the price extreme occurred;
- `confirmed_at` — when the system had enough completed evidence to know the swing was confirmed;
- side (`HIGH`/`LOW`);
- price;
- timeframe;
- significance score/class.

Replay must not expose the swing before `confirmed_at`.

### 6.3 Protected swing

A confirmed swing becomes **protected** when subsequent price action proves that the swing was the structural pivot from which a qualified continuation/break was generated.

Conceptually:

- in bullish structure, the protected low is the meaningful low whose continuation produced a qualified higher break;
- in bearish structure, the protected high is the meaningful high whose continuation produced a qualified lower break.

Protected swings matter for:

- thesis invalidation;
- MSS detection;
- trade-manager structure integrity;
- candidate structural trailing references.

A protected swing is not automatically the final broker stop; trade-plan/management documents own that decision.

### 6.4 External / major swing

A high-significance confirmed swing that defines a wider structural boundary or important higher-timeframe objective.

Typical uses:

- H1/H4 external targets;
- wider regime/range boundaries;
- major liquidity/technical context consumed by other market-intelligence desks.

The Candle Structure engine exposes the geometry; Liquidity/SMC and Technical Structure documents own their higher-level interpretation.

## 7. Swing significance

Swing significance should be continuous rather than based only on timeframe or a fixed bar count.

Candidate inputs include:

- price excursion from the prior opposite swing, normalized by volatility;
- prominence relative to neighbouring extremes;
- distance/time of the reaction away from the pivot;
- number/persistence of candles involved;
- displacement generated from the swing;
- whether the swing later caused a qualified break;
- whether it became protected/external structure.

Exact weights and thresholds remain research/calibration questions.

## 8. Structure state per timeframe

Each timeframe independently maintains a structural state such as:

- `BULLISH`
- `BEARISH`
- `RANGE`
- `TRANSITION`
- `UNDETERMINED`

A fresh M5 bearish shift during an H1 uptrend changes M5 state/context first; it does not automatically flip H1 bearish.

Typical authority mapping remains:

```text
H4  macro regime / major external structure
H1  directional structural map
M15 primary opportunity structure
M5  entry/timing structure
```

## 9. Break hierarchy

A structural level interaction is not binary. The engine should expose distinct states so strategies can use early evidence without pretending it is fully confirmed.

### PROBE

Price trades beyond a relevant swing/level intrabar or by wick, but completed acceptance is not established.

A probe is not BOS/MSS.

### QUALIFIED_BREAK

A completed candle closes through a relevant confirmed swing with sufficient penetration/close quality/displacement for the break to be considered real evidence.

A qualified break may be usable by breakout/timing desks before full follow-through confirmation, depending on family rules.

### CONFIRMED_BOS

A qualified break that is consistent with the existing directional structure and receives sufficient acceptance/follow-through or deterministic confirmation.

BOS represents continuation, not reversal.

### MSS_CANDIDATE

A qualified break occurs against the existing directional structure and damages a relevant protected swing/local structural sequence.

This moves the affected timeframe toward `TRANSITION`; it does not instantly establish a new opposite trend.

### CONFIRMED_MSS

Counter-structure evidence becomes sufficiently strong to confirm a market-structure shift. A strong MSS should normally involve:

- a meaningful protected swing or structural level;
- a qualified completed-candle break;
- credible opposing displacement/acceptance;
- enough context to distinguish true transition from a wick/probe.

Even a confirmed MSS means **transition/opposite thesis evidence**, not automatically a fully established opposite trend. New trend confirmation requires subsequent opposite structural development.

### FAILED_BREAK

Price produces breakout evidence but fails to hold/accept beyond the level and returns into prior structure with meaningful contrary response.

This event is especially useful to the Failed Breakout Reversal desk.

## 10. BOS quality

BOS quality should consider, at minimum:

- significance of the level/swing broken;
- completed-close penetration beyond the level;
- candle body/range quality;
- displacement strength;
- close location;
- opposing wick/rejection penalty;
- acceptance/follow-through or successful retest evidence where the selected family requires it.

Not every strategy requires waiting for the same confirmation depth. For example, Breakout Expansion may consume a strong `QUALIFIED_BREAK` earlier, while structural state may not upgrade to `CONFIRMED_BOS` until later evidence arrives.

## 11. MSS quality

MSS quality should consider, at minimum:

- significance/protected status of the swing damaged;
- strength of the prior directional structure;
- break quality;
- opposing displacement;
- reclaim/acceptance behaviour;
- subsequent opposite swing formation;
- whether the event is local M5 damage or meaningful M15/H1 transition.

This prevents a tiny M5 zigzag from being treated as a major reversal.

## 12. Avoiding over-restriction

The structure engine should expose graduated evidence rather than turn every uncertainty into a hard gate.

Examples:

- `PROBE` may be weak evidence;
- `QUALIFIED_BREAK` may be actionable evidence for an expansion family;
- `CONFIRMED_BOS` is stronger continuation evidence;
- `MSS_CANDIDATE` raises conflict/reversal pressure;
- `CONFIRMED_MSS` strongly challenges the prior thesis.

This architecture allows earlier entries when evidence is genuinely strong without lying about the maturity of the structure event.

## 13. Outputs

The Candle/Structure desk should expose a structured report, including at least:

- Bull Evidence score;
- Bear Evidence score;
- confidence / evidence coverage;
- candle-sequence state;
- displacement BUY/SELL evidence;
- rejection BUY/SELL evidence;
- compression/expansion state;
- exhaustion evidence;
- confirmed swing list with `pivot_time` and `confirmed_at`;
- latest protected high/low by timeframe;
- external/major swing references;
- current structure state per timeframe;
- latest break events (`PROBE`, `QUALIFIED_BREAK`, `CONFIRMED_BOS`, `MSS_CANDIDATE`, `CONFIRMED_MSS`, `FAILED_BREAK`);
- concise reasons supporting and opposing the current directional case.

## 14. Authority boundaries

This document owns raw candle/structure behaviour only.

It does **not** own:

- FVG, Order Block, premium/discount or liquidity-pool interpretation — see `LIQUIDITY_AND_SMC.md`;
- support/resistance/location policy — see `TECHNICAL_STRUCTURE_AND_LEVELS.md`;
- EMA/RSI/ATR strategy meaning — see `INDICATORS_AND_VOLATILITY.md`;
- strategy-family decisions — see `../20-trading-decisions/STRATEGY_FLOOR.md`;
- final entry decision — see `../20-trading-decisions/ENTRY_TIMING.md`;
- final stop/target construction — future `TRADE_PLAN.md`;
- broker/risk authority.

## 15. Persistence and restart

Raw rolling candles may be refreshed/reloaded. Structural state may be reconstructed deterministically from validated candle history.

Any persisted optimization/cache must never allow a candidate swing or break event to become available earlier after restart than it would have been chronologically.

Open-trade lifecycle state remains separately durable under the restart/recovery contract.

## 16. Replay requirements

Replay/live parity requires:

- same completed-candle chronology;
- same swing candidate/confirmation logic;
- explicit `confirmed_at` timestamps;
- no retroactive access to future-confirmed pivots;
- deterministic break classification;
- no use of final-bar knowledge to upgrade earlier decisions.

If a symmetric pivot algorithm is ever used internally, the pivot is unavailable until its right-side confirmation candles have completed.

## 17. Dashboard visibility

The operator dashboard should show only a compact summary, for example:

```text
CANDLE / STRUCTURE DESK
Bull Evidence      84
Bear Evidence      31
M15 Structure      BULLISH
M5 Structure       TRANSITION → BULLISH
Displacement       BULL STRONG
Latest Event       QUALIFIED_BREAK ↑
Protected Low      4312.40
Exhaustion         LOW
```

Detailed swing/event diagnostics belong in logs/research tools, not the main dashboard.

## 18. Tests required before implementation can be verified

At minimum:

- no-lookahead pivot-confirmation tests;
- candidate swing may change, confirmed swing cannot appear early;
- protected-swing promotion tests;
- wick-only probe never becomes BOS/MSS;
- qualified break requires completed-candle evidence;
- BOS continuation vs MSS transition distinction;
- lower-timeframe MSS cannot overwrite higher-timeframe state;
- failed-break classification tests;
- volatility-normalization invariance tests;
- live/replay event-timestamp parity tests.

## 19. Explicit non-goals

This engine must not:

- force every candle into BUY/SELL;
- treat named candlestick patterns as strategies;
- use uncompleted candles as structural proof;
- mark every minor pivot as equal structural importance;
- convert a single local MSS into an immediate H1/H4 reversal;
- hide future-bar pivot confirmation in replay.

## 20. Open calibration questions

The architecture above is provisional. Exact numeric values remain unresolved for:

- volatility-normalized swing prominence/excursion thresholds;
- candidate-to-confirmed reversal/persistence requirements;
- significance-score weights/classes;
- minimum close penetration for `QUALIFIED_BREAK`;
- family-specific acceptance/follow-through requirements;
- exact BOS/MSS quality-score calibration;
- compression/expansion/exhaustion numeric bands.

These values should be frozen only after replay/research shows the trade-off between noise rejection, entry delay and opportunity recall.