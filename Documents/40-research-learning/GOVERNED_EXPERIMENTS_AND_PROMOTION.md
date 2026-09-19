# GoldSwingTraderAI — Experiments and Promotion

**Status:** PROVISIONAL
**Version:** 0.1-promotion
**Authority:** Champion/challenger evidence stages, holdout, canary and rollback

## Purpose

A candidate becomes production policy only through a staged, reversible,
evidence-backed process. A candidate cannot approve itself.

## Lifecycle

~~~mermaid
stateDiagram-v2
    [*] --> PROPOSED
    PROPOSED --> RESEARCHING
    RESEARCHING --> VALIDATED
    VALIDATED --> LOCKED
    LOCKED --> HOLDOUT_PASSED
    HOLDOUT_PASSED --> STRESS_PASSED
    STRESS_PASSED --> SHADOW
    SHADOW --> DEMO_CANARY
    DEMO_CANARY --> PROMOTION_READY
    PROMOTION_READY --> PROMOTED: explicit approval + rollback target
    RESEARCHING --> REJECTED
    VALIDATED --> HOLDOUT_FAILED
    HOLDOUT_PASSED --> STRESS_FAILED
    PROMOTED --> ROLLED_BACK
    PROMOTED --> DISABLED
~~~

## Stage meaning

| Stage | Question | Broker authority |
|---|---|---|
| research/validation | does the candidate improve the declared objective without leakage? | none |
| LOCKED | is semantic fingerprint frozen? | none |
| final holdout | does the unchanged candidate survive untouched data? | none |
| stress | does it survive declared friction/regime/missing optional evidence? | none |
| shadow | does live timing look plausible with no orders? | none |
| DEMO Canary | does the terminal lifecycle behave safely? | normal DEMO path only |
| promoted | has explicit approval accepted it? | still normal hard gate |

## Holdout rule

LOCKED stores a semantic SHA-256 fingerprint. The final holdout identity is
durable and may be consumed once. A changed candidate needs a new version and
new evidence cycle.

## Champion/challenger and rollback

Champion is the approved policy. Challenger is compared with Champion, not
zero. PROMOTION_READY is not authority. Promotion requires explicit approval
and a known rollback target. Rollback/disable is durable and reasoned; a short
ordinary losing streak is not automatic proof of failure.

## Objectives

Review Net/Avg R, drawdown, Profit Factor, Opportunity Recall, capture,
entry/exit quality, friction, trade frequency, complexity and stability.

## Source and tests

research/promotion.py owns the state machine and durable history. Tests are
test_promotion_governance.py and the research persistence suites.

## Explicit non-goals

No stage skipping, self-promotion, holdout reuse, silent open-trade semantic
change, failure erasure or direct broker authority.

