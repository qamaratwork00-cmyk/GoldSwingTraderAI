# GoldSwingTraderAI — Open Questions / Freeze Matrix

**Status:** LIVING LEDGER  
**Version:** 1.8-design

This file separates remaining items into four classes so implementation is not delayed by values that should be learned from evidence or ordinary engineering choices.

```text
FIX BEFORE BUILD       = required architecture/safety decision still missing
CALIBRATE IN RESEARCH  = implement configurable deterministic baseline, tune with chronological evidence
IMPLEMENTATION CHOICE  = coder may choose a suitable implementation that preserves frozen contract
DEFER LATER            = not required for V1
```

A `CALIBRATE IN RESEARCH` item is **not permission to guess silently**. Initial values must be explicit/configurable, replay-safe and documented; research may propose governed changes.

## Current freeze status

At behavioural-contract level there are currently **no `FIX BEFORE BUILD` items**. The major trading, risk, session, execution, persistence, learning and recovery architecture is sufficiently defined for implementation to continue through the large phases in `../CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md`.

The V1 engineering style is frozen in `../60-engineering/CODING_STANDARD.md`: Python 3.11+, lightweight production runtime, minimal dependencies, direct/auditable architecture, shared snapshot/derived calculations and professional non-noisy commenting/error handling.

Remaining items below are research calibration, ordinary implementation choices, operator details or later-version work; they must not silently change frozen behavioural or engineering invariants.

## Market intelligence

### CALIBRATE IN RESEARCH

- runtime candle-window sizes per timeframe;
- volatility-normalized swing prominence/excursion thresholds;
- candidate-to-confirmed swing reversal/persistence requirements;
- swing-significance weights/classes;
- completed-close penetration for `QUALIFIED_BREAK`;
- family-specific BOS/MSS acceptance/follow-through quality;
- compression/expansion/exhaustion bands;
- S/R zone width/strength/freshness/role-flip thresholds;
- equal-high/low/liquidity clustering tolerance and sweep/reclaim thresholds;
- FVG/qualified-OB quality thresholds;
- volatility/momentum/extension bands;
- indicator parameter refinements beyond initial EMA20/EMA50/RSI/ATR design.

### FROZEN PRINCIPLE

Completed candles own structural confirmation. Forming-candle/intrabar information is telemetry only unless a later explicit contract grants it structural authority.

## Strategy / scoring / entry

### FROZEN V1 DIRECTION

Initial strategy floor contains six parallel families:

1. Trend Pullback Continuation
2. Breakout Expansion
3. Breakout Retest Continuation
4. Liquidity Sweep Reversal
5. Failed Breakout Reversal
6. Compression Expansion

Opportunity and Entry Timing remain separate; BUY and SELL theses are independent; safety remains outside weighted scoring.

### CALIBRATE IN RESEARCH

- family-specific Opportunity Score thresholds;
- Entry Timing thresholds;
- evidence-group weights;
- synergy cap;
- conflict penalty;
- Red-Team calibration;
- minimum Evidence Coverage;
- chase/extension tolerance;
- ideal-entry zone and setup-expiry values;
- exact Market Episode duplicate/opportunity heuristics beyond the frozen re-entry limit.

### DEFER LATER

- independent FVG/OB-led production family unless research proves it deserves one.

## Trade Plan / targets / exits

### FROZEN INITIAL POLICY

```text
Credible target room <1.20R  → current plan rejected
1.20R–<1.50R                 → conditional; credible ~2R+ expansion path required
1.50R–<2.00R                 → good
2.00R+                       → strong
3R/4R+                       → runner potential
```

Primary Structural Target is normally a management checkpoint. A valid Expansion Target is the default initial broker TP; a valid Primary Target may be used when no valid Expansion Target exists. Fixed 100/200/300-pip TP logic is not used. Runner extension requires fresh continuation/acceptance evidence and a new objective. V1 core logic does not depend on partial closes.

### CALIBRATE IN RESEARCH

- family-specific stop-buffer calculation;
- Stop Quality numeric thresholds;
- protection/trailing eligibility;
- exact M5/M15/H1 structural trail precedence thresholds;
- continuation/reversal thresholds for HOLD/PROTECT/TRAIL/RUNNER/EXIT;
- objective-quality thresholds for runner progression;
- future family/regime refinements to initial RR guard.

### DEFER LATER

- partial-profit system for larger divisible volume.

## Risk

### FROZEN INITIAL POLICY

```text
Profile  Equity Range            Normal Risk   Elevated Risk    Entry Ceiling   Daily Lock
SMALL    >0 and < $300           3.0–4.5%      >4.5–6.5%        7%              12%
MEDIUM   $300–$999.99            2.0–3.0%      >3.0–4.5%        5%               9%
NORMAL   $1,000+                 1.0–2.0%      >2.0–3.5%        4%               7%
```

There is **no V1 minimum-balance floor for a positive SMALL account**. `$99`, `$50`, `$30`, etc. remain SMALL; actual minimum-lot all-in risk, hard ceiling, margin, daily lock and execution safety decide whether a specific plan can trade.

Capacity is `0/1`. Account Safety P/L uses cash-flow-adjusted equity change. Manual loss reset is OFF by default and, when explicitly enabled, max one per UTC risk day. Three consecutive closed bot losses trigger minimum 30-minute cooldown plus fresh M15 context; same Market Episode allows at most one genuinely fresh re-entry.

### IMPLEMENTATION CHOICE

- broker-specific commission extraction where not already represented in executable/equity truth;
- classification adapter for unusual broker balance/credit operations, provided unknown classification fails safely.

### CALIBRATE IN RESEARCH

- slippage reserve model by broker/session/volatility;
- any future drawdown-aware preference inside already frozen risk bands.

### DEFER LATER

- multi-position aggregate-risk model beyond V1 `0/1`;
- separate emergency trade-count quota. V1 relies on intent uniqueness, episode/re-entry controls, one-shot writes and reconciliation rather than a normal trade quota.

### OPERATOR DETAIL TO FIX DURING UX IMPLEMENTATION

- exact `R,R` second-key timing window.

## Session / news

### FROZEN INITIAL POLICY

```text
TIER 1 CRITICAL  → -15/+15 min entry blackout
TIER 2 HIGH      → -5/+5 min entry blackout
TIER 3 CONTEXT   → no automatic hard blackout
```

Severe post-news dislocation requires normalized conditions plus one clean completed M5.

```text
Daily break:    T-20m no new entry, T-10m mandatory flatten
Daily reopen:   normalized conditions + 1 clean completed M5
Weekend:        T-60m no new entry, T-30m mandatory flatten
Weekend reopen: gap assessment + normalized conditions + 2 clean completed M5
```

### IMPLEMENTATION CHOICE

- production event-provider adapter(s), freshness TTL and provider mapping, while preserving `NEWS_SAFETY_UNKNOWN` on required-truth failure.

### CALIBRATE IN RESEARCH

- holiday/liquidity caution contribution to soft scoring;
- future evidence-backed changes to blackout/reopen timings.

### DEFER LATER

- special long-duration speech taxonomy beyond ordinary event/shock handling unless required by actual provider data.

## Execution / broker safety

### FROZEN INITIAL POLICY

Spread:

```text
SpreadRatio <=1.50         → NORMAL
>1.50–2.25                 → ELEVATED + full revalidation
>2.25                      → current entry prevented
spread >25% of SL distance → current entry prevented
```

Adverse price drift:

```text
<=10% of planned SL distance → normal revalidation
>10–20%                      → elevated full revalidation
>20%                         → current intent prevented / WAIT if thesis survives
```

Controller:

```text
one PRIMARY
10s renewal target
30s lease TTL
monotonic fencing epoch
fresh ownership before every broker write
standby takeover only after expiry + full reconciliation
```

Environment:

```text
Verified connected MT5 DEMO account → DEMO_GUARD PASS
DEMO status not verified            → broker-write permission not granted
```

V1 defines only the positive DEMO guard. There is no separate REAL authorization policy or REAL hard-block contract in V1.

### IMPLEMENTATION CHOICE

- shared coordination-store product/library, provided frozen atomic lease + fencing contract is satisfied;
- exact broker comment string shape and magic integer, provided durable Execution Intent/Trade lineage remains authoritative and magic/comment are only reconciliation aids;
- bounded retry/backoff mechanics for safe read-only/pre-submit operations; irreversible ambiguous writes remain one-shot/reconciliation-only.

### CALIBRATE IN RESEARCH / DEMO OBSERVATION

- healthy-spread baseline sample window/minimum count and persisted-baseline expiry;
- future evidence-backed spread/drift/lease timing refinements.

## Persistence / backup / migration

### FIX BEFORE BUILD

None at behavioural-contract level. Broker truth remains authoritative for live positions/orders/deals; critical local lifecycle/risk state must persist and reconcile.

### IMPLEMENTATION CHOICE

Initial implementation may choose storage stack, schema layout, checkpoint format, migration mechanism, backup cadence/retention and export packaging provided it satisfies:

- atomic/durable critical state;
- schema versioning;
- restart recovery;
- Strategy Registry + learning portability;
- broker reconciliation;
- fresh-machine restore test;
- public backup of useful project intelligence;
- financial-authority secret exclusion/scanning.

Live mutable database files need not be Git-merged directly if a safer portable checkpoint/export represents the same required recovery state.

The chosen persistence stack must also satisfy the frozen Coding Standard: use the smallest safe solution and do not add ORM/service-layer complexity without a demonstrated need.

## Research / learning / autonomous improvement

### FROZEN PRINCIPLE

Research is automatic where practical but cannot self-promote production, bypass hard safety, generate/execute arbitrary Python or leak future data into replay.

### CALIBRATE IN RESEARCH

- minimum sample/confidence requirements by family/regime;
- development/validation/holdout periods;
- walk-forward/stress details;
- Shadow/DEMO Canary/Main DEMO promotion thresholds;
- bounded StrategyMemory influence;
- Entry/Exit Learning candidate thresholds;
- autonomous recipe parameter ranges;
- duplicate-variant classifier;
- Monte Carlo/block/regime-aware methods if useful.

### DEFER LATER

- opaque/complex ML model as a V1 dependency. V1 remains fully functional with explicit interpretable logic.

## Operator / dashboard

### IMPLEMENTATION CHOICE

- exact terminal dimensions/section order;
- dashboard refresh cadence independent of decision cadence;
- safe-shutdown/export key layout;
- concise English/Roman-Urdu wording polish.

### DEFER LATER

- optional external notification channels.

## Engineering / release

### FROZEN ENGINEERING PRINCIPLE

- Python baseline is **3.11+**;
- production runtime follows `../60-engineering/CODING_STANDARD.md`;
- runtime dependencies are minimal/standard-library-first;
- official `MetaTrader5` is the terminal-integration boundary;
- heavier research/data-science dependencies remain isolated from normal runtime unless a later governed decision proves otherwise.

### IMPLEMENTATION CHOICE

- exact compatible dependency pins/upper bounds within the frozen baseline;
- final filenames/classes while preserving documented ownership;
- persistence libraries consistent with the lightweight standard;
- CI/static/security/coverage thresholds;
- packaging/version/tag layout;
- optional research-only analytical libraries.

### REQUIRED BEFORE VERIFIED RELEASE

- controlled MT5 DEMO certification;
- no-lookahead replay proof;
- duplicate-write/fault-injection proof;
- controller split-brain/fencing proof;
- scheduled PRE_CLOSE/reopen proof;
- restart/reconciliation proof;
- fresh-machine recovery proof;
- financial-secret scan;
- frozen Coding Standard quality review;
- final release audit with actual evidence.

## Governance conclusion

The behavioural design close-out is complete enough for implementation to continue. No major subsystem or `FIX BEFORE BUILD` item is currently known.

The former below-`$100` profile question is closed: any positive equity below `$300` is SMALL. Actual risk geometry and existing safety authorities decide trade affordability.

Research-calibration values and ordinary library/file choices remain explicit work for implementation/replay. Python/runtime complexity principles are frozen by `CODING_STANDARD.md` and DEC-063.

Documents remain honestly `DRAFT/PROVISIONAL` where implementation or executable verification does not yet exist. They must not be relabeled `IMPLEMENTED` or `VERIFIED` until required code/tests/evidence actually exist.
