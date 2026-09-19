# GoldSwingTraderAI — Documentation Standard

**Status:** FROZEN
**Version:** 1.1-frozen
**Authority:** Documentation placement, ownership, status and change-control rules.

## 1. Purpose

GoldSwingTraderAI is documentation-first.

> **One behavioural or engineering rule has one authoritative home. Other documents link to it; they do not restate a competing version.**

This standard prevents overlapping Markdown files from silently disagreeing about the same behaviour or implementation-quality rule.

This document is itself the **frozen documentation-maintenance contract**.
Freezing the standard does not freeze the project content: topic documents,
source maps, tests, release evidence and operator guidance must continue to
evolve as implementation advances. It freezes the rules for preserving prior
meaning, synchronizing related documents, classifying status and recording
material changes. Changing this standard requires an explicit governance
decision; ordinary feature work must follow it.

## 2. Repository root and docs-root primary guides

Repository root is reserved for repository entry/runtime artifacts. `README.md` is the primary project introduction/navigation file.

Detailed behavioural and engineering documentation belongs under `docs/`.

The following high-visibility whole-project/operator/developer guides intentionally live directly in `docs/`:

- `docs/FINAL_BUILD_PROMPT.md` — whole-project implementation handoff summary;
- `docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` — large implementation phases, phase completion and recovery navigation;
- `docs/USER_MANUAL.md` — authoritative operator/user manual;
- `docs/SETUP_AND_RUN_GUIDE.md` — authoritative installation/startup/shutdown/migration/recovery guide;
- `docs/CODER_GUIDE.md` — authoritative feature-oriented developer map.

The numbered folders still own the relevant domain categories. Previous subfolder paths for User/Setup/Coder guides may remain only as lightweight compatibility redirects; behavioural content must not be maintained in two places.

These docs-root guides summarize/navigate authoritative subsystem contracts where appropriate; they do not create competing trading, risk, execution, research or coding-standard rules.

## 3. Folder ownership

### `docs/00-foundation/`
Owns the project constitution:

- mission and non-goals;
- system-wide invariants;
- high-level architecture;
- trading-floor authority model.

### `docs/10-market-intelligence/`
Owns market observations/inference:

- market data/history;
- candle structure;
- HTF technical structure/levels/location;
- optional technical confluence such as causal Trendline/Fibonacci/broker-local POC;
- liquidity/SMC primitives;
- indicators/volatility;
- macro/fundamental/event facts;
- session context as market evidence.

`TECHNICAL_STRUCTURE_AND_LEVELS.md` is the behavioural authority for generic technical zones/location and optional Trendline/Fibonacci/POC confluence even if implementation uses separate `technical.py` and `confluence.py` modules for clean code.

Market-intelligence documents do not grant final broker authority.

### `docs/20-trading-decisions/`
Owns how evidence becomes trade intent or open-trade action:

- strategy families;
- BUY/SELL thesis construction;
- scoring/fusion/debate and decision attribution;
- setup lifecycle and entry timing;
- structural Trade Plan;
- Trade Manager and exits.

### `docs/30-risk-execution/`
Owns hard financial/operational authority:

- monetary risk and dynamic/hybrid sizing;
- daily loss/manual reset accounting;
- hard market/news/risk permission states;
- cooldown/blocked states;
- centralized broker-write permission;
- DEMO guard;
- account/symbol/order safety and one-shot execution;
- controller lease/fencing;
- persistence, restart, reconciliation, backup and migration.

Risk/safety rules are not converted into weighted strategy scores.

### `docs/40-research-learning/`
Owns evidence generation and governed improvement:

- chronological replay/backtest parity;
- validation/holdouts/WFA/stress;
- StrategyMemory and entry/exit learning boundaries;
- strategy discovery;
- autonomous declarative invention;
- experiments/promotion/rollback.

There is intentionally no separate authoritative `OFFLINE_RESEARCH.md`.

### `docs/50-operator/`
Owns operator-domain supporting material, especially dashboard/UX and operator-control semantics. Primary `USER_MANUAL.md` and `SETUP_AND_RUN_GUIDE.md` are surfaced at docs root.

### `docs/60-engineering/`
Owns implementation/developer/diagnostic/release authority and maps:

- `CODING_STANDARD.md` — source-code quality, complexity, dependency, commenting, performance and phase-quality contract;
- module structure;
- system health/diagnostics aggregation;
- test/verification strategy;
- release checklist;
- final release audit.

Primary `CODER_GUIDE.md` is surfaced at docs root. Coder Guide is feature-oriented; Module Structure is file/module-oriented; Coding Standard owns engineering-style rules that those documents consume.

### `docs/90-governance/`
Owns:

- design-decision ledger;
- open questions/freeze matrix;
- this documentation standard;
- future change-control records if needed.

## 4. Status lifecycle

Authoritative design/engineering documents use:

```text
DRAFT
PROVISIONAL
FROZEN
IMPLEMENTED
VERIFIED
SUPERSEDED
```

- `DRAFT` — incomplete working document;
- `PROVISIONAL` — current agreed direction, still open to refinement/calibration;
- `FROZEN` — approved behavioural or engineering contract for implementation;
- `IMPLEMENTED` — corresponding behaviour/rule exists in code/process;
- `VERIFIED` — exact implementation passed required executable validation.
- `SUPERSEDED` — replaced by a named authoritative document or contract; keep
  a redirect or traceable replacement note rather than silently deleting useful
  meaning.

Do not mark a document `IMPLEMENTED` because a plan exists, or `VERIFIED` because Markdown is complete.

## 5. Standard technical-document shape

Where useful, subsystem contracts should include:

```text
Title
Status
Authority
Depends on
Purpose
Core principles
Inputs
Outputs
States/models
Decision rules
Hard rules
Soft evidence
Failure behaviour
Persistence/restart
Replay requirements
Dashboard visibility
Tests required
Explicit non-goals
Open questions
```

Engineering standards may adapt this shape where states/market inputs are not relevant, but authority/status/change rules still apply.

### 5.1 Self-contained explanation rule

Each non-redirect document must be understandable without opening a second file
to discover what the document is trying to explain. Cross-links are for
authoritative detail, not for hiding the document's purpose or execution path.
At minimum, the reader must be able to answer:

| Reader question | Required answer in the document |
|---|---|
| Why does this exist? | Purpose, scope and explicit non-goals |
| Where does it run? | Layer, owning modules and entry points |
| What does it consume and produce? | Inputs, outputs, schemas or typed models |
| What happens in order? | Lifecycle, state transitions and authority gates |
| What can run independently? | Parallel/dataflow lanes and shared snapshot rules |
| What happens when information is missing? | `UNKNOWN`, fail-closed, retry, quarantine or explicit error semantics |
| How is it proven? | Source paths, executable tests and live-evidence boundary |
| How is it operated or researched? | Dashboard/operator visibility and replay/calibration implications |

### 5.2 Diagram and table rule

Use a visual when prose alone would make ownership, parallelism, state
transitions, dependency direction or event order difficult to verify.

```mermaid
flowchart TB
    A["Authoritative contract"] --> B["Source ownership"]
    B --> C["Executable tests"]
    C --> D["Operator / research evidence"]
    D --> E["Release audit"]
```

Choose the smallest visual that makes the relationship precise:

| Relationship being explained | Preferred form |
|---|---|
| Exact field/module/authority mapping | Markdown table |
| Ownership, dependency or dataflow | Mermaid flowchart |
| Lifecycle or permission transitions | Mermaid state diagram |
| Ordered events or handoff | Mermaid sequence/timeline |
| Repeated numeric comparison | Table or chart with named units |
| One fact or one short sequence | Prose; no decorative diagram |

Diagram labels must use the same names as the code and authoritative contract.
Do not draw “parallel” boxes unless the work really shares one immutable
snapshot and has no hidden ordering dependency. A chart must identify its
metric, time basis and data source; it must never imply live or broker evidence
that has not been collected.

## 6. Avoiding duplication

Examples:

- daily-loss/manual-reset arithmetic → `30-risk-execution/RISK_CONTRACT.md`;
- hard news permission → `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` from event facts supplied by `10-market-intelligence/FUNDAMENTAL_AND_NEWS.md`;
- entry-state semantics → `20-trading-decisions/ENTRY_TIMING.md`;
- BOS/MSS/swing definitions → `10-market-intelligence/CANDLE_STRUCTURE.md`;
- technical zones/location and Trendline/Fibonacci/POC confluence semantics → `10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md`;
- initial entry/SL/targets/original R → `20-trading-decisions/TRADE_PLAN.md`;
- post-entry management → `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md`;
- centralized broker-write permission/one-shot/controller semantics → `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`;
- source-code quality/complexity/dependency/commenting rules → `60-engineering/CODING_STANDARD.md`;
- decision attribution → `SCORING_AND_DECISION_FUSION.md` plus the actual blocking authority;
- fault aggregation → `60-engineering/SYSTEM_HEALTH_AND_DIAGNOSTICS.md`;
- promotion chronology → `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md`.

Compatibility redirect files contain only a pointer to the authoritative path.

If two documents contain competing detailed versions of the same rule, that is a documentation defect and must be resolved before implementing affected behaviour.

## 7. Cross-references

Use relative repository links wherever possible. Supporting docs should link to authoritative sources instead of pasting a second independent version.

Final Build Prompt, Coder Guide, Module Structure and Build/Recovery Guide may summarize Coding Standard requirements for execution clarity, but `CODING_STANDARD.md` remains detailed authority and wins if wording diverges.

## 8. Design decisions and freeze matrix

Material accepted choices belong in `90-governance/DESIGN_DECISIONS.md`.

Unresolved or not-yet-fixed items belong in `90-governance/OPEN_QUESTIONS.md`, classified as appropriate:

```text
FIX BEFORE BUILD
CALIBRATE IN RESEARCH
IMPLEMENTATION CHOICE
DEFER LATER
```

Research calibration and ordinary implementation choices do not automatically block implementation.

When an important question is resolved:

1. update authoritative topic doc;
2. add/supersede decision entry where material;
3. reclassify/remove the open item;
4. update affected summaries/links.

## 9. Implementation synchronization rule

Documentation is updated during each coherent implementation phase, not as end-of-project cleanup.

Synchronize as applicable:

- authoritative topic doc;
- `DESIGN_DECISIONS.md` / `OPEN_QUESTIONS.md`;
- `60-engineering/CODING_STANDARD.md` only after explicitly approved engineering-standard change;
- `60-engineering/MODULE_STRUCTURE.md`;
- `CODER_GUIDE.md`;
- User/Setup/operator docs;
- testing/release docs;
- `docs/README.md`.

A phase is not complete while code and authoritative documentation knowingly disagree or while affected code knowingly violates the frozen Coding Standard.

## 10. Final Build Prompt rule

`docs/FINAL_BUILD_PROMPT.md` is a whole-project handoff summary. It may summarize frozen/current implementation direction, including Coding Standard, but it must not override authoritative subsystem documents.

Before it is marked `FROZEN`:

- implementation-critical behavioural choices must be frozen or explicitly classified/deferred;
- cross-document contradiction/coverage audit must be complete;
- implementation phases and validation expectations must be explicit.

## 11. ChatGPT Project Build and Recovery Guide rule

`docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` is persistent meta-guide for completing the project in large phases and resuming safely after interruption.

It defines:

- large phases and deliverables;
- exit gates before moving forward;
- Coding Standard quality review as part of phase completion;
- context-loss reconstruction;
- incomplete/broken phase recovery;
- docs/code mismatch recovery;
- failed-test procedure;
- Git/local/state mismatch handling;
- crash-during-broker-write recovery;
- new-machine/disaster recovery;
- final completion/audit flow.

It points to authoritative documents rather than inventing behavioural or engineering rules.

## 12. Reference-project rule

External/prior projects may be studied for lessons, but GoldSwingTraderAI documentation describes GoldSwingTraderAI itself. Do not copy legacy project identity, compatibility constraints or architecture merely because they existed elsewhere.

## 13. Preservation-first update rule

Documentation updates are **append-first and contract-preserving**. A new
implementation must not erase the earlier rationale, constraints, planned
sequence, verification boundary or unresolved decision merely because the code
has advanced.

Preserve earlier information by placing its useful meaning in the correct
design section. For example, if a read-only launcher becomes an integrated
startup service, the startup section must still explain the read-only readiness
path, the full startup sequence, the authority handoff and the evidence
required before live use. The reader should learn the whole design in one
place, not hunt through a dated status diary.

Use status/evidence labels only where they prevent a dangerous
misunderstanding. Do not turn normal topic documents into a chronology of
patches. A superseded implementation detail may be named briefly inside the
design explanation, but the document's main voice must remain the intended
system contract.

Normal documentation edits should not produce unexplained deletions. Before
finalizing a docs change, inspect the diff for removed paragraphs, tables,
checklists, prompt instructions and phase gates. A deletion is acceptable only
when it is an exact duplicate, a security exposure, or the same information is
moved into the correct authoritative section without loss of meaning.

## 14. Complete-explanation rule

Every non-redirect document must explain its subject from purpose to evidence.
At the appropriate depth, include:

- why the subject exists and what problem it solves;
- where it sits in the end-to-end runtime and which documents surround it;
- inputs, outputs, state transitions and authority boundaries;
- what may run independently/parallel and what must remain ordered;
- exact source modules, public entry points and important tests;
- persistence/restart and failure/unknown behaviour;
- operator/dashboard/research visibility where applicable;
- a small flow or ownership diagram when relationships are easier to understand
  visually;
- current software evidence versus live broker/DEMO evidence;
- explicit non-goals, calibration items and next proof required.

The root prompt and ChatGPT guide must additionally explain how an implementation
agent should navigate the documentation, choose the next phase, preserve prior
work, verify changes and recover from context loss. They are summaries and
process guides, not hidden replacements for topic authorities.

## 15. Documentation change record

Material documentation work should leave an auditable record in the working
diff or task handoff. The record should name:

```text
date/checkpoint
documents touched
old information retained or moved
new implementation/evidence added
links or source owners updated
tests/link checks run
remaining uncertainty
```

This makes a documentation update reviewable in the same way as a code change.
The record belongs in the review/working handoff; ordinary design documents
should remain timeless manuals rather than becoming chronological change logs.

## 16. Frozen completeness and freeze protocol

This protocol is mandatory for every material implementation or documentation
change. A user-highlighted defect is an example of a wider impact class, not a
limit on the audit scope. The agent must inspect the whole affected contract
graph and must not update only the file named in the request.

### 16.1 Before implementation

Create an internal impact map covering:

| Question | Required inspection |
|---|---|
| What is the requested behaviour? | authoritative topic document, system contract and decision ledger |
| Which phase owns it? | build/recovery phase map, Coder Guide and open/freeze matrix |
| Where is it implemented? | source package, entry point, configuration and persistence/schema |
| What can it affect? | upstream inputs, downstream authorities, dashboard/operator, research and recovery |
| How is it proven? | focused tests, integration tests, live-environment evidence and release audit |
| Which documents can become stale? | docs index, architecture, module map, coder guide, prompts, setup/manual, testing/release docs |

The implementation may proceed only after every affected area has an owner or
an explicit reason why it is not affected. A missing feature row, absent phase
detail, broken cross-link, undocumented source owner or unpropagated state is
treated as a documentation defect even if the code itself passes tests.

### 16.2 During implementation

Maintain one change packet:

~~~text
authoritative contract
→ decision/freeze classification
→ architecture/dataflow
→ source owner and entry point
→ typed inputs/outputs/states
→ tests and failure cases
→ persistence/restart impact
→ dashboard/operator/research impact
→ release/evidence impact
~~~

When a rule crosses more than one layer, update the owner first and update
supporting navigation documents in the same coherent change. Do not leave a
known interim contradiction between code, topic docs and the Coder Guide.

### 16.3 Required document propagation

For a material feature, inspect and update as applicable:

1. authoritative domain contract;
2. Architecture and parallel/ordered dataflow;
3. Design Decisions and Open Questions;
4. Module Structure and Coder Guide;
5. Final Build Prompt and ChatGPT Build/Recovery Guide;
6. Setup/Run Guide and User Manual;
7. Dashboard/UX and operator evidence;
8. Testing/Verification and Final Release Audit;
9. docs index, links, phase map and status labels.

No file is changed mechanically just to satisfy the list. Each affected
document must either explain the new behaviour or record why the behaviour is
outside its scope. Useful old rationale, constraints, phase gates, tests and
unresolved proof requirements must be retained in the correct section.

### 16.4 Freeze review before handoff

Before a change is called complete, run this review:

- every phase and feature has a purpose, owner, source path, entry point and test;
- DEMO Guard, fail-closed/UNKNOWN behaviour, no-lookahead and write boundary
  are explicitly traceable where relevant;
- diagrams use real module/state names and do not imply uncollected evidence;
- old useful content is preserved or deliberately relocated with no unexplained
  deletion;
- Phase 1–9 foundation, Phase 10 research, Phase 11 recovery/backup and Phase
  12 integration/certification remain visibly distinct;
- code, tests, docs and current evidence agree;
- links, headings, status labels and command examples are checked;
- remaining external/live proof is clearly marked PENDING rather than implied.

Only after this review may the coherent change be frozen, committed or
published. This protocol is itself frozen project process; future exceptions
require an explicit governance decision.

## 17. Whole-project guide minimum

The high-visibility guides are not allowed to collapse the system into a vague
summary. Their minimum content is frozen as follows:

| Guide | Minimum explanation that must remain present |
|---|---|
| `docs/README.md` | reading order, folder ownership, every authoritative document, status vocabulary and source-area coverage route |
| `docs/CODER_GUIDE.md` | individually explained Phases 1–9, separate Phase 10, Phase 11 and Phase 12 contracts, architecture/dataflow diagrams, feature → authority → source → entry point → tests, DEMO Guard, runtime and recovery traces |
| `docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` | implementation loop, impact audit, phase exit gates, resume/context-loss recovery and evidence language |
| `docs/FINAL_BUILD_PROMPT.md` | compact handoff, authority order, architecture invariants, feature route, frozen coding/safety rules and final validation boundary |
| `docs/SETUP_AND_RUN_GUIDE.md` | installation, configuration, launcher modes, stale/closed-market wait, startup/recovery, shutdown, restore and operator commands |
| `docs/USER_MANUAL.md` | human interpretation of runtime states, dashboard, safety, no-trade reasons and recovery actions |

Phase headings alone do not satisfy the Coder Guide requirement. Each phase
must identify purpose, outputs, owner modules, boundaries, tests and its exit
condition. Removing those details to make a guide shorter is a documentation
regression, even when the replacement prose is technically true.

## 18. Final documentation gate

Before a branch is published or a project checkpoint is called complete, the
reviewer/agent must be able to answer “where is this defined?” for every
source-area, feature, state, operator view, research artifact and release
claim. The answer must resolve to a documented authority and a source/test
map, or to an explicit `OUT OF SCOPE` / `PENDING EXTERNAL EVIDENCE` record.

The final gate includes the executable
`python scripts/verify_documentation.py .` check, a repository link check,
source/script/test filename coverage, duplicate/accidental-deletion review,
stale evidence-count review and a comparison of code, tests and docs against
the same commit. Passing tests cannot waive this documentation gate.
