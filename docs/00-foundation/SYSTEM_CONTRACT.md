# GoldSwingTraderAI — System Contract

**Status:** PROVISIONAL  
**Version:** 0.2-design  
**Authority:** Highest-level behavioural contract

## Core contract

GoldSwingTraderAI is an XAUUSD/XAUUSDm trading system built around multi-timeframe structure, parallel specialist analysis, independent BUY/SELL theses, explicit opportunity/timing separation, hard risk authority, centralized broker-write permission and governed research/learning.

If another document conflicts with this contract, this document wins until the contradiction is formally resolved in the design-decision ledger.

## Market-analysis contract

- H4, H1, M15 and M5 are the primary design timeframes.
- Completed candles are authoritative for structural decisions; unfinished candles may supply telemetry only where explicitly allowed.
- Market analysis runs in parallel rather than as a long sequential filter chain.
- Candle/structure, technical/location, liquidity/SMC, indicator/quant, fundamental/session and strategy specialists publish bounded evidence.
- Expansion/volatility views may combine Candle + Quant evidence; they must not create competing definitions of the same facts.
- Each analytical desk should, where meaningful, return BUY evidence, SELL evidence, confidence/coverage and reasons.
- Missing optional non-safety evidence is not automatically scored as bearish or zero; it remains unavailable/unknown.
- Strong opposing evidence matters more than merely missing confluence.

## Decision contract

The decision system maintains at least:

- BUY Thesis;
- SELL Thesis;
- Directional Edge;
- Conflict / Red-Team objection;
- Opportunity Score;
- Entry Timing Score;
- Evidence Coverage / Confidence;
- operator-facing Final Trade Score;
- stable decision/reason trace.

A strong opportunity may remain `ARMED` while entry timing is poor. Temporary timing weakness should normally produce `WAIT`, not destroy the setup.

Every meaningful `WAIT`, `MISSED`, `INVALID` or `BLOCKED` state must be attributable to a machine-readable reason plus a concise operator explanation.

## Strategy-floor contract

Initial production-family candidates are currently provisional:

1. `TREND_PULLBACK_CONTINUATION`
2. `BREAKOUT_EXPANSION`
3. `BREAKOUT_RETEST_CONTINUATION`
4. `LIQUIDITY_SWEEP_REVERSAL`
5. `FAILED_BREAKOUT_REVERSAL`
6. `COMPRESSION_EXPANSION`

FVG, qualified Order Block, premium/discount, liquidity pools, session highs/lows, EMA, RSI, ATR and individual candle patterns are primarily evidence primitives, not automatically separate production strategies.

All strategy families evaluate the same verified market snapshot in parallel. Compatible agreement may add bounded support; correlated evidence must not be double-counted as independent certainty.

## Timing and Trade Plan contract

- M15 primarily identifies opportunity/location/target context.
- M5 primarily identifies the executable moment.
- Setup state and entry decision are separate.
- Entry decisions include at least ENTER BUY, ENTER SELL, WAIT, MISSED, INVALID and BLOCKED.
- Valid second-chance entries are allowed only when the original thesis survives and a genuinely fresh structural trigger appears.
- Chase detection should normally defer entry rather than erase a valid opportunity.
- Structural invalidation/SL and market objectives are defined before monetary sizing.
- Risk must reject an unaffordable structural plan rather than tighten its stop merely to fit the account.
- Original approved R remains immutable for lifecycle/performance attribution.

## Risk and safety contract

Risk/safety are not weighted scoring components. They return hard authority such as PASS/BLOCK/UNKNOWN.

A high strategy score cannot override:

- invalid or stale market data;
- unacceptable broker/account state;
- hard daily-loss lock;
- hard news/event block or required news-safety uncertainty;
- unacceptable monetary risk or margin;
- unresolved broker/order lifecycle;
- critical persistence corruption;
- duplicate-controller uncertainty;
- unsafe execution conditions.

Daily-loss lock and deliberate governed manual reset are retained. The current provisional daily-risk boundary is the UTC calendar day (`00:00 UTC`). Exact percentages/accounting/reset count remain under the Risk Contract/open questions.

## Execution contract

The irreversible broker path remains narrow:

```text
validated decision
→ Trade Plan
→ risk/session/news/data/account authorities
→ centralized Execution Permission Gate
→ persist Execution Intent
→ broker pre-check
→ ONE governed irreversible submit
→ classify result
→ verify/reconcile
```

All bot-managed create/modify/close writes must use the governed execution path. Strategy, research, dashboard and learning code may not call raw irreversible MT5 writes directly.

Ambiguous acknowledgement must never trigger blind duplicate submission.

The initial release safeguard is DEMO-first. A real account must not silently gain write authority. Future explicitly approved REAL execution uses the same trading/risk/execution architecture; DEMO-only is a release policy, not a permanent inability to trade LIVE.

## Single-controller contract

For one managed account/symbol, only one bot instance may hold active broker-write authority. Other machines may observe, research or shadow. Failover must reconcile broker/local state before acquiring execution authority.

## Trade-management contract

Open-trade management is a second decision floor. It evaluates continuation and reversal evidence in parallel and may return:

- HOLD;
- PROTECT;
- TRAIL;
- RUNNER;
- EXIT.

Trailing should primarily follow proven market structure with volatility-aware buffering. It should not mechanically tighten on every small profit fluctuation. Stops may tighten but should not intentionally widen beyond approved risk. Original R remains immutable.

## Persistence / recovery contract

Critical responsibilities must survive restart and machine replacement. Durable/portable state includes, as applicable:

- risk/order/trade lifecycle;
- Trade Plan/original R context;
- Opportunity/Market Episode identity;
- Strategy Registry and genealogy;
- Champion/Challenger/promotion history;
- entry/exit learning and StrategyMemory;
- research/autonomous candidate history;
- fault/backup metadata.

Broker positions/orders/deals remain actual exposure truth. Restored/local state supplies context and must be reconciled before new broker writes.

The public repository may be used as disaster-recovery/versioned backup for project intelligence under the current policy. Credentials, tokens, private keys or other authentication material capable of unauthorized financial action or direct paid-service cost must never be committed.

## Research and learning contract

Research evaluates completed trades, missed opportunities, blocked/rejected opportunities and invalidated setups. Entry and exit learning measure MFE/MAE, entry efficiency, capture efficiency and premature-exit cost.

Governed strategy discovery/autonomous invention may propose bounded declarative candidates but may not directly rewrite production code, risk controls, broker permissions or safety gates.

No `eval`, `exec`, arbitrary generated Python or silent self-modification is part of the intended autonomous strategy design.

Promotion is evidence-driven and may include independent validation, locked candidate, one-shot final holdout, stress, Shadow and DEMO Canary stages before production approval.

## System-health contract

Normal trading decisions and bot faults are separate.

- `WAIT`, `ENTRY_EXTENDED`, `NEWS_BLACKOUT` or a functioning `LOSS_LOCKED` state are not automatically system errors.
- Data/order/account/state/controller failures must expose subsystem, severity, trading impact and recovery/action state.
- No critical unknown may silently fall back to a safe-looking default.

## Operator contract

The main dashboard is compact and mostly read-only. It separates Market, Decision, Risk, Execution, Learning/Backup and System Health state. Restrained emojis may be used as visual status markers with text fallback; presentation never becomes trading authority.

## Development contract

No production trading implementation is complete until the relevant design docs are frozen/deferred appropriately, executable tests exist, replay/live parity claims are justified, crash/restart/duplicate-submit risks are tested, disaster recovery is verified, and the exact build passes its required DEMO release gates.
