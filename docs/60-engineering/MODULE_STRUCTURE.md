# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 0.1-design  
**Authority:** File/module ownership map and dependency direction.  
**Depends on:** `CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`

## Purpose

This document is the file-oriented companion to `CODER_GUIDE.md`.

The Coder Guide explains a feature end-to-end. This document shows where code should live and which directions dependencies may flow.

Exact filenames remain provisional until implementation begins. The ownership boundaries below are the important part.

## Design goals

- one primary code owner per behaviour;
- no raw MT5 calls from strategy/research/UI code;
- no duplicated risk/news/account permission logic;
- one centralized final broker-write permission gate;
- persistence/restart concerns separated from trading semantics;
- research/learning isolated from production broker authority;
- modules small enough to test independently but not fragmented into unnecessary micro-files.

## Planned top-level package shape

A reasonable implementation target is conceptually:

```text
goldswingtraderai/
├── app/                 runtime entrypoint and coordinator
├── domain/              immutable contracts, IDs, enums, snapshots
├── market_data/         MT5 facts, candles, quotes, history validation
├── intelligence/        candle/structure/technical/liquidity/quant/macro/session
├── strategies/          production strategy-family desks
├── decisions/           theses, fusion, timing, trade-plan construction
├── risk/                monetary risk and risk-state policy
├── execution/           permission gate, broker writes, lifecycle/reconciliation
├── management/          post-entry trade manager
├── persistence/         state store, recovery, registry, backup/migration
├── research/            replay, validation, discovery, invention, promotion
├── operator/            dashboard/operator-facing presentation
├── diagnostics/         health/fault aggregation and reason registry
└── tests/               executable verification
```

This is a design map, not a requirement to create empty directories before their responsibilities exist.

## `app/`

### Runtime coordinator

Owns orchestration only:

```text
startup
→ verified snapshot
→ parallel desks
→ strategies/theses
→ timing/plan
→ risk/safety
→ execution permission
→ broker lifecycle
→ trade manager
→ journal/research/dashboard
```

It must not reimplement candle logic, scoring, risk formulas or broker safety.

## `domain/`

Shared stable data contracts should include concepts such as:

- Market Snapshot;
- Decision/Opportunity/Market Episode IDs;
- Trade Plan;
- Risk Result;
- Execution Permission Result;
- Execution Intent;
- trade lifecycle state;
- health/fault event;
- strategy/candidate identity and version metadata.

Domain objects should avoid direct MT5/network/database dependencies.

## `market_data/`

Primary responsibilities:

- MT5 connection/read-only market facts;
- symbol resolution/specifications;
- Bid/Ask freshness;
- completed-candle retrieval/synchronization;
- history quality/gap checks;
- broker tradeability facts.

Raw broker reads are normalized here before market-intelligence desks consume them.

## `intelligence/`

Suggested bounded owners:

- Candle/Structure Engine — candle sequences, swings, BOS/MSS, displacement;
- Technical/Location Engine — S/R zones, range/location/target room;
- Liquidity/SMC Engine — liquidity pools, sweeps, FVG, qualified OB, premium/discount;
- Indicator/Quant Engine — EMA/RSI/ATR, volatility/momentum/extension metrics;
- Fundamental/News Facts Adapter — macro/event facts and provider health;
- Session Context Engine — Asia/London/New York participation/context.

These modules publish evidence. They do not size lots or call the broker-write path.

Expansion/volatility may be exposed through a composite view over Candle + Quant outputs rather than duplicating their definitions in a separate authoritative engine.

## `strategies/`

Owns the initial family desks:

- Trend Pullback Continuation;
- Breakout Expansion;
- Breakout Retest Continuation;
- Liquidity Sweep Reversal;
- Failed Breakout Reversal;
- Compression Expansion.

Each consumes audited primitives and returns family-specific BUY/SELL opportunity evidence.

No strategy module may call MT5 writes, risk-reset functions or production promotion functions.

## `decisions/`

Primary responsibilities:

- independent BUY thesis;
- independent SELL thesis;
- Debate/Red Team;
- scoring/fusion/conflict/coverage;
- decision attribution and `why no trade` trace;
- persistent setup lifecycle;
- M5 entry timing;
- initial structural Trade Plan.

`WAIT`, `MISSED`, `INVALID` and safety `BLOCKED` must remain semantically distinct.

## `risk/`

Owns:

- broker-aware monetary risk;
- dynamic lot sizing;
- min-lot affordability;
- aggregate exposure;
- margin/risk policy;
- UTC risk-day accounting;
- daily-loss lock;
- governed manual reset;
- cooldown/runaway circuit policy;
- position-capacity risk result.

Risk returns authority but does not call `order_send`.

## `execution/`

This package contains the narrow irreversible boundary.

### Centralized execution permission gate

One primary component, conceptually named:

```text
ExecutionPermissionGate
```

must combine authoritative permission inputs and return:

```text
ALLOW / BLOCK / UNKNOWN
primary reason
secondary reasons
```

It must include the environment policy input (`DEMO_ALLOWED`, future explicitly approved `REAL_ALLOWED`, or `BLOCK`) and must prevent scattered ad-hoc LIVE/DEMO checks.

### Broker write adapter

The low-level MT5 write adapter owns the actual irreversible calls for:

- create/open;
- modify SL/TP;
- close.

All such calls must be reachable only through the governed execution path after required permission and lifecycle persistence.

### Order lifecycle / reconciliation

Owns:

- Execution Intent state;
- pre-submit persistence requirement;
- one irreversible send per approved intent;
- ambiguous acknowledgement classification;
- positions/orders/deals reconciliation;
- ownership of bot-managed versus manual/foreign exposure.

### Execution controller/lease

Owns the single-active-controller invariant for one managed account/symbol and safe failover after reconciliation.

## `management/`

Owns the post-entry decision floor:

- Continuation Score;
- Reversal Score;
- protection need;
- structural trailing;
- runner objective progression;
- HOLD / PROTECT / TRAIL / RUNNER / EXIT.

It proposes management actions. Actual broker modification/close still passes through `execution/`.

## `persistence/`

Primary responsibilities:

- atomic durable state;
- schema/version/integrity checks;
- risk/order/trade lifecycle persistence;
- Strategy Registry storage;
- entry/exit learning state storage;
- promotion/research history persistence;
- startup recovery;
- portable backup/restore;
- laptop migration;
- public GitHub backup artifacts according to the financial-secret policy.

Persistence stores state; it does not redefine the meaning of a strategy/risk rule.

## `research/`

Suggested owners:

- deterministic replay/validation;
- performance/opportunity research;
- entry learning;
- exit learning;
- StrategyMemory;
- governed strategy discovery;
- declarative autonomous invention;
- experiment/promotion/rollback registry.

Research cannot access the irreversible broker adapter directly. Shadow has zero broker-write authority. DEMO Canary, when authorized, still uses the normal production Risk + Execution Permission Gate.

## `operator/`

Owns presentation only:

- compact terminal dashboard;
- restrained emoji/status rendering;
- human English/Roman-Urdu explanations;
- startup/shutdown/operator workflows.

The UI never decides whether a trade is allowed.

## `diagnostics/`

Owns cross-subsystem aggregation of:

- OK/WARN/DEGRADED/BLOCKED/ERROR;
- primary/secondary faults;
- trading impact;
- recovery state/history;
- backup/controller health.

Subsystems remain authority for the faults they originate.

## Critical dependency rules

Allowed direction should remain broadly:

```text
facts → intelligence → strategies/decisions → plan
                                  ↓
                             risk/safety
                                  ↓
                     ExecutionPermissionGate
                                  ↓
                        broker write adapter
```

Persistence/diagnostics/operator observe or support these authorities without creating bypasses.

Prohibited dependencies include:

```text
strategy → raw MT5 order_send        NO
research → raw MT5 order_send        NO
dashboard → raw MT5 order_send       NO
learning → risk-limit mutation       NO
broker adapter → strategy decision   NO
```

## Public-repo / secret boundary

Code, docs, strategies, learning/research state and backup metadata may be versioned publicly under the current project policy.

Actual credentials/keys/tokens capable of unauthorized financial action or direct paid-service cost must remain outside tracked source/state artifacts.

Implementation must make this boundary easy to audit rather than scattering credentials through modules.

## Tests implied by module ownership

At minimum, tests must prove:

- strategy/research/UI cannot bypass `ExecutionPermissionGate`;
- one governed MT5 write path exists;
- DEMO/REAL environment policy has one primary code owner;
- dependency imports do not introduce raw broker-write access in prohibited modules;
- restart/migration preserves domain identity;
- reason codes remain consistent across execution, diagnostics and dashboard.

## Evolution rule

When implementation chooses actual filenames/classes/functions, this document must be updated in the same implementation phase. Do not keep fictional names after the real module structure exists.

Any later split/merge that changes behavioural ownership must also update `CODER_GUIDE.md`, relevant authoritative topic docs, tests and governance ledgers.
