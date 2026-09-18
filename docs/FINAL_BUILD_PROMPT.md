# GoldSwingTraderAI — Final Build Prompt

**Status:** PROVISIONAL — FINAL HANDOFF CANDIDATE  
**Version:** 0.8-design  
**Location:** `docs/` root. This is a whole-project implementation handoff, not a competing behavioural authority.

## Role

Implement **GoldSwingTraderAI**, a fresh XAUUSD/XAUUSDm trading system for meaningful intraday/open-session directional moves. Build the documented system; do not recreate a prior scalper or invent undocumented shortcuts.

Use `docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` for large implementation phases, phase completion and recovery after interrupted work.

## Authority order

1. `docs/00-foundation/SYSTEM_CONTRACT.md`
2. authoritative topic document for the feature
3. `docs/90-governance/DESIGN_DECISIONS.md`
4. `docs/90-governance/OPEN_QUESTIONS.md`
5. `docs/60-engineering/CODING_STANDARD.md` for source-code quality/complexity/dependency rules
6. `docs/60-engineering/MODULE_STRUCTURE.md`
7. `docs/CODER_GUIDE.md`
8. operator/testing/release supporting docs
9. this prompt as summary/handoff only

If authoritative documents conflict, resolve the documentation contradiction before coding the affected behaviour. Never silently guess a critical rule.

## Architecture that must survive implementation

- XAUUSD/XAUUSDm focused.
- H4 context, H1 direction, M15 opportunity/location, M5 entry timing.
- Completed candles own structural confirmation; no future-confirmed pivots/lookahead.
- Parallel specialist desks, not a long sequential filter chain.
- Independent BUY and SELL theses.
- Opportunity and Entry Timing are separate dimensions.
- Explicit conflict/Red-Team handling.
- Six initial V1 strategy families operate in parallel:
  1. Trend Pullback Continuation
  2. Breakout Expansion
  3. Breakout Retest Continuation
  4. Liquidity Sweep Reversal
  5. Failed Breakout Reversal
  6. Compression Expansion
- Candle/structure leads; EMA20/EMA50, RSI, ATR, FVG, OB and similar tools are supporting evidence rather than universal hard gates.
- Safety is binary authority outside soft scoring.
- Structural Trade Plan exists before monetary sizing.
- Original R is immutable.
- One centralized Execution Permission Gate owns final irreversible MT5 write permission.
- One-shot irreversible submission; ambiguous acknowledgement is reconciled, never blind-retried.
- One active execution controller per managed account/symbol.
- Persistent risk/order/trade/opportunity/research/learning state survives restart and laptop migration.
- Research/learning/invention cannot silently self-promote or bypass hard safety.

## Frozen coding and implementation style

The implementation must obey `docs/60-engineering/CODING_STANDARD.md`, which is **FROZEN FOR INITIAL IMPLEMENTATION**.

Primary engineering objective:

> **Use the minimum clear production-grade code that fully expresses the required behaviour and safety. Keep the runtime light, explicit, optimized enough for the real workload, professionally commented and easy to audit. Do not build unnecessary bulk.**

Mandatory implementation rules:

- target Python 3.11+;
- standard library first; keep runtime dependencies minimal;
- use the official `MetaTrader5` package for terminal integration;
- do not add pandas/web frameworks/ORM/task queues/ML stacks to the live runtime without a real requirement;
- keep heavier research dependencies isolated from production runtime;
- prefer pure typed functions for deterministic market/risk/math calculations;
- use classes only where real state/resource/lifecycle ownership exists;
- use dataclasses/enums/typed IDs where they protect domain semantics; do not wrap every primitive unnecessarily;
- build one verified snapshot and reuse derived facts rather than repeatedly hitting MT5 or recalculating the same EMA/ATR/structure facts in multiple desks;
- a fresh execution read remains mandatory where the execution contract requires it;
- avoid both a giant multi-thousand-line `bot.py` and hundreds of trivial micro-files;
- do not create speculative Factory/Service/Manager abstraction layers;
- comments/docstrings explain **why**, chronology, safety invariants and broker quirks; do not narrate obvious syntax;
- no broad silent exception swallowing; convert boundary failures into explicit safe states/reasons;
- keep logs concise/structured and redact authority-bearing secrets;
- keep configuration/policy values centralized; no scattered magic trading/risk constants;
- performance work should remove duplicate reads/calculations and unbounded work before attempting clever micro-optimization;
- tests protect frozen behaviour, safety and regressions rather than padding test counts;
- safety code should remain deliberately boring and step-by-step rather than clever/metaprogrammed.

Before completing each phase, review code for dead code, duplicate calculations, unnecessary abstraction, mixed-responsibility modules, vague names, needless dependencies, silent exception handling, missing safety comments and noisy/sensitive logging.

Do **not** weaken a documented behaviour or safety rule merely to keep the source shorter.

## Positive DEMO guard — V1

V1 defines one environment rule only:

```text
Connected MT5 account verified DEMO
→ DEMO_GUARD = PASS
```

Broker writes may proceed only when this guard and every other required execution authority pass.

If DEMO status is not verified, broker-write permission is not granted.

Do **not** implement a separate REAL authorization system, REAL mode workflow, or V1 REAL hard-block contract. Do not scatter environment checks through strategies; the positive DEMO guard is one explicit input to the centralized execution-permission path.

## Initial frozen risk policy

```text
Profile  Equity Range            Normal Risk   Elevated Risk    Entry Ceiling   Daily Lock
SMALL    >0 and < $300           3.0–4.5%      >4.5–6.5%        7%              12%
MEDIUM   $300–$999.99            2.0–3.0%      >3.0–4.5%        5%               9%
NORMAL   $1,000+                 1.0–2.0%      >2.0–3.5%        4%               7%
```

Important rules:

- **There is no V1 `$100` minimum balance/equity floor.** Any positive DayStartEquity below `$300` is SMALL.
- `$99`, `$50`, `$30`, etc. do not become blocked merely because the account is below `$100`.
- Account size alone must not be added as an extra hard filter; actual executable risk geometry is authoritative.
- SMALL evaluates practical broker minimum volume such as `0.01`; a theoretical raw lot below minimum is not an automatic reject.
- Actual all-in risk of executable volume decides affordability.
- If minimum volume makes the current plan exceed the SMALL `7%` new-entry ceiling, block that current plan without tightening SL; the opportunity may remain ARMED for a better natural entry.
- Never tighten/widen structural SL merely to fit a desired lot/risk.
- High strategy score does not increase monetary risk.
- Profile is fixed from positive DayStartEquity for the UTC risk day rather than switching because of intraday floating P/L.
- V1 capacity is `0/1`: one independently risk-bearing Gold position.
- Manual/foreign/unknown-owner Gold exposure blocks a new bot Gold entry and is never managed as bot-owned.
- Daily loss accounting uses cash-flow-adjusted verified account equity so floating account drawdown counts.
- Manual loss reset is OFF by default; if explicitly enabled, maximum one governed `R,R` reset per UTC risk day.
- One ordinary loss does not create a global cooldown.
- At most one genuinely fresh same-Market-Episode re-entry; a second loss in that episode locks it.
- Three consecutive closed bot losses trigger at least 30 minutes cooldown plus fresh completed M15 context and a fresh opportunity before release.
- Generic margin estimates are diagnostic only; exact broker-required margin is authoritative when available and must be freshly revalidated before execution.

Items explicitly classified as research calibration or later-version work in `OPEN_QUESTIONS.md` must not block V1 implementation.

## Trade Plan, target and runner policy

No fixed 100/200/300-pip take-profit system.

Initial structural RR guard:

```text
<1.20R          → reject current plan
1.20R–<1.50R    → conditional; credible ~2R+ expansion path required
1.50R–<2.00R    → good
2.00R+          → strong
3R/4R+          → runner potential, not guaranteed
```

Target roles:

- Immediate Obstacle;
- Primary Structural Target — normally management checkpoint;
- Expansion Target — default initial broker TP when valid;
- Runner Objective — only after fresh continuation/acceptance evidence and a newly defined objective.

V1 core management must work correctly with one indivisible `0.01` position; partial profit is not required.

## Open-trade management

Open trades are evaluated through parallel continuation/reversal/protection/target evidence and one of:

```text
HOLD
PROTECT
TRAIL
RUNNER
EXIT
```

Do not close a healthy Gold expansion merely because a tiny profit threshold was reached. Protection/trailing should primarily follow confirmed structure with appropriate volatility/noise buffering.

A stop may tighten; it must not intentionally widen beyond original approved risk.

## Scheduled closure / reopen policy

V1 does not intentionally carry bot-managed Gold through known scheduled XAU closure/reopen gap risk.

```text
Daily break:
T-20m  no new entry
T-10m  mandatory governed flatten
Reopen normalized + at least 1 clean completed M5

Weekend:
T-60m  no new entry
T-30m  mandatory governed flatten
Reopen gap assessment + normalized conditions + at least 2 clean completed M5
```

Timing is relative to the verified broker Gold session schedule, not a guessed fixed clock. PRE_CLOSE flatten overrides runner logic.

If close result is ambiguous or broker becomes unavailable, persist unresolved exposure and reconcile; never fake a closed position.

## News safety

Initial V1 policy:

```text
TIER 1 CRITICAL  → -15/+15 min hard new-entry blackout
TIER 2 HIGH      → -5/+5 min hard new-entry blackout
TIER 3 CONTEXT   → no automatic hard blackout
```

Known linked Tier-1 clusters remain blocked through final critical item +15 minutes.

Scheduled news does not automatically force-close an existing managed trade.

After blackout, resume promptly when required facts/quotes/spread/data normalize. Severe post-event dislocation requires at least one clean completed M5 plus normalized execution conditions. Missing required event truth becomes `NEWS_SAFETY_UNKNOWN` rather than silent clear.

## Spread and price drift

Use a healthy broker/symbol spread baseline from valid normal observations.

```text
SpreadRatio <=1.50        → NORMAL
>1.50–2.25                → ELEVATED + full revalidation
>2.25                     → current entry prevented
spread >25% of SL distance→ current entry prevented
```

Adverse price drift from Approved Entry Reference, normalized by planned structural stop distance:

```text
<=10%       → normal revalidation
>10–20%     → elevated full revalidation
>20%        → current intent prevented; WAIT/rebuild if thesis survives
```

Any fresh quote that breaks hard risk, stop geometry, target room or chase validity prevents the current execution regardless of ratio.

## Central execution permission and broker-write path

All create/modify/close actions pass through one auditable boundary conceptually equivalent to `ExecutionPermissionGate` / `BrokerWriteGuard`.

Inputs include authoritative results for:

```text
DEMO guard
account identity
market/data/quote integrity
news/session permission
risk
position capacity/ownership
order lifecycle/reconciliation
controller ownership
fresh broker execution checks
```

Output must expose:

```text
ALLOW / BLOCK / UNKNOWN
Primary Reason
Secondary Reasons
Would Otherwise Trade where meaningful
```

Raw MT5 irreversible calls must not be reachable directly from strategy, scoring, timing, Trade Plan, dashboard, research, learning or autonomous-invention code.

Before send, persist a durable Execution Intent. One intent allows at most one irreversible send until reconciliation proves the outcome and a fresh governed intent is authorized.

## Controller / second-laptop policy

V1 uses a shared cross-machine controller lease with fencing:

```text
one PRIMARY
renewal target 10 seconds
lease TTL 30 seconds
monotonic fencing epoch
fresh controller ownership required before every broker write
```

A second laptop remains read-only/Observer while another valid controller exists.

Standby takeover may occur only after authoritative lease expiry, must obtain a new epoch atomically, then enter recovery/reconciliation. It does not become PRIMARY READY until broker/state/account/risk/session/execution reconciliation passes.

A returned old primary with a stale epoch cannot write.

Coordination uncertainty fails closed for irreversible broker writes.

## Persistence and broker truth

Broker is authority for current positions/orders/deals/account facts. Local state owns intent, strategy context and lifecycle history.

Persist/recover at least:

- UTC risk-day state, loss lock/reset/cooldown;
- Execution Intents and unresolved order lifecycle;
- bot-managed open-trade plan, original R, SL/TP/objectives;
- Opportunity and Market Episode lineage;
- journals/performance;
- Strategy Registry and Champion/Challenger/Shadow/Canary/Rejected history;
- StrategyMemory and entry/exit learning;
- research/invention/promotion history;
- state schema/integrity/backup metadata.

Restart/migration never means blank financial/order state. Reconcile broker truth before new entries.

## Public backup / financial-secret policy

The public repository may back up source, docs, strategies, learned parameters, autonomous candidates, performance/research history and portable recovery intelligence.

Never commit authority-bearing secrets capable of financial action, authenticated account control or direct paid-service cost, including trading passwords, private broker/session tokens, paid API keys, GitHub PATs, private/signing keys or paid cloud/database credentials.

Run a financial-secret scanner before public backup. Detection should block publication with an explicit reason such as `FINANCIAL_SECRET_DETECTED`.

If a financial credential is accidentally committed publicly, removal alone is insufficient; revoke/rotate it.

## Research, learning and autonomous improvement

Research should automatically analyze taken, missed, blocked/rejected and invalidated opportunities where practical.

Required principles:

- chronological/no-lookahead replay;
- independent validation/holdout/stress as documented;
- MFE/MAE, realized R and move-capture efficiency;
- entry quality and premature-exit/profit-giveback analysis;
- large-move recall;
- StrategyMemory remains bounded;
- autonomous candidates are declarative/bounded, never arbitrary executed Python;
- candidates cannot change hard risk/broker authority;
- production promotion is governed and cannot occur silently.

Research-calibration values listed in `OPEN_QUESTIONS.md` should be explicit/configurable and tuned through evidence rather than guessed as hidden constants.

## Dashboard requirements

Preserve useful prior GoldScalperAI visibility rather than removing it:

- runtime mode/role;
- XAU symbol;
- Bid/Ask;
- spread + quality;
- M5 candle timer;
- trend/structure;
- EMA20/EMA50 relation;
- RSI;
- ATR;
- signal/action + exact reason;
- risk profile, risk and lot;
- daily P/L/limit/remaining budget;
- position count/capacity;
- loss streak/cooldown;
- open trade entry/SL/TP/objectives.

Add compact Decision, Execution, Learning, Backup and System Health panels. Dashboard observes authoritative state; it does not own trading decisions.

## Prohibited shortcuts

Do not:

- turn every soft signal into a hard gate;
- require every indicator/SMC primitive for every trade;
- treat missing optional evidence as score zero;
- let score override risk/news/account/data/execution safety;
- use future candles/future-confirmed pivots;
- move structural SL to fit desired risk;
- redefine original R after trailing;
- invent an arbitrary `$100` or other positive-equity minimum trading floor for SMALL accounts;
- open automatic second Gold position/hedge in V1;
- manage manual/foreign exposure as bot-owned;
- blind-retry ambiguous broker writes;
- assume unknown broker/order/P&L/exposure truth is safe/zero;
- bypass the centralized write gate;
- let two controllers write simultaneously;
- silently reset critical state after crash/corruption;
- allow research/AI to self-promote or modify hard safety;
- generate/eval/exec arbitrary autonomous Python;
- leak financial-authority secrets;
- introduce unnecessary abstractions/dependencies/frameworks that make the runtime harder to audit or operate;
- duplicate expensive market calculations/MT5 reads when a verified shared result already exists;
- treat calibration/ordinary implementation choices as reasons to stall the entire build.

## Large implementation sequence

Use `docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` as the operational phase guide:

1. Foundation/package/contracts
2. MT5 read layer + market data
3. Full market intelligence
4. Strategy floor + BUY/SELL fusion + entry timing
5. Trade Plan + Risk Engine
6. Session/news + persistence/recovery foundation
7. Execution gate + controller + governed MT5 writes
8. Trade Manager + runner/exit
9. Dashboard + operator workflows
10. Replay/research/learning/autonomous lab
11. Backup/migration/fault-recovery drill
12. Full integration + controlled DEMO certification + release audit

After every coherent phase, code, tests and relevant documentation must agree before proceeding.

## Validation principles

- Documentation completion is not implementation proof.
- Static checks are not runtime proof.
- Software correctness is not profitability proof.
- Historical results do not guarantee future profit.
- Replay claims require chronological no-lookahead proof.
- Irreversible broker writes require duplicate-prevention/fault-injection/restart evidence.
- Backup existence is not recovery proof; fresh-machine restore must be tested.
- Learning/promotion must prove production cannot silently mutate.
- Dashboard/reason traces are tested behaviour, not decoration.
- Passing tests does not excuse unnecessary complexity that violates the frozen Coding Standard.

## Implementation readiness

`docs/90-governance/OPEN_QUESTIONS.md` classifies remaining items as frozen direction, research calibration, implementation choice, operator detail or later-version work. Research calibration and ordinary implementation choices are **not** reasons to delay the build.

Before treating this prompt as FROZEN, perform one final cross-document contradiction/coverage audit. After that audit, implementation may proceed in the large phases above without reopening already frozen decisions unless the user explicitly changes them or evidence requires a governed revision.
