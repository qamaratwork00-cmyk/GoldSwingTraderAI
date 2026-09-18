# GoldSwingTraderAI — Coder Guide

**Status:** DRAFT  
**Version:** 0.4-design  
**Authority:** Feature-oriented developer implementation map. It does not redefine trading behaviour.

## Purpose

This guide tells a developer or coding agent where each feature belongs and what cross-cutting invariants must remain intact.

Core rule:

> **Do not fix a cross-cutting feature by editing only the most visible file. Trace the full authority path.**

Use `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for large implementation phases and resume/recovery procedure.

## Relationship to engineering docs

- `60-engineering/MODULE_STRUCTURE.md` — file/module-oriented ownership map;
- `CODER_GUIDE.md` — feature-oriented change/debug map;
- `60-engineering/TESTING_AND_VERIFICATION.md` — validation architecture;
- `60-engineering/RELEASE_CHECKLIST.md` — release gates;
- `60-engineering/FINAL_RELEASE_AUDIT.md` — evidence-backed final sign-off.

## Authority/change path

For a feature that can affect trading behaviour, trace:

```text
authoritative design contract
→ configuration
→ market/broker facts
→ specialist intelligence
→ strategy/decision fusion
→ entry timing
→ Trade Plan
→ risk/session/news authority
→ centralized execution permission
→ broker adapter/write path
→ persistence/reconciliation
→ dashboard/operator visibility
→ replay/research parity
→ tests
```

Not every feature touches every layer; the coder must prove which layers it touches.

## Planned runtime ownership

```text
entrypoint
  ↓
runtime coordinator
  ↓
verified market snapshot
  ↓
parallel specialist desks
  ↓
six strategy families + independent BUY/SELL theses
  ↓
Red Team / decision fusion
  ↓
opportunity lifecycle + entry timing
  ↓
structural Trade Plan
  ↓
risk + session/news/system authorities
  ↓
CENTRAL EXECUTION PERMISSION GATE
  ↓
durable Execution Intent
  ↓
one governed MT5 create/modify/close path
  ↓
reconciliation + Trade Manager
  ↓
journal / research / learning / dashboard
```

The coordinator orchestrates authorities; it must not duplicate their algorithms.

## Feature ownership index

| Feature | Behaviour authority | Code-owner category |
|---|---|---|
| Global invariants | `00-foundation/SYSTEM_CONTRACT.md` | core/config |
| Market data/history | `10-market-intelligence/MARKET_DATA_AND_HISTORY.md` | market-data/broker read |
| Candle/structure | `10-market-intelligence/CANDLE_STRUCTURE.md` | market intelligence |
| S/R/location/target room | `10-market-intelligence/TECHNICAL_STRUCTURE_AND_LEVELS.md` | market intelligence |
| Liquidity/FVG/OB | `10-market-intelligence/LIQUIDITY_AND_SMC.md` | market intelligence |
| EMA/RSI/ATR/volatility | `10-market-intelligence/INDICATORS_AND_VOLATILITY.md` | quant/intelligence |
| Macro/event facts | `10-market-intelligence/FUNDAMENTAL_AND_NEWS.md` | news/fundamental adapter |
| Session context | `10-market-intelligence/SESSION_CONTEXT.md` | session intelligence |
| Strategy families | `20-trading-decisions/STRATEGY_FLOOR.md` | strategy |
| BUY/SELL fusion/Red Team | `20-trading-decisions/SCORING_AND_DECISION_FUSION.md` | decision/fusion |
| Opportunity/entry timing | `20-trading-decisions/ENTRY_TIMING.md` | lifecycle/timing |
| Entry/SL/targets/original R | `20-trading-decisions/TRADE_PLAN.md` | planning |
| HOLD/PROTECT/TRAIL/RUNNER/EXIT | `20-trading-decisions/TRADE_MANAGER_AND_EXIT.md` | trade management |
| Monetary sizing/daily safety | `30-risk-execution/RISK_CONTRACT.md` | risk |
| Hard market/news/risk states | `30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md` | permission-state |
| Execution gate/broker safety/controller | `30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md` | execution/broker guard |
| Restart/recovery/portable state | `30-risk-execution/PERSISTENCE_RESTART_AND_RECOVERY.md` | persistence/lifecycle |
| Replay/validation | `40-research-learning/RESEARCH_AND_VALIDATION.md` | research/replay |
| Discovery/invention | `40-research-learning/GOVERNED_STRATEGY_DISCOVERY.md`, `AUTONOMOUS_STRATEGY_INVENTION.md` | research |
| Promotion/rollback | `40-research-learning/GOVERNED_EXPERIMENTS_AND_PROMOTION.md` | promotion governance |
| StrategyMemory/AI boundaries | `40-research-learning/LEARNING_AND_AI_BOUNDARIES.md` | learning/advisory |
| Dashboard | `50-operator/DASHBOARD_AND_UX.md` | UI/operator |

## V1 environment implementation

Do not build a DEMO/REAL mode engine.

V1 has one positive environment input:

```text
Connected account verified DEMO
→ DEMO_GUARD = PASS
```

If DEMO status is not verified, broker-write permission is not granted.

The DEMO guard must be evaluated in one primary environment/account policy component and passed into the centralized execution-permission result. Do not scatter `if demo` checks throughout strategy, risk or UI code.

V1 does not define a separate REAL authorization workflow or REAL hard-block contract.

## Centralized Execution Permission Gate

A developer should be able to inspect one primary component and understand why an irreversible MT5 action may or may not occur.

Conceptual inputs:

```text
DEMO guard              PASS / NOT_VERIFIED
Account identity        PASS / BLOCK / UNKNOWN
Market/data/quote       PASS / BLOCK / UNKNOWN
News/session            PASS / BLOCK / UNKNOWN
Risk                    PASS / BLOCK / UNKNOWN
Position/ownership      PASS / BLOCK / UNKNOWN
Order lifecycle         PASS / BLOCK / UNKNOWN
Controller lease        PASS / BLOCK / UNKNOWN
Fresh execution checks  PASS / BLOCK / UNKNOWN
```

Output:

```text
Execution Permission    ALLOW / BLOCK / UNKNOWN
Primary Reason          <reason>
Secondary Reasons       <reasons>
Would Otherwise Trade   YES / NO / N/A
```

Dashboard renders this output but never owns it.

## Broker-write call-site invariant

All bot-managed create/modify/close actions must use one governed write path.

Raw `order_send`/equivalent irreversible calls must not be reachable from:

- market intelligence;
- strategy modules;
- scoring/fusion;
- entry timing;
- Trade Plan;
- dashboard;
- research/learning/invention.

Before irreversible send:

```text
permission passes
→ durable Execution Intent persisted
→ broker pre-checks
→ exactly one governed write attempt
→ classify outcome
→ reconcile
```

Ambiguous acknowledgement means reconciliation, not retry.

## Position ownership/capacity

V1 capacity is `0/1` independently risk-bearing Gold position.

Ownership states include at least:

```text
BOT_MANAGED
MANUAL
FOREIGN_EA
UNKNOWN_OWNER
```

Manual/foreign/unknown Gold exposure is never modified as bot-owned and prevents a fresh bot Gold entry until reconciled clear.

Opposite opportunity while a bot position is open routes to Trade Manager as reversal/exit evidence; it does not create an automatic hedge.

## Risk implementation invariants

- profile/risk bands and ceilings are owned by `RISK_CONTRACT.md`;
- SMALL may evaluate executable minimum lot such as `0.01` even when theoretical raw lot is smaller;
- actual all-in executable risk decides affordability;
- structural SL is never moved merely to fit desired risk;
- high score cannot increase monetary risk;
- daily lock uses cash-flow-adjusted verified account equity;
- manual reset does not erase cumulative day history;
- one ordinary loss does not trigger global cooldown;
- same episode re-entry and 3-loss cooldown rules must persist across restart.

## Trade Plan / exit invariants

- no fixed 100/200/300-pip TP authority;
- original R immutable;
- Primary/Expansion/Runner objectives have distinct roles;
- initial RR guard is implemented from the Trade Plan authority;
- V1 exit logic cannot depend on partial close being available;
- runner extension requires fresh evidence/new objective;
- stop may tighten but never intentionally widen beyond original approved risk;
- PRE_CLOSE flatten overrides runner logic.

## Session/news invariants

- scheduled close times come from verified broker Gold session schedule;
- daily T-20 no-new-entry / T-10 flatten;
- weekend T-60 no-new-entry / T-30 flatten;
- reopen freshness requirements are enforced before entry readiness;
- news Tier 1 `-15/+15`, Tier 2 `-5/+5`, Tier 3 no automatic hard blackout;
- severe post-news dislocation requires clean M5 + normalized conditions;
- news blackout alone does not force-close an existing managed trade.

## Spread / price-drift implementation

Healthy spread baseline must exclude stale/news-spike/reopen-dislocation observations.

Initial states:

```text
SpreadRatio <=1.50  NORMAL
>1.50–2.25          ELEVATED + revalidate
>2.25               current entry prevented
spread >25% SL dist current entry prevented
```

Adverse price drift:

```text
<=10% stop distance    normal revalidation
>10–20%                elevated full revalidation
>20%                   current intent prevented
```

Fresh geometry/risk/target/chase invalidation prevents execution regardless of ratio.

## Controller lease/fencing

Cross-machine ownership requires a shared coordination mechanism satisfying the frozen contract:

```text
ControllerInstanceID
current holder
monotonic fencing epoch
lease expiry
renewal target 10s
TTL 30s
```

Every broker write freshly verifies holder + non-expired matching epoch.

A local file lock alone is insufficient for multi-laptop safety.

A standby that acquires an expired lease enters RECOVERING/RECONCILING first. It becomes PRIMARY READY only after broker/state/account/risk/session/execution reconciliation passes.

Stale epochs cannot write.

## Persistence implementation rules

Storage technology is an implementation choice, but required semantics are not:

- atomic/durable critical writes;
- schema versioning/migration handling;
- unresolved Execution Intent survival;
- risk-day/reset/cooldown survival;
- open-trade plan/original R survival;
- Opportunity/Episode lineage survival;
- Strategy Registry/learning/research portability;
- broker reconciliation after restart/restore;
- critical corrupt state never silently becomes empty safe state.

## Public backup / financial-secret invariant

Public backup may contain project intelligence needed for recovery.

Do not commit credentials/tokens/private keys that enable unauthorized financial action, authenticated account control or direct paid-service cost.

Financial-secret scanning should block unsafe publication. A publicly exposed authority-bearing credential must be rotated/revoked.

## Research/learning coding boundary

Research may propose configurations/strategies through approved declarative primitives. It may not:

- call broker writes;
- mutate hard risk/session/execution authority;
- self-promote to production;
- generate/eval/exec arbitrary Python;
- use future data in replay.

## Dashboard preservation

Do not remove useful prior operator facts: mode, symbol, Bid/Ask, spread, M5 timer, trend/structure, EMA20/50, RSI, ATR, signal/reason, risk/lot, daily P/L/limit, position 0/1, loss streak and open-trade context.

Add Decision, Execution, Learning, Backup and Health views without turning the dashboard into the owner of those states.

## Debugging order

When a trade did not happen:

```text
1. Account/DEMO guard/data valid?
2. Controller ownership valid?
3. Session/news permission clear?
4. Risk/daily lock/cooldown clear?
5. Previous order ambiguity/reconciliation clear?
6. Valid opportunity exists?
7. BUY vs SELL thesis/conflict?
8. Entry Timing ENTER vs WAIT/MISSED/INVALID?
9. Trade Plan/target room/RR valid?
10. Risk/lot/margin/position capacity valid?
11. Spread/price drift/fresh quote valid?
12. What exactly did Execution Permission Gate return?
```

Do not start by weakening the strategy threshold when the blocker is execution or state integrity.

## Safety invariants

- unknown critical financial/broker/order/controller state fails closed for broker writes;
- no score overrides hard safety;
- no lookahead;
- original R immutable;
- no blind duplicate retry;
- no second independent Gold risk position in V1;
- no external position ownership confusion;
- no multiple active writers;
- no critical-state reset after crash;
- no autonomous hard-safety mutation;
- no financial-secret leak.

## Implementation documentation rule

During each large phase, add the real module names/config/runtime call path/persistence/dashboard/tests to this guide and `60-engineering/MODULE_STRUCTURE.md`.

A feature section should eventually identify:

```text
Purpose
Authoritative doc
Primary module
Related modules
Config fields
Runtime call path
Persistence/state
Dashboard visibility
Replay/research parity
Tests
Known failure modes
Change checklist
```

Do not invent source filenames merely to make documentation look complete before implementation chooses them.
