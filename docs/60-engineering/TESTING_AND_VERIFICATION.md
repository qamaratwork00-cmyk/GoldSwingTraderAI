# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 0.6-design  
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
→ Research Ablation / Outcome Tests
→ Integration Tests
→ Fault / Crash Injection
→ Persistence / Migration Tests
→ Broker DEMO Tests
→ Learning / Discovery / Promotion Governance Tests
→ End-to-End DEMO Certification
```

## No-lookahead tests

Must prove:

- candidate swings may evolve;
- confirmed swings appear only at `confirmed_at`;
- wick-only probes do not become confirmed BOS/MSS;
- future candles/targets/FVG/OB/news revisions do not leak backward;
- trendlines use only already-confirmed swing anchors;
- Fibonacci anchors use only already-confirmed structural swings;
- POC/volume profile uses only volume/candle history available at that replay point;
- replay chronology matches documented information availability;
- post-hoc future outcome labels cannot feed backward into the original historical decision/plan.

Future-data leakage is release-blocking.

## Replay/live parity

Where parity is claimed, replay and live paths should reuse the same decision semantics. Feed identical snapshots/events into shared logic and compare outputs.

Do not claim intrabar parity without sufficient historical data. Current decision replay is explicitly `BAR_CLOSE`; initial stop/target outcome labeling is explicitly bar-high/low modeling rather than tick-perfect execution.

## Strategy/decision tests

Each family requires positive/negative fixtures covering:

- valid narrative recognized;
- noisy lookalike rejected;
- BUY/SELL theses independent;
- conflict represented;
- missing optional evidence is UNKNOWN/absent, not zero;
- correlated evidence is not repeatedly counted;
- one strong family can create an opportunity without mandatory all-family confluence.

## Trendline / Fibonacci / POC confluence tests

Initial V1 confluence is explicitly **bonus-only**.

Tests must prove:

- causal support/resistance trendline construction from confirmed swings;
- trendline touch/break/reclaim classification is deterministic;
- Fibonacci anchors/levels are chronological and deterministic;
- Volume Profile/POC prefers real volume when available and otherwise labels tick-volume approximation;
- POC alone cannot manufacture directional strategy authority;
- missing all confluence leaves the base family score unchanged;
- supportive confluence can only add a bounded positive family bonus;
- opposed/unclear confluence does not become a hidden hard BLOCK;
- repeated/correlated Trendline/Fib/POC evidence cannot inflate scores without cap;
- confluence source modules contain no risk/execution authority;
- production confluence configuration defaults all implemented sources ON;
- research may disable individual confluence sources without introducing a penalty/hard gate.

A positive-only family uplift does not imply monotonically higher fused Opportunity Score because both BUY and SELL may gain support and conflict may rise. Tests/research must measure the final signed effect instead of asserting automatic improvement.

## Research ablation tests

The same historical chronology must be reused for all controlled confluence variants:

```text
BASE
TRENDLINE
FIBONACCI
DIRECTIONAL_COMBINED
ALL
```

Decision-level ablation must prove/report:

- identical event timestamps across variants;
- Opportunity/ENTER/WAIT/MISSED/INVALID counts;
- BUY/SELL leading counts;
- average Opportunity/Conflict scores;
- signed deltas versus BASE;
- POC marginal effect through `ALL - DIRECTIONAL_COMBINED`;
- no fabricated Net R/Profit Factor/win rate from decision events alone.

When the bracket outcome layer is attached, tests must preserve the distinction between analytical decision evidence and explicit initial Trade Plan path evidence.

## Research Trade Plan outcome tests

Initial post-hoc outcome modeling must prove:

- production Trade Plan geometry is built from the historical snapshot/intelligence available at the ENTER timestamp;
- later candles are used only after that decision/plan is frozen;
- BUY and SELL stop/target touch logic is symmetric;
- MFE/MAE are normalized by immutable original R;
- target-before-stop produces the broker target RR for the initial bracket model;
- stop-before-target produces `-1R` for the initial bracket model;
- stop and target touched in the same M5 is `BOTH_TOUCHED_AMBIGUOUS`, never favorable guessed order;
- neither touched within configured horizon remains `HORIZON_UNRESOLVED`;
- ambiguous/unresolved cases do not enter resolved bracket Net R/PF/drawdown;
- resolved coverage is always reported;
- 2R/3R/4R reach metrics may use observed MFE without pretending those levels were necessarily realized;
- `resolved_bracket_*` metrics are not labeled full production/broker P&L.

Full Trade Manager/runner replay remains separate validation before management parity can be claimed.

## Entry lifecycle tests

Prove:

- `WAIT` preserves valid setup;
- `MISSED` differs from `INVALID`;
- fresh second-chance events can re-arm;
- stale unchanged re-entry is rejected;
- same Market Episode allows at most one genuinely fresh re-entry;
- chase/extension and price drift can defer entry without deleting thesis.

## Decision attribution tests

Every non-entry path should produce stable reason codes and authority trace. Do not collapse into generic `NO TRADE`.

## Trade Plan tests

Cover:

- structural invalidation;
- volatility-aware buffer;
- Stop Quality;
- target hierarchy and RR;
- RR guard `<1.20R`, conditional `1.20–<1.50R`, good `1.50R+`, strong `2R+`;
- Primary checkpoint / Expansion objective / Runner roles;
- broker normalization cannot silently redesign thesis;
- price-drift degradation;
- immutable original R after trailing/restart;
- manager works with indivisible `0.01` and no partial-close dependency.

## Risk tests

Cover:

- SMALL/MEDIUM/NORMAL boundaries;
- **any positive DayStartEquity below `$300` resolves SMALL; no `$100` floor**;
- normal/elevated bands and hard ceilings;
- minimum-lot evaluation rather than raw-lot auto-rejection;
- one independently risk-bearing Gold position `0/1`;
- external/manual/unknown ownership protection;
- exact broker-margin authority when available;
- UTC risk-day rollover;
- cash-flow-adjusted `AccountSafetyPL`;
- floating drawdown affects safety immediately;
- daily lock persists restart;
- manual reset default OFF / max one per UTC day when enabled;
- reset preserves cumulative history;
- one ordinary loss does not trigger global cooldown;
- second same-episode loss locks episode;
- three consecutive closed losses trigger minimum 30-minute cooldown plus fresh M15 context;
- unknown financial state fails closed.

## Positive DEMO guard tests

```text
verified connected DEMO account → DEMO_GUARD PASS
DEMO status not verified        → broker-write permission not granted
```

Prove:

- verified DEMO + other hard authorities PASS can produce execution ALLOW;
- DEMO status comes from environment/account authority, not UI/strategy;
- unknown DEMO status cannot silently become PASS;
- V1 does not invent separate REAL authorization/hard-block workflow;
- verified DEMO can perform real-time create/modify/close when ordinary checks pass.

## Centralized Execution Permission Gate tests

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

and returns deterministic `ALLOW / BLOCK / UNKNOWN` plus stable reasons.

Any bypass is release-blocking.

## Spread / price-drift tests

Cover:

- healthy baseline excludes stale/news/reopen abnormal samples;
- `SpreadRatio <=1.50` NORMAL;
- `>1.50–2.25` ELEVATED + full revalidation, not automatic block;
- `>2.25` prevents current entry;
- spread >25% of approved SL distance prevents entry;
- adverse drift `<=10%` normal revalidation;
- `>10–20%` full revalidation;
- `>20%` prevents current intent / surviving opportunity WAIT;
- fresh risk/target/chase/stop invalidation blocks regardless of ratio.

## Execution tests

Critical invariants:

- correct account/symbol/specs;
- fresh quote/spread/drift/SL/TP/volume/margin;
- intent persisted before send;
- exactly one irreversible send per Intent ID lifetime;
- pre-check reject = zero send attempts;
- success-like ACK is not verified exposure until broker truth confirms;
- ambiguous acknowledgement causes reconciliation, never blind retry;
- manual/foreign ownership protection;
- modify/close ambiguity reconciliation.

Fake broker adapters should count send calls and simulate acceptance with lost responses.

## Controller / multi-instance tests

Prove:

- simultaneous acquisition produces exactly one PRIMARY;
- second laptop remains Observer while valid holder exists;
- renewal/TTL follows current contract;
- every write checks non-expired holder + matching fencing epoch;
- stale epoch cannot write after takeover;
- coordination uncertainty blocks irreversible writes;
- lease expiry alone does not make standby execution-ready;
- takeover obtains new epoch + completes reconciliation;
- old primary cannot write after failover;
- planned handoff avoids duplicate exposure.

A deterministic in-memory backend proves semantics only; controlled cross-machine certification needs a real shared atomic backend.

## Session / news tests

Cover:

- Tier 1 `-15/+15`, Tier 2 `-5/+5`, Tier 3 no hard blackout;
- linked Tier-1 cluster through final item +15;
- required event truth failure → `NEWS_SAFETY_UNKNOWN`;
- scheduled news alone does not force-close managed trade;
- severe post-news recovery needs clean M5 + normalized conditions;
- daily PRE_CLOSE no-entry T-20 / flatten T-10;
- weekend no-entry T-60 / flatten T-30;
- verified broker schedule authority;
- daily reopen ≥1 clean M5;
- weekend reopen gap assessment + ≥2 clean M5;
- ambiguous/unavailable close persists/reconciles rather than faking flat.

## Crash/fault injection

Simulate failure around:

- before/after intent persistence;
- during/after send;
- broker fill before local save;
- SL/TP modification;
- close;
- PRE_CLOSE flatten;
- daily loss lock;
- controller renewal/takeover;
- atomic state write.

Recovery must be deterministic or safely BLOCK with explicit reason — never duplicate exposure.

## Persistence and corruption tests

Cover:

- truncated/checksum-invalid state;
- old/incompatible schema;
- atomic-write interruption;
- critical state does not reset to defaults;
- opportunity revalidation after downtime;
- original R/open-trade persistence;
- risk-day/reset/cooldown/episode persistence;
- unresolved `SUBMITTING/ACCEPTED_UNKNOWN` recovery;
- Candidate/Promotion/Research journal persistence where implemented.

## Laptop migration and backup tests

Fresh-machine restore must preserve/recover:

- Strategy IDs/versions;
- Champion/Challenger state;
- entry/exit learning;
- autonomous candidates/genealogy/rejected memory;
- promotion history;
- important risk/order/trade/opportunity context.

Public artifacts must exclude financial-authority credentials/tokens/keys. Restored state never overrides fresh broker truth.

## Dashboard/diagnostic tests

Test semantic rendering:

- normal WAIT is not system error;
- hard block exact reason;
- DEMO guard accurate;
- controller role/epoch/reconcile accurate;
- PRE_CLOSE/reopen/news accurate;
- Execution Permission reason correct;
- backup/controller health correct;
- optional Trendline/Fib/POC absent does not render as hard failure;
- Discovery Health/candidate/suppression state can be surfaced once runtime DTO wiring exists;
- emoji/text fallback cannot affect logic.

## Learning tests

Prove:

- small samples have low confidence;
- StrategyMemory influence bounded;
- entry/exit research creates challengers rather than live mutation;
- learning outage can degrade safely when baseline independent;
- evidence versions/environments isolated;
- risk/safety mutation denied.

## Discovery / autonomous invention tests

Prove:

- only approved declarative primitives accepted;
- Trendline/Fibonacci/POC labels map to explicit audited primitives;
- arbitrary executable-code candidates rejected;
- independent episode IDs prevent duplicate evidence inflation;
- eligible recurring evidence creates candidate **or explicit suppression reason**;
- eligible evidence without either outcome surfaces degraded liveness;
- variants versus new families classified;
- genealogy/rejected memory survives restart;
- substantially duplicate/rejected ideas suppressed after restart;
- candidates cannot call broker or self-promote.

## Promotion tests

Cover:

- required stage ordering;
- locked fingerprint semantics;
- final-holdout one-shot/consumed state;
- Shadow zero broker authority;
- DEMO Canary still uses normal Risk + Execution Gate;
- open-trade policy version retained;
- rollback/history persistence;
- unsafe schema migration blocks promotion.

## Public repository secret scanning

Before public backup/release scan for actual financial-authority secrets such as MT5 passwords, broker/API tokens, paid-service secrets, GitHub PATs and private/signing keys.

Strategies, learning parameters and research are not automatically secrets under current policy.

If authority-bearing credential was exposed publicly, removal alone is not enough; revoke/rotate it.

## CI versus controlled DEMO tests

Public CI should run tests requiring no live financial credentials: unit/contract/replay/research/persistence/governance/secret-scan/static checks.

Actual MT5 DEMO execution tests run in controlled environment with credentials supplied outside repository.

## End-to-end DEMO certification

Before DEMO verification, execute controlled lifecycle covering startup, data, intelligence/confluence, strategy/opportunity/timing, Trade Plan, risk, DEMO guard, centralized permission, submit, position management, scheduled-close behaviour, close, journal/research feed, restart/recovery and selected fault scenarios.

## Evidence reporting

Example:

```text
Unit                    PASS / count
Replay chronology        PASS / count
Confluence causality     PASS / count
Confluence ablation      PASS / count
Bracket outcome model    PASS / count / coverage
Discovery liveness       PASS / count
Execution gate           PASS / count
Controller/failover      PASS / count
Crash recovery           PASS / count
Migration                PASS / count
DEMO execution           PENDING/PASS
Long forward sample      PENDING/PASS
```

Do not mark pending evidence as PASS. Do not convert ambiguous/unresolved bracket outcomes into synthetic resolved P/L.

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
- autonomous self-promotion/broker bypass;
- eligible discovery evidence silently disappearing without candidate/suppression reason;
- optional confluence accidentally acting as an undocumented hard gate;
- research outcome model favorably resolving unknown same-bar stop/target ordering.

## Explicit non-goals

Testing must not:

- claim profitability from software correctness;
- mark docs VERIFIED because Markdown is complete;
- hide failing/pending evidence;
- present resolved initial-bracket modeling as full Trade Manager/broker P/L;
- replace live DEMO proof with only mocks where live proof is required.

## Open questions

- final CI coverage/static/security thresholds;
- full Trade Manager replay/forward-evidence parity requirements;
- final controlled DEMO certification sample/steps;
- long-duration forward-evidence requirement;
- final historical/DEMO evidence threshold for retaining each optional confluence feature.
