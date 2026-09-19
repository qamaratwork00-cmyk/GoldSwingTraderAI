# GoldSwingTraderAI — Shared Glossary

**Status:** CANDIDATE FOR ADOPTION
**Version:** 0.1-foundation
**Authority:** Shared terminology used by the new Documents manual

## How to use this file

Words that sound similar often have different safety meaning. This glossary
gives each important term one plain-language definition. Topic contracts may
add detail, but they must not redefine a term silently.

| Term | Plain-language meaning |
|---|---|
| Approved Entry Reference | The planned price/zone used to measure later drift; it is not necessarily the final fill |
| Account Safety P/L | Equity change adjusted for non-trading cash flows; used for the real account loss lock |
| ARMED | An opportunity is still valid enough to watch, but current timing may not be executable |
| Broker truth | Fresh facts read from MT5 about account, symbol, quotes, positions, orders or deals |
| Candidate | A research hypothesis that has not been promoted into production |
| Completed candle | A bar whose close is known; structural decisions may use it, while forming bars are not structural proof |
| Confluence | Optional supporting evidence that agrees with an existing thesis; it is not automatically a hard gate |
| Controller | The lease/fencing authority deciding which runtime may write for an account/symbol |
| DEMO Guard | Positive verification that the connected MT5 account is DEMO; V1 writes require PASS |
| Decision Snapshot | Immutable analytical result for one cycle, before hard execution permission |
| Data Quality | HEALTHY, INSUFFICIENT, STALE, SPARSE, CORRUPT or UNKNOWN description of required market facts |
| Entry Timing | The question “is this moment efficient enough to act?” after an opportunity exists |
| Episode / Market Episode | A coherent market event used to group opportunity, re-entry and research evidence |
| Execution Intent | Durable one-shot record describing a create, modify or close action before broker submission |
| Expansion Target | The normal larger structural objective and usually the initial broker TP in V1 |
| FVG | Fair Value Gap; a three-candle imbalance primitive, not a universal requirement |
| Hard authority | A subsystem whose BLOCK or UNKNOWN cannot be overridden by a score |
| Intelligence Snapshot | Shared, read-only collection of market evidence derived from one market snapshot |
| Original R | Immutable original approved risk distance used for lifecycle and research accounting |
| Opportunity | A directional idea worth tracking, independent of whether current timing is ready |
| POC | Point of Control from broker-local volume profile; real volume is preferred and tick-volume approximation is labelled |
| Primary Target | First meaningful objective and management checkpoint; touching it does not require full exit |
| PROTECT | Management action that reduces open risk using an earned structural reference |
| READY | Current analytical/runtime prerequisites are satisfied; it still does not replace final gate checks unless the context says so |
| READINESS mode | Read-only MT5 inspection/monitor; strategy and broker writes are disabled |
| Reconciliation | Comparing durable intent/context with fresh broker positions/orders/deals to establish truth |
| Red Team | Explicit challenge to the leading thesis using opposing or weak-quality evidence |
| Runner | Continuation beyond the normal objective, allowed only after a new objective is earned |
| Structural invalidation | Price behaviour that proves the original market thesis wrong |
| Trade Plan | Structural entry, invalidation/SL, objectives and original-R geometry created before monetary sizing |
| UNKNOWN | Required truth cannot be trusted; hard authorities fail closed rather than guessing |
| WAIT | The idea may survive, but timing or current geometry is not good enough now |

## State words

The manual uses three different categories:

1. Analytical states: DISCOVERED, ARMED, WAITING, READY, MISSED, INVALIDATED.
2. Hard permission states: PASS, BLOCK, UNKNOWN, ALLOW.
3. Operational health states: OK, WARN, DEGRADED, BLOCKED, ERROR.

They must not be mixed. For example, ENTRY_EXTENDED is normally an analytical
WAIT reason, while DATA_CORRUPT is an operational fault and DEMO_GUARD_NOT_
VERIFIED is a hard permission failure.

