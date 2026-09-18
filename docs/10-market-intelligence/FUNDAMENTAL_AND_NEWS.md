# GoldSwingTraderAI — Fundamental and News Intelligence

**Status:** PROVISIONAL  
**Version:** 0.3-implementation-baseline  
**Authority:** Macro/fundamental Gold context, scheduled-event facts, provider freshness and holiday context.  
**Depends on:** `MARKET_DATA_AND_HISTORY.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Purpose

This document defines market-intelligence facts and opinions related to Gold fundamentals and scheduled news. It intentionally separates **macro opinion** from **hard trading permission**.

> **Macro/fundamental opinion is soft evidence. Event-risk permission is enforced by the risk/session safety layer.**

## Phase 3 implementation checkpoint

Provider-neutral scheduled-event normalization is implemented in:

```text
src/goldswingtraderai/intelligence/news.py
```

It currently accepts supplied provider records and publishes normalized event facts. A production external calendar provider/credential integration is **not yet selected or implemented**.

Implemented baseline outputs include:
- provider health/freshness: `VERIFIED/DEGRADED/STALE/UNAVAILABLE/UNKNOWN`;
- provider event ID/title/currency/scheduled UTC time;
- internal TIER 1/2/3 classification;
- factual pre/post window bounds;
- merging of overlapping/linked non-Tier-3 event windows;
- explicit `required_event_truth_available` instead of silently assuming no news.

`intelligence/snapshot.py` may attach these `NewsFacts` to the shared `IntelligenceSnapshot`. The intelligence layer still does **not** derive hard `NEWS_BLACKOUT` permission.

## Fundamental context

Potential future provider-backed soft inputs include:

- USD/DXY behaviour;
- US Treasury yields;
- rate expectations;
- Fed policy context;
- inflation/labour data context;
- risk sentiment;
- geopolitical stress where a reliable source exists.

These macro-opinion feeds are not required for the Phase-3 baseline and remain future adapter work. Price/structure remains primary trading evidence.

## Scheduled-event facts

Normalized facts may represent events such as:

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

This document publishes event facts/classification. `../30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` owns final hard permission state.

## Initial V1 event tiers

### TIER 1 — Critical Gold/USD shock events

Baseline title mapping includes FOMC/rate decision, Fed Chair press conference, CPI, NFP and Core PCE/PCE high-impact concepts.

Initial hard-safety policy consumed later is:

```text
15 minutes before scheduled event
through
15 minutes after scheduled event
```

The Phase-3 facts adapter records these bounds but does not itself block trading.

Linked/overlapping critical windows are merged so a known rate-decision/press-conference cluster does not falsely reopen between adjacent windows.

### TIER 2 — High-impact USD events

Baseline concepts include PPI, Retail Sales, GDP, ISM, JOLTS, ADP and jobless/unemployment claims. Other USD events explicitly marked high/critical by a provider fall into Tier 2 unless a Tier-1 mapping applies.

Initial factual window:

```text
5 minutes before scheduled event
through
5 minutes after scheduled event
```

### TIER 3 — Contextual / ordinary events

Tier 3 records event context but carries no automatic hard blackout window in the Phase-3 facts model.

Provider-specific mapping tables may later supersede the baseline keyword mapper. Any such mapping must remain versioned/auditable.

## Open trades during scheduled news

A scheduled news blackout blocks **new entries** under the later safety state machine. It does not automatically force-close an already-open bot-managed trade merely because an event approaches.

Open positions remain under Trade Manager + execution safety.

## Provider health and fallback

The intelligence model distinguishes:

```text
VERIFIED
DEGRADED
STALE
UNAVAILABLE
UNKNOWN
```

The current baseline default freshness TTL is 30 minutes when the adapter is called without a provider-specific value. That TTL is an implementation default, not a frozen provider policy.

Required event truth is usable only when effective provider health is `VERIFIED` or `DEGRADED`. Missing fetch time, stale data, unavailable provider or unknown health never becomes silent `no news`.

Future production integration should support an accepted primary source and, where practical, an accepted fallback source. The later safety layer decides how combined-provider truth becomes `NEWS_CLEAR/BLACKOUT/UNKNOWN/WARMUP`.

## Fundamental evidence

Future soft outputs may include:

- Fundamental BUY Support;
- Fundamental SELL Support;
- USD context;
- yield/rates context;
- Fed/inflation context;
- risk-sentiment context;
- confidence/freshness;
- concise reasons/counter-evidence.

Fundamental evidence cannot force a trade against clearly contrary price structure.

## Holiday context

Holiday calendars provide participation/liquidity context. A US/UK/bank holiday does **not** automatically mean XAU is closed.

Actual broker tradeability and live market data remain market-open authority.

## Unscheduled shocks

The system cannot guarantee advance knowledge of every breaking geopolitical or macro event. Abnormal gaps, spread explosions, price velocity and feed dislocation are handled by market-data/volatility/execution safety even when no scheduled-event record exists.

## News-safety handoff

This desk publishes event facts, internal tier and provider health. The later hard safety layer consumes those facts to derive:

```text
NEWS_CLEAR
NEWS_BLACKOUT
NEWS_SAFETY_UNKNOWN
POST_NEWS_WARMUP
```

The intelligence desk must not bypass or duplicate that permission state machine.

## Replay requirements

Historical event research must preserve what event information would have been known at the decision time. Revised future macro data cannot be silently substituted into prior decisions where that would create look-ahead.

Replay should preserve event tier/window mapping version and provider-health assumptions used at the simulated decision time.

## Dashboard visibility

Compact example:

```text
Macro Bias       UNKNOWN / MILD BUY
Next Event       CPI • TIER 1
Event In         00:42:15
News Facts       VERIFIED
```

Hard `CLEAR/BLACKOUT/UNKNOWN/WARMUP` status must be displayed from the safety layer, not invented here.

## Tests required / current evidence

Required:
- provider freshness/stale handling;
- fallback-provider path when implemented;
- event identity/time normalization;
- Tier 1 mapping and `-15/+15` factual windows;
- linked critical-event cluster handling;
- Tier 2 mapping and `-5/+5` factual windows;
- Tier 3 no automatic hard blackout;
- no silent `no news` fallback;
- replay chronology.

Phase-3 deterministic tests cover tier mapping, cluster merging and stale-provider handling in `tests/test_intelligence_snapshot.py`.

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
- provider-specific mapping table and freshness TTL;
- primary/fallback reconciliation rules;
- macro-opinion data sources;
- future evidence-based changes to initial tier membership/windows;
- detailed treatment of unusual long-duration speeches or unscheduled events.
