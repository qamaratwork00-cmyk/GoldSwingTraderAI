# GoldSwingTraderAI — Trade Manager and Exit

**Status:** PROVISIONAL
**Version:** 0.1-management
**Authority:** Post-entry management, structural protection and exit actions

## Purpose

Once a bot-owned position exists, the manager decides whether the original move
is healthy, needs protection, deserves extension or should exit. It is a second
decision floor, not a second broker writer.

## Management pipeline

~~~mermaid
flowchart TB
    TRADE["Verified broker position + durable ManagedTrade"] --> FACTS["Fresh market/intelligence/session facts"]
    FACTS --> SCORES["Continuation, reversal, structure, candle, momentum and path"]
    SCORES --> ACTION["HOLD / PROTECT / TRAIL / RUNNER / EXIT"]
    ACTION --> CHECK["Ownership, controller, quote and PRE_CLOSE checks"]
    CHECK --> INTENT["Durable MODIFY/CLOSE Intent"]
    INTENT --> BROKER["One governed broker operation"]
    BROKER --> VERIFY["Broker verification"]
    VERIFY --> STATE["Persist updated ManagedTrade"]
~~~

## Action meanings

| Action | Meaning | Minimum reason |
|---|---|---|
| HOLD | thesis remains healthy | no earned protection/exit reason |
| PROTECT | reduce risk using earned structure | progress plus valid structural reference |
| TRAIL | tighten behind proven structure | new tighter reference |
| RUNNER | extend objective | acceptance/continuation plus new objective |
| EXIT | close failed/exhausted/unsafe trade | meaningful reversal, collapse or mandatory safety |

One opposite candle, a small profit or touching Primary does not automatically
exit a healthy move. PRE_CLOSE flatten does override HOLD/RUNNER.

## Stop and objective rules

Protection/trailing follows confirmed structure and volatility buffer. A new
stop may tighten but must not intentionally widen beyond original approved
risk. A normal hierarchy is M5 protected swing, then M15 structure, then H1
runner structure where it still tightens.

Primary is a checkpoint. Expansion is the normal initial objective. A runner
requires:

- previous objective is accepted/broken rather than rejected;
- structure and continuation remain healthy;
- reversal is limited;
- a fresh objectively defined target exists;
- session/execution conditions remain safe.

Profit alone cannot extend TP. Only one active Runner Objective exists at a
time. V1 does not require partial closes.

## Exit conditions

Normal EXIT needs meaningful combinations such as material M15 failure, failed
reclaim, opposing displacement/MSS, target-path exhaustion or continuation
collapse. A scheduled PRE_CLOSE flatten is an explicit safety exit and does not
need reversal evidence.

Ambiguous close/modify acknowledgement leaves the local trade state unresolved
until reconciliation; it is not marked closed by assumption.

## Implementation and tests

| Source | Role | Tests |
|---|---|---|
| management/models.py | typed action/evidence/trade models | test_trade_manager.py |
| management/manager.py | action decision | test_trade_manager.py |
| management/store.py | durable ManagedTrade | test_management_execution.py, test_persistence_recovery.py |
| management/execution.py | verified modify/close bridge | test_management_execution.py |
| research/management_replay.py | historical management semantics | test_management_replay.py |

## Dashboard and research

Show original/current SL/TP separately, objective stage, current R, action and
reason. Research measures MFE, MAE, Capture Efficiency, premature-exit cost,
Primary→Expansion and Expansion→Runner progression, plus PRE_CLOSE outcomes.

## Explicit non-goals

Management does not create a new entry thesis, change original R, bypass risk,
modify foreign positions, call raw order_send or require a fixed pip exit.

