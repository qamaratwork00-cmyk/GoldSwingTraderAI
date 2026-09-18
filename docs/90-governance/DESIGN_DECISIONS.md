# GoldSwingTraderAI — Design Decisions

**Status:** LIVING LEDGER  
**Version:** 1.7-design

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

## DEC-004 — Opportunity and entry timing are separate

**Decision:** A valid setup may stay `ARMED` while entry timing is poor.  
**Status:** PROVISIONAL

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

**Decision:** Wick/probe, qualified completed-candle break, confirmed BOS, MSS candidate, confirmed MSS and failed break are distinct evidence states rather than one binary flag.  
**Status:** PROVISIONAL

## DEC-021 — MSS means transition before new trend

**Decision:** A confirmed counter-structure MSS challenges the prior thesis and moves that timeframe toward transition; it does not by itself establish a fully confirmed opposite trend.  
**Status:** PROVISIONAL

## DEC-022 — Timeframes retain independent structure state

**Decision:** H4, H1, M15 and M5 structure states are maintained independently. Lower-timeframe change cannot silently overwrite higher-timeframe structure.  
**Status:** PROVISIONAL

## DEC-023 — Technical structure owns adaptive zones and location

**Decision:** Support/resistance is modeled as adaptive zones with quality/lifecycle. A separate Location/Target-Room view evaluates current price; location is important evidence but not a universal hard gate.  
**Status:** PROVISIONAL

## DEC-024 — Liquidity/SMC is contextual evidence, not mandatory confluence

**Decision:** Liquidity pools, sweeps, FVG, qualified OB and premium/discount are context-aware evidence and not mandatory for every trade.  
**Status:** PROVISIONAL

## DEC-025 — Indicators describe and normalize; price structure leads

**Decision:** EMA20/EMA50, RSI and ATR are initial quantitative tools. They support analysis but do not independently create or veto trades.  
**Status:** PROVISIONAL

## DEC-026 — Fundamental opinion and event safety are separate

**Decision:** Macro/fundamental context is soft evidence. Scheduled-event safety may become hard permission through risk/session state. Missing optional macro opinion does not equal missing required event safety.  
**Status:** PROVISIONAL

## DEC-027 — Structural Trade Plan before risk sizing

**Decision:** Entry reference, structural invalidation, volatility-aware stop buffer and objectives are defined before monetary sizing. Risk rejects an unaffordable plan rather than distorting the structural stop.  
**Status:** PROVISIONAL

## DEC-028 — Original R is immutable

**Decision:** Original approved risk distance/R remains immutable for analytics and lifecycle attribution even after SL/TP changes.  
**Status:** PROVISIONAL

## DEC-029 — UTC calendar risk day

**Decision:** Daily-risk accounting boundary is `00:00 UTC`, independent of XAU reopen/holiday labels.  
**Status:** PROVISIONAL

## DEC-030 — Centralized final broker-write permission gate

**Decision:** All irreversible MT5 create/modify/close actions must pass one centralized Execution Permission Gate/Broker Write Guard.  
**Status:** PROVISIONAL

## DEC-031 — DEMO-first is a release safeguard, not a permanent LIVE prohibition

**Decision:** Initial release authorizes broker writes only on approved DEMO. Future REAL uses the same strategy/risk/gate/execution path after explicit frozen release approval.  
**Status:** SUPERSEDED FOR V1 BY DEC-062  
**Note:** Retained as historical design evolution. V1 now defines only a positive DEMO guard and intentionally does not specify REAL authorization/hard-block behaviour.

## DEC-032 — One-shot irreversible submission with reconciliation

**Decision:** One Execution Intent permits at most one irreversible submit until reconciliation proves otherwise. Blind retry is prohibited.  
**Status:** PROVISIONAL

## DEC-033 — System health is separate from normal trading decisions

**Decision:** Decision attribution and technical System Health are separate. Normal WAIT/NEWS_BLACKOUT/LOSS_LOCKED are not automatically system errors.  
**Status:** PROVISIONAL

## DEC-034 — Persistent strategy/learning state is portable

**Decision:** Strategy Registry, genealogy, Champion/Challenger state, entry/exit learning, research/promotion history and critical lifecycle context survive restart/laptop migration.  
**Status:** PROVISIONAL

## DEC-035 — Public repository may back up project intelligence; financial-authority secrets do not belong there

**Decision:** Code/docs/strategy/learning/research state may be versioned for recovery; credentials/keys/tokens with financial or paid-service authority must never be committed.  
**Status:** PROVISIONAL

## DEC-036 — Single active execution controller

**Decision:** Only one runtime instance may hold broker-write authority for one managed account/symbol.  
**Status:** PROVISIONAL

## DEC-037 — Learning includes entry quality and exit/capture quality

**Decision:** Learning measures taken/missed/blocked/invalidated opportunities, MFE/MAE, capture efficiency and premature-exit cost, and proposes challengers rather than silently mutating production.  
**Status:** PROVISIONAL

## DEC-038 — Strategy discovery/invention is governed and declarative

**Decision:** Autonomous candidates use approved declarative primitives/recipes, retain genealogy/rejected memory, and cannot create arbitrary executable Python, change risk or call broker directly.  
**Status:** PROVISIONAL

## DEC-039 — Promotion uses evidence stages and one-shot final holdout

**Decision:** Candidate promotion proceeds through research, validation, locked candidate, final untouched holdout, stress, Shadow and DEMO Canary before production approval as applicable.  
**Status:** PROVISIONAL

## DEC-040 — Compact dashboard with restrained emojis and explicit reasons

**Decision:** Main terminal UX remains compact, uses meaningful status emojis, separates major state panels, and shows stable reason codes plus concise explanation.  
**Status:** PROVISIONAL

## DEC-041 — Research documentation is consolidated by authority

**Decision:** No separate authoritative `OFFLINE_RESEARCH.md`; methodology/discovery/invention/promotion remain in their respective authorities.  
**Status:** PROVISIONAL

## DEC-042 — Account-size Gold risk profiles use hybrid sizing

**Decision:** `SMALL $100–$299`, `MEDIUM $300–$999`, `NORMAL $1,000+`. SMALL normally uses practical `0.01` base/min-lot evaluation; MEDIUM stepped dynamic; NORMAL fully dynamic percentage sizing.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-043 — Execution friction is part of effective monetary risk exactly once

**Decision:** Effective trade risk accounts for executable geometry plus spread/slippage/fees according to broker semantics without double-counting.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-044 — Minimum-lot excess may preserve the opportunity while current entry is blocked

**Decision:** If minimum volume exceeds hard risk ceiling, current plan is blocked but opportunity may remain ARMED for a naturally better structural entry.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-045 — Preserve useful GoldScalperAI dashboard observability

**Decision:** Preserve useful prior dashboard facts including mode, Bid/Ask, spread, M5 timer, trend, EMA20/50, RSI, ATR, signal/reason, risk/lot, daily P/L/loss limit, position count, loss streak and open-trade context.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-046 — Profile hard entry ceilings and daily loss locks

**Decision:** New-entry ceilings: `SMALL 7%`, `MEDIUM 5%`, `NORMAL 4%`. Daily locks: `SMALL 12%`, `MEDIUM 9%`, `NORMAL 7%`.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-047 — Initial normal and elevated Gold risk bands

**Decision:** `SMALL 3.0–4.5%, >4.5–6.5%`; `MEDIUM 2.0–3.0%, >3.0–4.5%`; `NORMAL 1.0–2.0%, >2.0–3.5%`.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-048 — V1 allows one independently risk-bearing Gold position

**Decision:** Capacity is `0/1`; opposite opportunity first informs Trade Manager rather than opening automatic hedge/second position.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-049 — Unexpected manual/foreign Gold exposure blocks new bot entry

**Decision:** External Gold positions are never managed as bot-owned and block new bot Gold entries until reconciled clear.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-050 — Bot-managed Gold positions flatten before scheduled market closure

**Decision:** V1 does not intentionally carry bot-managed Gold through daily XAU break/weekend closure. PRE_CLOSE blocks new entries and requires governed flatten.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-051 — Initial scheduled-news blackout policy is short and tiered

**Decision:** TIER 1 blocks `-15/+15 min`, linked critical clusters through final item +15; TIER 2 blocks `-5/+5 min`; TIER 3 has no automatic hard blackout. Scheduled news does not automatically close an open managed trade.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-052 — Post-news warmup is evidence-driven, not a long fixed delay

**Decision:** After minimum blackout, entry remains paused only while spread/quotes/data/volatility are dislocated. Severe dislocation requires one clean completed M5 candle plus normalized execution conditions. Missing required calendar truth becomes `NEWS_SAFETY_UNKNOWN`.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-053 — Manual daily-loss reset is disabled by default and limited to one per UTC day

**Decision:** Manual loss reset remains available as a governed feature but is OFF by default. If explicitly enabled, at most one `R,R` double-confirm reset may occur per UTC risk day, only from `LOSS_LOCKED`. It preserves cumulative broker/day P/L and audit history and cannot clear unrelated hard blockers.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-054 — Cooldown targets churn, not every loss

**Decision:** One ordinary losing trade does not trigger global cooldown. V1 permits at most one genuinely fresh re-entry in the same Market Episode; if that re-entry also loses, the episode is locked. Three consecutive closed bot-trade losses trigger a minimum 30-minute global cooldown, and release also requires fresh completed M15 context plus a fresh valid opportunity/episode. Execution/shock cooldown remains condition-based until the responsible market/execution fault normalizes.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION

## DEC-055 — Initial daily/weekend close and reopen timing

**Decision:** Timing is relative to the broker's verified XAU session-close schedule rather than a fixed local/server clock. Daily break: no new entry from `T-20m`, mandatory governed flatten from `T-10m`; daily reopen requires normalized execution/data plus one clean completed M5 candle. Weekend: no new entry from `T-60m`, mandatory flatten from `T-30m`; weekend reopen requires gap assessment, normalized execution/data and two clean completed M5 candles.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Reason:** Avoid known closure/reopen gap risk without relying on DST-sensitive guessed clock times.

## DEC-056 — Daily loss lock uses cash-flow-adjusted account-equity safety P/L

**Decision:** `AccountSafetyPL = CurrentVerifiedEquity - DayStartEquity - NetNonTradingCashFlowSinceDayStart`. This account-safety metric, including floating account drawdown through broker equity, drives the daily loss lock. Realized/floating P/L, commissions/swaps/fees already contained in equity are not added again. Deposits/withdrawals/identifiable non-trading adjustments are removed from the trading P/L calculation. Bot strategy-performance P/L is tracked separately so manual/foreign activity does not contaminate strategy analytics. Manual reset creates a new audited cycle reference while cumulative day P/L remains visible.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Reason:** Protect the actual account while keeping clean bot-performance attribution and avoiding double-counting.

## DEC-057 — Spread and price-drift protection is dynamic and normalized

**Decision:** V1 uses a healthy broker/symbol spread baseline rather than a single fixed Gold spread number. Spread Ratio `<=1.50` is normal; `>1.50–2.25` is elevated and requires full revalidation but is not an automatic block; `>2.25` blocks the current entry. Spread also blocks if it exceeds 25% of approved entry-to-structural-SL price distance. Adverse price drift from Approved Entry Reference is normalized by planned stop distance: `<=10%` normal revalidation, `>10–20%` elevated full revalidation, `>20%` blocks the current Execution Intent/returns to WAIT if thesis survives. Any fresh drift that breaks risk, stop, target-room or chase validity blocks regardless of percentage.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Reason:** Avoid both over-restrictive fixed-pip filters and uncontrolled chasing/execution friction.

## DEC-058 — Initial structural RR guard is bounded but not over-restrictive

**Decision:** V1 rejects a current entry plan when credible structural target room is below `1.20R`. `1.20R–<1.50R` is marginal/conditional and requires a credible larger expansion path; initial V1 expects roughly `2.0R+` Expansion Target room with acceptable path quality. `1.50R–<2.00R` is good and `2.00R+` is strong. `3R/4R+` represents large-move/runner potential, not a guaranteed outcome. Higher RR or strategy score never authorizes higher monetary risk.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Reason:** Reject poor target economics without creating an ultra-rare high-RR-only bot.

## DEC-059 — Primary target is a checkpoint; Expansion is the normal broker objective; Runner must be earned

**Decision:** V1 uses structural/liquidity objectives rather than fixed 100/200/300-pip TP. Primary Structural Target is normally a management checkpoint, not an automatic full exit. A valid Expansion Target is the default initial broker TP; if no valid Expansion Target exists, a valid Primary Target may be used. Runner extension requires fresh acceptance/continuation evidence plus a newly defined objective and may not occur merely because price is profitable. Only one current Runner Objective is active at a time; any further extension requires fresh evidence. PRE_CLOSE flatten overrides runner logic.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Reason:** Preserve the ability to capture large Gold expansions while keeping every TP extension structurally anchored and auditable.

## DEC-060 — V1 core logic does not depend on partial closes

**Decision:** V1 must remain fully correct for an indivisible broker-minimum `0.01` position. The baseline manager handles the full position through HOLD/PROTECT/TRAIL/RUNNER/EXIT and does not require partial profit taking. Partial-profit policies may be researched for a later version/larger executable volumes but are not an implicit V1 dependency.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Reason:** Keep behaviour consistent across small accounts and avoid designing core exit logic around volume reductions that may not be executable.

## DEC-061 — Cross-machine execution ownership uses lease + monotonic fencing

**Decision:** V1 permits one PRIMARY execution controller for a managed account/symbol. Controller ownership uses a shared coordination store with atomic acquisition, authoritative expiry semantics and a monotonic fencing epoch. Initial renewal target is `10s` and lease TTL is `30s`. Every irreversible broker write must freshly verify current holder, unexpired lease and matching current epoch. A second laptop remains Observer while another valid holder exists. Standby takeover is allowed only after authoritative lease expiry, must obtain a new epoch atomically and must complete durable-state + broker reconciliation before becoming PRIMARY READY. A stale old epoch can never regain write authority by local assumption.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Reason:** Prevent split-brain/duplicate broker writes while still allowing controlled recovery after laptop/process failure.

## DEC-062 — V1 defines only a positive DEMO guard

**Decision:** V1 broker-write environment permission is granted only when the connected MT5 account is positively verified as DEMO: `DEMO_GUARD = PASS`. If DEMO status is not verified, broker-write permission is not granted. V1 intentionally does **not** define a separate REAL authorization workflow, REAL hard-block contract, LIVE override or alternate REAL execution path. A verified DEMO account is real-time broker execution on that DEMO account, not dry-run simulation.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Supersedes for V1:** DEC-031 environment-policy wording.  
**Reason:** Keep the first implementation narrowly scoped to the user's requested DEMO guard without inventing unnecessary REAL-account policy.

## DEC-063 — V1 implementation follows a frozen lightweight production-code standard

**Decision:** V1 source code must follow `docs/60-engineering/CODING_STANDARD.md`: Python 3.11+; standard-library-first/minimal runtime dependencies; official MetaTrader5 boundary; pure functions for deterministic calculations where practical; classes only for genuine state/resource/lifecycle ownership; typed dataclasses/enums/IDs where they protect semantics; one verified snapshot/shared derived facts rather than duplicate MT5 reads/calculations; no giant all-in-one file and no unnecessary micro-file/framework/factory/service-manager architecture; concise comments/docstrings that explain why/safety/chronology; explicit non-silent error handling; structured secret-safe logging; heavier research dependencies isolated from normal runtime; and a code-quality review as part of every phase exit gate.  
**Status:** FROZEN FOR INITIAL IMPLEMENTATION  
**Reason:** Keep the bot expert-level, optimized, clean and maintainable without allowing unnecessary code bulk/architecture to become an operational risk.

## Change rule

A decision may be superseded only by an explicit later decision entry identifying the previous decision and explaining the change. Historical decisions should not be silently rewritten to hide design evolution.