# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 1.7-implementation-map  
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
│   └── dashboard.py
└── research/
    ├── replay.py
    ├── ablation.py
    ├── outcomes.py
    ├── management_replay.py
    ├── stress.py
    ├── validation.py
    ├── metrics.py
    ├── learning.py
    ├── episode_journal.py
    ├── discovery.py
    ├── invention.py
    └── promotion.py
```

Detailed file ownership remains in `docs/CODER_GUIDE.md`; this document focuses on dependency boundaries.

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
→ research replay
→ controlled ablation
→ historical Trade Plan reconstruction
→ bracket / chronological Trade Manager outcome modeling
→ declared execution-friction stress
→ fixed-policy walk-forward validation
→ metrics / episode journal
→ discovery/invention candidates
→ governed promotion evidence
```

The execution package remains the only package allowed to contain irreversible raw MT5 writes.

## Ownership highlights

### `market_data/`
Read-only broker/account/symbol/quote/completed-candle boundary.

### `intelligence/`
Shared causal structure/quant/technical/liquidity/session/news facts. `intelligence/confluence.py` owns confirmed-swing Trendlines, causal Fibonacci geometry and broker-local Volume Profile/POC. These are soft facts only; no broker authority.

### `strategies/` + `decisions/`
Parallel strategy families, BUY/SELL fusion, Opportunity/Entry Timing and structural Trade Plan. `strategies/confluence.py` is positive-only; production defaults enable Trendline/Fibonacci/POC and research toggles cannot become hard permission.

### `risk/`
Monetary sizing/profile/min-lot/capacity plus daily/cooldown/episode state and hard session/news permission. SMALL includes any positive day-start equity below `$300`.

### `persistence/`
Standard-library SQLite with canonical JSON, checksums, schema versions, transactions and event rows. Corrupt critical state never silently becomes empty/default.

### `execution/`
Single raw irreversible broker-write authority:

```text
hard authorities
→ ExecutionPermission
→ durable ExecutionIntent
→ order_check
→ fresh lease/fencing
→ persist SUBMITTING
→ one order_send only
→ broker reconciliation
```

A success-like ACK still requires broker-truth verification. In-memory coordination is tests only; production cross-laptop shared coordination remains required before failover certification.

### `management/`
Second decision floor for verified bot-owned open trades. HOLD/PROTECT/TRAIL/RUNNER/EXIT. It can create governed ExecutionIntents but cannot call raw MT5.

### `operator/`
Read-only stdlib presentation over flattened authoritative facts. UI must not recompute strategy/risk/execution permission.

### `research/replay.py`
Chronological prefix-only bar-close replay reusing production Intelligence + Decision semantics. Explicit `BAR_CLOSE` realism.

### `research/ablation.py`
Controlled same-chronology variants without a second strategy implementation. Supports decision, initial-bracket and manager evidence layers. Decision-only evidence never invents P/L.

### `research/outcomes.py`
Historical production Trade Plan reconstruction plus ambiguity-safe `TARGET_FIRST / STOP_FIRST / BOTH_TOUCHED_AMBIGUOUS / HORIZON_UNRESOLVED` path labeling.

### `research/management_replay.py`
Chronological production Trade Manager replay. Active stop/TP is checked before each new manager action. Optional declared assumptions model adverse fill, executable-side spread, completed-M5 modify delay and deterministic modify rejection without rewriting structural geometry or original R.

### `research/stress.py`
Deterministic execution-friction scenario orchestration around a fixed analytical `ReplayRun`. Default probes are 1.50x spread, 0.10R adverse entry, one-M5 modify delay, every-second modify rejection and combined stress. These are calibration probes, not frozen production thresholds or broker facts.

### `research/validation.py`
Owns fixed-policy chronological walk-forward validation.

```text
DEVELOPMENT CONTEXT
→ later non-overlapping VALIDATION SLICE
```

Responsibilities/invariants:

- build windows from historically eligible replay events;
- allow overlapping development context but never overlapping scored validation slices;
- run production Decision semantics from development start so Opportunity state is reconstructed causally;
- score only the validation slice;
- truncate every window's dataset at validation end so future windows cannot resolve earlier-window outcomes;
- optionally attach the declared execution-stress report to validation evidence;
- perform no parameter search/optimization;
- never consume the governed one-shot final holdout in `research/promotion.py`.

The implemented validation mode is `FIXED_POLICY_WALK_FORWARD`. Exact window sizes remain research calibration rather than code authority.

### `research/metrics.py`
Owns actual trade/outcome metrics and Opportunity Recall. Counterfactual blocked/missed MFE is isolated from actual broker P/L.

### `research/learning.py`
Owns interpretable StrategyMemory summaries and bounded score nudges. Evidence is isolated by family/direction/regime/session/environment/policy version.

### `research/episode_journal.py`
Durable automatic feed from outcome-labelled episodes into discovery observations and approved primitive mapping.

### `research/discovery.py`
Owns approved primitives, declarative candidate recipes, independent-episode requirements, fingerprints/similarity and durable CandidateRegistry. No arbitrary-code or broker authority.

### `research/invention.py`
Owns automatic recurring-cluster cycle and `IDLE / HEALTHY / DEGRADED` discovery health. Eligible evidence must create a candidate or explicit governed suppression reason.

### `research/promotion.py`
Owns durable challenger lifecycle: stage order, locked fingerprint, one-shot final holdout, Shadow/Canary chronology, explicit promotion approval and rollback. `broker_authority` remains false.

## Runtime / research efficiency rule

```text
live/runtime:
one verified broker snapshot
→ shared intelligence
→ parallel strategies
→ decision/timing
→ TradePlan
→ Risk + hard permissions
→ centralized execution if needed
→ Trade Manager
→ presentation

historical research:
one dataset / chronology
→ production Decision semantics
→ historical Trade Plan / management replay
→ optional declared stress
→ fixed-policy walk-forward slices
→ metrics / learning / discovery
```

Research should not rerun expensive analysis merely to reconstruct already durable facts unless chronological replay specifically requires it.

## Prohibited dependency directions

```text
intelligence → order_send                       NO
strategies   → order_send/risk reset            NO
decisions    → raw order_send                   NO
risk         → raw order_send                   NO
persistence  → trading decision                 NO
management   → raw order_send                   NO
operator     → MT5/risk/gate authority          NO
research     → production broker write          NO
invention    → arbitrary Python/eval/exec       NO
candidate    → hard-risk/safety mutation        NO
candidate    → self-promotion                   NO
confluence   → hard execution permission        NO
outcomes     → historical-decision mutation     NO
manager replay → raw broker execution           NO
stress model → production risk/safety mutation  NO
validation  → automatic tuning/final holdout     NO
```

## Current deterministic tests

Later-phase coverage includes:

```text
tests/test_technical_confluence.py
tests/test_execution_safety.py
tests/test_trade_manager.py
tests/test_management_execution.py
tests/test_management_replay.py
tests/test_dashboard.py
tests/test_research_ablation.py
tests/test_research_outcomes.py
tests/test_research_stress.py
tests/test_research_validation.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Current verified walk-forward checkpoint: **163 passing tests**, Ruff PASS and financial-secret scan PASS.

Alongside earlier suites these protect no-lookahead, positive-only confluence, ambiguity-safe outcomes, production-manager reuse, immutable-R stress accounting, explicit stress assumptions, fixed-policy walk-forward chronology, development/validation separation, validation-boundary clipping, risk/session/execution safety, restart integrity and discovery/promotion governance.

Deterministic CI is software evidence, not live DEMO certification or proof of strategy edge.

## Remaining Phase-10 work

- dataset identity/versioning and reproducible evidence-manifest tooling;
- broad real historical XAU replay datasets and regime coverage;
- sufficiently large walk-forward/independent-validation evidence;
- empirical stress calibration from historical/DEMO observations;
- historical PRE_CLOSE/session-policy integration where trustworthy history exists;
- final untouched holdout evidence for locked candidates;
- richer replay-versus-DEMO attribution;
- operator visibility for Discovery Health/candidate stage and compact confluence context.

## Phase completion rule

At each phase exit, record actual files/dependencies/tests here and in `docs/CODER_GUIDE.md`. Behavioural thresholds remain owned by authoritative topic documents.
