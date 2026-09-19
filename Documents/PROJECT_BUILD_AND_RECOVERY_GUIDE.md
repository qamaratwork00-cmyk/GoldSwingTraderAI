# GoldSwingTraderAI — Project Build and Recovery Guide

**Status:** CANDIDATE FOR ADOPTION
**Version:** 0.1-agent-guide
**Authority:** AI/developer build sequence, context recovery and safe continuation

## Purpose

This guide tells an implementation agent how to work on the project without
guessing, restarting or silently damaging a safety boundary. It is a process
guide. Trading behaviour remains in the topic contracts.

## Agent loop

~~~mermaid
flowchart TB
    ORIENT["Read index and contract"] --> SCOPE["Choose one phase/feature"]
    SCOPE --> TRACE["Find authority, source, entry point and tests"]
    TRACE --> DESIGN["State inputs, outputs, failure, persistence and authority"]
    DESIGN --> IMPLEMENT["Small typed deterministic change"]
    IMPLEMENT --> VERIFY["Focused + integration + quality checks"]
    VERIFY --> SYNCHRONIZE["Update affected documentation graph"]
    SYNCHRONIZE --> HANDOFF["Record proof, limits and next incomplete phase"]
~~~

Never jump from a feature request directly to a broker adapter.

## Source-of-truth reading order

1. Documents/README.md.
2. Documents/90-governance/DOCUMENTATION_STANDARD.md.
3. Documents/00-foundation/SYSTEM_CONTRACT.md.
4. Relevant topic contract.
5. Documents/90-governance/DESIGN_DECISIONS.md.
6. Documents/90-governance/OPEN_QUESTIONS.md.
7. Documents/60-engineering/CODING_STANDARD.md.
8. Documents/60-engineering/MODULE_STRUCTURE.md.
9. Documents/CODER_GUIDE.md.
10. Current code, tests, state schema and executable evidence.

If documents conflict, stop the affected implementation and repair the
authority before coding.

## What a phase packet contains

| Packet part | Minimum content |
|---|---|
| contract | purpose, inputs, outputs, states and authority |
| architecture | dataflow and parallel/ordered diagram |
| implementation | exact source owner and public entry point |
| failure | unavailable, stale, corrupt, ambiguous and retry semantics |
| persistence | identity, transaction, restart and migration effect |
| tests | positive, negative, UNKNOWN, chronology and fault cases |
| operator | dashboard/reason/action visibility |
| research | replay/metric/evidence effect |
| release | software versus external evidence classification |
| documentation | all affected destinations and retained rationale |

## Frozen documentation completeness process

The highlighted issue is an example, not the whole scope. Audit:

~~~text
requirement
→ authority
→ phase
→ architecture
→ source/entry point
→ model/state
→ persistence/restart
→ tests
→ dashboard/operator
→ research/replay
→ setup/manual/prompt
→ release/open questions
~~~

An implementation phase is not complete while a known code/docs/test
contradiction remains.

## If context is lost

~~~text
inspect tree and branch
→ read Documents/README.md
→ read SYSTEM_CONTRACT.md
→ read affected topic
→ inspect DESIGN_DECISIONS and OPEN_QUESTIONS
→ inspect current code/tests/commits
→ find last verified phase
→ continue at first incomplete dependency
~~~

Repository truth beats remembered conversation wording.

## If implementation is interrupted

1. Classify each deliverable DONE, PARTIAL, MISSING or BROKEN.
2. Preserve uncommitted changes and inspect the diff.
3. Finish the smallest missing dependency.
4. Run focused tests before broad tests.
5. Repair docs in the same change packet.
6. Never label a phase complete on test count alone.

## If docs and code disagree

- Frozen contract correct, code wrong: fix code and add regression.
- Accepted code newer, docs stale: update the authority and propagation graph.
- True unresolved conflict: stop, classify in decisions/open questions, then code.

Do not hide a contradiction in a dashboard label or a comment.

## If tests fail

~~~text
reproduce
→ identify invariant
→ isolate smallest owner
→ fix root cause
→ add regression
→ focused suite
→ phase suite
→ full suite and quality checks
~~~

Never weaken a safety test just to obtain green output.

## Crash during broker write

If an Intent is SUBMITTING or acknowledgement is ambiguous:

~~~text
DO NOT RESEND
→ restore the Intent
→ query current broker positions/orders/deals
→ reconcile ticket, symbol, direction and volume
→ classify VERIFIED, FAILED or RECONCILING
→ create a new governed Intent only after truth is resolved
~~~

## Corrupt or missing runtime state

~~~text
block affected broker writes
→ preserve the corrupt artifact and diagnostics
→ restore the last verified checkpoint into a new database
→ connect MT5 and capture current recovery truth
→ reconcile positions/orders/deals and unresolved Intents
→ rebuild only what evidence proves
→ remain RECONCILING/BLOCKED while critical truth is unresolved
~~~

Never turn malformed state into empty exposure, zero risk or a passing gate.

## New-machine recovery

~~~mermaid
sequenceDiagram
    participant OLD as Old machine
    participant ART as Verified checkpoint
    participant NEW as New machine
    participant MT5 as MT5 terminal
    OLD->>ART: Export and verify public-safe state
    NEW->>ART: Restore into a new database
    NEW->>MT5: Configure intended DEMO terminal
    MT5-->>NEW: Fresh account, symbol and exposure truth
    NEW->>NEW: Reconcile state and controller fencing
    NEW->>NEW: READY only after every authority passes
~~~

Credentials are configured separately and never copied into the repository or
checkpoint. Restore is context; broker truth remains current MT5 truth.

## Build completion rule

~~~text
code exists
+ focused tests pass
+ failure/restart cases are explicit
+ coding standard review passes
+ documentation graph is synchronized
+ external evidence is honestly separated
+ no known critical contradiction
~~~

