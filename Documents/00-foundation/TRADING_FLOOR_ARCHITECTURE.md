# GoldSwingTraderAI — Trading Floor Architecture

**Status:** PROVISIONAL
**Version:** 0.1-foundation
**Authority:** Specialist-desk ownership and authority boundaries

## Why a trading floor

The system is easier to reason about when every analytical desk has one
question, one output and one limit. The floor prevents a single giant strategy
function from mixing market interpretation, money and broker side effects.

## Floor wiring

~~~mermaid
flowchart TB
    SNAP["Verified shared snapshot"] --> MARKET["Market desks"]
    MARKET --> FAMILIES["Six independent strategy families"]
    FAMILIES --> TEAMS["Independent BUY and SELL thesis teams"]
    TEAMS --> BOARD["Red Team, fusion, timing and Trade Plan"]
    BOARD --> CONTROL["Risk, session/news and execution authorities"]
    CONTROL --> BROKER["One governed broker boundary"]
    BROKER --> MANAGE["Trade Manager, persistence and research"]
~~~

The first four analytical groups can consume shared immutable facts. The
control boards are ordered. No desk may obtain permission by collecting enough
soft votes.

## Desk catalogue

| Desk | Owns | Publishes | Cannot do |
|---|---|---|---|
| Market Data | MT5 facts, symbol, quote, history, positions and quality | normalized read facts | strategy, sizing or writes |
| Candle/Structure | anatomy, sequences, swings, BOS/MSS, displacement, rejection and compression | StructureReport | order or risk permission |
| Technical/Location | zones, location, target room and conflict | TechnicalReport | redefine swings or write |
| Confluence | causal Trendline, Fibonacci and broker-local POC | optional ConfluenceReport | become mandatory gate |
| Liquidity/SMC | pools, sweeps, FVG, qualified OB and path | LiquidityReport | label every wick a sweep |
| Quant | EMA20/50, RSI14, ATR14, volatility, momentum and extension | QuantReport | stand-alone trade veto |
| Fundamental/News | macro opinion, event facts and provider health | NewsFacts | silently grant NEWS_CLEAR |
| Session Context | timezone-safe session labels/ranges | SessionReport | own broker OPEN/CLOSED |
| Strategy Floor | six family hypotheses | FamilyReport per family | size or write |
| BUY Team | strongest coherent bullish case | BUY thesis | hide SELL evidence |
| SELL Team | strongest coherent bearish case | SELL thesis | hide BUY evidence |
| Red Team | opposing evidence and correlation challenge | objections/conflict | invent arbitrary blockers |
| Fusion Board | edge, conflict, coverage and reasons | DecisionSnapshot | override hard safety |
| Entry Timing | M5 executable moment and opportunity lifecycle | ENTER/WAIT/MISSED/INVALID | call broker |
| Trade Plan | entry, invalidation, SL, objectives and original R | TradePlan | size account risk |
| Risk | affordability, capacity, daily loss and cooldown | PASS/BLOCK/UNKNOWN | change structural SL |
| Session/News Permission | hard schedule/news states | permission states | source a commercial provider |
| Execution Gate | final broker-write permission | ALLOW/BLOCK/UNKNOWN | decide direction |
| Writer/Reconciler | one broker action and outcome truth | verified lifecycle | blind retry |
| Controller | lease and fencing epoch | ownership proof | bypass recovery |
| Trade Manager | open-trade action and objective progression | HOLD/PROTECT/TRAIL/RUNNER/EXIT | use a second write path |
| Persistence | durable records, checkpoints and backups | recoverable state | pretend backup is broker truth |
| Research Lab | replay, metrics, discovery and promotion | evidence/candidates | direct live mutation |
| Operator | DTOs and terminal display | readable status | recalculate authority |
| System Health | fault aggregation and impact | health records | redefine subsystem policy |

## Six family questions

| Family | Question | Evidence emphasis |
|---|---|---|
| Trend Pullback Continuation | Is a directional move resuming from useful location? | HTF context, pullback, M5 resumption and room |
| Breakout Expansion | Is an accepted break releasing expansion? | qualified break, acceptance, momentum and path |
| Breakout Retest Continuation | Did a meaningful break hold when retested? | break, retest location and M5 response |
| Liquidity Sweep Reversal | Was an existing pool taken and rejected? | pool existence, sweep, reclaim and shift |
| Failed Breakout Reversal | Did attempted acceptance fail and reverse? | failed-break event and opposing response |
| Compression Expansion | Did compression release with evidence? | compression, release, break and volatility build |

## Optional confluence rule

~~~text
supportive Trendline/Fibonacci/POC → bounded positive bonus
missing optional confluence        → no base-score penalty
opposed/unclear confluence         → visible context/conflict, not automatic block
POC alone                          → no directional authority
~~~

Trendline uses confirmed swings, Fibonacci uses confirmed impulse anchors, and
POC records whether the volume source is real or tick-volume approximation.

## Authority chain

~~~mermaid
flowchart LR
    SOFT["Many soft evidence producers"] --> THESIS["Thesis and structural plan"]
    THESIS --> MONEY["Risk and session/news"]
    MONEY --> GATE["One final permission gate"]
    GATE --> WRITE["One raw MT5 writer"]
~~~

This asymmetry is intentional. It permits flexible market interpretation while
keeping irreversible action narrow and auditable.

## Source and test navigation

| Floor area | Source | Proof |
|---|---|---|
| market desks | intelligence/candle_structure.py, technical.py, liquidity.py, indicators.py, confluence.py, session.py, news.py | test_intelligence_core.py, test_technical_liquidity.py, test_technical_confluence.py, test_intelligence_snapshot.py |
| family floor | strategies/floor.py, strategies/confluence.py | test_strategy_decisions.py |
| fusion/timing/plan | decisions/fusion.py, opportunity.py, timing.py, trade_plan.py | test_strategy_decisions.py, test_trade_plan_risk.py |
| risk/session | risk/engine.py, state.py, permissions.py | test_trade_plan_risk.py, test_risk_state_regressions.py, test_session_news_permissions.py |
| execution | execution/gate.py, service.py, mt5_writer.py, reconcile.py, controller.py | test_execution_safety.py, test_sqlite_coordination.py |
| management | management/manager.py, execution.py, store.py | test_trade_manager.py, test_management_execution.py |
| research | research/ | test_research_*.py, test_discovery_*.py, test_promotion_governance.py |

## What the floor does not mean

Logical parallelism is not permission voting. A higher score is not higher
monetary risk. A dashboard panel is not a control authority. A research
candidate is not production. A broker acknowledgement is not necessarily
verified exposure.

