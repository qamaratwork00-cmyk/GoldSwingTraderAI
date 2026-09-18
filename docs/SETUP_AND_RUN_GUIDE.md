# GoldSwingTraderAI — Setup and Run Guide

**Status:** DRAFT — CORE MODULES IMPLEMENTED; INTEGRATED PERSISTENT TRADING RUNTIME PENDING  
**Version:** 0.6-implementation  
**Authority:** Operator workflow for installation, startup, safe shutdown, migration, restore and common blocked-state handling.  
**Depends on:** `50-operator/DASHBOARD_AND_UX.md`, `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`, `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md`

## Purpose

This guide records real commands and current runtime reality.

Important distinction:

- deterministic production modules now exist through the current Phase-10 foundation, including strategy/risk/execution/management/research components;
- the current `goldswing` / `python -m goldswingtraderai` launcher still runs the **read-only MT5 readiness path**;
- the launcher has not yet been replaced by the final persistent full-trading orchestrator;
- controlled Windows/MT5 DEMO execution certification remains pending.

Do not infer that a module is missing merely because the current launcher does not yet orchestrate it, and do not infer live trading readiness merely because component tests are green.

## Prerequisites

For the Windows MT5 read path:

- Windows machine with MetaTrader 5 installed and open;
- intended MT5 account already connected in the terminal;
- Python **3.11+**;
- repository checkout/clone;
- network access required by terminal/broker.

The official `MetaTrader5` Python package is optional in CI but required for local terminal integration.

## First-time development setup

From repository root on Windows PowerShell/cmd:

```text
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,mt5]"
copy .env.example .env
```

For deterministic development/CI without MT5 terminal support:

```text
python -m pip install -e ".[dev]"
pytest
python scripts/scan_financial_secrets.py .
```

Do not place MT5 passwords, authentication/session tokens or other financial-authority secrets in the repository.

## Current `.env` fields

The safe example currently exposes non-secret configuration such as:

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

`GSTAI_ALLOWED_ACCOUNT_LOGIN` and `GSTAI_ALLOWED_SERVER` are optional identity pins.

### DEMO guard is not a config switch

There is deliberately no setting that disables DEMO verification.

```text
Connected MT5 account positively verified DEMO
→ DEMO_GUARD PASS
```

V1 does not define a separate REAL authorization workflow.

## Current launcher command

With MT5 open and environment activated:

```text
python -m goldswingtraderai
```

Equivalent console command:

```text
goldswing
```

### Current launcher behaviour

The launcher currently performs **read-only readiness**:

```text
load/validate non-secret settings
→ initialize MT5 Python bridge
→ read connected account facts
→ resolve configured Gold symbol
→ read broker symbol specifications
→ read Bid/Ask
→ load completed H4/H1/M15/M5 candles
→ build normalized MarketSnapshot
→ evaluate positive DEMO fact
→ check optional account identity pins
→ log readiness/data quality
→ shutdown MT5 bridge
```

The current `app/main.py` intentionally reports `broker_write_implemented=False` because the launcher itself does not yet call the integrated execution runtime.

This does **not** mean execution modules are absent. The repository already contains deterministic implementations for execution intent/gate/checks/controller/MT5 writer/service/reconciliation, but they are not yet wired into the normal persistent launcher.

## Current default history windows

```text
H4    400 completed candles
H1    750 completed candles
M15  2000 completed candles
M5   4000 completed candles
```

MT5 bar position `0` is the forming candle. Completed history starts at position `1`.

## Current deterministic subsystem checkpoint

Implemented/tested component families include:

```text
market_data/
intelligence/        # structure, quant, technical, liquidity, session/news, confluence
strategies/
decisions/
risk/
persistence/
execution/
management/
operator/
research/
```

Notable current behaviour:

- causal Trendline/Fibonacci/broker-local POC confluence exists as optional bonus-only intelligence;
- SMALL is any positive UTC day-start equity below `$300`; no `$100` floor;
- one-shot Execution Intent and reconciliation logic exist;
- SQLite persistence/recovery exists;
- HOLD/PROTECT/TRAIL/RUNNER/EXIT Trade Manager exists;
- discovery/invention has durable liveness/candidate/promotion machinery.

These deterministic modules still require final runtime orchestration and controlled broker integration evidence.

## Intended full startup after orchestration is complete

```text
load + validate durable state
→ connect MT5
→ verify account/server/DEMO status
→ resolve Gold symbol/specs
→ load/validate H4/H1/M15/M5 history
→ reconcile positions/orders/deals
→ restore risk/open-trade/opportunity state
→ load Strategy Registry + learning/research state
→ verify news/session inputs
→ acquire controller lease/epoch
→ rebuild/revalidate market intelligence
→ run strategies/fusion/timing/TradePlan/risk
→ evaluate centralized Execution Permission Gate
→ READY
```

## Runtime roles

### PRIMARY
Single instance with governed broker-write authority for managed account/symbol.

### STANDBY
May wait for valid lease expiry, then must reconcile before becoming PRIMARY READY.

### OBSERVER
Analysis/dashboard only; no broker writes.

### RESEARCH
Replay/experiments; no production broker writes.

### RECOVERING / RECONCILING
Runtime is restoring/reconciling state and is not yet broker-write ready.

## Expected trading states

`WAIT` normally requires no operator action. A valid setup may remain armed while timing improves.

Expected policy blocks include:

- `NEWS_BLACKOUT`;
- `SESSION_PRE_CLOSE`;
- `LOSS_LOCKED`;
- `POSITION_CAPACITY_FULL`;
- `EXTERNAL_GOLD_EXPOSURE`;
- `SPREAD_TOO_HIGH` / `PRICE_DRIFT`;
- `ANOTHER_ACTIVE_CONTROLLER`;
- `DEMO_GUARD_NOT_VERIFIED`.

System failures such as account mismatch, unresolved broker acknowledgement, corrupt state, controller coordination failure or required-data/news truth failure require recovery/reconciliation rather than forced trading.

## Optional confluence visibility

Future integrated runtime/dashboard may show compact lines such as:

```text
Trendline   M15 support TOUCH
Fib         BUY 0.618
POC         NEAR (tick-volume)
```

These are analytical context only. Missing Trendline/Fibonacci/POC is not itself a reason to block a trade.

## Manual daily-loss reset

Feature is OFF by default.

When operator UX is fully wired, reset is available only from `LOSS_LOCKED`, requires deliberate `R,R` confirmation, is limited to one per UTC risk day, and creates durable audit/new-cycle state without erasing cumulative day P/L.

Exact keyboard timing remains an operator-detail item.

## Scheduled closure behaviour

```text
Daily break:
T-20m stop new entries
T-10m mandatory governed flatten

Weekend:
T-60m stop new entries
T-30m mandatory governed flatten
```

Timing comes from verified broker Gold session schedule rather than guessed local clock.

After reopen:

```text
Daily   → normalized conditions + at least 1 clean completed M5
Weekend → gap assessment + normalized conditions + at least 2 clean completed M5
```

Hard permission logic is implemented deterministically; live schedule/provider wiring and controlled DEMO evidence remain integration work.

## Safe shutdown target

Current read-only launcher exits after one readiness snapshot and shuts down MT5 bridge in `finally`.

Final persistent runtime should use:

```text
stop new entry triggering
→ reconcile any in-flight broker write
→ persist risk/order/trade/opportunity/learning state
→ create/verify checkpoint as configured
→ release controller lease safely
→ exit
```

## Laptop migration target

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

Production shared cross-laptop coordination backend and fresh-machine drill remain pending release work.

## Disaster recovery

Recovery requires repository + portable recovery state/checkpoint + separately supplied financial credentials + intended MT5 access.

Never replay a stale backup assumption about open/closed positions without checking broker truth.

## Public backup / secret rule

Public backup may contain code, docs, strategies, learned parameters, research/promotion history and portable recovery intelligence.

Never commit authority-bearing credentials/keys/tokens such as MT5 secrets, private broker/session tokens, paid API keys, GitHub PATs, private/signing keys or paid cloud/database credentials.

Run:

```text
python scripts/scan_financial_secrets.py .
```

If a financial credential was committed publicly, rotate/revoke it; deletion alone is insufficient.

## Verification status

Repository CI runs Ruff, Pytest and financial-secret scan.

Current deterministic green status is software evidence only. The following remain pending before honest DEMO verification:

- fully integrated persistent runtime;
- real Windows/MT5 read/write lifecycle evidence;
- production shared cross-laptop coordination backend/failover evidence;
- backup/export/fresh-machine recovery drill;
- full end-to-end controlled DEMO certification.
