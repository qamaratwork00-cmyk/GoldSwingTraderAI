# GoldSwingTraderAI — ChatGPT Project Build and Recovery Guide

**Status:** PROVISIONAL  
**Version:** 1.1-design  
**Authority:** Whole-project implementation sequencing, phase completion, resume/recovery and build-navigation process. This file does **not** redefine trading behaviour.

## Purpose

This guide exists so ChatGPT or another implementation agent can complete GoldSwingTraderAI quickly in large coherent phases, recover after interruption/context loss, and avoid restarting or guessing when something goes wrong.

Core rule:

> **Recover project truth from the repository, repair the smallest broken layer, verify it, then continue from the last verified phase. Do not restart the whole project unless the repository/state is genuinely unrecoverable.**

## Source-of-truth order

When starting, resuming or recovering work, read in this order:

1. `README.md`
2. `docs/README.md`
3. `docs/00-foundation/SYSTEM_CONTRACT.md`
4. relevant authoritative topic document
5. `docs/90-governance/DESIGN_DECISIONS.md`
6. `docs/90-governance/OPEN_QUESTIONS.md`
7. `docs/60-engineering/CODING_STANDARD.md`
8. `docs/60-engineering/MODULE_STRUCTURE.md`
9. `docs/CODER_GUIDE.md`
10. `docs/FINAL_BUILD_PROMPT.md`
11. this guide
12. current code, tests, state schema, latest commits and executable evidence

If docs conflict, stop the affected implementation path and resolve the contradiction in the authoritative docs first. Do not silently pick whichever rule is easiest to code.

## Frozen implementation-quality rule

Every implementation phase must obey `docs/60-engineering/CODING_STANDARD.md`.

The build target is not merely code that works; it is **lightweight production-grade code** that is clear, auditable and efficient enough for the actual workload without unnecessary architecture.

Before a phase closes, review affected code for:

```text
duplicate MT5 reads / duplicate derived calculations
unnecessary abstraction / speculative classes
mixed-responsibility oversized modules
dead code
scattered magic thresholds
vague names
missing safety/chronology comments
broad or silent exception handling
needless runtime dependencies
noisy or secret-leaking logs
weak tests around frozen invariants
```

Do not perform cosmetic rewrites for their own sake, but do not allow known avoidable bulk/complexity to accumulate phase after phase.

## Large implementation phases

The project should be built in **large phases**, not dozens of tiny disconnected tasks.

### PHASE 1 — Foundation, package skeleton and contracts

Build the real package layout, configuration system, IDs/enums/domain models, reason codes, immutable contracts, logging/journal foundation and DEMO guard input.

Deliverables:
- runnable package skeleton;
- configuration validation;
- common domain models;
- deterministic IDs/version metadata;
- basic structured logging;
- secret-safe config pattern;
- initial unit-test harness;
- frozen Coding Standard applied to the initial source skeleton.

Exit gate: package imports/runs, config errors fail clearly, secrets are not committed, core contracts have tests, and the initial code passes the Coding Standard quality review.

### PHASE 2 — MT5 read layer, Gold symbol facts and market data

Build MT5 connection/read adapter, XAUUSD/XAUUSDm resolution, broker symbol facts, Bid/Ask, history loading, H4/H1/M15/M5 synchronization, completed-candle chronology and data-quality checks.

Prefer one normalized verified snapshot and reusable derived inputs rather than repeated MT5 calls in downstream components.

Exit gate: verified DEMO account/symbol facts, deterministic candle snapshots, stale/missing data states, no-lookahead data tests, no duplicate unnecessary MT5 read paths.

### PHASE 3 — Full market intelligence

Build Candle Structure, Technical Structure/Levels, Liquidity/SMC, EMA/RSI/ATR/volatility, session context and fundamental/news fact adapters.

Compute deterministic facts once per appropriate snapshot/scope and share typed results rather than re-running the same indicator/structure work independently in every strategy.

Exit gate: every desk publishes typed evidence from the same snapshot; no desk gains broker authority; chronological replay parity tests pass for implemented logic; unnecessary duplicated calculations are removed.

### PHASE 4 — Strategy floor, BUY/SELL theses and decision fusion

Implement the six V1 strategy families in parallel, independent BUY and SELL theses, evidence coverage, conflict/Red-Team handling, Opportunity lifecycle and Entry Timing.

Exit gate: no filter-soup pipeline; valid setup can remain ARMED/WAIT; reasons for WAIT/MISSED/INVALID are deterministic and testable; strategy code remains direct rather than framework-heavy.

### PHASE 5 — Trade Plan, targets and Risk Engine

Implement structural invalidation/SL, volatility buffer, objective hierarchy, immutable original R, frozen RR guard, hybrid account-size sizing, minimum-lot handling, daily Account Safety P/L, loss lock, manual reset and cooldown.

Exit gate: structural stop is never distorted to fit risk; all-in risk is broker-aware; profile ceilings/daily locks and original R invariants pass tests; risk code remains explicit/auditable.

### PHASE 6 — Session/news safety, persistence and recovery foundation

Implement news states/windows, PRE_CLOSE/reopen rules, durable risk/order/trade/opportunity state, schema/versioning, atomic writes, restart reconstruction and broker reconciliation primitives.

Use the smallest persistence stack that safely satisfies the frozen requirements; do not introduce an ORM/service layer without a real need.

Exit gate: restart does not erase risk/order state; scheduled close/reopen policy is testable; corrupt/unknown critical state fails safely.

### PHASE 7 — Central execution gate, controller lease and MT5 writes

Implement one centralized Execution Permission Gate, positive DEMO guard, account identity pinning, spread/drift checks, margin/stop/volume checks, controller lease/fencing, durable Execution Intent, one-shot create/modify/close and ambiguous-result reconciliation.

Keep safety code intentionally direct and easy to audit.

Exit gate: raw irreversible MT5 writes exist only behind the governed boundary; duplicate/fault-injection tests pass; second controller cannot write; DEMO execution works only when all required authorities pass.

### PHASE 8 — Trade Manager, structural protection and runner

Implement HOLD/PROTECT/TRAIL/RUNNER/EXIT, structure-led trailing, objective progression, reversal evidence and mandatory PRE_CLOSE flatten integration.

Exit gate: profit is not cut by arbitrary tiny thresholds; stop never widens beyond original risk; runner extension needs fresh structural evidence; pre-close flatten overrides runner.

### PHASE 9 — Dashboard and operator workflows

Implement the compact dashboard and preserve useful GoldScalperAI observability: mode, symbol, Bid/Ask, spread, M5 timer, trend/structure, EMA20/50, RSI, ATR, signal/reason, risk/lot, daily P/L/limit, loss streak, position 0/1 and open-trade context. Add Decision, Execution, Learning, Backup and Health visibility.

Update `docs/USER_MANUAL.md` and `docs/SETUP_AND_RUN_GUIDE.md` with real commands/keys only after they actually exist.

Dashboard refresh remains presentation work and must not duplicate strategy/order triggering.

Exit gate: operator can understand exactly why the bot is WAIT/ENTER/BLOCKED and what state requires action.

### PHASE 10 — Replay, research, learning and governed invention

Implement deterministic chronological replay, taken/missed/blocked/invalidated metrics, MFE/MAE/capture efficiency, Entry/Exit Learning, StrategyMemory, candidate registry, declarative strategy discovery/invention and promotion stages.

Research may use heavier analytical libraries when justified, but these must remain isolated from normal production runtime dependencies.

Exit gate: no lookahead; learning cannot mutate hard safety; candidates cannot self-promote or execute arbitrary Python.

### PHASE 11 — Backup, migration and fault-recovery drill

Implement portable state export/checkpoint, financial-secret scanner, backup verification, fresh-machine restore workflow and controller handoff/failover verification.

Exit gate: a fresh machine can restore project intelligence, configure credentials separately, reconcile MT5 and safely resume without duplicate exposure.

### PHASE 12 — Full integration, DEMO certification and release audit

Run end-to-end tests, replay, broker fault injection, restart tests, scheduled-close tests, news tests, controller split-brain tests, dashboard checks and controlled MT5 DEMO forward certification.

Exit gate: required evidence exists in `TESTING_AND_VERIFICATION.md`, `RELEASE_CHECKLIST.md` and `FINAL_RELEASE_AUDIT.md`. Only then may implemented/verified statuses be promoted honestly.

## Phase completion rule

A phase is complete only when all five are true:

```text
CODE EXISTS
+ REQUIRED TESTS PASS
+ FROZEN CODING STANDARD QUALITY REVIEW PASSES
+ DOCUMENTATION MATCHES CODE
+ NO KNOWN CRITICAL CONTRADICTION
```

After every coherent phase update, as applicable:
- authoritative topic document;
- `docs/90-governance/DESIGN_DECISIONS.md`;
- `docs/90-governance/OPEN_QUESTIONS.md`;
- `docs/60-engineering/CODING_STANDARD.md` only if a governed engineering-standard change is explicitly approved;
- `docs/60-engineering/MODULE_STRUCTURE.md`;
- `docs/CODER_GUIDE.md`;
- operator docs;
- testing/release docs;
- `docs/README.md`.

Do not postpone known documentation mismatch to the end.

## What to do if conversation/context is lost

Do not ask the user to reconstruct the whole project from memory.

Recovery sequence:

```text
inspect repository tree
→ read docs/README.md
→ read SYSTEM_CONTRACT
→ read DESIGN_DECISIONS
→ read OPEN_QUESTIONS
→ read CODING_STANDARD
→ read MODULE_STRUCTURE + CODER_GUIDE
→ read FINAL_BUILD_PROMPT + this guide
→ inspect latest code/tests/commits
→ identify last phase whose exit gate is actually satisfied
→ continue from first incomplete phase
```

Repository truth beats remembered conversation wording when the repository contains the later accepted decision.

## What to do if code is incomplete or a phase was interrupted

1. Identify the active phase.
2. Compare its required deliverables against repository files/tests.
3. Mark each deliverable `DONE`, `PARTIAL`, `MISSING`, or `BROKEN` privately/in the work log.
4. Finish the smallest missing dependency first.
5. Run focused tests.
6. Run that phase's integration tests.
7. Run the Coding Standard quality review on affected code.
8. Sync docs.
9. Continue; do not rewrite already verified subsystems without cause.

## What to do if something important was missed

If a requirement is discovered late:

```text
find authoritative home
→ determine affected phases/modules
→ add/adjust decision/open-question record if material
→ implement smallest correct cross-cutting change
→ add regression test proving the miss cannot recur
→ update operator/coder docs if visible
→ rerun downstream affected tests
```

Never hide the miss by changing only the dashboard or comments.

## What to do if docs and code disagree

Classify the mismatch:

- **code bug** — frozen doc is correct; fix code;
- **doc stale** — code implements an explicitly accepted later decision; update authoritative doc/ledger;
- **true unresolved conflict** — stop affected feature, resolve decision, then code.

Do not label code `VERIFIED` while a known authoritative mismatch exists.

## What to do if tests fail

Do not disable or weaken a safety test merely to make the suite green.

Use this order:

```text
reproduce deterministically
→ identify authority/invariant being tested
→ isolate smallest failing layer
→ fix root cause
→ add regression coverage
→ run focused suite
→ run phase suite
→ run relevant cross-phase safety suite
```

A flaky broker/network test should be separated from deterministic logic tests, not deleted.

A passing test suite is necessary but does not by itself prove the code is acceptably simple/maintainable; the Coding Standard quality review remains part of the phase gate.

## What to do if GitHub/local state differ

1. Stop new irreversible broker actions if the running code/version is uncertain.
2. Identify commit/version currently executing.
3. Preserve uncommitted local changes/state/checkpoints.
4. Compare local code to repository version.
5. Never overwrite live mutable trading state blindly from Git.
6. Reconcile broker truth after code/state restoration.
7. Resume only from a known code + schema + state combination.

## What to do if persistent state is missing/corrupt

Critical order/risk/trade state must not silently reset to empty.

```text
STATE CORRUPT/MISSING
→ block affected new broker writes
→ preserve evidence
→ restore last verified checkpoint if available
→ connect MT5
→ reconcile positions/orders/deals
→ rebuild market intelligence chronologically
→ reconstruct only what broker/history + durable evidence can prove
→ remain BLOCKED/RECONCILING for unresolved critical facts
```

Optional learning state may fall back to frozen baseline behaviour only where the authoritative persistence/learning contracts allow it.

## What to do after a crash during broker write

If an Execution Intent was `SUBMITTING` or acknowledgement is ambiguous:

```text
DO NOT RESEND
→ restore intent
→ query broker positions/orders/deals
→ reconcile lineage/time/symbol/volume
→ classify accepted/failed/unresolved
→ only then allow a fresh governed intent
```

One-shot execution is more important than convenience.

## New-laptop / disaster recovery

```text
clone repository
→ install verified runtime/dependencies
→ restore portable state/checkpoint
→ configure financial credentials separately
→ run financial-secret scan/integrity checks
→ connect intended MT5 DEMO environment
→ validate account/symbol
→ acquire controller lease/epoch
→ reconcile broker truth
→ rebuild market intelligence
→ verify risk/session/news state
→ run startup self-tests
→ READY
```

A backup never proves there is no open broker position. MT5/broker reconciliation is mandatory.

## Fast-work rule

To finish quickly without sacrificing correctness:

- work in the large phases above;
- batch related files/tests/doc updates;
- follow the frozen Coding Standard instead of repeatedly redesigning source style;
- prefer the smallest implementation that fully satisfies the authoritative contract;
- avoid repeated cosmetic refactors during implementation;
- choose ordinary libraries/file layouts as implementation choices where `OPEN_QUESTIONS.md` permits it;
- calibrate market thresholds through replay/research instead of blocking the build;
- do not reopen already frozen decisions unless evidence or the user explicitly changes them.

## Definition of project complete

GoldSwingTraderAI is not complete merely because `bot.py` runs.

Project completion requires:

- all required phases implemented;
- authoritative docs synchronized;
- frozen Coding Standard respected across production source;
- no known safety bypass;
- no-lookahead replay evidence;
- risk/session/news/execution invariants tested;
- one-shot order/reconciliation tested;
- controller/failover tested;
- restart and fresh-machine recovery tested;
- financial-secret scan passing;
- dashboard/operator workflow usable;
- controlled DEMO certification completed;
- final release audit evidence recorded.

Profitability is evaluated through research/DEMO evidence and is never guaranteed by software completion.

## Final recovery principle

> **When uncertain: inspect, reconcile, verify, then continue. Never guess critical financial/broker state, never replay a stale open-trade assumption, and never restart the entire project just because one phase failed.**
