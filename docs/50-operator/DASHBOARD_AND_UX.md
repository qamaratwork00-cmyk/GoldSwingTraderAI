# GoldSwingTraderAI — Dashboard and UX

**Status:** PROVISIONAL — IMPLEMENTED BASELINE  
**Version:** 0.6-implementation  
**Authority:** Main terminal dashboard information architecture, operator visibility, reason presentation and restrained emoji usage.  
**Depends on:** `../20-trading-decisions/SCORING_AND_DECISION_FUSION.md`, `../30-risk-execution/RISK_CONTRACT.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`, `../60-engineering/SYSTEM_HEALTH_AND_DIAGNOSTICS.md`

## Purpose

The dashboard answers at a glance:

- what the market is doing;
- what the bot currently thinks;
- why it entered, waits, missed, invalidated or is blocked;
- what risk/execution authority currently says;
- what is happening to an open managed trade;
- whether learning, persistence/backup and system health are healthy.

The dashboard **observes authoritative state; it never defines trading behaviour or broker-write permission.**

## Current implementation checkpoint — Phase 9

Implemented owner:

```text
operator/dashboard.py
operator/__init__.py
```

The V1 baseline is intentionally lightweight: pure standard-library terminal rendering, no web framework and no extra UI dependency. `DashboardData` receives already-authoritative facts and `render_dashboard()` only formats them.

Deterministic tests currently prove:

- prior useful GoldScalperAI visibility is preserved;
- WAIT, BLOCKED and OPEN TRADE are visually distinct;
- stable reason codes plus concise Roman-Urdu/English explanation are visible;
- emoji and plain-text fallback both work;
- dashboard source has no MetaTrader5/raw `order_send`, Risk Engine or Execution Gate authority;
- money/countdown formatting is deterministic.

This is a renderer baseline, not a final live-screen certification. Full runtime wiring and Windows terminal observation remain integration work.

## UX principles

- compact and decision-focused;
- stable English machine terms/reason codes;
- concise English/Roman-Urdu operator explanations where useful;
- meaningful emojis only;
- normal `WAIT` must not look like a system fault;
- final Execution Permission must remain visible;
- useful prior dashboard facts must not be removed merely for visual minimalism;
- in-place refresh is preferred; refresh must never create strategy triggers or broker writes.

## GoldScalperAI visibility preservation rule

Preserve or improve whenever the fact is available:

- account mode / DEMO guard / runtime role;
- XAU symbol;
- Bid / Ask;
- live spread and spread quality;
- M5 candle time remaining;
- concise multi-timeframe trend/structure;
- EMA20 / EMA50;
- RSI;
- ATR;
- current decision/action;
- exact reason for `ENTER`, `WAIT`, `MISSED`, `INVALID`, `BLOCKED` or management action;
- Account Profile / proposed risk / proposed lot;
- daily Account Safety P/L, daily loss limit and remaining budget;
- position count/capacity;
- loss streak/cooldown;
- open-trade entry/current price/original and current SL/TP/objectives/R context.

Add Decision, Execution, Learning, Backup/State and System Health visibility around that core.

## Emoji / text markers

Recommended visual meanings:

```text
🌍 MARKET        ⚖️ DECISION       📈 OPEN TRADE
🛡️ RISK          ⚙️ EXECUTION      🧠 LEARNING
💾 STATE/BACKUP  🩺 HEALTH          💬 WHY

✅ PASS/HEALTHY
🟡 WAIT/CAUTION
🔴 BLOCK/ERROR
⚠️ DEGRADED
```

Plain fallback such as `[MARKET]`, `[WAIT]`, `[BLOCK]`, `[EXEC]` must preserve the same semantics.

## Header / market visibility

Header should expose project, symbol, connected account mode, DEMO guard, runtime/controller role, Account Profile, UTC time, M5 countdown and market/session state.

Market panel should show authoritative supplied values for:

- Bid / Ask / spread + spread state;
- H4/H1/M15/M5 structure summary;
- EMA20/EMA50;
- RSI;
- ATR;
- volatility/momentum/session/news context where useful.

Visible indicators remain supporting context; UI visibility does not turn them into trade gates.

## Decision panel

Show at least:

- BUY Thesis score;
- SELL Thesis score;
- Opportunity Score;
- Entry Timing Score;
- Evidence Coverage;
- leading strategy family;
- final action;
- exact reason code.

Example:

```text
⚖️ DECISION    🟡 WAIT
BUY 84 | SELL 28 | Opportunity 82 | Entry 58 | Coverage 92%
Strategy TREND_PULLBACK_CONTINUATION
Reason ENTRY_EXTENDED
```

Never collapse every non-trade into generic `NO TRADE`.

## Human reason explanation

A stable reason code remains primary; a short explanation may follow, for example:

```text
ENTRY_EXTENDED
Entry extended hai; setup valid ho sakta hai, better timing ka wait.
```

```text
MIN_LOT_UNAFFORDABLE
Current setup par broker minimum lot actual risk ceiling se bahar hai.
```

```text
PRE_CLOSE_FLATTEN
Scheduled close qareeb hai; managed trade governed close path par hai.
```

The renderer currently contains concise fallback explanations for common V1 reason codes. It must not invent a different reason from the authoritative subsystem.

## Risk panel

Display supplied authoritative risk facts such as:

- Account Profile;
- risk state;
- proposed all-in risk percentage;
- proposed normalized lot;
- Day Safety P/L;
- daily loss limit and remaining percentage;
- position count/capacity;
- loss streak;
- cooldown.

The UI **must not recalculate** sizing, daily loss or broker risk.

## Execution panel

Display the centralized execution result and controller state, for example:

```text
⚙️ EXECUTION   ✅ ALLOW
Controller PRIMARY | Epoch 12
Reconcile COMPLETE | Reason EXECUTION_READY
```

Relevant details may include account identity, DEMO guard, broker reconciliation, Intent/lifecycle and primary blocker when available.

The dashboard does not independently call `evaluate_execution_permission()` or raw MetaTrader5 functions.

## Session/news visibility

Show as applicable:

- OPEN / PRE_CLOSE / CLOSED / REOPEN_WARMUP;
- PRE_CLOSE countdown/flatten requirement;
- reopen clean-M5 progress;
- NEWS_CLEAR / BLACKOUT / UNKNOWN / POST_NEWS_WARMUP;
- next event/tier/countdown.

A mandatory PRE_CLOSE flatten should remain prominent even if market continuation is otherwise bullish.

## Open Trade panel

For a managed trade prioritize:

- direction;
- entry/current price;
- original/current SL;
- current broker TP;
- Primary / Expansion / Runner objectives;
- current R based on immutable original-R definition;
- Trade Manager action;
- exact management reason.

Example:

```text
📈 OPEN TRADE  BUY | Manager RUNNER
Entry ... | Now ... | SL ... (orig ...) | TP ... | R ...
Primary ... | Expansion ... | Runner ...
Reason RUNNER_EARNED_BY_CONTINUATION
```

Open-trade display never grants MODIFY/CLOSE authority; management writes still pass the governed execution path.

## Learning / State / Health

Keep these compact:

```text
🧠 Learning  ACTIVE / PENDING / DEGRADED
💾 Backup    VERIFIED / STALE / FAILED / PENDING
🩺 Health    HEALTHY / DEGRADED / BLOCKED
```

Later research implementation may add Champion/Challenger/StrategyMemory/Capture metrics. Optional learning failure must not be disguised as trading safety success.

Normal trading states such as WAIT, NEWS_BLACKOUT or LOSS_LOCKED are not automatically system faults.

## Runtime roles

Visually distinguish:

```text
PRIMARY
STANDBY
OBSERVER
RESEARCH
RECOVERING / RECONCILING
```

Only authoritative controller/execution state decides write capability; a dashboard label cannot promote itself to PRIMARY.

## Operator controls

Main V1 dashboard remains mostly read-only. Do not add casual controls for changing strategy weights, bypassing safety, forcing entries or promoting research candidates.

Governed operator actions, when implemented, may include safe shutdown, permitted manual loss reset double-confirmation and portable export/recovery workflows.

## Current renderer contract

`DashboardData` is a presentation DTO. It intentionally does not depend on Risk Engine, Strategy Floor, MetaTrader5 or Execution Gate internals. A later runtime state-builder may flatten authoritative subsystem results into this DTO.

`OpenTradeView` is also presentation-only.

This separation is deliberate: **changing the dashboard must not change trading behaviour.**

## Tests required

- WAIT vs BLOCKED vs OPEN TRADE rendering;
- stable reason + concise explanation;
- Bid/Ask/spread/M5 timer/structure/EMA/RSI/ATR visibility;
- risk/lot/daily-P&L/position/loss-streak/cooldown visibility;
- Execution Permission/controller/epoch/reconciliation visibility;
- open trade SL/TP/objective/manager visibility;
- conventional signed money formatting;
- plain-text fallback;
- source-level absence of raw broker/risk/execution authority;
- future integration test proving refresh cannot create duplicate decisions/writes.

## Explicit non-goals

The dashboard must not:

- become a second strategy/risk/execution specification;
- place/modify/close trades because the screen refreshed;
- hide blockers behind generic `NO TRADE`;
- remove useful facts solely for minimalism;
- overwhelm the primary view with every FVG/swing/log row;
- require manual parameter tuning for normal operation;
- introduce a web/UI framework unless a later real requirement justifies it.

## Remaining integration/polish work

- runtime builder from authoritative subsystem state into `DashboardData`;
- actual in-place terminal refresh loop and screen dimensions;
- final safe-shutdown/export controls;
- live Windows terminal visual verification;
- Phase-10 learning/research facts once those subsystems exist.
