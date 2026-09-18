# GoldSwingTraderAI — Open Questions / Freeze Matrix

**Status:** LIVING LEDGER  
**Version:** 2.6-design

This file separates remaining items so implementation is not delayed by values that should be learned from evidence or ordinary engineering choices.

```text
FIX BEFORE BUILD       = required architecture/safety decision still missing
CALIBRATE IN RESEARCH  = explicit deterministic baseline, tune only with chronological evidence
IMPLEMENTATION CHOICE  = coder may choose implementation preserving frozen contract
DEFER LATER            = not required for V1
```

At behavioural-contract level there are currently **no known `FIX BEFORE BUILD` items**.

## Current implementation status

Deterministic core exists through Phase 10 including:

```text
1  Foundation/config/domain/CI
2  MT5 read layer + market snapshots
3  Market intelligence + Trendline/Fibonacci/POC
4  Strategies/fusion/Opportunity/Entry Timing
5  Trade Plan + Risk
6  Session/news permission + SQLite persistence
7  Execution intent/gate/controller/writer/reconciliation
8  Trade Manager + execution bridge
9  Dashboard renderer
10 Chronological replay / ablation / outcomes / Trade Manager replay
   + execution stress
   + fixed-policy walk-forward
   + dataset/evidence identity
   + portable integrity-checked research datasets
   + read-only MT5 historical acquisition adapter
   + metrics/learning/discovery/invention/promotion
```

This does **not** mean live DEMO release or real-data validation is complete. Final runtime orchestration, shared cross-laptop coordination, runtime-state backup/fresh-machine drill, controlled Windows/MT5 evidence and DEMO certification remain pending.

## Market intelligence

### FROZEN

- completed candles own structural confirmation;
- lower-TF cannot silently overwrite higher-TF state;
- Trendline/Fibonacci/POC are optional bonus-only confluence, not mandatory gates;
- broker-local POC uses real volume where available, otherwise labelled tick-volume approximation.

### CALIBRATE

- candle/swing/break/compression/zone/liquidity/FVG/OB thresholds;
- volatility/momentum/extension bands;
- confluence parameters and measured value;
- future evidence-backed indicator refinements.

## Strategy / scoring / entry

### FROZEN

Six parallel production families remain Trend Pullback, Breakout Expansion, Breakout Retest, Liquidity Sweep Reversal, Failed Breakout Reversal and Compression Expansion. BUY/SELL theses are independent; safety stays outside weighted scoring; confluence is not a seventh mandatory family.

### CALIBRATE

Family/opportunity/timing thresholds, evidence weights, synergy/conflict/Red-Team calibration, coverage/chase/expiry, Market Episode heuristics and bounded confluence bonus/correlation cap.

## Trade Plan / targets / exits

### FROZEN

```text
<1.20R       reject current plan
1.20–<1.50R conditional; credible ~2R+ expansion path required
1.50–<2.00R good
2.00R+       strong
3R/4R+       runner potential
```

Primary is normally checkpoint; Expansion default broker TP; no fixed-pip TP; runner requires fresh continuation/new objective; V1 does not depend on partial closes.

### CALIBRATE

Family stop buffers/Stop Quality, trail/protection/runner thresholds, family/regime RR refinements and replay-vs-DEMO management differences.

## Risk

### FROZEN

```text
SMALL   >0 and < $300     normal 3.0–4.5%   elevated >4.5–6.5%   ceiling 7%   daily lock 12%
MEDIUM  $300–$999.99      normal 2.0–3.0%   elevated >3.0–4.5%   ceiling 5%   daily lock 9%
NORMAL  $1,000+           normal 1.0–2.0%   elevated >2.0–3.5%   ceiling 4%   daily lock 7%
```

No positive-balance `$100` floor. Capacity `0/1`. Account Safety P/L uses cash-flow-adjusted equity. Manual reset OFF by default/max one per UTC day if enabled. Three consecutive closed bot losses trigger minimum 30-minute cooldown + fresh M15 context.

### CALIBRATE / IMPLEMENTATION

Unusual broker balance/credit classification, commission extraction where needed, empirical slippage reserve and future drawdown-aware preference inside frozen bands.

## Session / news

### FROZEN

```text
Tier1 -15/+15
Tier2 -5/+5
Tier3 context only
Daily T-20 no entry / T-10 flatten / reopen +1 clean M5
Weekend T-60 no entry / T-30 flatten / reopen gap assessment +2 clean M5
```

### PENDING

Production event-provider adapter/TTL/mapping, verified broker-session schedule adapter and trustworthy historical session schedule source for PRE_CLOSE replay.

## Execution / broker safety

### FROZEN

Spread `<=1.50` normal, `>1.50–2.25` elevated/revalidate, `>2.25` block, and >25% SL distance block. Adverse drift `<=10%` normal, `>10–20%` revalidate, `>20%` prevent current intent. One PRIMARY controller with lease/fencing. Verified connected DEMO required for V1 broker-write permission.

### IMPLEMENTED

ExecutionIntent lifecycle, centralized gate, one-shot send, writer boundary, reconciliation and deterministic lease/fencing semantics.

### PENDING / CALIBRATE

Production shared cross-laptop backend, broker-specific retry/reconciliation refinements, healthy-spread baseline persistence, empirical slippage/modify-failure/delay and variable-spread/tick evidence.

## Persistence / backup / migration

### IMPLEMENTED

Standard-library SQLite + canonical JSON + SHA-256 checksums + schema versions + transactional state/events + typed recovery adapters.

Portable **research dataset** bundles are implemented separately; they do not replace runtime-state backup.

### PHASE 11–12 PENDING

Runtime-state backup cadence/retention, portable runtime checkpoint manifest, migration/rollback for future schemas, public-safe backup publication, fresh-machine restore and production shared controller hosting.

## Research / learning / evidence

### IMPLEMENTED DETERMINISTIC FOUNDATION

- chronological Decision replay;
- confluence ablation;
- Trade Plan and Trade Manager outcome replay;
- declared execution stress;
- fixed-policy walk-forward;
- content-addressed dataset/evidence identity;
- portable `dataset_manifest.json` + timeframe CSV bundles;
- read-only MT5 historical acquisition through existing `MT5Reader`;
- exact-count history validation;
- historical M5 median-spread derivation or explicit override;
- acquisition → bundle export path;
- metrics/StrategyMemory/research episodes;
- discovery/invention/promotion governance.

### FROZEN RESEARCH/EVIDENCE PRINCIPLES

- no future leakage;
- no autonomous production promotion/hard-safety bypass;
- development context is not validation evidence;
- walk-forward does not consume final holdout;
- serious evidence identifies code/policy/content-addressed dataset/config/realism/limitations;
- mutable filename alone is insufficient;
- bundle/evidence output contains no financial-authority secrets;
- portable dataset trusted only after integrity/content verification;
- existing research bundle destinations are never silently overwritten;
- research MT5 acquisition reuses `MT5Reader`, never a second raw MetaTrader5 client;
- requested historical sample size is exact: partial history is failure, not a smaller silent experiment;
- absent historical spread is explicit and requires override rather than hidden zero/current-live substitution.

### SOFTWARE GAP NOW CLOSED

The generic “build an MT5 historical acquisition adapter” item is closed. `research/acquisition.py` exists and deterministic CI verifies its contract.

### STILL PENDING — REAL EXTERNAL EVIDENCE

- controlled Windows/MT5 run against real XAUUSD/XAUUSDm history;
- source-label/source-version convention based on observed broker/history facts;
- maximum reliable history depth and any broker terminal limits;
- broad regime-diverse real datasets acquired and archived through the portable bundle contract;
- evidence-package directory/naming/publication convention;
- integration of real datasets with walk-forward/stress reports;
- historical PRE_CLOSE schedule integration.

### CALIBRATE

Real-data periods/sample sizes, walk-forward windows, stress severity, promotion thresholds, StrategyMemory influence, discovery recipe/similarity thresholds, Monte Carlo method and optional-confluence retention thresholds.

## Operator / dashboard

### IMPLEMENTED

Lightweight stdlib read-only renderer.

### PENDING

Authoritative runtime DTO, Discovery Health/candidate display, compact confluence display, live refresh/polish and Windows visual verification.

## Engineering / release required before VERIFIED

- final persistent runtime orchestration;
- controlled MT5 DEMO certification;
- broad reproducible real-data evidence;
- production shared controller/fencing proof;
- scheduled PRE_CLOSE/reopen proof;
- restart/reconciliation + fresh-machine recovery;
- financial-secret scan;
- final coding/release audit.

## Governance conclusion

No major behavioural `FIX BEFORE BUILD` item is known. Current work is now predominantly **evidence packaging, real external data/integration, runtime integration and controlled certification**, not redesign.
