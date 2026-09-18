# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 1.3-implementation-map  
**Authority:** File/module ownership map and dependency direction. It does **not** redefine trading behaviour.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`

## Core engineering rule

> **One primary owner per responsibility; facts flow forward; irreversible broker authority stays narrow and last.**

## Current package shape — implemented through Phase 10 foundation

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

production/replay facts + outcomes
→ research metrics/episode journal
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

`strategies/confluence.py` is deliberately **positive-only**: it can add a small capped uplift when Trendline/Fib/POC context supports an existing family, but it cannot lower the base family score or require any confluence feature to exist.

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
   → structure/quant/technical/liquidity
   → optional Trendline/Fib/POC confluence
→ parallel strategies
→ bounded positive-only confluence uplift
→ one decision/timing derivation
→ one TradePlan
→ one RiskEvaluation + hard permission set
→ one centralized execution path if needed
→ one Trade Manager cycle
→ one presentation frame

then asynchronously/offline as appropriate:
outcomes
→ one durable research episode
→ bounded discovery cycle
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
invention    → arbitrary Python/eval/exec        NO
candidate    → hard-risk/safety mutation         NO
candidate    → self-promotion                    NO
confluence   → hard execution permission         NO
```

## Current deterministic tests

Later-phase coverage includes:

```text
tests/test_technical_confluence.py
tests/test_execution_safety.py
tests/test_trade_manager.py
tests/test_management_execution.py
tests/test_dashboard.py
tests/test_discovery_invention.py
tests/test_discovery_journal.py
tests/test_promotion_governance.py
```

Alongside earlier suites these protect no-lookahead, non-restrictive strategy fusion, positive-only technical confluence, risk/session/execution safety, restart integrity, one-shot broker writes, structural management, dashboard isolation and working discovery/invention liveness.

CI gates remain Ruff, Pytest and financial-secret scan. Deterministic CI is software evidence, not live DEMO certification or proof of strategy edge.

## Remaining Phase-10 work

- broader replay and live/replay parity tests;
- stress/fault/ablation evidence utilities;
- richer entry/exit attribution and research reports;
- operator visibility for Discovery Health/candidate stage and compact Trendline/Fib/POC context;
- calibration of research/confluence thresholds on real historical/DEMO evidence.

## Phase completion rule

At each phase exit, record actual files/dependencies/tests here and in `docs/CODER_GUIDE.md`. Behavioural thresholds remain owned by authoritative topic documents.
