# GoldSwingTraderAI — Governed Strategy Discovery

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Parameter discovery, strategy-recipe discovery, candidate comparison and evidence-driven market-behaviour discovery.  
**Depends on:** `RESEARCH_AND_VALIDATION.md`, `../20-trading-decisions/STRATEGY_FLOOR.md`, `LEARNING_AND_AI_BOUNDARIES.md`

## Purpose

The discovery system searches for improvements while preserving production semantics, safety boundaries and statistical discipline.

> **Discovery proposes candidates. It does not directly change production.**

## Discovery levels

### Level A — Parameter discovery

May research bounded values such as:

- score weights;
- displacement/extension thresholds;
- freshness decay;
- timing bands;
- conflict/synergy caps;
- trail/target parameters that are explicitly designated as researchable.

Hard safety invariants are not parameter-search space.

### Level B — Strategy recipe discovery

May combine approved audited primitives into a declarative market hypothesis, including:

- primary required behaviours;
- optional supporting evidence;
- conflicts/counter-evidence;
- timing profile;
- invalidation model;
- target model;
- preferred regimes.

### Level C — Market-behaviour discovery

May search repeated missed/losing/winning episode clusters for recurring behaviour not represented well by current families.

The objective is evidence-driven hypothesis generation, not random combinatorial strategy generation.

## Candidate sources

Useful discovery triggers include:

- repeated high-quality missed moves;
- repeated false-entry clusters;
- repeated premature exits;
- regime-specific family deterioration;
- recurring profitable sequences not represented by current families.

## Candidate discipline

A discovered candidate should retain:

- Candidate ID;
- parent/related family if any;
- discovery reason/hypothesis;
- declarative recipe/parameter changes;
- dataset/evidence references;
- complexity estimate;
- status and chronology.

## Duplicate/variant detection

A candidate that is merely an existing strategy plus a minor supporting primitive should normally be classified as a **variant** rather than a new family.

A genuinely new family should represent a materially different market narrative, invalidation/timing/target logic or episode structure.

## Complexity control

Candidates with many conditions/parameters receive an explicit complexity penalty/stronger evidence requirement. The system should prefer few primary behaviours plus bounded optional support over filter soup.

## Hard exclusions

Discovery may not optimize or remove:

- account identity checks;
- no-lookahead rules;
- one-shot broker submission;
- ambiguous-ack reconciliation;
- daily hard safety semantics;
- unknown broker/exposure fail-closed rules;
- original-R immutability;
- financial-secret handling.

## Candidate evaluation

All candidates must pass the research chronology owned by `RESEARCH_AND_VALIDATION.md` and promotion chronology owned by `GOVERNED_EXPERIMENTS_AND_PROMOTION.md`.

Positive development data alone is never production permission.

## Failed-candidate memory

Rejected candidates remain in durable research memory with reason/evidence so the discovery system does not repeatedly reinvent the same failed idea without materially new evidence.

## Strategy version isolation

Results are attached to strategy/policy versions. Evidence from a materially changed version must not be silently treated as identical to the prior version.

## Entry/exit discovery

Discovery may propose entry/exit policy challengers based on recurring evidence such as:

- excessive chase rejection;
- too-late breakout entries;
- premature structural trailing;
- poor runner capture.

Production entry/exit behaviour remains unchanged until governed promotion.

## Outputs

At minimum:

- discovery observation;
- hypothesis;
- Candidate ID/type;
- parent/genealogy;
- proposed declarative/parameter change;
- complexity;
- supporting/counter evidence;
- required validation path;
- current status.

## Tests required

- hard-safety fields excluded from search space;
- duplicate/variant classification;
- failed-candidate persistence;
- version isolation;
- complexity guard;
- entry/exit candidate creation without production mutation.

## Explicit non-goals

Discovery must not:

- generate/execute arbitrary Python;
- directly edit production policy;
- change risk because recent trades won/lost;
- self-promote candidates;
- randomly search unlimited condition combinations.

## Open questions

- final parameter-search bounds;
- exact complexity penalty;
- minimum independent episodes per discovery type;
- exact duplicate/new-family similarity criteria;
- exact discovery scheduling/resource limits.