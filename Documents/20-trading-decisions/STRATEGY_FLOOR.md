# GoldSwingTraderAI — Strategy Floor

**Status:** PROVISIONAL
**Version:** 0.1-strategy
**Authority:** Six production strategy-family hypotheses and optional confluence

## Purpose

The strategy floor answers: which coherent market hypotheses exist right now?
It does not decide account affordability or broker permission.

## Shared-snapshot parallelism

~~~mermaid
flowchart TB
    SNAP["One IntelligenceSnapshot"] --> A["Trend Pullback Continuation"]
    SNAP --> B["Breakout Expansion"]
    SNAP --> C["Breakout Retest Continuation"]
    SNAP --> D["Liquidity Sweep Reversal"]
    SNAP --> E["Failed Breakout Reversal"]
    SNAP --> F["Compression Expansion"]
    A --> REPORT["Independent FamilyReports — BUY + SELL + coverage"]
    B --> REPORT
    C --> REPORT
    D --> REPORT
    E --> REPORT
    F --> REPORT
    REPORT --> FUSION["Decision Fusion"]
~~~

The implementation may call families sequentially for deterministic output.
They are logically parallel because no family reads another family’s result,
mutates shared state or grants permission.

## Family catalogue

| Family | Market question | Main evidence | Does not require |
|---|---|---|---|
| Trend Pullback Continuation | Is an established move resuming from useful location? | HTF context, M15 pullback/location, M5 resumption, room | every FVG/OB/Fib/TL |
| Breakout Expansion | Is accepted break releasing expansion? | break maturity, acceptance, momentum, volatility, path | perfect retest |
| Breakout Retest Continuation | Did a meaningful break hold on retest? | prior break, retest location and M5 response | every SMC primitive |
| Liquidity Sweep Reversal | Was existing liquidity taken and rejected? | pool, sweep, reclaim, rejection/MSS | wick alone |
| Failed Breakout Reversal | Did acceptance fail and reverse? | FAILED_BREAK, opposing response and location | same narrative as sweep |
| Compression Expansion | Did compressed price release directionally? | compression, release, break, volatility build and path | guessed direction before release |

Every family can publish BUY, SELL or neutral evidence. A family report retains
score, coverage, supporting labels, conflicts, timing profile and target/path
context.

## Optional technical confluence

~~~text
base family score
+ bounded supportive Trendline/Fibonacci/POC bonus
= adjusted family score
~~~

Missing or opposed optional confluence does not subtract the base score or
create a hard block. POC is direction-neutral alone. Correlated tools are
capped so one market event is not counted six times.

## Strategy boundaries

Strategy code may consume IntelligenceSnapshot and produce typed hypotheses. It
may not query MetaTrader5, calculate monetary lot risk, inspect controller
ownership, write SQLite lifecycle state as a broker action, or call order_send.

## Opportunity identity

The family floor can create/update a Market Episode and Opportunity, but it does
not decide whether the opportunity is currently executable. Stable
opportunity_id and episode_id must survive WAIT, MISSED and restart through the
decisions/persistence owners.

## Implementation and tests

| Source | Role | Tests |
|---|---|---|
| strategies/floor.py | six family evaluation | test_strategy_decisions.py |
| strategies/confluence.py | optional positive-only bonus | test_strategy_decisions.py, test_technical_confluence.py |
| intelligence/snapshot.py | shared input | test_intelligence_snapshot.py |
| decisions/fusion.py | bounded correlation/conflict | test_strategy_decisions.py |

## Research and dashboard

Research must compare each family and optional confluence with Opportunity
Recall, trade frequency, Net R, drawdown and capture. The dashboard shows
leading family, BUY/SELL cases, coverage and optional confluence as context.

## Explicit non-goals

No family is a universal filter. All six need not agree. The floor does not
size risk, create broker permission, modify a position or self-promote a
research candidate.

