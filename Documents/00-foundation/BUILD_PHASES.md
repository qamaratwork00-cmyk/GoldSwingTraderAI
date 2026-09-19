# GoldSwingTraderAI — Build Phases

**Status:** PROVISIONAL
**Version:** 0.1-foundation
**Authority:** Phase ownership, dependency order and exit gates

## Why phases exist

The phases are a build dependency map. They are not a status diary and they do
not allow a later layer to hide an incomplete earlier authority.

~~~mermaid
flowchart LR
    P1["1–2 Foundation + reads"] --> P3["3 Intelligence"]
    P3 --> P4["4 Decisions"]
    P4 --> P5["5 Plan + risk"]
    P5 --> P6["6 Session + persistence"]
    P6 --> P7["7 Execution + controller"]
    P7 --> P8["8 Trade Manager"]
    P8 --> P9["9 Dashboard"]
    P9 --> P10["10 Research"]
    P10 --> P11["11 Recovery + backup"]
    P11 --> P12["12 Runtime + DEMO certification"]
~~~

## Phase 1–9: production foundation

### Phase 1 — Foundation, package and contracts

Build Python package shape, settings, IDs/enums, domain models, reason codes,
structured logging, secret-safe configuration and CI.

Exit: package imports, invalid configuration fails clearly, secret scan works,
typed contracts and foundational tests pass.

### Phase 2 — MT5 read layer and Gold facts

Build the single MT5Reader boundary, XAUUSDm/XAUUSD resolution, account and
symbol facts, Bid/Ask, completed H4/H1/M15/M5 history, open-position facts and
data quality.

Exit: no-lookahead reads, deterministic chronology, explicit stale/missing/
corrupt states and no duplicate raw read authority.

### Phase 3 — Market intelligence

Build candle structure, technical zones/location, causal confluence,
liquidity/SMC, EMA/RSI/ATR/volatility, session and news facts.

Exit: all desks consume shared facts, no desk writes, confluence is optional
bonus-only, and chronology tests pass.

### Phase 4 — Strategy floor and decision fusion

Build six families, independent BUY/SELL theses, Red Team conflict,
Opportunity identity and M5 Entry Timing.

Exit: no filter soup, WAIT preserves a valid idea, one family may lead and
optional evidence cannot become a hidden hard gate.

### Phase 5 — Trade Plan and Risk

Build structural invalidation, SL buffer, target hierarchy, immutable original
R, RR guard, hybrid account profiles, min-lot handling, daily safety P/L,
loss lock, reset and cooldown.

Exit: risk can reject affordability without changing structure; all-in risk,
profile ceilings and daily state are tested.

### Phase 6 — Session/news and persistence foundation

Build news states, PRE_CLOSE/reopen rules, SQLite StateStore, typed records,
checksums and restart semantics.

Exit: critical state survives restart and corrupt/unknown truth fails explicitly.

### Phase 7 — Central execution and controller

Build DEMO Guard, account/symbol checks, spread/drift/margin checks, Intent
lifecycle, one-shot writer, reconciliation and controller lease/fencing.

Exit: one Intent cannot send twice, ambiguous acknowledgement never blind
retries, and controller takeover requires recovery.

### Phase 8 — Trade Manager

Build HOLD, PROTECT, TRAIL, RUNNER and EXIT, structure-led protection,
objective progression and PRE_CLOSE override.

Exit: small profit does not force exit, runner needs a new objective, and local
state changes only after broker verification.

### Phase 9 — Dashboard and operator surface

Build compact full-cycle dashboard plus the separate READINESS monitor. Preserve
useful market/risk/trade facts and add Decision, Execution, Research, Backup and
Health visibility.

Exit: operator can distinguish WAIT, BLOCKED, system fault and stale-data wait.

## Phase 10: research and governed improvement

Build chronological replay, actual/counterfactual outcomes, MFE/MAE, capture,
Opportunity Recall, ablation, walk-forward, datasets, evidence packages,
StrategyMemory, episode journal, discovery, invention and promotion.

Exit:

~~~text
no lookahead
actual P/L separate from counterfactual outcomes
candidate declarative and bounded
eligible evidence → candidate OR explicit suppression reason
no self-promotion or hard-safety bypass
restart preserves research/rejected memory
~~~

Phase 10 is offline evidence work. It does not certify live trading.

## Phase 11: backup, migration and fault recovery

Build portable checkpoint/restore, verified local backups, public-safe staging,
fresh-database restore, controller fencing and startup reconciliation.

Exit: a fresh machine can restore context, configure credentials separately,
reconcile current MT5 truth and remain blocked until all authorities pass.

Phase 11 is recovery proof. A checkpoint is never broker truth.

## Phase 12: integrated runtime and DEMO release

Compose startup, recovery authorities, persistent M5 loop, lease renewal,
governed entry/management cycles, backup cadence, live DTOs and terminal
dashboard. Then collect controlled Windows MT5 DEMO evidence:

- fresh read and data warm-up;
- OPEN/MODIFY/CLOSE lifecycle;
- ambiguous acknowledgement/reconciliation;
- restart with broker state;
- scheduled close/reopen;
- controller failover and stale-primary denial;
- fresh-machine restore;
- real-XAU replay/walk-forward/calibration;
- final release audit.

Exit: evidence is recorded in TESTING_AND_VERIFICATION.md and
FINAL_RELEASE_AUDIT.md. Only then may the status become DEMO VERIFIED for the
exact build and environment.

## Universal phase exit gate

~~~text
CODE EXISTS
+ FOCUSED TESTS PASS
+ QUALITY/CODING REVIEW PASS
+ DOCUMENTS MATCH IMPLEMENTATION
+ FAILURE AND RESTART CASES COVERED
+ NO KNOWN CRITICAL CONTRADICTION
+ EXTERNAL EVIDENCE CLASSIFIED HONESTLY
~~~

