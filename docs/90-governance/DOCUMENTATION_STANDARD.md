# GoldSwingTraderAI — Documentation Standard

**Status:** PROVISIONAL  
**Version:** 0.4-design  
**Authority:** Documentation placement, ownership, status and change-control rules.

## 1. Purpose

GoldSwingTraderAI is documentation-first. This standard prevents the repository from becoming a collection of overlapping Markdown files that disagree about the same behaviour.

Core rule:

> **One behavioural rule has one authoritative home. Other documents link to it; they do not restate a competing version.**

## 2. Repository root and docs-root primary guides

Repository root is reserved for repository entry/runtime artifacts. `README.md` remains the primary project introduction/navigation file. Future root artifacts such as `CHANGELOG.md`, `VERSION`, release manifests, dependency/runtime files and source folders may exist when implementation begins.

Detailed behavioural documentation belongs under `docs/`.

A small set of **high-visibility whole-project/operator/developer guides** live directly in `docs/` so they can be found without opening numbered subfolders:

- `docs/FINAL_BUILD_PROMPT.md` — final implementation handoff; DRAFT until design freeze.
- `docs/USER_MANUAL.md` — authoritative operator/user manual.
- `docs/SETUP_AND_RUN_GUIDE.md` — authoritative installation/startup/shutdown/migration/recovery guide.
- `docs/CODER_GUIDE.md` — authoritative feature-oriented developer map.
- `docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` — final large-phase build/recovery navigation guide, created at the end of design when the actual phase plan is stable.

The numbered folders still own the relevant **domain category**, but the three high-use User/Setup/Coder guides are intentionally surfaced at docs root. Their previous subfolder paths may remain as lightweight compatibility redirects only; behavioural content must not be maintained in two places.

These root-level guides summarize/navigate authoritative subsystem contracts where appropriate; they do not create competing trading, risk, execution or research rules.

## 3. Folder ownership

### `docs/00-foundation/`
Owns the constitution of the project:

- mission and non-goals;
- system-wide invariants;
- high-level architecture;
- trading-floor authority model.

It must not become a second copy of detailed entry, exit, risk or research rules.

### `docs/10-market-intelligence/`
Owns what the system can observe and infer about the market:

- market data/history;
- candle structure;
- HTF technical structure/levels/location;
- liquidity/SMC primitives;
- indicators/volatility;
- macro/fundamental/event facts;
- session context as market evidence.

Market-intelligence documents do not grant final execution authority.

### `docs/20-trading-decisions/`
Owns how market evidence becomes a trade idea or open-trade action:

- production strategy families;
- BUY/SELL thesis construction;
- scoring/fusion/debate and decision attribution;
- setup lifecycle and entry timing;
- structural Trade Plan;
- Trade Manager and exits.

### `docs/30-risk-execution/`
Owns hard financial/operational authority:

- monetary risk and dynamic sizing;
- daily loss/manual reset accounting;
- hard market/news/risk permission states;
- cooldown/blocked states;
- centralized broker-write permission;
- account/symbol/order safety and one-shot execution;
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

There is intentionally no separate authoritative `OFFLINE_RESEARCH.md`; offline/replay methodology belongs in `RESEARCH_AND_VALIDATION.md` to avoid duplicate contracts.

Research cannot silently redefine production or hard-risk semantics.

### `docs/50-operator/`
Owns the operator-domain supporting material, especially dashboard/UX and operator-control semantics. The primary high-use `USER_MANUAL.md` and `SETUP_AND_RUN_GUIDE.md` are surfaced directly in `docs/` for convenience while remaining operator-domain documents.

Operator docs explain authoritative behaviour but do not redefine it.

### `docs/60-engineering/`
Owns implementation/developer/diagnostic/release maps:

- module structure;
- system health/diagnostics aggregation;
- test/verification strategy;
- release checklist;
- final release audit.

The primary high-use `CODER_GUIDE.md` is surfaced directly in `docs/` for convenience while remaining an engineering-domain document. The Coder Guide is feature-oriented; Module Structure is file/module-oriented. System Health explains fault aggregation, not the underlying risk/execution rules.

### `docs/90-governance/`
Owns design governance:

- design-decision ledger;
- open questions;
- this documentation standard;
- future change-control records if needed.

Whole-project handoff/high-use guides do **not** live here; they live directly in `docs/`.

## 4. Status lifecycle

Every authoritative design document should declare one of:

```text
DRAFT
PROVISIONAL
FROZEN
IMPLEMENTED
VERIFIED
```

Meaning:

- `DRAFT`: incomplete; do not treat as settled behaviour.
- `PROVISIONAL`: current agreed direction, still open to refinement/calibration.
- `FROZEN`: approved behavioural contract for implementation.
- `IMPLEMENTED`: corresponding behaviour exists in code, but not necessarily fully validated.
- `VERIFIED`: exact implementation passed the required executable validation.

Do not mark a document VERIFIED merely because the Markdown is complete.

## 5. Standard technical-document shape

Where appropriate, subsystem contracts should use:

```text
# Title
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

Not every document needs every heading, but omissions should be deliberate.

## 6. Avoiding duplication

Examples:

- Exact daily-loss/manual-reset arithmetic belongs in `30-risk-execution/RISK_CONTRACT.md`; the state machine consumes the resulting risk state and the User Manual explains it to the operator.
- Exact news-event facts belong in `10-market-intelligence/FUNDAMENTAL_AND_NEWS.md`; hard news permission belongs in `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md`.
- Exact entry-state semantics belong in `20-trading-decisions/ENTRY_TIMING.md`; `ARCHITECTURE.md` only shows high-level flow.
- Exact candle/BOS/MSS definitions belong in `10-market-intelligence/CANDLE_STRUCTURE.md`; Technical/Liquidity/Strategy documents consume them rather than redefine them.
- Initial Trade Plan semantics belong in `20-trading-decisions/TRADE_PLAN.md`; post-entry management belongs in `TRADE_MANAGER_AND_EXIT.md`.
- Final broker-write permission/one-shot semantics belong in `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`; Coder/Module docs only map the code owner.
- `Why no trade?` decision attribution belongs in `SCORING_AND_DECISION_FUSION.md` plus the blocking authority; `SYSTEM_HEALTH_AND_DIAGNOSTICS.md` owns fault aggregation, not a competing decision engine.
- Exact promotion chronology belongs in `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md`; engineering docs map its implementation path.
- Compatibility redirect files must contain only a pointer to the new authoritative path, not a second behavioural copy.

If two documents contain competing detailed versions of the same rule, that is a documentation defect and must be resolved before implementation.

## 7. Cross-references

Use relative repository links wherever possible. A supporting doc should link to the authoritative source instead of pasting a second independent version.

Examples:

> Daily loss calculation/reset-reference semantics are defined by `30-risk-execution/RISK_CONTRACT.md`.

> Hard news permission is defined by `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` from event facts supplied by `10-market-intelligence/FUNDAMENTAL_AND_NEWS.md`.

## 8. Design decisions and open questions

A materially important accepted choice should be recorded in `DESIGN_DECISIONS.md`.

An unresolved choice that could change implementation must be recorded in `OPEN_QUESTIONS.md` instead of being guessed in code or in the final build prompt.

When an open question is resolved:

1. update the authoritative topic document;
2. add/adjust the design-decision entry;
3. remove/mark the open question resolved;
4. update affected supporting links/summaries.

## 9. Implementation synchronization rule

Documentation is updated during each implementation phase, not after the project is finished.

When code ownership/behaviour changes, synchronize as applicable:

- authoritative topic doc;
- `DESIGN_DECISIONS.md` / `OPEN_QUESTIONS.md`;
- `60-engineering/MODULE_STRUCTURE.md`;
- `CODER_GUIDE.md`;
- operator docs;
- test/release docs;
- `docs/README.md`.

A phase is not complete while code and its authoritative documentation knowingly disagree.

## 10. Final Build Prompt rule

`docs/FINAL_BUILD_PROMPT.md` is a handoff summary. It may reference frozen design documents and implementation sequence, but it must not become a shadow specification that contradicts them.

Before it can become FROZEN:

- required core topic documents must be FROZEN;
- required open questions must be resolved or explicitly deferred;
- cross-document contradiction audit must be complete;
- implementation phases and validation expectations must be explicit.

## 11. ChatGPT Project Build and Recovery Guide rule

`docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` is created at the end of the design phase after the build structure is stable. It is a navigation/recovery meta-guide for completing the project in large phases.

It should define:

- large implementation phases and their deliverables;
- required checks before moving to the next phase;
- how to reconstruct project state after conversation/context loss;
- how to resume after failed/incomplete code, missing files, docs/code mismatch, failed tests or interrupted work;
- how to recover on a new machine from repository/state backups;
- how to identify the last verified phase rather than restarting blindly;
- final completion/audit flow.

It must point back to authoritative documents instead of inventing behavioural rules.

## 12. Reference-project rule

External/prior repositories may be studied for lessons, but GoldSwingTraderAI documentation must describe GoldSwingTraderAI itself. Do not copy prior project identity, legacy compatibility constraints or file architecture merely because they existed in a reference project.
