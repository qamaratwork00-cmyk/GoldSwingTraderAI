# GoldSwingTraderAI — Architecture

**Status:** PROVISIONAL  
**Version:** 0.4-design  
**Authority:** High-level system architecture

## High-level flow

```text
VERIFIED MARKET / BROKER FACTS
            │
            ▼
PARALLEL MARKET-INTELLIGENCE DESKS
Candle/Structure | Technical/Location | Liquidity/SMC
Indicator/Quant  | Fundamental Facts | Session Context
            │
            ▼
PARALLEL STRATEGY FAMILIES
            │
            ▼
BUY THESIS  ↔  SELL THESIS
            │
            ▼
DEBATE / RED TEAM
            │
            ▼
DECISION FUSION
Opportunity + Timing + Conflict + Coverage + Reasons
            │
            ▼
STRUCTURAL TRADE PLAN
Entry Reference + Invalidation/SL + Targets + Original R
            │
            ▼
HARD AUTHORITIES
Risk + Session/News + Data/Account + Position/Order + Controller
            │
            ▼
CENTRAL EXECUTION PERMISSION GATE
DEMO Guard + ALLOW / BLOCK / UNKNOWN + Reasons
            │
            ▼
PERSIST EXECUTION INTENT
            │
            ▼
ONE GOVERNED BROKER WRITE + RECONCILIATION
            │
            ▼
OPEN-TRADE MANAGEMENT FLOOR
            │
            ▼
JOURNAL / LEARNING / RESEARCH / DISCOVERY
```

Cross-cutting services:

```text
PERSISTENCE / RESTART / BACKUP / MIGRATION
CONTROLLER LEASE / FENCING
SYSTEM HEALTH / DIAGNOSTICS
DASHBOARD / OPERATOR VISIBILITY
```

They support/observe the authoritative flow without creating a second trading authority.

## Architectural principles

### 1. Parallel analysis

The system does not force all evidence through one long sequential filter chain where a weak optional signal can prematurely kill a valid opportunity. Specialist desks consume the same validated snapshot and publish independent bounded evidence.

### 2. One behavioural owner per rule

- Data layer owns broker/market facts.
- Candle Structure owns candle sequences/swings/BOS/MSS geometry.
- Technical owns generic zones/location/target room.
- Liquidity owns pools/sweeps/FVG/qualified OB/premium-discount interpretation.
- Quant owns indicators/volatility/momentum/extension metrics.
- Fundamental/Session intelligence publishes facts/context, not broker-write authority.
- Strategy families own family-specific opportunity hypotheses.
- Decision Fusion owns thesis combination/conflict/decision attribution.
- Entry Timing owns executable timing/setup lifecycle.
- Trade Plan owns initial structural entry/SL/targets/original R.
- Risk owns affordability/exposure/daily-loss policy.
- Session/Risk State owns hard market/news/risk permission composition.
- Execution owns the positive DEMO guard, centralized final broker-write permission, controller ownership checks and irreversible MT5 path.
- Trade Manager owns post-entry management intent.
- Persistence owns durable state/recovery/backup mechanics.
- Research/Learning owns governed evidence/candidate creation, never direct broker authority.
- System Health aggregates faults/impact/recovery without redefining subsystem rules.

### 3. Separate opportunity from entry timing

A market opportunity may be strong while current execution timing is poor. Persistent setup lifecycle and separate Opportunity/Entry Timing scores preserve valid ideas without chasing.

### 4. Separate market opinion from hard safety

Analytical uncertainty may lower confidence. Safety uncertainty can block action. Missing optional macro/indicator evidence is different from unknown financial risk, required event safety, broker identity, order outcome, controller ownership or corrupted state.

### 5. Structural plan before monetary sizing

Strategy/timing define a coherent structural plan first. Risk sizes or rejects that plan; risk must not distort market invalidation simply to fit a lot size.

### 6. One final broker-write permission boundary

All bot-managed create/modify/close operations pass a single centralized permission boundary consuming authoritative subsystem results.

V1 environment permission is one positive input:

```text
verified connected MT5 DEMO account
→ DEMO_GUARD PASS
```

If DEMO status is not verified, broker-write permission is not granted. V1 does not define a separate REAL authorization/hard-block path.

### 7. State survives process and machine boundaries

Restart/laptop migration must not erase risk locks, order ambiguity, open-trade context, strategy genealogy, learning or promotion history. Broker truth is freshly reconciled before execution resumes.

### 8. One cross-machine execution owner

Only one PRIMARY may have broker-write authority for the managed account/symbol.

V1 controller ownership uses a shared lease with monotonic fencing epoch. Initial renewal target is 10 seconds and lease TTL is 30 seconds. Every irreversible write freshly verifies the current non-expired ownership epoch.

Standby takeover after expiry enters recovery/reconciliation first; lease ownership alone is not execution readiness.

## Timeframe hierarchy

```text
H4  → macro regime / major external structure / major liquidity
H1  → directional structure / thesis context
M15 → opportunity / location / target / structural context
M5  → entry timing / fine structure / retest / reclaim
M1  → diagnostics/execution telemetry unless explicitly promoted later
```

Higher timeframes provide context and meaningful contradiction rather than universal vetoes.

## Setup lifecycle

High-level lifecycle remains conceptually:

```text
DISCOVERED
   ↓
ARMED
   ↓
READY
   ↓
TRIGGERED
```

with branches such as:

```text
ARMED → WAITING → READY
ARMED → MISSED → RE-ARMED
ARMED → STALE
ARMED → INVALIDATED
```

Exact vocabulary belongs to `../20-trading-decisions/ENTRY_TIMING.md`.

## Decision outputs

The decision/timing system distinguishes at least:

- ENTER BUY;
- ENTER SELL;
- WAIT;
- MISSED;
- INVALID;
- BLOCKED.

`WAIT` means the thesis may remain valid. `INVALID` means the opportunity itself failed. `BLOCKED` means an independent safety/risk/system authority prevents execution.

## Decision attribution

Every cycle should preserve where the path stopped, for example:

```text
Data        PASS
Strategy    BUY 87
Entry       PASS
Trade Plan  PASS
News        PASS
Risk        BLOCK: MIN_LOT_UNAFFORDABLE
Execution   NOT_REACHED
```

This is decision attribution, not the same as a System Health fault.

## Execution architecture

```text
Approved Plan
→ Risk/Session/News/Data/Account/Position/Order/Controller results
→ DEMO Guard + Execution Permission Gate
→ persist Execution Intent
→ fresh broker pre-check
→ one irreversible request
→ ACCEPTED_VERIFIED | ACCEPTED_UNKNOWN | FAILED
→ reconciliation as required
```

Ambiguous broker acknowledgement is reconciliation-only; blind duplicate retry is prohibited.

A verified DEMO account is real-time broker execution on that DEMO account, not DRY RUN.

## Open-trade architecture

An open managed trade is continuously evaluated by parallel evidence. The Trade Manager consumes at least:

- Continuation Score;
- Reversal Score;
- Structure Integrity;
- Candle Health;
- Momentum/Expansion Health;
- Target Remaining / Liquidity Path;
- Protection Need;
- Session/Pre-Close requirement.

It returns HOLD, PROTECT, TRAIL, RUNNER or EXIT. Broker modification/close still passes through the governed execution boundary.

Known scheduled XAU closure is a hard V1 session boundary: PRE_CLOSE blocks new entries and mandatory flatten overrides HOLD/RUNNER before closure.

## Persistence / recovery architecture

Durable state includes risk/order/trade lifecycle, original R, Opportunity/Episode lineage, Strategy Registry, learning/research/promotion state and diagnostic/backup metadata where applicable.

Startup conceptually:

```text
validate local state
→ connect/verify MT5 + DEMO status
→ reconcile broker positions/orders/deals
→ restore risk/trades
→ rebuild market intelligence
→ revalidate opportunities
→ load learning/strategy registry
→ acquire current controller lease/epoch
→ reconcile execution state
→ READY
```

## Research / learning architecture

```text
Runtime evidence / trades / missed+blocked opportunities
                         │
                         ▼
                   RESEARCH LAB
            ┌────────────┼────────────┐
            ▼            ▼            ▼
       Entry/Exit     Discovery     Invention
        Learning         │        declarative only
            └────────────┼────────────┘
                         ▼
               Independent validation
                         ▼
                 Locked Challenger
                         ▼
               Final untouched holdout
                         ▼
                       Stress
                         ▼
                       Shadow
                         ▼
                    DEMO Canary
                         ▼
               governed promotion
```

Research cannot bypass risk/execution, silently mutate production or generate arbitrary executable strategy code.

## Health / operator architecture

System Health reports `OK/WARN/DEGRADED/BLOCKED/ERROR`, subsystem, trading impact and recovery state. Dashboard presents compact Market/Decision/Setup/Trade/Risk/Execution/Learning/Backup/Health panels with restrained emojis and stable reason codes.
