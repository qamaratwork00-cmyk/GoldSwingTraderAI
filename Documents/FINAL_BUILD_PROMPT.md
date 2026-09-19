# GoldSwingTraderAI — Final Build Prompt

**Status:** CANDIDATE FOR ADOPTION
**Version:** 0.1-handoff
**Authority:** Compact implementation handoff; detailed documents remain authoritative

## Mission

Implement GoldSwingTraderAI as the documented XAUUSD/XAUUSDm system. Build the
system that exists in the Documents manual; do not recreate a scalper, invent
undocumented filters or bypass the authority chain.

## Mandatory reading

Read Documents/README.md, DOCUMENTATION_STANDARD.md,
00-foundation/SYSTEM_CONTRACT.md, the relevant topic contract,
DESIGN_DECISIONS.md, OPEN_QUESTIONS.md, CODING_STANDARD.md,
MODULE_STRUCTURE.md and CODER_GUIDE.md before editing.

## Non-negotiable architecture

- H4 context, H1 direction, M15 opportunity and M5 timing.
- M1 is execution-health and diagnostic context only; it never independently
  creates a Swing trade.
- Completed-candle chronology and no lookahead.
- One normalized snapshot shared by independent desks.
- Six parallel strategy families.
- Independent BUY and SELL theses with visible conflict.
- Opportunity and Entry Timing are separate.
- Structural Trade Plan before monetary sizing.
- Immutable original R.
- Risk/session/news/account/controller are hard authorities outside score.
- Positive DEMO Guard is required for broker writes.
- One central gate, one Intent identity, one raw writer.
- Ambiguous acknowledgement reconciles; it is never blindly retried.
- One active execution controller with fencing.
- Restart/restore preserves critical state and reconciles broker truth.
- Research and AI cannot self-modify hard safety or self-promote.

## Implementation loop

~~~text
read authority
→ trace source owner
→ state inputs/outputs/failure/persistence
→ implement smallest clear typed change
→ add boundary tests
→ update complete documentation graph
→ run quality and documentation checks
→ report software proof versus external proof
~~~

## Phase order

Phase 1–9 build the deterministic production foundation.
Phase 10 builds offline research and governed improvement.
Phase 11 builds portable recovery, backup and migration proof.
Phase 12 integrates the persistent runtime and collects final DEMO evidence.

Do not collapse these phases into one “complete” claim.

## Accuracy without filter soup

One coherent family may lead. Missing optional Trendline/Fibonacci/POC evidence
does not subtract base strategy score. A poor M5 moment normally becomes WAIT.
High score never increases monetary risk and never overrides a hard BLOCK.

## Proof discipline

Separate:

- deterministic software tests;
- chronological research evidence;
- connected MT5 read evidence;
- real DEMO broker lifecycle evidence;
- fresh-machine/failover evidence;
- final exact-build audit.

Never report a higher proof class than the evidence actually collected.

The new-manual structural gate is
python scripts/verify_documents_manual.py .
The legacy docs gate remains separate and must not be treated as the new
manual's authority.
