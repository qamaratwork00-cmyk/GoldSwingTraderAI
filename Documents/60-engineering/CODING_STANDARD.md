# GoldSwingTraderAI — Coding Standard

**Status:** FROZEN FOR INITIAL IMPLEMENTATION
**Version:** 0.1-engineering
**Authority:** Code quality, safety, performance, typing, comments and dependencies

## Engineering objective

Write the smallest clear production-grade code that fully expresses the
documented behaviour. The target is expert code that is clean, optimized for
the real bounded workload, easy to audit and properly commented—not a large
architecture built for appearance.

## Applies to the whole repository

The rules cover runtime, MT5 adapters, intelligence, strategies, risk,
execution, persistence, dashboard, operator tools, research, scripts,
configuration and tests. A research dependency exception may change the
dependency boundary; it may not weaken chronology, determinism, safety,
secret handling or evidence quality.

## Python and dependencies

- Python 3.11+.
- Standard library first.
- Official MetaTrader5 only at the broker boundary.
- Keep the live runtime free of pandas, web frameworks, ORM, task queues and
  ML stacks unless a documented need is approved.
- Heavier research tools remain isolated from normal runtime startup.
- Every new dependency must reduce real complexity or add necessary capability.

## Functions, classes and modules

Use pure functions for deterministic calculations with explicit inputs. Use a
class only when it owns real state, resources or lifecycle: MT5 adapter,
StateStore, controller lease, Intent lifecycle, recovery coordinator or
runtime loop.

Avoid giant bot.py files and avoid hundreds of trivial wrappers. Split by
responsibility, not arbitrary line count. Do not introduce FactoryFactory,
ServiceManager or generic repository layers without a demonstrated second use
case or frozen interface requirement.

## Typed domain boundaries

Use enums for stable states, frozen dataclasses for immutable facts, slots where
useful, and typed IDs where identity matters. Normalize raw MT5/JSON/CLI data
once at the boundary:

~~~text
presence/type
→ units, symbol, direction and UTC normalization
→ finite/domain validation
→ typed fact or explicit UNKNOWN/CORRUPT
~~~

Never convert malformed external state to zero, false, empty exposure or PASS.

## Snapshot and performance rules

Build one verified cycle snapshot and share derived facts. Do not repeat MT5
reads or recompute EMA/ATR/structure in every desk. Fresh execution reads remain
mandatory where the execution contract demands them.

Use bounded histories, monotonic scheduling, no busy-wait, no repeated full
history scans without need and no dataframe construction in the live loop.
Prefer simple O(n) bounded work over risky cache complexity. Every cache must
state key, freshness and invalidation.

## Chronology and determinism

- use timezone-aware UTC internally;
- make completed versus forming candle assumptions visible;
- preserve pivot_time versus confirmed_at;
- sort tickets, events, candidates and reason codes explicitly;
- use deterministic tie-breakers;
- never depend on set/dict iteration for decision order;
- record random seeds if research randomness exists;
- never use future outcomes to build an earlier decision.

## Safety code

Execution, risk, persistence and reconciliation favour explicit boring steps.
For each durable or broker action document:

- identity and scope;
- legal previous state;
- transaction boundary;
- retry/restart behaviour;
- broker truth that can contradict local state;
- fencing/idempotency rule.

One Intent ID may send once. Ambiguity reconciles. A successful database commit
does not prove broker execution, and a broker acknowledgement does not always
prove final exposure.

## Error taxonomy

| Situation | Required treatment |
|---|---|
| invalid input | explicit validation error |
| unavailable truth | UNKNOWN/UNAVAILABLE; fail closed where required |
| corrupt state | explicit integrity/fault result |
| policy rejection | stable BLOCK reason |
| ambiguous broker result | durable unresolved Intent and reconciliation |
| programming invariant | fail loudly with context |
| shutdown | stop safely and release ownership |

No broad exception may swallow a broker, controller or recovery failure and
continue as if permission passed.

## Configuration and thresholds

Every threshold has one owner:

- frozen rule: topic contract and policy module;
- calibration value: versioned research/config;
- operational setting: validated Settings;
- technical invariant: local constant with a why-comment.

Do not read environment variables deep inside calculations or create duplicate
configuration paths.

## Comments and docstrings

Comments explain why, chronology, broker quirks, safety invariants or
non-obvious trade-offs. They do not narrate obvious syntax.

Required comment topics include no-lookahead, DEMO Guard, one-shot writes,
reconciliation, controller fencing, original-R immutability, scheduler cadence,
strict persistence and research outcome labelling.

Public/core functions and classes need concise docstrings describing purpose,
inputs/outputs and important failure semantics.

## Logging and secrets

Use structured, concise, secret-redacting logs. Log lifecycle transitions,
blocks, Intents, reconciliation, recovery and material faults; do not dump
giant market objects each cycle. Never log passwords, tokens, private keys,
PATs or paid-service credentials.

## Tests

Tests protect behaviour, not count. For a safety-sensitive change include
positive, negative, UNKNOWN, chronology, restart and boundary cases as
applicable. Fakes must not hide unsafe assumptions.

## Expert review questions

Before completion, answer:

1. Which functions are pure?
2. Which classes own state/resources?
3. What is fresh versus shared?
4. What is the time/memory/broker-call bound?
5. Are ordering and tie-breaks deterministic?
6. What happens when truth is missing or ambiguous?
7. What identity prevents duplicate durable/broker action?
8. Which exact test protects the hard boundary?
9. What comment prevents a tempting unsafe future change?
10. Which documentation graph was synchronized?

## Prohibited shortcuts

No silent fallback, score bypass of hard safety, direct MetaTrader5 import in
strategies, raw order_send outside the writer, blind retry, secret in source,
future-confirmed data, arbitrary generated code, martingale or dashboard
recalculation of authority.

