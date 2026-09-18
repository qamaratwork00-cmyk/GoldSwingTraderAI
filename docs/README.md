# GoldSwingTraderAI Documentation Index

This folder is the design source of truth for GoldSwingTraderAI.

> **One topic, one authoritative home. Supporting documents link to that authority instead of creating competing versions.**

## Status meanings

- **DRAFT** — incomplete working document.
- **PROVISIONAL** — current agreed direction; still open to refinement/calibration.
- **FROZEN** — approved behavioural contract for implementation.
- **IMPLEMENTED** — corresponding behaviour exists in code.
- **VERIFIED** — exact implementation passed required executable validation.

## Quick-access whole-project guides

These important project-wide/operator/developer guides live directly in `docs/` so they are visible immediately:

- [`FINAL_BUILD_PROMPT.md`](FINAL_BUILD_PROMPT.md) — PROVISIONAL final implementation handoff candidate.
- [`CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md`](CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md) — PROVISIONAL large implementation phases, resume/recovery and project-completion guide.
- [`USER_MANUAL.md`](USER_MANUAL.md) — authoritative operator/user manual; DRAFT until implemented commands/UI exist.
- [`SETUP_AND_RUN_GUIDE.md`](SETUP_AND_RUN_GUIDE.md) — authoritative setup/startup/shutdown/restore/migration guide; DRAFT until real commands exist.
- [`CODER_GUIDE.md`](CODER_GUIDE.md) — authoritative feature-oriented developer map; DRAFT until real source modules are implemented.

Old subfolder locations for User Manual, Setup/Run Guide and Coder Guide are compatibility redirects only.

## Folder ownership

| Folder | Owns |
|---|---|
| `00-foundation/` | Mission, system-wide invariants, high-level architecture, trading-floor ownership |
| `10-market-intelligence/` | Market facts/inference: data, candles, structure, levels, liquidity, indicators, macro, sessions |
| `20-trading-decisions/` | Strategy families, theses, scoring/fusion, entry timing, Trade Plan, exits |
| `30-risk-execution/` | Monetary risk, permission states, broker-write safety, persistence/restart/reconciliation |
| `40-research-learning/` | Replay/validation, discovery, invention, experiments/promotion, learning/AI boundaries |
| `50-operator/` | Dashboard/UX and operator-domain supporting docs; primary User/Setup guides are at docs root |
| `60-engineering/` | Module map, diagnostics, testing, release gates and audit; primary Coder Guide is at docs root |
| `90-governance/` | Design decisions, freeze matrix/open questions and documentation/change governance |

## 00 — Foundation

| Document | Status | Purpose |
|---|---|---|
| [Project Vision](00-foundation/PROJECT_VISION.md) | PROVISIONAL | Mission, trading personality, timeframe intent and non-goals |
| [System Contract](00-foundation/SYSTEM_CONTRACT.md) | PROVISIONAL | Highest-level behavioural contract |
| [Architecture](00-foundation/ARCHITECTURE.md) | PROVISIONAL | High-level system flow and authority boundaries |
| [Trading Floor Architecture](00-foundation/TRADING_FLOOR_ARCHITECTURE.md) | PROVISIONAL | Specialist desks, BUY/SELL teams, debate/red-team and authority model |

## 10 — Market Intelligence

| Document | Status | Purpose |
|---|---|---|
| [Market Data and History](10-market-intelligence/MARKET_DATA_AND_HISTORY.md) | PROVISIONAL | Rolling history, timeframe data and data-quality rules |
| [Candle Structure and Price Behaviour](10-market-intelligence/CANDLE_STRUCTURE.md) | PROVISIONAL | Candle sequences, swing lifecycle, BOS/MSS, displacement, rejection, compression/expansion |
| [Technical Structure and Levels](10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md) | PROVISIONAL | S/R zones, range context, location and target room |
| [Liquidity and SMC](10-market-intelligence/LIQUIDITY_AND_SMC.md) | PROVISIONAL | Liquidity pools/sweeps, FVG, qualified OB, premium/discount and path |
| [Indicators and Volatility](10-market-intelligence/INDICATORS_AND_VOLATILITY.md) | PROVISIONAL | EMA/RSI/ATR, volatility, momentum, extension and quantitative support |
| [Fundamental and News](10-market-intelligence/FUNDAMENTAL_AND_NEWS.md) | PROVISIONAL | Macro opinion, event facts and provider health; hard permission lives in risk/session safety |
| [Session Context](10-market-intelligence/SESSION_CONTEXT.md) | PROVISIONAL | Asia/London/New York market evidence; not the hard permission state machine |

## 20 — Trading Decisions

| Document | Status | Purpose |
|---|---|---|
| [Strategy Floor](20-trading-decisions/STRATEGY_FLOOR.md) | PROVISIONAL | Six parallel initial production strategy families |
| [Entry Timing](20-trading-decisions/ENTRY_TIMING.md) | PROVISIONAL | Persistent setup lifecycle and executable timing |
| [Scoring and Decision Fusion](20-trading-decisions/SCORING_AND_DECISION_FUSION.md) | PROVISIONAL | BUY/SELL theses, conflict, scoring, Red Team and why-no-trade attribution |
| [Trade Plan](20-trading-decisions/TRADE_PLAN.md) | PROVISIONAL | Entry reference, structural invalidation/SL, targets, RR and immutable original R |
| [Trade Manager and Exit](20-trading-decisions/TRADE_MANAGER_AND_EXIT.md) | PROVISIONAL | HOLD/PROTECT/TRAIL/RUNNER/EXIT and post-entry structural management |

## 30 — Risk and Execution

| Document | Status | Purpose |
|---|---|---|
| [Risk Contract](30-risk-execution/RISK_CONTRACT.md) | PROVISIONAL | Monetary risk, hybrid sizing, UTC risk day, loss lock/manual reset and exposure |
| [Session and Risk State Machine](30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md) | PROVISIONAL | Hard market/news/risk/system permission states and composition |
| [Execution and Broker Safety](30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md) | PROVISIONAL | DEMO guard, Execution Permission Gate, MT5 safety, one-shot writes, controller lease and reconciliation |
| [Persistence, Restart and Recovery](30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md) | PROVISIONAL | Durable lifecycle, portable Strategy Registry, backup/restore and laptop migration |

## 40 — Research and Learning

| Document | Status | Purpose |
|---|---|---|
| [Research and Validation](40-research-learning/RESEARCH_AND_VALIDATION.md) | PROVISIONAL | Chronological replay, validation, holdouts, stress/WFA and evidence reporting |
| [Governed Strategy Discovery](40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md) | PROVISIONAL | Parameter/recipe candidate discovery and comparison |
| [Autonomous Strategy Invention](40-research-learning/AUTONOMOUS_STRATEGY_INVENTION.md) | PROVISIONAL | Bounded declarative invention, genealogy and prohibited self-writing behaviour |
| [Governed Experiments and Promotion](40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md) | PROVISIONAL | Champion/Challenger, holdout, Shadow, DEMO Canary, promotion and rollback |
| [Learning and AI Boundaries](40-research-learning/LEARNING_AND_AI_BOUNDARIES.md) | PROVISIONAL | StrategyMemory, entry/exit learning, ML/AI authority limits and evidence isolation |

A separate authoritative `OFFLINE_RESEARCH.md` is intentionally not used.

## 50 — Operator

| Document | Status | Purpose |
|---|---|---|
| [Dashboard and UX](50-operator/DASHBOARD_AND_UX.md) | PROVISIONAL | Compact terminal dashboard, reason trace, execution permission, health/backup visibility |
| [User Manual — docs root](USER_MANUAL.md) | DRAFT | Normal operation, WAIT/BLOCKED handling, governed controls and safety guidance |
| [Setup and Run Guide — docs root](SETUP_AND_RUN_GUIDE.md) | DRAFT | Setup, startup/shutdown, migration, restore and troubleshooting workflow |

## 60 — Engineering

| Document | Status | Purpose |
|---|---|---|
| [Coder Guide — docs root](CODER_GUIDE.md) | DRAFT | Feature-oriented ownership/change/debugging map |
| [Module Structure](60-engineering/MODULE_STRUCTURE.md) | DRAFT | File/module-oriented planned ownership and dependency direction |
| [System Health and Diagnostics](60-engineering/SYSTEM_HEALTH_AND_DIAGNOSTICS.md) | PROVISIONAL | Fault severity, trading impact, recovery and overall-health aggregation |
| [Testing and Verification](60-engineering/TESTING_AND_VERIFICATION.md) | PROVISIONAL | No-lookahead, execution gate, crash/restart, migration, learning and DEMO test architecture |
| [Release Checklist](60-engineering/RELEASE_CHECKLIST.md) | PROVISIONAL | DEMO release gates and sign-off checklist |
| [Final Release Audit](60-engineering/FINAL_RELEASE_AUDIT.md) | DRAFT TEMPLATE | Evidence-backed release snapshot; PASS only after tests execute |

`CODER_GUIDE.md` is feature-oriented. `MODULE_STRUCTURE.md` is file/module-oriented.

## 90 — Governance

| Document | Status | Purpose |
|---|---|---|
| [Design Decisions](90-governance/DESIGN_DECISIONS.md) | Living ledger | Accepted/provisional architectural decisions and rationale |
| [Open Questions / Freeze Matrix](90-governance/OPEN_QUESTIONS.md) | Living ledger | Frozen direction vs research calibration vs implementation choice vs later-version work |
| [Documentation Standard](90-governance/DOCUMENTATION_STANDARD.md) | PROVISIONAL | Placement, authority, status, duplication and change-control rules |

## Key boundaries

- Candle Structure owns BOS/MSS/swing geometry; Technical/Liquidity consume it.
- Technical owns generic zones/location/target room; Liquidity owns pools/sweeps/FVG/OB interpretation.
- Fundamental/News publishes facts/opinion; Session/Risk state owns final hard news permission.
- Trade Plan owns initial entry/SL/targets/original R; Trade Manager owns post-entry management.
- Risk owns monetary affordability; Execution owns final broker-write permission/path.
- Scoring/Fusion owns decision attribution; System Health owns technical fault aggregation.
- Persistence owns storage/recovery/backup mechanics; research docs own strategy/learning semantics.

## Authority rule

When documents conflict:

1. `00-foundation/SYSTEM_CONTRACT.md`
2. specific authoritative topic document
3. `90-governance/DESIGN_DECISIONS.md`
4. `90-governance/OPEN_QUESTIONS.md` for explicitly classified unresolved/calibration items
5. supporting engineering/operator docs
6. `FINAL_BUILD_PROMPT.md` as handoff summary only

No implementation should silently resolve a contradiction by guessing.
