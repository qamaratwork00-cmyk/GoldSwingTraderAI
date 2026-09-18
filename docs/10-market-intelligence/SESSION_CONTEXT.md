# GoldSwingTraderAI — Session Context

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Asia/London/New York session context as soft market evidence.  
**Depends on:** `MARKET_DATA_AND_HISTORY.md`, `TECHNICAL_STRUCTURE_AND_LEVELS.md`, `FUNDAMENTAL_AND_NEWS.md`

## Purpose

This document defines session context as market evidence. It does **not** own hard OPEN/CLOSED/PRE_CLOSE/LOSS_LOCKED permission; those states belong to `../30-risk-execution/SESSION_AND_RISK_STATE_MACHINE.md`.

## Session model

The market-intelligence layer may classify context such as:

```text
ASIA
LONDON
NEW_YORK
LONDON_NY_OVERLAP
OFF_HOURS / TRANSITION
```

Exact boundaries must use a timezone-safe implementation and account for daylight-saving effects where relevant.

## Session facts

The desk may publish:

- current session/context;
- session start/end references;
- session high/low/range;
- previous session high/low;
- session range relative to recent history;
- participation/volatility context;
- session transition/overlap context.

Session highs/lows may be consumed by Technical and Liquidity desks without redefining their semantics here.

## Soft evidence only

A session is not automatically good or bad for a trade. For example:

- Asia may provide compression/range structure;
- London may create expansion/sweeps;
- New York may continue, reverse or invalidate prior structure.

Historical family performance by session may become bounded learning evidence after validation, but it must not silently become a universal session hard block.

## Holiday interaction

Holiday context may reduce expected participation or change range behaviour, but market closure is determined by broker/live market state.

## Session transitions

Transition periods may increase spread/uncertainty or change liquidity behaviour. These are descriptive facts for scoring/timing. Any actual execution block is owned by hard safety/execution policy.

## Outputs

At minimum:

- current session/context;
- current/previous session high and low;
- session range and normalized range quality;
- session transition/overlap state;
- BUY/SELL contextual support if justified;
- confidence/freshness.

## Replay requirements

Session assignment must be deterministic from historical timestamp/timezone rules. DST/session conversions must not differ between replay and live execution.

## Dashboard visibility

Compact example:

```text
Session       LONDON → NY
Asia Range    COMPLETE
London Range  EXPANDING
Context       ACTIVE
```

## Tests required

- timezone/DST conversion;
- session-high/low chronology;
- overlap classification;
- holiday does not equal closure;
- replay/live session parity.

## Explicit non-goals

This desk must not:

- own broker market-open state;
- own daily-loss reset;
- block every trade in a historically weaker session;
- redefine liquidity sweeps or technical zones.

## Open questions

- exact canonical session boundaries/timezone representation;
- exact overlap labels;
- whether any session transition deserves a validated hard execution restriction later.