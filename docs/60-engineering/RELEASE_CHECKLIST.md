# GoldSwingTraderAI — Release Checklist

**Status:** PROVISIONAL  
**Version:** 0.5-design  
**Authority:** DEMO release gates and sign-off checklist.  
**Depends on:** `TESTING_AND_VERIFICATION.md`, `../90-governance/OPEN_QUESTIONS.md`, `../90-governance/DOCUMENTATION_STANDARD.md`

## Purpose

A bot that runs is not automatically release-ready. This checklist defines minimum evidence before a build can be called DEMO-ready/verified.

## Release stages

```text
DESIGN
→ IMPLEMENTATION
→ INTERNAL TEST
→ REPLAY VERIFIED
→ DEMO CANDIDATE
→ DEMO CANARY
→ MAIN DEMO
→ DEMO VERIFIED
```

V1 release scope ends at controlled DEMO verification. It does not define a separate REAL authorization/release stage.

## Design and documentation gates

- [ ] Required authoritative docs are FROZEN or explicitly classified/deferred with rationale.
- [ ] No implementation-critical question is silently guessed.
- [ ] Code behaviour, authoritative docs and tests agree.
- [ ] `DESIGN_DECISIONS.md` and `OPEN_QUESTIONS.md` are current.
- [ ] `docs/CODER_GUIDE.md` and `60-engineering/MODULE_STRUCTURE.md` map the real implementation.
- [ ] User/Setup/operator docs match actual launcher/runtime/recovery state.
- [ ] `FINAL_BUILD_PROMPT.md` matches current architecture and safety rules.
- [ ] `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` phase status matches reality.
- [ ] Root `README.md` does not advertise an obsolete implementation phase.

## Market data / no-lookahead gates

- [ ] H4/H1/M15/M5 synchronization verified.
- [ ] Duplicate/stale/gap detection verified.
- [ ] No-lookahead swing/BOS/MSS/liquidity tests pass.
- [ ] Trendline anchors use only confirmed swings available at that time.
- [ ] Fibonacci anchors/levels use only confirmed structural swings available at that time.
- [ ] POC/volume profile uses only historical volume/candle information available at that time.
- [ ] Replay does not expose future-confirmed pivots/events.
- [ ] Intrabar limitations documented honestly.

## Strategy / scoring gates

- [ ] Six initial families have positive/negative scenario tests.
- [ ] BUY/SELL theses independent.
- [ ] Conflict/Red Team visible/tested.
- [ ] Missing optional evidence is not score zero.
- [ ] Correlated-evidence double-count protection passes.
- [ ] Opportunity/Entry remain separate.
- [ ] WAIT/MISSED/INVALID/BLOCKED reasons stable/explainable.
- [ ] One strong coherent family may lead without all-family/all-indicator consensus.

## Trendline / Fibonacci / POC confluence gates

- [ ] Technical confluence module is chronological/no-lookahead.
- [ ] Support/resistance trendline touch/break/reclaim tests pass.
- [ ] Fibonacci retracement/extension geometry tests pass.
- [ ] POC prefers real volume when available and otherwise labels tick-volume approximation.
- [ ] POC alone cannot create directional trade authority.
- [ ] Missing Trendline/Fibonacci/POC leaves base family score unchanged.
- [ ] Supportive confluence bonus is bounded/capped.
- [ ] Opposed/unclear confluence cannot silently hard-block a trade.
- [ ] Research ablation evaluates Net R/drawdown/Opportunity Recall/large-move capture/trade frequency, not win rate alone.

## Entry / Trade Plan gates

- [ ] Setup persistence/re-entry verified.
- [ ] Chase/price-drift protections verified.
- [ ] Structural invalidation/SL/targets verified.
- [ ] Initial RR guard verified.
- [ ] Primary/Expansion/Runner roles verified.
- [ ] Original R immutability verified.
- [ ] Plan degradation can WAIT without deleting valid opportunity.
- [ ] Core manager works without requiring partial close.

## Risk gates

- [ ] SMALL/MEDIUM/NORMAL profile boundaries pass.
- [ ] Any positive DayStartEquity below `$300` resolves SMALL.
- [ ] No arbitrary `$100` minimum account gate remains in code/docs/tests.
- [ ] Normal/elevated risk bands and hard ceilings pass.
- [ ] Broker-aware monetary risk/volume normalization passes.
- [ ] Minimum-lot handling evaluates executable lot rather than changing SL.
- [ ] Position capacity `0/1` passes.
- [ ] Manual/foreign/unknown Gold ownership rule passes.
- [ ] Margin handling passes.
- [ ] UTC risk-day rollover verified.
- [ ] Cash-flow-adjusted Account Safety P/L verified.
- [ ] Floating drawdown affects daily safety immediately.
- [ ] Daily loss lock persists restart.
- [ ] Manual reset default OFF/max-one semantics pass.
- [ ] Manual reset cannot bypass unrelated hard blocks.
- [ ] Same-episode re-entry and 3-loss cooldown rules pass.
- [ ] Unknown financial truth fails closed.

## News/session gates

- [ ] Macro opinion/event-safety facts separated.
- [ ] Tier 1 `-15/+15`, Tier 2 `-5/+5`, Tier 3 no-hard-blackout pass.
- [ ] Required news-safety unknown fails closed.
- [ ] Scheduled news alone does not force-close managed trade.
- [ ] Severe post-news warmup follows evidence rules.
- [ ] Daily T-20 no-entry / T-10 flatten passes from verified broker schedule.
- [ ] Weekend T-60 no-entry / T-30 flatten passes.
- [ ] Daily reopen normalized + ≥1 clean M5.
- [ ] Weekend reopen gap assessment + normalized + ≥2 clean M5.
- [ ] Ambiguous close persists/reconciles rather than falsely flat.

## Positive DEMO guard gate

- [ ] Connected account DEMO status positively verified by environment authority.
- [ ] Verified DEMO produces `DEMO_GUARD = PASS`.
- [ ] Unverified DEMO status cannot grant broker-write permission.
- [ ] DEMO guard centralized, not scattered strategy/UI checks.
- [ ] V1 does not depend on separate REAL authorization/hard-block workflow.
- [ ] Verified DEMO can perform governed real-time create/modify/close when all ordinary checks pass.

## Centralized broker-write permission gate

- [ ] One primary Execution Permission Gate exists.
- [ ] DEMO/account/data/news/risk/position/order/controller/fresh-execution results feed it.
- [ ] Gate returns ALLOW/BLOCK/UNKNOWN plus reasons.
- [ ] Strategy/timing/Trade Plan/dashboard/research/learning cannot reach raw irreversible MT5 writes.
- [ ] Create/modify/close use governed boundary.

Any bypass is release-blocking.

## Execution gates — zero compromise

- [ ] Intended account/server/mode verified before writes.
- [ ] Gold symbol/specs validated.
- [ ] Fresh quote/spread/drift/SL/TP/volume/margin revalidated pre-send.
- [ ] Healthy spread baseline excludes abnormal periods.
- [ ] Intent durably persisted before irreversible send.
- [ ] Same Intent ID cannot send twice for its lifetime.
- [ ] Pre-check failure makes zero irreversible send attempts.
- [ ] Success-like ACK is not accepted as verified exposure without broker truth.
- [ ] Ambiguous acknowledgement never blind-retries.
- [ ] Reconciliation restores accepted/unknown state safely.
- [ ] Manual/foreign positions never managed as bot-owned.
- [ ] Modify/close ambiguity uses reconciliation.

## Controller / multi-instance gates

- [ ] Shared coordination backend satisfies atomic acquisition + monotonic fencing.
- [ ] Only one active PRIMARY can write managed account/symbol.
- [ ] Renewal target/TTL current V1 (`10s`/`30s`) unless governed later change.
- [ ] Every write verifies holder + unexpired matching epoch.
- [ ] Observer/Standby/Research cannot broker-write.
- [ ] Coordination uncertainty stops irreversible writes.
- [ ] Standby takeover only after authoritative expiry.
- [ ] Takeover gets new epoch + broker/state reconciliation before PRIMARY READY.
- [ ] Old primary with stale epoch cannot write.
- [ ] Planned handoff avoids duplicate exposure.
- [ ] Cross-laptop certification uses real shared atomic backend, not only in-memory test backend.

## Crash / persistence gates

- [ ] Crash after send does not duplicate exposure.
- [ ] Open-trade context/original R survives restart.
- [ ] Risk-day/reset/cooldown/Episode lineage survives restart.
- [ ] `SUBMITTING/ACCEPTED_UNKNOWN` survives/reconciles.
- [ ] Critical corrupt/incompatible state fails safely.
- [ ] SQLite checksum/schema/transaction behaviour tested.
- [ ] Stored opportunities revalidated after downtime.

## Migration / backup gates

- [ ] Strategy Registry survives migration.
- [ ] Champion/Challenger/autonomous genealogy survives migration.
- [ ] Entry/Exit Learning survives migration.
- [ ] Promotion/rejection/rollback history survives migration.
- [ ] Fresh-machine disaster-recovery drill completed.
- [ ] Restored state reconciles broker truth before trading.
- [ ] Public backup contains required project intelligence.
- [ ] Financial-secret scanner passes.
- [ ] Public backup contains no financial-authority credentials/tokens/keys.
- [ ] Backup/restore integrity actually tested.
- [ ] Any exposed authority-bearing credential revoked/rotated.

## Trade Manager / exit gates

- [ ] HOLD/PROTECT/TRAIL/RUNNER/EXIT semantics tested.
- [ ] Small profit alone does not force breakeven/full exit.
- [ ] Structural trailing never intentionally widens approved risk.
- [ ] Runner extension requires fresh objective/continuation evidence.
- [ ] PRE_CLOSE flatten overrides HOLD/RUNNER.
- [ ] Exit research reports MFE/MAE/Capture/Premature Exit metrics.

## Learning / discovery / autonomous gates

- [ ] StrategyMemory small-sample/bounded influence tested.
- [ ] Entry/Exit Learning creates candidates rather than silent live mutation.
- [ ] Optional learning outage degrades safely where permitted.
- [ ] Autonomous invention uses approved declarative primitives only.
- [ ] Trendline/Fibonacci/POC map to explicit audited discovery primitives.
- [ ] Arbitrary generated executable trading code rejected.
- [ ] Independent episode IDs prevent fake sample inflation.
- [ ] Eligible recurring evidence creates candidate OR explicit governed suppression reason.
- [ ] Silent eligible-evidence loss reports `DISCOVERY_DEGRADED`/equivalent.
- [ ] Duplicate/rejected candidate memory survives restart.
- [ ] Autonomous candidates cannot change risk/call broker/self-promote.

## Research / promotion gates

- [ ] Research chronology/no-lookahead verified.
- [ ] Actual P/L and counterfactual missed/blocked outcomes remain separate.
- [ ] Opportunity Recall and meaningful missed moves reported.
- [ ] Final holdout is one-shot for locked candidate.
- [ ] Stress/regime/direction evidence exists as required.
- [ ] Shadow has zero broker authority.
- [ ] DEMO Canary uses normal Risk + Execution Gate.
- [ ] Promotion/rollback/version history auditable.
- [ ] Claims do not exceed actual evidence.

## Dashboard / system-health gates

- [ ] Operator can identify Market/Decision/Risk/Execution/System states separately.
- [ ] Every non-trade/block has reason + explanation.
- [ ] DEMO guard visible.
- [ ] Execution Permission visible.
- [ ] Controller role/lease/reconcile visible.
- [ ] PRE_CLOSE/reopen/news visible.
- [ ] WAIT not shown as system failure.
- [ ] Critical faults show subsystem/impact/recovery.
- [ ] Backup/learning health visible.
- [ ] Discovery Health/candidate/suppression state visible once final runtime DTO wiring exists.
- [ ] Optional Trendline/Fib/POC display does not imply mandatory gating.
- [ ] Emoji markers have text fallback and do not affect logic.

## Controlled MT5 DEMO gate

- [ ] Final persistent runtime orchestration exists.
- [ ] Startup-to-close lifecycle tested on intended DEMO environment.
- [ ] Broker fills/slippage/stop modification/close recorded.
- [ ] Restart/reconciliation tested against real DEMO broker state.
- [ ] Disconnect/market-closed/spread-block scenarios verified.
- [ ] Scheduled PRE_CLOSE flatten tested on DEMO where feasible.
- [ ] Controller handoff/failover tested safely where feasible.

## Release-blocking defects

Do not sign off DEMO VERIFIED if any remain:

- future-data leakage;
- DEMO guard bypass;
- centralized execution-permission bypass;
- duplicate-order risk;
- wrong-account write possibility;
- unknown exposure treated as zero;
- controller split-brain/stale-epoch write;
- hard loss/safety bypass;
- original-R corruption;
- false-flat scheduled-close state;
- critical restart-state loss;
- required recovery restore failure;
- public financial credential leakage;
- autonomous self-promotion/broker bypass;
- eligible discovery evidence silently lost without candidate/suppression reason;
- optional confluence acting as undocumented hard filter;
- critical BLOCK state with no explainable reason/recovery path.

## Final sign-off

Release decision must reference evidence-backed `FINAL_RELEASE_AUDIT.md`. Pending evidence remains pending; never convert it to PASS for convenience.
