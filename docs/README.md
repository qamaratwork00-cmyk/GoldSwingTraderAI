# GoldSwingTraderAI Documentation Index

This folder is the design source of truth for GoldSwingTraderAI.

> **One topic, one authoritative home. Supporting documents link to that authority instead of creating competing versions.**

## Status meanings

- **DRAFT** — incomplete working document.
- **PROVISIONAL** — agreed direction; still open to refinement/calibration.
- **FROZEN** — approved behavioural/engineering contract for implementation.
- **IMPLEMENTED** — corresponding behaviour exists in code.
- **VERIFIED** — exact implementation passed required executable validation.
- **SUPERSEDED** — replaced by a named authoritative document or contract; the
  useful meaning remains traceable through a redirect or replacement note.

## Documentation architecture and proof boundary

```mermaid
flowchart TB
    A["Vision + system contract"] --> B["Verified market facts"]
    B --> C["Strategies + decision fusion"]
    C --> D["Risk + execution authority"]
    D --> E["Persistence + operator runtime"]
    B --> F["Research + validation"]
    F --> C
```

The documentation is written as a set of design contracts: intent first,
facts next, decisions after facts, hard monetary/broker authority after
decisions, and durable/operator/research boundaries alongside the runtime.
The reading order below follows that dependency direction.

Executable software proof is owned by
[`TESTING_AND_VERIFICATION.md`](60-engineering/TESTING_AND_VERIFICATION.md).
Revision-specific live, broker and DEMO evidence is owned by
[`FINAL_RELEASE_AUDIT.md`](60-engineering/FINAL_RELEASE_AUDIT.md). Calibration
and external proof gates are classified in
[`OPEN_QUESTIONS.md`](90-governance/OPEN_QUESTIONS.md). None of these
evidence documents silently overrides a behavioural authority.

### Documentation consistency rule

Whenever a contract, source owner, state, schema or release gate changes,
update the authoritative topic, its module/test map and the relevant operator,
research and release references. Compatibility redirects remain pointers only.

## Quick-access whole-project guides

- [`FINAL_BUILD_PROMPT.md`](FINAL_BUILD_PROMPT.md) — whole-project implementation handoff contract.
- [`CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md`](CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md) — large phases, resume/recovery and project-completion guide.
- [`USER_MANUAL.md`](USER_MANUAL.md) — operator-facing behaviour/manual.
- [`SETUP_AND_RUN_GUIDE.md`](SETUP_AND_RUN_GUIDE.md) — setup, safe READINESS mode, stale-market wait behavior, explicit live startup/recovery modes and persistent-runtime workflow.
- [`CODER_GUIDE.md`](CODER_GUIDE.md) — complete phase-by-phase developer manual with feature, source, entry-point and test ownership, including the DEMO Guard and readiness/runtime traces.
- [`60-engineering/CODING_STANDARD.md`](60-engineering/CODING_STANDARD.md) — **FROZEN** project-wide code quality/dependency/complexity/commenting contract.
- [`90-governance/DOCUMENTATION_STANDARD.md`](90-governance/DOCUMENTATION_STANDARD.md) — **FROZEN** documentation preservation, synchronization, completeness and change-control contract.

Old subfolder locations for User Manual, Setup/Run Guide and Coder Guide are compatibility redirects only.

## Recommended reading order

The documents are interconnected, but a reader should not have to discover the
order by trial and error:

1. [Project Vision](00-foundation/PROJECT_VISION.md) — why the system exists and what it is not.
2. [System Contract](00-foundation/SYSTEM_CONTRACT.md) — system-wide behavioural invariants.
3. [Architecture](00-foundation/ARCHITECTURE.md) — runtime/dataflow and authority boundaries.
4. [Trading Floor Architecture](00-foundation/TRADING_FLOOR_ARCHITECTURE.md) — specialist desks and ownership.
5. The 10, 20 and 30 folders — facts → decisions → hard permission/execution.
6. [Module Structure](60-engineering/MODULE_STRUCTURE.md) and [Coder Guide](CODER_GUIDE.md) — exact phase, source, entry-point and test navigation.
7. [Coding Standard](60-engineering/CODING_STANDARD.md) — how code must be written, commented, optimized and verified.
8. The 40 folder — offline replay, learning, discovery and promotion boundaries.
9. [Setup and Run Guide](SETUP_AND_RUN_GUIDE.md), [User Manual](USER_MANUAL.md) and [Dashboard and UX](50-operator/DASHBOARD_AND_UX.md) — how a human operates the system.
10. [Final Build Prompt](FINAL_BUILD_PROMPT.md) and [ChatGPT Build and Recovery Guide](CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md) — how an implementation agent completes and safely resumes the project.
11. [Documentation Standard](90-governance/DOCUMENTATION_STANDARD.md), then the remaining 90 folder — how documentation stays complete, consistent and frozen.

This is a reading path, not a new authority order. The authority order below
still decides which document owns a rule.

## Folder ownership

| Folder | Owns |
|---|---|
| `00-foundation/` | Mission, system-wide invariants, high-level architecture, trading-floor ownership |
| `10-market-intelligence/` | Market facts/inference: data, candles, structure, levels/confluence, liquidity, indicators, macro, sessions |
| `20-trading-decisions/` | Strategy families, theses, scoring/fusion, entry timing, Trade Plan, exits |
| `30-risk-execution/` | Monetary risk, permission states, broker-write safety, persistence/restart/reconciliation |
| `40-research-learning/` | Replay/validation, discovery, invention, experiments/promotion, learning/AI boundaries |
| `50-operator/` | Dashboard/UX supporting docs; primary User/Setup guides are at docs root |
| `60-engineering/` | Coding standard, module map, diagnostics, testing, release gates/audit; primary Coder Guide at docs root |
| `90-governance/` | Design decisions, freeze matrix/open questions and documentation/change governance |

## Repository implementation coverage

This matrix is the short route from a source area to its documentation and
executable proof. The full feature-level mapping (including exact entry points)
is maintained in the [Coder Guide](CODER_GUIDE.md); the file-level ownership
map is maintained in [Module Structure](60-engineering/MODULE_STRUCTURE.md).

| Source area | What it owns | Primary documentation | Primary proof route |
|---|---|---|---|
| `config/`, `domain/`, `diagnostics/`, `security/` | settings, modes, IDs, enums, typed facts, reason codes, secret-safe logging and scanning | [System Contract](00-foundation/SYSTEM_CONTRACT.md), [Coding Standard](60-engineering/CODING_STANDARD.md) | `tests/test_settings.py`, `test_models.py`, `test_ids.py`, `test_logging.py`, `test_secret_scanner.py`, `test_coding_contract_regressions.py` |
| `market_data/` | the single MT5 read boundary, symbol/spec/quote/history/position facts and normalized market snapshots | [Market Data and History](10-market-intelligence/MARKET_DATA_AND_HISTORY.md) | `tests/test_market_data.py`, `test_intelligence_snapshot.py`, `test_recovery_mt5.py` |
| `intelligence/` | causal structure, technical location/confluence, liquidity/SMC, indicators/volatility, session and news facts | [Market Intelligence](10-market-intelligence/) | `tests/test_intelligence_core.py`, `test_technical_confluence.py`, `test_technical_liquidity.py`, `test_session_news_provider.py` |
| `strategies/`, `decisions/` | six family hypotheses, optional confluence bonus, BUY/SELL fusion, opportunity lifecycle, timing and structural Trade Plan | [Strategy Floor](20-trading-decisions/STRATEGY_FLOOR.md), [Decision docs](20-trading-decisions/) | `tests/test_strategy_decisions.py`, `test_trade_plan_risk.py` |
| `risk/` | monetary sizing, account profiles, exposure/capacity, risk-day, loss lock, reset and cooldown | [Risk Contract](30-risk-execution/RISK_CONTRACT.md), [Session/Risk State Machine](30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md) | `tests/test_trade_plan_risk.py`, `test_risk_state_regressions.py`, `test_small_account_profile.py`, `test_session_news_permissions.py` |
| `execution/` | hard checks, DEMO Guard composition, centralized gate, one-shot Intent, MT5 writer, reconciliation and controller fencing | [Execution and Broker Safety](30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md) | `tests/test_execution_safety.py`, `test_sqlite_coordination.py`, `test_live_startup_runtime.py` |
| `management/` | managed-trade state, HOLD/PROTECT/TRAIL/RUNNER/EXIT and governed modify/close bridge | [Trade Manager and Exit](20-trading-decisions/TRADE_MANAGER_AND_EXIT.md) | `tests/test_trade_manager.py`, `test_management_execution.py`, `test_management_replay.py` |
| `persistence/` | SQLite state/events, typed recovery, checkpoints, backup/catalog and public-safe staging | [Persistence, Restart and Recovery](30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md) | `tests/test_persistence_recovery.py`, `test_runtime_checkpoint.py`, `test_backup_catalog.py`, `test_operator_scripts.py` |
| `app/` | startup composition, live recovery authorities, session/news handoff, governed cycle, persistent loop and dashboard mapping | [Architecture](00-foundation/ARCHITECTURE.md), [Setup and Run](SETUP_AND_RUN_GUIDE.md) | `tests/test_startup_recovery.py`, `test_live_startup_runtime.py`, `test_runtime_loop.py`, `test_app_readiness.py` |
| `operator/` | pure readiness and full-cycle dashboard DTOs/renderers | [Dashboard and UX](50-operator/DASHBOARD_AND_UX.md) | `tests/test_dashboard.py`, `test_app_readiness.py` |
| `research/`, `scripts/` | chronological replay, metrics, datasets, evidence packages, learning, discovery, invention, promotion and safe operator CLIs | [Research and Validation](40-research-learning/RESEARCH_AND_VALIDATION.md), [Research folder](40-research-learning/) | `tests/test_research_*.py`, `test_discovery_*.py`, `test_promotion_governance.py`, `test_walk_forward_script.py` |
| `tests/`, `.github/` | executable contract matrix and repository quality automation | [Testing and Verification](60-engineering/TESTING_AND_VERIFICATION.md), [Release Checklist](60-engineering/RELEASE_CHECKLIST.md) | documentation verifier, full `pytest`, Ruff, compile and financial-secret scan |

If a new source area, feature, state, operator panel, research artifact or
release claim cannot be placed in this matrix and the Coder Guide, the change
has not passed the frozen documentation-completeness gate.

## 00 — Foundation

| Document | Status | Purpose |
|---|---|---|
| [Project Vision](00-foundation/PROJECT_VISION.md) | PROVISIONAL | Mission, trading personality, timeframe intent, non-goals |
| [System Contract](00-foundation/SYSTEM_CONTRACT.md) | PROVISIONAL | Highest-level behavioural contract |
| [Architecture](00-foundation/ARCHITECTURE.md) | PROVISIONAL | High-level system flow/authority boundaries including technical confluence |
| [Trading Floor Architecture](00-foundation/TRADING_FLOOR_ARCHITECTURE.md) | PROVISIONAL | Specialist desks, BUY/SELL teams, debate/red-team and authority model |

## 10 — Market Intelligence

| Document | Status | Purpose |
|---|---|---|
| [Market Data and History](10-market-intelligence/MARKET_DATA_AND_HISTORY.md) | PROVISIONAL | Rolling history, timeframe data and data-quality rules |
| [Candle Structure and Price Behaviour](10-market-intelligence/CANDLE_STRUCTURE.md) | PROVISIONAL | Candle sequences, swing lifecycle, BOS/MSS, displacement, rejection, compression/expansion |
| [Technical Structure and Levels](10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md) | PROVISIONAL | S/R zones, location/target room plus causal Trendline/Fibonacci/broker-local POC confluence ownership |
| [Liquidity and SMC](10-market-intelligence/LIQUIDITY_AND_SMC.md) | PROVISIONAL | Liquidity pools/sweeps, FVG, qualified OB, premium/discount/path |
| [Indicators and Volatility](10-market-intelligence/INDICATORS_AND_VOLATILITY.md) | PROVISIONAL | EMA/RSI/ATR, volatility, momentum, extension |
| [Fundamental and News](10-market-intelligence/FUNDAMENTAL_AND_NEWS.md) | PROVISIONAL | Macro opinion/event facts/provider health; hard permission lives in risk/session safety |
| [Session Context](10-market-intelligence/SESSION_CONTEXT.md) | PROVISIONAL | Asia/London/New York market evidence; not hard permission state |

Trendline/Fibonacci/POC are optional soft confluence in V1. They are not mandatory trade gates.

## 20 — Trading Decisions

| Document | Status | Purpose |
|---|---|---|
| [Strategy Floor](20-trading-decisions/STRATEGY_FLOOR.md) | PROVISIONAL | Six parallel production families + optional bounded confluence support |
| [Entry Timing](20-trading-decisions/ENTRY_TIMING.md) | PROVISIONAL | Persistent setup lifecycle/executable timing |
| [Scoring and Decision Fusion](20-trading-decisions/SCORING_AND_DECISION_FUSION.md) | PROVISIONAL | BUY/SELL theses, conflict/scoring/Red Team/why-no-trade |
| [Trade Plan](20-trading-decisions/TRADE_PLAN.md) | PROVISIONAL | Entry reference, structural invalidation/SL, targets/RR/original R |
| [Trade Manager and Exit](20-trading-decisions/TRADE_MANAGER_AND_EXIT.md) | PROVISIONAL | HOLD/PROTECT/TRAIL/RUNNER/EXIT |

## 30 — Risk and Execution

| Document | Status | Purpose |
|---|---|---|
| [Risk Contract](30-risk-execution/RISK_CONTRACT.md) | PROVISIONAL | Monetary risk, hybrid sizing, UTC risk day, loss lock/reset/exposure |
| [Session and Risk State Machine](30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md) | PROVISIONAL | Hard market/news/risk/system permission states |
| [Session/News Provider Contract](30-risk-execution/SESSION_NEWS_PROVIDER_CONTRACT.md) | PROVISIONAL | Strict provider-neutral live session/news snapshot boundary |
| [Execution and Broker Safety](30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md) | PROVISIONAL | DEMO guard, gate, MT5 safety, one-shot writes, controller/reconciliation |
| [Persistence, Restart and Recovery](30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md) | PROVISIONAL | SQLite durable lifecycle, backup/restore/laptop migration contract |

## 40 — Research and Learning

| Document | Status | Purpose |
|---|---|---|
| [Research and Validation](40-research-learning/RESEARCH_AND_VALIDATION.md) | PROVISIONAL | Chronological replay, validation, ablation, Opportunity Recall, holdouts/stress |
| [Governed Strategy Discovery](40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md) | PROVISIONAL | Working discovery liveness, audited primitives, candidate comparison |
| [Autonomous Strategy Invention](40-research-learning/AUTONOMOUS_STRATEGY_INVENTION.md) | PROVISIONAL | Bounded declarative invention/genealogy/prohibited self-writing |
| [Governed Experiments and Promotion](40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md) | PROVISIONAL | Challenger/holdout/Shadow/DEMO Canary/promotion/rollback |
| [Learning and AI Boundaries](40-research-learning/LEARNING_AND_AI_BOUNDARIES.md) | PROVISIONAL | StrategyMemory, entry/exit learning, AI authority limits |

A separate authoritative `OFFLINE_RESEARCH.md` is intentionally not used.

## 50 — Operator

| Document | Status | Purpose |
|---|---|---|
| [Dashboard and UX](50-operator/DASHBOARD_AND_UX.md) | PROVISIONAL | Compact cycle dashboard plus read-only READINESS wait frame, confluence context, discovery health and reason/execution/health visibility |
| [User Manual](USER_MANUAL.md) | DRAFT | Normal operation/interpretation, safety and operator evidence boundary |
| [Setup and Run Guide](SETUP_AND_RUN_GUIDE.md) | DRAFT | Readiness/live startup modes, persistent runtime, installation, recovery and migration |

## 60 — Engineering

| Document | Status | Purpose |
|---|---|---|
| [Coding Standard](60-engineering/CODING_STANDARD.md) | **FROZEN** | Lightweight production-grade Python/dependency/abstraction/commenting/performance rules |
| [Coder Guide](CODER_GUIDE.md) | PROVISIONAL developer manual | Phase-by-phase feature, source, entry-point, test and operator/evidence ownership |
| [Module Structure](60-engineering/MODULE_STRUCTURE.md) | PROVISIONAL module map | Module/dependency ownership and boundaries |
| [System Health and Diagnostics](60-engineering/SYSTEM_HEALTH_AND_DIAGNOSTICS.md) | PROVISIONAL | Fault severity/trading impact/recovery/health aggregation |
| [Testing and Verification](60-engineering/TESTING_AND_VERIFICATION.md) | PROVISIONAL | No-lookahead, confluence, discovery liveness, execution/recovery/DEMO proof architecture |
| [Release Checklist](60-engineering/RELEASE_CHECKLIST.md) | PROVISIONAL | DEMO release gates/sign-off checklist |
| [Final Release Audit](60-engineering/FINAL_RELEASE_AUDIT.md) | DRAFT TEMPLATE | Evidence-backed release snapshot; PASS only after actual evidence |

## 90 — Governance

| Document | Status | Purpose |
|---|---|---|
| [Design Decisions](90-governance/DESIGN_DECISIONS.md) | Authoritative ledger | Accepted/provisional decisions, including SQLite/confluence/discovery-liveness decisions |
| [Open Questions / Freeze Matrix](90-governance/OPEN_QUESTIONS.md) | Authoritative matrix | Frozen direction vs calibration vs implementation choice vs later work |
| [Documentation Standard](90-governance/DOCUMENTATION_STANDARD.md) | FROZEN | Placement, authority, status, preservation, synchronization, completeness and change-control rules |

## Key boundaries

- Candle Structure owns BOS/MSS/swing geometry.
- Technical owns generic zones/location/target room and documented confluence authority; implementation may split technical/confluence modules for clean code.
- Trendline/Fibonacci/POC are soft bonus/context, not hard permission.
- Liquidity owns pools/sweeps/FVG/OB interpretation.
- Fundamental/News publishes facts/opinion; Session/Risk owns hard news permission.
- Trade Plan owns initial entry/SL/targets/original R; Trade Manager owns post-entry management.
- Risk owns monetary affordability; Execution owns final broker-write path.
- Scoring/Fusion owns decision attribution; System Health owns technical fault aggregation.
- Persistence owns storage/recovery/backup mechanics; research docs own learning/candidate semantics.
- Coding Standard owns source-quality/complexity/dependency/commenting rules.

## Authority rule

When documents conflict:

1. `00-foundation/SYSTEM_CONTRACT.md`
2. specific authoritative topic document
3. `90-governance/DESIGN_DECISIONS.md`
4. `90-governance/OPEN_QUESTIONS.md`
5. `90-governance/DOCUMENTATION_STANDARD.md` for documentation placement, preservation and synchronization rules
6. `60-engineering/CODING_STANDARD.md` for engineering rules
7. supporting engineering/operator docs
8. `FINAL_BUILD_PROMPT.md` as handoff summary only

`DOCUMENTATION_STANDARD.md` is the authority for document placement,
preservation, synchronization and change control; it is not a competing
trading-behaviour authority. Read it before editing docs, then use the
behavioural order above to resolve subsystem meaning.

No implementation should silently resolve contradiction by guessing.
