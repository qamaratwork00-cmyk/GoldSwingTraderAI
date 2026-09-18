# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 1.8-implementation-map  
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
→ market_data → MarketSnapshot
→ intelligence → IntelligenceSnapshot
→ strategies → StrategyFloorReport
→ decisions → DecisionSnapshot / TradePlan
→ risk → monetary + hard session/news authority
→ persistence → durable critical state
→ execution → gate / intent / broker write / reconciliation
→ management → open-trade decision floor
→ operator → read-only presentation

historical dataset
→ replay / ablation / outcomes / management replay
→ declared stress
→ fixed-policy walk-forward
→ dataset + evidence identity
→ metrics / learning / episode journal
→ discovery / invention
→ governed promotion
```

The execution package remains the only package allowed to contain irreversible raw MT5 writes.

## Ownership highlights

### `market_data/`
Read-only broker/account/symbol/quote/completed-candle boundary.

### `intelligence/`
Shared causal structure/quant/technical/liquidity/session/news facts. `intelligence/confluence.py` owns causal Trendline/Fibonacci/POC facts. No broker authority.

### `strategies/` + `decisions/`
Parallel strategy families, BUY/SELL fusion, Opportunity/Entry Timing and structural Trade Plan. Confluence is bounded positive-only.

### `risk/`
Monetary sizing/profile/min-lot/capacity plus daily/cooldown/episode and hard session/news permission.

### `persistence/`
Standard-library SQLite with canonical JSON/checksums/schema versions/transactions. Corrupt critical state never silently becomes default.

### `execution/`
Single raw broker-write authority:

```text
hard authorities
→ ExecutionPermission
→ durable ExecutionIntent
→ order_check
→ fresh lease/fencing
→ persist SUBMITTING
→ one order_send only
→ reconciliation
```

### `management/`
Second decision floor for verified bot-owned trades: HOLD/PROTECT/TRAIL/RUNNER/EXIT. No raw MT5 writes.

### `operator/`
Read-only presentation. UI cannot recompute strategy/risk/execution authority.

### `research/replay.py`
Chronological prefix-only `BAR_CLOSE` production Decision replay.

### `research/ablation.py`
Controlled same-chronology analytical/outcome/manager variant comparison.

### `research/outcomes.py`
Historical production Trade Plan reconstruction plus ambiguity-safe initial bracket outcomes.

### `research/management_replay.py`
Chronological production Trade Manager replay with optional declared adverse fill/spread/modify assumptions. Active barriers are checked before new management decisions.

### `research/stress.py`
Fixed-analytical-run execution-friction scenarios. Calibration evidence only; no production safety mutation.

### `research/validation.py`
`FIXED_POLICY_WALK_FORWARD`: development context followed by non-overlapping scored validation; no tuning; outcome data clipped at validation boundary; no final-holdout authority.

### `research/evidence.py`
Primary owner of research dataset/evidence reproducibility identity.

Responsibilities:

```text
ReplayDataset
→ canonical source/version + symbol/account-context + candle facts
→ per-timeframe SHA-256 identities
→ dataset_sha256

experiment inputs
+ code revision
+ policy version
+ dataset identity
→ input_fingerprint_sha256

inputs + generated time + results + limitations
→ manifest_sha256
→ canonical public JSON representation
```

Rules:

- timeframe ordering is normalized before hashing;
- candle OHLC/volume/spread fields are content-addressed;
- source label/version, replay spread/realism and symbol geometry participate in identity;
- economic replay account context participates; broker endpoint `login/server` do not;
- manifest configuration/results are normalized deterministically;
- financial-secret-shaped fields are rejected with `FINANCIAL_SECRET_DETECTED`;
- evidence identity has no broker, risk, strategy-selection or promotion authority.

### `research/metrics.py`
Actual/counterfactual metric separation and Opportunity Recall.

### `research/learning.py`
Bounded/context-isolated StrategyMemory.

### `research/episode_journal.py`
Durable research episodes and approved primitive mapping.

### `research/discovery.py` / `invention.py`
Declarative candidate/rejected-memory ownership and candidate-or-suppression liveness. No arbitrary Python/broker authority.

### `research/promotion.py`
Governed stage order, locked fingerprint, one-shot final holdout, Shadow/Canary chronology, explicit promotion approval and rollback.

## Runtime / research efficiency

```text
live:
verified snapshot → shared intelligence → strategies → decision → TradePlan
→ risk/permissions → execution → manager → dashboard

research:
dataset → replay/outcomes/manager → stress/walk-forward
→ dataset/evidence identity → metrics/learning/discovery
```

## Prohibited dependency directions

```text
intelligence → order_send                       NO
strategies   → order_send/risk reset            NO
decisions    → raw order_send                   NO
risk         → raw order_send                   NO
management   → raw order_send                   NO
operator     → MT5/risk/gate authority          NO
research     → production broker write          NO
invention    → arbitrary Python/eval/exec       NO
candidate    → hard-risk/safety mutation        NO
candidate    → self-promotion                   NO
outcomes     → historical-decision mutation     NO
stress       → production safety mutation       NO
validation   → hidden tuning/final holdout       NO
evidence     → trading/promotion authority      NO
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
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Current verified checkpoint: **168 tests PASS**, Ruff PASS and financial-secret scan PASS.

Coverage now includes no-lookahead, confluence causality, ambiguity-safe outcomes, production-manager reuse, stress assumptions, walk-forward validation boundaries, deterministic dataset identity, evidence input/full-record hashing and manifest secret-field rejection.

## Remaining Phase-10 work

- real historical XAU dataset ingestion/export around the identity contract;
- persisted/reproducible evidence package output;
- broad regime-diverse real-data walk-forward/independent validation;
- empirical stress calibration from historical/DEMO observations;
- historical PRE_CLOSE/session-policy integration;
- final untouched holdout evidence for locked candidates;
- richer replay-versus-DEMO attribution and operator visibility.

## Phase completion rule

At each coherent implementation checkpoint, update this map plus `docs/CODER_GUIDE.md`, the authoritative topic doc, testing contract and open-question ledger before moving on.
