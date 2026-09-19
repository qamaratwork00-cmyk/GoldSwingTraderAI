# GoldSwingTraderAI — Testing and Verification

**Status:** CANDIDATE FOR ADOPTION  
**Version:** 0.1-evidence-contract  
**Authority:** Test layers, evidence quality and release proof

## 1. What a passing test means

A passing test proves only the behaviour that the test exercises. It does not
prove that MT5 is connected, that XAUUSD prices are current, that an external
provider is operating, or that a Windows DEMO broker run succeeded.

The project therefore uses an evidence ladder. Every completion statement must
name the highest rung actually demonstrated.

## 2. Evidence ladder

~~~mermaid
flowchart TB
    UNIT["Unit and contract tests"] --> INTEGRATION["Composed local integration"]
    INTEGRATION --> REPLAY["Deterministic historical replay"]
    REPLAY --> PAPER["Read-only live / paper observation"]
    PAPER --> DEMO["Real DEMO broker write drill"]
    DEMO --> RECOVERY["Fresh-machine restore and failover"]
    RECOVERY --> RELEASE["Release certification"]
~~~

| Rung | Proves | Does not prove |
|---|---|---|
| Unit/contract | Pure rules and typed boundaries | Real broker behaviour |
| Composed local integration | Adapters cooperate in a controlled process | Real network/terminal timing |
| Historical replay | No-lookahead logic and deterministic outcomes on a known dataset | Future performance |
| Read-only live observation | Current feed, identity and dashboard behaviour | Broker writes |
| DEMO write drill | Real DEMO order lifecycle under documented conditions | Production authorization |
| Restore/failover | Operational continuity, fencing and reconciliation | Universal broker compatibility |
| Release certification | The declared release scope was evidenced | Claims outside that scope |

## 3. Controlled evidence boundary

The following statements are intentionally different:

- “The deterministic test suite passes.”
- “The runtime starts in READINESS.”
- “The runtime remains alive while market data is stale.”
- “The runtime reached READY on fresh data.”
- “The broker writer performed a DEMO OPEN, MODIFY and CLOSE.”
- “A restart reconciled the broker truth.”
- “A second machine could not write while the primary lease was valid.”

Never replace the last four statements with the first one. A release report
must record command, environment, timestamp, configuration class, dataset or
broker account, result and retained evidence.

## 4. Test layers

### 4.1 Pure domain tests

These cover stable vocabularies, IDs, models, chronology and mathematical
invariants. They should be fast, deterministic and independent of MT5.

Primary files:

- tests/test_models.py
- tests/test_ids.py
- tests/test_coding_contract_regressions.py

### 4.2 Market and intelligence tests

These cover closed-candle chronology, freshness, structure, technical
location, liquidity, indicators, session and news semantics.

Primary files:

- tests/test_market_data.py
- tests/test_intelligence_core.py
- tests/test_intelligence_snapshot.py
- tests/test_technical_liquidity.py
- tests/test_technical_confluence.py
- tests/test_session_news_permissions.py

### 4.3 Decision and risk tests

These cover independent BUY/SELL theses, fusion, timing, Trade Plan geometry,
risk sizing, affordability, risk-day locks and session/news permission.

Primary files:

- tests/test_strategy_decisions.py
- tests/test_trade_plan_risk.py
- tests/test_risk_state_regressions.py
- tests/test_margin_authority.py
- tests/test_small_account_profile.py

### 4.4 Execution and recovery tests

These cover DEMO Guard, fresh spread/drift checks, Intent one-shot behaviour,
reconciliation, controller fencing, SQLite coordination, restart state and
MT5 recovery truth.

Primary files:

- tests/test_execution_safety.py
- tests/test_sqlite_coordination.py
- tests/test_persistence_recovery.py
- tests/test_runtime_checkpoint.py
- tests/test_startup_recovery.py
- tests/test_recovery_mt5.py

### 4.5 Management and runtime tests

These cover Trade Manager actions, verified management writes, dashboard
mapping, readiness startup and the persistent loop.

Primary files:

- tests/test_trade_manager.py
- tests/test_management_execution.py
- tests/test_app_readiness.py
- tests/test_live_startup_runtime.py
- tests/test_runtime_loop.py
- tests/test_dashboard.py

### 4.6 Research and governance tests

These cover dataset identity, replay, outcomes, stress, walk-forward,
evidence packages, discovery, invention and promotion.

Primary files:

- tests/test_research_datasets.py
- tests/test_research_acquisition.py
- tests/test_research_validation.py
- tests/test_research_stress.py
- tests/test_research_outcomes.py
- tests/test_research_ablation.py
- tests/test_research_evidence.py
- tests/test_research_packages.py
- tests/test_research_session_history.py
- tests/test_management_replay.py
- tests/test_discovery_invention.py
- tests/test_discovery_journal.py
- tests/test_promotion_governance.py

### 4.7 Operational scripts and security tests

These cover restore, public backup staging, secret scanning, documentation
contracts and the walk-forward command boundary.

Primary files:

- tests/test_operator_scripts.py
- tests/test_backup_catalog.py
- tests/test_secret_scanner.py
- tests/test_documentation_contract.py
- tests/test_walk_forward_script.py

## 5. Determinism requirements

Tests must control time, randomness, external facts and filesystem paths when
those values affect the result. A replay test must identify:

- dataset fingerprint;
- code/config fingerprint;
- timezone and calendar assumptions;
- completed-candle boundary;
- spread/slippage model;
- starting account and position state;
- expected output or invariant.

If a test depends on the current wall clock or a live provider, it belongs in
an explicitly marked integration/evidence layer, not in the deterministic core.

## 6. Safety properties to test explicitly

The suite must retain negative tests for:

- non-DEMO account or mismatched identity;
- missing symbol or MT5 initialization;
- stale, sparse, corrupt or insufficient market data;
- forming-candle lookahead;
- M1 attempting to create a Swing trade;
- unknown position ownership;
- external Gold exposure;
- insufficient margin or unaffordable minimum lot;
- spread and price drift violations;
- news blackout and unknown news safety;
- pre-close flatten conditions;
- duplicate Intent retry after uncertain acknowledgement;
- stale controller epoch or missing lease;
- corrupt local state;
- secret leakage in logs, backups or staged public artifacts.

Positive tests are not enough. Safety is defined by what the system refuses.

## 7. Runtime verification sequence

~~~mermaid
sequenceDiagram
    participant DEV as Developer
    participant TEST as Test suite
    participant APP as Runtime
    participant MT5 as DEMO terminal
    participant EVID as Evidence package
    DEV->>TEST: run deterministic suite
    TEST-->>DEV: pass/fail with exact command
    DEV->>APP: start in READINESS
    APP->>MT5: initialize and read truth
    MT5-->>APP: identity, quote, candles and positions
    APP-->>DEV: dashboard and structured logs
    DEV->>APP: exercise controlled transition
    APP->>MT5: perform only approved DEMO operation
    MT5-->>APP: broker result
    APP->>EVID: retain logs, IDs and reconciliation proof
~~~

The DEMO sequence must be performed only after the deterministic and local
integration layers pass. It must use a small, explicitly approved DEMO scope.

## 8. Test command policy

The normal local gate is:

~~~text
python -m pytest -q
python -m ruff check src tests scripts
~~~

The exact environment, Python version, package installation command and
configuration must be recorded with release evidence. A local pass from a
different commit is not evidence for the current commit.

## 9. Verification report minimum

Every verification report should contain:

| Field | Required content |
|---|---|
| Revision | Git commit or immutable source identity |
| Environment | OS, Python, package and MT5 terminal details where relevant |
| Scope | Test layer or broker/research drill |
| Command | Exact command executed |
| Result | PASS, FAIL, BLOCKED or NOT RUN |
| Observations | Important warnings, stale data or manual steps |
| Evidence | Log, JSON, checkpoint, screenshot or broker ticket reference |
| Reviewer | Person who accepted the result |
| Boundary | What the result explicitly does not prove |

## 10. Source and proof map

| Concern | Implementation | Proof |
|---|---|---|
| Test configuration | pyproject.toml | test run evidence |
| Documentation contract | scripts/verify_documentation.py | tests/test_documentation_contract.py |
| Runtime loop | app/loop.py and app/cycle.py | tests/test_runtime_loop.py |
| Dashboard proof | app/dashboard.py and operator/dashboard.py | tests/test_dashboard.py |
| Broker safety | execution package | tests/test_execution_safety.py |
| Research proof | research package and scripts/run_walk_forward.py | research test files and evidence package |

## 11. Completion rule

“Complete” is a scoped statement. The project may be complete for deterministic
core behaviour while remaining incomplete for live DEMO certification. The
release audit must never promote a lower evidence rung into a higher one.
