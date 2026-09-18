# GoldSwingTraderAI — Module Structure

**Status:** DRAFT  
**Version:** 0.4-design  
**Authority:** File/module ownership map and dependency direction.  
**Depends on:** `CODING_STANDARD.md`, `../CODER_GUIDE.md`, `../00-foundation/ARCHITECTURE.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`

## Purpose

This is the file-oriented companion to `../CODER_GUIDE.md`. Exact filenames may evolve during implementation; ownership boundaries are the important contract.

All implementation must also satisfy the frozen source-quality/complexity rules in `CODING_STANDARD.md`.

## Design goals

- one primary code owner per behaviour;
- no raw MT5 writes from strategy/research/UI;
- no duplicated risk/news/account permission logic;
- one centralized final broker-write permission gate;
- one positive DEMO guard owner;
- one cross-machine execution-controller owner with lease/fencing;
- persistence/restart separated from trading semantics;
- research/learning isolated from production broker authority;
- modules testable without unnecessary micro-file fragmentation;
- no giant all-in-one `bot.py`;
- no speculative Service/Manager/Factory layers where a direct module/function is clearer;
- deterministic calculations should prefer pure functions;
- stateful classes should exist only for genuine resource/lifecycle/state ownership;
- verified market/broker facts and derived intelligence should be calculated once per appropriate scope and reused;
- live runtime dependencies remain minimal; heavier research dependencies stay isolated.

Typical modules will often fall around 100–300 lines, while complex authorities may reasonably reach 300–500. These are review signals, not hard limits; split only when responsibilities actually diverge.

## Planned top-level package shape

```text
goldswingtraderai/
├── app/                 runtime entrypoint/coordinator
├── domain/              immutable contracts, IDs, enums, snapshots
├── market_data/         MT5 facts, candles, quotes, history validation
├── intelligence/        candle/structure/technical/liquidity/quant/macro/session
├── strategies/          six production strategy-family desks
├── decisions/           theses, fusion, timing, Trade Plan
├── risk/                monetary risk + risk state policy
├── execution/           DEMO guard, permission gate, controller, broker writes, reconciliation
├── management/          post-entry Trade Manager
├── persistence/         state store, recovery, registry, backup/migration
├── research/            replay, validation, discovery, invention, promotion
├── operator/            dashboard/operator presentation
├── diagnostics/         health/fault aggregation and reason registry
└── tests/               executable verification
```

Do not create empty directories merely to imitate this map before responsibilities exist.

## Runtime data-flow efficiency

The preferred flow is:

```text
MT5/raw broker facts
→ normalized verified snapshot
→ shared derived intelligence
→ strategies/decisions/risk consumers
```

Do not independently query/recalculate the same facts in multiple desks when one authoritative result can be shared safely.

Execution remains an intentional exception where the execution contract requires a fresh pre-submit quote/spec/account/controller verification; optimization must never weaken freshness/safety.

## `app/`

Runtime coordinator owns orchestration only:

```text
startup
→ verified snapshot
→ parallel desks
→ strategies/theses
→ timing/plan
→ risk/session/news safety
→ execution permission
→ broker lifecycle
→ Trade Manager
→ journal/research/dashboard
```

It must not reimplement candle logic, scoring, risk formulas or broker safety.

The coordinator should remain thin; avoid turning it into a second hidden business-logic owner.

## `domain/`

Stable contracts should include concepts such as:

- Market Snapshot;
- Decision/Opportunity/Market Episode IDs;
- Trade Plan;
- Risk Result;
- Session/News Permission Result;
- DEMO Guard Result;
- Execution Permission Result;
- Execution Intent;
- Controller Lease/Epoch identity;
- trade lifecycle state;
- health/fault event;
- strategy/candidate identity/version metadata.

Domain objects should avoid direct MT5/network/database dependencies.

Use dataclasses/enums/typed IDs where they protect meaning; do not create wrappers that add no semantic value.

## `market_data/`

Owns:

- MT5 connection/read-only facts;
- account facts needed by account/environment verification;
- symbol resolution/specifications;
- Bid/Ask freshness;
- completed-candle retrieval/synchronization;
- history quality/gap checks;
- broker tradeability/session schedule facts.

Raw reads are normalized before intelligence consumes them.

Keep MT5-specific return structures near this boundary rather than leaking them into strategy/decision code.

## `intelligence/`

Suggested bounded owners:

- Candle/Structure Engine;
- Technical/Location Engine;
- Liquidity/SMC Engine;
- Indicator/Quant Engine;
- Fundamental/News Facts Adapter;
- Session Context Engine.

These publish evidence. They do not size lots or call broker writes.

Where possible, deterministic calculations should be small typed pure functions operating on the shared verified snapshot/derived inputs.

## `strategies/`

Owns the six initial desks:

- Trend Pullback Continuation;
- Breakout Expansion;
- Breakout Retest Continuation;
- Liquidity Sweep Reversal;
- Failed Breakout Reversal;
- Compression Expansion.

Each consumes audited primitives and returns family-specific BUY/SELL opportunity evidence.

No strategy module may call MT5 writes, risk-reset functions or production-promotion functions.

Strategy modules should express family logic directly; do not add framework-style inheritance/factory machinery unless multiple real implementations prove it useful.

## `decisions/`

Owns:

- independent BUY thesis;
- independent SELL thesis;
- Debate/Red Team;
- scoring/fusion/conflict/coverage;
- decision attribution / `why no trade`;
- Opportunity/Market Episode lifecycle;
- M5 Entry Timing;
- initial structural Trade Plan.

`WAIT`, `MISSED`, `INVALID` and hard-safety `BLOCKED` remain semantically distinct.

## `risk/`

Owns:

- account profile resolution;
- broker-aware all-in monetary risk;
- hybrid/dynamic lot sizing;
- minimum-lot affordability;
- margin/risk policy;
- UTC risk-day Account Safety P/L;
- daily-loss lock;
- governed manual reset;
- consecutive-loss/same-episode cooldown state;
- V1 position-capacity risk result (`0/1`).

Future multi-position aggregate-risk design is not a V1 dependency.

Risk returns authority but never calls `order_send`.

Risk/safety calculations should remain explicit and audit-friendly rather than compressed into opaque generic frameworks.

## `execution/`

This package contains the narrow irreversible boundary.

### Account / positive DEMO guard

One primary environment/account policy component verifies:

```text
connected MT5 account positively verified DEMO
→ DEMO_GUARD PASS
```

If DEMO status is not verified, broker-write permission is not granted.

V1 does not implement a separate REAL authorization/hard-block engine or alternate LIVE path. Do not scatter `if demo` logic through strategies/UI.

### Centralized Execution Permission Gate

One primary component, conceptually:

```text
ExecutionPermissionGate
```

combines authoritative inputs and returns:

```text
ALLOW / BLOCK / UNKNOWN
primary reason
secondary reasons
Would Otherwise Trade where meaningful
```

Inputs include DEMO guard, account identity, market/quote integrity, news/session, risk, position/ownership/capacity, order lifecycle/reconciliation, controller ownership and fresh execution checks.

### Broker write adapter

Owns actual irreversible MT5 calls for:

- create/open;
- modify SL/TP;
- close.

All are reachable only through the governed path after permission and required lifecycle persistence.

### Order lifecycle / reconciliation

Owns:

- Execution Intent;
- pre-submit durable persistence;
- one irreversible send per approved intent;
- ambiguous acknowledgement classification;
- positions/orders/deals reconciliation;
- ownership classification `BOT_MANAGED/MANUAL/FOREIGN_EA/UNKNOWN_OWNER`.

### Controller lease / fencing

Owns the single-active-controller invariant.

Required state/behaviour includes conceptually:

```text
ControllerInstanceID
managed account/symbol scope
current lease holder
monotonic fencing epoch
lease expiry
last renewal
```

Initial V1 renewal target is 10 seconds and TTL 30 seconds. Every irreversible write freshly verifies current holder + non-expired matching epoch.

A local-only lock is insufficient for cross-laptop safety. Standby takeover after expiry must acquire a new epoch and reconcile broker/local state before PRIMARY READY.

Execution safety code should remain intentionally direct and step-by-step. Avoid metaprogramming or generic pipelines that make irreversible-write permission hard to audit.

## `management/`

Owns post-entry decision floor:

- Continuation Score;
- Reversal Score;
- protection need;
- structural trailing;
- objective/runner progression;
- HOLD / PROTECT / TRAIL / RUNNER / EXIT;
- PRE_CLOSE mandatory flatten intent.

Management proposes actions. Actual modify/close still passes through `execution/`.

## `persistence/`

Owns:

- atomic durable critical state;
- schema/version/integrity checks;
- risk/order/trade/opportunity lifecycle persistence;
- Strategy Registry;
- learning state;
- promotion/research history;
- startup recovery;
- portable backup/restore;
- laptop migration;
- public-backup artifacts under financial-secret policy.

Storage technology is an implementation choice; semantics above are not.

Prefer the smallest persistence stack that safely satisfies atomicity, schema/versioning, recovery and portability. Do not introduce an ORM/database service unless it materially simplifies the actual requirement.

## `research/`

Suggested owners:

- deterministic replay/validation;
- performance/opportunity research;
- Entry Learning;
- Exit Learning;
- StrategyMemory;
- governed strategy discovery;
- declarative autonomous invention;
- experiment/promotion/rollback registry.

Research cannot access irreversible broker adapter directly. Shadow has zero broker-write authority. DEMO Canary still uses normal Risk + centralized Execution Permission Gate.

Research may use heavier numerical/data-science dependencies where justified, but those should not become required imports for normal live runtime startup.

## `operator/`

Owns presentation only:

- compact terminal dashboard;
- status/reason rendering;
- English/Roman-Urdu explanation;
- startup/shutdown/operator workflows.

UI never decides whether a trade is allowed.

Dashboard refresh must not trigger duplicate market analysis/order activity simply because the screen redraws.

## `diagnostics/`

Owns cross-subsystem aggregation of:

- OK/WARN/DEGRADED/BLOCKED/ERROR;
- primary/secondary faults;
- trading impact;
- recovery state/history;
- backup/controller health.

Subsystems remain authority for the faults they originate.

Diagnostics/logging should be concise and structured rather than dumping large objects every cycle.

## Critical dependency direction

Broadly:

```text
facts → intelligence → strategies/decisions → plan
                                  ↓
                         risk/session/news
                                  ↓
                    ExecutionPermissionGate
                                  ↓
                       broker write adapter
```

Persistence/diagnostics/operator support/observe without bypassing authority.

Prohibited dependencies:

```text
strategy → raw MT5 order_send        NO
research → raw MT5 order_send        NO
dashboard → raw MT5 order_send       NO
learning → risk-limit mutation       NO
broker adapter → strategy decision   NO
```

## Public-repo / secret boundary

Code, docs, strategies, learning/research state and recovery metadata may be versioned publicly under project policy.

Credentials/keys/tokens capable of unauthorized financial action, authenticated account control or direct paid-service cost remain outside tracked artifacts and are checked by secret scanning.

## Tests implied by module ownership

At minimum prove:

- strategy/research/UI cannot bypass `ExecutionPermissionGate`;
- one governed MT5 write path exists;
- positive DEMO guard has one primary code owner;
- prohibited modules do not gain raw write access;
- position ownership/capacity is respected;
- controller lease/fencing prevents simultaneous writers/stale epoch writes;
- restart/migration preserves domain identity and critical lifecycle;
- reason codes remain consistent across execution, diagnostics and dashboard;
- shared snapshot/derived-fact reuse does not weaken fresh-execution checks;
- live runtime can start without optional heavy research dependencies.

## Module quality review

Before a phase closes, apply the `CODING_STANDARD.md` quality gate to affected modules. Review specifically for duplicate MT5 reads/calculations, unnecessary abstraction, dead code, mixed responsibilities, scattered magic constants, silent exception handling, needless runtime dependencies and comments that fail to explain important safety/chronology decisions.
