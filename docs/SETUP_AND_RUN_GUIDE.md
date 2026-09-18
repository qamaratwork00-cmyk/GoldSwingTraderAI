# GoldSwingTraderAI — Setup and Run Guide

**Status:** DRAFT — PHASE 1/2 COMMANDS IMPLEMENTED; TRADING WORKFLOW NOT YET IMPLEMENTED  
**Version:** 0.5-implementation  
**Authority:** Operator workflow for installation, startup, safe shutdown, migration, restore and common blocked-state handling.  
**Depends on:** `50-operator/DASHBOARD_AND_UX.md`, `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`, `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md`

## Purpose

This guide records real commands as they become implemented. Current commands cover package setup and **read-only MT5 Phase 2 readiness**. They do not yet start automated trading because the governed broker-write phase has not been implemented.

## Current prerequisites

For the Windows MT5 read path:

- Windows machine with MetaTrader 5 installed and open;
- intended MT5 account already connected in the terminal;
- Python **3.11+**;
- repository checkout/clone;
- network access required by the terminal/broker.

The official `MetaTrader5` Python package is optional in CI but required for local terminal reads.

## First-time development setup

From the repository root on Windows PowerShell/cmd:

```text
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,mt5]"
copy .env.example .env
```

For deterministic development/CI on a machine without MT5 terminal support:

```text
python -m pip install -e ".[dev]"
pytest
python scripts/scan_financial_secrets.py .
```

Do not place MT5 passwords, authentication/session tokens or other financial-authority secrets in the repository.

## Current `.env` fields

The safe example currently exposes only non-secret configuration:

```text
GSTAI_ENV=development
GSTAI_PREFERRED_SYMBOL=XAUUSDm
GSTAI_SYMBOL_ALIASES=XAUUSDm,XAUUSD
GSTAI_MANUAL_RESET_ENABLED=false
GSTAI_STATE_DIR=.state
GSTAI_LOG_LEVEL=INFO
GSTAI_ALLOWED_ACCOUNT_LOGIN=
GSTAI_ALLOWED_SERVER=
```

`GSTAI_ALLOWED_ACCOUNT_LOGIN` and `GSTAI_ALLOWED_SERVER` are optional identity pins. If supplied, the current read-only readiness path reports a mismatch explicitly.

### DEMO guard is not a config switch

There is deliberately no `GSTAI_REQUIRE_DEMO` setting.

V1 owns this as a runtime invariant:

```text
Connected MT5 account positively verified DEMO
→ DEMO_GUARD PASS
```

A local config value cannot disable that rule.

## Current Phase 2 run command

With MT5 open and the local environment activated:

```text
python -m goldswingtraderai
```

Equivalent installed console command:

```text
goldswing
```

Current runtime behaviour is **read-only**:

```text
load/validate non-secret settings
→ initialize MT5 Python bridge
→ read connected account facts
→ resolve configured Gold symbol (default XAUUSDm → XAUUSD fallback)
→ read broker symbol specifications
→ read Bid/Ask
→ load completed H4/H1/M15/M5 candles
→ build one normalized market snapshot
→ evaluate positive DEMO fact
→ check optional account identity pins
→ log concise readiness/data-quality result
→ shutdown MT5 Python bridge
```

No `order_send`, create, modify or close path is implemented at this stage.

## Current default history windows

```text
H4    400 completed candles
H1    750 completed candles
M15  2000 completed candles
M5   4000 completed candles
```

MT5 bar position `0` is the forming candle. The current reader intentionally starts completed history at position `1`.

## Current readiness outcomes

Useful current log events include:

```text
PHASE_2_READINESS_START
MARKET_SNAPSHOT_READY
ACCOUNT_IDENTITY_MISMATCH
DEMO_GUARD_NOT_VERIFIED
MARKET_DATA_DEGRADED
MT5_UNAVAILABLE
MT5_NOT_INITIALIZED
SYMBOL_NOT_FOUND
DATA_UNAVAILABLE
DATA_INSUFFICIENT
DATA_STALE
DATA_SPARSE
DATA_CORRUPT
```

A degraded snapshot can still be displayed/read, but it must not later become broker-write permission merely because the process is running.

## V1 environment rule

V1 uses a positive DEMO guard only:

```text
Connected MT5 account verified DEMO
→ DEMO_GUARD PASS
```

When the execution phase exists, broker writes will require this guard plus all ordinary account/data/session/news/risk/controller/execution checks.

V1 does not define a separate REAL authorization workflow.

## Planned full startup

The final trading startup remains:

```text
load + validate durable state
→ connect MT5
→ verify account/server/DEMO status
→ resolve Gold symbol/specs
→ load/validate H4/H1/M15/M5 history
→ reconcile positions/orders/deals
→ restore risk/open-trade/opportunity state
→ load Strategy Registry + learning
→ verify news/session inputs
→ acquire controller lease/epoch
→ rebuild/revalidate market intelligence
→ evaluate centralized Execution Permission Gate
→ READY
```

Only the early read-only subset above exists today.

## Runtime roles — planned

### PRIMARY

Single instance with governed broker-write authority for the managed account/symbol.

### STANDBY

May analyze and wait for controller lease expiry. It cannot write while another valid PRIMARY exists. After takeover it must reconcile before becoming PRIMARY READY.

### OBSERVER

Analysis/dashboard only; no broker writes.

### RESEARCH

Historical/replay/experimental use; no production broker writes.

### RECOVERING / RECONCILING

Runtime is restoring/reconciling state and is not yet broker-write ready.

## What to do on WAIT — future trading runtime

Normally nothing.

Example:

```text
ENTRY_EXTENDED
Setup remains ARMED
```

Do not restart or alter settings simply because the bot is waiting for better timing.

## Expected policy blocks — future trading runtime

Examples:

- `NEWS_BLACKOUT` — wait for event safety/normalization;
- `SESSION_PRE_CLOSE` — scheduled XAU closure approaching;
- `LOSS_LOCKED` — daily safety budget exhausted;
- `POSITION_CAPACITY_FULL` — one bot-managed Gold risk position already exists;
- `EXTERNAL_GOLD_EXPOSURE` — manual/foreign/unknown Gold exposure exists;
- `SPREAD_TOO_HIGH` / `PRICE_DRIFT` — current entry execution degraded;
- `ANOTHER_ACTIVE_CONTROLLER` — another instance owns the controller lease;
- `DEMO_GUARD_NOT_VERIFIED` — positive DEMO verification is unavailable.

Do not bypass the centralized Execution Permission Gate when it is implemented.

## System blocks

`ACCOUNT_IDENTITY_MISMATCH`, unresolved broker acknowledgement, state corruption, controller coordination failure or required data/news truth failure require reconciliation/recovery rather than manual trade forcing.

Manual loss reset cannot clear unrelated technical/system blocks.

## Manual daily-loss reset — planned operator control

The feature is OFF by default.

When its UX is implemented, reset is available only from `LOSS_LOCKED`, requires deliberate `R,R` confirmation, is limited to one per UTC risk day and creates a durable audit event/new cycle reference without erasing cumulative day P/L.

Exact keyboard timing remains an operator-UX implementation detail.

## Scheduled closure behaviour — frozen, not yet runtime-implemented

V1 does not intentionally carry bot-managed Gold through scheduled XAU closure/reopen gap risk.

```text
Daily break:
T-20m stop new entries
T-10m mandatory governed flatten

Weekend:
T-60m stop new entries
T-30m mandatory governed flatten
```

Timing comes from the verified broker Gold session schedule rather than a hard-coded local clock.

After reopen:

```text
Daily   → normalized conditions + at least 1 clean completed M5
Weekend → gap assessment + normalized conditions + at least 2 clean completed M5
```

## Current safe shutdown

The Phase 2 command reads one snapshot and exits; the MT5 Python bridge is shut down in a `finally` path.

The future persistent trading runtime will use the fuller shutdown sequence:

```text
stop new entry triggering
→ reconcile any in-flight broker write
→ persist risk/order/trade/opportunity/learning state
→ create/verify checkpoint as configured
→ release controller lease safely
→ exit
```

## Planned laptop migration

```text
OLD PRIMARY
stop new intents
→ reconcile in-flight writes
→ safe shutdown
→ verify recovery checkpoint/backup
→ release controller lease

NEW MACHINE
clone/install project
→ configure financial credentials separately
→ restore portable state
→ validate schema/integrity
→ connect intended MT5 DEMO account
→ acquire new controller epoch
→ broker reconciliation
→ rebuild market intelligence
→ validate risk/news/session state
→ startup self-checks
→ PRIMARY READY
```

## Disaster recovery after laptop loss

Recovery requires repository + portable recovery state/checkpoint + separately supplied financial credentials + intended MT5 access.

Never replay a stale backup assumption that a position is open or closed without checking broker truth.

## Public backup / secret rule

Public backup may contain code, docs, strategies, learned parameters, research/promotion history and portable recovery intelligence.

Never commit authority-bearing credentials/keys/tokens such as MT5 trading secrets, private broker/session tokens, paid API keys, GitHub PATs, private/signing keys or paid cloud/database credentials.

Run:

```text
python scripts/scan_financial_secrets.py .
```

If a financial credential was committed publicly, rotate/revoke it; deletion alone is insufficient.

## Verification status

Current deterministic repository checks include Ruff, Pytest and the financial-secret scanner through GitHub Actions.

**Actual connected MT5 DEMO read verification remains pending on the intended Windows terminal.** Do not interpret passing fake-adapter CI as proof that a specific local broker terminal is configured correctly.

This guide will continue to gain exact persistence/controller/trading/dashboard commands only after those features actually exist.
