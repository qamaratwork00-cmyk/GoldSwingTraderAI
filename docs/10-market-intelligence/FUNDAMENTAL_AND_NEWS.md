# GoldSwingTraderAI — Fundamental and News Intelligence

**Status:** PROVISIONAL  
**Version:** 0.2-design  
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
- Fed Chair communications;
- CPI/Core CPI;
- NFP and major labour releases;
- Core PCE/PCE;
- PPI;
- Retail Sales;
- GDP;
- ISM activity data;
- JOLTS/ADP/jobless claims;
- other provider-classified high-impact USD events.

For each event, publish at least:

- event identity;
- relevant currency/market;
- scheduled time;
- impact/severity metadata;
- provider timestamp/freshness;
- source health.

This document publishes event facts/classification. `../30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` owns final hard permission state.

## Initial V1 event tiers

The initial implementation uses three operational tiers.

### TIER 1 — Critical Gold/USD shock events

Initial examples include:

- FOMC rate decision / policy statement / SEP or dot-plot release;
- Fed Chair press conference or clearly scheduled major Fed Chair communication;
- CPI / Core CPI;
- NFP;
- Core PCE / PCE where provider marks the release as high impact.

Initial hard no-new-entry window:

```text
15 minutes before scheduled event
through
15 minutes after scheduled event
```

For a known event cluster, such as a rate decision followed by a scheduled press conference, the hard window covers the cluster and extends through **15 minutes after the final scheduled critical item** rather than reopening briefly between linked events.

### TIER 2 — High-impact USD events

Initial examples may include:

- PPI;
- Retail Sales;
- GDP;
- ISM releases;
- JOLTS / ADP / major labour updates;
- weekly claims or other events when the accepted provider marks them high impact for USD/Gold.

Initial hard no-new-entry window:

```text
5 minutes before scheduled event
through
5 minutes after scheduled event
```

### TIER 3 — Contextual / ordinary events

Tier 3 does **not** create an automatic hard blackout in V1. It may affect macro/session context and confidence but remains soft evidence unless market behaviour itself triggers another safety authority.

Provider-specific names may differ. The mapping layer must normalize provider labels into these internal tiers and keep the mapping versioned/auditable.

## Open trades during scheduled news

A scheduled news blackout blocks **new entries**. It does not automatically force-close an already-open bot-managed trade merely because an event approaches.

Open positions remain under Trade Manager + execution safety. They may be protected or exited for structural, session, execution or risk reasons, but news timing alone is not an automatic close command in V1.

## Provider health and fallback

The desk must distinguish at least:

```text
VERIFIED
DEGRADED
STALE
UNAVAILABLE
UNKNOWN
```

Where practical, V1 should support an accepted primary event-calendar source plus an accepted fallback/secondary source so one provider outage does not unnecessarily stop trading.

Examples:

- macro-opinion feed unavailable but scheduled-event feed healthy → macro evidence UNKNOWN/DEGRADED; event facts remain usable;
- primary event source unavailable but accepted fallback verifies required event truth → event safety may continue;
- required event-calendar truth unavailable/stale across all accepted sources → publish insufficient event truth so the safety layer enters `NEWS_SAFETY_UNKNOWN` for new entries.

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

This desk publishes event facts, internal tier and provider health. The hard safety layer consumes those facts to derive:

```text
NEWS_CLEAR
NEWS_BLACKOUT
NEWS_SAFETY_UNKNOWN
POST_NEWS_WARMUP
```

The intelligence desk must not bypass or duplicate that permission state machine.

## Replay requirements

Historical event research must preserve what event information would have been known at the decision time. Revised future macro data cannot be silently substituted into prior decisions where that would create look-ahead.

Replay should preserve the event tier/window policy version used at the time of the simulated decision.

## Dashboard visibility

Compact example:

```text
Macro Bias       MILD BUY
Next Event       CPI • TIER 1
Event In         00:42:15
News Facts       VERIFIED
```

Hard `CLEAR/BLACKOUT/UNKNOWN/WARMUP` status should be displayed from the safety layer, not invented here.

## Tests required

- provider freshness/stale handling;
- accepted fallback provider path;
- macro-opinion missing versus event-facts missing;
- event identity/time normalization;
- Tier 1 mapping and `-15/+15 minute` event window facts;
- linked critical-event cluster handling;
- Tier 2 mapping and `-5/+5 minute` event window facts;
- Tier 3 does not independently create a hard blackout;
- holiday context not equalling market closure;
- no silent `no news` fallback;
- replay chronology where historical news data is used.

## Explicit non-goals

This desk must not:

- place orders;
- hard-block entries by itself;
- override price/structure with macro opinion;
- claim perfect breaking-news awareness;
- treat provider failure as neutral/clear;
- automatically close a managed position solely because scheduled news is approaching.

## Open questions

- final production data provider(s) and credentials/configuration;
- final provider-specific mapping table for every named event;
- exact freshness TTL by provider/API;
- future evidence-based changes to initial tier membership/windows if DEMO/research justifies them;
- detailed treatment of unusual long-duration speeches or unscheduled events.
