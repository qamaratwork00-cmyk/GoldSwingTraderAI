# GoldSwingTraderAI — System Contract

**Status:** PROVISIONAL
**Version:** 0.1-foundation
**Authority:** Highest-level behavioural and safety contract

## Purpose

This is the constitution of GoldSwingTraderAI. Every module, runtime mode,
dashboard, research path and recovery workflow must preserve these rules.
Detailed topic documents may add implementation detail, but they may not
silently contradict this contract.

## The complete contract

~~~mermaid
flowchart TB
    BROKER["Verified broker and market facts"] --> INTEL["Independent bounded intelligence"]
    INTEL --> THESIS["BUY and SELL theses"]
    THESIS --> TIMING["Opportunity and M5 timing"]
    TIMING --> PLAN["Structural Trade Plan"]
    PLAN --> HARD["Risk, session/news, identity, position and controller"]
    HARD --> GATE["Central Execution Permission Gate"]
    GATE --> INTENT["Durable one-shot Intent"]
    INTENT --> WRITE["One MT5 write"]
    WRITE --> TRUTH["Broker verification and reconciliation"]
    TRUTH --> STATE["Durable lifecycle, dashboard and research evidence"]
~~~

The system is allowed to say “not now” at many points. It is not allowed to
skip an authority boundary or turn unknown financial truth into a passing
default.

## Non-negotiable invariants

### Facts and chronology

- MT5 account, symbol, quote, completed candles and open-position facts come
  through one normalized read boundary.
- H4/H1/M15/M5 structural work uses completed candles.
- Swing pivot time and confirmation time are different.
- A replay prefix cannot see a future-confirmed swing, break or outcome.
- One cycle shares one immutable market/intelligence snapshot.
- Fresh broker reads remain mandatory immediately before operations that require
  current truth.

### Analysis and decisions

- intelligence desks describe evidence; they do not grant broker permission;
- strategy families evaluate independently from the same snapshot;
- BUY and SELL theses are built independently;
- conflict remains visible;
- Opportunity and Entry Timing are separate;
- one strong family may lead;
- missing optional evidence is not automatically negative evidence;
- Trendline/Fibonacci/POC are bonus/context only in V1;
- a Trade Plan exists before monetary sizing;
- original R is immutable.

### Hard safety

- risk is independent from the strategy score;
- unknown account, exposure, required session/news, persistence or controller
  truth fails closed for new broker writes;
- V1 allows one independently risk-bearing Gold position;
- manual/foreign/unknown Gold exposure is never treated as bot-owned;
- V1 has a positive DEMO Guard, not a hidden REAL override;
- all create/modify/close actions use one central gate and one writer path;
- an Intent ID may send at most once;
- ambiguous acknowledgement triggers reconciliation, never blind retry;
- one PRIMARY controller owns a managed account/symbol;
- a new fencing epoch is not readiness until recovery reconciles truth.

### Runtime and recovery

- READINESS is read-only;
- stale/insufficient/sparse market data may keep the process alive but never
  grants strategy or broker permission;
- corrupt, identity, DEMO, persistence, controller and unknown required
  session/news failures remain fail-closed;
- restore loads context; MT5 remains current exposure truth;
- restart never silently erases risk, intent, managed-trade, opportunity or
  research lifecycle state;
- shutdown stops new work, reconciles in-flight actions, persists state and
  releases ownership safely.

### Improvement

- research reuses documented chronology and labels actual/counterfactual
  outcomes separately;
- learning may observe and make bounded recommendations;
- discovery/invention creates declarative candidates only;
- candidates cannot generate arbitrary executable code, modify hard safety or
  self-promote;
- promotion requires evidence stages, an untouched holdout and explicit
  approval.

## V1 monetary policy

The risk contract owns the detailed formula, but the system-wide profiles are:

| Profile | Positive day-start equity | Normal band | Elevated band | Entry ceiling | Daily lock |
|---|---:|---:|---:|---:|---:|
| SMALL | below 300 | 3.0–4.5% | above 4.5–6.5% | 7% | 12% |
| MEDIUM | 300–999.99 | 2.0–3.0% | above 3.0–4.5% | 5% | 9% |
| NORMAL | 1,000 or more | 1.0–2.0% | above 2.0–3.5% | 4% | 7% |

Any positive day-start equity below 300 is SMALL. There is no 100-dollar
eligibility floor. Broker minimum volume, structural stop geometry and actual
all-in risk decide whether a particular plan is affordable.

## V1 session/news policy

The broker schedule owns market-open truth:

~~~text
Daily:   T-20m no new entry, T-10m mandatory governed flatten
Weekend: T-60m no new entry, T-30m mandatory governed flatten
~~~

Reopen requires normalized conditions and clean completed M5 candles:

~~~text
Daily   → at least 1 clean M5
Weekend → gap assessment plus at least 2 clean M5
~~~

Scheduled news policy:

~~~text
Tier 1 critical: -15/+15 minutes
Tier 2 high:     -5/+5 minutes
Tier 3 context:  no automatic hard blackout
~~~

Scheduled news alone does not automatically close an open trade. Required news
truth that is stale or unavailable becomes NEWS_SAFETY_UNKNOWN.

## V1 lifecycle outputs

Analytical outputs:

~~~text
ENTER BUY | ENTER SELL | WAIT | MISSED | INVALID
~~~

Hard/runtime outputs:

~~~text
PASS | BLOCK | UNKNOWN | ALLOW | RECONCILING | READY
~~~

Management outputs:

~~~text
HOLD | PROTECT | TRAIL | RUNNER | EXIT
~~~

Health outputs:

~~~text
OK | WARN | DEGRADED | BLOCKED | ERROR
~~~

These vocabularies are not interchangeable. A normal NEWS_BLACKOUT is not a
system crash; a corrupt Execution Intent is not an analytical WAIT.

## Authority ownership

| Responsibility | Owner |
|---|---|
| raw broker facts | market_data/mt5_reader.py |
| normalized cycle snapshot | market_data/snapshot.py and intelligence/snapshot.py |
| market evidence | intelligence/ |
| family hypotheses | strategies/ |
| fusion/timing/Trade Plan | decisions/ |
| monetary risk | risk/engine.py and risk/state.py |
| session/news permission | risk/permissions.py |
| raw write | execution/mt5_writer.py |
| write permission/intent/controller/reconciliation | execution/ |
| open-trade decision | management/ |
| durable records/checkpoints/backups | persistence/ |
| startup composition and recovery orchestration | app/ |
| presentation | app/dashboard.py and operator/ |
| offline evidence and promotion | research/ and scripts/ |

## Contract conflict rule

If a change appears to require two owners, stop and resolve the ownership in
90-governance/DESIGN_DECISIONS.md before coding. The solution is not to copy a
rule into a second module or dashboard.

## Verification boundary

This contract is checked through deterministic unit/integration tests and the
release audit. It is not itself proof that the intended Windows terminal,
provider, shared coordination storage or broker lifecycle has been exercised.

