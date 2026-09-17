# GoldSwingTraderAI — Design Decisions

**Status:** LIVING LEDGER  
**Version:** 0.2-design

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
**Reason:** Reduce noise and look-ahead while retaining earlier opportunity/timing awareness.

## DEC-019 — Pivot time and confirmation time are distinct

**Decision:** Every confirmed swing records both the time of the price extreme and the later time when confirmation became available. Replay/live logic may not use the swing before its confirmation time.  
**Status:** PROVISIONAL  
**Reason:** Prevent hidden future-bar leakage from pivot algorithms.

## DEC-020 — Structural breaks use graduated states

**Decision:** Wick/probe, qualified completed-candle break, confirmed BOS, MSS candidate, confirmed MSS and failed break are distinct evidence states rather than one binary `break=true` flag.  
**Status:** PROVISIONAL  
**Reason:** Allow earlier strong opportunities without falsely claiming mature structure confirmation.

## DEC-021 — MSS means transition before new trend

**Decision:** A confirmed counter-structure MSS challenges the prior thesis and moves that timeframe toward transition; it does not by itself establish a fully confirmed opposite trend.  
**Status:** PROVISIONAL  
**Reason:** Prevent one local counter-break from flipping the entire directional model.

## DEC-022 — Timeframes retain independent structure state

**Decision:** H4, H1, M15 and M5 structure states are maintained independently. Lower-timeframe structural change may influence scores/timing but cannot silently overwrite higher-timeframe structure.  
**Status:** PROVISIONAL

## Change rule

A decision may be superseded only by an explicit later decision entry that identifies the previous decision and explains the change. Historical decisions should not be silently rewritten to hide design evolution.