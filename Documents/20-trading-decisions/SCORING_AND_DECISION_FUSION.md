# GoldSwingTraderAI — Scoring and Decision Fusion

**Status:** PROVISIONAL
**Version:** 0.1-fusion
**Authority:** BUY/SELL thesis construction, conflict, coverage and attribution

## Purpose

Fusion turns independent family evidence into two competing analytical theses.
It must preserve why a direction leads, what opposes it and how much evidence
was available. It does not turn a score into risk or broker permission.

## Fusion pipeline

~~~mermaid
flowchart TB
    FAMILIES["Six FamilyReports"] --> BONUS["Bounded optional confluence"]
    BONUS --> BUY["Build BUY thesis"]
    BONUS --> SELL["Build SELL thesis"]
    BUY --> RED["Red Team, correlation and coverage"]
    SELL --> RED
    RED --> BOARD["DecisionBoard — edge, conflict, reasons"]
    BOARD --> OPPORTUNITY["Opportunity identity/lifecycle"]
    OPPORTUNITY --> TIMING["M5 Entry Timing"]
~~~

## Independent theses

BUY and SELL use the same evidence independently. The baseline can rank the
strongest three same-direction family cases using bounded weights:

~~~text
primary 65% + secondary 25% + tertiary 10%
~~~

Small bounded synergy may be applied when support is not materially
correlated. Scores remain configurable implementation baselines subject to
replay calibration.

## Conflict and Red Team

Examples:

~~~text
BUY 88 / SELL 25 → clear BUY edge
BUY 88 / SELL 84 → BUY leads but conflict is high
~~~

Red Team records strong opposition, low coverage, correlated support,
extension, poor room and no edge. These reasons may produce WAIT or lower
confidence; they are not substitutes for risk/news/controller BLOCK.

## Coverage and UNKNOWN

Coverage says how much expected analytical evidence was available. Missing
optional inputs are omitted/reweighted, not silently treated as bearish zero.
Required financial/session/order truth is kept outside the weighted market score.

## Action meanings

~~~text
ENTER BUY | ENTER SELL | WAIT | MISSED | INVALID
~~~

BLOCKED is a downstream hard-authority result. A dashboard and research record
must preserve both the analytical result and the hard blocker, including
Would Otherwise Trade where meaningful.

## Score interpretation

Human bands may describe weak, developing, valid, strong and exceptional
evidence, but thresholds do not override hard authorities or create risk.

## Implementation and tests

decisions/fusion.py builds the DecisionBoard; decisions/snapshot.py stores the
typed result; decisions/opportunity.py preserves identity; decisions/timing.py
evaluates current timing. Tests are in test_strategy_decisions.py.

## Research and dashboard

Research separates strategy weakness from safety-blocked counterfactuals. The
dashboard shows BUY thesis, SELL thesis, edge, conflict, opportunity, timing,
coverage, leading family and hard permission separately.

## Explicit non-goals

Fusion must not query MT5, hide opposing evidence, turn missing optional facts
into a hard block, change risk, or call the execution gate.

