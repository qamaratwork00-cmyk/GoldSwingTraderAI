# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 0.4-design  
**Authority:** Test taxonomy, executable proof requirements, replay/live parity, crash/restart, migration, learning-governance and release verification.  
**Depends on:** `../90-governance/DOCUMENTATION_STANDARD.md`, `../40-research-learning/RESEARCH_AND_VALIDATION.md`, `../30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md`

## Purpose

Testing must prove documented invariants. `VERIFIED` is reserved for behaviour that actually passed required executable validation against the exact implementation.

> **Software verification and strategy validation are separate.**

## Test layers

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

Must prove:

- candidate swings may evolve;
- confirmed swings appear only at `confirmed_at`;
- wick-only probes do not become confirmed BOS/MSS;
- future candles/targets/FVG/OB/news revisions do not leak backward;
- replay chronology matches documented information availability.

Any future-data leakage is release-blocking.

## Replay/live parity

Where parity is claimed, replay and live paths should reuse the same decision semantics. Feed identical snapshots/events into shared logic and compare outputs.

Do not claim intrabar parity without sufficient historical data.

## Strategy/decision tests

Each strategy family requires positive/negative fixtures covering:

- valid narrative recognized;
- noisy lookalike rejected;
- BUY/SELL theses independent;
- conflict represented;
- missing optional evidence is UNKNOWN/absent, not zero;
- correlated evidence is not repeatedly counted;
- one strong family can create an opportunity without mandatory all-family confluence.

## Entry lifecycle tests

Prove:

- `WAIT` preserves a valid setup;
- `MISSED` differs from `INVALID`;
- fresh second-chance events can re-arm;
- stale unchanged re-entry is rejected;
- same Market Episode allows at most one genuinely fresh re-entry;
- chase/extension and price drift can defer entry without deleting the thesis.

## Decision attribution tests

Every non-entry path should produce stable reason codes and authority trace.

Example:

```text
Strategy PASS
Entry PASS
Trade Plan PASS
News PASS
Risk BLOCK: MIN_LOT_UNAFFORDABLE
Execution NOT_REACHED
Would otherwise trade: YES
```

Do not collapse this into generic `NO TRADE`.

## Trade Plan tests

Cover:

- family-specific structural invalidation;
- volatility-aware buffer;
- Stop Quality;
- target hierarchy and RR;
- initial RR guard `<1.20R`, conditional `1.20–<1.50R`, good `1.50R+`, strong `2R+` semantics;
- Primary checkpoint / Expansion broker objective / Runner objective roles;
- broker normalization cannot silently redesign thesis;
- price-drift degradation;
- immutable original R after trailing/restart;
- core manager remains valid with indivisible `0.01` and no partial close.

## Risk tests

Use broker-spec fixtures to validate actual monetary risk and volume normalization.

Cover:

- SMALL/MEDIUM/NORMAL profile boundaries;
- normal/elevated bands and hard entry ceilings;
- minimum lot evaluation rather than raw-lot auto-rejection;
- one independently risk-bearing Gold position `0/1`;
- external/manual/unknown Gold ownership protection;
- margin checks;
- UTC risk-day rollover;
- cash-flow-adjusted `AccountSafetyPL`;
- floating drawdown affects daily safety immediately;
- daily loss lock persists across restart;
- manual reset default OFF / max one per UTC day when enabled;
- reset preserves cumulative day history;
- one ordinary loss does not trigger global cooldown;
- second same-episode loss locks that episode;
- three consecutive closed losses trigger minimum 30-minute cooldown plus fresh M15 context;
- unknown financial state fails closed.

Manual reset must not bypass unrelated `BLOCKED` states.

## Positive DEMO guard tests

V1 has one environment permission rule:

```text
verified connected DEMO account → DEMO_GUARD PASS
DEMO status not verified        → broker-write permission not granted
```

Tests must prove:

- verified DEMO + all other hard authorities PASS can produce execution `ALLOW`;
- DEMO verification is sourced from the account/environment authority, not strategy/UI code;
- missing/unknown DEMO status cannot silently become PASS;
- the V1 implementation does not require or invent a separate REAL authorization workflow/hard-block path;
- a verified DEMO account can perform real-time broker create/modify/close when ordinary governed checks pass.

## Centralized Execution Permission Gate tests

The final broker-write authorization boundary is an explicit tested feature.

Prove the gate consumes authoritative:

```text
DEMO guard
account identity
market/data/quote integrity
news/session safety
risk
position/ownership/capacity
order lifecycle/reconciliation
controller ownership
fresh execution checks
```

and returns deterministic `ALLOW / BLOCK / UNKNOWN` plus stable primary/secondary reasons.

At minimum verify:

- any hard BLOCK prevents broker write even with excellent strategy/Trade Plan;
- required UNKNOWN safety input cannot become ALLOW;
- primary/secondary reasons are preserved;
- create/modify/close all require the same governed authorization boundary;
- strategy, research, learning and dashboard cannot directly invoke irreversible MT5 write adapter;
- raw broker-write call sites are statically/auditably confined to intended execution adapter/path.

A bypass is release-blocking.

## Spread / price-drift tests

Cover:

- healthy spread baseline excludes stale/news/reopen abnormal samples;
- `SpreadRatio <=1.50` NORMAL;
- `>1.50–2.25` ELEVATED and fully revalidated rather than automatically blocked;
- `>2.25` prevents current entry;
- spread greater than 25% of approved structural stop distance prevents current entry;
- adverse drift `<=10%` can pass normal revalidation;
- `>10–20%` receives full revalidation;
- `>20%` prevents current intent/returns surviving opportunity to WAIT;
- fresh risk/target/chase/stop invalidation prevents execution regardless of ratio.

## Execution tests

Critical invariants:

- correct account/symbol/specs;
- fresh quote/spread/drift/SL/TP/volume/margin;
- intent persisted before send;
- **exactly one irreversible send per Execution Intent**;
- ambiguous acknowledgement causes reconciliation, never blind retry;
- manual/foreign position ownership protection;
- modification/close ambiguity reconciliation.

Fake broker adapters should count send calls and simulate acceptance with lost responses.

## Controller / multi-instance tests

Prove:

- simultaneous controller acquisition produces exactly one PRIMARY;
- second laptop remains Observer while a valid holder exists;
- renewal target/TTL logic follows configured V1 contract;
- every irreversible write freshly checks non-expired holder + matching fencing epoch;
- stale epoch cannot write after takeover;
- coordination-store uncertainty blocks irreversible writes;
- lease expiry alone does not make standby execution-ready;
- standby takeover obtains a new epoch and completes broker/state reconciliation before PRIMARY READY;
- old primary returning after failover cannot write with stale epoch;
- planned handoff avoids duplicate exposure.

## Session / news tests

Cover:

- Tier 1 `-15/+15`, Tier 2 `-5/+5`, Tier 3 no automatic hard blackout;
- linked Tier-1 cluster through final item +15;
- required event truth failure → `NEWS_SAFETY_UNKNOWN`;
- scheduled news alone does not force-close managed trade;
- severe post-news dislocation needs clean M5 + normalized conditions;
- daily PRE_CLOSE no-new-entry at T-20 and flatten at T-10;
- weekend no-new-entry T-60 and flatten T-30;
- timing derived from verified broker XAU session schedule;
- daily reopen needs at least one clean M5 plus normalized conditions;
- weekend reopen needs gap assessment + two clean M5 plus normalized conditions;
- ambiguous/unavailable close outcome persists and reconciles rather than faking flat.

## Crash/fault injection

Simulate failure around:

- before/after intent persistence;
- during/after order send;
- after broker fill before local save;
- SL/TP modification;
- close;
- PRE_CLOSE flatten;
- daily loss lock;
- controller lease renewal/takeover;
- atomic state write.

Recovery must be deterministic or safely BLOCK with explicit reason—never duplicate exposure.

## Persistence and corruption tests

Cover:

- truncated/checksum-invalid state;
- old/incompatible schema;
- atomic-write interruption;
- critical state does not reset to defaults;
- opportunity revalidation after downtime;
- original R/open-trade context persistence;
- risk-day/reset/cooldown/episode lineage persistence;
- unresolved `SUBMITTING/ACCEPTED_UNKNOWN` recovery.

## Laptop migration and backup tests

Fresh-machine restore must preserve/recover:

- Strategy IDs/versions;
- Champion/Challenger state;
- entry/exit learning;
- autonomous candidates/genealogy;
- promotion history;
- important risk/order/trade/opportunity context.

Backup verification must prove required project intelligence is present and financial-authority credentials/tokens/keys are absent from public artifacts.

Restored state never overrides fresh broker truth.

## News/provider tests

Distinguish:

- macro opinion unavailable but required event safety verified → degraded soft evidence;
- required event truth unavailable → hard safety unknown/block.

## Dashboard/diagnostic tests

Test semantic rendering:

- normal `WAIT` is not a system error;
- hard block displays exact reason;
- positive DEMO guard status is accurate;
- controller role/epoch/reconcile status is accurate;
- PRE_CLOSE/reopen/news states render correctly;
- centralized Execution Permission status/reason is correct;
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
- DEMO Canary still uses normal Risk + centralized Execution Permission Gate;
- open-trade policy version retained;
- rollback/history persistence;
- unsafe schema migration blocks promotion.

## Public repository secret scanning

Before public backup/release, scan for actual financial-authority secrets such as MT5 passwords, broker/API auth tokens, paid-service secrets, GitHub PATs and private/signing keys.

Strategies, learning parameters and research are not automatically secrets under current project policy.

If an authority-bearing credential was exposed publicly, removal alone is not enough; it must be revoked/rotated.

## CI versus controlled DEMO tests

Public CI should run tests requiring no live financial credentials: unit/contract/replay/persistence/migration/governance/secret-scan/static checks.

Actual MT5 DEMO execution tests run in a controlled environment with credentials supplied outside the repository.

## End-to-end DEMO certification

Before DEMO verification, execute a controlled lifecycle covering startup, data, opportunity, entry, Trade Plan, risk, DEMO guard, centralized permission, submit, position management, scheduled-close behaviour, close, journal, restart/recovery and selected fault scenarios.

## Evidence reporting

Example:

```text
Unit                 412/412 PASS
Replay parity         38/38 PASS
Execution gate        24/24 PASS
Controller/failover   12/12 PASS
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
- DEMO guard bypass;
- duplicate broker submission risk;
- wrong-account write possibility;
- unknown exposure treated as zero;
- controller split-brain/stale-epoch write;
- daily-loss bypass;
- original-R corruption;
- critical state loss on restart;
- scheduled-close state falsely marked flat;
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
