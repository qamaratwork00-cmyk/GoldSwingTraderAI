# GoldSwingTraderAI — Coding Standard

**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Version:** 1.0  
**Authority:** Source-code quality, complexity, dependency, commenting, performance and maintainability rules for V1 implementation.  
**Depends on:** `../00-foundation/SYSTEM_CONTRACT.md`, `MODULE_STRUCTURE.md`, `../CODER_GUIDE.md`

## Purpose

GoldSwingTraderAI must be production-grade without becoming architecturally heavy.

> **Implement the minimum clear code that fully expresses the required behaviour and safety. No clever shortcuts, no decorative complexity, no duplicate calculations, and no unnecessary abstraction.**

This standard applies to ChatGPT, coding agents and human contributors.

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

## Comments and docstrings

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