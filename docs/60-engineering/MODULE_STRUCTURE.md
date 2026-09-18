# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 2.0-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — implemented through Phase 10 research foundation

```text
src/goldswingtraderai/
├── app/
├── config/
├── diagnostics/
├── domain/
├── market_data/
├── intelligence/
├── strategies/
├── decisions/
├── risk/
├── persistence/
├── execution/
├── management/
├── operator/
└── research/
    ├── replay.py
    ├── ablation.py
    ├── outcomes.py
    ├── management_replay.py
    ├── stress.py
    ├── validation.py
    ├── evidence.py
    ├── datasets.py
    ├── acquisition.py
    ├── metrics.py
    ├── learning.py
    ├── episode_journal.py
    ├── discovery.py
    ├── invention.py
    └── promotion.py
```

Detailed file ownership remains in `docs/CODER_GUIDE.md`.

## Dependency direction

```text
config/domain
→ market_data → MarketSnapshot / read-only MT5 facts
→ intelligence → IntelligenceSnapshot
→ strategies → StrategyFloorReport
→ decisions → DecisionSnapshot / TradePlan
→ risk → monetary + hard session/news authority
→ persistence → durable critical state
→ execution → gate / intent / broker write / reconciliation
→ management → open-trade decision floor
→ operator → read-only presentation

MT5Reader or external historical source
→ research acquisition / portable dataset bundle / dataset identity
→ replay / ablation / outcomes / management replay
→ declared stress / fixed-policy walk-forward
→ evidence manifest
→ metrics / learning / episode journal
→ discovery / invention / governed promotion
```

The execution package remains the only package allowed to contain irreversible raw MT5 writes.

## Ownership highlights

### `market_data/`
Read-only broker/account/symbol/quote/completed-candle boundary. `MT5Reader.completed_candles()` excludes forming MT5 bar position 0 and is reused by research acquisition.

### `intelligence/`
Shared causal structure/quant/technical/liquidity/session/news facts. Trendline/Fibonacci/POC facts are soft confluence only.

### `strategies/` + `decisions/`
Parallel strategy families, BUY/SELL fusion, Opportunity/Entry Timing and structural Trade Plan. Confluence is bounded positive-only.

### `risk/`
Monetary sizing/profile/min-lot/capacity plus daily/cooldown/episode and hard session/news permission.

### `persistence/`
Standard-library SQLite with canonical JSON/checksums/schema versions/transactions. Corrupt critical state never silently becomes default.

### `execution/`
Single raw broker-write authority.

### `management/`
Second decision floor for verified bot-owned trades: HOLD/PROTECT/TRAIL/RUNNER/EXIT. No raw MT5 writes.

### `operator/`
Read-only presentation. UI cannot recompute strategy/risk/execution authority.

### `research/replay.py`
Chronological prefix-only `BAR_CLOSE` production Decision replay.

### `research/ablation.py`
Controlled same-chronology analytical/outcome/manager comparison.

### `research/outcomes.py`
Historical production Trade Plan reconstruction plus ambiguity-safe initial bracket outcomes.

### `research/management_replay.py`
Chronological production Trade Manager replay with optional declared adverse fill/spread/modify assumptions.

### `research/stress.py`
Fixed-analytical-run execution-friction scenarios; no production safety mutation.

### `research/validation.py`
Fixed-policy walk-forward with non-overlapping scored validation, no hidden tuning and no final-holdout authority.

### `research/evidence.py`
Dataset/evidence content identity and canonical manifest hashing.

### `research/datasets.py`
Portable offline `ReplayDataset` bundle owner. Manifest/file hashes and recomputed dataset identity are verified before use. Broker login/server are excluded.

### `research/acquisition.py`
Read-only historical acquisition owner. It **depends on `market_data/MT5Reader`** rather than wrapping MetaTrader5 again.

```text
HistoricalAcquisitionRequest
→ MT5Reader.resolve_symbol()
→ MT5Reader.account_facts() / symbol_spec()
→ MT5Reader.completed_candles() for every requested timeframe
→ exact-count validation
→ spread provenance resolution
→ ReplayDataset
→ optional research/datasets.py export
```

Rules:

- H4/H1/M15/M5 requested counts required; optional M1 supported by ordinary Timeframe contract;
- no partial-history acceptance when actual bars are fewer than declared;
- historical replay spread defaults to median positive M5 `spread_points * point`;
- absent historical spread requires explicit non-negative override;
- live current spread is not used as hidden historical fallback;
- source label/version are explicit provenance supplied by caller;
- no broker writes, no execution permission, no promotion authority.

### `research/metrics.py`
Actual/counterfactual metric separation and Opportunity Recall.

### `research/learning.py`
Bounded/context-isolated StrategyMemory.

### `research/episode_journal.py`
Durable research episodes and approved primitive mapping.

### `research/discovery.py` / `invention.py`
Declarative candidate/rejected-memory ownership and candidate-or-suppression liveness.

### `research/promotion.py`
Governed stage order, locked fingerprint, one-shot final holdout, Shadow/Canary chronology, explicit promotion approval and rollback.

## Prohibited dependency directions

```text
intelligence → order_send                       NO
strategies   → order_send/risk reset            NO
decisions    → raw order_send                   NO
risk         → raw order_send                   NO
management   → raw order_send                   NO
operator     → MT5/risk/gate authority          NO
research     → production broker write          NO
acquisition  → raw MetaTrader5 duplicate client NO
acquisition  → execution/promotion authority    NO
invention    → arbitrary Python/eval/exec       NO
candidate    → hard-risk/safety mutation        NO
candidate    → self-promotion                   NO
outcomes     → historical-decision mutation     NO
stress       → production safety mutation       NO
validation   → hidden tuning/final holdout       NO
evidence     → trading/promotion authority      NO
datasets     → broker credentials/authority     NO
```

## Current deterministic tests

Later-phase suites include:

```text
tests/test_management_replay.py
tests/test_research_ablation.py
tests/test_research_outcomes.py
tests/test_research_stress.py
tests/test_research_validation.py
tests/test_research_evidence.py
tests/test_research_datasets.py
tests/test_research_acquisition.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Current verified checkpoint: **178 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Remaining Phase-10 work

- controlled Windows/MT5 real-history acquisition evidence and source/version convention;
- persisted result/evidence package layout beside immutable dataset identities;
- broad regime-diverse real-data walk-forward/independent validation;
- empirical stress calibration;
- historical PRE_CLOSE/session-policy integration;
- final untouched holdout evidence;
- replay-versus-DEMO attribution and operator visibility.

## Phase completion rule

At each coherent implementation checkpoint, update this map plus `docs/CODER_GUIDE.md`, the authoritative topic doc, testing contract and open-question ledger before moving on.
