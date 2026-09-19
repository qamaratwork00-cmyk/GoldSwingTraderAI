# GoldSwingTraderAI — Setup and Run Guide

**Status:** CANDIDATE FOR ADOPTION
**Version:** 0.1-operator-setup
**Authority:** Installation, runtime modes, shutdown, restore and operator commands

## Purpose

This guide takes an operator from a clean Windows machine to a safe readiness
run and explains when the full persistent runtime may be attempted.

## Prerequisites

- Windows with MetaTrader 5 installed and open;
- intended DEMO account connected in MT5;
- Python 3.11 or newer;
- repository checkout;
- network access required by the terminal/broker;
- credentials configured in MT5 or secure external configuration, never in Git.

## Install

~~~text
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,mt5]"
copy .env.example .env
~~~

CI/read-only development may use:

~~~text
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/scan_financial_secrets.py .
~~~

## Safe configuration

~~~text
GSTAI_ENV=development
GSTAI_PREFERRED_SYMBOL=XAUUSDm
GSTAI_SYMBOL_ALIASES=XAUUSDm,XAUUSD
GSTAI_RUNTIME_MODE=READINESS
GSTAI_READINESS_KEEP_ALIVE=true
GSTAI_READINESS_POLL_SECONDS=30
GSTAI_STATE_DIR=.state
GSTAI_STATE_MODE=EXISTING
GSTAI_RESTORE_CHECKPOINT=
GSTAI_ALLOWED_ACCOUNT_LOGIN=
GSTAI_ALLOWED_SERVER=
GSTAI_MT5_MAGIC=
GSTAI_MT5_DEVIATION_POINTS=
GSTAI_MT5_COMMENT_PREFIX=GSTAI
GSTAI_HEALTHY_SPREAD_BASELINE=
GSTAI_SESSION_NEWS_FILE=
GSTAI_SESSION_NEWS_TTL_SECONDS=1800
~~~

DEMO verification is not a configuration switch. Empty identity pins mean
“do not pin this field,” not “ignore mismatches.” Primary/standby modes require
non-secret magic/deviation configuration and a valid state mode.

## Runtime modes

~~~mermaid
flowchart TB
    MODE["GSTAI_RUNTIME_MODE"] --> READINESS["READINESS — read-only monitor"]
    MODE --> PRIMARY["PRIMARY — recover, acquire controller, run"]
    MODE --> STANDBY["STANDBY — wait/take over only after recovery"]
    PRIMARY --> LOOP["Persistent M5 loop"]
    STANDBY --> LOOP
    LOOP --> STOP["Safe shutdown"]
~~~

Start safe readiness:

~~~text
python -m goldswingtraderai
~~~

Equivalent installed command:

~~~text
goldswing
~~~

READINESS:

~~~text
load settings
→ initialize MT5Reader
→ read account/symbol/DEMO/quote/history
→ build MarketSnapshot
→ render readiness frame
→ keep polling stale/insufficient/sparse data if enabled
→ exit on healthy/non-retryable result or Ctrl+C
~~~

No strategy, risk sizing, Intent or broker write runs in READINESS.

PRIMARY/STANDBY:

~~~text
initialize MT5 and recovery truth
→ select EXISTING/INITIALIZE/RESTORE local state
→ build repositories/reconciler/controller
→ load session/news observation
→ StartupRecoveryCoordinator
→ READY or RECONCILING/BLOCKED
→ persistent M5 cycle, 10s heartbeat and backup cadence
~~~

Missing session/news truth is UNKNOWN and prevents READY. Only stale,
insufficient and sparse market quality are retryable pre-READY states.

## Closed market

The process may remain alive while quotes/candles are stale. The readiness
screen shows exact quality and counts, STRATEGY NOT RUN and BROKER WRITES
DISABLED. It does not guess that every stale feed is a calendar closure.

## State modes

~~~text
EXISTING   → use current local DB; missing critical state blocks
INITIALIZE → create first risk-day baseline only in empty store
RESTORE    → verify checkpoint and restore to a new DB
~~~

RESTORE never overwrites runtime.db and never grants trading authority.

## Session/news file

Use the schema in SESSION_NEWS_PROVIDER_CONTRACT.md. The producer must publish
an atomic account/server/symbol-scoped snapshot. Missing, malformed, stale or
future-dated data remains UNKNOWN.

## Safe shutdown

~~~text
stop new triggers
→ finish or reconcile in-flight write
→ persist risk/order/trade/opportunity/research state
→ verify backup/checkpoint if configured
→ release controller
→ shut down MT5
~~~

Do not delete the state directory to clear a runtime error.

## Restore and migration

~~~text
python scripts/restore_runtime_checkpoint.py <checkpoint> <new-db>
~~~

Then configure the intended DEMO terminal and let startup reconcile current
positions/orders/deals. A second laptop must not run PRIMARY while a valid
PRIMARY lease exists.

## Research commands

Dataset acquisition and fixed-policy walk-forward commands are documented in
RESEARCH_AND_VALIDATION.md. They do not send broker orders.

## Source and tests

Main owners are config/settings.py, app/main.py, app/runtime.py, app/startup.py,
app/recovery.py, app/loop.py and persistence/. Tests:
test_settings.py, test_app_readiness.py, test_live_startup_runtime.py,
test_runtime_loop.py, test_startup_recovery.py and test_operator_scripts.py.

## Live evidence warning

Green tests do not certify the connected terminal, provider, broker write
lifecycle, restart, failover or profitability. Record those in the final audit.

