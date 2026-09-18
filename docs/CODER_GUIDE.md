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

- `60-engineering/MODULE_STRUCTURE.md` will be **file-oriented**: every module, responsibility and dependency direction.
- `CODER_GUIDE.md` is **feature-oriented**: every feature and the complete path a developer must inspect.
- `60-engineering/TESTING_AND_VERIFICATION.md` owns validation requirements.
- `60-engineering/RELEASE_CHECKLIST.md` owns release sign-off gates.

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
CENTRAL EXECUTION PERMISSION GATE
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
| Central broker-write permission gate | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | execution permission / broker guard |
| Broker send / account safety | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | execution/broker guard |
| Restart / recovery / reconciliation | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | state/lifecycle |
| Replay / holdouts / validation | `40-research-learning/RESEARCH_AND_VALIDATION.md` | research/replay |
| Governed strategy discovery | `40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md` | research/discovery |
| Autonomous invention | `40-research-learning/AUTONOMOUS_STRATEGY_INVENTION.md` | research/invention |
| Promotion / rollback | `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md` | governance/promotion |
| Learning / AI limits | `40-research-learning/LEARNING_AND_AI_BOUNDARIES.md` | learning/advisory |
| Dashboard / operator controls | `50-operator/DASHBOARD_AND_UX.md` | UI/operator |

## Centralized execution-permission feature

This is an intentionally visible and auditable feature of GoldSwingTraderAI.

### Goal

A developer should be able to inspect **one primary execution-permission component** and understand why the bot may or may not perform an irreversible MT5 write.

The exact source filename will be frozen in `60-engineering/MODULE_STRUCTURE.md`, but the implementation must provide a single primary code owner conceptually equivalent to:

```text
ExecutionPermissionGate
```

or

```text
BrokerWriteGuard
```

Do not scatter the final permission decision across strategy files, risk code, dashboard rendering and raw MT5 adapters.

### Inputs to the centralized gate

The gate consumes authoritative results rather than reimplementing every subsystem:

```text
Environment policy        DEMO_ALLOWED / REAL_ALLOWED / BLOCK
Account identity          PASS / BLOCK / UNKNOWN
Market + quote integrity  PASS / BLOCK / UNKNOWN
News/session safety       PASS / BLOCK / UNKNOWN
Risk                      PASS / BLOCK / UNKNOWN
Position capacity         PASS / BLOCK / UNKNOWN
Order lifecycle           PASS / BLOCK / UNKNOWN
Controller ownership      PASS / BLOCK / UNKNOWN
Fresh execution checks    PASS / BLOCK / UNKNOWN
```

### Output

The primary result should be easy to demonstrate and test:

```text
Execution Permission      ALLOW / BLOCK / UNKNOWN
Primary Reason            <reason code>
Secondary Reasons         <reason codes>
Would Otherwise Trade     YES / NO / N/A
```

The dashboard may render this attractively, but the dashboard does not own the result.

### DEMO / future REAL switch

The current development/release safeguard allows broker execution only for the approved DEMO environment. This policy must be represented as one explicit input to the centralized permission component, not repeated as scattered `if demo` conditions.

Future REAL execution is therefore not a second trading engine. Once explicitly approved by a future frozen release policy, it uses:

```text
same strategy
same risk authority
same execution permission gate
same one-shot broker path
same reconciliation
```

with the environment policy changed from DEMO-only to the approved REAL policy.

### Ordinary blockers are not hidden LIVE blockers

The following may block a specific trade in DEMO or future approved REAL execution, but they are normal safety authorities rather than permanent REAL-account prohibitions:

```text
DAILY_LOSS_LOCK
NEWS_BLACKOUT
DATA_STALE / invalid data
ACCOUNT_IDENTITY_MISMATCH
SPREAD_TOO_HIGH
PRICE_DRIFT
MIN_LOT_UNAFFORDABLE
MARGIN_INSUFFICIENT
POSITION_CAPACITY_FULL
ORDER_ACK_UNKNOWN / unresolved lifecycle
critical state corruption
ANOTHER_ACTIVE_CONTROLLER
broker/symbol unavailable
```

These should be visible through the same permission trace so a developer/operator never has to guess which rule stopped the trade.

### Broker-write call-site rule

Creation, modification and closure of bot-managed positions must have one governed broker-write path. Raw `order_send`/equivalent irreversible calls must not be reachable directly from:

- strategy modules;
- scoring/fusion;
- entry timing;
- trade-plan construction;
- dashboard/UI;
- research/learning/autonomous strategy code.

The execution adapter may contain low-level MT5 API calls, but it acts only after the centralized permission boundary and persisted intent/lifecycle requirements are satisfied.

### Why this feature is kept together

Keeping the final permission logic together makes the safety model:

- easy to show to another developer;
- easy to audit;
- easy to test exhaustively;
- less likely to acquire hidden bypasses;
- easier to explain on the dashboard;
- safer to extend from DEMO to a future explicitly approved REAL mode.

## Dependency-direction rules

These rules are intended to become coding invariants:

1. Broker/data adapters provide facts; strategy modules should not call raw MT5 directly.
2. Market-intelligence desks describe evidence; they do not grant broker authority.
3. Strategy produces opportunity intent; it does not size lots or send orders.
4. Entry timing may return ENTER/WAIT/MISSED/INVALID, but it cannot bypass risk or safety.
5. Trade-plan logic chooses structural entry/SL/target semantics; risk decides whether that plan is affordable.
6. Risk approval does not itself send an order.
7. The centralized execution-permission component is the final broker-write authorization boundary.
8. Execution receives a fully approved and durably persisted decision before the irreversible submit step.
9. Dashboard observes state; it never becomes a broker-write authority.
10. Research/AI/ML may propose or rank candidates but cannot mutate hard safety limits or self-deploy arbitrary code.
11. Replay and live paths must share frozen decision semantics wherever parity is claimed.

## Safety invariants a coder must preserve

- Unknown financial/broker/order state fails closed.
- A high strategy score cannot override a hard risk/news/account/data block.
- Original R remains immutable for lifecycle and performance attribution.
- Stops are not widened merely to fit a desired lot/risk budget.
- An ambiguous broker acknowledgement is reconciliation-only; no blind duplicate retry.
- Optional intelligence may fail neutral/unknown where documented; hard safety uncertainty must block.
- Missing optional evidence is not silently converted to bearish/bullish evidence or score zero.
- Autonomous discovery/invention cannot generate and execute arbitrary Python.
- No broker-write path may bypass the centralized execution-permission gate.
- DEMO/REAL environment authorization must have one explicit policy source rather than duplicated ad-hoc checks.

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
10. What does the centralized Execution Permission Gate report?
11. Are fresh quote/order-check/execution conditions valid?
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

For the centralized execution-permission feature specifically, implementation documentation must show the exact source file, public interface, all broker-write call sites and the tests proving that no bypass exists.

Do not fill unrelated features with guessed filenames before the module architecture is actually frozen. The guide should map the real project, not force the implementation to imitate a prior repository.
