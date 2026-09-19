# GoldSwingTraderAI — Design Decision Ledger

**Status:** CANDIDATE FOR ADOPTION  
**Version:** 0.1-decision-ledger  
**Authority:** Durable project decisions, supersession and rationale

## 1. How to read this ledger

This ledger protects the reasoning behind the architecture. A future change
must not quietly reverse a decision because the implementation file changed.
If a decision is replaced, keep the old row, mark it SUPERSEDED and add the new
decision with its reason and affected documents.

The authoritative behaviour remains in the relevant contract document. This
ledger explains why that contract exists.

| Status | Meaning |
|---|---|
| ACTIVE | Applies to the current V1 design |
| SUPERSEDED | Kept for history; a later decision is authoritative |
| CALIBRATE | Architecture is fixed; numerical values require evidence |
| EXTERNAL | Requires real broker/provider/operational proof |

## 2. Product and architecture decisions

| ID | Decision | Reason and consequence | Status |
|---|---|---|---|
| DEC-001 | Documentation is built before implementation changes | The manual is the design contract; code must have an owner and proof map | ACTIVE |
| DEC-002 | Use a Trading Floor model | Parallel desks can produce independent evidence while authority remains ordered | ACTIVE |
| DEC-003 | BUY and SELL are independent theses | A strong BUY must not be created only by negating a weak SELL, and vice versa | ACTIVE |
| DEC-004 | Opportunity and Entry Timing are separate | A valid market episode may wait for a fresh M5 trigger | ACTIVE |
| DEC-005 | Safety rules are hard gates, not weighted score points | Risk, identity and broker safety cannot be averaged away | ACTIVE |
| DEC-006 | Market structure is the primary directional evidence | Indicators support interpretation but do not replace causal structure | ACTIVE |
| DEC-007 | Six strategy families form the initial floor | Coverage is explicit and comparable across trend, breakout, reversal and compression | ACTIVE |
| DEC-008 | FVG, Order Block and indicators are reusable primitives | They are evidence components, not independent permission authorities | ACTIVE |
| DEC-009 | Trade Manager is part of the trading floor | A system is incomplete if it can enter but cannot protect, trail and exit | ACTIVE |
| DEC-010 | Structural trailing is preferred | Protection follows invalidation and structure rather than arbitrary points | ACTIVE |
| DEC-011 | Setup and episode state persist across restarts | A restart must not invent a new opportunity or forget risk lineage | ACTIVE |
| DEC-012 | Holiday caution is distinct from a normal closed session | A holiday may have unusual liquidity without being treated as a normal closure | ACTIVE |
| DEC-013 | History is rolling, while evidence is durable | Operational state can be compacted; research evidence must remain reproducible | ACTIVE |
| DEC-014 | Daily loss lock and manual reset are explicit | Risk-day state survives restart and cannot be bypassed by process restart | ACTIVE |
| DEC-015 | No fixed daily trade target | Quality and permission matter more than a forced trade count | ACTIVE |
| DEC-016 | Strategy invention is governed | New ideas need evidence, complexity controls, holdout and promotion | ACTIVE |
| DEC-017 | The final build prompt is a handoff contract | A new coding session must recover the same architecture and gates | ACTIVE |

## 3. Chronology and structure decisions

| ID | Decision | Reason and consequence | Status |
|---|---|---|---|
| DEC-018 | Swing points have a lifecycle | Candidate, confirmed, protected and external are not interchangeable | ACTIVE |
| DEC-019 | Pivot time and confirmation time are separate | The system must not pretend a later confirmation was known at the pivot | ACTIVE |
| DEC-020 | Breaks are graduated | Probe, qualified break, confirmed BOS, MSS candidate, confirmed MSS and failure carry different evidence | ACTIVE |
| DEC-021 | MSS is a transition, not a normal trend label | Reversal evidence needs different semantics from continuation | ACTIVE |
| DEC-022 | Timeframes have independent jobs | H4/H1/M15/M5/M1 facts must not be collapsed into one opaque signal | ACTIVE |
| DEC-023 | Technical zones describe location | Trendline, Fibonacci and POC can improve context but cannot create permission alone | ACTIVE |
| DEC-024 | Liquidity is contextual | A pool, sweep, FVG or OB is meaningful only in the causal market context | ACTIVE |
| DEC-025 | Indicators support, never dominate | EMA, RSI, ATR and volatility describe state; they do not override structure | ACTIVE |
| DEC-026 | Macro context and event safety are separate | A macro bias can inform analysis while an event blackout can hard-block entries | ACTIVE |
| DEC-027 | A Trade Plan exists before risk sizing | Stop geometry and targets define the risk unit before money is calculated | ACTIVE |
| DEC-028 | Original R is immutable | Later management must be measured against the entry plan, not a moving definition | ACTIVE |
| DEC-029 | Risk day is UTC-based | Restart and location must not change the daily accounting boundary | ACTIVE |

## 4. Risk and execution decisions

| ID | Decision | Reason and consequence | Status |
|---|---|---|---|
| DEC-030 | One central execution gate owns final permission | There must be one auditable answer before any broker write | ACTIVE |
| DEC-031 | REAL wording from the early design is not a V1 authority | V1 is DEMO-only; old REAL wording is retained only as history | SUPERSEDED BY DEC-062 |
| DEC-032 | Intent is one-shot and reconciliation-driven | An unknown broker acknowledgement must not cause an accidental duplicate | ACTIVE |
| DEC-033 | Health is separate from trading permission | A healthy process may still be blocked by data, risk or session state | ACTIVE |
| DEC-034 | Strategy and learning state are portable | Offline research must be reproducible without importing broker authority | ACTIVE |
| DEC-035 | Public intelligence contains no secrets | Backups and evidence may be published only after scanning and staging | ACTIVE |
| DEC-036 | One active controller exists per account/symbol scope | Multiple writers create split-brain risk | ACTIVE |
| DEC-037 | Learning covers entry and exit outcomes | Trade Manager behaviour is part of performance, not an afterthought | ACTIVE |
| DEC-038 | Discovery is declarative and governed | Search space must be inspectable instead of hidden arbitrary code | ACTIVE |
| DEC-039 | Promotion requires holdout evidence | In-sample improvement alone cannot change a live rule | ACTIVE |
| DEC-040 | Dashboard is compact but reason-rich | Operators need the current authority and the reason, not a wall of raw values | ACTIVE |
| DEC-041 | Research topics have one consolidated home | Duplicate research rules create conflicting authority | ACTIVE |
| DEC-042 | The early $100 lower risk boundary is not authoritative | Account profiles were later formalized with exact bands and ceilings | SUPERSEDED BY DEC-064 |
| DEC-043 | Execution friction is applied once | Spread/slippage must not be charged repeatedly by different layers | ACTIVE |
| DEC-044 | Minimum-lot failure preserves the opportunity | An unaffordable minimum lot is a risk block, not a reason to invent a signal | ACTIVE |
| DEC-045 | Useful dashboard information is preserved during redesign | Improving documentation or UI must not remove operational truth | ACTIVE |
| DEC-046 | Entry ceilings and daily locks are hard limits | Score cannot override account-level affordability or loss protection | ACTIVE |
| DEC-047 | Normal and elevated risk bands are explicit | Small changes in profile must be visible and testable | ACTIVE |
| DEC-048 | V1 allows one managed Gold position | Capacity is conservative until evidence justifies expansion | ACTIVE |
| DEC-049 | Foreign Gold exposure blocks new entry | Unknown or external exposure cannot be counted as zero | ACTIVE |
| DEC-050 | Flatten before a hard session closure | Open risk must be handled before the broker/session boundary | ACTIVE |
| DEC-051 | News uses tiers and windows | The safety response depends on event severity and timing | ACTIVE |
| DEC-052 | Post-news warmup is explicit | The first quote after an event is not automatically safe | ACTIVE |
| DEC-053 | Manual reset is disabled by default and bounded | A reset cannot become a hidden loss-lock bypass | ACTIVE |
| DEC-054 | Cooldown is not triggered by every loss | Cooldown responds to the defined consecutive-loss condition | ACTIVE |
| DEC-055 | Close and reopen windows are configuration facts | Timing policy must be explicit and testable | ACTIVE |
| DEC-056 | AccountSafetyPL is the risk-day accounting basis | Realized, floating and non-trading cash flow are handled consistently | ACTIVE |
| DEC-057 | Spread and drift thresholds are dynamic | Execution friction must be judged against current context, not one fixed number | ACTIVE |
| DEC-058 | Minimum R:R is a hard plan guard | A trade with insufficient target room is not rescued by a score | ACTIVE |
| DEC-059 | Targets and runner behaviour are explicit | Management needs a declared hierarchy instead of ad hoc exits | ACTIVE |
| DEC-060 | Partial close is not a V1 dependency | Management must remain safe on brokers/accounts where partial close is unavailable | ACTIVE |

## 5. Coordination, coding and runtime decisions

| ID | Decision | Reason and consequence | Status |
|---|---|---|---|
| DEC-061 | Lease and fencing protect ownership | A stale primary must be unable to write after takeover | ACTIVE |
| DEC-062 | V1 is positive DEMO-only | Every broker write must pass explicit DEMO Guard verification; REAL is outside release scope | ACTIVE |
| DEC-063 | Coding standard is frozen | Expert-level code needs deterministic boundaries, typing, tests and safe comments | ACTIVE |
| DEC-064 | No arbitrary minimum account balance | Affordability is calculated from broker/account facts and the selected profile | ACTIVE |
| DEC-065 | SQLite is the initial durable coordination store | It provides transactional local state and a clear migration boundary | ACTIVE |
| DEC-066 | Trendline, Fibonacci and POC are optional bonus evidence | They enrich confluence without becoming hidden hard gates | ACTIVE |
| DEC-067 | Discovery must remain live | A governed candidate pipeline must not be a dead placeholder | ACTIVE |
| DEC-068 | Closed market means wait, not process death | The bot remains observable and can recover at reopen | ACTIVE |
| DEC-069 | Readiness is visible and persistent | Stale data and startup recovery must not look like a crashed bot | ACTIVE |
| DEC-070 | Documentation completeness is a release concern | Every implementation area needs a guide and proof destination | ACTIVE |
| DEC-071 | Documentation has an executable structural gate | Metadata, links, source/test coverage and diagrams are checked before adoption | ACTIVE |

## 6. Changing a decision

A proposed change must include:

1. the current decision ID;
2. the observed problem or new evidence;
3. the alternative considered;
4. safety and recovery impact;
5. affected code, tests and documents;
6. whether the change is architecture, calibration or external proof;
7. a rollback or supersession statement.

Do not edit a single implementation file and call that a design decision.
