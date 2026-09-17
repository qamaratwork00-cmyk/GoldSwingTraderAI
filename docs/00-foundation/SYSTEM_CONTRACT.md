# GoldSwingTraderAI — System Contract

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Highest-level behavioural contract

## Core contract

GoldSwingTraderAI is an XAUUSD/XAUUSDm trading system built around multi-timeframe structure, parallel specialist analysis, independent BUY/SELL theses, explicit timing evaluation, hard risk authority and governed research.

If another document conflicts with this contract, this document wins until the conflict is formally resolved in the design-decision ledger.

## Market-analysis contract

- H4, H1, M15 and M5 are the primary design timeframes.
- Completed candles are authoritative for structural decisions; unfinished candles may supply telemetry only where explicitly allowed.
- Market analysis runs in parallel rather than as a long sequential filter chain.
- Candle, structure, liquidity, technical, indicator, fundamental/session, expansion, strategy and timing specialists may all produce evidence.
- Each analytical desk should, where meaningful, return BUY evidence, SELL evidence, confidence/coverage and reasons.
- Missing non-safety evidence is not automatically scored as bearish or zero; it is marked unavailable/unknown.
- Strong opposing evidence matters more than merely missing confluence.

## Decision contract

The decision system maintains at least:

- BUY Thesis
- SELL Thesis
- Directional Edge
- Conflict / Red-Team objection
- Opportunity Score
- Entry Timing Score
- Evidence Coverage / Confidence
- Final Trade Score for operator visibility

A strong opportunity may remain `ARMED` while entry timing is poor. Temporary timing weakness should normally produce `WAIT`, not destroy the setup.

## Strategy-floor contract

Initial production-family candidates are currently provisional:

1. TREND_PULLBACK_CONTINUATION
2. BREAKOUT_EXPANSION
3. BREAKOUT_RETEST_CONTINUATION
4. LIQUIDITY_SWEEP_REVERSAL
5. FAILED_BREAKOUT_REVERSAL
6. COMPRESSION_EXPANSION

FVG, Order Block, premium/discount, session highs/lows, EMA, RSI, ATR and candle patterns are primarily evidence primitives, not automatically separate production strategies.

All strategy families evaluate the same verified market snapshot in parallel. Compatible agreement may add bounded support; correlated evidence must not be double-counted as independent certainty.

## Timing contract

- M15 primarily identifies opportunity/location/target context.
- M5 primarily identifies the executable moment.
- Setup state and entry decision are separate.
- Entry decisions include at least: ENTER BUY, ENTER SELL, WAIT, MISSED, INVALID and BLOCKED.
- Valid second-chance entries are allowed when the original thesis survives and a genuinely fresh structural trigger appears.
- Chase detection must not erase a valid opportunity; it should normally defer entry until price/structure becomes efficient again.

## Risk and safety contract

Risk/safety are not weighted scoring components. They return hard authority such as PASS/BLOCK/UNKNOWN.

A high strategy score cannot override:

- invalid or stale market data;
- unacceptable broker/account state;
- hard daily-loss lock;
- hard news/event block;
- unacceptable monetary risk or margin;
- unresolved order state;
- unsafe execution conditions.

Daily-loss-limit and deliberate manual-reset behaviour are retained as an operator-governed risk feature. Exact automatic risk-cycle boundary and reopen semantics remain documented separately until frozen.

## Execution contract

The irreversible broker path should remain narrow:

validated decision → trade plan → risk approval → execution safety → persist intent → broker pre-check → one governed submit → reconciliation.

Ambiguous acknowledgement must never trigger blind duplicate submission.

## Trade-management contract

Open-trade management is a second decision floor. It evaluates continuation and reversal evidence in parallel and may return:

- HOLD
- PROTECT
- TRAIL
- RUNNER
- EXIT

Trailing should primarily follow proven market structure with volatility-aware buffering. It should not mechanically tighten on every small profit fluctuation. The original approved risk/R definition must remain immutable for performance and lifecycle accounting.

## Research contract

Research must evaluate not only completed trades but also rejected, missed and invalidated opportunities. Governed strategy discovery and autonomous invention may propose bounded candidate policies/recipes but may not directly rewrite live code, risk controls, broker permissions or safety gates.

No `eval`, `exec`, arbitrary generated Python or silent self-modification is part of the intended autonomous strategy design.

## Development contract

No production trading implementation should be considered complete until the relevant design docs are frozen, executable tests exist, replay/live parity has been addressed, and the exact implementation has passed its required validation gates.
