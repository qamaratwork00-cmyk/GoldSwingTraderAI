# GoldSwingTraderAI Documentation Index

This folder is the design source of truth for GoldSwingTraderAI.

## Status meanings

- **DRAFT** — incomplete working document.
- **PROVISIONAL** — current agreed direction; still open to refinement.
- **FROZEN** — approved design contract for implementation.
- **IMPLEMENTED** — corresponding behaviour exists in code.
- **VERIFIED** — implementation has passed required executable validation.

## 00 — Foundation

| Document | Status | Purpose |
|---|---|---|
| [Project Vision](00-foundation/PROJECT_VISION.md) | PROVISIONAL | Mission, trading personality, timeframe intent and non-goals |
| [System Contract](00-foundation/SYSTEM_CONTRACT.md) | PROVISIONAL | Highest-level behavioural contract |
| [Architecture](00-foundation/ARCHITECTURE.md) | PROVISIONAL | High-level system flow and authority boundaries |
| [Trading Floor Architecture](00-foundation/TRADING_FLOOR_ARCHITECTURE.md) | PROVISIONAL | Specialist desks, BUY/SELL teams and institutional-floor model |

## 10 — Market Intelligence

| Document | Status | Purpose |
|---|---|---|
| [Market Data and History](10-market-intelligence/MARKET_DATA_AND_HISTORY.md) | PROVISIONAL | Rolling candle history, timeframe data and persistence rules |
| Candle Structure | DRAFT / upcoming | Candle anatomy, sequences, swings, BOS/MSS and displacement |
| Technical/Liquidity/Indicators | DRAFT / upcoming | Technical, liquidity, FVG/OB and indicator evidence |
| Fundamental and News | DRAFT / upcoming | Macro context, holidays and hard news safety |

## 20 — Trading Decisions

| Document | Status | Purpose |
|---|---|---|
| [Strategy Floor](20-trading-decisions/STRATEGY_FLOOR.md) | PROVISIONAL | Parallel production strategy families and family evidence contract |
| [Entry Timing](20-trading-decisions/ENTRY_TIMING.md) | PROVISIONAL | Persistent setup lifecycle and executable entry timing |
| [Scoring and Decision Fusion](20-trading-decisions/SCORING_AND_DECISION_FUSION.md) | PROVISIONAL | BUY/SELL theses, opportunity/timing scores and conflict handling |
| [Trade Manager and Exit](20-trading-decisions/TRADE_MANAGER_AND_EXIT.md) | PROVISIONAL | Continuation/reversal board, structural trailing and runner logic |

## 30 — Risk and Execution

| Document | Status | Purpose |
|---|---|---|
| [Risk Contract](30-risk-execution/RISK_CONTRACT.md) | PROVISIONAL | Risk authority, daily-loss/manual-reset intent and trade-frequency safeguards |
| [Session and Risk State Machine](30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md) | PROVISIONAL | OPEN/PRE-CLOSE/CLOSED/reopen/holiday + risk/system states |
| Execution and Broker Safety | DRAFT / upcoming | One-shot order path and broker safeguards |
| Restart and Recovery | DRAFT / upcoming | Durable lifecycle, reconciliation and restart semantics |

## 40 — Research and Learning

Planned authoritative documents:

- `RESEARCH_AND_VALIDATION.md`
- `GOVERNED_STRATEGY_DISCOVERY.md`
- `AUTONOMOUS_STRATEGY_INVENTION.md`
- `LEARNING_AND_AI_BOUNDARIES.md`

## 50 — Operator

Planned documents:

- `DASHBOARD_AND_UX.md`
- `USER_MANUAL.md`
- `SETUP_AND_RUN_GUIDE.md`

## 60 — Engineering

Planned documents:

- `MODULE_STRUCTURE.md`
- `CODER_GUIDE.md`
- `TESTING_AND_VERIFICATION.md`
- `RELEASE_CHECKLIST.md`
- `FINAL_RELEASE_AUDIT.md`

## 90 — Governance

| Document | Status | Purpose |
|---|---|---|
| [Design Decisions](90-governance/DESIGN_DECISIONS.md) | Living ledger | Accepted/provisional decisions and rationale |
| [Open Questions](90-governance/OPEN_QUESTIONS.md) | Living ledger | Unresolved design choices that must not be silently guessed |
| [Final Build Prompt](90-governance/FINAL_BUILD_PROMPT.md) | DRAFT | Final implementation brief; frozen only after core design freeze |

## Authority rule

When documents conflict, use this precedence until the conflict is formally resolved:

1. `00-foundation/SYSTEM_CONTRACT.md`
2. Specific authoritative topic document
3. `90-governance/DESIGN_DECISIONS.md`
4. Supporting/operator documentation

No implementation should silently resolve a documented contradiction by guessing.
