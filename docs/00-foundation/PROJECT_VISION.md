# GoldSwingTraderAI — Project Vision

**Status:** PROVISIONAL  
**Version:** 0.1-design  
**Authority:** Product intent and project direction

## Purpose

GoldSwingTraderAI is a fresh XAUUSD/XAUUSDm trading system designed to capture meaningful intraday and swing expansion rather than repeatedly scalp small fluctuations. The goal is to identify, enter and manage high-quality directional moves with enough flexibility to take a healthy number of valid trades without becoming a filter-heavy, ultra-restricted bot.

The system should be capable of participating in moves that may reach 100, 200, 300+ normalized pips when market structure supports them. These pip labels are reporting concepts, not fixed take-profit requirements. Trading logic must reason in broker-native price/point units and original R.

## Design philosophy

1. **Institutional-floor thinking.** Multiple specialist desks analyse the same verified market snapshot in parallel.
2. **Price and candle structure first.** Candle sequences, swings, BOS/MSS, displacement, compression/expansion, rejection and liquidity behaviour are primary market language.
3. **Indicators support; they do not rule.** EMA, RSI, ATR and related indicators provide bounded evidence rather than single-point authority.
4. **Flexible opportunity detection.** A weak supporting desk should not automatically destroy a valid trade thesis.
5. **Strong opposing evidence matters.** BUY and SELL theses compete independently and disagreement is explicitly measured.
6. **Opportunity and timing are separate.** A strong setup may remain armed while the bot waits for a better M5 entry.
7. **Safety is not a score.** Risk, news, broker identity, market-data integrity and execution safety retain hard authority.
8. **Large-move management.** Open positions are managed by structural continuation/reversal evidence rather than small-profit reflexes.
9. **Governed improvement.** Strategy discovery and autonomous invention are research processes, never direct self-modification of live trading authority.
10. **Documentation before implementation.** Core behaviour is documented and audited before production trading code is written.

## Timeframe intent

- **H4:** macro regime, major structure, major liquidity and long-range context.
- **H1:** directional structure and higher-timeframe thesis.
- **M15:** opportunity, location, target and structural trade context.
- **M5:** entry timing and fine structural confirmation.
- **M1:** diagnostics/execution telemetry only unless a future validated design explicitly promotes it.

## Desired behaviour

GoldSwingTraderAI should prefer good opportunities over perfect-looking opportunities. It should avoid filter soup, avoid chasing, preserve valid setups while timing improves, permit structurally justified re-entry, and manage winners in a way that leaves room for larger directional expansion.

The system must remain explainable: the operator should be able to see which desks support BUY, which support SELL, why the final decision was made, what invalidates the thesis, and what the trade manager is doing after entry.

## Non-goals

- No guarantee of profit, accuracy, win rate or future return.
- No requirement to take a fixed number of trades per day.
- No fixed 100/200/300-pip TP logic.
- No unrestricted self-writing or self-executing strategy code.
- No strategy or AI component may bypass hard risk/execution controls.
