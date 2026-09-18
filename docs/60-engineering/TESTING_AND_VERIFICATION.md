# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 0.7-design  
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
→ Research Ablation / Outcome / Management Replay Tests
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
- post-hoc future outcome labels cannot feed backward into the original historical decision/plan;
- management action for one completed M5 can affect only the following bar or later, never the already-completed bar that generated it.

Future-data leakage is release-blocking.

## Replay/live parity

Where parity is claimed, replay and live paths should reuse the same production semantics. Feed identical snapshots/events into shared logic and compare outputs.

Current realism labels must remain explicit:

```text
Decision replay          BAR_CLOSE
Initial bracket outcomes BAR_HIGH_LOW
Trade Manager replay     BAR_CLOSE_IDEALIZED + active bar-high/low barriers
```

Do not claim tick/broker parity without sufficient historical/live evidence.

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

A positive-only family uplift does not imply monotonically higher fused Opportunity Score because both BUY and SELL may gain support and conflict may rise. Tests/research measure the final signed effect rather than assuming automatic improvement.

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

Initial-bracket and manager ablation must preserve the distinction between analytical decision evidence and modeled outcome evidence.

## Research Trade Plan outcome tests

Initial post-hoc outcome modeling must prove:

- production Trade Plan geometry is built from historical snapshot/intelligence available at ENTER time;
- later candles are used only after that decision/plan is frozen;
- BUY and SELL stop/target touch logic is symmetric;
- MFE/MAE are normalized by immutable original R;
- target-before-stop produces broker-target RR for the initial bracket model;
- stop-before-target produces `-1R` for the initial bracket model;
- stop and target touched in the same M5 is `BOTH_TOUCHED_AMBIGUOUS`, never favorable guessed order;
- neither touched within configured horizon remains `HORIZON_UNRESOLVED`;
- ambiguous/unresolved cases do not enter resolved bracket Net R/PF/drawdown;
- resolved coverage is always reported;
- 2R/3R/4R reach metrics may use observed MFE without pretending those levels were necessarily realized;
- `resolved_bracket_*` metrics are not labeled full production/broker P/L.

## Research Trade Manager replay tests

The idealized chronological manager layer must prove:

- historical READY Trade Plan creates the research `ManagedTrade` without changing production code;
- the **currently active** stop and broker TP are checked before a new management action on each M5;
- a tightened stop can realize positive R rather than reverting to original `-1R` assumptions;
- active stop + active TP touched in the same M5 remains `BOTH_TOUCHED_AMBIGUOUS`;
- a bar that survives active barriers is completed before `evaluate_trade_manager()` sees it;
- HOLD/PROTECT/TRAIL/RUNNER/EXIT come from the production Trade Manager, not a separate backtest policy;
- manager modification requested at one completed-bar boundary applies only to the following bar or later;
- RUNNER changes the active objective only through the production manager state transition;
- manager EXIT records current modeled R and reason;
- `HORIZON_OPEN` and ambiguous outcomes remain outside resolved manager Net R/PF/drawdown;
- Capture Efficiency and profit giveback are derived only from modeled path facts;
- confluence management ablation uses identical decision chronology and correct signed deltas versus BASE;
- `BAR_CLOSE_IDEALIZED` is visible in documentation/evidence and never described as broker-realized P/L.

Still required before broker-parity claims:

- historical PRE_CLOSE/session-policy integration;
- stop/TP modification delay/failure stress;
- fill/slippage stress;
- tick/intrabar comparison where needed;
- controlled DEMO replay-versus-broker evidence.

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

Prove verified DEMO + other hard authorities can ALLOW, DEMO status comes from account/environment authority, unknown DEMO cannot become PASS, and V1 does not invent a separate REAL authorization workflow.

## Centralized Execution Permission Gate tests

Prove the gate consumes authoritative DEMO/account/data/news/risk/position/order/controller/fresh-execution results and returns deterministic `ALLOW / BLOCK / UNKNOWN` plus stable reasons.

Any bypass is release-blocking.

## Spread / price-drift tests

Cover:

- healthy baseline excludes stale/news/reopen abnormal samples;
- `SpreadRatio <=1.50` NORMAL;
- `>1.50–2.25` ELEVATED + full revalidation;
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

## Controller / multi-instance tests

Prove one PRIMARY, observer-only second controller while lease valid, lease/epoch freshness before each write, stale epoch denial, coordination uncertainty blocking, takeover reconciliation and old-primary write denial. Controlled cross-machine certification needs a real shared atomic backend.

## Session / news tests

Cover Tier1/Tier2/Tier3 windows, required calendar truth, post-news warmup, daily/weekend PRE_CLOSE timing, verified broker schedule, reopen clean-M5 rules and ambiguous-close reconciliation.

## Crash/fault injection

Simulate failure around intent persistence/send/fill, SL/TP modification, close, PRE_CLOSE flatten, daily lock, controller takeover and atomic state writes. Recovery must never duplicate exposure.

## Persistence and corruption tests

Cover checksum/schema/truncation failure, atomic interruption, opportunity revalidation, original-R/trade/risk state persistence, unresolved ExecutionIntent recovery and candidate/promotion/research persistence.

## Laptop migration and backup tests

Fresh-machine restore must preserve Strategy IDs/versions, Champion/Challenger state, learning, autonomous genealogy/rejected memory, promotion history and important risk/order/trade/opportunity context. Public artifacts exclude financial-authority secrets; restored state never overrides broker truth.

## Dashboard/diagnostic tests

Test semantic rendering for WAIT vs fault, exact hard reason, DEMO guard, controller/epoch/reconcile, PRE_CLOSE/news, execution permission, backup/controller health, optional confluence absence and Discovery Health. Emoji/text fallback cannot affect logic.

## Learning tests

Prove small-sample low confidence, bounded StrategyMemory influence, challenger rather than silent live mutation, safe optional degradation, evidence-version isolation and risk/safety mutation denial.

## Discovery / autonomous invention tests

Prove approved primitives only, Trendline/Fib/POC mapping, arbitrary-code rejection, independent episode IDs, candidate-or-suppression liveness, degraded state on silent eligible-evidence loss, durable rejected/genealogy memory and no broker/self-promotion authority.

## Promotion tests

Cover lifecycle order, locked fingerprint, one-shot holdout, Shadow zero broker authority, Canary normal Risk+Execution path, policy-version retention, rollback/history persistence and unsafe schema migration block.

## Public repository secret scanning

Before public backup/release scan for financial-authority secrets. If a credential was exposed publicly, revoke/rotate it; deletion alone is insufficient.

## CI versus controlled DEMO tests

Public CI runs credential-free unit/contract/replay/research/persistence/governance/secret-scan/static checks. Actual MT5 DEMO execution tests run in a controlled environment with credentials outside the repository.

## End-to-end DEMO certification

Before DEMO verification, execute controlled startup/data/intelligence/strategy/timing/TradePlan/risk/permission/submit/management/close/journal/research/restart/fault lifecycle.

## Evidence reporting

Example:

```text
Unit                      PASS / count
Replay chronology          PASS / count
Confluence causality       PASS / count
Confluence ablation        PASS / count
Bracket outcome model      PASS / count / coverage
Trade Manager replay       PASS / count / coverage / realism
Discovery liveness         PASS / count
Execution gate             PASS / count
Controller/failover        PASS / count
Crash recovery             PASS / count
Migration                  PASS / count
DEMO execution             PENDING/PASS
Long forward sample        PENDING/PASS
```

Do not mark pending evidence as PASS. Do not convert ambiguous/unresolved/open replay outcomes into synthetic resolved P/L.

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
- critical restart-state loss;
- scheduled-close false-flat state;
- required recovery restore failure;
- public financial credential leakage;
- autonomous self-promotion/broker bypass;
- eligible discovery evidence silently disappearing;
- optional confluence acting as undocumented hard gate;
- research favorably resolving unknown same-bar stop/target ordering;
- replay applying a management modification retroactively to the bar that generated it.

## Explicit non-goals

Testing must not claim profitability from software correctness, mark docs VERIFIED because Markdown is complete, hide pending evidence, present idealized replay as broker-realized P/L, or replace required live DEMO proof with only mocks.

## Open questions

- final CI coverage/static/security thresholds;
- historical PRE_CLOSE/session integration into manager replay;
- execution modification failure/latency/slippage stress assumptions;
- final controlled DEMO certification sample/steps;
- long-duration forward-evidence requirement;
- final historical/DEMO evidence threshold for retaining each optional confluence feature.
