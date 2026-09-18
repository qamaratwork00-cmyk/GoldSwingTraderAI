# GoldSwingTraderAI — User Manual

**Status:** DRAFT  
**Version:** 0.4-design  
**Authority:** Human-facing explanation of normal operation and operator actions.  
**Depends on:** `50-operator/DASHBOARD_AND_UX.md`, `SETUP_AND_RUN_GUIDE.md`

## Purpose

This manual explains how to operate and interpret GoldSwingTraderAI. It does not redefine trading logic; authoritative subsystem documents own behaviour.

## Normal daily use

```text
1. Open MT5 and connect the intended DEMO account.
2. Start GoldSwingTraderAI.
3. Let startup validation and broker reconciliation complete.
4. Confirm DEMO guard, controller role and execution readiness.
5. Let the bot analyze/manage automatically.
6. Use governed safe shutdown when stopping it.
```

Normal use should not require editing code or manually tuning scores.

## V1 DEMO guard

Broker writes are enabled only when the connected MT5 account is positively verified as DEMO and every other required authority passes.

Typical dashboard state:

```text
Environment       DEMO ✅ VERIFIED
DEMO Guard        ✅ PASS
Controller        ⚡ PRIMARY
Execution         ✅ ALLOW
```

If DEMO status cannot be verified, the DEMO guard does not pass and broker-write permission is not granted. V1 does not define a separate REAL authorization workflow.

## Main status meanings

- `🟢 ENTER BUY/SELL` — current market/timing/plan/risk/safety/execution path passed;
- `🟡 WAIT` — thesis may remain valid but current entry/timing is not acceptable yet;
- `MISSED` — executable opportunity window passed without justified fill;
- `INVALID` — thesis no longer survives;
- `🔴 BLOCKED` — a hard authority prevents action;
- `📈 OPEN TRADE` — Trade Manager owns the managed position.

Always read the reason code and short explanation rather than interpreting color alone.

## Why no trade?

Examples:

- `ENTRY_EXTENDED` — valid idea, poor current entry;
- `TARGET_ROOM_POOR` — structural reward/path is insufficient;
- `NEWS_BLACKOUT` — scheduled safety window;
- `SESSION_PRE_CLOSE` — scheduled XAU closure is approaching;
- `MIN_LOT_UNAFFORDABLE` — broker minimum volume makes current structural plan too risky;
- `SPREAD_TOO_HIGH` — current execution friction is excessive;
- `PRICE_DRIFT` — price moved too far from approved entry reference;
- `POSITION_CAPACITY_FULL` — bot already has its one V1 Gold risk position;
- `EXTERNAL_GOLD_EXPOSURE` — manual/foreign Gold exposure exists;
- `DATA_STALE` — required market truth is stale/invalid;
- `ANOTHER_ACTIVE_CONTROLLER` — another instance owns broker-write authority.

A non-trade is not automatically a fault.

## Risk profile and daily safety

Initial V1 profiles:

```text
SMALL   $100–$299
MEDIUM  $300–$999
NORMAL  $1,000+
```

The dashboard should show profile, proposed lot, all-in risk, current risk band, hard entry ceiling, daily Account Safety P/L and remaining loss budget.

Daily safety accounting includes floating account drawdown through verified broker equity. Deposits/withdrawals and identifiable non-trading balance changes are adjusted out of trading P/L accounting.

## Daily loss lock and manual reset

When the active daily loss limit is exhausted:

```text
LOSS_LOCKED
→ no new entries/re-entry/add-ons
→ open managed trade still receives safe Trade Manager handling
```

Manual loss reset is **OFF by default**. If deliberately enabled, V1 allows maximum one governed `R,R` reset per UTC risk day from `LOSS_LOCKED`. It does not erase cumulative day losses/history and cannot bypass unrelated risk/data/news/account/execution blocks.

## Loss streak and cooldown

One ordinary losing trade does not trigger a global cooldown.

V1 allows at most one genuinely fresh re-entry in the same Market Episode. If that re-entry also loses, that episode is locked.

Three consecutive closed bot losses trigger at least a 30-minute cooldown. Time alone does not release it; fresh completed M15 context, a fresh valid opportunity and healthy execution state are also required.

## Position capacity

V1 uses Gold position capacity `0/1`.

- one bot-managed independently risk-bearing Gold position maximum;
- opposite opportunity first becomes Trade Manager reversal/exit evidence;
- no automatic hedge/second independent Gold position;
- manual/foreign/unknown-owner Gold exposure is never managed as bot-owned and prevents a fresh bot Gold entry until reconciled clear.

## Targets and large-move behaviour

The bot does **not** use fixed 100/200/300-pip take profits.

It tracks:

- Immediate Obstacle;
- Primary Structural Target;
- Expansion Target;
- Runner Objective.

Primary target is normally a management checkpoint, not an automatic full exit. A valid Expansion Target is normally the initial broker TP. Runner extension must be earned through fresh continuation/acceptance evidence and a new structural/liquidity objective.

V1 remains fully functional with one indivisible `0.01` position; partial profit is not required.

## Open-trade actions

The Trade Manager selects among:

```text
HOLD
PROTECT
TRAIL
RUNNER
EXIT
```

Small opposite candles or a small floating profit do not automatically mean exit. Protection/trailing should follow proven structure and may tighten risk, but must not intentionally widen beyond original approved risk.

## Scheduled market close

V1 intentionally flattens bot-managed Gold before known XAU closure/reopen gap risk.

```text
Daily break:
T-20m no new entry
T-10m mandatory flatten

Weekend:
T-60m no new entry
T-30m mandatory flatten
```

After daily reopen, at least one clean completed M5 plus normalized conditions is required. Weekend reopen requires gap assessment, normalized conditions and at least two clean completed M5 candles.

Runner status does not override mandatory PRE_CLOSE flatten.

## News safety

Initial V1 new-entry windows:

```text
TIER 1 CRITICAL  -15/+15 min
TIER 2 HIGH      -5/+5 min
TIER 3 CONTEXT   no automatic hard blackout
```

Scheduled news alone does not automatically close an existing managed trade. Severe post-news dislocation keeps entry paused until execution conditions normalize and at least one clean completed M5 is available.

## Spread and price drift

The bot evaluates spread dynamically against a healthy broker/symbol baseline. Elevated spread may still be tradable after full revalidation; clearly excessive spread prevents the current entry.

Price movement away from the approved entry reference is also normalized by the planned structural stop distance. Large adverse drift prevents the current intent rather than chasing the market.

## Runtime roles

- `PRIMARY` — the only instance with current governed broker-write authority;
- `STANDBY` — may take over only after valid lease expiry and full reconciliation;
- `OBSERVER` — analysis/dashboard, no broker writes;
- `RESEARCH` — replay/experiments, no production broker writes;
- `RECOVERING/RECONCILING` — ownership may exist but broker writes are not ready yet.

A second laptop must not independently execute while another valid PRIMARY exists.

## System Health

Normal states such as `WAIT`, `NEWS_BLACKOUT` or `LOSS_LOCKED` are not automatically technical faults.

System Health should separately report operational issues such as stale data, account mismatch, unresolved broker acknowledgement, controller coordination failure, state corruption, provider failure or backup/restore problems.

## Learning and research

Learning measures taken, missed, blocked/rejected and invalidated opportunities plus MFE/MAE, entry quality, realized R and move-capture efficiency.

StrategyMemory and autonomous candidates cannot immediately rewrite production after a few trades. Candidate changes move through governed research/validation/promotion stages and cannot bypass risk/execution authority.

## Backups and laptop change

Source, docs, strategies, learning/research state and recovery intelligence may be backed up publicly according to project policy. Financial-authority credentials/keys/tokens must remain outside public backups.

After restore on another laptop, the bot must validate state, acquire controller ownership and reconcile current MT5 positions/orders/deals before new entries.

## Do not manually edit critical state

Do not delete/edit order lifecycle, risk state, Strategy Registry, promotion history or critical trade state merely to clear an error. Use governed recovery/reset workflows once implemented.

## Project status caveat

This manual remains DRAFT until actual commands, launcher names, keyboard timing, screenshots and implemented dashboard behaviour exist and are verified.
