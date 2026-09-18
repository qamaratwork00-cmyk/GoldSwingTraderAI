# GoldSwingTraderAI — Session and Risk State Machine

**Status:** PROVISIONAL  
**Version:** 0.3-design  
**Authority:** Hard market/session permission states, risk/system permission composition, news-safety states and state transitions.  
**Depends on:** `RISK_CONTRACT.md`, `EXECUTION_AND_BROKER_SAFETY.md`, `../10-market-intelligence/FUNDAMENTAL_AND_NEWS.md`, `../10-market-intelligence/SESSION_CONTEXT.md`

## Core principle

Market state, risk state and system/execution safety are separate authorities. The market can be open while risk is locked, and a holiday can reduce participation while XAU remains genuinely tradeable.

This document owns **permission states**, not session-analysis quality or daily-loss arithmetic.

## Market/session permission states

### OPEN

Broker/live market is functioning and new trades may be considered if risk, news, system and execution authorities also permit them.

### PRE_CLOSE

Scheduled XAU closure is approaching.

V1 policy:

- new entries are blocked;
- existing bot-managed Gold positions must be flattened before the scheduled closure while the broker remains tradeable;
- Trade Manager may protect/exit earlier for normal structural reasons, but it may not intentionally carry a bot-managed position through the scheduled daily XAU break or weekend closure;
- the exact pre-close no-new-entry/mandatory-flatten lead time remains a broker/research calibration value.

Reason codes should distinguish `SESSION_PRE_CLOSE` from `PRE_CLOSE_FLATTEN`.

### CLOSED

Broker-confirmed XAU closure/weekend/scheduled break.

- New entries: blocked.
- V1 normally expects no bot-managed Gold position to remain open because PRE_CLOSE should have flattened it.
- If a managed position remains because the broker became unavailable, a close acknowledgement was ambiguous, or another operational fault occurred, persist/reconcile the exposure as an exceptional state rather than pretending it is flat.
- Reconciliation/state maintenance continues where possible.
- Research/background analysis may continue.

### REOPEN_WARMUP

The first returned quote after closure is not sufficient for trade readiness.

Evidence may include:

- fresh valid quotes;
- symbol tradeability;
- normalized spread;
- candle continuity;
- gap/dislocation assessment;
- sufficient fresh data for required timeframe decisions.

Warmup is evidence-driven rather than an unnecessarily long fixed delay. No fresh entry is allowed until required reopen evidence passes.

### HOLIDAY_CAUTION

Holiday calendar context indicates potentially unusual participation/liquidity, but the market may remain open. Broker tradeability and live market data remain authority for actual OPEN/CLOSED status.

## News-safety states

Market Intelligence publishes event facts/provider health. This state machine derives hard permission according to the frozen event policy.

Suggested states:

```text
NEWS_CLEAR
NEWS_BLACKOUT
NEWS_SAFETY_UNKNOWN
POST_NEWS_WARMUP
```

### NEWS_CLEAR

Required event-safety information is verified and no configured hard blackout is active.

### NEWS_BLACKOUT

A verified scheduled event falls inside a configured hard no-new-entry window.

This is an expected safety state, not a system fault.

### NEWS_SAFETY_UNKNOWN

Required scheduled-event safety cannot be verified. New entries fail closed where policy requires event verification.

### POST_NEWS_WARMUP

After a major event, new entries remain paused until the configured evidence of market normalization is satisfied. The intended design is not timer-only if spread/quotes/volatility remain dislocated.

Exact event tiers/windows/recovery criteria remain open.

## Risk/system states

### NORMAL

No special risk lock is active.

### LOSS_LOCKED

The Risk Contract reports that the daily loss budget is exhausted.

- New entries/re-entry/add-ons blocked.
- Open-trade management remains active where safely possible.
- Governed manual reset may transition the risk state only according to `RISK_CONTRACT.md`.

This document does **not** redefine daily P/L calculation/reset-reference semantics.

### COOLDOWN

Temporary pause after a frozen adverse-behaviour/churn trigger. Exact trigger/release rules belong to Risk Contract and remain open.

### BLOCKED

Critical truth/safety is unavailable or invalid, for example:

- broker/account identity uncertainty;
- stale/corrupt required market data;
- unresolved order lifecycle;
- unknown required financial state;
- critical persistence corruption;
- unknown required news safety;
- execution-controller ownership uncertainty.

No operator shortcut may silently bypass a genuine `BLOCKED` state.

## Permission composition

Final entry permission is composed from at least:

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
PRE_CLOSE + any otherwise-valid state → no new entry; existing managed trade must flatten
OPEN + NEWS_CLEAR + LOSS_LOCKED + READY → no new entries
OPEN + NEWS_BLACKOUT + NORMAL + READY → no new entries; expected safety block
OPEN + NEWS_SAFETY_UNKNOWN + NORMAL + READY → no new entries if verification required
HOLIDAY_CAUTION + NEWS_CLEAR + NORMAL + READY → may trade with caution context
OPEN + NEWS_CLEAR + NORMAL + BLOCKED → no new entries
```

## UTC risk-day relationship

Daily-loss accounting/reset boundary is owned by `RISK_CONTRACT.md`. The current provisional decision is a **UTC calendar risk day (`00:00 UTC`)** rather than XAU reopen semantics.

This state machine simply consumes the resulting risk-state transition; it does not maintain a competing reset formula.

## Broker truth over calendar

A calendar may suggest expected open/closed/holiday conditions, but actual broker tradeability and valid live quotes determine whether XAU can be executed.

Calendar says open + broker unavailable → not executable.

Holiday says caution + broker/live market healthy → not automatically CLOSED.

The configured close schedule is used to enter PRE_CLOSE early enough to flatten, but broker tradeability remains the final fact for whether a close can actually execute.

## Open-trade priority

A hard new-entry block should not automatically stop safe management of an already-open managed position. Trade Manager/execution remain active where required and broker operations are safely available.

`PRE_CLOSE` is a special case: it creates an explicit V1 requirement to close the bot-managed position before the known XAU closure rather than carry gap risk into reopen.

## Dashboard requirements

Operator should distinguish at a glance:

- Market State;
- News Safety State;
- Risk State;
- System/Execution State;
- exact primary/secondary block reason;
- PRE_CLOSE countdown/flatten status where knowable;
- next expected transition where knowable;
- manual-reset state as published by Risk Contract.

## Tests required

- OPEN/PRE_CLOSE/CLOSED transitions;
- PRE_CLOSE blocks new entries;
- PRE_CLOSE requests governed flatten of any bot-managed Gold position;
- no intentional managed-position carry through scheduled daily XAU break/weekend;
- close ambiguity/unavailable broker is persisted and reconciled rather than treated as flat;
- REOPEN_WARMUP evidence;
- holiday caution not market closure;
- NEWS_CLEAR/BLACKOUT/UNKNOWN/WARMUP transitions;
- daily-loss state consumed from Risk Contract without duplicate accounting;
- BLOCKED state cannot be overridden by manual reset;
- permission composition truth table;
- broker state overrides calendar assumptions.

## Open questions

- exact PRE_CLOSE no-new-entry and mandatory-flatten lead time;
- exact REOPEN_WARMUP evidence/fresh-candle requirements;
- exact event tiers/blackout windows;
- exact POST_NEWS_WARMUP normalization rules;
- final cooldown transition rules (owned numerically by Risk Contract).
