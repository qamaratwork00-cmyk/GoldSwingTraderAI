# GoldSwingTraderAI — Documentation Standard

**Status:** FROZEN FOR THE NEW DOCUMENTS MANUAL
**Version:** 0.1-freeze
**Authority:** Documentation structure, completeness, preservation and change control

## Purpose

GoldSwingTraderAI is documentation-first. A coder, operator or AI agent must
be able to understand the complete responsibility chain before changing code.

This standard governs the new Documents/ manual. Existing docs/ is preserved
for reference and is not a hidden dependency of this set.

> Updating a document means preserving useful meaning, adding the new verified
> implementation, and synchronizing every affected document. It does not mean
> deleting the old design because the code moved forward.

## One rule, one owner

Every behavioural rule has one authoritative home:

| Rule | Authority |
|---|---|
| system invariants | 00-foundation/SYSTEM_CONTRACT.md |
| runtime topology and startup | 00-foundation/ARCHITECTURE.md |
| desk ownership | 00-foundation/TRADING_FLOOR_ARCHITECTURE.md |
| market facts/chronology | 10-market-intelligence/MARKET_DATA_AND_HISTORY.md and the relevant intelligence contract |
| strategy/fusion/timing/plan/management | the matching 20-trading-decisions contract |
| money, permission, broker write and recovery | the matching 30-risk-execution contract |
| research semantics and promotion | the matching 40-research-learning contract |
| code style | 60-engineering/CODING_STANDARD.md |
| evidence commands | 60-engineering/TESTING_AND_VERIFICATION.md |
| document change process | this file |

Supporting documents explain how to find and use a rule. They do not create a
second competing threshold or state machine.

## Required information architecture

Every substantive document must answer these questions in plain language:

1. Why does this subject exist?
2. Where is it in the end-to-end runtime?
3. What exact files and public entry points own it?
4. What does it consume and produce?
5. What can run independently and what must remain ordered?
6. What are the states and transitions?
7. What happens when data is missing, stale, corrupt or ambiguous?
8. What survives restart or machine migration?
9. What does the operator see?
10. What does replay/research need to preserve?
11. Which tests prove the software boundary?
12. Which live/provider/broker proof is still pending?
13. What is explicitly outside the subject?
14. Which questions remain open?

The standard document shape is:

~~~text
metadata
purpose and reader promise
system position diagram
inputs and outputs
rules and states
parallel/ordered boundary
failure and UNKNOWN semantics
persistence/restart
operator/dashboard
research/replay
source and test map
verification boundary
non-goals
open questions
~~~

An engineering or operator document may adapt the headings, but it may not omit
the explanation, ownership, failure, proof and non-goal requirements.

## Diagram and table standard

Use Mermaid when the relationship is easier to verify visually:

- flowchart for dependency/dataflow;
- state diagram for lifecycle/permission transitions;
- sequence diagram for startup or broker events;
- table for exact file, field, threshold or test mappings.

Every diagram must:

- use real names from code or the authoritative contract;
- show the direction of authority;
- distinguish parallel evidence from ordered permission;
- avoid implying a live result that has not been collected;
- remain small enough to read.

If a visual adds no precision, use prose or a table instead. Decorative
diagrams are not a quality signal.

## Metadata and versioning

Every non-index document has:

~~~text
Status
Version
Authority
Depends on (when applicable)
~~~

Version numbers change when meaning, ownership, source maps, state semantics or
proof boundaries change. A spelling-only correction may keep the version but
must still pass link/coverage checks.

Status describes evidence honestly:

- a plan is not IMPLEMENTED;
- deterministic tests are not live MT5 proof;
- a connected DEMO read is not a write/modify/close certification;
- a completed document is not a profitable strategy.

## Full affected-graph update rule

When a feature changes, inspect the complete graph:

~~~mermaid
flowchart TB
    REQUIREMENT["Requirement or implementation change"] --> AUTHORITY["Behavioural authority"]
    AUTHORITY --> ARCH["Architecture and dataflow"]
    AUTHORITY --> SOURCE["Source owner and entry point"]
    SOURCE --> TESTS["Focused, integration and fault tests"]
    SOURCE --> STATE["Persistence and restart impact"]
    SOURCE --> VIEW["Dashboard and operator impact"]
    SOURCE --> RESEARCH["Replay and learning impact"]
    TESTS --> RELEASE["Testing, release and open questions"]
    ARCH --> INDEX["Coder Guide, module map and index"]
    RELEASE --> REVIEW["Same-change documentation review"]
~~~

The user may mention one missing row or one missing diagram. That mention is a
signal to audit the wider graph, not permission to edit only that line.

## Preservation-first rewrite rule

The new manual is allowed to rewrite an entire file from zero. A rewrite is
valid only when it retains or deliberately relocates:

- the original purpose and design rationale;
- all accepted constraints and negative rules;
- phase ownership and completion gates;
- source modules and entry points;
- test names and evidence limits;
- persistence/restart and failure semantics;
- dashboard/operator and research consequences;
- unresolved questions and later-work boundaries.

Do not remove a paragraph, table, diagram or phase gate merely because it is
old. Remove only exact duplication, unsafe secret material or a rule that is
explicitly superseded—and record the supersession.

The CONTENT_COVERAGE_MATRIX.md file is the review checklist for this rule.

## Phase separation rule

Every project summary must keep these ideas separate:

| Phase group | Meaning |
|---|---|
| Phase 1–9 | deterministic production foundation and operator surface |
| Phase 10 | research, replay, learning, discovery and promotion |
| Phase 11 | portable backup, restore, migration, controller and recovery proof |
| Phase 12 | integrated persistent runtime, live dashboard and final DEMO certification |

Phase 10 research is not live trading. Phase 11 recovery is not broker truth.
Phase 12 release certification is not proven by unit-test count.

## Freeze process

Before calling a change complete:

1. Identify the one behavioural owner.
2. Read every upstream and downstream contract.
3. Update the source/test/entry-point map.
4. Add or update the relevant diagram/table.
5. Describe missing/corrupt/ambiguous data.
6. Describe persistence and restart consequences.
7. Describe operator and research consequences.
8. Update decisions/open questions and phase status.
9. Inspect the diff for unexplained semantic deletion.
10. Run link, filename coverage, Mermaid-fence, secret and code checks.

The freeze record must name the checkpoint, files touched, old meaning retained,
new implementation added, tests run and external proof still pending.

## Review checklist

~~~text
[ ] Existing useful rationale was retained or deliberately relocated
[ ] Authority and source owner are singular and explicit
[ ] DEMO Guard is traceable where broker writes are relevant
[ ] UNKNOWN/fail-closed behaviour is explicit
[ ] No-lookahead is explicit where time-series facts are relevant
[ ] One-shot write/reconciliation is explicit where broker actions are relevant
[ ] Controller/fencing is explicit where multi-instance behaviour is relevant
[ ] Dashboard and research effects are documented
[ ] Exact source/test filenames are present
[ ] Relative links resolve
[ ] Diagram labels match implementation
[ ] Current software evidence is separated from live evidence
[ ] Open questions and release blockers are not hidden
~~~

## Adoption rule

Documents remain CANDIDATE FOR ADOPTION until the new-manual audit passes. At
adoption time, the project must explicitly choose one of:

1. replace old docs/ with this manual;
2. keep old docs/ as archived historical reference with clear redirects; or
3. merge selected files through a documented migration plan.

No silent deletion or ambiguous dual authority is allowed.

