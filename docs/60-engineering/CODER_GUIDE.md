# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT  
**Authority:** Developer implementation map. It explains where a feature lives once code exists; it does not redefine trading behaviour.

## Purpose

This guide is the developer-facing map for the whole bot. For each major feature it must eventually answer:

1. What does the feature do?
2. Which design document owns its semantics?
3. Which module is the primary code owner?
4. Which configuration, runtime call-site, persistence, dashboard and tests are also involved?
5. What safety invariants must remain intact when the feature changes?

The key rule is: **do not fix or change a cross-cutting feature by editing only the most visible file.**

## Relationship to other engineering docs

- `MODULE_STRUCTURE.md` will be **file-oriented**: every module, responsibility and dependency direction.
- `CODER_GUIDE.md` is **feature-oriented**: every feature and the complete path a developer must inspect.
- `TESTING_AND_VERIFICATION.md` owns validation requirements.
- `RELEASE_CHECKLIST.md` owns release sign-off gates.

These documents should link to each other rather than repeat full contracts.

## Authoritative change path

When a feature affects trading authority, inspect the entire path relevant to that feature:

```text
design contract
→ configuration
→ market/broker facts
→ specialist intelligence
→ strategy/decision fusion
→ trade plan
→ risk/safety
→ execution
→ persistence/reconciliation
→ dashboard/operator visibility
→ replay/research parity
→ tests
```

Not every feature touches every layer, but a coder must prove which layers are involved before changing behaviour.

## Planned runtime ownership model

```text
bot entrypoint
   ↓
runtime coordinator
   ↓
verified market snapshot
   ↓
parallel specialist desks
   ↓
strategy floor + BUY/SELL theses
   ↓
decision fusion + entry timing
   ↓
structural trade plan
   ↓
independent risk/session/safety authority
   ↓
durable pre-submit state
   ↓
one governed broker submission
   ↓
reconciliation + trade manager
   ↓
journal/research/dashboard
```

The coordinator should orchestrate authorities; it should not duplicate their algorithms.

## Feature ownership index — design phase

The table below defines documentation ownership now. Code ownership will be added as modules are implemented.

| Feature | Behaviour authority | Future code owner category |
|---|---|---|
| Project identity and global invariants | `00-foundation/SYSTEM_CONTRACT.md` | core/config |
| Market data / candle history | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | broker/market data |
| Candle interpretation | `10-market-intelligence/CANDLE_STRUCTURE.md` | market intelligence |
| Technical structure / levels | `10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md` | market intelligence |
| Liquidity / FVG / OB | `10-market-intelligence/LIQUIDITY_AND_SMC.md` | market intelligence |
| Indicators / volatility | `10-market-intelligence/INDICATORS_AND_VOLATILITY.md` | market intelligence |
| Fundamental / news context | `10-market-intelligence/FUNDAMENTAL_AND_NEWS.md` | market intelligence + safety adapter |
| Strategy families | `20-trading-decisions/STRATEGY_FLOOR.md` | strategy |
| Entry timing / setup lifecycle | `20-trading-decisions/ENTRY_TIMING.md` | decision/timing |
| BUY/SELL fusion / scoring | `20-trading-decisions/SCORING_AND_DECISION_FUSION.md` | decision/fusion |
| Entry/SL/target/original R | `20-trading-decisions/TRADE_PLAN.md` | planning |
| Open-position management / exit | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | management |
| Monetary risk | `30-risk-execution/RISK_CONTRACT.md` | risk |
| Session / daily lock / cooldown state | `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` | session/risk state |
| Broker send / account safety | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | execution/broker guard |
| Restart / recovery / reconciliation | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | state/lifecycle |
| Replay / holdouts / validation | `40-research-learning/RESEARCH_AND_VALIDATION.md` | research/replay |
| Governed strategy discovery | `40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md` | research/discovery |
| Autonomous invention | `40-research-learning/AUTONOMOUS_STRATEGY_INVENTION.md` | research/invention |
| Promotion / rollback | `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md` | governance/promotion |
| Learning / AI limits | `40-research-learning/LEARNING_AND_AI_BOUNDARIES.md` | learning/advisory |
| Dashboard / operator controls | `50-operator/DASHBOARD_AND_UX.md` | UI/operator |

## Dependency-direction rules

These rules are intended to become coding invariants:

1. Broker/data adapters provide facts; strategy modules should not call raw MT5 directly.
2. Market-intelligence desks describe evidence; they do not grant broker authority.
3. Strategy produces opportunity intent; it does not size lots or send orders.
4. Entry timing may return ENTER/WAIT/MISSED/INVALID, but it cannot bypass risk or safety.
5. Trade-plan logic chooses structural entry/SL/target semantics; risk decides whether that plan is affordable.
6. Risk approval does not itself send an order.
7. Execution receives a fully approved and durably persisted decision.
8. Dashboard observes state; it never becomes a broker-write authority.
9. Research/AI/ML may propose or rank candidates but cannot mutate hard safety limits or self-deploy arbitrary code.
10. Replay and live paths must share frozen decision semantics wherever parity is claimed.

## Safety invariants a coder must preserve

- Unknown financial/broker/order state fails closed.
- A high strategy score cannot override a hard risk/news/account/data block.
- Original R remains immutable for lifecycle and performance attribution.
- Stops are not widened merely to fit a desired lot/risk budget.
- An ambiguous broker acknowledgement is reconciliation-only; no blind duplicate retry.
- Optional intelligence may fail neutral/unknown where documented; hard safety uncertainty must block.
- Missing optional evidence is not silently converted to bearish/bullish evidence or score zero.
- Autonomous discovery/invention cannot generate and execute arbitrary Python.

## Debugging order — target architecture

When an expected trade does not occur, diagnose by authority rather than changing the strategy first:

```text
1. Is broker/account/data state valid?
2. Is the market/session state tradeable?
3. Is risk state unlocked and verified?
4. Is any previous order/lifecycle ambiguity unresolved?
5. Does a valid opportunity exist?
6. What are BUY and SELL thesis scores/conflict?
7. Is the setup ARMED/READY and is timing ENTER rather than WAIT/MISSED/INVALID?
8. Is the structural trade plan valid and target room sufficient?
9. Is the plan affordable under monetary risk/margin/exposure rules?
10. Are fresh quote/order-check/execution conditions valid?
```

## How this guide will evolve

During implementation, every major feature section must add:

```text
Purpose
Authoritative design doc
Primary module
Related modules
Configuration fields
Runtime call path
Persistence/state
Dashboard visibility
Replay/research parity
Tests
Known failure modes
Change checklist
```

Do not fill these with guessed filenames before the module architecture is actually frozen. The guide should map the real project, not force the implementation to imitate a prior repository.