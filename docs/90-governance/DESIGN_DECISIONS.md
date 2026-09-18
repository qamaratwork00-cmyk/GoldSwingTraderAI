# GoldSwingTraderAI — Design Decisions

**Status:** LIVING LEDGER  
**Version:** 0.7-design

This ledger records accepted/provisional architectural decisions so future implementation does not silently reinterpret past discussion.

## DEC-001 — Documentation-first development

**Decision:** Core behaviour is documented before production trading implementation begins.  
**Status:** FROZEN  
**Reason:** Prevent architecture drift and undocumented assumptions.

## DEC-002 — Institutional trading-floor architecture

**Decision:** Specialist analytical desks operate in parallel on the same verified market snapshot.  
**Status:** PROVISIONAL  
**Reason:** Avoid long sequential filter chains that unnecessarily kill valid opportunities.

## DEC-003 — Independent BUY and SELL theses

**Decision:** BUY and SELL cases are built independently and compared explicitly.  
**Status:** PROVISIONAL  
**Reason:** A strong BUY score is not genuine conviction when an equally strong SELL case exists.

## DEC-004 — Opportunity and entry timing are separate

**Decision:** A valid setup may stay `ARMED` while entry timing is poor.  
**Status:** PROVISIONAL  
**Reason:** Avoid deleting good opportunities merely because the current M5 candle is late/extended.

## DEC-005 — Safety is not weighted scoring

**Decision:** Risk, news-safety, broker/account integrity and execution safety remain hard PASS/BLOCK/UNKNOWN authority outside soft market scoring.  
**Status:** PROVISIONAL

## DEC-006 — Candle/structure is primary market language

**Decision:** Candle sequences, market structure, liquidity, displacement and compression/expansion are primary. Indicators are supporting evidence.  
**Status:** PROVISIONAL

## DEC-007 — Initial strategy-floor families

**Decision:** Initial production candidates are Trend Pullback Continuation, Breakout Expansion, Breakout Retest Continuation, Liquidity Sweep Reversal, Failed Breakout Reversal and Compression Expansion.  
**Status:** PROVISIONAL

## DEC-008 — FVG/OB/indicators are primitives by default

**Decision:** FVG, Order Block, premium/discount, EMA, RSI, ATR and similar tools do not automatically become separate production strategies.  
**Status:** PROVISIONAL

## DEC-009 — Post-entry decision floor

**Decision:** Open trades are managed through parallel continuation/reversal analysis with actions HOLD, PROTECT, TRAIL, RUNNER and EXIT.  
**Status:** PROVISIONAL

## DEC-010 — Structural trailing

**Decision:** Trailing should primarily follow proven market structure with volatility-aware buffering, not mechanically tighten on every small profit move.  
**Status:** PROVISIONAL

## DEC-011 — Setup persistence and second-chance entries

**Decision:** Missed/temporarily poorly timed setups may be re-armed only when the original thesis survives and a genuinely fresh structural event appears.  
**Status:** PROVISIONAL

## DEC-012 — Holiday does not equal market closed

**Decision:** Holiday calendars provide context; actual broker tradeability and valid live market data determine whether Gold is open.  
**Status:** PROVISIONAL

## DEC-013 — Rolling market history, durable evidence

**Decision:** Runtime uses bounded rolling candle history; permanent durable storage prioritizes decisions, trade/risk lifecycle and research evidence over giant raw candle archives.  
**Status:** PROVISIONAL

## DEC-014 — Daily loss lock and manual reset retained

**Decision:** GoldSwingTraderAI retains a daily-loss lock and deliberate governed manual-reset feature rather than removing manual reset entirely.  
**Status:** PROVISIONAL

## DEC-015 — No fixed daily trade target

**Decision:** The bot has no minimum number of trades it must take per day. Opportunity frequency comes from valid market episodes.  
**Status:** PROVISIONAL

## DEC-016 — Governed autonomous strategy invention

**Decision:** Autonomous research may propose bounded declarative strategies/policies but may not generate/execute arbitrary Python or bypass risk/execution authority.  
**Status:** PROVISIONAL

## DEC-017 — Final build prompt is an implementation contract

**Decision:** The repository will contain a final implementation prompt that references frozen authoritative docs and forbids silent requirement invention.  
**Status:** FROZEN

## DEC-018 — Swing lifecycle separates early evidence from authority

**Decision:** Structural pivots progress through `CANDIDATE → CONFIRMED`, with some confirmed swings later promoted to `PROTECTED` or `EXTERNAL/MAJOR` roles. Candidate swings may support soft evidence but cannot independently confirm BOS/MSS or become sole structural authority.  
**Status:** PROVISIONAL

## DEC-019 — Pivot time and confirmation time are distinct

**Decision:** Every confirmed swing records both the time of the price extreme and the later time when confirmation became available. Replay/live logic may not use the swing before its confirmation time.  
**Status:** PROVISIONAL

## DEC-020 — Structural breaks use graduated states

**Decision:** Wick/probe, qualified completed-candle break, confirmed BOS, MSS candidate, confirmed MSS and failed break are distinct evidence states rather than one binary `break=true` flag.  
**Status:** PROVISIONAL

## DEC-021 — MSS means transition before new trend

**Decision:** A confirmed counter-structure MSS challenges the prior thesis and moves that timeframe toward transition; it does not by itself establish a fully confirmed opposite trend.  
**Status:** PROVISIONAL

## DEC-022 — Timeframes retain independent structure state

**Decision:** H4, H1, M15 and M5 structure states are maintained independently. Lower-timeframe structural change may influence scores/timing but cannot silently overwrite higher-timeframe structure.  
**Status:** PROVISIONAL

## DEC-023 — Technical structure owns adaptive zones and location

**Decision:** Support/resistance is modeled as adaptive zones with quality/lifecycle. A separate Location/Target-Room view evaluates where current price stands; location is important evidence but not a universal hard gate.  
**Status:** PROVISIONAL

## DEC-024 — Liquidity/SMC is contextual evidence, not mandatory confluence

**Decision:** Liquidity pools, sweeps, FVG, qualified OB and premium/discount are context-aware evidence. A sweep requires meaningful liquidity plus post-interaction failure/reclaim; FVG/OB are not mandatory for every trade.  
**Status:** PROVISIONAL

## DEC-025 — Indicators describe and normalize; price structure leads

**Decision:** EMA20/EMA50, RSI and ATR are initial quantitative tools. They support momentum/volatility/extension analysis but do not independently create or veto trades.  
**Status:** PROVISIONAL

## DEC-026 — Fundamental opinion and event safety are separate

**Decision:** Macro/fundamental context is soft evidence. Scheduled-event safety may become hard permission through the risk/session state machine. Missing optional macro opinion does not equal missing required event safety.  
**Status:** PROVISIONAL

## DEC-027 — Structural Trade Plan before risk sizing

**Decision:** Entry reference, structural invalidation, volatility-aware stop buffer and market objectives are defined before monetary sizing. Risk must reject an unaffordable plan rather than distort its structural stop.  
**Status:** PROVISIONAL

## DEC-028 — Original R is immutable

**Decision:** Original approved risk distance/R remains immutable for analytics and lifecycle attribution even after SL/TP management changes.  
**Status:** PROVISIONAL

## DEC-029 — UTC calendar risk day

**Decision:** The provisional daily-risk accounting boundary is `00:00 UTC`, independent of XAU reopen/holiday labels.  
**Status:** PROVISIONAL  
**Reason:** Deterministic accounting and replayability.

## DEC-030 — Centralized final broker-write permission gate

**Decision:** All irreversible MT5 create/modify/close actions must pass one centralized Execution Permission Gate/Broker Write Guard that consumes authoritative risk/news/account/data/order/controller results and returns ALLOW/BLOCK/UNKNOWN with reasons.  
**Status:** PROVISIONAL  
**Reason:** Make broker authority easy to audit, test, demonstrate and extend without scattered bypasses.

## DEC-031 — DEMO-first is a release safeguard, not a permanent LIVE prohibition

**Decision:** Initial implementation/release authorizes broker writes only on the approved DEMO environment. Future REAL execution requires an explicit frozen release/config policy but uses the same strategy, risk, centralized permission gate, one-shot broker path and reconciliation rather than a separate trading engine.  
**Status:** PROVISIONAL

## DEC-032 — One-shot irreversible submission with reconciliation

**Decision:** One Execution Intent permits at most one irreversible submit until reconciliation proves otherwise. Ambiguous acknowledgement enters reconciliation; blind retry is prohibited.  
**Status:** PROVISIONAL

## DEC-033 — System health is separate from normal trading decisions

**Decision:** `Why no trade?`/decision attribution belongs to decision/risk/execution authorities. Cross-subsystem System Health reports faults, severity, impact and recovery. Normal WAIT/NEWS_BLACKOUT/LOSS_LOCKED are not automatically system errors.  
**Status:** PROVISIONAL

## DEC-034 — Persistent strategy/learning state is portable

**Decision:** Strategy Registry, strategy genealogy, Champion/Challenger state, entry/exit learning, research/promotion history and critical lifecycle context must survive restart and laptop migration.  
**Status:** PROVISIONAL

## DEC-035 — Public repository may back up project intelligence; financial-authority secrets do not belong there

**Decision:** While the repository is public, code, docs, strategy definitions, learned parameters, autonomous candidates, research/promotion history and appropriate state backups may be versioned there for disaster recovery. Credentials/keys/tokens that can enable unauthorized financial action or direct paid-service cost must never be committed.  
**Status:** PROVISIONAL

## DEC-036 — Single active execution controller

**Decision:** For one managed account/symbol, only one runtime instance may hold broker-write authority. Other machines may observe/research/shadow. Failover must reconcile broker and local state before takeover.  
**Status:** PROVISIONAL

## DEC-037 — Learning includes entry quality and exit/capture quality

**Decision:** Learning evaluates TAKEN/MISSED/BLOCKED/INVALIDATED opportunities and explicitly measures entry efficiency, MFE/MAE, capture efficiency and premature-exit cost. Learning proposes challengers; it does not silently mutate current production.  
**Status:** PROVISIONAL

## DEC-038 — Strategy discovery/invention is governed and declarative

**Decision:** Autonomous candidates are built from approved market primitives/recipes, retain genealogy and rejected-candidate memory, and cannot create arbitrary executable Python, change risk or call the broker directly.  
**Status:** PROVISIONAL

## DEC-039 — Promotion uses evidence stages and one-shot final holdout

**Decision:** Candidate promotion proceeds through research/independent validation/locked candidate/final untouched holdout/stress/Shadow/DEMO Canary before production approval as applicable. The final holdout is consumed once for a locked candidate.  
**Status:** PROVISIONAL

## DEC-040 — Compact dashboard with restrained emojis and explicit reasons

**Decision:** Main terminal UX remains compact, uses meaningful emojis as status markers (not decoration), separates Market/Decision/Risk/Execution/System/Learning state, and shows stable reason codes plus human explanation for WAIT/BLOCKED/MISSED/INVALID/EXIT.  
**Status:** PROVISIONAL

## DEC-041 — Research documentation is consolidated by authority

**Decision:** There is no separate authoritative `OFFLINE_RESEARCH.md`. Chronological/offline methodology belongs to `RESEARCH_AND_VALIDATION.md`; discovery, invention and promotion each have their own documents.  
**Status:** PROVISIONAL

## DEC-042 — Account-size Gold risk profiles use hybrid sizing

**Decision:** Initial V1 profile boundaries are `SMALL $100–$299`, `MEDIUM $300–$999`, and `NORMAL $1,000+`. SMALL normally treats broker minimum `0.01` as the practical base unit and validates its real all-in risk; MEDIUM uses stepped dynamic lots; NORMAL uses fully dynamic percentage sizing. A theoretical raw lot below broker minimum is not by itself a trade blocker.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Reason:** Gold minimum-lot granularity can otherwise make small accounts artificially unable to trade.

## DEC-043 — Execution friction is part of effective monetary risk exactly once

**Decision:** Effective trade risk must account for executable entry/SL geometry plus spread, expected slippage reserve and commissions/fees according to broker semantics, without double-counting any cost already embedded in the executable quote/fill. A displayed Gold spread such as `$0.26` is converted through broker symbol/contract facts rather than assumed to equal the same account-currency cost.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-044 — Minimum-lot excess may preserve the opportunity while current entry is blocked

**Decision:** If broker minimum volume exceeds the profile hard risk ceiling at the current entry, the current plan is blocked, but the underlying opportunity may remain `ARMED` when the thesis is still valid and a naturally better structural entry could reduce risk. Structural SL is never artificially tightened to make the minimum lot fit.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-045 — Preserve useful GoldScalperAI dashboard observability

**Decision:** GoldSwingTraderAI may reorganize and improve the dashboard, but it must preserve useful operator-facing facts from the prior GoldScalperAI dashboard where the data remains meaningful: mode/runtime identity, Bid/Ask, spread, M5 candle timer, concise trend/structure, EMA20/EMA50, RSI, ATR, action/signal and reason, risk/lot, daily P/L/loss-limit visibility, position count/capacity, loss streak, and open-trade entry/SL/TP/objective context. New decision, execution, learning, backup and health panels are additive rather than a reason to remove this useful visibility.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-046 — Profile hard entry ceilings and daily loss locks

**Decision:** Initial V1 hard new-entry ceilings are `SMALL 7%`, `MEDIUM 5%`, `NORMAL 4%`. Initial UTC-risk-day loss locks are `SMALL 12%`, `MEDIUM 9%`, `NORMAL 7%`. These are hard limits, not normal Target Risk values; Target Risk and acceptable bands remain lower separately calibrated values.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Reason:** Preserve practical Gold trading room for small/medium accounts while keeping explicit upper bounds and a daily circuit breaker.

## Change rule

A decision may be superseded only by an explicit later decision entry that identifies the previous decision and explains the change. Historical decisions should not be silently rewritten to hide design evolution.
