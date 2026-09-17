# GoldSwingTraderAI — Final Build Prompt

**Status:** DRAFT — DO NOT IMPLEMENT FROM THIS YET  
**Version:** 0.2-design
**Location:** Repository root by design. This is an implementation handoff artifact, not a topic authority.

This file becomes the final implementation contract only after the core design documents are frozen and unresolved items are either decided or explicitly deferred.

## Role

You are implementing **GoldSwingTraderAI**, a fresh and independent XAUUSD/XAUUSDm trading system designed to capture meaningful swing and intraday directional moves using an institutional-style parallel decision architecture.

Do not infer requirements from unrelated prior projects. Do not copy legacy code, comments, filenames or compatibility layers merely because they existed elsewhere. The repository documentation is authoritative.

## Authority order

Read and obey, in order:

1. `docs/00-foundation/SYSTEM_CONTRACT.md`
2. The authoritative topic document for the feature being implemented
3. `docs/90-governance/DESIGN_DECISIONS.md`
4. `docs/90-governance/OPEN_QUESTIONS.md`
5. Supporting engineering/operator documentation

If documents conflict, stop and resolve the contradiction in documentation rather than silently choosing one interpretation. This prompt summarizes frozen requirements; it does not override their authoritative source documents.

## Project principles

Implementation must preserve:

- H4/H1/M15/M5 multi-timeframe design;
- completed-candle structural authority;
- parallel specialist desks rather than one long filter chain;
- independent BUY and SELL theses;
- separate Opportunity and Entry Timing scores;
- explicit conflict/red-team handling;
- persistent setup lifecycle and WAIT semantics;
- hard risk/news/broker/data authority outside weighted scoring;
- one governed irreversible broker submission followed by reconciliation;
- durable lifecycle/restart state;
- structural trade management for large moves;
- governed research/discovery without arbitrary self-writing code.

## Prohibited shortcuts

Do not:

- turn every soft signal into a hard gate;
- treat missing optional evidence as score zero;
- let a high score override risk or execution safety;
- make RSI/EMA/FVG/OB alone the trading authority;
- use future candles or look-ahead in replay;
- redefine original R after trailing;
- blind-retry ambiguous broker submissions;
- generate/eval/exec arbitrary Python as autonomous strategy invention;
- silently decide any item still listed as unresolved in `docs/90-governance/OPEN_QUESTIONS.md`.

## Intended implementation sequence

The final sequence will be refined, but implementation is expected to proceed approximately as follows:

1. Project/package skeleton and immutable contracts.
2. Market-data and completed-candle synchronization.
3. Candle/structure/liquidity intelligence primitives.
4. Parallel specialist-desk interfaces.
5. Production strategy floor.
6. BUY/SELL thesis construction and decision fusion.
7. Persistent setup lifecycle and entry-timing board.
8. Trade planning and structural targets/stops.
9. Risk/session/safety authority.
10. Durable order lifecycle, execution and reconciliation.
11. Open-trade management / trailing / runner logic.
12. Replay, diagnostics and opportunity research.
13. Governed strategy discovery and autonomous invention.
14. Dashboard/operator UX.
15. DEMO readiness and release validation.

Each phase must include executable tests for its frozen behavioural invariants before the phase is treated as complete.

## Validation principle

Documentation completion is not implementation proof. Static checks are not runtime proof. Historical backtests are not profitability proof. A final release may only claim the validation that actually executed against the exact code being released.

## Current restriction

This file is a living draft. Do not begin production implementation solely from it while any required core document remains PROVISIONAL or a necessary behaviour is unresolved.