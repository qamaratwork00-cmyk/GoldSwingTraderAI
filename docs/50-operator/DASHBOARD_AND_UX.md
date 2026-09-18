# GoldSwingTraderAI — Dashboard and UX

**Status:** PROVISIONAL  
**Version:** 0.4-design  
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
- centralized Execution Permission must be visible when it is the final allow/block boundary;
- useful operational visibility carried forward from the prior GoldScalperAI dashboard must not be removed merely to make the screen look cleaner.

## GoldScalperAI visibility preservation rule

GoldSwingTraderAI is a new system, but the prior GoldScalperAI dashboard contained useful operator information that remains valuable. These fields should be preserved or improved in the new compact layout whenever the underlying data is available:

- current bot/account mode and runtime role;
- XAU symbol;
- Bid and Ask;
- live spread and spread quality;
- current M5 candle time remaining;
- concise trend/structure direction;
- EMA20 / EMA50 values or compact relation where useful;
- RSI;
- ATR;
- current signal/action;
- exact reason for `WAIT`, `ENTER`, `BLOCKED`, `MISSED`, `INVALID` or management action;
- account/risk profile and proposed risk/lot;
- daily P/L;
- daily loss limit / remaining daily risk budget;
- active-position count/capacity;
- consecutive-loss/loss-streak information where it remains useful for risk/diagnostics;
- open-trade entry/SL/TP or structural objectives when a trade exists.

These items may be reorganized, condensed or grouped into newer panels, but they must not silently disappear if they remain meaningful to the operator.

The new dashboard adds richer structure, decision, execution, learning, backup and health information around this useful core rather than replacing it with a less informative screen.

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
- account profile (`SMALL`, `MEDIUM`, `NORMAL`);
- production policy version;
- UTC time;
- M5 candle time remaining where available;
- current market state.

A real account connected while the current policy remains DEMO-first must be prominent as an environment-authorization block, not a mysterious generic error.

## Market panel

Compact market context should retain practical live visibility while adding the swing-system context. It may include:

- Bid / Ask;
- live spread and spread quality;
- H4/H1/M15/M5 structure summary;
- concise bullish/bearish/range/transition state;
- volatility/momentum phase;
- session context;
- location/target path;
- news-safety status;
- concise EMA20/EMA50 relation/values;
- RSI;
- ATR.

Indicators remain secondary context and must not become trade authority merely because they are visible.

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
- final action/signal;
- exact primary reason.

Example:

```text
⚖️ DECISION
BUY 87     SELL 31     Edge +56 BUY
Opportunity 86 | Entry 78 | Coverage 94%
Strategy TREND_PULLBACK
Status 🟡 WAIT
Reason ENTRY_EXTENDED
```

## Why / blocker attribution

Every `WAIT`, `MISSED`, `INVALID`, `BLOCKED` or `EXIT` should show a stable reason code plus concise human explanation.

Example:

```text
Code: ENTRY_EXTENDED
Entry abhi ideal zone se door hai. Setup valid hai; fresh pullback/reclaim ka wait.
```

Risk-geometry example:

```text
Code: RISK_GEOMETRY_TOO_LARGE
Setup valid hai lekin current entry par 0.01 lot ka all-in risk profile ceiling se bahar hai. Better structural entry ka wait.
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

- Account Profile: `SMALL`, `MEDIUM` or `NORMAL`;
- sizing mode: base/min-lot hybrid, stepped dynamic or fully dynamic;
- `NORMAL` / `LOSS_LOCKED` / `COOLDOWN` / `BLOCKED` state;
- equity/balance facts where appropriate;
- Target Risk and Acceptable Gold Risk Band status;
- structural SL monetary risk;
- spread/execution-friction impact as calculated by the Risk Contract;
- actual proposed all-in risk;
- proposed normalized lot;
- open risk;
- daily P/L and daily loss limit/remaining risk budget;
- position count/capacity;
- loss streak where meaningful;
- Risk PASS/BLOCK reason.

Example SMALL account display:

```text
🛡️ RISK
Profile          SMALL
Sizing           BASE 0.01
Target Risk      ...
Structural Risk  ...
Spread Impact    ...
All-in Risk      ...
Daily P/L        ...
Daily Remaining  ...
Position         0/1
Loss Streak      0
Risk Band        ACCEPTABLE
Decision         ✅ PASS
```

The dashboard must not assume a quoted Gold spread such as `$0.26` equals `$0.26` account cost; it displays the broker-aware conversion published by Risk/Execution.

Exact risk percentages are owned by Risk Contract/config, not this dashboard document.

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
- current broker TP if one exists;
- Primary/Expansion/Runner objectives;
- current realized/unrealized R context;
- MFE/MAE;
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

Before execution readiness, show a startup checklist including account, environment authorization, symbol/specs, history, state integrity, broker reconciliation, risk profile, Strategy Registry, learning, news safety and execution-controller authority.

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

## Compact target layout

A future implementation may use a compact layout similar to:

```text
════════ GoldSwingTraderAI ════════
XAUUSDm | DEMO ✅ | SMALL | ⚡ PRIMARY
Bid ... | Ask ... | Spread ... | M5 ...
───────────────────────────────────
🌍 MARKET      BULLISH
EMA20/50 ... | RSI ... | ATR ...
⚖️ DECISION    🟡 WAIT • BUY BIAS
🎯 SETUP       ARMED • Score 86
🛡️ RISK        ✅ NORMAL • 0.01
Today ... | Limit ... | Pos 0/1 | LS 0
⚙️ EXECUTION   ✅ READY
🧠 LEARNING    ✅ ACTIVE
🩺 SYSTEM      ✅ HEALTHY
💾 BACKUP      ✅ VERIFIED
───────────────────────────────────
💬 Entry thori extended hai.
   Setup valid hai — pullback ka wait.
════════════════════════════════════
```

Exact dimensions/ordering may change for readability, but the useful facts above remain available.

## Refresh behaviour

Dashboard refresh frequency is presentation only and must not cause repeated strategy triggers or duplicate order attempts. Prefer in-place refresh rather than endless terminal scrolling.

## Tests required

- WAIT versus BLOCKED versus system-fault rendering;
- stable reason code + human explanation;
- decision trace correctness;
- preserved Bid/Ask/spread/candle-timer/trend/EMA/RSI/ATR visibility where available;
- preserved daily P/L/loss-limit/position/loss-streak visibility;
- SMALL/MEDIUM/NORMAL profile and sizing-mode display;
- all-in risk/spread-impact display comes from authority rather than UI recomputation;
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
- remove useful operator facts solely for visual minimalism;
- overwhelm the main screen with every swing/FVG/OB/log line;
- require manual tuning for normal operation.

## Open questions

- final terminal dimensions/section order;
- exact refresh cadence;
- final wording polish;
- final safe-shutdown/export operator controls;
- optional future notification channels.
