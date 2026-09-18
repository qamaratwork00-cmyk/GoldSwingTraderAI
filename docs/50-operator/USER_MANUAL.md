# GoldSwingTraderAI — User Manual

**Status:** DRAFT  
**Version:** 0.2-design  
**Authority:** Human-facing explanation of normal operation and operator actions.  
**Depends on:** `DASHBOARD_AND_UX.md`, `SETUP_AND_RUN_GUIDE.md`

## Purpose

This manual explains how to interpret and operate the bot. It does not redefine trading logic; authoritative subsystem docs own behaviour.

## Normal daily use

Typical operation should be simple:

```text
1. Open MT5 and verify the intended account/environment.
2. Start GoldSwingTraderAI.
3. Wait for startup checks and broker reconciliation.
4. Confirm dashboard shows the expected runtime role and readiness.
5. Let the bot analyze/manage automatically.
6. Use safe shutdown when stopping the process.
```

Normal operation should not require editing code or tuning scores manually.

## Reading the main status

Common meanings:

- `🟢 ENTER BUY/SELL` — market/timing/plan/risk/safety/execution authorities have passed for the current governed action;
- `🟡 WAIT` — the thesis may remain valid but current entry/timing is not good enough;
- `MISSED` — an executable opportunity window passed without justified fill;
- `INVALID` — the trade thesis itself no longer survives;
- `🔴 BLOCKED` — a hard risk/news/execution/system authority prevents action;
- `📈 OPEN TRADE` — Trade Manager owns ongoing position-management decisions.

Always read the reason code/human explanation rather than interpreting status color alone.

## Why no trade?

The bot should tell the operator whether the trade stopped at market opportunity, entry timing, Trade Plan, news, risk or execution.

Examples:

- `ENTRY_EXTENDED` — setup remains valid but price is too late/extended;
- `TARGET_ROOM_POOR` — plan economics/location are poor;
- `NEWS_BLACKOUT` — expected safety block;
- `MIN_LOT_UNAFFORDABLE` — minimum broker volume exceeds approved risk;
- `DATA_STALE` — system/data problem requiring safe block.

Do not treat every non-trade as a fault.

## Central Execution Permission

All final bot-managed MT5 create/modify/close actions pass through one centralized Execution Permission Gate.

The dashboard should show its result clearly, for example:

```text
⚙️ EXECUTION
Environment       DEMO ✅ AUTHORIZED
Controller        ⚡ PRIMARY
Permission        ✅ ALLOW
```

or:

```text
Environment       REAL
Permission        🔴 BLOCK
Reason            ENVIRONMENT_NOT_AUTHORIZED
Policy            DEMO-FIRST
```

The current project release is DEMO-first. This does not mean the architecture can never trade a real account. A future explicitly approved REAL policy is intended to use the same strategy/risk/execution gate and broker path.

Normal safety blockers such as daily loss, news, spread, price drift, min-lot risk, margin, order ambiguity or another active controller apply to the approved execution environment and are not hidden permanent LIVE blockers.

## Risk states

- `NORMAL` — risk system permits evaluation;
- `LOSS_LOCKED` — daily loss budget exhausted; no new entries;
- `COOLDOWN` — temporary churn/adverse-behaviour pause according to frozen policy;
- `BLOCKED` — critical financial/system truth is unavailable/unsafe.

Open-trade management remains active where safely possible.

## Manual loss reset

If available under the frozen Risk Contract, manual reset is a deliberate governed action. It does not delete today's broker loss and cannot bypass technical/account/order/execution blocks.

## Open trade

When a managed trade is open, read:

- strategy/episode identity;
- entry/current price;
- original/current SL;
- current R, MFE and MAE;
- primary/expansion objectives;
- Continuation/Reversal state;
- Trade Manager action and reason.

Small opposite candles or a temporary pullback do not automatically mean the bot should exit.

## Learning

The Learning panel may show StrategyMemory, Entry Learning, Exit Learning and Champion/Challenger status.

Learning does not immediately rewrite live rules after a few trades. Proposed improvements go through research, validation, holdout, Shadow and DEMO Canary before production promotion.

## Autonomous strategies

Autonomous candidates are declarative research hypotheses. They do not directly send orders or self-promote. Their status/history survives restart and machine migration.

## System Health

A normal trading decision such as `WAIT` or an expected policy block such as `NEWS_BLACKOUT` is not automatically a system problem.

System Health reports actual operational issues such as stale data, account mismatch, order ambiguity, state corruption, provider failure or backup/restore problems.

Follow the dashboard's `Trading Impact`, `Recovery` and `Action Required` fields.

## Runtime roles

- `PRIMARY EXECUTOR` — the only active broker-write controller for the managed account/symbol;
- `OBSERVER` — analysis/dashboard with broker writes disabled;
- `RESEARCH` — replay/experiment use with no production broker writes.

A second laptop should not independently execute against the same managed account/symbol.

## Backups and laptop change

Strategies, learning, autonomous candidates and research/promotion history should be recoverable from the project's backed-up state. Financial-authority credentials are configured separately and must not be committed publicly.

After restore on another laptop, the bot must reconcile current broker positions/orders/deals before resuming new entries.

## Do not manually edit critical state

Do not manually delete/edit order lifecycle, risk state, Strategy Registry, promotion history or learning databases to clear an error. Use documented recovery/reset tools when implemented.

## Project status caveat

This manual remains DRAFT during design. Exact commands, keys, launcher names and screenshots will be added only after the corresponding implementation exists and has been verified.
