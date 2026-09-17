# GoldSwingTraderAI — Documentation Standard

**Status:** PROVISIONAL  
**Authority:** Documentation placement, ownership, status and change-control rules.

## 1. Purpose

GoldSwingTraderAI is documentation-first. This standard prevents the repository from becoming a collection of overlapping Markdown files that disagree about the same behaviour.

Core rule:

> **One behavioural rule has one authoritative home. Other documents link to it; they do not restate a competing version.**

## 2. Repository-root documents

Root-level documents are reserved for repository entry/handoff artifacts, not detailed subsystem contracts.

Current root roles:

- `README.md` — project introduction and navigation.
- `FINAL_BUILD_PROMPT.md` — final implementation handoff; DRAFT until design freeze.

Future root-level artifacts such as `CHANGELOG.md`, `VERSION` or release manifests may exist when implementation/release work begins.

Detailed behavioural documents belong under `docs/`.

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
- HTF technical structure/levels;
- liquidity/SMC primitives;
- indicators/volatility;
- macro/fundamental evidence;
- session context as market evidence.

Market-intelligence documents do not grant execution authority.

### `docs/20-trading-decisions/`
Owns how market evidence becomes a trade idea or open-trade action:

- production strategy families;
- BUY/SELL thesis construction;
- scoring/fusion/debate;
- setup lifecycle and entry timing;
- structural trade plan;
- trade manager and exits.

### `docs/30-risk-execution/`
Owns hard financial/operational authority:

- monetary risk;
- daily loss/manual reset;
- session safety state machine;
- cooldown/blocked states;
- broker/account write guards;
- one-shot execution;
- persistence, restart and reconciliation.

Risk/safety rules are not converted into weighted strategy scores.

### `docs/40-research-learning/`
Owns evidence generation and governed improvement:

- replay/backtest parity;
- offline research;
- validation/holdouts/WFA/stress;
- strategy discovery;
- autonomous declarative invention;
- experiments/promotion/rollback;
- learning/ML/AI boundaries.

Research cannot silently redefine production or hard-risk semantics.

### `docs/50-operator/`
Owns human-facing usage:

- dashboard/UX;
- operator controls;
- user manual;
- setup/run guide.

Operator docs explain authoritative behaviour but do not redefine it.

### `docs/60-engineering/`
Owns implementation/developer/release maps:

- module structure;
- coder guide;
- test/verification strategy;
- release checklist;
- final release audit.

The Coder Guide is feature-oriented. Module Structure is file-oriented.

### `docs/90-governance/`
Owns design governance:

- design-decision ledger;
- open questions;
- this documentation standard;
- future change-control records if needed.

The final build prompt does **not** live here; it lives at repository root.

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
- `PROVISIONAL`: current agreed direction, still open to refinement.
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

- Exact daily-loss/manual-reset semantics belong in `30-risk-execution/`; `USER_MANUAL.md` links/explains them.
- Exact entry-state semantics belong in `20-trading-decisions/ENTRY_TIMING.md`; `ARCHITECTURE.md` only shows the high-level flow.
- Exact candle definitions belong in `10-market-intelligence/CANDLE_STRUCTURE.md`; strategy docs consume those definitions rather than redefining them.
- Exact promotion chronology belongs in `40-research-learning/`; Coder Guide maps its code path once implemented.

If two documents currently contain competing detailed versions of the same rule, that is a documentation defect and must be resolved before implementation.

## 7. Cross-references

Use relative repository links wherever possible. A supporting doc should say, for example:

> Daily loss and reset semantics are defined by `../30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md`.

It should not paste a second independent version of those semantics.

## 8. Design decisions and open questions

A materially important accepted choice should be recorded in `DESIGN_DECISIONS.md`.

An unresolved choice that could change implementation must be recorded in `OPEN_QUESTIONS.md` instead of being guessed in code or in the final build prompt.

When an open question is resolved:

1. update the authoritative topic document;
2. add/adjust the design-decision entry;
3. remove or mark the open question resolved;
4. update any affected supporting links/summaries.

## 9. Final Build Prompt rule

`FINAL_BUILD_PROMPT.md` is a handoff summary. It may reference frozen design documents and implementation sequence, but it must not become a shadow specification that contradicts them.

Before it can become FROZEN:

- required core topic documents must be FROZEN;
- required open questions must be resolved or explicitly deferred;
- cross-document contradiction audit must be complete;
- implementation phases and validation expectations must be explicit.

## 10. Reference-project rule

External/prior repositories may be studied for lessons, but GoldSwingTraderAI documentation must describe GoldSwingTraderAI itself. Do not copy prior project identity, legacy compatibility constraints or file architecture merely because they existed in a reference project.