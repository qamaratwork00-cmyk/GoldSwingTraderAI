# GoldSwingTraderAI — Session and Risk State Machine

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Market/session state and risk/system permission states

## Core principle

Market state and risk/system state are separate. The market can be open while trading is loss-locked, or a holiday can reduce liquidity while the market remains genuinely tradeable.

## Market/session states

### OPEN

Normal market operation. New trades may be considered if risk, safety and execution authorities also permit them.

### PRE-CLOSE

Scheduled XAU closure is approaching.

- New entries: blocked by default.
- Open-trade management: remains active.
- Position flatten/overnight policy: not yet frozen for this project.

### CLOSED

Broker-confirmed XAU closure, weekend or scheduled rollover break.

- New entries: blocked.
- Open-trade broker actions depend on market availability; reconciliation/state maintenance continues.
- Research/background analysis may continue.

### REOPEN_WARMUP

The first returned quote after a closure does not automatically mean the system is ready to trade.

The system should verify:

- fresh quotes;
- valid symbol tradeability;
- acceptable spread behaviour;
- candle continuity;
- no unexplained open-market gaps;
- enough fresh data for the required timeframe decisions.

Warmup should be evidence-driven rather than an unnecessarily long fixed delay. Exact fresh-candle requirements remain open.

### HOLIDAY_CAUTION

A calendar holiday does not automatically mean Gold is closed.

If XAU is genuinely open and market data is healthy, trading may remain allowed. Holiday context may influence soft session/liquidity evidence, but broker tradeability and actual market data are authoritative for market-open state.

A US holiday with an open, functioning Gold market is therefore not automatically `CLOSED`.

## Risk/system states

### NORMAL

No special risk lock is active.

### LOSS_LOCKED

The configured daily loss limit has been reached.

- New entries: blocked.
- Open-trade management: remains active.
- Manual governed reset: retained as a supported operator feature under the Risk Contract.

### COOLDOWN

Temporary pause after defined adverse behaviour such as a loss sequence or other future policy trigger.

Open-trade management remains active. Exact cooldown trigger/duration and whether a fresh market event is required in addition to time remain open.

### BLOCKED

Critical truth/safety is unavailable or invalid. Examples may include:

- broker/account identity uncertainty;
- stale/corrupt market data;
- unresolved order lifecycle;
- unverified financial state;
- persistence corruption;
- hard news-safety uncertainty where verification is required.

No operator shortcut should silently bypass a genuine `BLOCKED` state.

## Permission composition

Final entry permission is composed from at least:

```text
Market State
+ Risk State
+ System/Safety State
+ Execution Readiness
= Entry Permission
```

Examples:

```text
OPEN + NORMAL + READY → entries may be evaluated
OPEN + LOSS_LOCKED + READY → no new entries; management active
HOLIDAY_CAUTION + NORMAL + READY → entries allowed with caution context
OPEN + NORMAL + BLOCKED → no new entries
```

## Daily loss reset and risk-cycle boundary

The project retains daily loss locking and governed manual reset. The exact automatic reset boundary must be frozen separately because the design discussion has considered both traditional risk-day rollover and XAU reopen/session-aware semantics.

Until resolved, implementation must not guess this boundary.

## Dashboard requirements

The operator should be able to distinguish at a glance:

- market state;
- risk state;
- system/safety state;
- reason for any block;
- next expected market transition where known;
- manual-reset usage/audit state.
