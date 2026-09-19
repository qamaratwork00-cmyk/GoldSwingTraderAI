# GoldSwingTraderAI — Coder Guide

**Status:** PROVISIONAL — AUTHORITATIVE DEVELOPER MANUAL
**Version:** 5.0-phase-manual
**Authority:** Feature-to-code navigation, phase implementation contract,
module ownership, authority boundaries, test ownership and developer workflow.
This guide explains how to implement the system; detailed trading, risk,
execution, research and coding rules remain owned by the linked authority
documents.

## 1. What this guide is for

GoldSwingTraderAI is documentation-first. The repository was designed as a
chain of contracts before the runtime was assembled:

~~~text
verified broker/market facts
→ market intelligence
→ independent strategy hypotheses
→ BUY/SELL fusion and entry timing
→ structural Trade Plan
→ monetary risk and hard authorities
→ one governed broker boundary
→ reconciliation and durable lifecycle state
→ management, learning, research and operator visibility
~~~

This guide answers the questions a coder must be able to answer before
changing code:

- What problem does this feature solve?
- Which phase introduced it and which later phase consumes it?
- Which document owns its meaning?
- Which source module owns its implementation?
- What are its inputs, outputs, states and failure modes?
- What may run independently, and what must remain ordered?
- Which tests prove the boundary?
- What does the operator see?
- What is software proof, and what still requires real MT5/DEMO evidence?

This is a navigation and implementation manual, not a replacement for topic
contracts. If a summary here conflicts with an authoritative topic document,
stop and resolve the contradiction; do not choose the easier implementation.

## 2. Authority and reading order

Read enough of the following chain before coding a material change:

1. [Project Vision](00-foundation/PROJECT_VISION.md) — mission and non-goals.
2. [System Contract](00-foundation/SYSTEM_CONTRACT.md) — frozen system-wide
   invariants.
3. [Architecture](00-foundation/ARCHITECTURE.md) — topology, parallel lanes,
   ordered authorities and runtime lifecycle.
4. The relevant domain authority:
   - [Market Intelligence](10-market-intelligence/MARKET_DATA_AND_HISTORY.md)
     for facts, history and freshness;
   - [Trading Decisions](20-trading-decisions/STRATEGY_FLOOR.md) and its
     linked decision documents for hypotheses, timing and plans;
   - [Risk and Execution](30-risk-execution/RISK_CONTRACT.md) and its linked
     contracts for hard permission, broker safety and recovery;
   - [Research and Validation](40-research-learning/RESEARCH_AND_VALIDATION.md)
     for chronology, metrics and evidence;
   - [Dashboard and UX](50-operator/DASHBOARD_AND_UX.md) for presentation
     visibility.
5. [Documentation Standard](90-governance/DOCUMENTATION_STANDARD.md) — the
   frozen preservation, synchronization and completeness process; read it
   before changing any document.
6. [Design Decisions](90-governance/DESIGN_DECISIONS.md) and
   [Open Questions](90-governance/OPEN_QUESTIONS.md) — frozen choices,
   calibration and external proof boundaries.
7. [Coding Standard](60-engineering/CODING_STANDARD.md) — code quality,
   complexity, dependency, comments, performance and error handling.
8. [Module Structure](60-engineering/MODULE_STRUCTURE.md) — file ownership
   and dependency direction.
9. This guide — exact source/test navigation and phase handoff.
10. [Testing and Verification](60-engineering/TESTING_AND_VERIFICATION.md) and
   [Final Release Audit](60-engineering/FINAL_RELEASE_AUDIT.md) — proof level
   and evidence language.

The [Final Build Prompt](FINAL_BUILD_PROMPT.md) is an implementation handoff
summary. The [ChatGPT Project Build and Recovery Guide](CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md)
is the phase/resume process. Neither may silently override a topic authority.

## 3. System in one picture

~~~mermaid
flowchart TB
    MODE["app/main.py — READINESS / PRIMARY / STANDBY"] --> READ["MT5Reader + normalized MarketSnapshot"]
    READ --> INTEL["Market intelligence desks"]
    INTEL --> STRAT["Strategy families + BUY/SELL theses"]
    STRAT --> FUSION["Fusion + Opportunity + Entry Timing"]
    FUSION --> PLAN["Structural Trade Plan"]
    PLAN --> HARD["Risk + session/news + identity + position + controller"]
    HARD --> GATE["Central Execution Permission Gate"]
    GATE --> INTENT["Durable Execution Intent"]
    INTENT --> WRITE["One MT5Writer boundary"]
    WRITE --> RECON["Broker reconciliation + persistence"]
    RECON --> MANAGE["Trade Manager + operator/research visibility"]
~~~

The diagram has two different kinds of ordering:

1. **Analytical lanes** may be evaluated independently from the same immutable
   snapshot. They produce evidence and hypotheses, not broker permission.
2. **Authority lanes** are ordered. Trade Plan precedes monetary risk; risk and
   hard authorities precede the gate; the gate precedes Intent and a broker
   write; a broker acknowledgement is not final truth until reconciliation.

## 4. Non-negotiable engineering and safety invariants

These are cross-cutting implementation rules. Detailed meanings belong to the
linked contracts, but every coder must preserve them:

| Invariant | Implementation consequence |
|---|---|
| One verified snapshot | Do not let separate desks silently read MT5 again or mix timestamps. |
| Closed-candle chronology | H4/H1/M15/M5 decision evidence cannot use a forming candle or future information. |
| Structure before sizing | Structural invalidation, targets and original R exist before monetary risk sizing. |
| Safety is not score | Risk, DEMO, identity, news/session, position, controller and execution checks are hard authorities. |
| DEMO-only V1 | Positive DEMO verification is required; there is no REAL override switch. |
| One broker write boundary | Raw irreversible MT5 calls belong only in execution/mt5_writer.py. |
| Intent is one-shot | The same durable Intent ID is never blindly sent twice. |
| Broker truth wins | Ambiguous acknowledgement becomes reconciliation work, not a retry guess. |
| Controller fencing | A stale holder/epoch cannot create a write. |
| Unknown is not pass | Missing/corrupt/stale critical truth remains UNKNOWN, BLOCKED or RECONCILING. |
| Dashboard is read-only | Rendering cannot calculate permission or trigger strategy/execution. |
| Research is not production authority | Replay, discovery and invention produce evidence/candidates, never raw broker writes. |
| Recovery is not reset | Restore/restart must not erase risk, lifecycle, learning, approval or cooldown truth. |

## 5. Logical parallelism versus ordered authority

~~~mermaid
flowchart TB
    SNAP["One immutable MarketSnapshot"] --> CANDLE["Candle / structure"]
    SNAP --> TECH["Technical / levels / indicators"]
    SNAP --> LIQ["Liquidity / SMC / confluence"]
    SNAP --> CONTEXT["Session / news / account context"]
    CANDLE --> STRATEGY["Independent strategy families"]
    TECH --> STRATEGY
    LIQ --> STRATEGY
    CONTEXT --> STRATEGY
    STRATEGY --> FUSION["BUY/SELL fusion and timing"]
    FUSION --> PLAN["Trade Plan"]
    PLAN --> RISK["Risk and hard authorities"]
    RISK --> GATE["Execution gate"]
    GATE --> WRITE["Intent → MT5Writer → reconcile"]
~~~

“Parallel” means independent ownership and a shared snapshot. It does not
require Python threads. A future concurrent implementation is acceptable only
if it preserves deterministic ordering, bounded outputs, chronology and the
same final authority model.

| Lane | Owns | May influence | Must never do |
|---|---|---|---|
| Market facts | Account, symbol, quote and completed candles | All downstream analysis | Decide direction or write broker state |
| Intelligence | Structure, levels, liquidity, quant, session/news evidence | Strategy hypotheses and reasons | Grant final execution permission |
| Strategy/decision | Families, BUY/SELL theses, fusion, lifecycle and timing | Action and structural plan | Size risk, check controller or call MT5 |
| Risk/safety | Affordability, daily lock, session/news, identity, position and execution facts | ALLOW/BLOCK/UNKNOWN | Improve a strategy score or rewrite structure |
| Execution/reconciliation | Intent, one request, broker truth and lifecycle status | Durable verified outcome | Decide strategy or blind-retry ambiguity |
| Management | HOLD/PROTECT/TRAIL/RUNNER/EXIT | Managed-trade action request | Bypass the same gate/write boundary |
| Operator | DTOs, terminal frames and explanations | Human visibility | Recalculate or grant authority |
| Research | Replay, metrics, candidates, invention and promotion evidence | Governed future strategy process | Become a production broker writer |

## 6. Phase architecture and completion model

The phases are deliberately distinct. Phases 1–9 build the production
foundation and operator surface. Phase 10 is the offline research/learning
boundary. Phase 11 is durable backup, migration, recovery and controller
proof. Phase 12 composes the full runtime and collects final environment
evidence. A phase is not complete merely because a file exists or the test
count increased.

~~~mermaid
flowchart TB
    P1["1 Foundation"] --> P2["2 MT5 read/data"]
    P2 --> P3["3 Intelligence"]
    P3 --> P4["4 Strategies/decisions"]
    P4 --> P5["5 Trade Plan/Risk"]
    P5 --> P6["6 Session/news/persistence"]
    P6 --> P7["7 Execution/DEMO/controller"]
    P7 --> P8["8 Trade Manager"]
    P8 --> P9["9 Dashboard/operator"]
    P9 --> P10["10 Research/learning/discovery"]
    P10 --> P11["11 Backup/recovery/failover"]
    P11 --> P12["12 Runtime integration/DEMO audit"]
~~~

Every phase packet contains:

~~~text
purpose
→ inputs/outputs/states
→ architecture and ownership
→ exact source modules and public entry points
→ positive/negative/unknown/chronology/fault tests
→ persistence/restart impact
→ dashboard/operator/research impact
→ external evidence boundary
→ documentation and exit gate
~~~

### Phase 1 — Foundation, package skeleton and contracts

**Purpose.** Establish a typed, dependency-light vocabulary before any broker
or strategy code exists. This prevents later modules from inventing different
meanings for account mode, direction, timeframes, reasons, IDs, timestamps or
hard decisions.

**Build outputs.**

- validated secret-free settings and explicit runtime/state modes;
- domain IDs, enums, immutable market/account models and reason codes;
- structured secret-safe JSON logging;
- financial-secret scanner and CI quality boundary;
- package exports and deterministic test foundations.

**Primary source map.**

| Responsibility | Source owner |
|---|---|
| Settings/config parsing | config/settings.py |
| IDs and stable identifiers | domain/ids.py |
| Shared enums | domain/enums.py |
| Immutable facts/models | domain/market.py and domain/models.py |
| Structured logs/redaction | diagnostics/logging.py |
| Secret boundary | security/financial_secrets.py |
| Package entry | __main__.py and __init__.py |

**Contract.** Phase 1 has no MT5, strategy, risk calculation or broker-write
authority. Invalid configuration fails explicitly. Secrets never become
repository data or ordinary log context.

**Tests and exit gate.** Run settings, model, ID, logging, secret-scanner and
coding-contract tests. The package imports/runs; malformed values fail clearly;
timestamps are explicit UTC; the Coding Standard review passes.

### Phase 2 — MT5 read layer, Gold facts and market snapshots

**Purpose.** Create one narrow read authority for Exness MT5 Gold facts. All
later analysis consumes normalized data rather than raw MetaTrader5 objects.

**Build outputs.**

- XAUUSDm/XAUUSD alias resolution;
- account facts and positive DEMO verification;
- verified SymbolSpec including point/tick/volume/stops/filling facts;
- Bid/Ask quote and open-position read facts;
- completed H4/H1/M15/M5 candle series;
- one MarketSnapshot with DataQuality and exact issues;
- freshness, sparse-history, insufficient-history and corrupt-data handling.

**Primary source map.**

| Responsibility | Source owner |
|---|---|
| Single MT5 read boundary | market_data/mt5_reader.py — MT5Reader |
| Snapshot construction | market_data/snapshot.py — MarketSnapshotBuilder |
| Normalized facts | domain/market.py |
| Data quality vocabulary | domain/enums.py — DataQuality |

**Contract.** The reader is read-only. No strategy, risk, dashboard or
recovery module creates a duplicate MT5 read client. Completed-candle
timestamps are the chronology boundary. STALE/INSUFFICIENT/SPARSE are explicit
states; they do not become permission to trade.

**Tests and evidence.** Use market-data, snapshot, model and no-lookahead
tests. CI can prove fake-reader contracts; controlled Windows MT5 evidence
must separately prove actual account, symbol, quote and history behaviour.

### Phase 3 — Market intelligence and optional confluence

**Purpose.** Convert one MarketSnapshot into bounded, typed descriptive
evidence without turning indicators or optional tools into hidden hard gates.

**Build outputs.**

- Candle Structure: confirmed swings, BOS/MSS and sequences;
- Technical Structure/Levels: zones, location and target room;
- Liquidity/SMC: pools, sweeps, FVG and qualified OB context;
- EMA20/EMA50, RSI, ATR, volatility, momentum and extension;
- session and fundamental/news facts;
- causal Trendline/Fibonacci/POC confluence when available.

**Primary source map.**

| Evidence | Source owner |
|---|---|
| Structure and swings | intelligence/candle_structure.py |
| Technical zones/location | intelligence/technical.py |
| Liquidity/SMC | intelligence/liquidity.py |
| Indicators/volatility | intelligence/indicators.py |
| Session context | intelligence/session.py |
| News/fundamental facts | intelligence/news.py and app/session_news.py |
| Optional confluence | intelligence/confluence.py and strategies/confluence.py |
| Shared intelligence DTO | intelligence/snapshot.py |

**Contract.** Every desk consumes the same immutable snapshot. Confirmed
evidence carries confirmation chronology; forming candles and future bars are
forbidden. Trendline/Fibonacci/POC are bonus/context evidence. Missing optional
confluence does not reduce the base strategy to zero and never independently
blocks an order.

**Tests and exit gate.** Intelligence, technical, liquidity, confluence and
session/news tests cover positive, absent, uncertain and no-lookahead cases.
The phase is complete only when every output is descriptive and no module can
write to MT5 or grant execution permission.

### Phase 4 — Strategy floor, BUY/SELL theses and decision fusion

**Purpose.** Turn evidence into auditable hypotheses and timing decisions
without allowing a long filter chain to silently destroy valid opportunities.

**Initial strategy families.**

1. Trend Pullback Continuation.
2. Breakout Expansion.
3. Breakout Retest Continuation.
4. Liquidity Sweep Reversal.
5. Failed Breakout Reversal.
6. Compression Expansion.

**Primary source map.**

| Responsibility | Source owner |
|---|---|
| Family evaluation | strategies/floor.py |
| Optional family confluence | strategies/confluence.py |
| Opportunity lifecycle | decisions/opportunity.py |
| BUY/SELL fusion | decisions/fusion.py and decisions/snapshot.py |
| Entry timing | decisions/timing.py |

**Contract.** BUY and SELL theses are built independently. Red-team/conflict
evidence remains visible. A valid opportunity may remain ARMED while timing is
WAIT or may become MISSED/INVALID with an explicit reason. Optional confluence
can add bounded support but cannot become a seventh mandatory strategy or a
hard permission gate. No module in this phase sizes monetary risk or calls MT5.

**Tests and exit gate.** Strategy-decision tests cover family attribution,
conflict, optional evidence, WAIT/MISSED/INVALID/BLOCKED distinctions,
chronology and deterministic output. The output is a DecisionSnapshot or
explicit non-entry result ready for Trade Plan construction.

### Phase 5 — Structural Trade Plan and Risk Engine

**Purpose.** Separate structural market validity from monetary affordability.
The market plan is fixed first; sizing responds to the plan and broker facts.

**Build outputs.**

- structural entry reference and invalidation/stop;
- Primary, Expansion and Runner objectives;
- immutable original R;
- bounded RR/target-room policy;
- SMALL/MEDIUM/NORMAL account profile resolution;
- broker-aware volume, min-lot, step, margin and risk geometry;
- UTC risk-day Account Safety P/L, daily lock and cooldown state;
- governed manual reset boundary, disabled by default.

**Primary source map.**

| Responsibility | Source owner |
|---|---|
| Structural plan | decisions/trade_plan.py |
| Monetary sizing and affordability | risk/engine.py |
| Risk-day/cooldown state | risk/state.py |
| Hard risk/session composition | risk/permissions.py |
| Risk/account profile vocabulary | risk package and domain enums |

**Contract.** Never distort a structural stop to make a lot affordable. Actual
broker minimum volume can block the current plan without invalidating the
underlying opportunity. There is no arbitrary 100-dollar eligibility floor.
Risk is not a strategy score. Original R is immutable after approval.

**Tests and exit gate.** Trade-plan/risk, small-account, margin, risk-state and
regression tests cover positive sizing, min-lot unaffordability, daily locks,
cooldown, reset limits, non-finite values and immutable geometry.

### Phase 6 — Session/news permission, SQLite persistence and recovery foundation

**Purpose.** Add hard market-safety truth and durable lifecycle state before
irreversible execution exists. This phase creates persistence primitives; the
full backup/migration/failover drill belongs to Phase 11 and integrated runtime
composition belongs to Phase 12.

**Build outputs.**

- session states, PRE_CLOSE flatten rules and reopen warm-up;
- provider-neutral news snapshot validation and freshness;
- NEWS_CLEAR/BLACKOUT/UNKNOWN/POST_NEWS_WARMUP semantics;
- standard-library SQLite StateStore;
- canonical JSON payloads, checksums, schema versions and event records;
- typed parsers for risk, opportunity, Trade Plan and lifecycle state.

**Primary source map.**

| Responsibility | Source owner |
|---|---|
| Session/news handoff | app/session_news.py |
| Session/news intelligence | intelligence/session.py and intelligence/news.py |
| Hard permission composition | risk/permissions.py |
| SQLite transactions/checksums | persistence/store.py |
| Runtime state models | persistence/runtime_state.py |
| State/checkpoint primitives | persistence/checkpoint.py |

**Contract.** Missing, stale, malformed or mis-scoped required truth is
UNKNOWN/BLOCKED, never implicit PASS. Persistence corruption cannot silently
reset to an empty safe-looking account. Restart must preserve risk, lifecycle,
intent, trade, learning and cooldown meaning.

**Tests and exit gate.** Session/news, persistence, typed-state, checksum,
schema, restart and corruption tests pass. The phase does not claim a
fresh-machine restore or shared coordination proof; those are Phase 11/12
evidence.

### Phase 7 — Central execution gate, DEMO Guard, controller and writes

**Purpose.** Concentrate all irreversible authority in one auditable boundary.
This is where the V1 positive DEMO Guard becomes an execution-environment
authority, not a configurable switch.

**Execution path.**

~~~mermaid
flowchart TB
    FACTS["Account + SymbolSpec + fresh quote + positions"] --> DEMO["MT5Reader.demo_guard"]
    DEMO --> ID["Account/server/symbol identity"]
    ID --> CHECKS["Spread + drift + margin + stop + volume + ownership checks"]
    CHECKS --> CTRL["Controller holder + unexpired fencing epoch"]
    CTRL --> GATE["execution/gate.py — ALLOW/BLOCK/UNKNOWN"]
    GATE --> INTENT["Durable ExecutionIntent"]
    INTENT --> WRITER["execution/mt5_writer.py — one request"]
    WRITER --> VERIFY["MT5 reconciliation"]
~~~

**Primary source map.**

| Responsibility | Source owner |
|---|---|
| Positive DEMO evidence | market_data/mt5_reader.py — MT5Reader.demo_guard |
| Execution checks | execution/checks.py |
| Permission composition | execution/gate.py |
| Intent lifecycle | execution/models.py and execution/intent_store.py |
| Broker request boundary | execution/service.py and execution/mt5_writer.py |
| Position/order reconciliation | execution/reconcile.py and app/recovery_mt5.py |
| Lease/fencing primitive | execution/controller.py and execution/sqlite_coordination.py |

**DEMO Guard rules.**

- Account mode must be positively normalized as DEMO.
- DEMO_GUARD PASS is evidence, not an environment variable.
- No setting disables the guard and no REAL override is defined in V1.
- Non-DEMO, unknown, mismatched or unavailable identity cannot produce
  broker-write permission.
- Readiness may display the DEMO fact but never turns it into a trade.

**Contract.** One Intent ID can produce at most one irreversible request.
Success-like acknowledgement is not final exposure truth. Ambiguous results
become reconciliation-only. A stale controller epoch cannot write. Raw
MetaTrader5 order calls remain unreachable from strategy, risk, dashboard and
research.

**Tests and evidence.** Execution-safety, controller, SQLite-coordination,
reconciliation and DEMO/account identity tests cover PASS/BLOCK/UNKNOWN,
duplicate-send prevention, stale-holder denial, ambiguous acknowledgement and
foreign/manual exposure. Actual Windows DEMO order proof remains a separate
controlled evidence gate.

### Phase 8 — Trade Manager and management execution bridge

**Purpose.** Govern the lifecycle of an already-open bot-managed position
without treating management as a second entry system.

**Build outputs.**

- HOLD, PROTECT, TRAIL, RUNNER and EXIT actions;
- fresh structure/continuation/reversal evidence;
- original R based management;
- Primary/Expansion/Runner objective progression;
- PRE_CLOSE flatten override;
- modify/close Intent path through the same execution gate and reconciliation.

**Primary source map.**

| Responsibility | Source owner |
|---|---|
| Management decision | management/manager.py |
| Managed-trade model/store | management/models.py and management/store.py |
| Management execution bridge | management/execution.py |
| Shared governed cycle | app/cycle.py |

**Contract.** Small profit alone does not force exit or arbitrary breakeven.
Runner extension needs fresh continuation and a real objective. Management
cannot widen approved original risk, create a second Gold exposure or bypass
DEMO, controller, ownership, risk and reconciliation checks.

**Tests and exit gate.** Trade-manager and management-execution tests cover
HOLD/PROTECT/TRAIL/RUNNER/EXIT, immutable original R, ownership mismatch,
PRE_CLOSE, ambiguous writes and broker-verified state updates.

### Phase 9 — Dashboard and operator workflows

**Purpose.** Make every authority and reason understandable to the operator
without creating a second authority. Phase 9 has two presentation contracts
because pre-cycle READINESS does not have strategy/risk/execution results.

**Full cycle dashboard.** After a governed RuntimeCycleResult, preserve useful
GoldScalperAI visibility:

- symbol, account mode, DEMO guard and runtime role;
- Bid/Ask, spread quality and M5 countdown;
- H4/H1/M15/M5 structure, EMA20/EMA50, RSI and ATR;
- BUY/SELL scores, Opportunity, Entry Timing, coverage and exact reason;
- risk profile, proposed risk/lot, day safety P/L/limit/remaining budget;
- position capacity, loss streak and cooldown;
- controller role/epoch, reconciliation and execution permission;
- open-trade entry/current/SL/TP/objectives/R/manager action;
- learning/discovery, candidate/suppression, backup and health state.

**Readiness monitor frame.** After every normalized READINESS snapshot,
including STALE/INSUFFICIENT/SPARSE waits, show:

- symbol, account mode, DEMO Guard and identity state;
- Bid/Ask/spread, quote age and DataQuality;
- H4/H1/M15/M5 completed-candle counts and exact issues;
- next poll interval;
- explicit STRATEGY NOT RUN and BROKER WRITES DISABLED.

It must not invent scores, risk, session/news permission or execution
permission. A healthy READINESS snapshot is still read-only. PRIMARY/STANDBY
full-cycle presentation begins only after governed recovery and a fresh cycle.

**Primary source map.**

| Responsibility | Source owner |
|---|---|
| Full cycle DTO mapping | app/dashboard.py — build_dashboard_data |
| Readiness DTO mapping | app/dashboard.py — build_readiness_dashboard_data |
| Full cycle rendering | operator/dashboard.py — render_dashboard |
| Readiness rendering | operator/dashboard.py — render_readiness_dashboard |
| Launcher sinks | app/main.py and app/loop.py |

**Tests and exit gate.** Dashboard tests prove visibility, WAIT/BLOCKED/open
trade distinction, text fallback and no raw authority. Readiness tests prove
stale frame emission, fresh transition and write-lock visibility. Rendering
never calls MT5, risk, gate or writer code.

### Phase 10 — Replay, metrics, learning and governed discovery

**Purpose.** Improve the stable baseline through chronological evidence without
allowing research to become production execution authority.

**Build outputs.**

- chronological replay with no-lookahead and historical PRE_CLOSE/session facts;
- actual versus counterfactual metrics;
- MFE, MAE, capture, drawdown, accuracy and Opportunity Recall;
- StrategyMemory and durable episode journal;
- stress, ablation, walk-forward, datasets and immutable evidence packages;
- governed discovery, declarative invention, candidate registry and promotion;
- explicit discovery liveness: candidate created or suppression reason.

**Primary source map.**

| Responsibility | Source owner |
|---|---|
| Chronological replay | research/replay.py and research/management_replay.py |
| Metrics/validation/stress | research/metrics.py, validation.py, stress.py, ablation.py |
| Dataset acquisition | research/acquisition.py and scripts/acquire_mt5_dataset.py |
| Evidence packages | research/evidence.py, packages.py and outcomes.py |
| Journal/learning | research/episode_journal.py, learning.py, session_history.py |
| Discovery/invention | research/discovery.py and invention.py |
| Promotion governance | research/promotion.py |
| Walk-forward boundary | scripts/run_walk_forward.py |

**Contract.** Candidates are declarative evidence objects; they cannot execute
arbitrary generated Python, self-promote, alter hard safety or call MT5.
Research results are not broker or profitability certification. The dashboard
may show research liveness, never research permission.

### Phase 11 — Portable backup, migration, recovery and controller proof

**Purpose.** Ensure state and ownership survive restart, machine migration,
corruption, failover and stale-primary conditions without duplicate exposure.

**Build outputs.**

- portable records/events checkpoint;
- secret-scanned public-safe staging;
- verified local rolling backup/catalog/retention;
- fresh-database-only restore;
- broker reconciliation after restore;
- durable SQLite coordination and monotonic fencing;
- PRIMARY/STANDBY takeover and stale-holder denial;
- integrated RecoveryAuthorities composition.

**Primary source map.**

| Responsibility | Source owner |
|---|---|
| SQLite records/events | persistence/store.py |
| Typed runtime recovery | persistence/runtime_state.py |
| Checkpoint/restore | persistence/checkpoint.py and scripts/restore_runtime_checkpoint.py |
| Backup/catalog | persistence/backup.py and tests/test_backup_catalog.py |
| Public-safe staging | persistence/publication.py and scripts/stage_public_backup.py |
| Controller/fencing | execution/controller.py and execution/sqlite_coordination.py |
| Recovery authorities | app/recovery.py and app/startup.py |
| Live broker truth adapter | app/recovery_mt5.py |
| Runtime composition | app/runtime.py |

**Contract.** Restore context never replaces live MT5 positions/orders/deals.
Restore refuses destructive overwrite of an existing runtime DB. Takeover
requires a new epoch plus complete recovery; lease acquisition alone is not
READY. Financial credentials never enter checkpoints or public artifacts.

### Phase 12 — Persistent runtime integration and final DEMO audit

**Purpose.** Compose the previous phases into one continuously running,
controller-gated process and collect the evidence needed for release claims.

**Build outputs.**

- READINESS / PRIMARY / STANDBY launcher composition;
- MT5 initialize → recovery truth → authorities → controller → READY;
- narrow stale-data pre-READY wait with heartbeat and no cycle/write;
- persistent M5 scheduler and 10-second controller renewal;
- governed entry/management cycle, backups and safe shutdown;
- fresh-machine restore, failover, restart/reconciliation and controlled
  Windows MT5 DEMO evidence;
- final documentation and release audit.

**Primary source map.**

| Runtime responsibility | Source owner |
|---|---|
| Module launcher | __main__.py and app/main.py |
| Live dependency composition | app/runtime.py |
| Startup/recovery | app/startup.py and app/recovery.py |
| Cycle orchestration | app/cycle.py |
| Persistent scheduler | app/loop.py |
| Session/news provider boundary | app/session_news.py |
| Dashboard sinks | app/main.py and app/loop.py |

**Contract.** The default READINESS path is read-only. PRIMARY/STANDBY become
write-capable only after all recovery authorities, DEMO, identity, controller,
session/news, state, position and execution requirements pass. Stale data keeps
the process observable but never grants permission.

**Release evidence.** Deterministic CI, local replay and fake-reader tests
cannot be reported as real broker/DEMO proof. Final release requires explicit
artifacts for controlled Windows lifecycle, fresh-machine restore,
cross-machine failover, restart reconciliation, accepted session/news
producer operation and real XAU validation.

## 7. Runtime entry points and lifecycle

| Entry point | What it does | Broker-write capability |
|---|---|---|
| __main__.py | Delegates module execution to app.main.main | None by itself |
| app.main.main | Loads settings, configures logging and selects explicit mode | Depends on selected mode |
| app.main.run_readiness | Initializes MT5, snapshots facts, renders monitor and waits safely | None |
| app.main.run_startup | Bounded integrated startup/recovery diagnostic | Releases authorities after result |
| app.main.run_persistent | Creates LiveStartupRuntime and PersistentRuntimeLoop | Only through governed cycle |
| app.loop.PersistentRuntimeLoop | Heartbeat, stale wait, M5 scheduling, backup and shutdown | Delegates to GovernedRuntimeCycle |
| app.cycle.GovernedRuntimeCycle | One fresh analysis/plan/risk/gate/management cycle | Delegates to ExecutionService |
| execution.mt5_writer | Narrow irreversible MT5 boundary | Only final governed writer |

### Startup sequence

~~~mermaid
flowchart TB
    SETTINGS["Load/validate settings"] --> INIT["MT5Reader.initialize"]
    INIT --> SNAP["Account + symbol + quote + completed candles"]
    SNAP --> RECOVERY["Build MT5RecoveryTruth + select local state"]
    RECOVERY --> AUTH["RecoveryAuthorities + repositories + reconciler"]
    AUTH --> CTRL["Controller acquisition/fencing"]
    CTRL --> RESULT{"Recovery state"}
    RESULT -->|"STALE/INSUFFICIENT/SPARSE"| WAIT["Heartbeat + re-probe; no strategy/write"]
    WAIT --> SNAP
    RESULT -->|"BLOCKED/unknown/fault"| STOP["Fail closed and operator review"]
    RESULT -->|"READY"| LOOP["Persistent M5 loop"]
    LOOP --> CYCLE["Fresh governed cycle"]
    CYCLE --> DASH["Dashboard + backup + health"]
~~~

The default READINESS sequence ends before RecoveryAuthorities and the
strategy cycle. Its monitor frame is still visible on every normalized read.
The persistent path does not run a cycle during the narrow stale-data wait.

### Safe shutdown

The process must stop new intents, reconcile any in-flight write, persist
critical lifecycle/risk state, create/verify due backups, release controller
ownership and shut down MT5. Keyboard interrupt is an operator stop, not a
permission bypass.

## 8. Feature-to-code traceability

The topic document owns behaviour, the source owner implements it and the tests
provide executable proof. The table is intentionally complete enough to locate
the first file a coder should open.

| Feature | Behaviour authority | Primary source / entry point | Main tests |
|---|---|---|---|
| Settings, modes and config validation | 00-foundation/SYSTEM_CONTRACT.md | config/settings.py: Settings.from_env | tests/test_settings.py |
| IDs, enums, reason codes and domain DTOs | 00-foundation/SYSTEM_CONTRACT.md | domain/ids.py, domain/enums.py, domain/models.py, domain/market.py | tests/test_ids.py, tests/test_models.py |
| Secret-safe logging and scanning | 60-engineering/CODING_STANDARD.md | diagnostics/logging.py, security/financial_secrets.py | tests/test_logging.py, tests/test_secret_scanner.py |
| Documentation completeness/link gate | 90-governance/DOCUMENTATION_STANDARD.md | scripts/verify_documentation.py | tests/test_documentation_contract.py, CI Documentation contract step |
| MT5 account/symbol/quote/history reads | 10-market-intelligence/MARKET_DATA_AND_HISTORY.md | market_data/mt5_reader.py: MT5Reader | tests/test_market_data.py |
| Normalized H4/H1/M15/M5 snapshot and freshness | 10-market-intelligence/MARKET_DATA_AND_HISTORY.md | market_data/snapshot.py: MarketSnapshotBuilder | tests/test_market_data.py, tests/test_intelligence_snapshot.py |
| Candle structure, swings, BOS and MSS | 10-market-intelligence/CANDLE_STRUCTURE.md | intelligence/candle_structure.py | tests/test_intelligence_core.py |
| Technical zones, location and target room | 10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md | intelligence/technical.py | tests/test_technical_confluence.py |
| Liquidity, sweep, FVG and OB evidence | 10-market-intelligence/LIQUIDITY_AND_SMC.md | intelligence/liquidity.py | tests/test_technical_liquidity.py |
| EMA20/EMA50, RSI, ATR and volatility | 10-market-intelligence/INDICATORS_AND_VOLATILITY.md | intelligence/indicators.py | tests/test_intelligence_core.py |
| Session/news facts and provider handoff | 10-market-intelligence/SESSION_CONTEXT.md; 30-risk-execution/SESSION_NEWS_PROVIDER_CONTRACT.md | intelligence/session.py, intelligence/news.py, app/session_news.py | tests/test_session_news_provider.py, tests/test_session_news_permissions.py |
| Optional Trendline/Fibonacci/POC confluence | 10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md | intelligence/confluence.py, strategies/confluence.py | tests/test_technical_confluence.py |
| Six-family strategy floor | 20-trading-decisions/STRATEGY_FLOOR.md | strategies/floor.py | tests/test_strategy_decisions.py |
| Independent BUY/SELL fusion and conflict | 20-trading-decisions/SCORING_AND_DECISION_FUSION.md | decisions/fusion.py, decisions/snapshot.py | tests/test_strategy_decisions.py |
| Opportunity lifecycle and entry timing | 20-trading-decisions/ENTRY_TIMING.md | decisions/opportunity.py, decisions/timing.py | tests/test_strategy_decisions.py |
| Structural Trade Plan and original R | 20-trading-decisions/TRADE_PLAN.md | decisions/trade_plan.py | tests/test_trade_plan_risk.py |
| Monetary risk, sizing and daily lock | 30-risk-execution/RISK_CONTRACT.md | risk/engine.py, risk/state.py | tests/test_trade_plan_risk.py, tests/test_risk_state_regressions.py, tests/test_small_account_profile.py |
| Session/news/risk hard permission | 30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md | risk/permissions.py | tests/test_session_news_permissions.py |
| DEMO Guard | 30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md | market_data/mt5_reader.py: MT5Reader.demo_guard; app/startup.py; execution/gate.py | tests/test_market_data.py, tests/test_execution_safety.py, tests/test_live_startup_runtime.py |
| Account/server/symbol identity | 30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md | execution/checks.py, app/recovery.py, app/main.py | tests/test_execution_safety.py, tests/test_startup_recovery.py, tests/test_app_readiness.py |
| Spread, drift, margin, stops and volume checks | 30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md | execution/checks.py, risk/engine.py | tests/test_execution_safety.py, tests/test_margin_authority.py |
| Central ALLOW/BLOCK/UNKNOWN gate | 30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md | execution/gate.py | tests/test_execution_safety.py |
| One-shot Intent and broker write | 30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md | execution/models.py, intent_store.py, service.py, mt5_writer.py | tests/test_execution_safety.py |
| Reconciliation and recovery truth | 30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md | execution/reconcile.py, app/recovery_mt5.py, app/recovery.py | tests/test_recovery_mt5.py, tests/test_startup_recovery.py |
| Controller lease and fencing | 30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md | execution/controller.py, execution/sqlite_coordination.py | tests/test_sqlite_coordination.py, tests/test_live_startup_runtime.py |
| Trade Manager | 20-trading-decisions/TRADE_MANAGER_AND_EXIT.md | management/manager.py, management/execution.py | tests/test_trade_manager.py, tests/test_management_execution.py |
| SQLite state/checkpoint/backup/restore | 30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md | persistence/store.py, runtime_state.py, checkpoint.py, backup.py, publication.py | tests/test_persistence_recovery.py, tests/test_runtime_checkpoint.py, tests/test_backup_catalog.py, tests/test_operator_scripts.py |
| Persistent M5 runtime and stale wait | 00-foundation/ARCHITECTURE.md | app/runtime.py, app/cycle.py, app/loop.py | tests/test_live_startup_runtime.py, tests/test_runtime_loop.py |
| READINESS keep-alive monitor | 50-operator/SETUP_AND_RUN_GUIDE.md | config/settings.py, app/main.py | tests/test_settings.py, tests/test_app_readiness.py |
| READINESS terminal monitor dashboard | 50-operator/DASHBOARD_AND_UX.md | app/dashboard.py, app/main.py, operator/dashboard.py | tests/test_app_readiness.py, tests/test_dashboard.py |
| Full cycle dashboard and health | 50-operator/DASHBOARD_AND_UX.md | app/dashboard.py, operator/dashboard.py | tests/test_dashboard.py |
| Replay, metrics, WFA and stress | 40-research-learning/RESEARCH_AND_VALIDATION.md | research/replay.py, metrics.py, validation.py, stress.py, scripts/run_walk_forward.py | tests/test_research_validation.py, test_research_stress.py, test_research_ablation.py, test_research_acquisition.py, test_research_datasets.py, test_research_evidence.py, test_research_packages.py, test_walk_forward_script.py |
| Learning and durable episodes | 40-research-learning/LEARNING_AND_AI_BOUNDARIES.md | research/learning.py, episode_journal.py | tests/test_research_session_history.py, tests/test_research_outcomes.py |
| Discovery and declarative invention | 40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md; AUTONOMOUS_STRATEGY_INVENTION.md | research/discovery.py, invention.py | tests/test_discovery_invention.py, tests/test_discovery_journal.py |
| Candidate promotion and rollback | 40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md | research/promotion.py | tests/test_promotion_governance.py |

## 9. Three high-value implementation traces

### 9.1 DEMO Guard trace

~~~mermaid
sequenceDiagram
    participant R as MT5Reader
    participant S as Startup/runtime
    participant G as Execution gate
    participant W as MT5Writer
    R->>R: normalize AccountFacts
    R->>R: demo_guard(AccountFacts)
    R-->>S: PASS / BLOCK / UNKNOWN
    S->>G: execution-environment authority
    G->>G: combine DEMO with all hard authorities
    G-->>W: ALLOW only after all checks pass
    W-->>S: broker result, then reconciliation truth
~~~

The guard is positive runtime evidence. It is not a setting, score or
dashboard switch. A dashboard can display it; it cannot create it.

### 9.2 Strategy and risk trace

~~~text
MarketSnapshot
→ IntelligenceSnapshot
→ six StrategyFamily hypotheses
→ independent BUY/SELL thesis
→ DecisionSnapshot / Opportunity / EntryTiming
→ TradePlan with structural SL, objectives and immutable original R
→ RiskEvaluation with actual broker volume/monetary affordability
→ hard permission and execution checks
~~~

If a coder needs to change what makes a setup structurally valid, the change
belongs in the decision authority. If the issue is whether the account can
execute that already-defined plan, it belongs in risk/execution. Do not fix a
risk problem by adding a strategy filter.

### 9.3 Dashboard trace

~~~mermaid
flowchart TB
    READ["MarketSnapshot"] --> READYMAP["app/dashboard.py — readiness mapper"]
    READYMAP --> READYDTO["ReadinessDashboardData"]
    READYDTO --> READYVIEW["render_readiness_dashboard"]
    CYCLE["RuntimeCycleResult + LiveCycleFacts"] --> CYCLEMAP["app/dashboard.py — cycle mapper"]
    CYCLEMAP --> CYCLEDTO["DashboardData"]
    CYCLEDTO --> CYCLEVIEW["render_dashboard"]
    READYVIEW --> SCREEN["Terminal; no authority"]
    CYCLEVIEW --> SCREEN
~~~

The readiness mapper cannot show missing strategy/risk facts as zeros or a
generic trade WAIT. The cycle mapper can show authoritative decision/risk/
execution values only after the governed cycle produced them. Both renderers
are pure presentation.

## 10. Where new code belongs

| Change type | Correct owner | Do not place it in |
|---|---|---|
| Raw MT5 row normalization | market_data/domain | strategy, dashboard or risk |
| Structure/levels/liquidity/quant evidence | intelligence | execution or UI |
| Strategy family hypothesis | strategies | risk/gate |
| Fusion, timing or Trade Plan | decisions | MT5 writer |
| Monetary affordability/daily lock | risk | strategy score |
| Hard permission | risk/permissions or execution/gate | dashboard or research |
| Intent/request/reconciliation | execution | strategy or renderer |
| Open-trade action | management | raw MT5 adapter |
| Persistence/restore/backup | persistence | business calculators |
| Startup composition/scheduling | app | domain models |
| Presentation DTO/terminal formatting | app/dashboard.py and operator/dashboard.py | authority modules |
| Replay/evidence/candidate lifecycle | research/scripts | production broker path |

If a change seems to belong in two rows, identify the single authority and add
a typed adapter at the boundary. Do not duplicate a rule just because two
modules need to display or consume it.

## 11. Module/dependency map

~~~text
src/goldswingtraderai/
├── app/             startup, recovery, cycle, loop, session-news, DTO mapping
├── config/          validated non-secret settings and runtime modes
├── domain/          immutable facts, enums, IDs and shared models
├── market_data/     single MT5 read boundary and normalized snapshots
├── intelligence/   structure, technical, liquidity, quant, session, news
├── strategies/     six strategy families and optional confluence
├── decisions/       fusion, opportunity, timing and Trade Plan
├── risk/            profiles, sizing, risk-day, lock and hard composition
├── execution/       checks, gate, Intent, writer, reconciliation, controller
├── management/      managed-trade state and Trade Manager decisions
├── persistence/     SQLite, checksums, checkpoints, backups, publication
├── operator/        presentation DTOs and pure terminal renderers
├── research/        replay, metrics, learning, discovery and promotion
├── diagnostics/     structured logging and reason vocabulary
└── security/        financial-secret scanning
~~~

Dependency direction is inward-to-outward:

~~~mermaid
flowchart LR
    DOMAIN["domain/config"] --> READ["market_data"]
    READ --> INTEL["intelligence"]
    INTEL --> DEC["strategies/decisions"]
    DEC --> RISK["risk"]
    RISK --> EXEC["execution"]
    EXEC --> APP["app orchestration"]
    APP --> OP["operator/persistence/research adapters"]
~~~

Pure domain/intelligence/decision calculations must not import raw
MetaTrader5. Presentation must not import execution internals to recalculate
permission. Research must not import a production writer.

## 12. Coding standard for every phase

The project-wide frozen standard applies to runtime, risk, execution,
persistence, dashboard, research, scripts, configuration and tests:

- Python 3.11+ and standard-library-first dependencies;
- typed dataclasses/enums/IDs at subsystem boundaries;
- pure functions for deterministic calculations where practical;
- classes only for genuine state, resource or lifecycle ownership;
- one snapshot/shared derived fact instead of duplicate MT5 reads;
- no giant mixed-responsibility module or speculative framework;
- concise comments/docstrings explaining why, safety and chronology;
- explicit error/UNKNOWN handling; no broad silent exception swallowing;
- finite-number, UTC, schema and identity validation at persistence boundaries;
- structured secret-safe logging;
- no arbitrary generated code in production research;
- focused tests for positive, negative, unknown, chronology and fault paths.

Before closing a phase, inspect for duplicate reads, magic thresholds, dead
code, vague names, avoidable dependencies, secret leakage and comments that
describe what the code does but not why the boundary exists.

## 13. Verification and evidence

From the repository root, the standard deterministic checks are:

~~~powershell
$env:PYTHONPATH = "src;."
python -m pytest -q
python -m ruff check src tests scripts
python -m compileall -q src tests scripts
git diff --check
python scripts/scan_financial_secrets.py .
python scripts/verify_documentation.py .
~~~

Evidence levels must remain separate:

| Evidence | Proves | Does not prove |
|---|---|---|
| Unit/contract tests | Pure rules and typed boundaries | Full runtime or broker |
| Component/integration tests | Owner composition and recovery semantics | Windows terminal or failover |
| Replay/research | Chronology and defined historical metrics | Future profitability |
| Persistence/controller tests | Local restore/fencing semantics | Arbitrary shared filesystem |
| Windows MT5 readiness | Real read/account/symbol/DEMO snapshot | Fresh recovery, order lifecycle or profitability |
| Controlled DEMO lifecycle | Intended broker execution/restart behaviour | Live-money safety or guaranteed returns |

Never write “complete”, “verified” or “DEMO certified” without the exact
evidence artifact and environment. A green test count is software evidence
only.

## 14. Documentation change gate

This guide follows the frozen documentation protocol in
90-governance/DOCUMENTATION_STANDARD.md and DEC-070/DEC-071. A material code change
must be propagated through the full affected graph:

~~~text
authoritative topic
→ decision/open-question classification
→ architecture diagram
→ module/source/test map
→ coder and phase guide
→ setup/user/dashboard docs
→ prompt and recovery guide
→ testing/release audit
→ links/status/evidence consistency
~~~

The agent must treat a highlighted missing row or section as a signal to audit
all related documents. Useful prior rationale is rewritten into the correct
section, not silently deleted. Phase 1–9 foundation, Phase 10 research, Phase
11 recovery/backup and Phase 12 integration/certification must remain distinct
in every summary.

## 15. Current completion boundary

The deterministic software foundation, runtime composition, stale-data
keep-alive and read-only readiness/full-cycle dashboard paths have executable
test coverage. The following remain external release evidence until their
artifacts exist:

1. accepted session/news producer operation on the intended environment;
2. fresh-machine checkpoint restore plus live broker reconciliation;
3. two-machine failover, stale-primary and split-brain drill;
4. authenticated external backup/publication flow;
5. controlled Windows MT5 DEMO OPEN/MODIFY/CLOSE/restart lifecycle;
6. broader real-XAU historical walk-forward/calibration;
7. final DEMO certification and release/documentation audit.

This boundary is intentionally explicit: code and docs can be complete for a
software layer while real-environment proof remains pending.
