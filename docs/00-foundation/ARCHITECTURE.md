# GoldSwingTraderAI — Architecture

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** High-level system architecture

## High-level flow

```text
VERIFIED MARKET DATA
        │
        ▼
PARALLEL SPECIALIST DESKS
Candle / Structure / Liquidity / Technical / Indicators
Fundamental / Session / Expansion / Strategy / Timing
        │
        ▼
BUY THESIS  ↔  SELL THESIS
        │
        ▼
DEBATE / RED TEAM
        │
        ▼
DECISION FUSION
Opportunity + Timing + Conflict + Coverage
        │
        ▼
HARD SAFETY + RISK AUTHORITY
        │
        ▼
EXECUTION DESK
        │
        ▼
OPEN-TRADE MANAGEMENT FLOOR
        │
        ▼
JOURNAL / RESEARCH / DISCOVERY
```

## Architectural principles

### 1. Parallel analysis

The trading system does not force market evidence through one long chain where an early weak filter can prematurely kill a valid opportunity. Specialist desks consume the same validated market snapshot and produce independent evidence in parallel.

### 2. Clear ownership

- Data layer owns broker/market facts.
- Analytical desks own interpretations, not execution authority.
- Strategy desks own family-specific opportunity hypotheses.
- Decision fusion owns evidence combination.
- Risk owns affordability/exposure/loss limits.
- Execution owns broker submission/reconciliation.
- Trade manager owns post-entry management within hard policy.
- Research owns offline/shadow candidate evaluation, never broker authority.

### 3. Separate opportunity from entry timing

A market opportunity may be strong while current execution timing is poor. The system therefore keeps persistent setup lifecycle and separate Opportunity and Entry Timing scores.

### 4. Separate analysis from safety

Analytical uncertainty may lower confidence. Safety uncertainty blocks action. A missing optional opinion is not the same as unknown broker risk, unknown news safety or corrupted state.

## Timeframe hierarchy

```text
H4  → macro regime / major liquidity / major structure
H1  → directional structure / thesis
M15 → opportunity / location / target / structural context
M5  → entry timing / fine structure / retest / reclaim
M1  → diagnostics and execution telemetry unless explicitly promoted later
```

Higher timeframes should provide context and meaningful contradiction, not become a universal veto machine.

## Setup lifecycle

```text
DISCOVERED
   ↓
ARMED
   ↓
READY
   ↓
TRIGGERED
```

Alternative endings:

```text
ARMED → WAITING → READY
ARMED → MISSED → RE-ARMED
ARMED → STALE
ARMED → INVALIDATED
```

The exact lifecycle vocabulary may be refined, but setup persistence is a core architectural requirement.

## Decision outputs

The final trading authority should distinguish:

- ENTER BUY
- ENTER SELL
- WAIT
- MISSED
- INVALID
- BLOCKED

`WAIT` means the market thesis may still be valid. `INVALID` means the opportunity thesis itself has failed. `BLOCKED` means a hard safety/risk/system authority prevents entry.

## Open-trade architecture

An open trade is continuously evaluated by parallel desks. The trade manager consumes at least:

- Continuation Score
- Reversal Score
- Structure Integrity
- Candle Health
- Momentum/Expansion Health
- Target Remaining / Liquidity Path
- Protection Need

It may return HOLD, PROTECT, TRAIL, RUNNER or EXIT.

## Research architecture

```text
Runtime evidence / trade journal / missed opportunities
                    │
                    ▼
              QUANT RESEARCH LAB
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    Ablation     Discovery    Invention
        └───────────┼───────────┘
                    ▼
             Independent validation
                    ▼
              Final untouched holdout
                    ▼
                  Shadow
                    ▼
                 DEMO
```

The research layer may recommend or promote only through governed stages. It cannot bypass risk or silently mutate production semantics.
