# GoldSwingTraderAI — Open Questions / Freeze Matrix

**Status:** LIVING LEDGER  
**Version:** 2.5-design

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

Deterministic core implementation currently exists through Phase 10, including:

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
   + declared execution stress
   + fixed-policy walk-forward validation
   + content-addressed dataset/evidence manifests
   + portable integrity-checked replay dataset bundles
   + metrics/learning + discovery/invention/promotion
```

This does **not** mean live DEMO release is complete. The normal launcher remains read-only readiness; final persistent orchestration, production shared cross-laptop coordination, runtime-state backup/fresh-machine drill and controlled Windows/MT5 DEMO certification remain pending.

## Market intelligence

### FROZEN PRINCIPLES

- completed candles own structural confirmation;
- lower-TF structure cannot silently overwrite higher-TF state;
- optional evidence does not become arbitrary hard safety;
- Trendline/Fibonacci/POC remain optional bonus-only confluence;
- broker-local POC uses real volume when available, otherwise labelled tick-volume approximation.

### CALIBRATE IN RESEARCH

- candle windows, swing/break/compression/zone/liquidity/FVG/OB thresholds;
- volatility/momentum/extension bands;
- indicator refinements beyond initial EMA20/50, RSI14, ATR14;
- trendline/Fibonacci/POC parameters;
- measured value of each optional confluence source.

## Strategy / scoring / entry

### FROZEN V1 DIRECTION

Six parallel production families remain:

1. Trend Pullback Continuation
2. Breakout Expansion
3. Breakout Retest Continuation
4. Liquidity Sweep Reversal
5. Failed Breakout Reversal
6. Compression Expansion

Opportunity and Entry Timing are separate; BUY/SELL theses independent; safety outside weighted scoring; confluence is not a seventh mandatory family.

### CALIBRATE IN RESEARCH

- family/opportunity/timing thresholds;
- evidence weights, synergy/conflict/Red-Team calibration;
- evidence coverage, chase, setup expiry;
- Market Episode heuristics beyond frozen re-entry limit;
- bounded confluence bonus/correlation cap;
- whether research supports any genuinely distinct new family.

## Trade Plan / targets / exits

### FROZEN INITIAL POLICY

```text
Credible target room <1.20R  → reject
1.20R–<1.50R                 → conditional; credible ~2R+ path required
1.50R–<2.00R                 → good
2.00R+                       → strong
3R/4R+                       → runner potential
```

Primary is normally management checkpoint; Expansion is default broker TP; fixed-pip TP is not used; runner requires fresh continuation/new objective; V1 does not depend on partial closes.

### IMPLEMENTED RESEARCH BASELINE

- chronological production Trade Manager replay;
- declared execution-friction stress;
- fixed-policy walk-forward validation with non-overlapping scored validation slices and no final-holdout authority;
- content-addressed dataset/evidence identity for reproducible research;
- portable research dataset export/import with integrity verification.

### CALIBRATE IN RESEARCH

- family stop buffers and Stop Quality;
- trail/protection/runner thresholds;
- family/regime RR refinements;
- replay-versus-DEMO management differences;
- empirical stress severity;
- walk-forward development/validation counts/stepping and minimum sample/regime coverage.

## Risk

### FROZEN INITIAL POLICY

```text
Profile  Equity Range            Normal Risk   Elevated Risk    Entry Ceiling   Daily Lock
SMALL    >0 and < $300           3.0–4.5%      >4.5–6.5%        7%              12%
MEDIUM   $300–$999.99            2.0–3.0%      >3.0–4.5%        5%               9%
NORMAL   $1,000+                 1.0–2.0%      >2.0–3.5%        4%               7%
```

No positive-balance `$100` floor. Capacity `0/1`. Account Safety P/L uses cash-flow-adjusted equity. Manual reset OFF by default/max one per UTC risk day if enabled. Three consecutive closed bot losses trigger minimum 30-minute cooldown + fresh M15 context.

### IMPLEMENTATION CHOICE / CALIBRATION

- unusual broker balance/credit classification;
- commission extraction where not represented in executable/equity truth;
- empirical slippage reserve;
- future drawdown-aware preference inside frozen bands.

## Session / news

### FROZEN INITIAL POLICY

```text
TIER 1 → -15/+15
TIER 2 → -5/+5
TIER 3 → context only
Daily  → T-20 no entry, T-10 flatten, reopen + 1 clean M5
Weekend→ T-60 no entry, T-30 flatten, reopen gap assessment + 2 clean M5
```

### INTEGRATION PENDING

- production event-provider adapter/TTL/mapping;
- verified broker-session schedule adapter;
- trustworthy historical broker-session schedule source for PRE_CLOSE replay.

## Execution / broker safety

### FROZEN INITIAL POLICY

Spread: `<=1.50` normal, `>1.50–2.25` elevated/revalidate, `>2.25` block, spread >25% SL distance block.

Adverse drift: `<=10%` normal, `>10–20%` revalidate, `>20%` prevent current intent.

Controller: one PRIMARY, 10s renewal target, 30s TTL, monotonic fencing epoch, fresh ownership before every write, takeover only after expiry + reconciliation.

Verified connected DEMO is required for V1 broker-write permission.

### IMPLEMENTED DETERMINISTIC BASELINE

ExecutionIntent lifecycle, centralized gate, one-shot send, MT5 writer boundary, reconciliation and deterministic lease/fencing semantics exist.

### IMPLEMENTED RESEARCH-STRESS BASELINE

```text
WIDER_SPREAD        1.50x dataset spread
ADVERSE_ENTRY       0.10R adverse fill
MODIFY_DELAY        1 completed M5
MODIFY_REJECTION    every 2nd submitted modify rejected
COMBINED            all four
```

These are research calibration baselines only.

### INTEGRATION / CALIBRATION PENDING

- production shared cross-laptop atomic coordination backend;
- bounded read retry/backoff and broker-specific reconciliation refinements;
- healthy-spread-baseline persistence;
- empirical slippage/modify failure/delay distributions;
- variable-spread/tick-order evidence where available.

## Persistence / backup / migration

### IMPLEMENTED V1 FOUNDATION

Standard-library SQLite + canonical JSON + SHA-256 checksums + explicit schema versions + transactional state/events + typed recovery adapters.

Portable **research datasets** now have a separate implemented CSV/manifest bundle. That does not replace the runtime-state backup/checkpoint work below.

### PHASE 11–12 PENDING

- runtime-state backup/checkpoint cadence/retention;
- portable runtime checkpoint/export/manifest format;
- schema migration/rollback when v2+ exists;
- automatic/public GitHub publication packaging for allowed recovery state;
- fresh-machine restore workflow;
- production shared controller persistence/hosting.

## Research / learning / evidence

### IMPLEMENTED DETERMINISTIC FOUNDATION

- chronological Decision replay;
- confluence ablation;
- production Trade Plan reconstruction and ambiguity-safe bracket outcomes;
- chronological production Trade Manager replay;
- declared execution stress;
- fixed-policy walk-forward validation;
- content-addressed `ReplayDatasetIdentity`;
- per-timeframe and dataset SHA-256 hashes;
- `ResearchEvidenceManifest` with code/policy/data/config/results/limitations;
- separate experiment-input fingerprint and complete-manifest hash;
- canonical JSON representation;
- evidence-key `FINANCIAL_SECRET_DETECTED` guard;
- portable `dataset_manifest.json` + timeframe CSV bundle export/import;
- bundle manifest/file/bar-count/recomputed-identity verification;
- optional supported timeframe preservation, including M1;
- broker endpoint login/server exclusion from research bundle;
- metrics/StrategyMemory/research episodes;
- declarative discovery/invention and governed promotion.

### FROZEN RESEARCH/EVIDENCE PRINCIPLES

- no future leakage;
- no autonomous production promotion or hard-safety bypass;
- walk-forward development context is not validation evidence;
- later windows cannot resolve earlier validation outcomes;
- walk-forward cannot consume final holdout;
- serious evidence must identify code revision + policy version + content-addressed dataset + explicit config/realism/limitations;
- mutable filename alone is not sufficient dataset identity;
- evidence manifests must not contain financial-authority secrets;
- broker endpoint login/server is not part of replay-economic dataset identity;
- a portable dataset is trusted only after manifest/file/content identity verification;
- existing research bundle destinations are never silently overwritten.

### NEXT IMPLEMENTATION CHOICES

- authoritative real historical XAU acquisition/import adapter(s) feeding the portable dataset contract;
- persisted evidence package layout/naming/retention beside immutable dataset identities;
- integration of generated manifests with broad real-data walk-forward/stress reports;
- historical PRE_CLOSE schedule integration once trustworthy data exists.

### CALIBRATE IN RESEARCH

- real-data sources/periods/sample sizes;
- development/validation/holdout periods and acceptance thresholds;
- stress severity;
- Shadow/DEMO Canary/Main DEMO thresholds;
- StrategyMemory influence and learning candidate thresholds;
- recipe/duplicate classifier parameters;
- Monte Carlo/block/regime-aware methods;
- optional confluence retention thresholds.

## Operator / dashboard

### IMPLEMENTED BASELINE

Lightweight stdlib renderer with requested GoldScalperAI facts plus Decision/Execution/Health presentation contracts.

### PENDING

Authoritative runtime DTO builder, Discovery Health/candidate/suppression display, compact confluence display, refresh/polish and Windows visual verification.

## Engineering / release

### REQUIRED BEFORE VERIFIED RELEASE

- final persistent runtime orchestration;
- controlled MT5 DEMO certification;
- broad reproducible real-data research evidence;
- no-lookahead/confluence/discovery proof;
- duplicate-write/fault-injection proof;
- production shared controller/fencing proof;
- scheduled PRE_CLOSE/reopen proof;
- restart/reconciliation and fresh-machine recovery proof;
- financial-secret scan;
- final coding/release audit.

## Governance conclusion

No major behavioural `FIX BEFORE BUILD` item is known.

Closed software-foundation gaps now include chronological production Trade Manager research, declared execution stress, fixed-policy walk-forward validation, deterministic dataset/evidence identity and portable integrity-checked research dataset bundles.

Current main work is **authoritative real-data acquisition/integration and evidence**, followed by runtime/provider/shared-controller/backup integration and controlled DEMO certification. Documents remain DRAFT/PROVISIONAL where real historical/live evidence is not yet complete.
