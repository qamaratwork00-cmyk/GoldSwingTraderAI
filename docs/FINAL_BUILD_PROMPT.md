# GoldSwingTraderAI — Final Build Prompt

**Status:** DRAFT — DO NOT IMPLEMENT FROM THIS YET  
**Version:** 0.4-design  
**Location:** `docs/` root by design. This is an implementation handoff artifact, not a topic authority.

This file becomes the final implementation contract only after required core design documents are frozen and remaining implementation-critical choices are resolved or explicitly deferred.

## Role

You are implementing **GoldSwingTraderAI**, a fresh and independent XAUUSD/XAUUSDm trading system designed to capture meaningful intraday/swing directional moves using a parallel specialist-floor architecture.

Do not infer requirements from unrelated prior projects. Do not copy legacy code, comments, filenames or compatibility layers merely because they existed elsewhere. The repository documentation is authoritative.

## Authority order

Read and obey, in order:

1. `docs/00-foundation/SYSTEM_CONTRACT.md`
2. The authoritative topic document for the feature being implemented
3. `docs/90-governance/DESIGN_DECISIONS.md`
4. `docs/90-governance/OPEN_QUESTIONS.md`
5. Supporting engineering/operator documentation

If documents conflict, stop and resolve the contradiction in documentation rather than silently choosing one interpretation. This prompt summarizes design requirements; it does not override their authoritative source documents.

## Project principles

Implementation must preserve:

- H4/H1/M15/M5 multi-timeframe design;
- completed-candle structural authority and explicit no-lookahead chronology;
- parallel specialist desks rather than one long filter chain;
- independent BUY and SELL theses;
- separate Opportunity and Entry Timing dimensions;
- explicit conflict/Red-Team handling;
- persistent setup lifecycle and meaningful WAIT/MISSED/INVALID semantics;
- structural Trade Plan before risk sizing;
- immutable original R;
- hard risk/news/account/data/order/controller authority outside weighted scoring;
- one centralized final broker-write permission gate;
- one governed irreversible broker-write path with durable intent and reconciliation;
- no blind retry after ambiguous broker acknowledgement;
- one active execution controller per managed account/symbol;
- durable restart state, portable Strategy Registry and laptop migration;
- public-repository disaster-recovery backup of project intelligence while excluding financial-authority credentials/keys/tokens;
- structural post-entry management for large moves;
- explicit entry/exit learning and StrategyMemory;
- governed discovery/invention/promotion without arbitrary self-writing code;
- explainable decision attribution plus separate System Health diagnostics;
- compact operator UX with restrained emoji status markers and text fallback.

## DEMO-first release policy

Initial broker-write implementation/release is for the approved **DEMO** environment. A real account must not silently gain execution authority.

This is a release safeguard, not a permanent architectural LIVE blocker. Future explicitly approved REAL execution must use the same:

```text
strategy/decision path
→ Trade Plan
→ Risk + hard safety
→ centralized Execution Permission Gate
→ durable Execution Intent
→ one-shot broker path
→ reconciliation
```

Do not build a second hidden LIVE trading engine or scatter `if demo` / `if live` checks throughout the codebase. Environment authorization has one primary policy owner and feeds the centralized execution-permission component.

## Centralized broker-write boundary

The implementation must provide one primary auditable component conceptually equivalent to `ExecutionPermissionGate` / `BrokerWriteGuard`.

It consumes authoritative results such as:

```text
Environment policy
Account identity
Market/data/quote integrity
News/session safety
Risk
Position capacity
Order lifecycle
Execution-controller ownership
Fresh broker execution checks
```

and returns an explicit result equivalent to:

```text
ALLOW / BLOCK / UNKNOWN
Primary Reason
Secondary Reasons
```

Raw irreversible MT5 create/modify/close calls must not be directly reachable from strategy, scoring, entry timing, Trade Plan, dashboard, research, learning or autonomous-invention modules.

## Public repository / disaster recovery policy

The repository may remain public during development and may contain/version project intelligence needed for recovery, including as appropriate:

- source code/docs/tests;
- strategy definitions and learned parameters;
- Strategy Registry and genealogy;
- entry/exit learning/StrategyMemory artifacts;
- autonomous candidates;
- research/promotion/rollback history;
- appropriate restore/checkpoint metadata/state artifacts.

Do **not** commit credentials, authentication tokens, private keys or other secrets capable of unauthorized financial action or direct paid-service cost, including MT5 trading passwords, broker/private tokens, paid API secrets and GitHub PATs.

Do not classify strategy/learning data as a secret merely because it is valuable unless the project policy is explicitly changed later.

## Documentation must stay synchronized with implementation

Documentation is part of each implementation step, not a cleanup task for the end.

After **every coherent implementation phase**, before moving to the next one:

1. update the authoritative topic document if behaviour/state/ownership/inputs/outputs/failure semantics changed;
2. update `docs/90-governance/DESIGN_DECISIONS.md` for new/superseded design decisions;
3. update `docs/90-governance/OPEN_QUESTIONS.md` when a question is resolved, deferred or discovered;
4. update `docs/60-engineering/MODULE_STRUCTURE.md` when real modules/files/dependency ownership change;
5. update `docs/60-engineering/CODER_GUIDE.md` when feature-to-code/config/runtime/persistence/dashboard/test ownership changes;
6. update operator-facing docs when visible behaviour, dashboard state, controls, setup, backup or recovery changes;
7. update `docs/60-engineering/TESTING_AND_VERIFICATION.md` / release docs when proof requirements materially change;
8. update `docs/README.md` if a document is added, moved, renamed, retired or changes status;
9. update this docs-root prompt only when a frozen implementation requirement or implementation sequence materially changes.

Do **not** mark a document `IMPLEMENTED` unless the described behaviour exists in current code. Do **not** mark it `VERIFIED` unless required executable validation actually passed against the exact implementation.

A phase is not complete while its code and authoritative documentation knowingly disagree.

## Prohibited shortcuts

Do not:

- turn every soft signal into a hard gate/filter soup;
- treat missing optional evidence as score zero;
- let a high strategy score override hard risk/news/account/data/order/execution safety;
- make RSI/EMA/FVG/OB alone the trading authority;
- use future candles, future-confirmed pivots or look-ahead in replay;
- change structural SL merely to make a desired lot/risk fit;
- redefine original R after trailing;
- bypass the centralized Execution Permission Gate;
- expose multiple independent raw MT5 broker-write paths;
- blind-retry ambiguous broker submissions/modifications/closes;
- assume unknown exposure/P&L/order state is zero/safe;
- allow two machines to independently control the same managed account/symbol;
- silently reset risk/order/trade state on restart/corruption;
- generate/eval/exec arbitrary Python as autonomous strategy invention;
- allow learning/research to self-promote or mutate hard risk/broker authority;
- leak financial-authority credentials into the public repository/backups/tests/logs;
- silently decide any item still listed unresolved in `docs/90-governance/OPEN_QUESTIONS.md`;
- postpone required documentation updates until the end of development.

## Intended implementation sequence

The final sequence may be refined when module names are frozen, but implementation is expected approximately as follows:

1. Project/package skeleton, configuration and immutable domain contracts.
2. Market-data/MT5 read adapter, symbol facts and completed-candle synchronization.
3. Candle/structure intelligence with no-lookahead tests.
4. Technical/location, liquidity/SMC, indicator/volatility, macro/event and session intelligence.
5. Parallel specialist interfaces and initial production strategy families.
6. Independent BUY/SELL theses, Red Team and decision fusion/attribution.
7. Persistent setup lifecycle and Entry Timing.
8. Structural Trade Plan, targets, original R and plan degradation.
9. Monetary Risk Contract plus UTC risk-day/loss-lock/manual-reset state.
10. Hard market/news/system permission composition.
11. Persistence foundation, durable Execution Intent and restart/reconciliation state.
12. Centralized Execution Permission Gate, broker adapter, one-shot submit/modify/close and controller ownership.
13. Open-trade management/trailing/runner/exit.
14. Dashboard, System Health and operator startup/shutdown/recovery UX.
15. Deterministic replay, research metrics, StrategyMemory and Entry/Exit Learning.
16. Governed discovery, declarative autonomous invention, promotion/rollback, Shadow/DEMO Canary.
17. Public-backup/secret-scan/machine-migration recovery drill.
18. DEMO readiness, release checklist and evidence-backed final audit.

Each phase must include executable tests for its frozen behavioural invariants and synchronized documentation before the next phase begins.

## Validation principles

- Documentation completion is not implementation proof.
- Static checks are not runtime proof.
- Software correctness is not profitability proof.
- Historical backtests are not guarantees of future return.
- Replay claims require chronological/no-lookahead evidence.
- Critical broker writes require fault-injection/duplicate-prevention/restart testing.
- Backup existence is not recovery proof; a fresh-machine restore drill is required for VERIFIED recovery claims.
- Learning/promotion must prove production cannot be silently mutated.
- The dashboard/reason trace is tested behaviour, not decoration.

## Current restriction

This remains a living DRAFT because many exact calibration/configuration values are still listed in `OPEN_QUESTIONS.md`. The major architecture is documented, but production implementation should not silently freeze those values from guesswork.