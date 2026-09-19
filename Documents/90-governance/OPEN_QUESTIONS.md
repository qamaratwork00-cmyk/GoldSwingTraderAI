# GoldSwingTraderAI — Open Questions and Closure Plan

**Status:** CANDIDATE FOR ADOPTION  
**Version:** 0.1-open-questions  
**Authority:** Unresolved choices, required evidence and completion boundaries

## 1. Why this file exists

An open question is not automatically a design failure. Some questions require
an implementation choice, some require historical calibration, and some can
only be answered in the real DEMO environment. Keeping them visible prevents
unfinished external proof from being mistaken for missing architecture.

Every question belongs to one closure class.

| Class | Meaning | Closure method |
|---|---|---|
| FIX BEFORE BUILD | Safety or ownership cannot be safely guessed | Decide in the contract and test it |
| IMPLEMENTATION CHOICE | Several safe implementations are possible | Choose one, document the boundary and test it |
| CALIBRATE IN RESEARCH | Architecture is fixed but numbers need evidence | Replay, stress, walk-forward and holdout |
| EXTERNAL PROOF | Only a real terminal, broker or machine can answer it | Run and retain an evidence package |
| DEFERRED V1 | Intentionally outside current scope | Keep blocked and do not let it leak into V1 |

## 2. Questions that must be fixed before release

| ID | Question | Why it matters | Owner/evidence |
|---|---|---|---|
| Q-001 | Which external provider publishes the session schedule and news facts? | Missing or stale provider data changes hard permission | Provider contract plus tests |
| Q-002 | What is the approved provider freshness and failure policy? | UNKNOWN must map to a deterministic safety state | Session/news contract |
| Q-003 | What shared coordination backend is used for two-machine failover? | Local SQLite alone cannot prove independent-machine fencing | Coordination drill |
| Q-004 | Which broker/account schedule is the release target? | Close/reopen and holiday rules are broker-specific | DEMO evidence |
| Q-005 | Which exact account/server/symbol identity is approved for certification? | DEMO Guard must verify identity, not only account mode | Redacted configuration and log |

## 3. Questions to answer through research

| ID | Question | Required evidence |
|---|---|---|
| Q-101 | What H1/M15/M5 thresholds produce stable structure and timing behaviour on XAU? | Chronological replay and walk-forward |
| Q-102 | Which strategy-family combinations generalize across market regimes? | Per-family outcomes, ablation and holdout |
| Q-103 | What confluence bonus is useful without overriding structure or safety? | Ablation, calibration and negative cases |
| Q-104 | What spread, slippage and price-drift distributions are realistic for the target broker? | Real DEMO observations plus historical model |
| Q-105 | How should ATR, volatility and extension thresholds adapt? | Regime-separated calibration and stress |
| Q-106 | What target hierarchy and runner policy improve risk-adjusted outcomes? | Management replay and outcome metrics |
| Q-107 | What walk-forward window sizes are statistically and operationally useful? | Multiple window sensitivity reports |
| Q-108 | What promotion thresholds are appropriate for the initial account profile? | Holdout evidence and risk review |
| Q-109 | Which StrategyMemory features improve decisions without leakage? | Feature lineage, ablation and baseline comparison |
| Q-110 | Which governed discovery primitives remain useful under complexity limits? | Candidate registry, replay, holdout and rollback package |

Numerical values are not “missing coding”. They must not be invented to make a
research question look closed.

## 4. Implementation choices still needing an explicit record

| ID | Question | Safe default until decided |
|---|---|---|
| Q-201 | How often should the persistent loop poll while the market is closed? | Keep the process alive with the configured readiness poll |
| Q-202 | How should dashboard frames be exposed to a future web UI? | Keep a pure DTO/rendering boundary; do not add authority to the UI |
| Q-203 | What retention period applies to operational logs and backup manifests? | Keep immutable evidence needed by the release/audit policy |
| Q-204 | How are schema migrations versioned? | Reject incompatible records rather than silently coercing them |
| Q-205 | Which public backup repository/artifact channel is authoritative? | Stage locally, scan, fingerprint and publish only after explicit approval |

## 5. External proof still required

| ID | Drill | Pass condition |
|---|---|---|
| Q-301 | Fresh Windows machine setup | Installation, configuration and launch work from the guide |
| Q-302 | Current MT5 data freshness | Quote and every required completed candle meet policy |
| Q-303 | DEMO OPEN | Intent, broker acknowledgement, ticket and reconciliation agree |
| Q-304 | DEMO MODIFY | Stop/target change is broker-verified and durable |
| Q-305 | DEMO CLOSE and restart | Final position truth survives close/restart without duplicate writes |
| Q-306 | Fresh-machine restore | Checkpoint restores into a new database and reconciles truth |
| Q-307 | Stale-primary fencing | Old process cannot write after lease/epoch invalidation |
| Q-308 | Two-machine takeover | Standby becomes primary only under the coordination policy |
| Q-309 | Public backup publication | Artifact is scan-clean, fingerprinted and retrievable |
| Q-310 | Historical XAU calibration | Broader data sample produces a reproducible evidence package |

## 6. Intentionally deferred

| ID | Deferred capability | Why it is not V1 |
|---|---|---|
| D-001 | REAL/live authorization | V1 is DEMO-only by decision |
| D-002 | Multiple simultaneous Gold positions | One-position capacity is the conservative V1 boundary |
| D-003 | Partial-close dependency | V1 management must work without relying on it |
| D-004 | M1 as an independent Swing signal | M1 is execution health/diagnostic context only |
| D-005 | Unbounded autonomous code generation | Discovery/invention remains governed and promotion-gated |
| D-006 | Silent migration of unknown state | Unknown broker exposure and corrupt state must block |

## 7. Closure rule

When a question is closed:

1. update this file;
2. update the authoritative topic document;
3. update the design decision ledger if the choice is durable;
4. update source/test maps;
5. add or update the evidence reference;
6. update every affected diagram and operator instruction;
7. run the documentation and test gates.

Closing a question in chat or in a commit message alone is not sufficient.
