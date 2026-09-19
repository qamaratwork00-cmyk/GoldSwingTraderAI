# GoldSwingTraderAI — Coding Standard

**Status:** FROZEN FOR INITIAL IMPLEMENTATION
**Version:** 1.2
**Authority:** Source-code quality, complexity, dependency, commenting, performance and maintainability rules for all maintained project code, with the V1 production-runtime baseline frozen below.
**Depends on:** `../00-foundation/SYSTEM_CONTRACT.md`, `MODULE_STRUCTURE.md`, `../CODER_GUIDE.md`

## Purpose

GoldSwingTraderAI must be production-grade without becoming architecturally heavy.

> **Implement the minimum clear code that fully expresses the required behaviour and safety. No clever shortcuts, no decorative complexity, no duplicate calculations, and no unnecessary abstraction.**

This standard applies to ChatGPT, coding agents and human contributors.

## Project-wide applicability

This is the engineering standard for the **whole maintained repository**, not
only the live trading loop. The same quality principles apply to:

| Code area | Required treatment |
|---|---|
| `src/` runtime, broker, risk, execution, persistence, dashboard and operator code | Full production-grade rules, especially safety, chronology, bounded work and explicit failure handling |
| `src/research/` and research/replay tooling | The same typing, chronology, determinism and auditability rules; heavier research dependencies are allowed only within the documented runtime boundary |
| `scripts/` and operator CLIs | Deterministic, validated inputs, safe failure, secret-safe output and restart/retry-aware behaviour where applicable |
| `tests/`, fixtures and fakes | Clear contract-focused tests that do not hide unsafe production assumptions behind unrealistic mocks |
| configuration, migration, backup, restore and diagnostic code | Explicit schemas, validation, idempotency and evidence-preserving failure behaviour |
| executable examples or maintained tooling outside these folders | The same rules unless a documented, approved exception names the reason and boundary |

Scope-specific differences do not create a loophole. For example, a research
module may use pandas while an equivalent live-runtime module may not, but both
must preserve chronology, deterministic ordering, explicit missing-data
semantics and reproducible evidence. Documentation itself is governed by
`docs/90-governance/DOCUMENTATION_STANDARD.md`; code examples inside docs must
still follow this standard.

## Core engineering style

The V1 codebase is **lightweight production Python**:

- readable before clever;
- explicit before magical;
- small cohesive modules instead of one giant `bot.py`;
- no unnecessary service/factory/manager layers;
- strong typing and domain models where they improve correctness;
- pure deterministic calculations where practical;
- stateful classes only where real ownership/lifecycle/state exists;
- runtime dependencies kept intentionally small;
- safety-critical behaviour remains easy to audit.

Do not optimize for shortest source-code length. Optimize for **clarity, correctness, low operational friction and easy debugging**.

## Python baseline

V1 targets **Python 3.11+**.

Use modern standard-library features where they reduce complexity. Prefer built-in types and standard-library functionality before adding a dependency.

The official `MetaTrader5` Python package is the broker-terminal integration dependency. `python-dotenv` or an equivalent very small configuration helper may be used for local environment loading.

A new runtime dependency must earn its place by materially reducing risk/complexity or providing a capability that would be unreasonable to implement safely in-project.

## Runtime dependency policy

### Live/runtime core

Keep the trading runtime lean.

Preferred baseline:

```text
Python standard library
+ MetaTrader5
+ minimal configuration helper
```

Do **not** add pandas, a web framework, ORM, task queue, distributed framework or ML stack to the live runtime merely for convenience.

`numpy` may be introduced only where a measured or clearly substantial numerical benefit justifies it. Simple EMA/RSI/ATR/rolling calculations do not automatically justify a heavy dependency.

### Research side

Research/replay tooling may use heavier analytical libraries such as NumPy, pandas, SciPy or ML/statistical packages when they materially improve research quality. Those dependencies should remain isolated so the normal trading runtime does not require the entire research stack.

## Domain modelling

Use:

- `Enum` for stable bounded states/reason categories;
- `dataclass` for clear data contracts;
- `frozen=True` for genuinely immutable facts/contracts;
- `slots=True` where useful for frequently-created stable domain objects;
- explicit typed IDs/value objects where identity mistakes would be costly.

Do not wrap every primitive in a class. Add a type/domain object when it protects semantics, identity or invariants.

## Functions versus classes

Prefer a pure function when the operation is:

- deterministic;
- stateless;
- easy to express from explicit inputs to explicit outputs.

Examples include indicator calculations, normalized ratios, RR calculations, scoring transforms and many structure helpers.

Use a class when the component owns real state/resources/lifecycle, such as:

- MT5 connection adapter;
- Opportunity lifecycle store/coordinator;
- risk state machine;
- persistence store;
- controller lease;
- execution lifecycle/reconciliation;
- dashboard runtime.

Do not create a class merely to hold one function.

## Module/file size and structure

Avoid both extremes:

- one multi-thousand-line `bot.py`;
- hundreds of tiny files with one trivial function each.

Typical cohesive modules will often be roughly **100–300 lines**. A complex authority may reasonably reach **300–500 lines**. These are review signals, not arbitrary hard limits.

When a module becomes difficult to reason about, test or review, split it by genuine responsibility—not by line count alone.

Do not create empty folders/classes/interfaces merely because an architecture diagram mentions them.

## No unnecessary abstraction

Do not introduce patterns such as:

```text
FactoryFactory
ServiceManager
AbstractProviderWrapper
GenericRepositoryInterface
```

unless the implementation has an actual demonstrated need for interchangeable implementations or lifecycle ownership.

One clear concrete implementation is preferable to speculative abstraction.

Abstract only after the second real use case or when an already-frozen contract requires an interface boundary for testing/safety.

## Market snapshot and calculation reuse

The runtime should build a verified market/broker snapshot and share it across consumers for that decision cycle.

Do not repeatedly query MT5 or recalculate the same EMA/ATR/structure/liquidity facts independently in multiple desks.

Preferred pattern:

```text
verified raw facts
→ one normalized snapshot
→ derived intelligence calculated once per required scope
→ shared immutable/read-only results consumed by strategies/decisions
```

A fresh broker read is still required where the execution contract explicitly demands fresh pre-submit facts. Reuse must never weaken freshness requirements.

## Performance policy

Optimize architecture before micro-optimizing syntax.

Required principles:

- bounded rolling histories in live runtime;
- no busy-wait loops;
- no repeated full-history scans when incremental/bounded calculation is sufficient;
- avoid unnecessary object/dataframe creation on every tick;
- cache/reuse derived facts within a decision snapshot where safe;
- separate dashboard refresh frequency from strategy/execution triggering;
- measure before introducing complex low-level optimization.

A simpler O(n) calculation on a small bounded M5 window may be better than a complicated cache that risks stale trading state.

Correctness and chronology always beat a premature speed optimization.

## Expert-level implementation rules

The standard above describes the style. The rules below describe how to make
that style reliable in a safety-sensitive runtime.

### Design before code

Before changing a module, write down the smallest contract that answers:

| Question | Required answer |
|---|---|
| What problem is being solved? | one sentence tied to an authoritative document |
| What are the inputs? | typed values, freshness and timezone/chronology assumptions |
| What is the output? | typed result, state transition or durable event |
| Who owns the rule? | exactly one module or authority |
| What is unknown/failure? | explicit decision/fault, never a convenient default |
| What is the cost? | expected time, memory, broker calls and persistence writes |
| How is it proved? | focused tests plus the relevant integration/recovery evidence |

If the answers are unclear, improve the contract or documentation before
adding code. A short implementation built on an unclear boundary becomes
expensive safety debt.

### Immutable facts and logical parallelism

Build one verified snapshot for a cycle and pass it into independent
calculators. Prefer frozen dataclasses, tuples and new result values over
in-place mutation. A function that receives a market snapshot must not reach
into a global MT5 client, read the clock unexpectedly or mutate the snapshot.

Independent intelligence/strategy functions may be evaluated sequentially for
determinism. They are logically parallel only when each can be run from the
same inputs without hidden ordering. Fusion, timing, Trade Plan, risk,
permission, intent and broker reconciliation are ordered authorities and must
remain visibly ordered in code.

### Complexity and resource budgets

Use the simplest algorithm that meets the bounded live workload. Treat these as
review budgets, not invitations to premature micro-optimization:

| Area | Default budget | Review trigger |
|---|---|---|
| Live candle history | bounded per timeframe/configuration | an unbounded list or full-history scan |
| Per-cycle broker reads | one shared snapshot plus explicitly fresh execution reads | duplicate reads from multiple desks |
| Per-cycle derived calculations | one calculation per evidence scope | repeated EMA/ATR/structure recomputation |
| Scheduling | one sleep/wakeup mechanism with monotonic timing | busy-wait or nested polling loops |
| Dashboard | read-only mapping at a lower cadence than trading | dashboard work delaying a cycle |
| Persistence | one clear transaction per lifecycle transition | partial multi-record updates |
| Research | heavier/offline computation allowed | research dependency imported by live startup |

Prefer O(n) over bounded n when it is easier to audit. Introduce an incremental
algorithm, cache or specialized data structure only after measuring a real
cost or when the data contract makes the bound necessary. Every cache must
state its key, freshness, invalidation rule and whether stale data is safe.

### Deterministic ordering

For identical facts, policy version and clock, results must be identical:

- sort broker tickets, events, candidates and evidence labels explicitly;
- never depend on set/dict iteration for decision order;
- use UTC-aware datetimes and explicit tie-breakers;
- do not use random values in production decisions without a recorded seed and
  an explicit research contract;
- keep reason-code ordering stable so dashboards, logs and tests are comparable;
- make first-match/last-match semantics visible instead of relying on incidental
  loop order.

### Chronology and time

Every time-sensitive function must state whether it uses:

- the latest completed candle;
- a forming candle for display only;
- the broker quote captured at a particular UTC instant;
- the risk-day clock;
- a scheduled session/news timestamp.

Use timezone-aware UTC internally. Reject naive datetimes at boundaries. Never
use a future-confirmed swing, future event result, later candle high/low or
post-entry outcome while constructing an earlier decision. Replay and live code
must share the same chronology semantics.

### Boundary normalization

Normalize untrusted external data once at the boundary:

1. verify presence and type;
2. normalize units, direction, symbol, timestamp and optional fields;
3. validate domain invariants;
4. return a typed fact or explicit unavailable/corrupt result;
5. keep the raw external shape out of business-rule modules.

Do not scatter defensive conversions through every consumer. Do not convert
missing, corrupt or unavailable broker truth into zero, false, empty exposure
or a passing permission.

Persisted JSON is also an external boundary: a restart, checkpoint or backup
may contain valid-looking but incorrectly typed values. Runtime restore code
must preserve JSON types instead of coercing arbitrary strings/numbers through
`str(...)`, `int(...)`, `float(...)` or `bool(...)`. Required booleans and
integers must be type-checked, numeric values must be finite, optional values
must preserve explicit `null`, and malformed state must raise an explicit
integrity error. In V1 this rule is enforced at the critical restore owners:
`persistence/runtime_state.py`, `execution/intent_store.py`,
`management/store.py`, `research/episode_journal.py` and the discovery-status
repository. Portable checkpoint/catalog, candidate/promotion registry, dataset
bundle and evidence-package parsers follow the same rule. The domain model
remains the final invariant check after parsing.

### Error and fault taxonomy

Use the narrowest useful error/result category:

| Situation | Required behaviour |
|---|---|
| invalid caller input | raise/return a clear validation failure at the boundary |
| unavailable external truth | return UNKNOWN/UNAVAILABLE and fail closed where required |
| corrupt external data | return DATA_CORRUPT with diagnostic context; never continue as valid |
| policy rejection | return a stable BLOCK reason, not an exception used as normal control flow |
| broker acknowledgement ambiguity | persist unresolved intent and reconcile; never blind-retry |
| invariant/programming defect | fail loudly with context and preserve durable state |
| shutdown/cancellation | stop at a safe boundary and report whether authority was released |

Catch an exception only if the module can add useful context or convert it to a
safe typed result. Preserve the original cause when re-raising. Never catch
Exception around a broker write, recovery transaction or controller check and
then continue.

### Configuration and policy ownership

Every threshold must have one owner and one source:

- frozen V1 rule → authoritative contract and its policy module;
- calibration value → versioned research/config input with evidence;
- operational setting → validated Settings/environment field;
- technical invariant → local constant with a comment explaining why it is
  invariant.

Do not read environment variables deep inside a calculation. Do not let a
dashboard option, candidate recipe or runtime convenience override a frozen
hard safety policy.

### Persistence and idempotency

For every durable transition, define:

- identity key and scope;
- legal previous states;
- new state/event;
- transaction boundary;
- retry/restart behaviour;
- checksum/schema version where portable;
- what broker truth can still contradict it.

An operation that can be retried after a crash must be idempotent or carry an
intent/fencing identity that makes duplicate action impossible. A successful
database commit is not proof of broker execution; a broker acknowledgement is
not proof of final exposure.

### Comments and docstrings

Comments must explain **why**, invariants, non-obvious market/broker behaviour, safety constraints or chronology—not narrate obvious syntax.

Good:

```python
# Structural confirmation may use completed candles only.
# Including the forming candle would break live/replay chronology parity.
confirmed = candles[:-1]
```

Avoid:

```python
# Increment counter by one.
counter += 1
```

Public/core APIs and important domain components should have concise docstrings covering purpose and any non-obvious contract.

Safety-sensitive sections should document the reason behind the guard, especially:

- no-lookahead boundaries;
- one-shot broker writes;
- reconciliation;
- DEMO guard;
- controller fencing;
- immutable original R;
- critical persistence behaviour.

Do not fill files with decorative comments that make the actual logic harder to scan.

### Comment requirements by code type

| Code | Required documentation |
|---|---|
| public function/class | purpose, inputs/outputs and the important invariant or failure result |
| pure market/risk calculation | units, chronology, edge cases and why the formula is appropriate |
| broker adapter | raw-to-domain mapping, missing-value semantics and broker quirk |
| execution/reconciliation | one-shot/idempotency rule, freshness requirement and ambiguity path |
| persistence transition | identity/scope, transaction reason and restart behaviour |
| scheduler/loop | cadence, clock choice, stop condition and fail-closed behaviour |
| research metric/replay | chronology, outcome labeling and what it must not claim |
| non-obvious branch | why the branch is necessary and which contract it protects |

Docstrings should be short enough to remain accurate. Update them when a
contract changes. Comments must not describe a line of syntax that a competent
reader can already see; they should protect the reader from a wrong but
tempting change.

## Naming

Names should describe domain meaning directly.

Prefer:

```text
approved_entry_reference
structural_stop
execution_intent_id
spread_ratio
controller_epoch
```

over vague names such as:

```text
data2
manager
handler2
value_x
helper_final
```

Avoid unnecessary abbreviations except stable trading/domain terms such as `SL`, `TP`, `RR`, `ATR`, `EMA`, `MFE`, `MAE` where their meaning is already project-standard.

## Configuration and constants

Trading/risk/session thresholds belong in a clear configuration/policy owner, not scattered magic numbers throughout source files.

Implementation constants that are true technical invariants may remain near their owner when that improves readability.

Research-calibrated values must be explicit/versioned/configurable according to the authoritative research/governance contracts.

Never create a second hidden config path for the same rule.

## Error handling

Errors must be explicit and actionable.

Do not use broad silent exception handling such as:

```python
try:
    ...
except Exception:
    pass
```

Boundary code may catch broad exceptions only when it immediately converts them into an explicit safe fault/recovery state, preserves diagnostics and cannot accidentally continue as if facts were valid.

Critical financial/broker/order/controller truth must never fall back to a convenient default.

Use stable reason/fault codes for machine behaviour and concise human explanations for logs/dashboard.

## Logging

Logging should be structured, concise and useful for reconstruction.

Do not log giant market objects every cycle or spam repeated identical messages.

Logs must never expose financial-authority credentials/tokens/private keys.

Prefer significant lifecycle events, state transitions, decisions, safety blocks, execution intents/results, reconciliation and faults over noisy per-line trace output.

## MT5 boundary

Raw MT5 reads belong in the market/broker adapter layer. Raw irreversible MT5 writes belong only in the governed execution adapter/path.

Do not leak MT5-specific return structures deep into strategy/decision code. Normalize broker facts near the adapter boundary into project domain models.

Do not hide broker errors behind generic booleans when the return code/reason materially affects recovery.

## Safety code must remain boring

Execution, risk, reconciliation and persistence safety should favor explicit step-by-step logic over compact clever expressions.

An auditor should be able to follow:

```text
input facts
→ invariant checks
→ result/reason
```

without reconstructing metaprogramming or implicit magic.

No dynamic `eval`, `exec`, runtime code generation or plugin-style arbitrary trading-code loading is allowed by this standard.

## Testing style

Tests protect behaviour and invariants; they are not a test-count competition.

Prefer:

- deterministic focused unit tests for pure calculations;
- contract/state-transition tests for risk/execution/persistence;
- positive + negative strategy fixtures;
- regression tests for every material bug;
- fault-injection around irreversible broker lifecycle;
- no-lookahead chronological fixtures.

Avoid tests that merely mirror implementation line-by-line without protecting meaningful behaviour.

Mocks/fakes should be used at external boundaries, not to mock every internal function.

## Verification and code-review checklist

Every material change should be reviewed in this order:

1. **Contract:** Is the authoritative document and single rule owner clear?
2. **Data:** Are inputs typed, normalized, fresh enough and chronology-safe?
3. **Purity:** Does a calculation avoid hidden I/O, global mutation and duplicate
   broker reads?
4. **Safety:** Can unknown, corrupt, stale or ambiguous truth accidentally pass?
5. **Authority:** Is the change placed before/after the correct gate, and can it
   reach the writer through only the intended path?
6. **Durability:** Does restart, retry, takeover or partial failure leave a
   reconstructable state?
7. **Performance:** Is the work bounded, measured where relevant and free of
   unnecessary allocations/queries?
8. **Observability:** Are reason codes, structured logs, dashboard fields and
   health impact sufficient to reconstruct the result without secrets?
9. **Tests:** Are positive, negative, unknown, boundary, chronology and
   interruption cases covered?
10. **Documentation:** Are the module map, coder guide, topic authority,
    testing/release docs and open questions synchronized?

The minimum verification command set for a code checkpoint is:

    PYTHONPATH=src python -m pytest -q
    PYTHONPATH=src python -m ruff check src tests scripts
    PYTHONPATH=src python -m compileall -q src tests scripts
    git diff --check
    PYTHONPATH=src python scripts/scan_financial_secrets.py .

The CI workflow additionally runs the source/script annotation contract and
publishes a `pytest-cov` report as an artifact. Coverage is an engineering
signal, not a substitute for controlled Windows MT5, broker, failover or DEMO
evidence; no coverage percentage alone can promote a release.

Passing these commands proves repository-level software quality only. It does
not prove broker connectivity, multi-machine fencing, real DEMO execution,
profitability or a fresh-machine recovery drill.

## Research/runtime separation

The research system may be computationally heavier, but production trading must not depend on research running successfully in real time unless an authoritative contract explicitly requires that dependency.

Research outputs consumed by production should be compact, versioned, validated artifacts/policies rather than an uncontrolled heavy notebook/dataframe pipeline inside the trading loop.

## Refactoring rule

Do not perform cosmetic rewrites during a phase unless they materially improve correctness, readability or reduce real complexity.

Before adding a new abstraction, dependency or layer, ask:

1. Does the current requirement actually need it?
2. Does it reduce total complexity?
3. Does it make testing/safety clearer?
4. Will a simpler function/dataclass/module work?

If the simpler design is sufficient, use it.

## Phase quality gate

Before a phase is considered complete, review its code for:

- duplicate calculations/MT5 reads;
- dead code;
- unnecessary abstraction;
- oversized mixed-responsibility modules;
- scattered magic constants;
- vague names;
- missing safety/chronology comments;
- broad/silent exception handling;
- needless runtime dependencies;
- logs that are too noisy or leak sensitive data;
- tests that miss the frozen invariant.

Then run the required tests and synchronize documentation.

## Explicit non-goals

V1 does **not** aim to become:

- an enterprise microservice platform;
- a generic multi-broker framework before one is required;
- a dependency-heavy data-science runtime;
- a design-pattern showcase;
- a single-file script that mixes every authority;
- a clever code-golf project.

## Change rule

This coding standard is **FROZEN FOR INITIAL IMPLEMENTATION**. A material relaxation or architectural expansion requires an explicit later Design Decision with rationale. Research calibration may change trading parameters without changing this engineering standard.
