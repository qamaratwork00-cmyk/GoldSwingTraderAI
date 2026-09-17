# GoldSwingTraderAI — Scoring and Decision Fusion

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Analytical scoring and trade-decision fusion

## Core principle

Specialist desks operate in parallel. Final trade quality is not a simple average and no single soft-evidence desk should automatically kill a valid opportunity.

Safety/risk are excluded from weighted market scoring and retain separate hard authority.

## Core outputs

The fusion system maintains at least:

- BUY Thesis
- SELL Thesis
- Directional Edge
- Conflict Score
- Red-Team Objection
- Opportunity Score
- Entry Timing Score
- Evidence Coverage
- Confidence
- Final Trade Score for operator visibility

## Independent BUY and SELL theses

BUY and SELL are scored independently from the same market snapshot.

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

- Price Action: candle behaviour, structure, displacement.
- Location: liquidity, FVG/OB context, premium/discount, session/HTF levels.
- Momentum/Expansion: volatility state, expansion phase, bounded indicator context.
- Context: H4/H1, session, macro/fundamental context.
- Strategy: production-family hypotheses.
- Timing: retest/reclaim, entry structure, chase risk, immediate momentum/location.

Correlated evidence may add a bounded synergy bonus; it must not be counted repeatedly as independent certainty.

## Opportunity Score

Answers: **Is this trade idea worth pursuing?**

Typical components:

- structure quality;
- location quality;
- expansion potential;
- target quality;
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
- freshness/executability.

## Unknown evidence

Unavailable optional evidence must not automatically become `0`.

Example:

- Optional macro opinion unavailable → mark UNKNOWN and adjust coverage/weighting.
- Scheduled-news safety unknown when policy requires verification → hard BLOCK outside the score engine.

## Conflict and Red Team

The system explicitly measures contradiction. Red Team challenges the leading thesis with concrete evidence such as:

- credible opposite structure;
- failed breakout risk;
- late/chased entry;
- insufficient target room;
- exhaustion/reversal evidence;
- duplicated/correlated supporting evidence.

The Red Team may lower confidence or recommend WAIT but may not invent arbitrary blockers.

## Score bands

Exact thresholds remain open to calibration. Initial conceptual bands:

- 0–49: weak/no edge
- 50–64: developing/watch
- 65–74: valid/armable
- 75–84: strong
- 85–100: exceptional

These bands are not automatic entry rules. A moderate but valid opportunity with excellent timing may be tradeable, while an exceptional opportunity with poor timing should wait.

## Dynamic decision surface

Opportunity and timing should interact without collapsing into one hidden number.

Example:

```text
Opportunity 92
Timing      70
```

may still be valid if directional edge is strong and conflict is low.

But:

```text
Opportunity 95
Timing      25
```

should not be rescued by the opportunity score; the system should normally WAIT.

## Evidence coverage

Coverage reports how much of the expected analytical floor has trustworthy evidence.

A high score with very low coverage should not be treated as equivalent to the same score with broad verified evidence.

## Confidence versus score

A desk may have a directional score and a separate confidence value. Score describes direction/quality; confidence describes how trustworthy the desk's current evidence is.

## Final Trade Score

The operator-facing Final Trade Score combines opportunity quality, timing quality and directional clarity with bounded conflict/synergy adjustments. It must not hide the component scores or become the sole internal authority.

Exact weights and family thresholds are intentionally not frozen yet. They should begin with bounded sensible defaults and be calibrated through replay, ablation and forward evidence rather than guessed permanently.
