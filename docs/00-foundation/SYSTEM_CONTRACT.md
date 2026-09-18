# GoldSwingTraderAI — System Contract

**Status:** PROVISIONAL  
**Version:** 0.4-design  
**Authority:** Highest-level behavioural contract

## Core contract

GoldSwingTraderAI is an XAUUSD/XAUUSDm trading system built around multi-timeframe structure, parallel specialist analysis, independent BUY/SELL theses, explicit opportunity/timing separation, structural Trade Plans, hard risk/safety authority, centralized broker-write permission and governed research/learning.

If another document conflicts with this contract, the contradiction must be formally resolved; implementation must not silently choose a different rule.

## Market-analysis contract

- H4, H1, M15 and M5 are primary timeframes.
- Completed candles are authoritative for structural confirmation; unfinished candles may supply telemetry only where explicitly allowed.
- Market analysis runs in parallel rather than as a long sequential filter chain.
- Candle/structure, technical/location, liquidity/SMC, indicator/quant, fundamental/session and strategy specialists publish bounded evidence from the same verified snapshot.
- Missing optional non-safety evidence is not automatically bearish/zero.
- Strong opposing evidence matters more than missing confluence.

## Decision contract

Maintain at least:

- BUY Thesis;
- SELL Thesis;
- Directional Edge;
- Conflict / Red-Team objection;
- Opportunity Score;
- Entry Timing Score;
- Evidence Coverage / Confidence;
- operator-facing Final Trade Score;
- stable decision/reason trace.

A strong opportunity may remain `ARMED` while entry timing is poor. Timing weakness should normally produce `WAIT`, not destroy the setup.

Every meaningful `WAIT`, `MISSED`, `INVALID` or `BLOCKED` state must expose a machine-readable reason plus concise operator explanation.

## Strategy-floor contract

Initial V1 families:

1. `TREND_PULLBACK_CONTINUATION`
2. `BREAKOUT_EXPANSION`
3. `BREAKOUT_RETEST_CONTINUATION`
4. `LIQUIDITY_SWEEP_REVERSAL`
5. `FAILED_BREAKOUT_REVERSAL`
6. `COMPRESSION_EXPANSION`

FVG, qualified Order Block, premium/discount, liquidity pools, session highs/lows, EMA20/EMA50, RSI, ATR and individual candle patterns are primarily evidence primitives, not mandatory independent production strategies.

All strategy families evaluate the same verified market snapshot in parallel. Compatible agreement may add bounded support; correlated evidence must not be counted as independent certainty repeatedly.

## Timing and Trade Plan contract

- M15 primarily identifies opportunity/location/target context.
- M5 primarily identifies executable timing.
- Opportunity/setup state and entry decision are separate.
- Entry outcomes include ENTER BUY, ENTER SELL, WAIT, MISSED, INVALID and BLOCKED.
- Valid second-chance entry requires the thesis to survive and a genuinely fresh structural/timing event.
- Chase detection normally defers entry rather than erasing a valid opportunity.
- Structural invalidation/SL and market objectives are defined before monetary sizing.
- Risk rejects an unaffordable plan rather than distorting structural SL.
- Original approved R remains immutable.

Initial target economics use structural objectives rather than fixed 100/200/300-pip take profits. Primary Target is normally a management checkpoint, Expansion Target is the normal broker objective when valid, and Runner extension must be earned by fresh continuation evidence plus a new objective.

## Risk and safety contract

Risk/safety are not weighted-scoring components. They return hard authority such as PASS/BLOCK/UNKNOWN.

A high strategy score cannot override:

- invalid/stale required market data;
- unacceptable broker/account state;
- daily loss lock/cooldown;
- news/session safety;
- monetary risk/margin;
- position ownership/capacity;
- unresolved broker/order lifecycle;
- critical persistence corruption;
- controller ownership uncertainty;
- unsafe execution conditions.

Initial account profiles and risk boundaries are owned by `../30-risk-execution/RISK_CONTRACT.md`; current V1 uses SMALL `$100–$299`, MEDIUM `$300–$999`, NORMAL `$1,000+`, one independently risk-bearing Gold position (`0/1`), UTC risk-day accounting, governed manual-reset semantics and broker-aware all-in sizing.

## V1 environment contract

V1 defines one positive environment guard only:

```text
Connected MT5 account positively verified DEMO
→ DEMO_GUARD = PASS
```

Broker writes may proceed only when the DEMO guard and every other required authority pass.

If DEMO status is not verified, broker-write permission is not granted.

V1 does not define a separate REAL authorization workflow, REAL hard-block contract, LIVE override or alternate REAL execution path.

A verified DEMO account is real-time broker execution on that DEMO account, not dry-run simulation.

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

All bot-managed create/modify/close writes use this path. Strategy, research, dashboard and learning code may not call raw irreversible MT5 writes directly.

Ambiguous acknowledgement never triggers blind duplicate submission.

## Single-controller contract

For one managed account/symbol, only one runtime may hold broker-write authority.

V1 uses a shared controller lease with monotonic fencing epoch. Initial renewal target is 10 seconds and lease TTL is 30 seconds. Every irreversible write must freshly verify current holder, unexpired lease and matching current epoch.

A second laptop remains Observer while another valid holder exists. Standby takeover requires authoritative expiry, a new epoch and full broker/local-state reconciliation before becoming PRIMARY READY. A stale old epoch cannot write.

## Session / scheduled-close contract

V1 does not intentionally carry bot-managed Gold through known scheduled XAU closure/reopen gap risk.

```text
Daily:   T-20m no new entry, T-10m mandatory governed flatten
Weekend: T-60m no new entry, T-30m mandatory governed flatten
```

Daily reopen requires normalized conditions plus at least one clean completed M5. Weekend reopen requires gap assessment, normalized conditions and at least two clean completed M5 candles.

If flatten acknowledgement is ambiguous or broker becomes unavailable, unresolved exposure remains durable and must reconcile; it is never marked closed by assumption.

## News-safety contract

Initial V1 new-entry policy:

```text
TIER 1 CRITICAL  -15/+15 min
TIER 2 HIGH      -5/+5 min
TIER 3 CONTEXT   no automatic hard blackout
```

Scheduled news alone does not automatically force-close an existing managed trade. Required event truth failure becomes safety unknown rather than silent clear. Severe post-event dislocation requires normalized execution conditions plus a clean completed M5 before new entry permission resumes.

## Trade-management contract

Open-trade management is a second decision floor. It evaluates continuation and reversal evidence in parallel and returns one of:

- HOLD;
- PROTECT;
- TRAIL;
- RUNNER;
- EXIT.

Trailing should primarily follow proven market structure with volatility-aware buffering. It should not mechanically tighten on every small profit fluctuation. Stops may tighten but must not intentionally widen beyond original approved risk. Original R remains immutable.

Mandatory PRE_CLOSE flatten overrides HOLD/RUNNER continuation logic.

## Persistence / recovery contract

Critical responsibilities survive restart and machine replacement. Durable/portable state includes, as applicable:

- risk/order/trade lifecycle;
- Trade Plan/original R context;
- Opportunity/Market Episode identity;
- controller/reconciliation context as required;
- Strategy Registry and genealogy;
- Champion/Challenger/promotion history;
- entry/exit learning and StrategyMemory;
- research/autonomous candidate history;
- fault/backup/schema metadata.

Broker positions/orders/deals are current exposure truth. Restored/local state supplies intent/context and must reconcile before new broker writes.

The public repository may back up project intelligence. Credentials, tokens, private keys or other authentication material capable of unauthorized financial action, authenticated account control or direct paid-service cost must never be committed.

## Research and learning contract

Research evaluates completed trades, missed opportunities, blocked/rejected opportunities and invalidated setups. Entry/exit learning measures MFE/MAE, entry efficiency, capture efficiency and premature-exit cost.

Governed discovery/autonomous invention may propose bounded declarative candidates but may not directly rewrite production code, hard risk controls, broker permissions or safety gates.

No `eval`, `exec`, arbitrary generated executable Python or silent self-modification is part of intended autonomous strategy design.

Promotion is evidence-driven and cannot occur silently.

## System-health contract

Normal trading decisions and technical faults are separate.

- `WAIT`, `ENTRY_EXTENDED`, `NEWS_BLACKOUT`, `SESSION_PRE_CLOSE` or a functioning `LOSS_LOCKED` state are not automatically system errors.
- Data/order/account/state/controller failures expose subsystem, severity, trading impact and recovery/action state.
- No critical unknown silently falls back to a safe-looking default.

## Operator contract

The dashboard remains compact and mostly read-only. It preserves useful prior GoldScalperAI observability and adds separate Decision, Execution, Learning, Backup and System Health state. Presentation never becomes trading authority.

## Development contract

Implementation proceeds in large phases defined by `../CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md`.

A phase is complete only when code exists, required tests pass, documentation matches the implementation and no known critical contradiction remains.

No release becomes VERIFIED merely because documentation/code appears complete; controlled DEMO, no-lookahead, duplicate-write, restart/reconciliation, controller/failover and recovery evidence must actually pass.
