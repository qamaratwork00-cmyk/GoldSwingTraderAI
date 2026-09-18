# GoldSwingTraderAI — Autonomous Strategy Invention

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Safe autonomous creation of declarative strategy hypotheses/candidates from audited primitives.  
**Depends on:** `GOVERNED_STRATEGY_DISCOVERY.md`, `RESEARCH_AND_VALIDATION.md`, `LEARNING_AND_AI_BOUNDARIES.md`

## Purpose

Autonomous invention may propose new strategy recipes from recurring market evidence, but it may not self-write executable trading code or bypass the governed validation/promotion path.

> **Autonomy may invent hypotheses, not unrestricted authority.**

## Approved primitive registry

Autonomous candidates may use only approved audited primitives exposed by the documented system, such as:

- structure/swing/BOS/MSS facts;
- candle/rejection/displacement/compression evidence;
- technical zones/location;
- liquidity pools/sweeps/FVG/OB/premium-discount;
- EMA/RSI/ATR/volatility/momentum evidence;
- session/macro context;
- target/path evidence;
- approved timing/invalidation/target models.

Unknown executable primitives are rejected.

## Declarative candidate format

A strategy candidate should describe, at minimum:

```text
Strategy/Candidate ID
Name / narrative
Parent/genealogy
Required behaviours
Optional supporting evidence
Counter-evidence/conflicts
Preferred regime
Timing profile
Invalidation model
Target model
Expiry/staleness logic
Discovery reason/evidence
```

The production interpreter executes audited primitives; the candidate does not contain arbitrary executable source code.

## Evidence-driven invention

Preferred invention flow:

```text
repeated observation/cluster
→ hypothesis
→ declarative candidate
→ research validation
```

The inventor should not generate thousands of random combinations without evidence.

Useful triggers include:

- large moves repeatedly missed by current families;
- recurring failure patterns;
- repeated high-capture market sequences;
- unrepresented regime behaviour.

## New family versus variant

Before declaring a new family, compare with the existing Strategy Floor.

A candidate that is effectively `Trend Pullback + extra RSI support` is a variant, not automatically a new production family.

A new family requires a materially distinct market narrative or timing/invalidation/target structure.

## Complexity control

Prefer a small number of primary behaviours plus optional support. Candidates that require many simultaneous conditions should receive stronger complexity penalties/evidence requirements.

The autonomous system must not recreate filter soup.

## Risk/execution boundaries

Autonomous strategies may describe structural invalidation and market targets, but may not:

- set/raise account risk;
- bypass daily loss/news/account/broker safety;
- change broker retry semantics;
- directly call MT5;
- acquire execution-controller authority.

All candidates use the same Trade Plan → Risk → Execution pipeline as governed strategies.

## No arbitrary code generation

The production autonomous invention design prohibits candidate execution through arbitrary generated Python or equivalents such as unrestricted `eval`, `exec` or dynamic source compilation.

A new primitive that requires new code is an engineering/design change and must be implemented/tested through normal governance.

## Persistent candidate registry

Autonomous candidates are durable and machine-independent. Persist:

- Candidate ID and genealogy;
- recipe/version;
- created time/reason;
- validation/promotion stage;
- performance/evidence references;
- rejection reason if failed.

Restart/laptop migration must not erase autonomous work.

## Rejected-candidate memory

Rejected candidates remain stored so the inventor can detect substantially similar prior failures. A rejected idea may be reconsidered only when materially new evidence or changed primitives justify a new candidate/version.

## Promotion boundary

Autonomous invention cannot self-promote. The candidate must pass research, final holdout, stress, shadow and DEMO canary gates defined elsewhere.

## Dashboard visibility

Compact example:

```text
Autonomous Lab   HEALTHY
Candidate        AUTO-021
Type             VARIANT / NEW FAMILY
Stage            VALIDATING
Broker Authority NONE
```

## Tests required

- unapproved primitive rejection;
- arbitrary-code rejection;
- duplicate-family/variant detection;
- complexity limits;
- risk/execution bypass attempts denied;
- candidate persistence/genealogy across restart/migration;
- rejected-candidate memory;
- self-promotion denial.

## Explicit non-goals

Autonomous invention must not:

- write/deploy arbitrary trading Python;
- invent broker/risk permissions;
- mutate production silently;
- use final holdout for iterative search;
- call itself a new family when it is only a trivial variant.

## Open questions

- exact declarative recipe grammar/schema;
- approved primitive registry versioning;
- similarity threshold for duplicate/variant detection;
- complexity bounds;
- autonomous discovery compute/scheduling limits.