# GoldSwingTraderAI — Fundamental and News Intelligence

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Macro/fundamental Gold context, scheduled-event facts, provider freshness and holiday context.  
**Depends on:** `MARKET_DATA_AND_HISTORY.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

This document defines market-intelligence facts and opinions related to Gold fundamentals and scheduled news. It intentionally separates **macro opinion** from **hard trading permission**.

> **Macro/fundamental opinion is soft evidence. Event-risk permission is enforced by the risk/session safety layer.**

## Fundamental context

Potential inputs include:

- USD/DXY behaviour;
- US Treasury yields;
- rate expectations;
- Fed policy context;
- inflation/labour data context;
- risk sentiment;
- geopolitical stress where a reliable source exists.

The desk may produce BUY and SELL fundamental support with confidence/freshness. Price/structure remains primary trading evidence.

## Scheduled-event facts

The desk may ingest provider-backed facts for events such as:

- FOMC/rate decisions;
- Powell/Fed communications;
- CPI/Core CPI;
- NFP and major labour releases;
- PCE;
- GDP and other validated high-impact USD events.

Exact event tiers and provider mappings remain open.

For each event, publish at least:

- event identity;
- relevant currency/market;
- scheduled time;
- impact/severity metadata;
- provider timestamp/freshness;
- source health.

This document does not decide the final blackout window; `../30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` owns hard permission semantics.

## Event tiers

A provisional conceptual hierarchy may be used:

```text
TIER 1 — critical Gold/USD shock events
TIER 2 — high impact
TIER 3 — contextual/ordinary
```

Exact classification and entry-blackout windows require validation/freeze.

## Provider health

The desk must distinguish at least:

```text
VERIFIED
DEGRADED
STALE
UNAVAILABLE
UNKNOWN
```

Example:

- macro-opinion feed unavailable but scheduled-event feed healthy → macro evidence UNKNOWN/DEGRADED; event facts remain usable;
- required event-calendar truth unavailable → event-safety layer may fail closed.

The system must never silently assume `no news` because a provider failed.

## Fundamental evidence

Suggested directional outputs:

- Fundamental BUY Support;
- Fundamental SELL Support;
- USD context;
- yield/rates context;
- Fed/inflation context;
- risk-sentiment context;
- confidence;
- freshness;
- concise reasons/counter-evidence.

Fundamental evidence cannot force a trade against clearly contrary price structure.

## Holiday context

Holiday calendars provide participation/liquidity context. A US/UK/bank holiday does **not** automatically mean XAU is closed.

Actual broker tradeability and live market data remain market-open authority.

## Unscheduled shocks

The system cannot guarantee advance knowledge of every breaking geopolitical or macro event. Abnormal gaps, spread explosions, price velocity and feed dislocation are handled by market-data/volatility/execution safety even when no scheduled-event record exists.

## News-safety handoff

This desk publishes event facts and provider health. The hard safety layer consumes those facts to derive states such as:

```text
NEWS_CLEAR
NEWS_BLACKOUT
NEWS_SAFETY_UNKNOWN
POST_NEWS_WARMUP
```

The intelligence desk must not bypass or duplicate that permission state machine.

## Replay requirements

Historical event research must preserve what event information would have been known at the decision time. Revised future macro data cannot be silently substituted into prior decisions where that would create look-ahead.

## Dashboard visibility

Compact example:

```text
Macro Bias       MILD BUY
USD Context      SUPPORTIVE
Yield Context    SUPPORTIVE
Next High Event  CPI
News Facts       VERIFIED
```

Hard `CLEAR/BLOCKED` status should be displayed from the safety layer, not invented here.

## Tests required

- provider freshness/stale handling;
- macro-opinion missing versus event-facts missing;
- event identity/time normalization;
- holiday context not equalling market closure;
- no silent `no news` fallback;
- replay chronology where historical news data is used.

## Explicit non-goals

This desk must not:

- place orders;
- hard-block entries by itself;
- override price/structure with macro opinion;
- claim perfect breaking-news awareness;
- treat provider failure as neutral/clear.

## Open questions

- final data providers;
- exact event-tier mapping;
- exact blackout windows by tier;
- post-event data freshness requirements;
- exact treatment of speeches/unscheduled high-impact events.