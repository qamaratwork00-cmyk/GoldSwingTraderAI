# GoldSwingTraderAI Documentation Index

This folder is the design source of truth for GoldSwingTraderAI. Core rule:

> **One topic, one authoritative home. Supporting documents link to that authority instead of creating competing versions.**

## Status meanings

- **DRAFT** — incomplete working document.
- **PROVISIONAL** — current agreed direction; still open to refinement/calibration.
- **FROZEN** — approved behavioural contract for implementation.
- **IMPLEMENTED** — corresponding behaviour exists in code.
- **VERIFIED** — the exact implementation passed required executable validation.

`FINAL_BUILD_PROMPT.md` intentionally lives at repository root because it is an implementation handoff artifact, not a topic authority.

## Folder ownership

| Folder | Owns |
|---|---|
| `00-foundation/` | Mission, system-wide invariants, high-level architecture, trading-floor ownership |
| `10-market-intelligence/` | Market facts/inference: data, candles, structure, levels, liquidity, indicators, macro, sessions |
| `20-trading-decisions/` | Strategy families, theses, scoring/fusion, entry timing, Trade Plan, exits |
| `30-risk-execution/` | Monetary risk, permission states, broker-write safety, persistence/restart/reconciliation |
| `40-research-learning/` | Replay/validation, discovery, invention, experiments/promotion, learning/AI boundaries |
| `50-operator/` | Dashboard, user manual, setup/run and operator workflows |
| `60-engineering/` | Module map, coder guide, diagnostics, testing, release gates and final audit |
| `90-governance/` | Design decisions, open questions and documentation/change governance |

## 00 — Foundation

| Document | Status | Purpose |
|---|---|---|
| [Project Vision](00-foundation/PROJECT_VISION.md) | PROVISIONAL | Mission, trading personality, timeframe intent and non-goals |
| [System Contract](00-foundation/SYSTEM_CONTRACT.md) | PROVISIONAL | Highest-level behavioural contract |
| [Architecture](00-foundation/ARCHITECTURE.md) | PROVISIONAL | High-level system flow and authority boundaries |
| [Trading Floor Architecture](00-foundation/TRADING_FLOOR_ARCHITECTURE.md) | PROVISIONAL | Specialist desks, BUY/SELL teams, debate/red-team and authority model |

Foundation documents remain high-level; detailed subsystem rules live below.

## 10 — Market Intelligence

| Document | Status | Purpose |
|---|---|---|
| [Market Data and History](10-market-intelligence/MARKET_DATA_AND_HISTORY.md) | PROVISIONAL | Rolling history, timeframe data and data-quality rules |
| [Candle Structure and Price Behaviour](10-market-intelligence/CANDLE_STRUCTURE.md) | PROVISIONAL | Candle sequences, swing lifecycle, BOS/MSS, displacement, rejection, compression/expansion |
| [Technical Structure and Levels](10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md) | PROVISIONAL | S/R zones, range context, location and target room |
| [Liquidity and SMC](10-market-intelligence/LIQUIDITY_AND_SMC.md) | PROVISIONAL | Liquidity pools/sweeps, FVG, qualified OB, premium/discount and path |
| [Indicators and Volatility](10-market-intelligence/INDICATORS_AND_VOLATILITY.md) | PROVISIONAL | EMA/RSI/ATR, volatility, momentum, extension and quantitative support |
| [Fundamental and News](10-market-intelligence/FUNDAMENTAL_AND_NEWS.md) | PROVISIONAL | Macro opinion, event facts and provider health; final hard permission is owned by risk/session safety |
| [Session Context](10-market-intelligence/SESSION_CONTEXT.md) | PROVISIONAL | Asia/London/New York market evidence; not the hard risk/session state machine |

## 20 — Trading Decisions

| Document | Status | Purpose |
|---|---|---|
| [Strategy Floor](20-trading-decisions/STRATEGY_FLOOR.md) | PROVISIONAL | Parallel production strategy families |
| [Entry Timing](20-trading-decisions/ENTRY_TIMING.md) | PROVISIONAL | Persistent setup lifecycle and executable timing |
| [Scoring and Decision Fusion](20-trading-decisions/SCORING_AND_DECISION_FUSION.md) | PROVISIONAL | BUY/SELL theses, conflict, scoring, Red Team and why-no-trade attribution |
| [Trade Plan](20-trading-decisions/TRADE_PLAN.md) | PROVISIONAL | Entry reference, structural invalidation/SL, targets and immutable original R |
| [Trade Manager and Exit](20-trading-decisions/TRADE_MANAGER_AND_EXIT.md) | PROVISIONAL | HOLD/PROTECT/TRAIL/RUNNER/EXIT and post-entry structural management |

## 30 — Risk and Execution

| Document | Status | Purpose |
|---|---|---|
| [Risk Contract](30-risk-execution/RISK_CONTRACT.md) | PROVISIONAL | Monetary risk, dynamic sizing, UTC risk day, loss lock/manual reset and exposure |
| [Session and Risk State Machine](30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md) | PROVISIONAL | Hard market/news/risk/system permission states and composition |
| [Execution and Broker Safety](30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md) | PROVISIONAL | Central Execution Permission Gate, MT5 identity/specs, one-shot writes and reconciliation |
| [Persistence, Restart and Recovery](30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md) | PROVISIONAL | Durable lifecycle, portable Strategy Registry, backup/restore and laptop migration |

## 40 — Research and Learning

| Document | Status | Purpose |
|---|---|---|
| [Research and Validation](40-research-learning/RESEARCH_AND_VALIDATION.md) | PROVISIONAL | Chronological replay, validation, holdouts, stress/WFA and evidence reporting |
| [Governed Strategy Discovery](40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md) | PROVISIONAL | Parameter/recipe candidate discovery and comparison |
| [Autonomous Strategy Invention](40-research-learning/AUTONOMOUS_STRATEGY_INVENTION.md) | PROVISIONAL | Bounded declarative invention, genealogy and prohibited self-writing behaviour |
| [Governed Experiments and Promotion](40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md) | PROVISIONAL | Champion/Challenger, holdout, Shadow, DEMO Canary, promotion and rollback |
| [Learning and AI Boundaries](40-research-learning/LEARNING_AND_AI_BOUNDARIES.md) | PROVISIONAL | StrategyMemory, entry/exit learning, ML/AI authority limits and evidence isolation |

A separate `OFFLINE_RESEARCH.md` is intentionally not used: offline methodology belongs in `RESEARCH_AND_VALIDATION.md`, while candidate discovery/invention/promotion have their own authorities. This avoids duplicate research specifications.

## 50 — Operator

| Document | Status | Purpose |
|---|---|---|
| [Dashboard and UX](50-operator/DASHBOARD_AND_UX.md) | PROVISIONAL | Compact terminal dashboard, restrained emojis, decision trace, execution permission, health/backup visibility |
| [User Manual](50-operator/USER_MANUAL.md) | DRAFT | Normal operation, WAIT/BLOCKED handling, governed controls and safety guidance |
| [Setup and Run Guide](50-operator/SETUP_AND_RUN_GUIDE.md) | DRAFT | First setup, startup/shutdown, migration, restore and troubleshooting workflow |

## 60 — Engineering

| Document | Status | Purpose |
|---|---|---|
| [Coder Guide](60-engineering/CODER_GUIDE.md) | DRAFT | Feature-oriented ownership/change/debugging map; includes centralized broker-write permission feature |
| [Module Structure](60-engineering/MODULE_STRUCTURE.md) | DRAFT | File/module-oriented planned ownership and dependency direction |
| [System Health and Diagnostics](60-engineering/SYSTEM_HEALTH_AND_DIAGNOSTICS.md) | PROVISIONAL | Fault severity, trading impact, recovery and overall-health aggregation |
| [Testing and Verification](60-engineering/TESTING_AND_VERIFICATION.md) | PROVISIONAL | No-lookahead, execution gate, crash/restart, migration, learning and DEMO test architecture |
| [Release Checklist](60-engineering/RELEASE_CHECKLIST.md) | PROVISIONAL | DEMO release gates and sign-off checklist |
| [Final Release Audit](60-engineering/FINAL_RELEASE_AUDIT.md) | DRAFT TEMPLATE | Evidence-backed release snapshot; PASS only after tests actually execute |

`CODER_GUIDE.md` is feature-oriented. `MODULE_STRUCTURE.md` is file/module-oriented. They must stay synchronized without becoming duplicate behavioural contracts.

## 90 — Governance

| Document | Status | Purpose |
|---|---|---|
| [Design Decisions](90-governance/DESIGN_DECISIONS.md) | Living ledger | Accepted/provisional architectural decisions and rationale |
| [Open Questions](90-governance/OPEN_QUESTIONS.md) | Living ledger | Remaining calibration/implementation choices that must not be silently guessed |
| [Documentation Standard](90-governance/DOCUMENTATION_STANDARD.md) | PROVISIONAL | Placement, authority, status, duplication and change-control rules |

## Root-level handoff

- [`../FINAL_BUILD_PROMPT.md`](../FINAL_BUILD_PROMPT.md) — DRAFT implementation handoff until required design contracts are frozen and remaining implementation-critical questions are resolved/deferred.

## Key cross-document boundaries

- Candle Structure owns BOS/MSS/swing geometry; Technical and Liquidity consume it rather than redefine it.
- Technical owns generic zones/location/target room; Liquidity owns pools/sweeps/FVG/OB/premium-discount interpretation.
- Fundamental/News publishes facts/opinion; Session/Risk state owns final hard news permission.
- Trade Plan owns initial entry/SL/targets/original R; Trade Manager owns post-entry changes/exits.
- Risk owns monetary affordability; Execution owns the centralized final broker-write permission and irreversible MT5 path.
- Scoring/Fusion owns decision attribution (`why no trade`); System Health owns technical/operational fault aggregation; Dashboard displays both.
- Persistence owns storage/recovery/backup mechanics; research docs own strategy/learning semantics.

## Authority rule

When documents conflict, use this precedence until the contradiction is formally resolved:

1. `00-foundation/SYSTEM_CONTRACT.md`
2. The specific authoritative topic document
3. `90-governance/DESIGN_DECISIONS.md`
4. `90-governance/OPEN_QUESTIONS.md` for explicitly unresolved choices
5. Supporting engineering/operator documentation
6. Root `FINAL_BUILD_PROMPT.md` summarizes frozen requirements; it does not override them

No implementation should silently resolve a documented contradiction by guessing.
