# GoldSwingTraderAI — Risk Contract

**Status:** PROVISIONAL — IMPLEMENTED BASELINE  
**Version:** 1.0-implementation  
**Authority:** Monetary risk, account-size risk profiles, dynamic/hybrid lot sizing, exposure, daily-loss/manual-reset semantics and risk-policy invariants.  
**Depends on:** `../20-trading-decisions/TRADE_PLAN.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Core principle

Risk is independent authority. A strong strategy score cannot make an unaffordable or unsafe trade acceptable.

> **Market logic chooses the structural plan. Risk decides how that plan can be sized for the account without distorting the market thesis.**

Risk outputs hard authority such as:

```text
PASS
BLOCK
UNKNOWN
```

Unknown financial/exposure truth fails closed for new entries.

## Account-size risk profiles — frozen V1 policy

V1 uses three Gold account profiles:

```text
SMALL   any positive equity below $300
MEDIUM  $300–$999.99
NORMAL  $1,000+
```

There is **no arbitrary minimum account-balance/equity floor** such as `$100` for V1 trading eligibility.

A positive-equity account does not become blocked merely because it falls to `$99`, `$50`, `$30` or another amount below `$100`. It remains `SMALL` while positive and below `$300`.

What decides whether a new trade is actually affordable is the existing risk system:

```text
structural SL geometry
+ broker minimum/step volume
+ all-in monetary risk
+ profile hard ceiling
+ verified margin/free margin
+ daily risk state
+ exposure/capacity
+ execution safety
```

Account size by itself is not an extra trade filter.

For risk-day consistency, the profile is resolved from positive `DayStartEquity` and remains fixed for that UTC risk day instead of switching because of intraday floating P/L.

## Frozen initial profile bands

| Profile | Normal / Target Risk Band | Elevated but Acceptable Gold Risk | New-Entry Hard Ceiling | Daily Loss Lock |
|---|---:|---:|---:|---:|
| SMALL | 3.0%–4.5% | >4.5%–6.5% | 7% | 12% |
| MEDIUM | 2.0%–3.0% | >3.0%–4.5% | 5% | 9% |
| NORMAL | 1.0%–2.0% | >2.0%–3.5% | 4% | 7% |

These values are initial DEMO/research implementation policy, not a profitability claim. Research may later propose a governed change, but production may not silently alter them.

Elevated risk is tolerance for Gold lot granularity/structural geometry; it is not preferred target sizing.

### SMALL

Designed for accounts where broker minimum volume, commonly `0.01`, is a coarse risk unit.

- applies to **all positive equity below `$300`**;
- practical base/minimum lot is normally `0.01` where broker rules require it;
- normal/target effective risk is `3.0%–4.5%`;
- elevated but acceptable effective risk is `>4.5%–6.5%`;
- no new entry may exceed the `7%` New-Entry Hard Ceiling;
- a theoretical raw size below `0.01` does **not** automatically reject the trade;
- calculate actual all-in risk of broker minimum volume using approved structural SL and current execution costs;
- if current geometry is too expensive, the current plan may be blocked while the underlying opportunity remains ARMED for a naturally better entry;
- never tighten structural SL merely to make minimum volume affordable;
- never block merely because equity is below `$100`.

### MEDIUM

- `$300–$999.99` day-start equity;
- stepped dynamic lots according to broker step;
- normal/target effective risk is `2.0%–3.0%`;
- elevated but acceptable effective risk is `>3.0%–4.5%`;
- no new entry may exceed the `5%` New-Entry Hard Ceiling;
- actual all-in risk is recalculated after lot normalization.

### NORMAL

- `$1,000+` day-start equity;
- fully dynamic percentage-based sizing;
- normal/target effective risk is `1.0%–2.0%`;
- elevated but acceptable effective risk is `>2.0%–3.5%`;
- no new entry may exceed the `4%` New-Entry Hard Ceiling;
- broker-step normalization and fresh all-in monetary-risk revalidation apply before execution.

## Risk concepts

### Target Risk Band

```text
SMALL   3.0%–4.5%
MEDIUM  2.0%–3.0%
NORMAL  1.0%–2.0%
```

### Acceptable Gold Risk Band

```text
SMALL   >4.5%–6.5%
MEDIUM  >3.0%–4.5%
NORMAL  >2.0%–3.5%
```

### New-Entry Hard Ceiling

```text
SMALL   7%
MEDIUM  5%
NORMAL  4%
```

A plan above its profile ceiling is not permitted at that entry/SL geometry. This is a risk-geometry decision, not a minimum-balance rule.

## Broker-aware all-in monetary risk

Risk must use broker facts rather than a naive `lot × pip` assumption. Relevant facts include tick size/value, contract size, account currency, executable entry side, structural SL distance, min/max/step volume, equity/free margin, spread, expected slippage reserve and commission/fees where applicable.

The question is:

> **For the proposed executable volume, what is the realistic account-currency downside if the approved structural SL is hit, including execution friction exactly once?**

### Spread treatment

A quoted Gold spread is a price-distance observation, not automatically the same number in account-currency cost. Convert it through verified broker symbol/tick facts.

Execution friction must never be double-counted. If fresh Ask/Bid entry already embeds spread in entry-to-SL monetary loss, spread may be shown diagnostically but is not added again.

## Hybrid dynamic lot sizing

```text
Resolve account profile
→ build structural Trade Plan
→ target profile Normal Risk Band
→ calculate raw volume
→ normalize to broker volume step/minimum
→ calculate realistic all-in risk
→ classify CONSERVATIVE / NORMAL / ELEVATED / EXCESSIVE
→ verify hard ceiling, margin, exposure and daily-risk state
→ PASS / BLOCK / UNKNOWN
```

For SMALL accounts, practical evaluation may begin with broker minimum `0.01` and evaluate its real risk directly rather than pretending a non-executable fractional lot is available.

## Minimum-lot handling

The rule is **not**:

```text
raw lot < 0.01 → automatic BLOCK
account < $100 → automatic BLOCK
```

Instead:

```text
positive equity below $300 → SMALL profile
raw lot < broker minimum    → evaluate broker minimum lot
actual all-in risk within allowed policy + all other checks pass → PASS
actual all-in risk above hard ceiling                            → BLOCK current plan
```

`MIN_LOT_UNAFFORDABLE` is reserved for cases where broker minimum volume itself creates all-in risk beyond the new-entry hard ceiling or another hard financial constraint.

If blocked only because current geometry makes minimum volume too expensive, the opportunity may remain ARMED and wait for a naturally better structural entry. Risk does not force a tighter stop.

## Drawdown-aware behaviour

V1 does not add arbitrary 50%/75% daily-budget trade restrictions. Existing profile bands, hard entry ceiling, daily lock, cooldown, capacity and execution safety remain authoritative.

Research may later propose a governed drawdown-aware preference inside already allowed risk bands, but it may not silently create a new balance floor or unrelated hard gate.

## Dynamic does not mean score-leveraged risk

A higher Opportunity/Final Trade Score does not automatically multiply monetary risk. Strategy quality decides whether an opportunity is worth pursuing; Risk independently decides affordable size.

## Original versus current open risk

Keep separate:

- Original Approved Risk / immutable original R basis;
- Current Open Risk to active broker stop;
- Locked Profit where stop has moved beyond entry.

Stop movement never redefines historical original R.

## Position capacity — V1 frozen policy

V1 allows one independently risk-bearing Gold position at a time.

```text
Capacity 0/1 → new independent Gold entry may be considered
Capacity 1/1 → new independent Gold entries blocked
```

This is not a daily trade quota. Analysis, setup tracking, opposite-thesis analysis, missed-opportunity logging and research continue while capacity is full.

Unexpected manual/foreign/unknown Gold exposure blocks new bot Gold entries until reconciled clear; external exposure is never treated as bot-owned.

## Margin guard

Actual broker margin authority is broker-specific.

The Risk Engine may expose a generic margin estimate as a **diagnostic only**. It must not falsely block a valid Gold plan merely because a generic `price × contract / leverage` approximation is high.

When exact broker-required margin is available it is authoritative. The implemented execution path performs fresh broker pre-submit validation/margin authority through the MT5 execution boundary; controlled real-DEMO broker evidence is still required before this behaviour is called VERIFIED.

## Daily P/L and daily loss-lock accounting — frozen V1 policy

The daily risk day begins at `00:00 UTC`.

### Account Safety P/L

Daily loss-lock authority protects the actual account:

```text
AccountSafetyPL
= CurrentVerifiedEquity
- DayStartEquity
- NetNonTradingCashFlowSinceDayStart
```

Identifiable deposits, withdrawals, broker credits/debits and other non-trading balance adjustments are excluded from trading P/L classification.

Broker equity already contains realized/floating trading P/L and applicable trading charges, so these must not be added again to the equity delta.

Floating losses therefore count toward the daily safety lock before realization.

If required equity/cash-flow truth is unknown or inconsistent, new entries fail closed until reconciled.

### Bot Performance P/L

Bot-managed XAU performance is journaled separately for strategy analytics. Manual/foreign activity must not contaminate bot strategy-performance attribution even though it can affect real account safety equity.

### Daily lock trigger

```text
SMALL   12%
MEDIUM   9%
NORMAL   7%
```

Initial cycle reference is `DayStartEquity`:

```text
CycleLossPct
= max(0, -CycleSafetyPL / CycleReferenceEquity × 100)
```

When the profile Daily Loss Lock is reached:

- state becomes `LOSS_LOCKED`;
- no new entries/re-entry/add-ons are permitted;
- an already-open bot trade continues under Trade Manager/execution safety rather than being force-closed solely because the daily lock triggered;
- cumulative day P/L/history remains visible and immutable.

For example, a `$30` SMALL day-start equity has the same SMALL percentages: 7% new-entry ceiling and 12% daily lock. The small dollar amounts are a consequence of percentage risk, not a separate minimum-balance restriction.

## Governed manual loss reset — frozen V1 policy

Manual daily-loss reset is retained but disabled by default.

If explicitly enabled:

- only `LOSS_LOCKED` may be reset;
- maximum one reset per UTC risk day;
- operator action requires deliberate double-confirm `R,R`;
- reset creates a new cycle reference from current verified equity/safety state;
- cumulative `AccountSafetyPL` and broker/day history remain visible and are never rewritten;
- the same profile Daily Loss Lock percentage applies to the new cycle;
- reset state/count must survive restart;
- reset cannot clear unrelated data/news/account/execution/reconciliation blockers.

## Cooldown — frozen V1 policy

Cooldown protects against churn; it is not punishment after every loss.

- one ordinary losing trade does not create a global cooldown;
- one genuinely fresh same-episode re-entry is permitted;
- if that re-entry also loses, that Market Episode is locked;
- three consecutive closed bot-trade losses trigger a minimum 30-minute global cooldown;
- release also requires no unresolved execution fault, fresh completed M15 context after trigger, and a fresh valid opportunity/episode;
- a winning closed trade resets the consecutive-loss counter, but does not retroactively bypass an already active minimum cooldown;
- abnormal execution/feed shocks may create condition-based cooldown until the responsible condition normalizes.

## Loss streak and trade frequency

There is no required minimum or normal maximum number of trades per day. Opportunity frequency comes from valid market episodes.

V1 does not add a normal fixed trade-count quota. Duplicate-intent, episode/re-entry, capacity, one-shot write and reconciliation safeguards handle runaway-loop protection.

## Risk output contract

Every evaluation should expose as applicable:

- Account Profile;
- sizing mode;
- Risk Decision/reason;
- Target Risk Band;
- risk classification;
- New-Entry Hard Ceiling;
- Actual Proposed All-in Risk;
- structural SL monetary risk;
- spread/execution-friction diagnostics;
- proposed normalized volume;
- margin diagnostic/verified broker-margin result;
- `DayStartEquity`;
- cumulative `AccountSafetyPL`;
- active `CycleSafetyPL` / cycle loss percentage;
- Daily Loss Lock and remaining cycle budget;
- separate Bot Performance P/L;
- manual reset state/count;
- loss streak;
- cooldown state/release conditions;
- position capacity.

## Prohibited risk behaviour

- martingale;
- averaging down to rescue a losing thesis;
- arbitrary minimum-balance/equity trading floor for a positive SMALL account;
- silent risk-limit expansion by strategy/research/AI;
- multiplying risk merely because strategy score is high or recent trades won;
- moving structural SL merely to fit risk budget;
- treating elevated band as preferred sizing;
- assuming unknown exposure/P&L is zero;
- double-counting execution friction or equity-contained fees/P&L;
- treating deposits/withdrawals as trading P/L;
- hiding external-account drawdown from Account Safety P/L;
- mixing manual/foreign P/L into bot strategy-performance attribution;
- opening a second independent Gold risk position/automatic hedge in V1;
- unlimited same-episode re-entry;
- resetting consecutive losses without a qualifying outcome;
- redefining original R after stop movement;
- using manual reset to bypass non-loss hard blocks;
- using a broker-inaccurate generic margin estimate as a hard blocker.

## Current implementation checkpoint

Implemented owners include:

```text
src/goldswingtraderai/risk/engine.py
src/goldswingtraderai/risk/state.py
src/goldswingtraderai/decisions/trade_plan.py
src/goldswingtraderai/persistence/runtime_state.py
src/goldswingtraderai/execution/checks.py
src/goldswingtraderai/execution/gate.py
src/goldswingtraderai/execution/service.py
```

Deterministic behaviour includes:

- positive equity `<$300` resolves to SMALL with no `$100` floor;
- day-start-equity profile stability;
- min-lot evaluation instead of raw-lot rejection;
- all-in risk and profile hard ceilings;
- cash-flow-adjusted Account Safety P/L;
- daily lock/manual-reset state;
- loss streak/cooldown/episode re-entry;
- capacity/external-exposure checks;
- exact broker margin authority when supplied, heuristic margin diagnostic otherwise;
- durable risk/cooldown/episode state;
- centralized execution consumes risk authority without allowing strategy score to bypass it.

Risk modules themselves still contain no raw broker-write authority; irreversible MT5 writes remain confined to the execution boundary.

## Persistence / replay

Day-start equity, cash-flow adjustments, cycle reference, daily lock/reset/cooldown/loss-streak/episode-reentry state and relevant risk references are durable through the SQLite persistence layer. Restart/laptop migration must not silently reset them.

Phase-10 research/replay can evaluate risk attribution separately from opportunity quality so a safety/risk block is not incorrectly blamed on the strategy. Counterfactual outcomes remain separate from actual broker P/L.

## Dashboard visibility

```text
🛡 RISK
Profile          SMALL
Equity           $30.00   (example; no minimum floor)
Sizing           BASE 0.01
Target Band      3.0–4.5%
All-in Risk      ...
Entry Ceiling    7%
Risk Band        ...
Day Safety P/L   ...
Cycle P/L        ...
Daily Lock       12%
Daily Remaining  ...
Manual Reset     OFF / 0/1 / USED
Loss Streak      ...
Cooldown         ...
Position         0/1
Decision         PASS / BLOCK / UNKNOWN
```

## Tests required / current evidence

Deterministic coverage includes:

- positive equity below `$100` remains SMALL rather than becoming blocked by profile classification;
- profile/risk-band/ceiling/daily-lock boundaries;
- broker-aware all-in risk and execution-friction accounting exactly once;
- raw lot below broker minimum does not auto-block;
- minimum lot above hard ceiling blocks current plan without tightening SL;
- exact broker margin can block while generic heuristic alone cannot;
- one managed Gold position blocks second independent entry;
- external Gold exposure blocks new bot entry without ownership confusion;
- UTC risk-day rollover and restart persistence;
- `AccountSafetyPL = equity delta - net non-trading cash flow`;
- floating loss affects Account Safety P/L immediately;
- deposits/withdrawals/credits do not masquerade as trading P/L;
- Bot Performance P/L remains separate from account-safety P/L;
- manual reset default OFF and max one per UTC risk day;
- reset preserves cumulative day P/L;
- one ordinary loss does not trigger global cooldown;
- one fresh same-episode re-entry maximum;
- second same-episode loss locks that episode;
- three consecutive losses trigger minimum 30-minute cooldown;
- cooldown release requires fresh M15 context, not timer only;
- risk state survives restart;
- centralized execution gate cannot override a Risk BLOCK/UNKNOWN.

Live broker margin/slippage/commission behaviour still requires controlled DEMO evidence.

## Open questions

- emergency/aggregate risk ceilings for future multi-position design;
- exact slippage-reserve model and commission treatment by broker/account type;
- exact identification/classification of unusual broker balance/credit adjustments;
- exact keyboard confirmation timing for `R,R`;
- any future evidence-backed drawdown-aware preference inside frozen bands.
