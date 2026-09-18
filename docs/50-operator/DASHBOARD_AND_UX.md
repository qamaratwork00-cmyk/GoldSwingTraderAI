# GoldSwingTraderAI — Dashboard and UX

**Status:** PROVISIONAL  
**Version:** 0.5-design  
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
- technical terms remain stable/English for logs/docs;
- short English/Roman-Urdu explanations may improve readability;
- meaningful emojis are visual markers, not decoration;
- avoid raw-data overload;
- one clear top-level status always visible;
- normal `WAIT` visually distinct from a system fault;
- centralized Execution Permission visible as the final allow/block boundary;
- useful operational visibility from the prior GoldScalperAI dashboard must not be removed merely to make the screen look cleaner.

## GoldScalperAI visibility preservation rule

Preserve or improve these fields whenever data is available:

- current bot/account mode and runtime role;
- XAU symbol;
- Bid and Ask;
- live spread and spread quality;
- current M5 candle time remaining;
- concise trend/structure direction;
- EMA20 / EMA50 values or relation;
- RSI;
- ATR;
- current signal/action;
- exact reason for `WAIT`, `ENTER`, `BLOCKED`, `MISSED`, `INVALID` or management action;
- account/risk profile and proposed risk/lot;
- daily Account Safety P/L;
- daily loss limit / remaining budget;
- active-position count/capacity;
- loss streak/cooldown;
- open-trade entry/SL/TP/objectives.

The new dashboard adds richer Decision, Execution, Learning, Backup and Health information around this core.

## Emoji policy

Recommended markers:

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

Plain-text fallback such as `[OK]`, `[WAIT]`, `[BLOCK]` must work without changing logic.

## Header

Expose compact identity facts such as:

- bot/project name;
- XAU symbol;
- connected account mode;
- DEMO guard state;
- runtime role (`PRIMARY`, `STANDBY`, `OBSERVER`, `RESEARCH`, `RECOVERING`);
- account profile (`SMALL`, `MEDIUM`, `NORMAL`);
- production policy version;
- UTC time;
- M5 candle time remaining;
- current market/session state.

V1 does not need a separate REAL authorization display. Environment visibility should answer whether positive DEMO verification passed.

## Market panel

May include:

- Bid / Ask;
- live spread + Spread Ratio/state;
- H4/H1/M15/M5 structure summary;
- bullish/bearish/range/transition state;
- volatility/momentum phase;
- session context;
- location/target path;
- news-safety status;
- EMA20/EMA50;
- RSI;
- ATR.

Indicators remain secondary context and do not become trade authority merely because they are visible.

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

Every `WAIT`, `MISSED`, `INVALID`, `BLOCKED` or `EXIT` shows a stable reason code plus concise explanation.

Examples:

```text
ENTRY_EXTENDED
Entry abhi ideal zone se door hai. Setup valid hai; fresh pullback/reclaim ka wait.
```

```text
RISK_GEOMETRY_TOO_LARGE
Setup valid hai lekin current entry par broker minimum lot ka all-in risk profile ceiling se bahar hai.
```

```text
SESSION_PRE_CLOSE
Gold session close qareeb hai; nayi entry allowed nahi.
```

The dashboard must never reduce all non-trades to generic `NO TRADE`.

## Decision trace

Example:

```text
Data        ✅ PASS
Strategy    ✅ BUY 87
Entry       🟡 WAIT 78
Trade Plan  ⏸ NOT READY
News        ✅ PASS
Risk        — NOT EVALUATED
Execution   — NOT REACHED
```

If a hard blocker stops an otherwise-qualified trade, show `Would otherwise trade? YES` where the authoritative decision layer can safely establish it.

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

Display authoritative risk state such as:

- Account Profile;
- sizing mode;
- `NORMAL` / `LOSS_LOCKED` / `COOLDOWN` / `BLOCKED`;
- equity/balance facts where useful;
- risk-band status;
- structural SL monetary risk;
- spread/execution-friction impact;
- actual proposed all-in risk;
- normalized lot;
- open risk;
- cumulative Day Safety P/L;
- active cycle P/L / daily limit / remaining budget;
- manual-reset state/count;
- position `0/1`;
- loss streak/cooldown;
- Risk PASS/BLOCK reason.

Example:

```text
🛡️ RISK
Profile          SMALL
Sizing           BASE 0.01
All-in Risk      ...
Risk Band        NORMAL / ELEVATED
Day Safety P/L   ...
Daily Remaining  ...
Manual Reset     OFF / AVAILABLE / USED
Position         0/1
Loss Streak      0
Cooldown         CLEAR
Decision         ✅ PASS
```

The UI displays broker-aware risk/spread calculations supplied by Risk/Execution; it does not recompute them.

## Execution Permission panel

The centralized broker-write safeguard must be directly visible.

Ready example:

```text
⚙️ EXECUTION
Account Mode      DEMO
DEMO Guard        ✅ PASS
Controller        ⚡ PRIMARY
Lease Epoch       ...
Broker Reconcile  ✅ COMPLETE
Account Identity  ✅ PASS
Fresh Checks      ✅ PASS
Permission        ✅ ALLOW
```

Environment-not-ready example:

```text
Account Mode      UNKNOWN / NOT VERIFIED
DEMO Guard        🔴 NOT VERIFIED
Permission        🔴 BLOCK
Reason            DEMO_GUARD_NOT_VERIFIED
```

Normal trade-specific block:

```text
DEMO Guard        ✅ PASS
Permission        🔴 BLOCK
Reason            SPREAD_TOO_HIGH
Would trade otherwise? YES
```

This panel only displays the result owned by `EXECUTION_AND_BROKER_SAFETY.md`; UI code must not recompute permission.

## Session/news visibility

Show as applicable:

- market state `OPEN/PRE_CLOSE/CLOSED/REOPEN_WARMUP`;
- PRE_CLOSE countdown and required flatten state;
- reopen clean-M5 progress;
- News Safety state;
- next event/tier/blackout countdown;
- post-news warmup state.

When mandatory PRE_CLOSE flatten is active, that requirement must be prominent even if Trade Manager continuation remains bullish.

## Open Trade panel

Prioritize:

- direction/symbol;
- strategy/policy/Episode IDs;
- entry/current price;
- original/current SL;
- current broker TP;
- Primary/Expansion/Runner objectives;
- original/current R context;
- MFE/MAE;
- Continuation/Reversal/Structure state;
- Trade Manager action;
- reason for last SL/TP/exit decision;
- PRE_CLOSE flatten state where relevant.

## Learning panel

Keep compact:

- StrategyMemory health;
- Entry Learning;
- Exit Learning;
- Champion;
- Challenger/stage;
- bounded adaptive influence;
- selected metric such as Capture Efficiency.

Shadow/candidate views clearly show that they do not have production broker authority.

## Backup/state panel

Expose:

- state integrity;
- Strategy Registry restore state;
- learning restore state;
- broker reconciliation;
- latest backup/checkpoint status/age.

## System Health panel

Use states/reasons owned by `SYSTEM_HEALTH_AND_DIAGNOSTICS.md`. A normal market `WAIT`, `NEWS_BLACKOUT`, `SESSION_PRE_CLOSE` or functioning `LOSS_LOCKED` is not automatically a system error.

## Startup view

Before execution readiness, show a checklist including:

- account identity;
- DEMO guard;
- symbol/specs;
- history/data integrity;
- state integrity;
- broker reconciliation;
- risk profile/state;
- Strategy Registry/learning;
- news/session safety;
- controller lease/epoch;
- centralized execution permission.

New broker writes remain disabled until required authorities are ready.

## Runtime roles

Visually distinguish:

```text
⚡ PRIMARY
🕒 STANDBY
👁️ OBSERVER
🧪 RESEARCH
🔄 RECOVERING / RECONCILING
```

An Observer/Standby/Research runtime must not display active broker-write authority.

## Operator controls

The dashboard is mostly read-only. Only deliberately governed actions should be exposed, such as:

- double-confirm manual daily-loss reset where enabled/permitted;
- safe shutdown;
- portable state export/restore workflows when implemented.

Do not expose casual hotkeys for changing weights, bypassing safety or impulsively promoting strategies.

## Compact target layout

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
Day ... | Limit ... | Pos 0/1 | LS 0
⚙️ EXECUTION   ✅ READY • DEMO PASS
🧠 LEARNING    ✅ ACTIVE
🩺 SYSTEM      ✅ HEALTHY
💾 BACKUP      ✅ VERIFIED
───────────────────────────────────
💬 Entry thori extended hai.
   Setup valid hai — pullback ka wait.
════════════════════════════════════
```

Exact dimensions/order may change for readability, but useful facts remain available.

## Refresh behaviour

Dashboard refresh is presentation only and must not create repeated strategy triggers or duplicate order attempts. Prefer in-place refresh rather than endless scrolling.

## Tests required

- WAIT vs BLOCKED vs technical-fault rendering;
- stable reason + human explanation;
- decision trace correctness;
- Bid/Ask/spread/M5 timer/trend/EMA/RSI/ATR visibility;
- daily safety P/L/limit/position/loss-streak visibility;
- profile/sizing display;
- risk/spread values come from authority rather than UI recomputation;
- positive DEMO guard display semantics;
- centralized Execution Permission correctness;
- controller role/lease/epoch visibility;
- PRE_CLOSE/reopen/news-state visibility;
- backup/learning/system-health panels;
- emoji fallback;
- refresh cannot create trading authority.

## Explicit non-goals

The dashboard must not:

- become a second strategy/risk/execution specification;
- place trades because a UI element changed;
- hide faults behind generic `NO TRADE`;
- remove useful operator facts solely for minimalism;
- overwhelm the main screen with every swing/FVG/OB/log line;
- require manual tuning for normal operation.

## Open questions

- final terminal dimensions/section order;
- exact refresh cadence;
- final wording polish;
- final safe-shutdown/export controls;
- optional future notification channels.
