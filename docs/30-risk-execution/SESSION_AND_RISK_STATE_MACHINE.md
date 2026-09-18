# GoldSwingTraderAI — Session and Risk State Machine

**Status:** PROVISIONAL  
**Version:** 0.5-design  
**Authority:** Hard market/session permission states, risk/system permission composition, news-safety states and state transitions.  
**Depends on:** `RISK_CONTRACT.md`, `EXECUTION_AND_BROKER_SAFETY.md`, `../10-market-intelligence/FUNDAMENTAL_AND_NEWS.md`, `../10-market-intelligence/SESSION_CONTEXT.md`

## Core principle

Market state, risk state and system/execution safety are separate authorities. The market can be open while risk is locked, and a holiday can reduce participation while XAU remains genuinely tradeable.

This document owns **permission states**, not session-analysis quality, event-fact sourcing or daily-loss arithmetic.

## Market/session permission states

### OPEN

Broker/live market is functioning and new trades may be considered if risk, news, system and execution authorities also permit them.

### PRE_CLOSE

Scheduled XAU closure is approaching.

V1 policy:

- new entries are blocked;
- existing bot-managed Gold positions must be flattened before scheduled closure while broker remains tradeable;
- Trade Manager may protect/exit earlier for structural reasons, but may not intentionally carry a bot-managed position through scheduled daily XAU break/weekend closure;
- exact pre-close no-new-entry/mandatory-flatten lead time remains broker/research calibration.

Reason codes should distinguish `SESSION_PRE_CLOSE` from `PRE_CLOSE_FLATTEN`.

### CLOSED

Broker-confirmed XAU closure/weekend/scheduled break.

- New entries blocked.
- V1 normally expects no bot-managed Gold position to remain open because PRE_CLOSE should have flattened it.
- If a managed position remains because broker became unavailable, close acknowledgement was ambiguous, or another fault occurred, persist/reconcile exposure rather than pretending flat.
- Reconciliation/state maintenance continues where possible.
- Research/background analysis may continue.

### REOPEN_WARMUP

First returned quote after closure is not sufficient for trade readiness.

Evidence may include fresh valid quotes, symbol tradeability, normalized spread, candle continuity, gap/dislocation assessment and sufficient fresh data for required timeframe decisions.

Warmup is evidence-driven rather than an unnecessarily long fixed delay.

### HOLIDAY_CAUTION

Holiday context may imply unusual participation/liquidity, but broker tradeability/live data remain authority for actual OPEN/CLOSED state.

## News-safety states

States:

```text
NEWS_CLEAR
NEWS_BLACKOUT
NEWS_SAFETY_UNKNOWN
POST_NEWS_WARMUP
```

### Initial V1 hard blackout windows

```text
TIER 1 CRITICAL   → no new entries from 15 min before through 15 min after
TIER 2 HIGH       → no new entries from 5 min before through 5 min after
TIER 3 CONTEXT    → no automatic hard blackout
```

Known linked TIER 1 clusters remain blocked through 15 minutes after the final scheduled critical item.

### NEWS_CLEAR

Required event-safety information is verified, no hard blackout is active, and required post-event normalization has passed.

### NEWS_BLACKOUT

Blocks new entries/re-entry/add-ons, but does **not** automatically force-close an already-open managed trade.

### NEWS_SAFETY_UNKNOWN

Required event safety cannot be verified through accepted current/fallback sources. New entries fail closed; provider failure never becomes silent `NEWS_CLEAR`.

### POST_NEWS_WARMUP

After minimum blackout ends, new entries remain paused only while market evidence remains abnormal/unreliable.

Evaluate fresh quotes, normalized spread, data continuity, volatility/dislocation and execution freshness. If normalized at expiry, permission may return promptly. Severe dislocation requires at least one clean completed M5 candle plus normalized execution conditions.

## Unscheduled shock interaction

An unscheduled shock may have no calendar event. Market-data, volatility and execution-safety authorities may still block/degrade trading because of spread explosion, stale quotes, extreme velocity, gaps or dislocation.

## Risk/system states

### NORMAL

No special risk lock/cooldown is active.

### LOSS_LOCKED

Risk Contract reports daily loss budget exhausted.

- New entries/re-entry/add-ons blocked.
- Open-trade management remains active where safely possible.
- Manual reset is disabled by default.
- If explicitly enabled, V1 permits at most one governed manual reset per UTC risk day using deliberate `R,R` confirmation and durable audit semantics owned by `RISK_CONTRACT.md`.
- Manual reset never clears unrelated `BLOCKED` conditions.

### COOLDOWN

V1 transitions to global `COOLDOWN` after **3 consecutive closed bot-trade losses** or when Risk/Execution declares an abnormal execution/shock cooldown.

For the 3-loss trigger:

- minimum duration is 30 minutes;
- time alone cannot release it;
- release also requires fresh completed M15 context after the trigger, no unresolved execution/reconciliation fault and a fresh valid opportunity/episode rather than replaying the failed setup.

One ordinary loss does **not** create a global cooldown.

Same-Market-Episode churn is handled separately: at most one genuinely fresh re-entry is allowed in the same episode; a second loss in that episode locks further entries for that episode.

### BLOCKED

Critical truth/safety unavailable/invalid, for example account identity uncertainty, stale/corrupt required data, unresolved order lifecycle, unknown financial state, persistence corruption, unknown required news safety or execution-controller ownership uncertainty.

No operator shortcut may silently bypass genuine `BLOCKED` state.

## Permission composition

```text
Market State
+ News Safety State
+ Risk State
+ System/Data State
+ Execution Readiness
= Entry Permission
```

Examples:

```text
OPEN + NEWS_CLEAR + NORMAL + READY → entries may be evaluated
PRE_CLOSE + otherwise-valid state → no new entry; existing managed trade must flatten
OPEN + NEWS_CLEAR + LOSS_LOCKED + READY → no new entries
OPEN + NEWS_CLEAR + COOLDOWN + READY → no new entries until cooldown release criteria pass
OPEN + NEWS_BLACKOUT + NORMAL + READY → no new entries
OPEN + POST_NEWS_WARMUP + NORMAL + READY → no new entries until normalization passes
OPEN + NEWS_SAFETY_UNKNOWN + NORMAL + READY → no new entries
HOLIDAY_CAUTION + NEWS_CLEAR + NORMAL + READY → may trade with caution context
OPEN + NEWS_CLEAR + NORMAL + BLOCKED → no new entries
```

## UTC risk-day relationship

Daily-loss accounting/reset boundary is owned by `RISK_CONTRACT.md`: UTC calendar risk day (`00:00 UTC`). This state machine consumes the resulting risk-state transitions without maintaining a competing formula.

## Broker truth over calendar

Calendar may suggest expected state, but broker tradeability and valid live quotes determine whether XAU can execute. Configured close schedule enters PRE_CLOSE early enough to flatten, while broker state remains final fact for whether close can actually execute.

## Open-trade priority

A hard new-entry block should not automatically stop safe management of an open managed position.

`PRE_CLOSE` is a special case requiring flatten before known XAU closure. Scheduled news blackout is **not** equivalent to PRE_CLOSE and does not by itself force-close an existing position.

## Dashboard requirements

Show at least Market State, News Safety State, next event/tier, blackout countdown, Risk State, loss streak, cooldown state/release condition, manual-reset state, System/Execution State, primary/secondary blocker, PRE_CLOSE countdown/flatten status and next expected transition where knowable.

## Tests required

- OPEN/PRE_CLOSE/CLOSED transitions;
- PRE_CLOSE blocks new entries and requests governed flatten;
- no intentional carry through scheduled daily XAU break/weekend;
- close ambiguity is persisted/reconciled;
- REOPEN_WARMUP evidence;
- holiday caution not market closure;
- TIER 1 `-15/+15` and linked-cluster blackout;
- TIER 2 `-5/+5` blackout;
- TIER 3 no automatic hard blackout;
- provider failure/fallback and `NEWS_SAFETY_UNKNOWN`;
- post-news normalization/clean-M5 severe-dislocation rule;
- scheduled news does not auto-close managed trade;
- one ordinary loss does not enter global cooldown;
- 3 consecutive closed losses enter 30-minute minimum cooldown;
- cooldown cannot release on timer alone;
- same-episode second loss locks episode;
- manual reset default OFF and cannot bypass BLOCKED;
- permission-composition truth table;
- broker state overrides calendar assumptions.

## Open questions

- exact PRE_CLOSE no-new-entry and mandatory-flatten lead time;
- exact REOPEN_WARMUP evidence/fresh-candle requirements;
- final production event provider(s), freshness TTL and provider-specific mapping details;
- future research-backed changes to initial news tiers/windows;
- exact keyboard confirmation timing for `R,R` as an operator UX detail.
