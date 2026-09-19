# GoldSwingTraderAI — Monetary Risk Contract

**Status:** PROVISIONAL
**Version:** 0.1-risk
**Authority:** Account profiles, executable risk, exposure, daily loss and cooldown

## Purpose

Risk answers one question after a Trade Plan exists: can this account afford
this exact structural plan at an executable broker volume?

Risk does not decide direction, move the structural stop, or send a request.

## Evaluation pipeline

~~~mermaid
flowchart TB
    PLAN["TradePlan — structural SL and original R"] --> CONTEXT["RiskContext — equity, quote, SymbolSpec and exposure"]
    CONTEXT --> PROFILE["Fixed UTC-day profile"]
    PLAN --> SIZE["Raw volume → broker step/minimum → actual all-in risk"]
    PROFILE --> SIZE
    CONTEXT --> SIZE
    SIZE --> STATE["Daily P/L, lock, cooldown and episode re-entry"]
    STATE --> RESULT["PASS / BLOCK / UNKNOWN"]
    RESULT --> GATE["Central Execution Gate"]
~~~

## Account profiles

| Profile | DayStartEquity | Normal risk | Elevated risk | Entry ceiling | Daily lock |
|---|---:|---:|---:|---:|---:|
| SMALL | positive and below 300 | 3.0–4.5% | above 4.5–6.5% | 7% | 12% |
| MEDIUM | 300–999.99 | 2.0–3.0% | above 3.0–4.5% | 5% | 9% |
| NORMAL | 1,000 or more | 1.0–2.0% | above 2.0–3.5% | 4% | 7% |

Profile is fixed from positive DayStartEquity for the UTC risk day. Intraday
floating P/L must not switch the profile. A positive 30, 50 or 99 account is
SMALL, not automatically ineligible.

## Executable all-in risk

The calculation uses broker tick size/value, contract size, account currency,
entry side, structural stop distance, min/max/step volume, spread and declared
slippage/fee treatment. Spread must be converted correctly and counted exactly
once; Ask/Bid geometry may already include it.

~~~text
structural plan
→ target profile band
→ raw volume
→ broker-normalized volume
→ actual all-in monetary risk
→ ceiling/margin/exposure/daily-state checks
~~~

If raw lot is below the broker minimum, evaluate the minimum lot. Only actual
all-in risk above the hard ceiling becomes MIN_LOT_UNAFFORDABLE. The stop is
never tightened to fit.

Generic margin is diagnostic. Exact broker margin, when available from the
execution boundary, is authoritative.

## Exposure and capacity

V1 capacity is 0/1 independently risk-bearing Gold position. A manual, foreign
or unknown-owner Gold position blocks a new bot entry and is never managed as
bot-owned. This is not a daily trade quota; analysis and research continue.

## Daily safety P/L

The risk day begins at 00:00 UTC:

~~~text
AccountSafetyPL
= CurrentVerifiedEquity
- DayStartEquity
- NetNonTradingCashFlowSinceDayStart
~~~

Broker equity already contains trading P/L and applicable charges. Deposits,
withdrawals and identifiable non-trading credits/debits are removed so they
are not called trading loss. Floating loss counts immediately.

Bot Performance P/L is tracked separately from account safety.

At the profile lock:

~~~text
LOSS_LOCKED
→ no new entries, add-ons or re-entry
→ open trade continues safe management
~~~

Unknown equity/cash-flow truth fails closed.

## Manual reset

Manual reset is OFF by default. If explicitly enabled:

- only LOSS_LOCKED can reset;
- maximum one governed R,R confirmation per UTC day;
- a new cycle reference uses current verified state;
- cumulative day P/L and history remain visible;
- unrelated news/account/execution/reconciliation blocks remain;
- reset state survives restart.

## Cooldown and episode re-entry

- one ordinary loss does not create global cooldown;
- one genuinely fresh same-episode re-entry is allowed;
- a second loss in that episode locks it;
- three consecutive closed bot losses create at least 30 minutes cooldown;
- release also needs fresh completed M15 context, a fresh valid opportunity and
  no unresolved execution fault;
- abnormal feed/execution shocks may impose condition-based cooldown.

There is no fixed daily trade count.

## Outputs and dashboard

RiskEvaluation should expose profile, target band, normalized volume, actual
all-in risk, ceiling, margin result, DayStartEquity, AccountSafetyPL, lock,
reset count, loss streak, cooldown and capacity. The dashboard displays these
facts without recalculating them.

## Implementation and tests

| Source | Role | Tests |
|---|---|---|
| risk/engine.py | plan affordability and volume | test_trade_plan_risk.py, test_small_account_profile.py, test_margin_authority.py |
| risk/state.py | day, lock, reset, cooldown and episode state | test_risk_state_regressions.py |
| execution/checks.py | fresh broker-relative checks | test_execution_safety.py |
| persistence/runtime_state.py | durable risk state | test_persistence_recovery.py |

## Prohibited behaviour

No martingale, score-leveraged risk, arbitrary positive-account floor, unknown
exposure as zero, double-counted friction, foreign P/L contamination, second
independent Gold position, unlimited re-entry or original-R rewrite.

