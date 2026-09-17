# GoldSwingTraderAI — Open Questions

**Status:** LIVING LEDGER  
**Version:** 0.2-design

These items are intentionally unresolved. Implementation must not silently choose an answer before the relevant design is frozen.

## Market intelligence

- Exact runtime candle-window sizes per timeframe.
- Exact volatility-normalized swing prominence/excursion thresholds.
- Exact candidate-to-confirmed swing reversal/persistence requirements.
- Exact swing-significance weights/classes.
- Exact completed-close penetration required for `QUALIFIED_BREAK`.
- Exact family-specific acceptance/follow-through requirements before a break upgrades to `CONFIRMED_BOS`.
- Exact BOS/MSS quality-score calibration.
- Exact compression/expansion/exhaustion numeric bands.
- Which intrabar facts, if any, may be used without becoming structural decision authority.
- Exact holiday/liquidity caution adjustments.

## Strategy floor

- Whether the six provisional production families remain exactly six at V1 freeze.
- Whether FVG- or Order-Block-led setups ever deserve independent production-family status.
- Exact Market Episode identity and duplicate-opportunity rules.
- Exact family-specific opportunity thresholds.

## Entry timing

- Exact entry-score floors by family.
- Exact chase/extension normalization and acceptable late-entry bands.
- Exact setup validity/expiry windows.
- Exact second-chance re-entry limits within one market episode.

## Scoring and fusion

- Initial desk/group weights.
- Maximum synergy bonus.
- Conflict penalty formula.
- Red-Team objection calibration.
- Minimum evidence coverage required for an executable decision.
- Exact relationship between Opportunity Score and Entry Timing Score.

## Risk

- Final per-trade target risk.
- Minimum-lot hard risk ceiling.
- Aggregate open-risk ceiling.
- Exact daily-loss percentage/tiering for this swing system.
- Exact bounded manual-reset count if different from the reference behaviour.
- Automatic daily/risk-cycle reset boundary: conventional risk-day rollover versus XAU reopen/session-aware semantics.
- Exact cooldown trigger/duration and whether fresh market structure is also required.
- Final confirmation of one-position-at-a-time policy.
- Emergency maximum-trades-per-day circuit breaker value.

## Session / position holding

- Exact pre-close no-new-trade window.
- Whether V1 ever permits holding positions over the scheduled XAU daily break/weekend.
- Exact REOPEN_WARMUP evidence and fresh-candle requirements.

## Trade manager / exits

- Exact protection eligibility before/after 1R/2R; R alone should not be the only trigger.
- Exact M5 vs M15 vs H1 trailing precedence.
- Exact structural trail buffer calculation.
- Exact runner-extension criteria and maximum allowed objective progression.
- Whether partial profit is supported when broker volume permits it.

## Research / autonomous discovery

- Exact minimum sample requirements by family.
- Exact selection/validation/final-holdout chronology and sizes.
- Walk-forward and Monte Carlo/stress requirements.
- Shadow/canary/main-DEMO promotion thresholds.
- Exact autonomous recipe grammar and permitted discovery primitives.
- How market-behaviour discovery proposes a genuinely new family without self-writing source code.

## Operator / dashboard

- Final dashboard section order and compact layout.
- Exact keyboard/operator controls.
- Exact bilingual English/Roman-Urdu wording standard.

## Engineering

- Final package/module layout.
- Python/runtime dependency policy.
- Exact CI/security/coverage gates.
- Release packaging and state-file exclusions.
