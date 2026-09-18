# GoldSwingTraderAI — Risk Contract

**Status:** PROVISIONAL  
**Version:** 0.2-design  
**Authority:** Monetary risk, dynamic lot sizing, aggregate exposure, daily-loss/manual-reset semantics and risk-policy invariants.  
**Depends on:** `../20-trading-decisions/TRADE_PLAN.md`, `../00-foundation/SYSTEM_CONTRACT.md`

## Core principle

Risk is independent authority. A strong strategy score cannot make an unaffordable or unsafe trade acceptable.

> **Market logic chooses the structural plan. Risk decides whether the account can safely afford that plan.**

Risk outputs hard authority such as:

```text
PASS
BLOCK
UNKNOWN
```

Unknown financial/exposure truth fails closed for new entries.

## Risk concepts

Keep distinct:

### Target Risk

The normal configured sizing target used to calculate volume.

### New-Entry Hard Ceiling

A maximum allowed actual risk for a new entry, especially relevant when broker minimum lot prevents exact target sizing.

### Emergency Safety Ceiling

A catastrophic invariant/circuit limit, **not** permission to size normal trades at that level.

Exact percentages remain open to validation/freeze.

## Broker-aware monetary risk

Risk must use broker facts rather than a naive `lot × pip` assumption. Relevant facts may include:

- tick size/value;
- contract size;
- account currency;
- entry/SL distance;
- min/max/step volume;
- current equity/free margin.

The question is: **if the approved structural SL is hit, what is the actual account-currency loss for the proposed volume?**

## Dynamic lot sizing

Conceptual flow:

```text
Allowed Risk = Equity × Target Risk
→ risk per unit volume from Entry to SL
→ raw volume
→ broker-step normalization
→ recalculate actual monetary risk
→ approve only if all ceilings/margin rules pass
```

Volume rounding must not silently increase risk beyond policy.

## Minimum-lot unaffordability

If the broker minimum volume (for example 0.01) produces more monetary risk than allowed, return:

```text
MIN_LOT_UNAFFORDABLE
```

The structural SL must **not** be tightened merely to make the minimum lot affordable.

## Original versus current open risk

Keep separate:

- Original Approved Risk / immutable original R basis;
- Current Open Risk to the active broker stop;
- Locked Profit where the stop has moved beyond entry.

Stop movement never redefines historical original R.

## Aggregate exposure

Track worst-case remaining open risk across all managed exposure. If future versions permit multiple positions/add-ons, aggregate risk remains a separate ceiling from per-trade risk.

Unknown open exposure is not treated as zero.

## Position capacity

One independently risk-bearing Gold position at a time remains the preferred V1 **PROVISIONAL** policy. This is not a trade-frequency quota. Analysis/research continue while capacity is full.

The final V1 position-count policy remains an open question until frozen.

## Margin guard

Even when monetary SL risk passes, required margin/free margin/margin-level policy must pass. Execution rechecks fresh broker facts before sending but does not redefine risk policy.

## Daily loss lock

GoldSwingTraderAI retains a hard daily-loss lock.

The current provisional risk-day direction is:

> **UTC calendar risk day (`00:00 UTC` boundary), independent of XAU reopen/holiday labels.**

This choice is deterministic/replayable and keeps daily risk accounting separate from broker market-open semantics.

The exact daily-loss percentage/tiering remains open.

When the daily limit is reached:

- risk state becomes `LOSS_LOCKED`;
- no new entries/re-entry/add-ons are permitted;
- open-trade management remains active where safely possible;
- broker P/L/history is not erased;
- the dashboard shows verified daily P/L, lock and remaining/reset state.

The exact realized/floating P/L accounting formula must be frozen before implementation; broker truth is authoritative where available.

## Governed manual loss reset

Manual reset is retained as an operator-governed feature. It does **not** erase or rewrite broker P/L.

It should include:

- deliberate multi-step/double-confirm action (for example `R,R` if that control is later frozen);
- bounded reset count per UTC risk day/cycle;
- verified current broker P/L as the new risk reference according to the final accounting formula;
- durable audit record;
- clear dashboard visibility.

Manual reset may affect `LOSS_LOCKED`; it must never bypass unrelated `BLOCKED` states such as account mismatch, unknown order outcome, corrupt state or unknown financial truth.

Exact reset count/confirmation timing remain open.

## Cooldown

Cooldown is intended as churn/runaway protection, not punishment after every loss.

Potential triggers may include:

- rapid repeated losses;
- repeated failures in the same Market Episode;
- abnormal execution/slippage;
- post-shock conditions;
- repeated invalidated re-entries.

A fresh structural/episode event may be required in addition to time before release. Exact rules remain open.

## Loss streak and trade frequency

Track consecutive losses and episode/family/day context for diagnostics/research.

There is no required minimum or normal maximum trade count per day. Opportunity frequency comes from valid market episodes.

A generous emergency trade-count circuit breaker may exist solely to catch software/re-entry loops. Its exact value remains open and must not become a normal trading quota.

## Re-entry

Re-entry requires a genuinely fresh market event/structure with the thesis and target/risk geometry still valid. Repeating the unchanged setup after a loss is not valid re-entry.

Market Episode identity helps distinguish fresh opportunity from stale repetition.

## External/manual exposure

Broker positions must distinguish bot-managed versus manual/foreign/unknown ownership. External exposure may affect aggregate account safety even when the bot does not own/manage that position.

Final V1 policy for unexpected Gold exposure remains open under execution safety.

## Risk output contract

Every risk evaluation should expose, as applicable:

- Risk Decision and reason code;
- Target Risk;
- Actual Proposed Risk;
- proposed normalized volume;
- minimum-lot risk;
- aggregate open risk;
- margin result;
- daily P/L/budget remaining;
- risk state;
- position-capacity state.

## Prohibited risk behaviour

- martingale;
- averaging down to rescue a losing thesis;
- silent risk-limit expansion by strategy/research/AI;
- changing risk because a score is high or recent trades won;
- moving structural SL merely to fit risk budget;
- treating emergency ceiling as target sizing permission;
- assuming unknown exposure/P&L is zero;
- redefining original R after stop movement;
- bypassing hard lock through manual reset.

## Persistence / replay

Daily lock/reset/cooldown and relevant risk references are durable. Restart/laptop migration must not silently reset them. Replay/research must reconstruct risk-day chronology without future leakage.

## Dashboard visibility

Compact example:

```text
🛡 RISK
State           NORMAL
Target Risk     ...
Actual Risk     ...
Lot             ...
Open Risk       ...
Daily P/L       ...
Daily Remaining ...
Position        0/1
Decision        PASS / BLOCK
```

If blocked, show the exact reason such as `MIN_LOT_UNAFFORDABLE` or `DAILY_LOSS_LIMIT_REACHED`.

## Tests required

- broker-aware monetary risk calculation;
- volume-step normalization/recalculated risk;
- minimum-lot block without SL manipulation;
- aggregate exposure/unknown exposure handling;
- margin policy;
- UTC risk-day rollover;
- daily lock persists across restart;
- manual reset preserves broker history/reference audit;
- manual reset cannot bypass unrelated hard block;
- cooldown/re-entry/circuit-breaker semantics once frozen.

## Open questions

- final target risk %;
- new-entry hard ceiling;
- emergency/aggregate risk ceilings;
- exact daily-loss percentage/tiering;
- realized/floating daily-loss accounting formula;
- bounded manual-reset count/confirmation window;
- exact cooldown trigger/release rules;
- final one-position-at-a-time confirmation;
- emergency trade-count circuit-breaker value.