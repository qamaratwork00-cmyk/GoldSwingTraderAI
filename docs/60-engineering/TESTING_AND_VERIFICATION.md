# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 0.2-design  
**Authority:** Test taxonomy, executable proof requirements, replay/live parity, crash/restart, migration, learning-governance and release verification.  
**Depends on:** `../90-governance/DOCUMENTATION_STANDARD.md`, `../40-research-learning/RESEARCH_AND_VALIDATION.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`

## Purpose

Testing must prove documented invariants. `VERIFIED` is reserved for behaviour that actually passed its required executable validation against the exact implementation.

> **Software verification and strategy validation are separate.**

## Test layers

Expected layers include:

```text
Unit / Contract Tests
→ Component Tests
→ Deterministic Replay Tests
→ Integration Tests
→ Fault / Crash Injection
→ Persistence / Migration Tests
→ Broker DEMO Tests
→ Learning / Promotion Governance Tests
→ End-to-End DEMO Certification
```

## No-lookahead tests

Dedicated tests must prove:

- candidate swings may evolve;
- confirmed swings appear only at `confirmed_at`;
- wick-only probes do not become BOS/MSS;
- future candles/targets/FVG/OB/news revisions do not leak into earlier decisions;
- replay chronology matches documented availability.

Any future-data leakage is release-blocking.

## Replay/live parity

Where parity is claimed, replay and live paths should reuse the same frozen decision semantics. Tests should feed identical snapshots/events into shared logic and compare outputs.

Do not claim parity for intrabar features without adequate historical data.

## Strategy/decision tests

Each strategy family requires positive and negative fixtures. Tests should cover:

- valid narrative recognized;
- noisy lookalike rejected;
- BUY/SELL theses independent;
- conflict correctly represented;
- missing optional evidence is UNKNOWN/absent, not zero;
- correlated evidence is not repeatedly counted.

## Entry lifecycle tests

Must prove:

- `WAIT` preserves a valid setup;
- `MISSED` differs from `INVALID`;
- fresh second-chance events can re-arm;
- stale unchanged re-entry is rejected;
- chase/extension and price drift can defer entry without deleting thesis.

## Decision attribution tests

Every non-entry path should produce stable machine reason codes and authority trace.

Example expected output:

```text
Strategy PASS
Entry PASS
Trade Plan PASS
News PASS
Risk BLOCK: MIN_LOT_UNAFFORDABLE
Execution NOT_REACHED
Would otherwise trade: YES
```

The system must not collapse this into generic `NO TRADE`.

## Trade Plan tests

Cover:

- family-specific structural invalidation;
- volatility-aware buffer;
- Stop Quality;
- target hierarchy/RR;
- broker normalization cannot silently redesign thesis;
- price-drift degradation;
- immutable original R after trailing/restart.

## Risk tests

Use broker-spec fixtures to validate actual monetary risk and volume normalization.

Cover:

- dynamic lot sizing;
- min-lot unaffordability;
- aggregate risk/margin;
- daily loss lock;
- UTC risk-day rollover;
- manual reset audit/reference;
- cooldown/runaway protections;
- unknown financial state fails closed.

Manual reset must not bypass unrelated `BLOCKED` states.

## Centralized Execution Permission Gate tests

The final broker-write authorization boundary is an explicit tested feature, not an implementation detail.

Tests must prove the primary gate consumes authoritative environment/account/data/news/risk/position/order/controller/fresh-execution results and returns deterministic `ALLOW / BLOCK / UNKNOWN` plus stable reasons.

At minimum verify:

- DEMO authorized + all hard authorities PASS can produce ALLOW;
- current REAL account under DEMO-first policy produces BLOCK with explicit environment reason;
- future REAL authorization can be represented through the same gate/path without a second trading engine;
- any hard BLOCK input prevents broker write even when strategy/Trade Plan are excellent;
- required UNKNOWN safety input cannot silently become ALLOW;
- primary and secondary blocker reasons are preserved;
- create, modify and close all require the same governed authorization boundary;
- strategy, research, learning and dashboard code cannot directly invoke the irreversible MT5 write adapter;
- raw broker-write call sites are statically/auditably confined to the intended execution adapter/path.

A test or architectural check should fail if a new code path bypasses the centralized permission component.

## Execution tests

Critical invariants:

- correct account/symbol/specs;
- fresh quote/price-drift/spread checks;
- valid volume/SL/TP/margin;
- intent persisted before send;
- **exactly one irreversible send per Execution Intent**;
- ambiguous acknowledgement causes reconciliation, never blind retry;
- manual/foreign position ownership protection;
- modification/close ambiguity reconciliation.

Fake broker adapters should count send calls and simulate acceptance with lost responses.

## Crash/fault injection

Deliberately simulate failure around:

- before/after intent persistence;
- during/after order send;
- after broker fill before local save;
- SL/TP modification;
- close;
- daily loss lock;
- atomic state write.

Recovery must be deterministic or safely BLOCK with explicit reason—never duplicate exposure.

## Persistence and corruption tests

Cover:

- truncated/checksum-invalid state;
- old/incompatible schema;
- atomic-write interruption;
- critical state does not reset to defaults;
- opportunity revalidation after downtime;
- original R/open-trade context persistence.

## Laptop migration and backup tests

A fresh-machine restore test must prove preservation of:

- Strategy IDs/versions;
- Champion/Challenger state;
- entry/exit learning;
- autonomous candidates/genealogy;
- promotion history;
- important risk/order/trade context as designed.

Backup verification must prove required project intelligence is present and financial-authority credentials/tokens/keys are absent from public backup artifacts.

Restored state never overrides fresh broker truth.

## Multi-instance tests

Prove one account/symbol has at most one active broker-write controller. Observer/Research instances cannot send. Failover must reconcile broker/state before acquiring execution authority.

## News/provider tests

Distinguish:

- macro opinion unavailable but event safety verified → degraded soft evidence;
- required event truth unavailable → hard safety unknown/block according to policy.

Post-news recovery should require market normalization where frozen policy says so, not timer-only unlock.

## Dashboard/diagnostic tests

Test semantic rendering:

- normal `WAIT` is not a system error;
- hard block displays exact reason;
- system fault displays subsystem/impact/recovery;
- centralized Execution Permission status/reason is represented correctly;
- backup/controller health shown correctly;
- emoji fallback cannot affect logic.

## Learning tests

Prove:

- small samples have low confidence;
- StrategyMemory influence is bounded;
- entry/exit research creates Challengers rather than mutating production;
- learning outage can degrade safely when baseline is independent;
- evidence versions/environments remain isolated;
- risk/safety mutation attempts are denied.

## Autonomous invention tests

Prove:

- only approved declarative primitives accepted;
- arbitrary executable-code candidates rejected;
- variants versus new families classified;
- genealogy/rejected-candidate memory survives restart;
- autonomous candidates cannot call broker or self-promote.

## Promotion tests

Cover:

- required stage ordering;
- final-holdout one-shot/consumed state;
- Shadow zero broker authority;
- Canary still uses normal Risk + centralized Execution Permission Gate;
- open-trade policy version retained;
- rollback/history persistence;
- unsafe schema migration blocks promotion.

## Public repository secret scanning

Before public backup/release, scan for actual financial-authority secrets such as MT5 passwords, broker/API authentication tokens, paid-service secrets, GitHub PATs and private/signing keys.

Strategies, learning parameters and research are **not automatically secrets** under the project's current policy and should not be excluded merely because they are valuable.

## CI versus controlled DEMO tests

Public CI should run tests that require no live financial credentials, including unit/contract/replay/persistence/migration/governance/secret-scan/static checks.

Actual MT5 DEMO execution tests run in a controlled environment with credentials provided outside the repository.

## End-to-end DEMO certification

Before DEMO verification, execute a real controlled lifecycle covering startup, data, opportunity, entry, Trade Plan, risk, centralized permission, submit, position management, close, journal, restart/recovery and selected fault scenarios.

## Evidence reporting

Release/audit output should state actual counts/results, for example:

```text
Unit                 412/412 PASS
Replay parity         38/38 PASS
Execution gate        24/24 PASS
Crash recovery        14/14 PASS
Migration              8/8 PASS
DEMO execution         6/6 PASS
Long forward sample    PENDING
```

Do not mark pending evidence as PASS.

## Release-blocking failures

At minimum:

- future-data leakage;
- centralized execution-permission bypass;
- duplicate broker submission risk;
- wrong-account write possibility;
- unknown exposure treated as zero;
- daily-loss bypass;
- original-R corruption;
- critical state loss on restart;
- required backup restore failure;
- public financial credential leakage;
- autonomous self-promotion/broker bypass.

## Explicit non-goals

Testing must not:

- claim profitability from software correctness;
- mark docs VERIFIED because Markdown is complete;
- hide failing/pending evidence;
- replace real DEMO execution tests with only mocks where live proof is required.

## Open questions

- exact CI platform/gates;
- coverage/static/security thresholds;
- final test fixture architecture;
- exact controlled DEMO certification sample/steps;
- long-duration forward-evidence requirement.
