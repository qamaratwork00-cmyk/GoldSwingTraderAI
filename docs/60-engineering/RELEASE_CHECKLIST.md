# GoldSwingTraderAI — Release Checklist

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** DEMO release gates and sign-off checklist.  
**Depends on:** `TESTING_AND_VERIFICATION.md`, `../90-governance/OPEN_QUESTIONS.md`, `../90-governance/DOCUMENTATION_STANDARD.md`

## Purpose

A bot that runs is not automatically release-ready. This checklist defines the minimum evidence expected before a build can be called DEMO-ready/verified.

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

`REAL MONEY READY` is not an automatic next state and requires a separate future release decision.

## Design and documentation gates

- [ ] Required authoritative docs are FROZEN or explicitly deferred with rationale.
- [ ] No implementation-critical open question is silently guessed.
- [ ] Code behaviour, authoritative docs and tests agree.
- [ ] `DESIGN_DECISIONS.md` and `OPEN_QUESTIONS.md` are current.
- [ ] `CODER_GUIDE.md` and `MODULE_STRUCTURE.md` map the real implementation.
- [ ] Operator docs match actual controls/startup/recovery.
- [ ] `FINAL_BUILD_PROMPT.md` matches frozen implementation sequence/requirements.

## Market data / no-lookahead gates

- [ ] H4/H1/M15/M5 data synchronization verified.
- [ ] Duplicate/stale/gap detection verified.
- [ ] No-lookahead swing/BOS/MSS/liquidity tests pass.
- [ ] Replay chronology does not expose future-confirmed pivots/events.
- [ ] Any intrabar parity limitations are explicitly documented.

## Strategy / scoring gates

- [ ] Initial production families have positive/negative scenario tests.
- [ ] BUY/SELL theses are independent.
- [ ] Conflict/Red Team is visible and tested.
- [ ] Missing optional evidence is not score zero.
- [ ] Correlated evidence double-count protection passes.
- [ ] Opportunity/Entry dimensions remain separate.

## Entry / Trade Plan gates

- [ ] WAIT/MISSED/INVALID/BLOCKED semantics verified.
- [ ] Setup persistence/re-entry rules verified.
- [ ] Chase/price-drift protections verified.
- [ ] Structural invalidation/SL/targets verified.
- [ ] Original R immutability verified.
- [ ] Plan degradation can WAIT without deleting valid opportunity.

## Risk gates

- [ ] Broker-aware monetary risk calculation passes.
- [ ] Dynamic lot sizing/volume normalization passes.
- [ ] Min-lot unaffordability blocks rather than changes SL.
- [ ] Margin/aggregate exposure handling passes.
- [ ] Daily loss lock persists across restart.
- [ ] Governed manual reset audit/reference passes.
- [ ] Manual reset cannot bypass unrelated hard blocks.
- [ ] Unknown financial truth fails closed.

## News/session gates

- [ ] Macro opinion and event-safety facts are separated.
- [ ] Required news-safety unknown state fails according to frozen policy.
- [ ] Holiday does not equal broker market closure.
- [ ] Post-news/reopen warmup follows frozen evidence rules.

## Execution gates — zero compromise

- [ ] Intended account/server/mode verified before writes.
- [ ] Gold symbol/specs validated.
- [ ] Fresh quote/spread/drift/SL/TP/volume/margin revalidated pre-send.
- [ ] Intent is durably persisted before irreversible send.
- [ ] Exactly one `order_send` per Execution Intent is proven.
- [ ] Ambiguous acknowledgement never triggers blind retry.
- [ ] Reconciliation restores accepted/unknown state safely.
- [ ] Manual/foreign positions are never silently managed as bot-owned.
- [ ] Modify/close ambiguity uses reconciliation.

## Crash / persistence gates

- [ ] Crash after send does not duplicate exposure.
- [ ] Open-trade context/original R survive restart.
- [ ] Critical corrupt/incompatible state fails safely.
- [ ] Atomic-write interruption preserves known-good state.
- [ ] Stored opportunities are revalidated after downtime.

## Migration / backup gates

- [ ] Strategy Registry survives machine migration.
- [ ] Champion/Challenger and autonomous genealogy survive migration.
- [ ] Entry/Exit Learning survives migration.
- [ ] Promotion/rejection/rollback history survives migration.
- [ ] Fresh-machine disaster-recovery drill completed.
- [ ] Restored state reconciles current broker truth before trading.
- [ ] Public backup contains required project intelligence.
- [ ] Public backup/repository contains no financial-authority credentials/tokens/keys.
- [ ] Backup/restore integrity is actually tested, not assumed.

## Multi-instance gate

- [ ] Only one active execution controller can write the managed account/symbol.
- [ ] Observer/Research instances cannot send/modify/close.
- [ ] Failover performs reconciliation before takeover.

## Trade Manager / exit gates

- [ ] HOLD/PROTECT/TRAIL/RUNNER/EXIT semantics tested.
- [ ] Structural trailing does not intentionally widen approved risk.
- [ ] Runner extensions require objective/continuation evidence.
- [ ] Exit research reports MFE/MAE/Capture/Premature Exit metrics.

## Learning / autonomous gates

- [ ] StrategyMemory small-sample/bounded influence tested.
- [ ] Entry Learning creates candidate policy rather than live mutation.
- [ ] Exit Learning creates candidate policy rather than live mutation.
- [ ] Optional learning outage degrades safely where permitted.
- [ ] Autonomous invention uses approved declarative primitives only.
- [ ] Arbitrary generated executable trading code is rejected.
- [ ] Autonomous candidates cannot change risk/call broker/self-promote.

## Research / promotion gates

- [ ] Research chronology/no-lookahead verified.
- [ ] Final holdout use is one-shot for locked candidate.
- [ ] Ablation/stress/regime/direction evidence exists as required.
- [ ] Shadow has zero broker authority.
- [ ] DEMO Canary uses normal Risk/Execution controls.
- [ ] Promotion/rollback/version history is auditable.
- [ ] Claims do not exceed actual evidence.

## Dashboard / system-health gates

- [ ] Operator can identify market/decision/risk/execution/system states separately.
- [ ] Every non-trade/block has a reason code and human explanation.
- [ ] `WAIT` is not shown as system failure.
- [ ] Critical faults show subsystem, impact and recovery/action.
- [ ] Backup/controller/learning health is visible.
- [ ] Emoji fallback does not affect logic.

## Controlled MT5 DEMO gate

- [ ] Startup-to-close end-to-end trade lifecycle tested on intended DEMO environment.
- [ ] Broker fills/slippage/stop modification/close behaviour recorded.
- [ ] Restart/reconciliation tested against real DEMO broker state.
- [ ] Selected disconnect/market-closed/spread-block scenarios verified where feasible.

## Release-blocking defects

Do not sign off DEMO VERIFIED if any of these remain unresolved:

- future-data leakage;
- duplicate-order risk;
- wrong-account write possibility;
- unknown exposure treated as zero;
- hard loss/safety bypass;
- original-R corruption;
- critical restart-state loss;
- required disaster-recovery restore failure;
- public financial credential leakage;
- autonomous self-promotion/broker bypass;
- critical BLOCK state with no explainable reason/recovery path.

## Final sign-off

The release decision must reference an evidence-backed `FINAL_RELEASE_AUDIT.md`. Pending evidence remains explicitly pending; it must not be converted to PASS for convenience.