# GoldSwingTraderAI — Runtime Architecture

**Status:** PROVISIONAL
**Version:** 0.1-foundation
**Authority:** Runtime topology, dataflow, parallelism and ordered authority

## Purpose

This document is the map a developer should use before opening a source file.
It explains how the project runs from MT5 initialization to a persistent M5
cycle, how intelligence runs in parallel, where authority becomes ordered, how
readiness remains visible while the market is closed, and where recovery and
research sit.

## Whole-system topology

~~~mermaid
flowchart TB
    MODE["Explicit mode — READINESS / PRIMARY / STANDBY"] --> START["Startup composition"]
    START --> SNAP["Verified MarketSnapshot"]
    SNAP --> INTEL["Parallel intelligence desks"]
    INTEL --> FUSION["Strategies, BUY/SELL fusion and Entry Timing"]
    FUSION --> PLAN["Structural Trade Plan"]
    PLAN --> AUTH["Ordered hard authorities"]
    AUTH --> GATE["Execution Permission Gate"]
    GATE --> INTENT["Persist one-shot Intent"]
    INTENT --> WRITE["One governed MT5 request"]
    WRITE --> RECON["Verify broker truth"]
    RECON --> STORE["Persist lifecycle and render dashboard"]
    STORE --> MANAGE["Trade Manager and research evidence"]
~~~

Cross-cutting services—persistence, controller fencing, health and operator
rendering—observe or support the chain. They cannot create a second broker
authority.

## Logical parallelism versus ordered authority

“Parallel” means independent calculations use the same immutable inputs. It
does not require threads or async code.

| Lane | May do | Must not do |
|---|---|---|
| intelligence | compute structure, technical, liquidity, quant, session and news evidence | place orders or set monetary permission |
| strategy | evaluate six families and directional cases | read MT5, size risk or call the gate |
| BUY/SELL debate | expose support, opposition and conflict | hide the opposite thesis |
| risk/session/news | evaluate hard conditions in defined order | improve an analytical score |
| execution | enforce gate, Intent, controller, write and reconciliation | invent strategy direction |
| management | decide HOLD/PROTECT/TRAIL/RUNNER/EXIT | bypass the same write boundary |
| operator/research | display or evaluate evidence | gain production write authority |

~~~mermaid
flowchart TB
    SNAP["One immutable cycle snapshot"] --> A["Candle + technical + liquidity + quant + context"]
    SNAP --> B["Six strategy family evaluations"]
    SNAP --> C["Account, exposure and session/news facts"]
    A --> F["Fusion and timing"]
    B --> F
    C --> F
    F --> P["Trade Plan"]
    P --> H["Risk and hard permissions"]
    H --> G["Gate"]
    G --> W["Intent → MT5 writer → reconciliation"]
~~~

The code may evaluate A, B and C sequentially for deterministic Python
execution. They remain separate because none is allowed to mutate a shared
result or turn optional absence into an invisible veto.

## Startup and recovery graph

Startup is not a normal decision cycle. It must construct trustworthy owners
before the persistent loop can run.

~~~mermaid
flowchart TB
    MODE["Mode and state selection"] --> MT5["Initialize MT5Reader"]
    MT5 --> FACTS["Account, symbol, DEMO, quote, candles"]
    FACTS --> BROKER["MT5RecoveryTruth — current positions and tick tolerance"]
    BROKER --> LOCAL["EXISTING / INITIALIZE / RESTORE local state"]
    LOCAL --> OWNERS["Repositories, reconciler and controller"]
    OWNERS --> RECOVER["StartupRecoveryCoordinator"]
    RECOVER --> READY{"All authorities ready?"}
    READY -->|"no"| HOLD["RECONCILING or BLOCKED"]
    READY -->|"yes"| LOOP["PersistentRuntimeLoop"]
~~~

Restore never becomes broker truth. A restored ManagedTrade or Intent must be
compared with fresh MT5 positions/orders/deals before new writes.

## READINESS and stale-data wait

The default launcher is useful when the market is closed. It keeps the process
observable without inventing an analytical result:

~~~mermaid
flowchart TB
    READ["Read MT5 snapshot"] --> QUALITY{"Data quality"}
    QUALITY -->|"HEALTHY"| RESULT["Readiness result"]
    QUALITY -->|"STALE / INSUFFICIENT / SPARSE"| WAIT["Read-only wait"]
    WAIT --> POLL["Bounded poll; renew controller only in PRIMARY/STANDBY"]
    POLL --> READ
    QUALITY -->|"CORRUPT / identity / DEMO / persistence fault"| BLOCK["Fail closed"]
~~~

During READINESS:

- strategy, risk sizing, Intent creation and broker writes do not run;
- the readiness renderer shows symbol, DEMO, identity, Bid/Ask, spread,
  quote age, quality, candle counts and exact issues;
- Ctrl+C is the normal operator stop;
- stale is not automatically labelled “market closed”; the exact quality
  reason remains visible.

During PRIMARY/STANDBY pre-READY wait:

- the same MT5Reader is reused;
- only retryable stale/insufficient/sparse data is re-probed;
- the controller heartbeat may renew while ownership is valid;
- no decision cycle or broker write runs before READY.

## Persistent runtime cycle

~~~mermaid
sequenceDiagram
    participant L as PersistentRuntimeLoop
    participant R as MT5Reader
    participant C as Governed cycle
    participant E as Execution service
    participant B as Broker
    participant S as StateStore
    L->>R: Capture fresh completed-cycle facts
    R-->>L: MarketSnapshot and recovery facts
    L->>C: Run entry and management branches
    C->>E: Submit approved action through gate
    E->>S: Persist Intent before write
    E->>B: One MT5 request
    B-->>E: Acknowledgement
    E->>B: Reconcile current truth when required
    E->>S: Persist verified lifecycle result
    C-->>L: Dashboard/research DTOs
    L->>L: Wait for next M5 boundary and renew lease
~~~

The entry branch and management branch share the final writer but remain
different decisions:

~~~text
entry:       intelligence → strategy → fusion/timing → Trade Plan → risk → gate
management:  fresh exposure → Trade Manager → gate
both:        Intent → one write → broker verification → durable update
~~~

## Entry and management authority

~~~mermaid
flowchart LR
    OPINION["Market opinion"] --> PLAN["Structural intent"]
    PLAN --> MONEY["Monetary authority"]
    MONEY --> PERMISSION["Write permission"]
    PERMISSION --> BROKER["Irreversible broker boundary"]
~~~

No high score, dashboard action, research result or new controller epoch may
skip an arrow.

## Persistence and recovery truth layers

| Layer | What it knows | What it cannot prove |
|---|---|---|
| StateStore | intent, context, risk, lineage and history | current broker exposure after downtime |
| checkpoint/backup | portable verified copy of local state | that a position is absent at the broker |
| MT5RecoveryTruth | current account/symbol/position/order/deal facts | why a historical intent was created |
| RecoveryAuthorities | whether all required facts align now | future broker behaviour |

## Research boundary

Research is an offline branch:

~~~mermaid
flowchart TB
    RUNTIME["Runtime records and portable datasets"] --> REPLAY["Chronological replay"]
    REPLAY --> METRICS["Metrics, ablation and stress"]
    METRICS --> WFA["Walk-forward and holdout"]
    WFA --> CANDIDATE["Governed candidate"]
    CANDIDATE --> APPROVAL["Explicit approval"]
    APPROVAL --> POLICY["Versioned policy — still uses normal safety"]
~~~

Research may reuse production semantics. It may not import the raw writer,
self-promote, alter hard safety or turn counterfactual P/L into account truth.

## Exact source ownership

| Architecture boundary | Source files | Tests |
|---|---|---|
| launcher/readiness | app/main.py, app/dashboard.py, operator/dashboard.py | test_app_readiness.py, test_dashboard.py |
| startup composition | app/runtime.py, app/startup.py, app/recovery.py, app/recovery_mt5.py | test_live_startup_runtime.py, test_startup_recovery.py, test_recovery_mt5.py |
| cycle and schedule | app/cycle.py, app/loop.py | test_runtime_loop.py |
| raw reads/snapshot | market_data/mt5_reader.py, market_data/snapshot.py | test_market_data.py, test_intelligence_snapshot.py |
| authority chain | decisions/, risk/, execution/ | test_strategy_decisions.py, test_trade_plan_risk.py, test_session_news_permissions.py, test_execution_safety.py |
| management | management/ | test_trade_manager.py, test_management_execution.py |
| state/backup | persistence/, execution/intent_store.py | test_persistence_recovery.py, test_runtime_checkpoint.py, test_backup_catalog.py |

## Explicit non-goals

Architecture does not define indicator thresholds, strategy weights, risk
formulas or provider selection in detail. Those belong to their topic contracts.
It also does not claim that a diagram is live broker evidence.

