# GoldSwingTraderAI

> Institutional-style XAUUSD/XAUUSDm trading system designed to capture meaningful intraday/open-session Gold moves using multi-timeframe structure, parallel market intelligence, intelligent entry/exit timing, governed learning/discovery, and broker-aware risk/execution safety.

**Project status:** Design close-out — architecture and V1 behavioural direction are substantially documented; production trading implementation has not started yet.

GoldSwingTraderAI is a fresh, independent Gold trading system. It is not intended to scalp every tiny fluctuation or wait only for ultra-rare perfect setups. It should identify meaningful opportunities, time entries intelligently, manage positions around structure, and remain in strong moves long enough to capture substantial expansion while respecting hard safety.

## Start here

- [`docs/README.md`](docs/README.md) — documentation index and authority map.
- [`docs/FINAL_BUILD_PROMPT.md`](docs/FINAL_BUILD_PROMPT.md) — current implementation handoff candidate.
- [`docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md`](docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md) — large build phases, resume/recovery and completion procedure.
- [`docs/USER_MANUAL.md`](docs/USER_MANUAL.md) — operator-facing behaviour guide.
- [`docs/SETUP_AND_RUN_GUIDE.md`](docs/SETUP_AND_RUN_GUIDE.md) — setup/startup/shutdown/migration/recovery guide.
- [`docs/CODER_GUIDE.md`](docs/CODER_GUIDE.md) — feature-oriented developer map.
- [`docs/00-foundation/SYSTEM_CONTRACT.md`](docs/00-foundation/SYSTEM_CONTRACT.md) — highest-level behavioural contract.
- [`docs/60-engineering/MODULE_STRUCTURE.md`](docs/60-engineering/MODULE_STRUCTURE.md) — planned module/dependency ownership map.

## Core design direction

- XAUUSD/XAUUSDm focused.
- H4/H1/M15/M5 multi-timeframe understanding.
- Completed-candle structural authority and explicit no-lookahead replay chronology.
- Parallel specialist desks rather than one long filter chain.
- Independent BUY and SELL theses with Red-Team/conflict handling.
- Separate Opportunity and Entry Timing dimensions.
- Six initial parallel strategy families.
- Structural Trade Plan before monetary sizing; original R immutable.
- Broker-aware hybrid risk with SMALL/MEDIUM/NORMAL profiles.
- Position capacity `0/1` for independently risk-bearing Gold exposure.
- One centralized Execution Permission Gate and one governed MT5 create/modify/close path.
- Positive V1 DEMO guard: verified connected DEMO account is required for broker-write permission.
- One-shot irreversible submission with reconciliation after ambiguous acknowledgement.
- One active execution controller with shared lease/fencing for multi-machine safety.
- Scheduled XAU close flattening; no intentional carry through known daily/weekend closure gaps.
- Structure-led HOLD/PROTECT/TRAIL/RUNNER/EXIT management for large moves.
- Entry/Exit Learning, StrategyMemory, governed discovery and declarative autonomous invention.
- Restart/laptop migration preserves critical lifecycle, risk, strategy and learning state.
- Public-repository disaster-recovery backup may include project intelligence; financial-authority credentials/keys/tokens must never be committed.
- Compact dashboard with explicit reason codes and separate Decision, Execution, Learning, Backup and Health visibility.

## Documentation-first development

The documentation under `docs/` is the design source of truth. One behavioural rule should have one authoritative home; supporting guides point to that authority rather than create competing versions.

Document statuses:

- `DRAFT` — incomplete working document.
- `PROVISIONAL` — current agreed direction, still open to refinement/calibration.
- `FROZEN` — approved design contract for implementation.
- `IMPLEMENTED` — corresponding behaviour exists in code.
- `VERIFIED` — exact implementation passed required executable validation.

Remaining calibration and ordinary implementation choices are classified in [`docs/90-governance/OPEN_QUESTIONS.md`](docs/90-governance/OPEN_QUESTIONS.md) so they do not unnecessarily delay the build.
