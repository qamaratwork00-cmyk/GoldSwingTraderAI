# GoldSwingTraderAI — Release Checklist

**Status:** PROVISIONAL  
**Version:** 0.4-design  
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
- [ ] User/Setup/operator docs match actual controls/startup/recovery.
- [ ] `FINAL_BUILD_PROMPT.md` matches implementation requirements/sequence.
- [ ] `CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md` phase status matches reality.

## Market data / no-lookahead gates

- [ ] H4/H1/M15/M5 synchronization verified.
- [ ] Duplicate/stale/gap detection verified.
- [ ] No-lookahead swing/BOS/MSS/liquidity tests pass.
- [ ] Replay does not expose future-confirmed pivots/events.
- [ ] Intrabar limitations are documented.

## Strategy / scoring gates

- [ ] Six initial families have positive/negative scenario tests.
- [ ] BUY/SELL theses are independent.
- [ ] Conflict/Red Team visible and tested.
- [ ] Missing optional evidence is not score zero.
- [ ] Correlated-evidence double-count protection passes.
- [ ] Opportunity/Entry remain separate.
- [ ] WAIT/MISSED/INVALID/BLOCKED reasons are stable/explainable.

## Entry / Trade Plan gates

- [ ] Setup persistence/re-entry rules verified.
- [ ] Chase/price-drift protections verified.
- [ ] Structural invalidation/SL/targets verified.
- [ ] Initial RR guard verified.
- [ ] Primary/Expansion/Runner objective roles verified.
- [ ] Original R immutability verified.
- [ ] Plan degradation can WAIT without deleting a valid opportunity.
- [ ] Core exit/manager logic works without requiring partial close.

## Risk gates

- [ ] SMALL/MEDIUM/NORMAL profile boundaries pass.
- [ ] Normal/elevated risk bands and hard entry ceilings pass.
- [ ] Broker-aware monetary risk/volume normalization passes.
- [ ] Minimum-lot handling evaluates executable lot rather than changing SL.
- [ ] Position capacity `0/1` passes.
- [ ] Manual/foreign/unknown Gold exposure ownership rule passes.
- [ ] Margin handling passes.
- [ ] UTC risk-day rollover verified.
- [ ] Cash-flow-adjusted Account Safety P/L verified.
- [ ] Floating drawdown affects daily safety immediately.
- [ ] Daily loss lock persists across restart.
- [ ] Manual reset default OFF and max-one enabled reset semantics pass.
- [ ] Manual reset cannot bypass unrelated hard blocks.
- [ ] Same-episode re-entry and 3-loss cooldown rules pass.
- [ ] Unknown financial truth fails closed.

## News/session gates

- [ ] Macro opinion and event-safety facts are separated.
- [ ] Tier 1 `-15/+15`, Tier 2 `-5/+5`, Tier 3 no-hard-blackout semantics pass.
- [ ] Required news-safety unknown fails closed.
- [ ] Scheduled news alone does not force-close an existing managed trade.
- [ ] Severe post-news warmup follows evidence rules.
- [ ] Daily T-20 no-entry / T-10 flatten passes from verified broker schedule.
- [ ] Weekend T-60 no-entry / T-30 flatten passes.
- [ ] Daily reopen requires normalized conditions + at least 1 clean M5.
- [ ] Weekend reopen requires gap assessment + normalized conditions + at least 2 clean M5.
- [ ] Ambiguous close state persists/reconciles rather than falsely reporting flat.

## Positive DEMO guard gate

- [ ] Connected account DEMO status is positively verified by account/environment authority.
- [ ] Verified DEMO produces `DEMO_GUARD = PASS`.
- [ ] Unverified DEMO status cannot grant broker-write permission.
- [ ] DEMO guard is one centralized input, not scattered strategy/UI checks.
- [ ] V1 does not depend on or invent a separate REAL authorization/hard-block workflow.
- [ ] A verified DEMO account can perform real-time create/modify/close when all ordinary checks pass.

## Centralized broker-write permission gate

- [ ] One primary `ExecutionPermissionGate`/equivalent exists.
- [ ] DEMO/account/data/news/risk/position/order/controller/fresh-execution results feed it.
- [ ] Gate returns ALLOW/BLOCK/UNKNOWN plus primary/secondary reasons.
- [ ] Strategy, scoring, Entry Timing, Trade Plan, dashboard, research and learning cannot directly reach irreversible MT5 writes.
- [ ] Create/modify/close all use the same governed boundary.

Any bypass is release-blocking.

## Execution gates — zero compromise

- [ ] Intended account/server/mode verified before writes.
- [ ] Gold symbol/specs validated.
- [ ] Fresh quote/spread/drift/SL/TP/volume/margin revalidated pre-send.
- [ ] Healthy spread baseline excludes abnormal periods.
- [ ] Intent is durably persisted before irreversible send.
- [ ] Exactly one `order_send` per Execution Intent is proven.
- [ ] Ambiguous acknowledgement never blind-retries.
- [ ] Reconciliation restores accepted/unknown state safely.
- [ ] Manual/foreign positions are never managed as bot-owned.
- [ ] Modify/close ambiguity uses reconciliation.

## Controller / multi-instance gates

- [ ] Shared lease backend satisfies atomic acquisition + monotonic fencing contract.
- [ ] Only one active PRIMARY can write the managed account/symbol.
- [ ] Renewal target/TTL configured to current V1 values (`10s`/`30s`) unless an explicitly governed later change exists.
- [ ] Every irreversible write freshly verifies holder + unexpired matching epoch.
- [ ] Observer/Standby/Research instances cannot broker-write.
- [ ] Coordination uncertainty stops irreversible writes.
- [ ] Standby takeover occurs only after authoritative expiry.
- [ ] Takeover gets a new epoch and completes broker/state reconciliation before PRIMARY READY.
- [ ] Old primary returning with stale epoch cannot write.
- [ ] Planned handoff avoids duplicate exposure.

## Crash / persistence gates

- [ ] Crash after send does not duplicate exposure.
- [ ] Open-trade context/original R survives restart.
- [ ] Risk-day/reset/cooldown/Episode lineage survives restart.
- [ ] `SUBMITTING/ACCEPTED_UNKNOWN` survives/reconciles.
- [ ] Critical corrupt/incompatible state fails safely.
- [ ] Atomic-write interruption preserves known-good state.
- [ ] Stored opportunities are revalidated after downtime.

## Migration / backup gates

- [ ] Strategy Registry survives migration.
- [ ] Champion/Challenger/autonomous genealogy survives migration.
- [ ] Entry/Exit Learning survives migration.
- [ ] Promotion/rejection/rollback history survives migration.
- [ ] Fresh-machine disaster-recovery drill completed.
- [ ] Restored state reconciles current broker truth before trading.
- [ ] Public backup contains required project intelligence.
- [ ] Financial-secret scanner passes.
- [ ] Public backup/repository contains no financial-authority credentials/tokens/keys.
- [ ] Backup/restore integrity is actually tested.
- [ ] Any publicly exposed authority-bearing credential is revoked/rotated.

## Trade Manager / exit gates

- [ ] HOLD/PROTECT/TRAIL/RUNNER/EXIT semantics tested.
- [ ] Structural trailing never intentionally widens approved risk.
- [ ] Runner extension requires fresh objective/continuation evidence.
- [ ] PRE_CLOSE flatten overrides HOLD/RUNNER as required.
- [ ] Exit research reports MFE/MAE/Capture/Premature Exit metrics.

## Learning / autonomous gates

- [ ] StrategyMemory small-sample/bounded influence tested.
- [ ] Entry/Exit Learning creates candidates rather than silent live mutation.
- [ ] Optional learning outage degrades safely where permitted.
- [ ] Autonomous invention uses approved declarative primitives only.
- [ ] Arbitrary generated executable trading code is rejected.
- [ ] Autonomous candidates cannot change risk/call broker/self-promote.

## Research / promotion gates

- [ ] Research chronology/no-lookahead verified.
- [ ] Final holdout use is one-shot for locked candidate.
- [ ] Stress/regime/direction evidence exists as required.
- [ ] Shadow has zero broker authority.
- [ ] DEMO Canary uses normal Risk + centralized Execution Permission Gate.
- [ ] Promotion/rollback/version history is auditable.
- [ ] Claims do not exceed actual evidence.

## Dashboard / system-health gates

- [ ] Operator can identify Market/Decision/Risk/Execution/System states separately.
- [ ] Every non-trade/block has reason + explanation.
- [ ] DEMO guard state visible.
- [ ] Central Execution Permission state/reason visible.
- [ ] Controller role/lease/reconcile state visible.
- [ ] PRE_CLOSE/reopen/news state visible.
- [ ] `WAIT` is not shown as a system failure.
- [ ] Critical faults show subsystem/impact/recovery.
- [ ] Backup/learning health visible.
- [ ] Emoji markers have text fallback and do not affect logic.

## Controlled MT5 DEMO gate

- [ ] Startup-to-close lifecycle tested on intended DEMO environment.
- [ ] Broker fills/slippage/stop modification/close behaviour recorded.
- [ ] Restart/reconciliation tested against real DEMO broker state.
- [ ] Selected disconnect/market-closed/spread-block scenarios verified.
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
- critical BLOCK state with no explainable reason/recovery path.

## Final sign-off

Release decision must reference evidence-backed `FINAL_RELEASE_AUDIT.md`. Pending evidence remains pending; it must never be converted to PASS for convenience.
