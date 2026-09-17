# GoldSwingTraderAI

> Institutional-style XAUUSD trading system designed to capture large swing and intraday moves using multi-timeframe structure, parallel market intelligence, intelligent entry/exit timing, governed strategy discovery, and broker-aware risk management.

**Project status:** Design phase — no production trading implementation yet.

GoldSwingTraderAI is being designed as a fresh, independent Gold trading system. Its purpose is not to scalp every small fluctuation or wait only for ultra-rare perfect setups. The system is intended to identify meaningful XAUUSD/XAUUSDm opportunities, time entries intelligently, manage open positions around market structure, and stay in strong moves long enough to capture substantial directional expansion.

The architecture follows an institutional trading-floor model: multiple specialist desks analyse the same verified market snapshot in parallel, independent BUY and SELL theses compete, a debate/red-team layer challenges the leading case, a decision-fusion layer combines evidence, and independent risk/safety authorities retain veto power before execution.

## Core design direction

- XAUUSD/XAUUSDm focused.
- Multi-timeframe market understanding with H4, H1, M15 and M5.
- Completed-candle decision authority; no look-ahead.
- Parallel candle, structure, liquidity, technical, indicator, fundamental, strategy and timing intelligence.
- Separate Opportunity Score and Entry Timing Score.
- Independent BUY Thesis and SELL Thesis with explicit conflict measurement.
- Strategy scoring is flexible; broker/risk/news/system safety remains hard-authority.
- Persistent setup lifecycle so a valid opportunity can wait for a better entry instead of disappearing.
- Structure-led trailing, exit and runner management for large moves.
- Governed strategy discovery and bounded autonomous strategy invention.
- Research must analyse taken, rejected and missed opportunities—not only completed trades.
- DEMO-first development and validation.

## Documentation-first development

The documentation under `docs/` is the design source of truth. Core behaviour will be discussed, documented, audited for contradictions, and frozen before implementation begins.

Document statuses use:

- `DRAFT` — incomplete working document.
- `PROVISIONAL` — current agreed direction, still open to refinement.
- `FROZEN` — design contract approved for implementation.
- `IMPLEMENTED` — corresponding behaviour exists in code.
- `VERIFIED` — implementation has passed the required executable validation.

The repository intentionally starts with design documents before trading code so implementation does not inherit accidental architecture or undocumented assumptions.