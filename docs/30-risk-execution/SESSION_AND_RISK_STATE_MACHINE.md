# GoldSwingTraderAI — Session and Risk State Machine

**Status:** PROVISIONAL  
**Version:** 0.7-implementation  
**Authority:** Hard market/session permission states, risk/system permission composition, news-safety states and state transitions.  
**Depends on:** `RISK_CONTRACT.md`, `EXECUTION_AND_BROKER_SAFETY.md`, `../10-market-intelligence/FUNDAMENTAL_AND_NEWS.md`, `../10-market-intelligence/SESSION_CONTEXT.md`

## Core principle

Market state, risk state and system/execution safety are separate authorities. The market can be open while risk is locked, and a holiday can reduce participation while XAU remains genuinely tradeable.

This document owns **permission states**, not session-analysis quality, event-fact sourcing or daily-loss arithmetic.

## Phase 6 implementation checkpoint

Hard session/news permission is implemented in `src/goldswingtraderai/risk/permissions.py` and deterministic CI is green.

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

Important implementation behaviour:

- daily PRE_CLOSE uses the frozen `T-20m` no-new-entry and `T-10m` flatten thresholds;
- weekend PRE_CLOSE uses `T-60m` and `T-30m`;
- daily reopen requires one clean completed M5 plus normalized conditions;
- weekend reopen requires two clean completed M5 candles, gap assessment and normalized conditions;
- holiday context remains `HOLIDAY_CAUTION` and does not manufacture a market closure;
- missing/unverified required broker session schedule becomes `UNKNOWN`, not an invented close time;
- unavailable/stale required news truth becomes `NEWS_SAFETY_UNKNOWN`, not silent clear;
- Tier-1/Tier-2 windows block new entry according to the frozen windows already normalized by the News desk;
- severe post-news dislocation requires normalized execution conditions plus one clean completed M5;
- this layer has no broker-write authority. Phase 7 will combine it with account/data/risk/controller/execution checks in the centralized write gate.

## Market/session permission states

### OPEN

Broker/live market is functioning and new trades may be considered if risk, news, system and execution authorities also permit them.

### PRE_CLOSE

Scheduled XAU closure is approaching.

Initial V1 timing is relative to the broker's verified XAU session-close time, not a hard-coded local/server clock.

#### Daily XAU break

```text
T-20 min  → no new entries
T-10 min  → mandatory governed flatten of any bot-managed Gold position
T-0       → expected CLOSED
```

#### Weekend closure

```text
T-60 min  → no new entries
T-30 min  → mandatory governed flatten of any bot-managed Gold position
T-0       → expected CLOSED
```

Trade Manager may protect/exit earlier for structural reasons, but may not intentionally carry a bot-managed position through the scheduled daily XAU break or weekend closure.

Reason codes distinguish `SESSION_PRE_CLOSE` from `PRE_CLOSE_FLATTEN`.

If the broker's session schedule cannot be verified, the system must not invent a close time. New-entry permission remains unknown until reliable session truth is available.

### CLOSED

Broker-confirmed XAU closure/weekend/scheduled break.

- New entries blocked.
- V1 normally expects no bot-managed Gold position to remain open because PRE_CLOSE should have flattened it.
- If a managed position remains because broker became unavailable, close acknowledgement was ambiguous, or another fault occurred, persist/reconcile exposure rather than pretending flat.
- Reconciliation/state maintenance continues where possible.
- Research/background analysis may continue.

### REOPEN_WARMUP

First returned quote after closure is not sufficient for trade readiness.

#### Daily reopen

New entries may resume only after all required facts pass:

- broker reports XAU tradeable;
- fresh valid Bid/Ask and required market data are healthy;
- spread/execution conditions have normalized under Execution Safety;
- no unresolved gap/dislocation/data/reconciliation problem exists;
- at least **one clean completed M5 candle** after reopen is available.

#### Weekend reopen

Weekend reopen is treated more conservatively because gap risk can be materially larger. New entries may resume only after:

- broker reports XAU tradeable;
- weekend gap/dislocation is assessed;
- fresh quotes/data and spread/execution conditions normalize;
- no unresolved reconciliation/data problem exists;
- at least **two clean completed M5 candles** after reopen are available.

A completed-candle requirement is a minimum freshness rule, not permission to ignore abnormal spread/quotes/dislocation. If conditions remain abnormal after the minimum candles, `REOPEN_WARMUP` continues.

### HOLIDAY_CAUTION

Holiday context may imply unusual participation/liquidity, but broker tradeability/live data remain authority for actual OPEN/CLOSED state. Holiday caution is context, not an automatic hard block.

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
PRE_CLOSE + otherwise-valid state → no new entry; existing managed trade must flatten at required threshold
OPEN + NEWS_CLEAR + LOSS_LOCKED + READY → no new entries
OPEN + NEWS_CLEAR + COOLDOWN + READY → no new entries until cooldown release criteria pass
OPEN + NEWS_BLACKOUT + NORMAL + READY → no new entries
OPEN + POST_NEWS_WARMUP + NORMAL + READY → no new entries until normalization passes
OPEN + NEWS_SAFETY_UNKNOWN + NORMAL + READY → no new entries
HOLIDAY_CAUTION + NEWS_CLEAR + NORMAL + READY → may trade with caution context
OPEN + NEWS_CLEAR + NORMAL + BLOCKED → no new entries
```

Phase 6 implements the session/news portion of this composition. The full account/data/risk/controller/broker-write composition belongs to the centralized Phase-7 Execution Permission Gate.

## UTC risk-day relationship

Daily-loss accounting/reset boundary is owned by `RISK_CONTRACT.md`: UTC calendar risk day (`00:00 UTC`). This state machine consumes the resulting risk-state transitions without maintaining a competing formula.

## Broker truth over calendar

Calendar may suggest expected state, but broker tradeability and valid live quotes determine whether XAU can execute. The verified broker XAU session schedule drives PRE_CLOSE timing so DST/server-time changes do not rely on a guessed fixed clock.

## Open-trade priority

A hard new-entry block should not automatically stop safe management of an open managed position.

`PRE_CLOSE` is a special case requiring flatten before known XAU closure. Scheduled news blackout is **not** equivalent to PRE_CLOSE and does not by itself force-close an existing position.

## Dashboard requirements

Show at least Market State, News Safety State, next event/tier, blackout countdown, Risk State, loss streak, cooldown state/release condition, manual-reset state, System/Execution State, primary/secondary blocker, PRE_CLOSE countdown/flatten status, REOPEN_WARMUP candle progress and next expected transition where knowable.

## Tests required

Implemented deterministic coverage includes:

- daily `T-20/T-10` transitions;
- weekend `T-60/T-30` transitions;
- CLOSED and unverified-schedule fail-safe states;
- daily one-M5 and weekend two-M5/gap-assessment reopen rules;
- holiday caution not market closure;
- Tier-1/Tier-2 blackout and clear path;
- required news truth failure;
- severe post-news one-clean-M5 rule;
- session/news permission composition and PRE_CLOSE flatten propagation.

Later integration/fault tests must additionally prove broker-session sourcing, actual scheduled close/reopen behaviour and interaction with the Phase-7 execution gate.

## Open questions

- final production event provider(s), freshness TTL and provider-specific mapping details;
- verified broker-session schedule sourcing/adapter details for the actual MT5/broker environment;
- future research-backed changes to initial news tiers/windows;
- exact keyboard confirmation timing for `R,R` as an operator UX detail;
- future research-backed changes, if any, to initial pre-close/reopen timing.
