from datetime import datetime, timedelta, timezone

from goldswingtraderai.risk import (
    ClosedTradeOutcome,
    CooldownDecision,
    CooldownState,
    cooldown_decision,
    record_closed_trade,
)


def test_win_resets_loss_streak_but_does_not_erase_triggered_cooldown() -> None:
    now = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
    triggered = CooldownState(
        consecutive_losses=3,
        triggered_at_utc=now,
        cooldown_until_utc=now + timedelta(minutes=30),
    )

    after_win = record_closed_trade(
        triggered,
        ClosedTradeOutcome.WIN,
        now + timedelta(minutes=5),
    )

    assert after_win.consecutive_losses == 0
    assert after_win.triggered_at_utc == triggered.triggered_at_utc
    assert after_win.cooldown_until_utc == triggered.cooldown_until_utc
    assert cooldown_decision(
        after_win,
        now + timedelta(minutes=10),
        latest_completed_m15_utc=now + timedelta(minutes=15),
        unresolved_execution_fault=False,
        fresh_opportunity=True,
    ) is CooldownDecision.COOLDOWN
