# GoldSwingTraderAI — Risk Contract

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Risk-policy intent and separation from strategy scoring

## Core principle

Risk is independent authority. A strong strategy score cannot make an unaffordable or unsafe trade acceptable.

## Risk is not a weighted score

Risk outputs hard states such as:

- PASS
- BLOCK
- UNKNOWN

Unknown financial truth should block new entries until verified.

## Per-trade risk

The final per-trade risk percentages, minimum-lot ceiling and aggregate open-risk limits for GoldSwingTraderAI are not yet frozen. The system is intended to use broker-aware monetary SL risk, dynamic lot sizing, broker volume steps, margin checks and structural stops rather than arbitrary fixed-lot sizing.

A stop should not be artificially tightened merely to force the minimum lot to fit a risk budget.

## Daily loss limit

GoldSwingTraderAI will retain the deliberate daily-loss-lock concept used in the reference system. When the configured daily loss limit is hit:

- new entries are blocked;
- open-trade management remains active;
- broker P/L/history is not erased;
- the dashboard must clearly display the lock.

The exact percentage/tiers for this new swing system remain an open design item unless explicitly frozen later.

## Manual loss reset

The current design intent is to retain the reference system's governed manual-reset behaviour rather than remove the feature.

Manual reset should include:

- explicit deliberate operator confirmation (for example a two-step/double-key action);
- a bounded reset count per risk cycle;
- current verified broker P/L as the new reference rather than erasing history;
- durable audit/journal record of the reset;
- clear dashboard visibility that an operator reset occurred.

The exact automatic risk-cycle rollover boundary and its relationship to XAU reopen remain an open item to be frozen in the session/risk state-machine document.

## Trade frequency

There is no required minimum trade count per day. The scorer must not reduce a market-quality score merely because several trades have already occurred.

The current expectation is that a healthy active system may often produce more opportunities than a traditional low-frequency swing bot, but frequency must come from valid market episodes rather than quota chasing.

A generous emergency trade-count circuit breaker may be used later as a runaway-software safeguard. Its exact value is not frozen.

## Re-entry

Re-entry is allowed only when a genuinely fresh market event/structure justifies it. Repeating the same unchanged setup after a loss is not valid re-entry.

A `Market Episode` identity should help distinguish:

- same stale thesis repeated;
- legitimate new pullback/retest;
- fresh liquidity event;
- structurally new second-chance opportunity.

## Position count

One-position-at-a-time is currently the preferred provisional design because it keeps exposure, trade management and restart reconciliation clear. This remains open to final confirmation before risk freeze.

## Prohibited risk behaviour

- martingale;
- averaging down to rescue a losing thesis;
- silent risk-limit expansion by strategy/research code;
- changing risk because a score is high;
- redefining original R after stop movement;
- blind duplicate order submission after ambiguous broker acknowledgement.
