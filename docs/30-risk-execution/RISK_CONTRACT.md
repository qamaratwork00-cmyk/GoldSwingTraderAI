# GoldSwingTraderAI — Risk Contract

**Status:** PROVISIONAL  
**Version:** 0.7-design  
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

## Frozen initial profile bands

The initial implementation/research policy uses:

| Profile | Normal / Target Risk Band | Elevated but Acceptable Gold Risk | New-Entry Hard Ceiling | Daily Loss Lock |
|---|---:|---:|---:|---:|
| SMALL | 3.0%–4.5% | >4.5%–6.5% | 7% | 12% |
| MEDIUM | 2.0%–3.0% | >3.0%–4.5% | 5% | 9% |
| NORMAL | 1.0%–2.0% | >2.0%–3.5% | 4% | 7% |

These values are **initial DEMO/research implementation policy**, not a profitability claim. Research may later propose a governed change, but production may not silently alter them.

A value inside the elevated band is not automatically preferred. It means the trade may remain executable when Gold lot granularity/structural geometry makes exact target sizing impossible and all other hard checks pass.

### SMALL

Designed for accounts where broker minimum volume (commonly `0.01`) is a coarse risk unit.

Default sizing behaviour:

- practical base/minimum lot is normally `0.01` where broker rules require it;
- normal/target effective risk is `3.0%–4.5%`;
- elevated but acceptable effective risk is `>4.5%–6.5%`;
- no new entry may exceed the `7%` New-Entry Hard Ceiling;
- a theoretical raw size below `0.01` does **not** automatically reject the trade;
- calculate the real all-in risk of `0.01` using the approved structural SL and current execution costs;
- if current entry geometry is too expensive but the thesis remains valid, the opportunity may remain ARMED while Entry/Trade Plan waits for a naturally better structural entry;
- never tighten the structural SL merely to make `0.01` affordable.

### MEDIUM

Designed for accounts where several broker lot steps are practically available.

Default sizing behaviour:

- stepped dynamic lots such as `0.01`, `0.02`, `0.03` according to broker step;
- normal/target effective risk is `2.0%–3.0%`;
- elevated but acceptable effective risk is `>3.0%–4.5%`;
- no new entry may exceed the `5%` New-Entry Hard Ceiling;
- actual all-in risk is recalculated after lot normalization.

### NORMAL

Designed for accounts where broker lot granularity is less restrictive.

Default sizing behaviour:

- fully dynamic percentage-based sizing;
- normal/target effective risk is `1.0%–2.0%`;
- elevated but acceptable effective risk is `>2.0%–3.5%`;
- no new entry may exceed the `4%` New-Entry Hard Ceiling;
- broker-step normalization and fresh all-in monetary-risk revalidation apply before execution.

## Risk concepts

### Target Risk Band

Preferred effective all-in risk after broker normalization and friction accounting:

```text
SMALL   3.0%–4.5%
MEDIUM  2.0%–3.0%
NORMAL  1.0%–2.0%
```

### Acceptable Gold Risk Band

Bounded elevated tolerance when Gold volume granularity/valid structural geometry prevents preferred sizing:

```text
SMALL   >4.5%–6.5%
MEDIUM  >3.0%–4.5%
NORMAL  >2.0%–3.5%
```

Elevated risk is tolerance, not target sizing.

### New-Entry Hard Ceiling

```text
SMALL   7%
MEDIUM  5%
NORMAL  4%
```

A plan above its profile ceiling is not permitted at that entry/SL geometry.

### Emergency Safety Ceiling

A catastrophic invariant/circuit limit, **not** permission to size normal trades at that level. Exact emergency/aggregate ceilings remain open.

## Broker-aware all-in monetary risk

Risk must use broker facts rather than a naive `lot × pip` assumption. Relevant facts include tick size/value, contract size, account currency, executable entry side, structural SL distance, min/max/step volume, equity/free margin, spread, expected slippage reserve and commission/fees where applicable.

The question is:

> **For the proposed executable volume, what is the realistic account-currency downside if the approved structural SL is hit, including execution friction exactly once?**

### Spread treatment

A quoted Gold spread such as `$0.26` is a price-distance observation, not automatically a `$0.26` account cost. The bot converts spread through verified broker symbol/contract/tick facts.

Execution friction must never be double-counted. If fresh Ask/Bid entry already embeds spread in entry-to-SL monetary loss, spread may be itemized diagnostically but is not added again.

## Hybrid dynamic lot sizing

```text
Resolve account profile
→ build structural Trade Plan
→ target profile Normal Risk Band
→ calculate raw volume
→ normalize to broker volume step/minimum
→ calculate realistic all-in risk
→ classify NORMAL / ELEVATED / EXCESSIVE
→ verify hard ceiling, margin, exposure and daily-risk state
→ PASS or BLOCK
```

For SMALL accounts, the practical path may begin with broker minimum `0.01` and evaluate its real risk directly rather than pretending a non-executable fractional lot is available.

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
→ NORMAL band: PASS if all other checks pass
→ ELEVATED band: PASS may be allowed if all other checks pass
→ above hard ceiling: BLOCK current plan
```

`MIN_LOT_UNAFFORDABLE` is reserved for cases where broker minimum volume itself creates all-in risk beyond the configured new-entry hard ceiling or another hard financial constraint.

If blocked only because current entry geometry makes `0.01` too expensive, the opportunity may remain ARMED and wait for a naturally better structural entry. Risk does not force a tighter stop.

## Drawdown-aware preference

Dynamic sizing should not become more aggressive as the account approaches its daily loss lock. Within a valid profile policy, the sizing engine should prefer the lower/safer side of its normal band when verified daily drawdown is already material. Exact drawdown-to-risk reduction curve remains an implementation/calibration question.

## Dynamic does not mean score-leveraged risk

A higher Opportunity/Final Trade Score does not automatically multiply monetary risk. Strategy quality decides whether an opportunity is worth pursuing; Risk independently decides affordable size.

## Original versus current open risk

Keep separate:

- Original Approved Risk / immutable original R basis;
- Current Open Risk to active broker stop;
- Locked Profit where stop has moved beyond entry.

Stop movement never redefines historical original R.

## Aggregate exposure

Track worst-case remaining open risk across all managed exposure. Unknown exposure is not treated as zero.

## Position capacity — V1 frozen policy

V1 allows **one independently risk-bearing Gold position at a time** for the managed account/symbol.

```text
Capacity 0/1 → new independent Gold entry may be considered
Capacity 1/1 → new independent Gold entries blocked
```

This is not a daily trade quota. Analysis, setup tracking, opposite-thesis analysis, missed-opportunity logging and research continue while capacity is full.

An opposite opportunity is first handed to Trade Manager as reversal/exit evidence. It cannot automatically create a hedge or second independent Gold position.

## Margin guard

Even when monetary SL risk passes, required margin/free margin/margin-level policy must pass. Execution rechecks fresh broker facts before sending but does not redefine risk policy.

## Daily loss lock

GoldSwingTraderAI retains a hard daily-loss lock on the UTC calendar risk day (`00:00 UTC` boundary).

```text
SMALL   12%
MEDIUM   9%
NORMAL   7%
```

When the applicable daily limit is reached:

- risk state becomes `LOSS_LOCKED`;
- no new entries/re-entry/add-ons are permitted;
- open-trade management remains active where safely possible;
- broker P/L/history is not erased;
- dashboard shows verified daily P/L, profile daily limit and remaining/reset state.

The exact realized/floating P/L accounting formula remains an implementation-freeze item; broker truth is authoritative where available.

## Governed manual loss reset — V1 frozen policy

Manual daily-loss reset is retained but is **disabled by default**.

If explicitly enabled by operator configuration:

- only `LOSS_LOCKED` may be reset; unrelated `BLOCKED`, reconciliation, account, data, news or execution faults remain blocked;
- maximum **one manual loss reset per UTC risk day**;
- operator action is deliberate double-confirm `R,R` (exact key timing may be an implementation detail, but accidental single-key reset is prohibited);
- reset uses the verified current broker/account risk reference under the final daily-P/L accounting formula;
- original cumulative broker/day P/L remains visible and is never rewritten or erased;
- reset creates a new audited risk cycle from the verified current reference rather than pretending earlier loss did not occur;
- reset count, timestamp, equity/reference, operator action and policy version persist across restart;
- after the one permitted reset is consumed, another `LOSS_LOCKED` state remains locked until the next UTC risk day.

Dashboard example:

```text
Manual Reset     OFF / AVAILABLE / USED
Reset Count      0/1
```

Reason codes may include `LOSS_LOCKED`, `MANUAL_RESET_AVAILABLE`, `MANUAL_RESET_USED` and `MANUAL_RESET_LIMIT_REACHED`.

## Cooldown — V1 frozen policy

Cooldown protects against churn; it is **not punishment after every loss**.

### One ordinary loss

One normally executed losing trade does **not** create a global cooldown by itself.

### Same Market Episode re-entry

A stopped/failed setup may re-enter only after a genuinely fresh structural/timing event while the thesis and target/risk geometry remain valid.

V1 allows at most **one fresh re-entry within the same Market Episode**. If that re-entry also closes as a loss, that Market Episode is locked from further entries. A new market episode is required.

Reason code: `EPISODE_REENTRY_LIMIT`.

### Consecutive-loss cooldown

After **3 consecutive closed bot-trade losses**, enter global `COOLDOWN` for at least **30 minutes**.

Time alone is insufficient for release. Before new entries resume, require:

- cooldown minimum elapsed;
- no unresolved execution/reconciliation fault;
- a fresh completed M15 market update/structure context after cooldown trigger;
- proposed setup belongs to a fresh valid opportunity/episode rather than immediate replay of the failed setup.

A winning closed trade resets the consecutive-loss counter. Breakeven/scratch handling is recorded separately and does not count as a loss unless final implementation accounting classifies it negative after costs.

### Execution/shock cooldown

Abnormal slippage, spread explosion, feed dislocation or execution shock may create a condition-based cooldown independent of loss count. Release requires the responsible execution/market conditions to normalize; a fixed timer must not force release while conditions remain unsafe.

## Loss streak and trade frequency

Track consecutive losses and episode/family/day context for dashboard and research.

There is no required minimum or normal maximum trade count per day. Opportunity frequency comes from valid market episodes.

A generous emergency trade-count circuit breaker may exist solely to catch software/re-entry loops; its exact value remains open and must not become a normal quota.

## Re-entry

Re-entry requires a genuinely fresh market event/structure with thesis and target/risk geometry still valid. Repeating an unchanged setup after a loss is not valid re-entry.

## External/manual exposure

Broker positions must distinguish bot-managed versus manual/foreign/unknown ownership. Unexpected external Gold exposure blocks new bot Gold entries until Execution/Reconciliation establishes a safe state; the bot never manages external exposure as if bot-owned.

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
- margin result;
- daily P/L / Daily Loss Lock / remaining budget;
- manual reset state/count;
- loss streak;
- cooldown state/release conditions;
- position capacity.

## Prohibited risk behaviour

- martingale;
- averaging down to rescue a losing thesis;
- silent risk-limit expansion by strategy/research/AI;
- multiplying risk merely because strategy score is high or recent trades won;
- moving structural SL merely to fit risk budget;
- treating elevated band/emergency ceiling as preferred sizing;
- assuming unknown exposure/P&L is zero;
- double-counting execution friction;
- opening a second independent Gold risk position/automatic hedge in V1;
- unlimited same-episode re-entry;
- resetting consecutive losses without a qualifying outcome;
- redefining original R after stop movement;
- using manual reset to bypass non-loss hard blocks.

## Persistence / replay

Daily lock/reset/cooldown/loss-streak/episode-reentry state and relevant risk references are durable. Restart/laptop migration must not silently reset them. Replay/research must reconstruct chronology without future leakage.

## Dashboard visibility

```text
🛡 RISK
Profile          SMALL
Sizing           BASE 0.01
Target Band      3.0–4.5%
All-in Risk      5.2%
Entry Ceiling    7%
Risk Band        ELEVATED
Daily P/L        ...
Daily Lock       12%
Manual Reset     OFF / 0/1 / USED
Loss Streak      0
Cooldown         CLEAR
Position         0/1
Decision         PASS / BLOCK
```

## Tests required

- profile/risk-band/ceiling/daily-lock boundaries;
- broker-aware all-in risk and execution-friction accounting exactly once;
- raw lot below broker minimum does not auto-block;
- one managed Gold position blocks second independent entry;
- opposite opportunity routes to Trade Manager;
- external Gold exposure blocks new bot entry without ownership confusion;
- UTC risk-day rollover and restart persistence;
- manual reset default OFF;
- only one enabled reset per UTC risk day;
- `R,R` double-confirm semantics;
- reset preserves cumulative broker/day P/L and audit trail;
- reset cannot bypass unrelated hard block;
- one ordinary loss does not trigger global cooldown;
- one fresh same-episode re-entry maximum;
- second same-episode loss locks that episode;
- 3 consecutive losses trigger minimum 30-minute cooldown;
- cooldown release requires fresh M15 context, not timer only;
- win resets consecutive-loss counter;
- execution/shock cooldown remains blocked while conditions unsafe.

## Open questions

- emergency/aggregate risk ceilings for future multi-position design;
- policy for account balances below `$100`;
- exact slippage-reserve model and commission treatment by broker/account type;
- exact realized/floating daily-loss accounting formula;
- exact keyboard confirmation timing for `R,R`;
- exact drawdown-aware target-band reduction curve;
- emergency trade-count circuit-breaker value.
