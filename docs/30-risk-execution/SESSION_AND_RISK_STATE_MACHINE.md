# GoldSwingTraderAI — Session and Risk State Machine

**Status:** PROVISIONAL — IMPLEMENTED BASELINE  
**Version:** 0.8-implementation  
**Authority:** Hard market/session permission states, risk/system permission composition, news-safety states and state transitions.  
**Depends on:** `RISK_CONTRACT.md`, `EXECUTION_AND_BROKER_SAFETY.md`, `../10-market-intelligence/FUNDAMENTAL_AND_NEWS.md`, `../10-market-intelligence/SESSION_CONTEXT.md`

## Core principle

Market state, risk state and system/execution safety are separate authorities. The market can be open while risk is locked, and a holiday can reduce participation while XAU remains genuinely tradeable.

This document owns **permission states**, not session-analysis quality, event-fact sourcing or daily-loss arithmetic.

## Current implementation checkpoint

Hard session/news permission is implemented in:

```text
src/goldswingtraderai/risk/permissions.py
```

The centralized broker-write composition consuming these results is implemented in:

```text
src/goldswingtraderai/execution/gate.py
src/goldswingtraderai/execution/service.py
```

Implemented contracts:

```text
BrokerSessionFacts
→ evaluate_market_permission()
→ MarketPermission

NewsFacts + NewsRecoveryFacts
→ evaluate_news_permission()
→ NewsPermission

MarketPermission + NewsPermission
→ combine_session_news_permission()
→ SessionNewsPermission
```

Important current behaviour:

- daily PRE_CLOSE: `T-20m` no new entry, `T-10m` mandatory flatten;
- weekend PRE_CLOSE: `T-60m`, `T-30m`;
- daily reopen: one clean completed M5 + normalized conditions;
- weekend reopen: two clean completed M5 + gap assessment + normalized conditions;
- holiday context remains caution, not fake closure;
- missing/unverified required broker schedule becomes `UNKNOWN`;
- unavailable/stale required news truth becomes `NEWS_SAFETY_UNKNOWN`;
- Tier 1/Tier 2 windows block according to frozen policy;
- severe post-news dislocation requires normalized execution conditions + one clean completed M5;
- these permission outputs have no raw broker-write call themselves; the centralized Execution Gate owns final composition.

Production broker-session schedule sourcing and external news-provider adapters remain integration work. The permission policy itself is implemented deterministically.

## Market/session permission states

### OPEN

Broker/live market is functioning and new trades may be considered if risk, news, system and execution authorities also permit them.

### PRE_CLOSE

Scheduled XAU closure is approaching. Timing is relative to verified broker XAU schedule, not a guessed fixed clock.

#### Daily XAU break

```text
T-20 min  → no new entries
T-10 min  → mandatory governed flatten
T-0       → expected CLOSED
```

#### Weekend closure

```text
T-60 min  → no new entries
T-30 min  → mandatory governed flatten
T-0       → expected CLOSED
```

Trade Manager may protect/exit earlier for structural reasons, but cannot intentionally carry a bot-managed Gold position through scheduled closure.

If the broker session schedule cannot be verified, the system must not invent a close time. New-entry permission remains unknown until reliable session truth exists.

### CLOSED

- new entries blocked;
- bot normally expects no managed Gold position because PRE_CLOSE should have flattened it;
- unresolved/ambiguous exposure persists and reconciles rather than being marked flat by assumption;
- research/background analysis may continue.

### REOPEN_WARMUP

First returned quote is not sufficient for trade readiness.

#### Daily reopen

Requires:

- broker reports XAU tradeable;
- fresh valid Bid/Ask and healthy required data;
- spread/execution conditions normalized;
- no unresolved gap/dislocation/reconciliation issue;
- at least **one clean completed M5** after reopen.

#### Weekend reopen

Requires:

- broker reports XAU tradeable;
- weekend gap/dislocation assessed;
- quotes/data/spread normalized;
- no unresolved reconciliation/data issue;
- at least **two clean completed M5** after reopen.

Minimum clean-candle count never overrides abnormal live execution conditions.

### HOLIDAY_CAUTION

Holiday context may imply unusual participation/liquidity, but broker tradeability/live data remain authority for actual OPEN/CLOSED state. Holiday caution is context, not automatic hard block.

## News-safety states

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

Known linked Tier-1 clusters remain blocked through 15 minutes after the final scheduled critical item.

### NEWS_CLEAR

Required event-safety information is verified, no hard blackout is active and required post-event normalization has passed.

### NEWS_BLACKOUT

Blocks new entries/re-entry/add-ons but does **not** automatically force-close an already-open managed trade.

### NEWS_SAFETY_UNKNOWN

Required event safety cannot be verified. New entries fail closed; provider failure never becomes silent `NEWS_CLEAR`.

### POST_NEWS_WARMUP

After minimum blackout ends, entries remain paused only while market evidence remains abnormal/unreliable. Severe dislocation requires one clean completed M5 plus normalized execution conditions.

## Unscheduled shock interaction

An unscheduled shock may have no calendar event. Market-data, volatility and execution-safety authorities may still degrade/block new entry because of spread explosion, stale quotes, extreme velocity, gaps or dislocation.

## Risk/system states

### NORMAL

No special risk lock/cooldown is active.

### LOSS_LOCKED

Risk Contract reports daily loss budget exhausted.

- no new entries/re-entry/add-ons;
- open-trade management remains active where safely possible;
- manual reset is OFF by default;
- if explicitly enabled, max one governed `R,R` reset per UTC risk day from LOSS_LOCKED;
- reset does not clear unrelated blockers.

### COOLDOWN

V1 enters global cooldown after **3 consecutive closed bot-trade losses** or an abnormal execution/shock cooldown.

For the three-loss trigger:

- minimum 30 minutes;
- time alone cannot release it;
- release also requires fresh completed M15 context, no unresolved execution/reconciliation fault and a fresh valid opportunity/episode.

One ordinary loss does not create global cooldown.

Same-Market-Episode churn is separate: at most one genuinely fresh re-entry is allowed in the episode; if that re-entry also loses, further entries for that episode are locked.

### BLOCKED

Critical truth/safety is unavailable/invalid, for example account identity uncertainty, stale/corrupt required data, unresolved order lifecycle, unknown financial state, persistence corruption, unknown required news safety or controller ownership uncertainty.

No operator shortcut may silently bypass genuine `BLOCKED` state.

## Permission composition

```text
Market State
+ News Safety
+ Risk State
+ System/Data State
+ Position/Order State
+ Controller State
+ Fresh Execution Checks
= centralized Execution Permission
```

Examples:

```text
OPEN + NEWS_CLEAR + NORMAL + all hard authorities PASS → broker write may be ALLOW
PRE_CLOSE + otherwise-valid state → no new entry; managed position must flatten at required threshold
OPEN + LOSS_LOCKED → no new entry
OPEN + COOLDOWN → no new entry until release criteria pass
OPEN + NEWS_BLACKOUT → no new entry
OPEN + POST_NEWS_WARMUP → no new entry until normalization passes
OPEN + NEWS_SAFETY_UNKNOWN → no new entry
HOLIDAY_CAUTION + otherwise healthy → may trade; holiday itself is not a hard block
```

The current `ExecutionPermissionGate` consumes these hard-authority results instead of recreating their policy.

## UTC risk-day relationship

Daily-loss accounting/reset boundary is owned by `RISK_CONTRACT.md` at `00:00 UTC`. This state machine consumes the resulting risk-state transitions without maintaining a competing formula.

## Broker truth over calendar

Calendar may suggest expected state, but broker tradeability and valid live quotes determine whether XAU can execute. Verified broker schedule drives PRE_CLOSE timing so DST/server-time changes do not rely on a guessed clock.

## Open-trade priority

A hard new-entry block should not automatically stop safe management of an open bot-managed position.

`PRE_CLOSE` is the explicit exception requiring flatten before known closure. Scheduled news blackout is not equivalent to PRE_CLOSE and does not by itself force-close an existing position.

## Persistence/restart

Risk-day/cooldown/episode state is durable through SQLite. Unresolved execution intents and managed-trade context also persist through their owning repositories. Restart must restore/reconcile those states before new broker writes.

## Dashboard requirements

Show as available:

- Market State;
- News Safety State;
- next event/tier/countdown;
- Risk State / loss streak / cooldown;
- manual-reset state;
- primary/secondary blocker;
- PRE_CLOSE countdown/flatten status;
- REOPEN_WARMUP progress;
- centralized Execution Permission result.

## Tests / current evidence

Deterministic coverage includes:

- daily `T-20/T-10` transitions;
- weekend `T-60/T-30` transitions;
- CLOSED/unverified-schedule fail-safe state;
- daily one-M5 and weekend two-M5/gap-assessment reopen rules;
- holiday caution not closure;
- Tier-1/Tier-2 blackout and clear path;
- required news truth failure;
- severe post-news one-clean-M5 rule;
- session/news permission composition;
- PRE_CLOSE flatten propagation;
- integration with centralized execution gate inputs.

Still required for release evidence:

- real broker-session schedule sourcing;
- production news-provider integration;
- controlled MT5 DEMO scheduled close/reopen/news observations;
- failover/restart interaction under real broker conditions.

## Open questions

- final production event provider(s), freshness TTL and provider mapping;
- verified broker-session schedule sourcing for intended broker environment;
- future evidence-backed changes to news tiers/windows;
- exact `R,R` keyboard confirmation timing as operator UX detail;
- future evidence-backed changes, if any, to pre-close/reopen timings.
