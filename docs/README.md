# GoldSwingTraderAI Documentation Index

This folder is the design source of truth for GoldSwingTraderAI. The goal is simple: **one topic, one authoritative home**. Supporting documents should link to the authoritative document instead of repeating the same rule with slightly different wording.

## Status meanings

- **DRAFT** — incomplete working document.
- **PROVISIONAL** — current agreed direction; still open to refinement.
- **FROZEN** — approved design contract for implementation.
- **IMPLEMENTED** — corresponding behaviour exists in code.
- **VERIFIED** — implementation has passed required executable validation.

## Where does a topic belong?

| Topic | Authoritative folder |
|---|---|
| Mission, constitutional rules, system-wide architecture | `00-foundation/` |
| Candles, structure, liquidity, indicators, fundamentals, market/session context | `10-market-intelligence/` |
| Strategy families, entry timing, scoring/fusion, trade plan, exit decisions | `20-trading-decisions/` |
| Risk, daily lock/reset, market-close safety, broker execution, restart/reconciliation | `30-risk-execution/` |
| Replay, validation, discovery, autonomous invention, experiments, promotion, learning/AI | `40-research-learning/` |
| Dashboard, user manual, setup/run and operator actions | `50-operator/` |
| Module map, coder guide, tests, release gates and final audits | `60-engineering/` |
| Design-decision ledger, unresolved questions and documentation/change governance | `90-governance/` |

`FINAL_BUILD_PROMPT.md` intentionally lives at the **repository root**, not inside `docs/`, because it is an implementation handoff artifact rather than a topic document.

## 00 — Foundation

| Document | Status | Purpose |
|---|---|---|
| [Project Vision](00-foundation/PROJECT_VISION.md) | PROVISIONAL | Mission, trading personality, timeframe intent and non-goals |
| [System Contract](00-foundation/SYSTEM_CONTRACT.md) | PROVISIONAL | Highest-level behavioural contract |
| [Architecture](00-foundation/ARCHITECTURE.md) | PROVISIONAL | High-level system flow and authority boundaries |
| [Trading Floor Architecture](00-foundation/TRADING_FLOOR_ARCHITECTURE.md) | PROVISIONAL | Specialist desks, BUY/SELL teams, debate/red-team and institutional-floor model |

Foundation documents stay deliberately high-level. Detailed entry, exit, risk or research rules belong in their specialist folders.

## 10 — Market Intelligence

| Document | Status | Purpose |
|---|---|---|
| [Market Data and History](10-market-intelligence/MARKET_DATA_AND_HISTORY.md) | PROVISIONAL | Rolling candle history, timeframe data and persistence rules |
| `CANDLE_STRUCTURE.md` | Upcoming | Candle anatomy, sequences, swings, BOS/MSS, rejection, displacement, compression/expansion |
| `TECHNICAL_STRUCTURE_AND_LEVELS.md` | Upcoming | HTF structure, support/resistance, location and structural zones |
| `LIQUIDITY_AND_SMC.md` | Upcoming | Liquidity pools/sweeps, FVG, qualified OB, premium/discount |
| `INDICATORS_AND_VOLATILITY.md` | Upcoming | EMA/RSI/ATR and quantitative supporting evidence |
| `FUNDAMENTAL_AND_NEWS.md` | Upcoming | Macro context, provider-backed event safety and holiday context |
| `SESSION_CONTEXT.md` | Upcoming | Asian/London/New York context as market evidence; not the risk-state machine |

## 20 — Trading Decisions

| Document | Status | Purpose |
|---|---|---|
| [Strategy Floor](20-trading-decisions/STRATEGY_FLOOR.md) | PROVISIONAL | Parallel production strategy desks and family evidence contract |
| [Entry Timing](20-trading-decisions/ENTRY_TIMING.md) | PROVISIONAL | Persistent opportunity lifecycle and executable entry timing |
| [Scoring and Decision Fusion](20-trading-decisions/SCORING_AND_DECISION_FUSION.md) | PROVISIONAL | BUY/SELL theses, Opportunity/Entry scores, conflict and red-team handling |
| `TRADE_PLAN.md` | Upcoming | Structural entry, stop, target, original R and runner objectives |
| [Trade Manager and Exit](20-trading-decisions/TRADE_MANAGER_AND_EXIT.md) | PROVISIONAL | Continuation/reversal board, structural trailing and runner/exit logic |

## 30 — Risk and Execution

| Document | Status | Purpose |
|---|---|---|
| [Risk Contract](30-risk-execution/RISK_CONTRACT.md) | PROVISIONAL | Monetary risk authority, daily-loss/manual-reset intent and frequency safeguards |
| [Session and Risk State Machine](30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md) | PROVISIONAL | OPEN/PRE-CLOSE/CLOSED/reopen/holiday plus risk/system states |
| `EXECUTION_AND_BROKER_SAFETY.md` | Upcoming | MT5 identity, pre-submit checks, one-shot send and ambiguous acknowledgement handling |
| `PERSISTENCE_RESTART_AND_RECOVERY.md` | Upcoming | Durable lifecycle, state integrity, restart and broker reconciliation |

## 40 — Research and Learning

Planned authoritative documents:

- `RESEARCH_AND_VALIDATION.md` — replay chronology, parity, holdouts, WFA/stress and evidence tiers.
- `OFFLINE_RESEARCH.md` — research-only workflows separated from runtime authority.
- `GOVERNED_STRATEGY_DISCOVERY.md` — parameter/strategy candidate discovery and comparison.
- `AUTONOMOUS_STRATEGY_INVENTION.md` — bounded declarative invention and prohibited self-writing behaviour.
- `GOVERNED_EXPERIMENTS_AND_PROMOTION.md` — shadow/canary/main DEMO promotion and rollback.
- `LEARNING_AND_AI_BOUNDARIES.md` — StrategyMemory/ML/AI authority limits and evidence isolation.

## 50 — Operator

Planned documents:

- `DASHBOARD_AND_UX.md` — terminal dashboard layout, state visibility and operator controls.
- `USER_MANUAL.md` — concept-to-shutdown operator guide; explains behaviour without redefining internal contracts.
- `SETUP_AND_RUN_GUIDE.md` — installation, MT5/DEMO setup, startup, shutdown and troubleshooting steps.

## 60 — Engineering

| Document | Status | Purpose |
|---|---|---|
| [Coder Guide](60-engineering/CODER_GUIDE.md) | DRAFT | Developer-facing feature ownership/change-path/troubleshooting guide |
| `MODULE_STRUCTURE.md` | Upcoming | Compact file-by-file ownership and dependency map once modules exist |
| `TESTING_AND_VERIFICATION.md` | Upcoming | Test taxonomy, parity, security/static/runtime validation requirements |
| `RELEASE_CHECKLIST.md` | Upcoming | Exact release gates and sign-off checklist |
| `FINAL_RELEASE_AUDIT.md` | Upcoming | Evidence-backed snapshot of what actually passed/failed/pending |

`CODER_GUIDE.md` is feature-oriented; `MODULE_STRUCTURE.md` is file-oriented. They must not become duplicate documents.

## 90 — Governance

| Document | Status | Purpose |
|---|---|---|
| [Design Decisions](90-governance/DESIGN_DECISIONS.md) | Living ledger | Accepted/provisional decisions and rationale |
| [Open Questions](90-governance/OPEN_QUESTIONS.md) | Living ledger | Unresolved choices that must not be silently guessed |
| [Documentation Standard](90-governance/DOCUMENTATION_STANDARD.md) | PROVISIONAL | Placement, authority, status, duplication and change-control rules for docs |

## Root-level handoff

- [`../FINAL_BUILD_PROMPT.md`](../FINAL_BUILD_PROMPT.md) — DRAFT implementation handoff. It is frozen only after the core design is frozen and required open questions are resolved or explicitly deferred.

## Authority rule

When documents conflict, use this precedence until the contradiction is formally resolved:

1. `00-foundation/SYSTEM_CONTRACT.md`
2. The specific authoritative topic document
3. `90-governance/DESIGN_DECISIONS.md`
4. Supporting engineering/operator documentation
5. Root `FINAL_BUILD_PROMPT.md` must summarize frozen requirements, not override them

No implementation should silently resolve a documented contradiction by guessing.