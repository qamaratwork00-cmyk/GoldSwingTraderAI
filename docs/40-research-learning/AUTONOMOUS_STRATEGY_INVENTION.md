# GoldSwingTraderAI — Autonomous Strategy Invention

**Status:** PROVISIONAL  
**Version:** 0.3-implementation  
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

If automatic feed is disconnected, eligible evidence silently disappears, or restart erases candidate/rejected memory, invention is degraded/not working.

## Approved primitive registry

Candidates may use only audited `ApprovedPrimitive` values exposed by `research/discovery.py`.

Current registry includes structural/break/MSS/rejection/displacement/compression, technical location, liquidity sweep/FVG/OB, EMA/RSI/ATR, session, target path, entry timing and explicit optional confluence primitives:

```text
TRENDLINE
FIBONACCI
VOLUME_PROFILE_POC
```

These confluence primitives exist so research can test whether recurring Trendline/Fib/POC evidence genuinely adds value. Their presence in the registry does **not** make them mandatory production filters or grant a distinct production strategy automatically.

Unknown strings or generated executable primitives are rejected before candidate creation.

## Declarative candidate format

Each candidate records typed ID, type, optional parent family, required/optional approved primitives, preferred regime, timing profile, invalidation model, target model, evidence lineage, fingerprint, chronology and current state.

Candidate recipes contain data only. They cannot contain `eval`, `exec`, generated Python or MT5 calls.

## Evidence-driven invention

Initial automatic triggers include repeated meaningful missed moves, false-entry clusters, premature exits, high-capture sequences and later regime-deterioration research.

Candidate creation requires repeated independent evidence. Duplicate copies of one episode do not count as multiple samples.

The inventor groups evidence by coherent trigger/direction/regime rather than randomly combining every available primitive.

## New family versus variant

Similarity against the existing six-family Strategy Floor and durable candidate registry determines whether a hypothesis is more appropriately a `VARIANT` or `NEW_FAMILY` research candidate.

A trivial extra RSI/FVG/Trendline/Fibonacci/POC condition must not be mislabeled a new family. Conversely, a materially different repeated primitive pattern may become a new-family challenger for validation.

## Liveness / health

Each cycle publishes:

```text
IDLE       no eligible recurring evidence yet
HEALTHY    candidate(s) created OR every eligible cluster has explicit governed suppression reason
DEGRADED   eligible evidence could not produce either outcome
```

The system must never report `HEALTHY` merely because the module imported successfully.

## Duplicate and rejected-candidate memory

Candidate fingerprints/similarity prevent repeated duplicate creation. Rejected candidates remain durable across restart/laptop recovery, and substantially similar rejected ideas are suppressed unless materially new evidence/versioning justifies another candidate.

## Complexity control

Initial recipes cap required/optional primitives. Prefer a few coherent primary behaviours over filter soup.

This applies strongly to confluence: availability of Trendline + Fibonacci + POC is not permission to invent a large mandatory checklist. More conditions require stronger out-of-sample evidence and Opportunity Recall/trade-frequency review.

## Risk/execution boundaries

Autonomous candidates cannot set/raise account risk, bypass daily loss/news/account/session/controller safety, redefine original R, directly call MT5 or gain raw execution authority.

Every eventual DEMO candidate still uses ordinary Trade Plan → Risk → centralized Execution path.

## Promotion boundary

Invention creates `PROPOSED` research candidates only. It cannot call itself production.

The governed lifecycle requires validation, locking, one-shot final holdout, stress, Shadow, DEMO Canary and `PROMOTION_READY` before explicit promotion approval. A locked candidate whose fingerprint changes must restart as a new candidate/version.

## Current implementation checkpoint — 2026-09-18

Implemented:

```text
research/episode_journal.py   durable automatic research feed + primitive mapping
research/discovery.py         primitive registry/recipes/similarity/CandidateRegistry
research/invention.py         automatic cluster cycle + health
research/promotion.py         governed post-discovery lifecycle
```

Deterministic tests prove:

- candidate creation from recurring evidence;
- restart persistence;
- duplicate/rejected memory;
- new-family/variant/policy classification;
- arbitrary/unapproved primitive rejection;
- automatic journal feed;
- Trendline/Fibonacci/POC evidence maps to explicit audited primitives;
- no self-promotion.

This is software/liveness evidence; candidate market quality still requires chronological replay/validation/forward evidence.

## Dashboard visibility

At minimum, surface discovery health, eligible clusters, candidate count/latest candidate, type/stage, last suppression reason and `Broker Authority: NONE` for research/shadow candidates.

## Tests required

- eligible recurring evidence actually reaches invention automatically;
- unapproved primitive/arbitrary-code rejection;
- explicit Trendline/Fibonacci/POC primitive mapping;
- duplicate-family/variant/new-family classification;
- complexity limits;
- risk/execution bypass denial;
- candidate/rejected-memory persistence across restart;
- explicit suppression reasons and degraded-health detection;
- locked-candidate immutability through final holdout;
- self-promotion denial.

## Explicit non-goals

Autonomous invention must not write/deploy arbitrary strategy Python, invent risk/broker permissions, silently mutate production, use final holdout for iterative search, claim a new family for a trivial variant, or convert optional confluence into mandatory production gating without governed evidence.

## Open questions / calibration

- final primitive registry versioning policy;
- final similarity/complexity thresholds;
- per-trigger minimum evidence/sample requirements;
- autonomous research scheduling/CPU budget;
- richer market-behaviour clustering;
- whether Trendline/Fibonacci/POC combinations have distinct out-of-sample edge or should remain supporting context.
