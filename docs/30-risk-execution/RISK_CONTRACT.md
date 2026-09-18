# GoldSwingTraderAI — Risk Contract

**Status:** PROVISIONAL  
**Version:** 0.3-design  
**Authority:** Monetary risk, account-size risk profiles, dynamic/hybrid lot sizing, aggregate exposure, daily-loss/manual-reset semantics and risk-policy invariants.  
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

## Account-size risk profiles

V1 uses three default Gold account profiles:

```text
SMALL   $100–$299
MEDIUM  $300–$999
NORMAL  $1,000+
```

These are the accepted initial implementation boundaries. They remain configuration values so later verified research/DEMO evidence may justify a governed change.

Balances below $100 are not assigned a default V1 trading profile by this decision; final handling remains an open implementation/policy question.

### SMALL

Designed for accounts where broker minimum volume (commonly `0.01`) is a coarse risk unit.

Default sizing behaviour:

- practical base/minimum lot is normally `0.01` where broker rules require it;
- a theoretical raw size below `0.01` does **not** automatically reject the trade;
- calculate the real all-in risk of `0.01` using the approved structural SL and current execution costs;
- allow the trade only when that all-in risk remains inside the configured SMALL profile permission band/ceiling;
- if current entry geometry is too expensive but the thesis remains valid, the opportunity may remain ARMED while Entry/Trade Plan waits for a naturally better structural entry;
- never tighten the structural SL merely to make `0.01` affordable.

### MEDIUM

Designed for accounts where several broker lot steps are practically available.

Default sizing behaviour:

- stepped dynamic lots such as `0.01`, `0.02`, `0.03` according to broker step;
- percentage Target Risk is increasingly meaningful;
- actual all-in risk is recalculated after lot normalization;
- controlled deviation around Target Risk may be allowed inside the configured MEDIUM risk band/ceiling.

### NORMAL

Designed for accounts where broker lot granularity is less restrictive.

Default sizing behaviour:

- fully dynamic percentage-based sizing;
- broker-step normalization;
- fresh all-in monetary-risk revalidation before execution;
- narrower dependence on minimum-lot exceptions because position granularity is normally sufficient.

## Risk concepts

Keep distinct:

### Target Risk

The preferred sizing target. It is a target, not necessarily an exact equality requirement after broker lot normalization.

### Acceptable Gold Risk Band

A configurable bounded range around/above Target Risk used mainly where Gold minimum-lot granularity prevents exact sizing.

This prevents an otherwise valid SMALL-account trade from being rejected merely because the theoretical lot was, for example, `0.007` while the broker minimum is `0.01`.

The band is not permission for unlimited risk.

### New-Entry Hard Ceiling

The maximum allowed actual all-in risk for a new entry. A trade above this ceiling is not permitted at the current entry/SL geometry.

### Emergency Safety Ceiling

A catastrophic invariant/circuit limit, **not** permission to size normal trades at that level.

Exact Target Risk, acceptable-band and ceiling percentages are profile-specific and remain open to validation/freeze.

## Broker-aware all-in monetary risk

Risk must use broker facts rather than a naive `lot × pip` assumption. Relevant facts include:

- tick size/value;
- contract size;
- account currency;
- executable entry side and structural SL distance;
- min/max/step volume;
- current equity/free margin;
- spread;
- expected slippage reserve where policy requires it;
- commission/fees where applicable.

The question is:

> **For the proposed executable volume, what is the realistic account-currency downside if the approved structural SL is hit, including execution friction exactly once?**

### Spread treatment

A quoted Gold spread such as `$0.26` is a price-distance observation, not automatically a `$0.26` account cost. The bot converts spread through verified broker symbol/contract/tick facts.

Execution friction must never be double-counted. If the fresh Ask/Bid executable entry already embeds spread in entry-to-SL monetary loss, spread may be itemized for diagnostics but must not be added again as a second loss. Slippage reserve and commission are added only according to their actual accounting semantics.

## Hybrid dynamic lot sizing

Conceptual flow:

```text
Resolve account profile
→ build structural Trade Plan
→ calculate preferred Target Risk
→ calculate raw volume
→ normalize to broker volume step/minimum
→ calculate realistic all-in risk for normalized volume
→ compare with profile Target / Acceptable Band / Hard Ceiling
→ verify margin/exposure/daily-risk state
→ PASS or BLOCK current plan
```

For SMALL accounts, the practical path may begin with broker minimum `0.01` and evaluate its real risk directly rather than pretending a non-executable fractional lot is available.

Volume rounding must not silently increase risk beyond the profile hard ceiling.

## Minimum-lot handling

The rule is **not**:

```text
raw lot < 0.01 → automatic BLOCK
```

Instead:

```text
raw lot < broker minimum
→ evaluate broker minimum lot
→ calculate actual all-in risk
→ if inside permitted profile band/ceiling: PASS
→ if above hard ceiling: BLOCK current plan
```

`MIN_LOT_UNAFFORDABLE` is reserved for cases where broker minimum volume itself creates all-in risk beyond the configured new-entry hard ceiling (or another hard financial constraint).

If the current plan is blocked only because entry geometry makes `0.01` too expensive, the market opportunity may remain valid/ARMED and wait for a genuinely better structural entry. Risk does not force a tighter stop.

## Dynamic does not mean score-leveraged risk

Lot/risk adaptation may depend on account profile, equity, structural SL distance, broker lot granularity, volatility/execution friction, exposure, margin and daily-risk state.

A higher Opportunity/Final Trade Score does not automatically multiply monetary risk. Strategy quality decides whether an opportunity is worth pursuing; Risk independently decides affordable size.

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

- Account Profile (`SMALL`, `MEDIUM`, `NORMAL`);
- sizing mode (`BASE_MIN_LOT`, `STEPPED_DYNAMIC`, `FULL_DYNAMIC` or equivalent);
- Risk Decision and reason code;
- Target Risk;
- Acceptable Gold Risk Band status;
- Actual Proposed All-in Risk;
- structural SL monetary risk;
- spread/execution-friction diagnostics;
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
- multiplying risk merely because a strategy score is high or recent trades won;
- moving structural SL merely to fit risk budget;
- treating emergency ceiling as target sizing permission;
- assuming unknown exposure/P&L is zero;
- double-counting spread/execution friction;
- redefining original R after stop movement;
- bypassing hard lock through manual reset.

## Persistence / replay

Daily lock/reset/cooldown and relevant risk references are durable. Restart/laptop migration must not silently reset them. Replay/research must reconstruct risk-day chronology without future leakage.

Account-profile policy/config version must be journaled so research knows which sizing rules produced each historical decision.

## Dashboard visibility

Compact example:

```text
🛡 RISK
Profile          SMALL
Sizing           BASE 0.01
Target Risk      ...
All-in Risk      ...
Risk Band        NORMAL / ACCEPTABLE / EXCESSIVE
Spread Impact    ...
Lot              0.01
Open Risk        ...
Daily P/L        ...
Decision         PASS / BLOCK
```

If blocked, show the exact reason such as `MIN_LOT_UNAFFORDABLE`, `RISK_GEOMETRY_TOO_LARGE` or `DAILY_LOSS_LIMIT_REACHED`.

## Tests required

- account-profile boundary tests: SMALL `$100–299`, MEDIUM `$300–999`, NORMAL `$1,000+`;
- broker-aware all-in monetary risk calculation;
- spread price-distance to account-currency conversion;
- execution friction included exactly once;
- raw lot below broker minimum does not auto-block;
- minimum-lot PASS inside allowed profile band/ceiling;
- minimum-lot hard-ceiling block without SL manipulation;
- stepped/full dynamic volume normalization/recalculated risk;
- valid opportunity may remain ARMED after current risk geometry blocks entry;
- aggregate exposure/unknown exposure handling;
- margin policy;
- UTC risk-day rollover;
- daily lock persists across restart;
- manual reset preserves broker history/reference audit;
- manual reset cannot bypass unrelated hard block;
- cooldown/re-entry/circuit-breaker semantics once frozen.

## Open questions

- exact Target Risk per SMALL/MEDIUM/NORMAL profile;
- exact Acceptable Gold Risk Band and new-entry hard ceiling per profile;
- emergency/aggregate risk ceilings;
- policy for account balances below `$100`;
- exact slippage-reserve model and commission treatment by broker/account type;
- exact daily-loss percentage/tiering;
- realized/floating daily-loss accounting formula;
- bounded manual-reset count/confirmation window;
- exact cooldown trigger/release rules;
- final one-position-at-a-time confirmation;
- emergency trade-count circuit-breaker value.