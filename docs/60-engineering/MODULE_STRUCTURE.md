# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 1.6-implementation-map  
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
│   ├── indicators.py
│   ├── candle_structure.py
│   ├── technical.py
│   ├── liquidity.py
│   ├── session.py
│   ├── news.py
│   ├── confluence.py
│   └── snapshot.py
├── strategies/
│   ├── floor.py
│   └── confluence.py
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
→ initial bracket / chronological Trade Manager outcome modeling
→ declared execution-friction stress
→ metrics / episode journal
→ discovery/invention candidates
→ governed promotion evidence
```

The execution package remains the only package allowed to contain irreversible raw MT5 writes.

## Ownership highlights

### `market_data/`
Read-only broker/account/symbol/quote/completed-candle boundary.

### `intelligence/`
Shared causal structure/quant/technical/liquidity/session/news facts. No broker authority.

`intelligence/confluence.py` owns:
- confirmed-swing trendline projection and touch/break/reclaim facts;
- causal Fibonacci retracement/extension geometry;
- broker-local volume-profile POC with explicit real-volume versus tick-volume source.

These are soft confluence facts only. Missing or opposing confluence must not become a universal trade blocker.

### `strategies/` + `decisions/`
Parallel strategy families, BUY/SELL fusion, Opportunity/Entry Timing and structural Trade Plan. Soft evidence remains separate from hard safety.

`strategies/confluence.py` is deliberately **positive-only**. Production defaults enable Trendline/Fibonacci/POC support; typed source toggles are research-ablation controls and cannot create penalties or hard permission.

Trendline behaviour naturally supports existing pullback, breakout, retest and compression families. A separate seventh family is not created unless governed research later proves a materially distinct edge.

### `risk/`
Monetary sizing/profile/min-lot/capacity plus daily/cooldown/episode state and hard session/news permission. SMALL includes any positive day-start equity below `$300`.

### `persistence/`
Standard-library SQLite with canonical JSON, checksums, schema versions, transactions and event rows. Corrupt critical state never silently becomes empty/default.

### `execution/`
Single raw irreversible broker-write authority.

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

A success-like ACK still requires broker-truth verification. The in-memory coordination backend is tests only; production cross-laptop shared coordination remains required before failover certification.

### `management/`
Second decision floor for verified bot-owned open trades. HOLD/PROTECT/TRAIL/RUNNER/EXIT. Management can create governed ExecutionIntents but cannot call raw MT5.

### `operator/`
Read-only stdlib presentation over flattened authoritative facts. UI must not recompute strategy/risk/execution permission.

### `research/replay.py`
Chronological prefix-only bar-close replay. It reuses production Intelligence + Decision semantics and explicitly declares `BAR_CLOSE` realism instead of pretending tick-perfect execution.

### `research/ablation.py`
Runs controlled same-chronology research variants without creating a second strategy implementation.

Current confluence variants are:

```text
BASE
TRENDLINE
FIBONACCI
DIRECTIONAL_COMBINED
ALL
```

It supports three evidence layers:

1. decision-level Opportunity/ENTER/WAIT/MISSED/frequency/score/conflict deltas;
2. initial Trade Plan bracket evidence from `research/outcomes.py`;
3. production Trade Manager evidence from `research/management_replay.py`.

Every layer exposes signed deltas versus BASE. Decision-only evidence never invents P/L.

### `research/outcomes.py`
Owns historical production Trade Plan reconstruction and initial bracket path labeling for analytical ENTER events.

It rebuilds Trade Plan geometry from the historical decision-time snapshot, then inspects only later M5 candles. Vocabulary:

```text
TARGET_FIRST
STOP_FIRST
BOTH_TOUCHED_AMBIGUOUS
HORIZON_UNRESOLVED
```

Same-bar stop+target ordering is never guessed favorably. Ambiguous/unresolved cases remain outside resolved bracket Net R and are exposed through coverage.

### `research/management_replay.py`
Owns chronological replay of the **production Trade Manager** plus declared research-only execution assumptions.

Default flow:

```text
create research ManagedTrade
→ check currently active stop/TP against next M5
→ if trade survives, complete bar
→ rebuild chronological IntelligenceSnapshot
→ call production evaluate_trade_manager()
→ record HOLD / PROTECT / TRAIL / RUNNER / EXIT
→ apply verified-style state transition for following bar
```

The default remains `BAR_CLOSE_IDEALIZED`. Optional `ManagementReplayAssumptions` add bounded stress without changing production management logic:

- adverse fill measured in immutable original-R units;
- executable-side Bid/Ask barrier approximation from a declared spread;
- completed-M5 manager-modify delay;
- deterministic every-Nth manager-modify rejection.

While a synthetic modify is pending, later modify submissions are suppressed until it resolves. This mirrors the production rule that ambiguous lifecycle state must reconcile before another irreversible write. Structural stop/target geometry and original R are never rewritten merely to hide adverse slippage.

Same-bar active stop+TP remains ambiguous. Open/ambiguous cases do not enter resolved management Net R.

### `research/stress.py`
Owns deterministic execution-friction scenario orchestration around a **fixed analytical ReplayRun**.

It changes only declared Trade Plan / fill / exit-side spread / manager-write assumptions and compares signed metrics versus BASE. Default V1 research probes are 1.50x spread, 0.10R adverse entry, one-M5 modify delay, every-second modify rejection and a combined scenario.

Those values are transparent calibration probes, not frozen production thresholds or historical broker claims. `stress.py` has no broker-write authority and does not simulate the complete Execution Permission Gate, margin, order book, variable intrabar spread or tick ordering.

### `research/metrics.py`
Owns actual trade/outcome metrics and Opportunity Recall. Counterfactual blocked/missed MFE is isolated from actual broker P/L.

### `research/learning.py`
Owns interpretable StrategyMemory summaries and bounded score nudges. Evidence is isolated by family/direction/regime/session/environment/policy version.

### `research/episode_journal.py`
Durable automatic feed from outcome-labelled episodes into discovery observations. It maps existing audited strategy-evidence labels to the approved primitive registry and infers research triggers such as missed move, false entry or premature exit.

### `research/discovery.py`
Owns approved primitives, declarative candidate recipes, independent-episode requirements, variant/new-family classification, fingerprints/similarity, duplicate/rejected memory and durable CandidateRegistry.

It has no arbitrary-code or broker authority.

### `research/invention.py`
Owns the automatic recurring-cluster cycle and `IDLE / HEALTHY / DEGRADED` discovery-health result.

Engineering liveness invariant:

```text
eligible evidence
→ candidate created
OR explicit governed suppression reason
```

Silent eligible-evidence loss is a defect.

### `research/promotion.py`
Owns the durable post-discovery challenger lifecycle. It enforces stage order, locked fingerprint, one-shot final holdout, Shadow/Canary chronology, explicit promotion approval and rollback history.

The registry's `broker_authority` remains false even at DEMO Canary/Promoted state; actual execution authority can only come from the normal runtime gate.

## Runtime / research efficiency rule

```text
one verified broker snapshot
→ one shared intelligence derivation
→ parallel strategies
→ bounded positive-only confluence uplift
→ one decision/timing derivation
→ one TradePlan
→ one RiskEvaluation + hard permission set
→ one centralized execution path if needed
→ one Trade Manager cycle
→ one presentation frame

historical research:
one dataset / chronology
→ production Decision semantics
→ shared historical Trade Plan reconstruction
→ initial bracket and/or production Trade Manager replay
→ optional declared execution stress
→ controlled variant comparison
→ metrics / learning / discovery
```

Research should not rerun expensive analysis merely to reconstruct facts already durably captured unless chronological replay specifically requires it.

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
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Current verified stress-research checkpoint includes **159 passing tests**, Ruff PASS and financial-secret scan PASS.

Alongside earlier suites these protect no-lookahead, non-restrictive strategy fusion, positive-only technical confluence, same-chronology ablation, ambiguity-safe outcome labeling, chronological production-manager reuse, immutable-R adverse-fill accounting, executable-side spread approximation, explicit stress scenarios, risk/session/execution safety, restart integrity, one-shot broker writes, dashboard isolation and discovery/invention liveness.

Deterministic CI is software evidence, not live DEMO certification or proof of strategy edge.

## Remaining Phase-10 work

- calibrate stress assumptions with broader historical XAU and controlled DEMO evidence;
- historical PRE_CLOSE/session-policy integration where trustworthy schedule history exists;
- broader real historical XAU replay datasets and regime coverage;
- walk-forward and independent-validation evidence;
- final untouched holdout evidence for locked candidates;
- richer entry/exit attribution and controlled replay-versus-DEMO comparison;
- operator visibility for Discovery Health/candidate stage and compact Trendline/Fib/POC context;
- calibration of research/confluence/management thresholds on real historical/DEMO evidence.

## Phase completion rule

At each phase exit, record actual files/dependencies/tests here and in `docs/CODER_GUIDE.md`. Behavioural thresholds remain owned by authoritative topic documents.
