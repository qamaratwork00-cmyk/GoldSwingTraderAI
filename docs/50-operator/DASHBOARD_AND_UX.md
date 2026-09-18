# GoldSwingTraderAI — Dashboard and UX

**Status:** PROVISIONAL  
**Version:** 0.2-design  
**Authority:** Main terminal dashboard information architecture, operator visibility, reason presentation and restrained emoji usage.  
**Depends on:** `../20-trading-decisions/SCORING_AND_DECISION_FUSION.md`, `../30-risk-execution/RISK_CONTRACT.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`, `../60-engineering/SYSTEM_HEALTH_AND_DIAGNOSTICS.md`

## Purpose

The dashboard should answer at a glance:

- What is the market doing?
- What does the bot currently think?
- Why did it enter, wait, miss or block?
- What is the active Trade Plan/open-trade state?
- Is risk/execution healthy and permitted?
- What is learning/research doing?
- Is backup/recovery healthy?
- Is the bot itself healthy?

The dashboard observes authoritative state; it does not define trading behaviour.

## UX principles

- compact and decision-focused;
- technical terms remain stable/English for consistency with logs/docs;
- short English/Roman-Urdu explanations may improve operator readability;
- meaningful emojis are used as visual markers, not decoration;
- avoid raw-data overload;
- one clear top-level status must always be visible;
- normal `WAIT` must remain visually distinct from a system fault;
- centralized Execution Permission must be visible when it is the final allow/block boundary.

## Emoji policy

Recommended section/status markers:

```text
🌍 MARKET
⚖️ DECISION
🎯 SETUP
📈 OPEN TRADE
🛡️ RISK
⚙️ EXECUTION
🧠 LEARNING
💾 STATE / BACKUP
🩺 SYSTEM HEALTH

✅ PASS / HEALTHY
🟡 WAIT / CAUTION
🔴 BLOCKED / ERROR
⚠️ DEGRADED
🔒 LOCKED
👁️ OBSERVER
```

Do not place multiple decorative emojis on every line. If a terminal cannot render a glyph, plain-text fallback such as `[OK]`, `[WAIT]`, `[BLOCK]` must work without affecting logic.

## Header

The header should expose compact identity facts such as:

- bot/project name;
- XAU symbol;
- verified account environment/mode;
- runtime role (`PRIMARY EXECUTOR`, `OBSERVER`, `RESEARCH`);
- production policy version;
- UTC time;
- M5 candle time remaining where available;
- current market state.

A real account connected while the current policy remains DEMO-first must be prominent as an environment-authorization block, not a mysterious generic error.

## Market panel

Compact market context may include:

- H4/H1/M15/M5 structure summary;
- volatility/momentum phase;
- session context;
- location/target path;
- news-safety status;
- spread quality;
- optional concise EMA/RSI/ATR line.

Indicators remain secondary context.

## Trading Floor Decision panel

Display at least:

- BUY Thesis;
- SELL Thesis;
- Directional Edge;
- Conflict;
- Opportunity Score;
- Entry Timing Score;
- Evidence Coverage;
- operator-facing Final Score;
- leading/supporting strategy family;
- final action.

Example:

```text
⚖️ DECISION
BUY 87     SELL 31     Edge +56 BUY
Opportunity 86 | Entry 78 | Coverage 94%
Strategy TREND_PULLBACK
Status 🟡 WAIT
```

## Why / blocker attribution

Every `WAIT`, `MISSED`, `INVALID`, `BLOCKED` or `EXIT` should show a stable reason code plus concise human explanation.

Example:

```text
Code: ENTRY_EXTENDED
Entry abhi ideal zone se door hai. Setup valid hai; fresh pullback/reclaim ka wait.
```

Hard-block example:

```text
Code: MIN_LOT_UNAFFORDABLE
0.01 minimum lot approved risk se zyada exposure de rahi hai.
```

The dashboard must never reduce all non-trades to `NO TRADE`.

## Decision trace

A compact authority chain should show where the action stopped, for example:

```text
Data       ✅ PASS
Strategy   ✅ BUY 87
Entry      🟡 WAIT 78
Trade Plan ⏸ NOT READY
News       ✅ PASS
Risk       — NOT EVALUATED
Execution  — NOT REACHED
```

If a hard blocker prevents an otherwise-qualified trade, show `Would otherwise trade? YES` where the authoritative decision layer can establish that counterfactual safely.

## Setup panel

For an active opportunity display at least:

- Opportunity/Episode ID;
- family/direction;
- lifecycle stage;
- quality/freshness;
- ideal entry zone/reference;
- invalidation reference;
- primary/expansion objective;
- current action.

## Trade Plan panel

When relevant display:

- entry reference;
- structural SL/Stop Quality;
- Primary/Expansion/Runner objectives;
- Primary/Expansion RR;
- Plan Quality;
- degradation reason such as `PRICE_DRIFT`.

## Risk panel

Display compact authoritative risk state such as:

- `NORMAL` / `LOSS_LOCKED` / `COOLDOWN` / `BLOCKED`;
- equity/balance facts where appropriate;
- target versus actual proposed risk;
- proposed lot;
- open risk;
- daily P/L and remaining risk budget;
- position capacity;
- Risk PASS/BLOCK reason.

Exact risk numbers are owned by Risk Contract/config, not this dashboard document.

## Execution Permission panel

The centralized broker-write safeguard should be directly visible and easy to demonstrate.

Compact example:

```text
⚙️ EXECUTION
Environment       DEMO ✅ AUTHORIZED
Controller        ⚡ PRIMARY
Account Identity  ✅ PASS
Order Lifecycle   ✅ CLEAR
Fresh Checks      ✅ PASS
Permission        ✅ ALLOW
```

Blocked example:

```text
⚙️ EXECUTION
Environment       REAL
Permission        🔴 BLOCK
Reason            ENVIRONMENT_NOT_AUTHORIZED
Policy            DEMO-FIRST
```

Or a normal trade-specific safety block:

```text
Permission        🔴 BLOCK
Reason            SPREAD_TOO_HIGH
Would trade otherwise? YES
```

This panel displays the result owned by `EXECUTION_AND_BROKER_SAFETY.md`; UI code must not recompute permission.

When a future frozen REAL policy is approved, the panel should show that authorization explicitly while keeping the same permission gate/path.

## Open Trade panel

When a bot-managed position is open, prioritize:

- direction/symbol;
- strategy/policy/Episode IDs;
- entry/current price;
- original/current SL;
- current realized/unrealized R context;
- MFE/MAE;
- Primary/Expansion objectives;
- Continuation/Reversal/Structure state;
- Trade Manager action;
- reason for last SL/TP/exit decision.

## Learning panel

Keep compact:

- StrategyMemory health;
- Entry Learning state;
- Exit Learning state;
- Champion;
- Challenger/stage;
- bounded/adaptive influence state;
- selected recent research metric such as Capture Efficiency.

Shadow/candidate views must clearly show that they do not have production authority unless in governed DEMO Canary.

## Backup/state panel

Expose:

- state integrity;
- Strategy Registry restore state;
- learning restore state;
- broker reconciliation;
- latest backup status/age.

## System Health panel

Use the states/reason codes owned by `SYSTEM_HEALTH_AND_DIAGNOSTICS.md`. A normal market `WAIT` or an expected policy block is not automatically a system error.

## Startup view

Before execution readiness, show a startup checklist including account, environment authorization, symbol/specs, history, state integrity, broker reconciliation, risk, Strategy Registry, learning, news safety and execution-controller authority.

New trades remain disabled until required startup authorities are ready.

## Runtime roles

Visually distinguish:

```text
⚡ PRIMARY EXECUTOR
👁️ OBSERVER
🧪 RESEARCH
```

An Observer may analyze/display but must not show broker-write authority.

## Operator controls

The main dashboard is mostly read-only. Only deliberately governed actions should be exposed, such as:

- double-confirm manual daily-loss reset where permitted;
- safe shutdown;
- portable state export/restore workflows where later implemented.

Do not expose casual hotkeys for changing weights, bypassing news/risk/execution permission or impulsively promoting strategies.

## Refresh behaviour

Dashboard refresh frequency is presentation only and must not cause repeated strategy triggers or duplicate order attempts. Prefer in-place refresh rather than endless terminal scrolling.

## Tests required

- WAIT versus BLOCKED versus system-fault rendering;
- stable reason code + human explanation;
- decision trace correctness;
- centralized Execution Permission display correctness;
- DEMO-first versus future authorized-REAL display semantics;
- role/controller visibility;
- backup/learning/system-health panels;
- emoji fallback;
- dashboard refresh cannot create trading authority.

## Explicit non-goals

The dashboard must not:

- become a second strategy/risk/execution specification;
- place trades because a UI element changed;
- hide system faults behind generic `NO TRADE`;
- overwhelm the main screen with every swing/FVG/OB/log line;
- require manual tuning for normal operation.

## Open questions

- final terminal dimensions/section order;
- exact refresh cadence;
- final wording polish;
- final safe-shutdown/export operator controls;
- optional future notification channels.
