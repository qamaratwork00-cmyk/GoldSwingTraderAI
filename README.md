# GoldSwingTraderAI

> Institutional-style XAUUSD/XAUUSDm trading system designed to capture meaningful swing and intraday moves using multi-timeframe structure, parallel market intelligence, intelligent entry/exit timing, governed learning/discovery, and broker-aware risk/execution safety.

**Project status:** Design phase — architecture corpus substantially documented; no production trading implementation yet.

GoldSwingTraderAI is being designed as a fresh, independent Gold trading system. Its purpose is not to scalp every small fluctuation or wait only for ultra-rare perfect setups. The system is intended to identify meaningful opportunities, time entries intelligently, manage open positions around market structure, and stay in strong moves long enough to capture substantial directional expansion.

The architecture follows a trading-floor model: multiple specialist desks analyse the same verified market snapshot in parallel, independent BUY and SELL theses compete, a debate/Red-Team layer challenges the leading case, Decision Fusion combines evidence, a structural Trade Plan is built, independent hard-risk/safety authorities evaluate it, and one centralized Execution Permission Gate controls the final broker-write path.

## Start here

- [`docs/README.md`](docs/README.md) — full documentation map, status and authority index.
- [`docs/00-foundation/SYSTEM_CONTRACT.md`](docs/00-foundation/SYSTEM_CONTRACT.md) — highest-level behavioural contract.
- [`docs/00-foundation/ARCHITECTURE.md`](docs/00-foundation/ARCHITECTURE.md) — high-level system architecture.
- [`docs/00-foundation/TRADING_FLOOR_ARCHITECTURE.md`](docs/00-foundation/TRADING_FLOOR_ARCHITECTURE.md) — specialist-desk ownership model.
- [`docs/60-engineering/CODER_GUIDE.md`](docs/60-engineering/CODER_GUIDE.md) — feature-oriented developer map, including the centralized broker-write permission feature.
- [`docs/60-engineering/MODULE_STRUCTURE.md`](docs/60-engineering/MODULE_STRUCTURE.md) — planned module/dependency ownership map.
- [`FINAL_BUILD_PROMPT.md`](FINAL_BUILD_PROMPT.md) — root-level implementation handoff; currently DRAFT, not yet an implementation authorization.

## Core design direction

- XAUUSD/XAUUSDm focused.
- H4/H1/M15/M5 multi-timeframe understanding.
- Completed-candle structural authority and explicit no-lookahead replay chronology.
- Parallel candle/structure, technical/location, liquidity/SMC, indicator/quant, fundamental/session and strategy intelligence.
- Separate Opportunity Score and Entry Timing Score.
- Independent BUY Thesis and SELL Thesis with explicit conflict/Red-Team handling.
- Persistent setup lifecycle so a good idea can WAIT for efficient timing instead of disappearing.
- Structural Trade Plan before monetary sizing; original R remains immutable.
- Broker-aware dynamic risk, daily-loss/manual-reset state and hard safety outside soft scoring.
- One centralized Execution Permission Gate and one governed MT5 create/modify/close path.
- One-shot irreversible submission; ambiguous broker acknowledgement is reconciled, never blind-retried.
- DEMO-first broker-write release policy; a future explicitly approved REAL mode uses the same engine/path rather than a separate hidden live implementation.
- Single active execution controller per managed account/symbol.
- Restart/laptop migration preserves Strategy Registry, learning, lifecycle and promotion history.
- Public-repository disaster-recovery backups may include project intelligence; actual financial-authority credentials/keys/tokens must not be committed.
- Structure-led HOLD/PROTECT/TRAIL/RUNNER/EXIT management for large moves.
- Entry/Exit Learning, StrategyMemory, governed discovery and declarative autonomous invention.
- Research analyses taken, missed, blocked/rejected and invalidated opportunities—not only completed trades.
- Compact dashboard with explicit reason codes, separate System Health, and restrained emoji status markers.

## Documentation-first development

The documentation under `docs/` is the design source of truth. Core behaviour is discussed, documented, audited for contradictions, and frozen/deferred before production implementation proceeds.

Document statuses use:

- `DRAFT` — incomplete working document.
- `PROVISIONAL` — current agreed direction, still open to refinement/calibration.
- `FROZEN` — design contract approved for implementation.
- `IMPLEMENTED` — corresponding behaviour exists in code.
- `VERIFIED` — implementation passed the required executable validation.

Detailed placement/ownership rules live in [`docs/90-governance/DOCUMENTATION_STANDARD.md`](docs/90-governance/DOCUMENTATION_STANDARD.md). Remaining unresolved calibration/implementation choices are tracked in [`docs/90-governance/OPEN_QUESTIONS.md`](docs/90-governance/OPEN_QUESTIONS.md) rather than guessed in code.
