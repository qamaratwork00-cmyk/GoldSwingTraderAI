# GoldSwingTraderAI — Final Release Audit

**Status:** CANDIDATE FOR ADOPTION  
**Version:** 0.1-audit-template  
**Authority:** Final evidence summary and release boundary

## 1. Purpose

This file is the final audit template. It is intentionally written as a
repeatable record rather than as a permanent claim that the project is
finished.

The audit answers four questions:

1. Which source revision was examined?
2. Which deterministic and external checks passed?
3. Which evidence is still missing?
4. What exact release scope is allowed?

## 2. Audit identity

| Field | Value to record |
|---|---|
| Audit ID | Unique immutable identifier |
| Git revision | Commit hash |
| Date/time | UTC |
| Release owner | Name |
| Target | DEMO account, symbol and broker |
| Python/OS | Exact environment |
| Configuration | Redacted configuration identity |
| Evidence package | Path and fingerprint |

## 3. Architecture audit

- [ ] The runtime follows the documented startup graph.
- [ ] MT5 reads enter through the single read boundary.
- [ ] The six strategy families remain descriptive hypotheses.
- [ ] Decisions, risk, permission and execution are separate authorities.
- [ ] All broker writes pass through the central gate and writer.
- [ ] Trade Manager uses verified position truth.
- [ ] Persistence, checkpoint and backup boundaries match the documents.
- [ ] Research cannot directly change live authority.

## 4. Deterministic evidence

| Area | Result | Evidence | Boundary |
|---|---|---|---|
| Domain/model contracts | PENDING | Test output | Does not prove MT5 |
| Market/intelligence | PENDING | Test output/replay | Does not prove current feed |
| Strategy/decision | PENDING | Test output/replay | Does not prove profitability |
| Risk/permission | PENDING | Test output | Does not prove broker margin |
| Execution/reconciliation | PENDING | Test output | Does not prove real terminal |
| Persistence/recovery | PENDING | Test output/checkpoint | Does not prove two-machine failover |
| Dashboard/operator | PENDING | Test output/screenshot | Does not prove safe authority |
| Research/promotion | PENDING | Evidence package | Does not prove future performance |

## 5. External evidence

| Drill | Result | Required retained proof |
|---|---|---|
| Fresh Windows setup | PENDING | Commands, environment and output |
| MT5 DEMO initialization | PENDING | Account/server identity |
| Fresh market data | PENDING | Quote and candle timestamps |
| DEMO OPEN | PENDING | Intent, request, broker ticket, reconciliation |
| DEMO MODIFY | PENDING | Before/after position truth |
| DEMO CLOSE | PENDING | Close result and final position truth |
| Restart recovery | PENDING | State/checkpoint/reconciliation trace |
| Fresh-machine restore | PENDING | Restore commands and integrity result |
| Stale-primary fencing | PENDING | Lease/epoch trace |
| Standby takeover | PENDING | Coordination and broker proof |
| Public backup staging | PENDING | Secret scan and artifact fingerprint |

## 6. Current release decision

Use exactly one of these statements:

~~~text
RELEASED — [scope] verified at [revision].
RELEASED-DEMO-OBSERVATION — read-only DEMO runtime verified; broker writes
remain unverified.
PARTIAL — deterministic foundation verified; external evidence remains open.
BLOCKED — release cannot proceed because [reason].
~~~

Do not use “DEMO VERIFIED” until the real DEMO OPEN/MODIFY/CLOSE/restart
sequence has been completed and reconciled.

## 7. Known boundaries

The audit must state clearly when any of the following remain unverified:

- external session/news provider operation;
- current broker schedule or holiday data;
- real spread, slippage and margin behaviour;
- two-machine shared coordination;
- fresh-machine restore;
- broker order acknowledgement edge cases;
- historical sample breadth and walk-forward calibration;
- production/REAL authorization, which is outside V1.

## 8. Sign-off

| Role | Name | Decision | Date | Evidence reference |
|---|---|---|---|---|
| Developer |  |  |  |  |
| Runtime/operator |  |  |  |  |
| Research reviewer |  |  |  |  |
| Release owner |  |  |  |  |
