# GoldSwingTraderAI — Open Questions / Freeze Matrix

**Status:** LIVING LEDGER  
**Version:** 2.3-design

This file separates remaining items so implementation is not delayed by values that should be learned from evidence or ordinary engineering choices.

```text
FIX BEFORE BUILD       = required architecture/safety decision still missing
CALIBRATE IN RESEARCH  = implement configurable deterministic baseline, tune with chronological evidence
IMPLEMENTATION CHOICE  = coder may choose a suitable implementation that preserves frozen contract
DEFER LATER            = not required for V1
```

A `CALIBRATE IN RESEARCH` item is **not permission to guess silently**. Initial values must be explicit/configurable, replay-safe and documented; research may propose governed changes.

## Current freeze status

At behavioural-contract level there are currently **no known `FIX BEFORE BUILD` items**.

Deterministic core implementation currently exists through Phase 10, including research evidence tooling:

```text
1  Foundation/config/domain/CI
2  MT5 read layer + market snapshots
3  Market intelligence + Trendline/Fibonacci/POC confluence
4  Strategies/fusion/Opportunity/Entry Timing
5  Trade Plan + Risk
6  Session/news permission + SQLite persistence
7  Execution intent/gate/controller/writer/reconciliation
8  Trade Manager + execution bridge
9  Dashboard renderer
10 Chronological replay + ablation + Trade Plan outcomes + Trade Manager replay
   + declared execution-friction stress
   + fixed-policy walk-forward validation
   + metrics/learning + discovery/invention/promotion
```

This does **not** mean live DEMO release is complete. The normal launcher remains read-only readiness; final persistent runtime orchestration, production shared cross-laptop coordination, backup/fresh-machine drill and controlled Windows/MT5 DEMO certification remain pending.

The frozen engineering style remains `../60-engineering/CODING_STANDARD.md`.

## Market intelligence

### FROZEN PRINCIPLES

- completed candles own structural confirmation;
- lower-TF structure cannot silently overwrite higher-TF state;
- optional market evidence does not become arbitrary hard safety;
- Trendline/Fibonacci/POC are optional confluence, not mandatory entry conditions;
- missing Trendline/Fibonacci/POC does not reduce base strategy score in initial production;
- POC is broker-local context; real volume preferred where available, otherwise tick-volume approximation is labelled honestly.

### CALIBRATE IN RESEARCH

- runtime candle-window sizes per timeframe;
- swing prominence/excursion/reversal/significance thresholds;
- qualified-break and BOS/MSS acceptance/follow-through quality;
- compression/expansion/exhaustion bands;
- S/R zone width/strength/freshness/role-flip thresholds;
- liquidity clustering and sweep/reclaim thresholds;
- FVG/qualified-OB quality thresholds;
- volatility/momentum/extension bands;
- indicator refinements beyond EMA20/EMA50/RSI14/ATR14;
- trendline proximity/break-buffer values;
- Fibonacci minimum-leg and retracement/extension weighting;
- POC lookback/bin/proximity values;
- whether each optional confluence source materially improves outcomes after ablation.

## Strategy / scoring / entry

### FROZEN V1 DIRECTION

Initial production floor contains six parallel families:

1. Trend Pullback Continuation
2. Breakout Expansion
3. Breakout Retest Continuation
4. Liquidity Sweep Reversal
5. Failed Breakout Reversal
6. Compression Expansion

Opportunity and Entry Timing remain separate; BUY/SELL theses independent; safety remains outside weighted scoring. Technical confluence is bonus-only, not a seventh mandatory family or hard gate.

### CALIBRATE IN RESEARCH

- family Opportunity thresholds;
- Entry Timing thresholds;
- evidence-group weights;
- synergy cap / conflict penalty / Red-Team calibration;
- minimum Evidence Coverage;
- chase/extension tolerance;
- ideal-entry zone/setup expiry;
- Market Episode duplicate/opportunity heuristics beyond frozen re-entry limit;
- bounded confluence bonus/correlation cap;
- whether a genuinely distinct confluence-led family deserves governed promotion.

### DEFER LATER

- independent FVG/OB-led production family unless research proves it;
- new confluence-led production family without governed validation/promotion.

## Trade Plan / targets / exits

### FROZEN INITIAL POLICY

```text
Credible target room <1.20R  → current plan rejected
1.20R–<1.50R                 → conditional; credible ~2R+ expansion path required
1.50R–<2.00R                 → good
2.00R+                       → strong
3R/4R+                       → runner potential
```

Primary Structural Target is normally a management checkpoint. Valid Expansion Target is default initial broker TP; valid Primary may be used if no Expansion exists. Fixed 100/200/300-pip TP logic is not used. Runner requires fresh continuation/acceptance plus a new objective. V1 core does not depend on partial closes.

### IMPLEMENTED RESEARCH EVIDENCE BASELINE

The production Trade Manager is reused chronologically in `research/management_replay.py`. `research/stress.py` adds declared adverse fill/spread/modify stress without changing production behaviour. `research/validation.py` now provides fixed-policy chronological walk-forward validation.

Walk-forward implementation rules are frozen at architecture level:

- development history may reconstruct causal state but is not scored as validation;
- validation slices cannot overlap;
- policy/config is fixed inside the validation run; no hidden auto-tuning;
- outcome data is clipped at validation end so later-window candles cannot resolve earlier trades;
- the utility cannot consume the one-shot final holdout.

Exact window sizes/sample requirements remain calibration, not frozen behaviour.

### CALIBRATE IN RESEARCH

- family-specific stop buffer;
- Stop Quality thresholds;
- protection/trailing eligibility;
- exact M5/M15/H1 trail precedence thresholds;
- continuation/reversal thresholds for HOLD/PROTECT/TRAIL/RUNNER/EXIT;
- objective-quality thresholds for runner progression;
- family/regime RR refinements;
- management replay versus DEMO outcome differences;
- empirical stress severity by broker/session/volatility;
- walk-forward development/validation event counts and window stepping;
- minimum independent validation sample/regime coverage.

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

There is **no V1 minimum-balance floor for positive SMALL accounts**. Actual min-lot all-in risk, ceiling, margin, daily lock and execution safety decide a specific plan.

Capacity is `0/1`. Account Safety P/L uses cash-flow-adjusted equity. Manual reset is OFF by default/max one per UTC risk day if enabled. Three consecutive closed bot losses trigger minimum 30-minute cooldown + fresh M15 context; same Market Episode permits at most one genuinely fresh re-entry.

### IMPLEMENTATION CHOICE

- broker-specific commission extraction where not already represented in executable/equity truth;
- classification adapter for unusual broker balance/credit operations, unknown fails safely.

### CALIBRATE IN RESEARCH

- slippage reserve model by broker/session/volatility;
- future drawdown-aware preference inside frozen bands.

### DEFER LATER

- multi-position aggregate-risk model beyond V1 `0/1`;
- separate emergency trade-count quota.

### OPERATOR DETAIL

- exact `R,R` second-key timing window.

## Session / news

### FROZEN INITIAL POLICY

```text
TIER 1 CRITICAL  → -15/+15 min entry blackout
TIER 2 HIGH      → -5/+5 min entry blackout
TIER 3 CONTEXT   → no automatic hard blackout

Daily break:    T-20m no entry, T-10m mandatory flatten
Daily reopen:   normalized + 1 clean completed M5
Weekend:        T-60m no entry, T-30m mandatory flatten
Weekend reopen: gap assessment + normalized + 2 clean completed M5
```

Deterministic permission logic is implemented in `risk/permissions.py`.

### IMPLEMENTATION CHOICE / INTEGRATION PENDING

- production event-provider adapter, TTL and mapping preserving `NEWS_SAFETY_UNKNOWN`;
- verified broker-session schedule adapter preserving `SESSION_SCHEDULE_UNKNOWN`;
- historical broker-session schedule source/representation needed to reproduce PRE_CLOSE inside research manager replay without guessed clock times.

### CALIBRATE IN RESEARCH

- holiday/liquidity caution contribution to soft scoring;
- evidence-backed future changes to blackout/reopen timings.

## Execution / broker safety

### FROZEN INITIAL POLICY

Spread:

```text
SpreadRatio <=1.50         → NORMAL
>1.50–2.25                 → ELEVATED + full revalidation
>2.25                      → current entry prevented
spread >25% of SL distance → current entry prevented
```

Adverse drift:

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
Verified connected MT5 DEMO → DEMO_GUARD PASS
DEMO not verified           → broker-write permission not granted
```

V1 defines no separate REAL authorization workflow.

### IMPLEMENTED DETERMINISTIC BASELINE

- durable ExecutionIntent lifecycle;
- centralized gate/checks;
- one-shot send invariant;
- raw MT5 writer boundary;
- success-like ACK still requires broker verification;
- ambiguous result becomes reconciliation-only;
- OPEN/MODIFY/CLOSE reconciliation;
- durable lineage authority;
- lease/fencing semantics with deterministic in-memory test backend.

### IMPLEMENTED RESEARCH-STRESS BASELINE

```text
BASE                no added friction
WIDER_SPREAD        1.50x dataset spread
ADVERSE_ENTRY       0.10R adverse fill
MODIFY_DELAY        1 completed M5
MODIFY_REJECTION    every 2nd submitted modify rejected
COMBINED            all four together
```

These are configurable **research baselines only**. They do not alter frozen production spread/drift rules and are not claims about actual broker distributions.

### IMPLEMENTATION CHOICE / INTEGRATION PENDING

- production shared cross-laptop coordination backend satisfying atomic lease/fencing contract;
- final magic/comment shape if later adjustment needed;
- bounded read-only/pre-submit retry/backoff;
- broker-specific reconciliation refinements from controlled evidence;
- healthy-spread-baseline persistence/sample implementation.

### CALIBRATE IN RESEARCH / DEMO OBSERVATION

- spread baseline sample window/minimum count/expiry;
- empirical slippage distribution by broker/session/volatility;
- empirical manager modification delay/failure distribution;
- variable-spread/tick-order stress where trustworthy data exists;
- evidence-backed spread/drift/lease timing refinements.

## Persistence / backup / migration

### IMPLEMENTED V1 FOUNDATION

```text
standard-library SQLite
+ canonical JSON records
+ SHA-256 checksums
+ explicit schema versions
+ transactional updates
+ event rows where requested
+ typed recovery adapters
```

Current persistence covers risk/cooldown/episode state, Opportunity/TradePlan, ExecutionIntent, managed-trade state and research/candidate/promotion state. Critical corruption/version mismatch fails explicitly. Broker remains authority for current positions/orders/deals.

### IMPLEMENTATION CHOICE / PHASE 11–12

- backup/checkpoint cadence/retention;
- portable checkpoint/export/manifest format;
- schema migration/rollback mechanism when schema v2+ exists;
- automatic/public GitHub publication packaging for allowed recovery state;
- final fresh-machine restore workflow;
- production shared controller coordination persistence/hosting.

Live mutable SQLite DB is runtime state, not a mergeable source artifact. Public backup/export excludes financial-authority secrets.

## Research / learning / autonomous improvement

### IMPLEMENTED DETERMINISTIC FOUNDATION

- chronological bar-close Decision replay;
- same-chronology confluence ablation;
- historical production Trade Plan reconstruction;
- ambiguity-safe initial bracket outcomes;
- chronological production Trade Manager replay;
- declared execution-friction stress engine;
- fixed-policy walk-forward validation scaffold;
- actual/counterfactual metric separation;
- research episode journal;
- bounded StrategyMemory;
- approved declarative primitive registry;
- durable candidate/rejected memory;
- recurring-cluster invention cycle;
- discovery `IDLE / HEALTHY / DEGRADED` liveness;
- governed promotion stages/locked fingerprint/one-shot holdout/self-promotion denial.

Research realism remains explicit:

```text
Decision replay          BAR_CLOSE
Initial bracket outcomes BAR_HIGH_LOW
Trade Manager replay     BAR_CLOSE_IDEALIZED
Execution stress         BAR_CLOSE_EXECUTION_STRESS + declared assumptions
Walk-forward             FIXED_POLICY_WALK_FORWARD
```

Walk-forward is independent chronological evidence, not the final untouched holdout. Ambiguous/unresolved/open modeled outcomes are not forced into resolved P/L.

### FROZEN PRINCIPLES

Research cannot self-promote production, bypass hard safety, execute arbitrary Python or leak future data. Eligible discovery evidence must create a candidate or explicit governed suppression reason.

### IMPLEMENTATION CHOICE / NEXT RESEARCH ENGINEERING

- dataset identity/versioning for broader XAU history;
- reproducible evidence-manifest packaging;
- historical PRE_CLOSE integration once trustworthy schedule history exists;
- real-data walk-forward orchestration using declared dataset identities.

### CALIBRATE IN RESEARCH

- minimum sample/confidence by family/regime;
- development/validation/holdout periods;
- walk-forward window sizes/stepping and minimum validation sample;
- empirical execution-stress severity and acceptance thresholds;
- Shadow/DEMO Canary/Main DEMO promotion thresholds;
- bounded StrategyMemory influence;
- Entry/Exit Learning candidate thresholds;
- autonomous recipe ranges;
- duplicate-variant classifier thresholds;
- Monte Carlo/block/regime-aware methods;
- optional confluence value through decision/bracket/management evidence.

### DEFER LATER

- opaque/complex ML as a V1 dependency.

## Operator / dashboard

### IMPLEMENTED BASELINE

- lightweight stdlib dashboard renderer;
- requested GoldScalperAI facts plus Decision/Execution/Health presentation contracts.

### INTEGRATION / POLISH PENDING

- authoritative runtime state-builder into DashboardData;
- Discovery Health/candidate/suppression fields;
- optional Trendline/Fib/POC compact display;
- in-place refresh cadence/dimensions;
- safe-shutdown/export controls;
- concise Roman-Urdu wording polish;
- live Windows terminal visual verification.

## Engineering / release

### FROZEN ENGINEERING PRINCIPLE

- Python 3.11+;
- `CODING_STANDARD.md` authoritative;
- minimal/standard-library-first runtime;
- official `MetaTrader5` terminal boundary;
- heavier research dependencies isolated unless governed later.

### IMPLEMENTATION CHOICE

- final dependency pins/upper bounds;
- CI coverage/static/security thresholds;
- packaging/version/tag layout;
- optional research-only analytical libraries.

### REQUIRED BEFORE VERIFIED RELEASE

- final persistent runtime orchestration;
- controlled MT5 DEMO certification;
- no-lookahead replay proof;
- confluence chronology + bonus-only proof;
- real-data independent/walk-forward evidence;
- discovery-liveness proof;
- duplicate-write/fault-injection proof;
- production shared controller/fencing proof;
- scheduled PRE_CLOSE/reopen proof;
- restart/reconciliation proof;
- fresh-machine recovery proof;
- financial-secret scan;
- Coding Standard quality review;
- final release audit with actual evidence.

## Governance conclusion

Behavioural design is complete enough to continue implementation/integration. No major subsystem or `FIX BEFORE BUILD` item is currently known.

Closed software gaps now include the former `$100` floor, local persistence-engine choice, chronological production Trade Manager research path, deterministic execution-stress foundation and fixed-policy walk-forward validation scaffold.

Current main work is **integration and evidence**, not redesign: identify/version real XAU datasets and package reproducible evidence, run meaningful walk-forward validation, calibrate stress, add historical session realism, then finish runtime/provider/shared-coordination/backup integration and controlled DEMO certification.

Documents remain `DRAFT/PROVISIONAL` where real historical/live broker evidence does not yet exist. Do not relabel them VERIFIED until required evidence passes.
