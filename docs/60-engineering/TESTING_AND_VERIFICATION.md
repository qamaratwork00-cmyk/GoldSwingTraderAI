# GoldSwingTraderAI — Testing and Verification

**Status:** PROVISIONAL  
**Version:** 0.9-design  
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
→ Research Ablation / Outcome / Management / Stress / Walk-Forward Tests
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
- trendlines/Fibonacci/POC use only facts available at that replay point;
- post-hoc outcome labels cannot feed backward into the original decision/plan;
- a management action affects only following bars, never the completed bar that generated it;
- a walk-forward validation window cannot inspect candles beyond its validation-end boundary.

Future-data leakage is release-blocking.

## Replay/live parity

Where parity is claimed, replay and live paths should reuse the same production semantics.

Current realism labels:

```text
Decision replay          BAR_CLOSE
Initial bracket outcomes BAR_HIGH_LOW
Trade Manager replay     BAR_CLOSE_IDEALIZED + active barriers
Execution stress         BAR_CLOSE_EXECUTION_STRESS + declared assumptions
Walk-forward             FIXED_POLICY_WALK_FORWARD over declared replay layers
```

Do not claim tick/broker parity without sufficient historical/live evidence.

## Strategy/decision and confluence tests

Prove valid narratives/noisy negatives, independent BUY/SELL theses, conflict representation, UNKNOWN optional evidence, bounded correlated evidence and that one strong family can create opportunity without mandatory all-family confluence.

Trendline/Fibonacci/POC tests additionally prove causal anchors/history, real-volume preference with labelled tick fallback, POC cannot manufacture directional authority, missing/opposed confluence is not a hidden hard gate, bonuses are bounded positive-only, production defaults are ON and research can disable sources for controlled ablation.

## Research ablation tests

All variants must reuse identical historical event chronology:

```text
BASE
TRENDLINE
FIBONACCI
DIRECTIONAL_COMBINED
ALL
```

Decision-level ablation must report Opportunity/ENTER/WAIT/MISSED/INVALID counts, BUY/SELL leadership, Opportunity/Conflict scores, signed deltas versus BASE and POC marginal effect. Decision events alone must never fabricate Net R, Profit Factor or win rate.

## Research Trade Plan outcome tests

Prove historical Trade Plan geometry is reconstructed from facts available at ENTER time; later bars are used only after the plan is frozen; BUY/SELL touch logic is symmetric; MFE/MAE use immutable original R; same-M5 stop+target becomes `BOTH_TOUCHED_AMBIGUOUS`; unresolved horizons remain unresolved; and ambiguous/unresolved cases stay outside resolved bracket P/L metrics.

## Research Trade Manager replay tests

Prove:

- READY historical plans create research `ManagedTrade` through production models;
- currently active stop/TP is checked before a new manager decision on each M5;
- tightened stops can realize positive R;
- same-bar active stop+TP remains ambiguous;
- surviving bar completes before production `evaluate_trade_manager()` sees it;
- HOLD/PROTECT/TRAIL/RUNNER/EXIT come from production manager logic;
- manager modification applies only following bar or later;
- RUNNER changes active objective only through production transition;
- manager EXIT records modeled R/reason;
- HORIZON_OPEN/ambiguous remain outside resolved management metrics;
- Capture Efficiency/giveback derive only from modeled path facts.

## Research execution-stress tests

Prove:

- analytical `ReplayRun` is held fixed while declared execution assumptions vary;
- exactly one clean BASE and unique scenario variants exist;
- stress assumptions are explicit/configurable;
- positive spread uses executable-side approximation: BUY exits Bid, SELL exits Ask;
- adverse entry is measured in immutable original-R units;
- adverse fill cannot move structural stop/target or rewrite original R;
- completed-M5 modify delay cannot affect the bar that generated it;
- pending modify suppresses overlapping modify submissions until resolution;
- deterministic every-Nth rejection leaves current broker geometry unchanged;
- modify lifecycle counters remain auditable;
- same-bar ambiguity/open outcomes remain unresolved;
- stress report computes signed deltas versus BASE.

Default calibration probes:

```text
WIDER_SPREAD        1.50x dataset spread
ADVERSE_ENTRY       0.10R adverse fill
MODIFY_DELAY        1 completed M5
MODIFY_REJECTION    every 2nd submitted modify rejected
COMBINED            all four together
```

These are not production thresholds or historical broker truth.

## Fixed-policy walk-forward validation tests

`research/validation.py` must prove:

- windows are built only from historically eligible replay events;
- each window has chronological development context followed by a later validation slice;
- validation slices cannot overlap;
- overlapping development context is permitted only for state/history reconstruction;
- production Opportunity state is run through development before validation begins;
- development events are **not** counted as validation metrics;
- validation metrics contain exactly the declared validation slice events;
- dataset/outcome history is truncated at each validation-end boundary;
- therefore later-window candles cannot resolve a trade from an earlier validation slice;
- a near-boundary trade may remain `HORIZON_OPEN` rather than leak future data;
- optional execution stress is attached to validation evidence, not used to reselect the analytical policy;
- `FIXED_POLICY_WALK_FORWARD` performs no automatic parameter search/tuning;
- walk-forward code has no authority to consume the one-shot final holdout in `research/promotion.py`;
- exact development/validation window sizes remain explicit research configuration, not hidden constants.

Synthetic CI windows prove chronology/software behaviour only. Strategy validation still requires broad real XAU data and sufficient sample/regime coverage.

## Entry lifecycle / Trade Plan / Risk tests

Entry lifecycle tests cover WAIT preservation, MISSED versus INVALID, fresh second chance, stale duplicate rejection, same-episode re-entry limits and chase/drift defer semantics.

Trade Plan tests cover structural invalidation, volatility buffer, Stop Quality, target hierarchy, RR guards, Primary/Expansion/Runner roles, broker normalization, immutable original R and indivisible 0.01 management.

Risk tests cover SMALL/MEDIUM/NORMAL boundaries, any positive equity below $300 as SMALL, normal/elevated/ceiling rules, min-lot evaluation, 0/1 capacity, external ownership, margin authority, UTC risk day, cash-flow-adjusted AccountSafetyPL, floating drawdown, daily lock/reset/cooldown/episode persistence and unknown-state fail-closed behaviour.

## Execution / controller / session tests

Positive DEMO guard, centralized execution gate, spread/drift thresholds, one-shot intent sending, ambiguous ACK reconciliation, manual/foreign ownership protection, modify/close ambiguity and broker truth must be covered.

Controller tests prove single PRIMARY, observer standby, lease/epoch freshness, stale-epoch denial, uncertainty blocking, takeover reconciliation and old-primary write denial. Cross-machine certification requires a real shared atomic backend.

Session/news tests cover Tier1/Tier2/Tier3 windows, required truth failure, post-news warmup, daily/weekend PRE_CLOSE timing, verified schedule, reopen clean-M5 rules and ambiguous-close reconciliation.

## Crash, persistence and migration tests

Fault injection covers intent persistence/send/fill, SL/TP modification, close, PRE_CLOSE, daily lock, controller takeover and atomic state writes. Recovery must never duplicate exposure.

Persistence tests cover checksum/schema/truncation failure, atomic interruption, Opportunity/TradePlan/original-R/risk state, unresolved ExecutionIntent recovery and research/candidate/promotion persistence.

Fresh-machine restore must preserve Strategy IDs/versions, Champion/Challenger state, learning, autonomous genealogy/rejected memory, promotion history and important risk/order/trade/opportunity state. Public artifacts exclude financial-authority secrets; broker truth remains authoritative after restore.

## Dashboard / learning / discovery / promotion tests

Dashboard tests distinguish WAIT from faults and surface exact DEMO/controller/PRE_CLOSE/news/execution/backup/optional-confluence/Discovery Health state without adding authority.

Learning tests prove low confidence for small samples, bounded StrategyMemory influence, challenger-not-live-mutation, evidence-version isolation and hard-safety mutation denial.

Discovery tests prove approved primitives only, arbitrary-code rejection, independent episodes, candidate-or-suppression liveness, durable rejected memory and no broker/self-promotion authority.

Promotion tests cover stage order, locked fingerprint, one-shot holdout, Shadow zero broker authority, DEMO Canary normal Risk+Execution path, rollback/history persistence and schema safety.

## CI versus controlled DEMO

Public CI runs credential-free unit/contract/replay/research/persistence/governance/secret-scan/static checks. Actual MT5 DEMO execution tests run in a controlled environment with credentials outside the repository.

## Evidence reporting

Example:

```text
Unit                      PASS / count
Replay chronology          PASS / count
Confluence ablation        PASS / count
Bracket outcome model      PASS / count / coverage
Trade Manager replay       PASS / count / coverage / realism
Execution stress           PASS / scenarios / assumptions
Walk-forward chronology    PASS / windows / validation events
Independent real-data run  PENDING/PASS
Discovery liveness         PASS / count
Execution gate             PASS / count
Controller/failover        PASS / count
Crash recovery             PASS / count
Fresh-machine restore      PENDING/PASS
DEMO execution             PENDING/PASS
Long forward sample        PENDING/PASS
```

Do not mark pending evidence as PASS. Do not convert ambiguous/unresolved/open replay outcomes into synthetic resolved P/L.

Current deterministic CI checkpoint after the fixed-policy walk-forward foundation: **163 tests PASS**, Ruff PASS and financial-secret scan PASS.

## Release-blocking failures

At minimum:

- future-data leakage;
- walk-forward development events counted as validation evidence;
- later validation-window data leaking backward to resolve earlier outcomes;
- validation utility mutating policy or consuming final holdout without governance;
- centralized execution-permission or DEMO-guard bypass;
- duplicate broker submission / wrong-account write;
- unknown exposure treated as zero;
- controller split-brain/stale epoch;
- daily-loss/original-R safety corruption;
- critical restart-state loss or scheduled-close false-flat state;
- required recovery restore failure;
- financial credential leakage;
- autonomous self-promotion/broker bypass;
- eligible discovery evidence silently disappearing;
- optional confluence acting as undocumented hard gate;
- favorable guessing of unknown same-bar ordering;
- retroactive management modification;
- stress model rewriting structural geometry/original R;
- hidden stress assumptions presented as broker fact.

## Explicit non-goals

Testing must not claim profitability from software correctness, mark docs VERIFIED because Markdown is complete, hide pending evidence, present idealized/stressed/walk-forward software fixtures as broker-realized P/L, or replace required real historical/DEMO proof with mocks.

## Open questions

- final CI coverage/static/security thresholds;
- real-data walk-forward development/validation window sizes and sample requirements;
- dataset identity/versioning and evidence-manifest format;
- historical PRE_CLOSE/session integration;
- empirical spread/slippage/modify-failure stress calibration;
- variable-spread/tick-order evidence where available;
- final controlled DEMO certification sample/steps;
- long-duration forward-evidence requirement;
- final historical/DEMO evidence threshold for optional confluence retention.
