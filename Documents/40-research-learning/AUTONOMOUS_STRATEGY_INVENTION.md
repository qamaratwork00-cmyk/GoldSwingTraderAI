# GoldSwingTraderAI — Autonomous Strategy Invention

**Status:** PROVISIONAL
**Version:** 0.1-invention
**Authority:** Automatic creation of bounded declarative research hypotheses

## Purpose

Invention turns recurring evidence into a candidate recipe and then stops at
governance. It may invent a hypothesis, not executable authority.

## Working path

~~~mermaid
flowchart TB
    EVIDENCE["Outcome-labelled episodes"] --> HYPOTHESIS["Declarative variant or new-family hypothesis"]
    HYPOTHESIS --> CHECK["Primitive, chronology and complexity validation"]
    CHECK --> REGISTRY["Candidate or suppression reason"]
    REGISTRY --> PROMOTION["Governed validation and promotion"]
~~~

The feature is operational only when the whole path is connected:
durable journal → approved mapping → recurring cluster → candidate/suppression
→ durable registry → promotion lifecycle.

## Approved primitive and candidate format

Candidate data can include required/optional approved primitives, parent family,
preferred regime, timing, invalidation, target model, source episode IDs,
fingerprint and status. It cannot contain eval, exec, generated Python,
MetaTrader5 calls, risk limits or permission overrides.

## Triggers and classification

Recurring meaningful missed moves, false-entry clusters, premature exits,
high-capture sequences and regime deterioration may trigger invention. A
candidate close to an existing family is a VARIANT. A materially different
pattern may be NEW_FAMILY. Adding one extra RSI/FVG/Trendline/Fibonacci/POC
condition is not automatically a new family.

## Source and tests

research/invention.py owns automatic candidate generation;
episode_journal.py supplies evidence; discovery.py validates primitives and
similarity; promotion.py owns later stages.

Tests: test_discovery_invention.py, test_discovery_journal.py and
test_promotion_governance.py.

## Dashboard and failure

Show candidate health, last suppression reason and Broker Authority: NONE.
Eligible evidence with no candidate and no suppression is DEGRADED. Rejected
and duplicate memory survives restart.

## Explicit non-goals

No executable code generation, production mutation, risk/broker authority,
unlimited filter recipes, final-holdout iteration or self-promotion.

