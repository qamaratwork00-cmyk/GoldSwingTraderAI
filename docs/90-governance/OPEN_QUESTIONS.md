# GoldSwingTraderAI — Open Questions

**Status:** LIVING LEDGER  
**Version:** 0.7-design

These items are intentionally unresolved. Most are calibration/implementation choices rather than missing major subsystems. Implementation must not silently choose an answer before the relevant contract/config is frozen.

## Market intelligence calibration

- Exact runtime candle-window sizes per timeframe.
- Exact volatility-normalized swing prominence/excursion thresholds.
- Exact candidate-to-confirmed swing reversal/persistence requirements.
- Exact swing-significance weights/classes.
- Exact completed-close penetration required for `QUALIFIED_BREAK`.
- Exact family-specific acceptance/follow-through requirements for `CONFIRMED_BOS`/MSS quality.
- Exact compression/expansion/exhaustion numeric bands.
- Exact S/R zone-width, strength/freshness and role-flip thresholds.
- Exact equal-high/low/liquidity clustering tolerance and sweep/reclaim thresholds.
- Exact FVG/qualified-OB quality thresholds.
- Exact volatility/momentum/extension bands and indicator periods if different from the initial EMA20/EMA50/RSI/ATR design.
- Which intrabar facts, if any, may be consumed as telemetry without becoming structural confirmation authority.

## Strategy / scoring / entry

- Whether the six initial production families remain exactly six at V1 freeze after validation.
- Whether any FVG/OB-led behaviour deserves an independent future production family.
- Exact Market Episode identity/duplicate-opportunity/re-entry mechanics.
- Exact family-specific Opportunity Score and Entry Timing thresholds.
- Initial evidence-group weights, synergy cap, conflict penalty and Red-Team calibration.
- Minimum Evidence Coverage for executable opportunity/timing decisions.
- Exact chase/extension tolerance, ideal-entry-zone and setup-expiry rules by family.
- Exact second-chance limits within one Market Episode.

## Trade Plan / targets / exits

- Exact family-specific stop-buffer calculation and Stop Quality thresholds.
- Whether the initial broker TP is always placed at a market objective, omitted for some runner designs, or follows a family-specific policy.
- Exact minimum acceptable target-room/RR policy by family; no universal value has been frozen.
- Exact protection/trailing eligibility and M5/M15/H1 precedence.
- Exact runner-extension criteria and objective progression limits.
- Whether/when partial profit is supported when broker volume permits it; V1 must remain valid without partials.

## Risk

**Resolved profile boundaries:**

```text
SMALL   $100–$299
MEDIUM  $300–$999
NORMAL  $1,000+
```

**Resolved sizing direction:** SMALL uses practical base/minimum-lot hybrid sizing with all-in risk validation; MEDIUM uses stepped dynamic lots; NORMAL uses fully dynamic percentage sizing. `raw lot < broker minimum` is not an automatic trade blocker.

**Resolved initial risk policy:**

```text
Profile  Normal Risk   Elevated Risk    Entry Ceiling   Daily Lock
SMALL    3.0–4.5%      >4.5–6.5%        7%              12%
MEDIUM   2.0–3.0%      >3.0–4.5%        5%               9%
NORMAL   1.0–2.0%      >2.0–3.5%        4%               7%
```

Elevated risk is tolerance, not target sizing.

Remaining risk questions:

- Emergency safety ceiling and aggregate open-risk ceiling.
- Policy for accounts below `$100`.
- Exact slippage-reserve model and commission treatment by broker/account type.
- Exact realized/floating P/L accounting formula for applying the frozen daily lock percentages.
- Bounded manual-reset count and confirmation timing per UTC risk day.
- Exact cooldown trigger/release rules.
- Exact drawdown-aware target-band reduction curve.
- Final V1 confirmation of one independently risk-bearing Gold position at a time.
- Emergency maximum-trade/runaway circuit-breaker value.

**Resolved direction:** the provisional daily-risk boundary is `00:00 UTC`; it is no longer an open XAU-reopen-versus-calendar question.

## Session / news / position holding

- Exact pre-close no-new-entry window.
- Whether V1 permits holding managed positions over the scheduled XAU daily break and/or weekend.
- Exact REOPEN_WARMUP evidence/fresh-candle requirements.
- Final event severity tiers and scheduled blackout windows.
- Exact POST_NEWS_WARMUP normalization criteria.
- Final provider(s), freshness/reliability requirements and fallback policy for event facts.
- Exact holiday/liquidity-caution adjustments, if any, to soft scoring.

## Execution / broker safety

- Exact price-drift and spread limits by broker/volatility context.
- Final policy for unexpected manual/foreign Gold positions.
- Exact DEMO-to-future-REAL approval/config mechanism. Architecture is already decided: REAL is not a separate engine and must use the same centralized Execution Permission Gate.
- Exact execution-controller/lease mechanism, timeout/clock/failover semantics and coordination store.
- Exact broker comment/magic/lineage conventions.
- Exact retry policy for safe read-only/before-submit operations; irreversible ambiguous writes remain no-blind-retry.

## Persistence / backup / migration

- Final storage engines/formats for durable state and research/learning data.
- Exact Git-tracked state artifacts versus generated checkpoint artifacts.
- Backup/checkpoint cadence, retention and pruning policy.
- Exact financial-authority secret scanner/tooling and CI integration.
- State schema migration/rollback compatibility policy.
- Exact portable export/import packaging and integrity format.
- Whether backup publication to GitHub is automatic or performed by a controlled external/script workflow; credentials for GitHub must never be embedded in tracked state.

## Research / learning / autonomous improvement

- Exact minimum independent sample/confidence requirements by family/regime.
- Exact development/validation/final-holdout periods and walk-forward/stress requirements.
- Exact Shadow, DEMO Canary and Main DEMO promotion thresholds.
- Exact bounded StrategyMemory influence/adjustment limits.
- Exact Entry Learning and Exit Learning candidate-creation thresholds.
- Exact autonomous recipe grammar and allowed parameter ranges for each primitive.
- Exact duplicate-variant versus genuinely-new-family classifier.
- Exact Monte Carlo/block/regime-aware method if used.
- Whether any ML model is included in V1 beyond explicit interpretable baseline logic.

## Operator / dashboard

- Final terminal dimensions/section order after implementation proves readability.
- Exact dashboard refresh cadence; presentation refresh must not become decision cadence.
- Exact `R,R` timing/keyboard implementation and safe-shutdown/export controls.
- Optional notification channels for critical health/trade events.
- Final wording polish for English technical terms plus concise Roman-Urdu explanations.

The restrained-emoji policy itself is decided: emojis are meaningful visual markers with text fallback, not decorative logic.

## Engineering / release

- Exact Python/runtime dependency versions and packaging policy.
- Final source filenames/classes inside the module ownership map once implementation starts.
- Exact persistence database/library choices.
- Exact CI/static/security/coverage thresholds.
- Exact controlled MT5 DEMO certification sample/steps and long-duration forward-evidence requirement.
- Final release packaging/version/tag strategy.

## Governance note

No major architectural subsystem is currently missing from the design corpus. Items above are retained because they can materially affect code/config/research and therefore must be chosen, validated or explicitly deferred rather than guessed.
