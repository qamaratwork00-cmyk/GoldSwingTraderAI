# GoldSwingTraderAI — Autonomous Strategy Invention

**Status:** PROVISIONAL  
**Version:** 0.2-implementation  
**Authority:** Safe automatic creation of declarative strategy hypotheses/candidates from audited research evidence.  
**Depends on:** `GOVERNED_STRATEGY_DISCOVERY.md`, `RESEARCH_AND_VALIDATION.md`, `LEARNING_AND_AI_BOUNDARIES.md`

## Purpose

Autonomous invention turns recurring research evidence into bounded declarative candidates. It does not self-write executable trading code, change production strategy or acquire broker authority.

> **Autonomy may invent hypotheses, not unrestricted authority.**

## Working-path requirement

A functioning invention feature requires all of the following, not merely a candidate class:

```text
outcome-labelled research episodes
→ durable journal
→ automatic approved-primitive mapping
→ recurring evidence clustering
→ candidate generation / explicit suppression reason
→ durable registry
→ validation/promotion pipeline
```

If the automatic feed is disconnected, eligible evidence silently disappears, or restart erases candidate/rejected memory, invention is considered degraded/not working.

## Approved primitive registry

Candidates may use only audited primitives exposed by `research/discovery.py`, such as structure/break/MSS, rejection/displacement/compression, technical location, liquidity sweep/FVG/OB, EMA/RSI/ATR context, session, target path and entry timing.

Unknown strings or generated executable primitives are rejected before candidate creation.

## Declarative candidate format

Each candidate records a typed ID, type, optional parent family, required/optional approved primitives, preferred regime, timing profile, invalidation model, target model, evidence lineage, fingerprint, chronology and current state.

Candidate recipes contain data only. They cannot contain `eval`, `exec`, generated Python or an MT5 call.

## Evidence-driven invention

Initial automatic triggers include repeated meaningful missed moves, false-entry clusters, premature exits, high-capture sequences and later regime-deterioration research.

Candidate creation requires repeated independent evidence. Duplicate copies of one episode do not count as multiple samples.

The inventor groups evidence by coherent trigger/direction/regime rather than randomly combining every available primitive.

## New family versus variant

Similarity against the existing six-family Strategy Floor and the durable candidate registry determines whether a hypothesis is more appropriately a `VARIANT` or a `NEW_FAMILY` research candidate.

A trivial extra RSI/FVG condition must not be mislabeled a new family. Conversely, a materially different repeated primitive pattern can be retained as a new-family challenger for validation.

## Liveness / health

Each cycle publishes:

```text
IDLE       no eligible recurring evidence yet
HEALTHY    candidate(s) created OR every eligible cluster has an explicit governed suppression reason
DEGRADED   eligible evidence could not produce either outcome
```

The system must never report `HEALTHY` merely because the module imported successfully.

## Duplicate and rejected-candidate memory

Candidate fingerprints/similarity prevent repeated duplicate creation. Rejected candidates remain durable across restart/laptop recovery, and substantially similar rejected ideas are suppressed unless materially new evidence/versioning justifies another candidate.

## Complexity control

Initial recipes cap the number of required/optional primitives. Exact bounds are research-calibratable, but the invariant is stable: prefer a few coherent primary behaviours over filter soup.

## Risk/execution boundaries

Autonomous candidates cannot set/raise account risk, bypass daily loss/news/account/session/controller safety, redefine original R, directly call MT5 or gain raw execution authority.

Every eventual DEMO candidate still uses the ordinary Trade Plan → Risk → centralized Execution path.

## Promotion boundary

Invention creates `PROPOSED` research candidates only. It cannot call itself production.

The governed lifecycle requires validation, locking, one-shot final holdout, stress, shadow, DEMO canary and `PROMOTION_READY` before explicit promotion approval. A locked candidate whose fingerprint changes must restart as a new candidate/version.

## Current implementation checkpoint — 2026-09-18

Implemented:

```text
research/episode_journal.py   durable automatic research feed
research/discovery.py         primitives/recipes/similarity/registry
research/invention.py         automatic cluster cycle + health
research/promotion.py         governed post-discovery lifecycle
```

Deterministic tests prove candidate creation from recurring evidence, restart persistence, duplicate/rejected memory, new-family/variant/policy classification, arbitrary-primitive rejection, automatic journal feed and no self-promotion.

This is software/liveness evidence; candidate market quality still requires chronological replay/validation/forward evidence.

## Dashboard visibility

At minimum, surface discovery health, eligible clusters, candidate count/latest candidate, type/stage, last suppression reason and `Broker Authority: NONE` for research/shadow candidates.

## Tests required

- eligible recurring evidence actually reaches invention automatically;
- unapproved primitive/arbitrary-code rejection;
- duplicate-family/variant/new-family classification;
- complexity limits;
- risk/execution bypass denial;
- candidate/rejected-memory persistence across restart;
- explicit suppression reasons and degraded-health detection;
- locked-candidate immutability through final holdout;
- self-promotion denial.

## Explicit non-goals

Autonomous invention must not write/deploy arbitrary strategy Python, invent risk/broker permissions, silently mutate production, use final holdout for iterative search, or claim a new family for a trivial variant.

## Open questions / calibration

- final primitive registry versioning policy;
- final similarity/complexity thresholds;
- per-trigger minimum evidence/sample requirements;
- autonomous research scheduling/CPU budget;
- richer market-behaviour clustering after the deterministic V1 baseline.
