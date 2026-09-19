# GoldSwingTraderAI

> Institutional-style XAUUSD/XAUUSDm trading system designed to capture meaningful intraday/open-session Gold moves using multi-timeframe structure, parallel market intelligence, intelligent entry/exit timing, governed learning/discovery, and broker-aware risk/execution safety.

**Project status:** Core deterministic subsystem implementation now includes the **Phase 12 runtime foundation**: market/data/intelligence, strategy/decision, Trade Plan/risk, session/news permission, SQLite persistence, centralized execution/reconciliation, Trade Manager, dashboard, replay/learning, governed discovery/invention/promotion, portable checkpoint/restore, live startup recovery, persistent M5 orchestration, provider-neutral session/news handoff and live dashboard DTO wiring all exist with CI-backed tests. The default `goldswing` mode remains **read-only MT5 readiness** and now stays alive in a bounded wait when market data is stale/warming up; explicit `PRIMARY`/`STANDBY` modes enter the controller-gated persistent runtime, wait safely for retryable stale market data before `READY`, and fail closed until a configured session/news snapshot or injected provider is supplied. Selection/operation of the accepted external producer, real shared cross-laptop proof, controlled Windows MT5 DEMO lifecycle, broad real-XAU validation and final release audit remain pending.

GoldSwingTraderAI is a fresh, independent Gold trading system. It is not intended to scalp every tiny fluctuation or wait only for ultra-rare perfect setups. It should identify meaningful opportunities, time entries intelligently, manage positions around structure, and remain in strong moves long enough to capture substantial expansion while respecting hard safety.

## Start here

- [`docs/README.md`](docs/README.md) — documentation index and authority map.
- [`docs/FINAL_BUILD_PROMPT.md`](docs/FINAL_BUILD_PROMPT.md) — current implementation handoff candidate.
- [`docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md`](docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md) — large build phases, resume/recovery and completion procedure.
- [`docs/USER_MANUAL.md`](docs/USER_MANUAL.md) — operator-facing behaviour guide.
- [`docs/SETUP_AND_RUN_GUIDE.md`](docs/SETUP_AND_RUN_GUIDE.md) — setup/startup/shutdown/migration/recovery guide.
- [`docs/CODER_GUIDE.md`](docs/CODER_GUIDE.md) — complete phase-by-phase developer manual with feature, source, entry-point, test and operator/evidence ownership.
- [`docs/00-foundation/SYSTEM_CONTRACT.md`](docs/00-foundation/SYSTEM_CONTRACT.md) — highest-level behavioural contract.
- [`docs/60-engineering/CODING_STANDARD.md`](docs/60-engineering/CODING_STANDARD.md) — frozen lightweight production-code standard.
- [`docs/90-governance/DOCUMENTATION_STANDARD.md`](docs/90-governance/DOCUMENTATION_STANDARD.md) — frozen rule that documentation updates preserve meaning and propagate through the whole affected graph.
- [`docs/60-engineering/MODULE_STRUCTURE.md`](docs/60-engineering/MODULE_STRUCTURE.md) — module/dependency ownership map.

## Current implementation checkpoint

Deterministic implementation currently includes:

- Python 3.11+ package/config/domain IDs/reason codes/logging/financial-secret scanner/CI;
- read-only MT5 account/symbol/quote/spec/history layer with XAUUSDm/XAUUSD resolution and completed H4/H1/M15/M5 snapshots;
- candle/structure, technical/location, liquidity/SMC, EMA/RSI/ATR/volatility, session/news intelligence;
- optional causal **Trendline + Fibonacci + broker-local POC/volume-profile confluence**;
- six parallel production strategy families, BUY/SELL fusion, Opportunity lifecycle and M5 Entry Timing;
- structural Trade Plan, immutable original R, frozen RR policy and broker-aware risk/min-lot/daily-lock/cooldown logic;
- positive DEMO guard, session/news hard permission, one-shot Execution Intent, centralized execution gate, MT5 writer/reconciliation and controller lease/fencing semantics;
- SQLite persistence/recovery adapters with checksum/schema/typed state handling;
- explicit `READINESS`/`PRIMARY`/`STANDBY` startup modes, fail-closed session/news wiring, explicit risk-day initialization and verified fresh-DB checkpoint restore;
- persistent M5 cycle orchestration with 10-second controller renewal, governed entry/management path, local verified backup cadence, safe shutdown and live `DashboardData` composition;
- strict account/server/symbol-scoped session/news JSON handoff with UTC/freshness validation and fail-closed launcher wiring;
- public-safe verified-backup staging and fresh-DB restore operator CLIs; publication/push remains an explicit external action;
- read-only Windows/MT5 exact-count dataset acquisition plus verified-bundle fixed-policy walk-forward/evidence-package tooling; real-XAU evidence remains an external certification step;
- HOLD/PROTECT/TRAIL/RUNNER/EXIT Trade Manager and governed execution bridge;
- compact read-only terminal cycle dashboard renderer plus a separate
  READINESS stale-data monitor frame;
- chronological replay, research metrics, StrategyMemory, durable episode journal, working discovery/invention liveness, candidate registry and governed promotion lifecycle.

CI currently protects Ruff, Pytest, the frozen documentation contract and
financial-secret scanning. Deterministic CI is software evidence, not live
broker proof or profitability proof.

## Core design direction

- XAUUSD/XAUUSDm focused.
- H4/H1/M15/M5 multi-timeframe understanding.
- Completed-candle structural authority and explicit no-lookahead chronology.
- Parallel specialist desks rather than one long filter chain.
- Independent BUY and SELL theses with Red-Team/conflict handling.
- Separate Opportunity and Entry Timing dimensions.
- Six initial parallel strategy families.
- Trendline/Fibonacci/POC are **bonus-only optional confluence**: supportive evidence may strengthen a valid setup; missing confluence does not penalize the base strategy; they are not hard gates.
- Structural Trade Plan before monetary sizing; original R immutable.
- Broker-aware hybrid risk with SMALL/MEDIUM/NORMAL profiles and **no arbitrary `$100` floor** for positive SMALL accounts.
- Position capacity `0/1` for independently risk-bearing Gold exposure.
- One centralized Execution Permission Gate and one governed MT5 create/modify/close path.
- Positive V1 DEMO guard only; no separate REAL authorization workflow in V1.
- One-shot irreversible submission with broker reconciliation after ambiguous acknowledgement.
- One active execution controller with lease/fencing semantics for multi-machine safety.
- Scheduled XAU close flattening; no intentional carry through known daily/weekend closure gaps.
- Structure-led HOLD/PROTECT/TRAIL/RUNNER/EXIT management for large moves.
- Entry/Exit Learning, StrategyMemory, governed discovery and declarative autonomous invention.
- Discovery must not be silently inert: eligible recurring evidence creates a candidate or an explicit suppression reason.
- Restart/laptop migration preserves critical lifecycle, risk, strategy and learning state.
- Public-repository disaster-recovery backup may include project intelligence; financial-authority credentials/keys/tokens must never be committed.
- Compact dashboard with explicit reason codes and separate Decision, Execution, Learning/Discovery, Backup and Health visibility.

## Trading personality

The target is **accuracy + healthy valid trade opportunity coverage**, not maximum filtering.

A strong coherent strategy family may lead without every optional primitive agreeing. Missing optional evidence is not score zero. Poor current timing normally means `WAIT`, not deletion of a valid opportunity. Research evaluates Opportunity Recall/missed meaningful moves and trade frequency alongside Net R, drawdown and accuracy.

## Documentation-first development

The documentation under `docs/` is the design source of truth. One behavioural or engineering rule should have one authoritative home; supporting guides point to that authority rather than create competing versions.

Documentation changes follow the frozen whole-project protocol in
[`docs/90-governance/DOCUMENTATION_STANDARD.md`](docs/90-governance/DOCUMENTATION_STANDARD.md): a highlighted omission is treated as a signal to audit the full affected graph. Useful prior meaning is retained or deliberately relocated; authority, architecture, source/test maps, operator/research impact, prompts and release evidence are synchronized before a change is published.

Document statuses:

- `DRAFT` — incomplete working document.
- `PROVISIONAL` — current agreed direction, still open to refinement/calibration.
- `FROZEN` — approved design/engineering contract for implementation.
- `IMPLEMENTED` — corresponding behaviour/rule exists in code/process.
- `VERIFIED` — exact implementation passed required executable validation.

Remaining calibration and implementation choices are classified in [`docs/90-governance/OPEN_QUESTIONS.md`](docs/90-governance/OPEN_QUESTIONS.md) so they do not unnecessarily delay the build.
