# GoldSwingTraderAI — Open Questions

**Status:** LIVING LEDGER  
**Version:** 1.4-design

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
- Exact volatility/momentum/extension bands and indicator periods if different from initial EMA20/EMA50/RSI/ATR design.
- Which intrabar facts, if any, may be consumed as telemetry without becoming structural confirmation authority.

## Strategy / scoring / entry

- Whether the six initial production families remain exactly six at V1 freeze after validation.
- Whether any FVG/OB-led behaviour deserves an independent future production family.
- Exact Market Episode identity/duplicate-opportunity mechanics beyond the frozen one-reentry limit.
- Exact family-specific Opportunity Score and Entry Timing thresholds.
- Initial evidence-group weights, synergy cap, conflict penalty and Red-Team calibration.
- Minimum Evidence Coverage for executable opportunity/timing decisions.
- Exact chase/extension tolerance, ideal-entry-zone and setup-expiry rules by family.

## Trade Plan / targets / exits

**Resolved initial target/RR direction:**

```text
Credible structural target room <1.20R  → reject current plan
1.20R–<1.50R                            → conditional/marginal
1.50R–<2.00R                            → good
2.00R+                                  → strong
3R/4R+                                  → runner potential, not guaranteed
```

A `1.20R–<1.50R` plan requires a credible larger expansion path; initial V1 expects roughly `2R+` Expansion Target room with acceptable path quality. Higher RR does not increase monetary risk.

**Resolved initial objective/TP direction:** Primary Structural Target is a management checkpoint rather than forced full exit. A valid Expansion Target is the default initial broker TP; if no valid Expansion Target exists, a valid Primary Target may be used. Fixed 100/200/300-pip TP logic is not used. Runner extension requires fresh continuation/acceptance evidence plus a newly defined structural/liquidity objective; profit alone cannot move TP endlessly.

**Resolved V1 partial-profit direction:** core V1 does not depend on partial closes. The full position is managed through HOLD/PROTECT/TRAIL/RUNNER/EXIT so `0.01` minimum-lot accounts remain fully supported. Partial-profit research is a future/version option.

Remaining Trade Plan/exit questions:

- Exact family-specific stop-buffer calculation and Stop Quality thresholds.
- Family/regime-specific refinements to the frozen initial RR guard after research.
- Exact protection/trailing eligibility and M5/M15/H1 precedence thresholds.
- Exact continuation/reversal score thresholds and objective-quality thresholds for runner progression/exit.

## Risk

**Resolved profile boundaries:** `SMALL $100–$299`, `MEDIUM $300–$999`, `NORMAL $1,000+`.

**Resolved initial risk policy:**

```text
Profile  Normal Risk   Elevated Risk    Entry Ceiling   Daily Lock
SMALL    3.0–4.5%      >4.5–6.5%        7%              12%
MEDIUM   2.0–3.0%      >3.0–4.5%        5%               9%
NORMAL   1.0–2.0%      >2.0–3.5%        4%               7%
```

**Resolved V1 capacity:** one independently risk-bearing Gold position (`0/1`); external Gold exposure blocks new bot entry.

**Resolved daily safety P/L:** daily lock is driven by cash-flow-adjusted account-equity change:

```text
AccountSafetyPL
= CurrentVerifiedEquity
- DayStartEquity
- NetNonTradingCashFlowSinceDayStart
```

Floating drawdown therefore counts immediately. Bot strategy-performance P/L remains separate from account-safety P/L. Manual reset creates a new audited risk-cycle reference while cumulative UTC-day P/L remains visible.

**Resolved manual reset:** OFF by default; if enabled, max one `R,R` reset per UTC day, only from `LOSS_LOCKED`, with cumulative P/L/history preserved.

**Resolved cooldown:** one ordinary loss does not trigger global cooldown; one fresh same-episode re-entry maximum; second same-episode loss locks that episode; 3 consecutive closed bot losses trigger minimum 30-minute cooldown plus fresh completed M15 context/fresh opportunity requirement.

Remaining risk questions:

- Emergency safety ceiling and aggregate-risk semantics for future multi-position design.
- Policy for accounts below `$100`.
- Exact slippage-reserve model and commission treatment by broker/account type beyond costs already represented in broker equity/executable geometry.
- Exact classification of unusual broker balance/credit adjustments as trading versus non-trading cash flow.
- Exact keyboard timing window for `R,R`.
- Exact drawdown-aware target-band reduction curve.
- Emergency maximum-trade/runaway circuit-breaker value.

**Resolved direction:** risk day is UTC calendar day at `00:00 UTC`.

## Session / news / position holding

**Resolved V1 holding policy:** flatten managed Gold before daily XAU break/weekend closure.

**Resolved initial close/reopen timing:**

```text
Daily break:
T-20m no new entry
T-10m mandatory flatten
Reopen: normalized conditions + 1 clean completed M5

Weekend:
T-60m no new entry
T-30m mandatory flatten
Reopen: gap assessment + normalized conditions + 2 clean completed M5
```

Timing is relative to verified broker XAU session schedule, not a guessed fixed clock.

**Resolved initial news policy:**

```text
TIER 1 CRITICAL   → -15 / +15 min hard entry blackout
TIER 2 HIGH       → -5 / +5 min hard entry blackout
TIER 3 CONTEXT    → no automatic hard blackout
```

Known linked TIER 1 clusters remain blocked through final critical item +15 min. Existing trade is not auto-closed solely due to news. Severe post-event dislocation requires one clean completed M5 plus normalized execution conditions.

Remaining session/news questions:

- Final production event provider(s), freshness TTL and provider-specific mapping table.
- Detailed handling of unusual long-duration speeches/unscheduled event classification.
- Future research-backed changes, if any, to frozen initial event tiers/windows.
- Exact holiday/liquidity-caution adjustments, if any, to soft scoring.
- Future research-backed changes, if any, to initial close/reopen timing.

## Execution / broker safety

**Resolved initial spread policy:** use healthy broker/symbol spread baseline. `SpreadRatio <=1.50` normal; `>1.50–2.25` elevated with full revalidation but not automatic block; `>2.25` block current entry. Independent guard blocks if spread exceeds 25% of approved entry-to-structural-SL price distance.

**Resolved initial price-drift policy:** adverse drift normalized by planned stop distance. `<=10%` normal revalidation; `>10–20%` elevated full revalidation; `>20%` blocks current Execution Intent/returns to WAIT when thesis survives. Risk/stop/target-room/chase invalidation blocks regardless of ratio.

**Resolved V1 controller/failover policy:** one shared cross-machine controller lease with monotonic fencing epoch. Initial renewal target is 10 seconds and TTL is 30 seconds. Every irreversible broker write must freshly verify current holder + non-expired matching epoch. A second laptop stays Observer while another valid controller exists. Standby takeover may occur only after lease expiry, must acquire a new epoch atomically, and must complete durable-state + broker reconciliation before becoming PRIMARY READY. Old/stale epochs cannot write after failover. Coordination uncertainty fails closed for broker writes.

Remaining execution questions:

- Exact healthy-spread rolling sampling window, minimum valid sample count and persisted-baseline expiry.
- Exact DEMO-to-future-REAL approval/config mechanism; REAL uses same centralized gate/engine.
- Final shared coordination-store backend/library satisfying the frozen lease/fencing contract.
- Exact broker comment/magic/lineage conventions.
- Exact retry policy for safe read-only/before-submit operations; irreversible ambiguous writes remain no-blind-retry.
- Future research-backed changes, if any, to initial spread/drift bands or controller lease timing.

## Persistence / backup / migration

- Final storage engines/formats for durable state and research/learning data.
- Exact Git-tracked state artifacts versus generated checkpoint artifacts.
- Backup/checkpoint cadence, retention and pruning policy.
- Exact financial-authority secret scanner/tooling and CI integration.
- State schema migration/rollback compatibility policy.
- Exact portable export/import packaging and integrity format.
- Whether backup publication to GitHub is automatic or performed by a controlled external/script workflow; GitHub credentials never embedded in tracked state.

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
- Exact `R,R` keyboard timing and safe-shutdown/export controls.
- Optional notification channels for critical health/trade events.
- Final wording polish for English technical terms plus concise Roman-Urdu explanations.

## Engineering / release

- Exact Python/runtime dependency versions and packaging policy.
- Final source filenames/classes once implementation starts.
- Exact persistence database/library choices.
- Exact CI/static/security/coverage thresholds.
- Exact controlled MT5 DEMO certification sample/steps and long-duration forward-evidence requirement.
- Final release packaging/version/tag strategy.

## Governance note

No major architectural subsystem is currently missing from the design corpus. Remaining items must be chosen, validated or explicitly deferred rather than guessed.
