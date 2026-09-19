from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import inspect

from goldswingtraderai.operator import DashboardData, OpenTradeView, render_dashboard
import goldswingtraderai.operator.dashboard as dashboard_module


NOW = datetime(2026, 9, 18, 12, 34, 56, tzinfo=timezone.utc)


def _data() -> DashboardData:
    return DashboardData(
        project="GoldSwingTraderAI",
        symbol="XAUUSDm",
        account_mode="DEMO",
        demo_guard="PASS",
        runtime_role="PRIMARY",
        account_profile="SMALL",
        utc_time=NOW,
        m5_seconds_remaining=184,
        market_state="OPEN",
        bid=3600.100,
        ask=3600.300,
        spread_price=0.200,
        spread_state="NORMAL",
        structure_summary="H4 BULL | H1 BULL | M15 BULL | M5 TRANSITION",
        ema_fast=3598.2,
        ema_slow=3591.4,
        rsi=61.3,
        atr=4.125,
        decision_action="WAIT",
        decision_reason="ENTRY_EXTENDED",
        buy_score=84.0,
        sell_score=28.0,
        opportunity_score=82.0,
        entry_score=58.0,
        evidence_coverage=92.0,
        strategy_family="TREND_PULLBACK_CONTINUATION",
        risk_state="NORMAL",
        proposed_risk_pct=3.75,
        proposed_volume=0.01,
        day_safety_pl=-1.25,
        daily_loss_limit_pct=12.0,
        daily_remaining_pct=10.75,
        position_count=0,
        position_capacity=1,
        loss_streak=0,
        cooldown="CLEAR",
        execution_permission="ALLOW",
        execution_reason="EXECUTION_READY",
        controller_role="PRIMARY",
        lease_epoch=12,
        broker_reconcile="COMPLETE",
        learning_state="ACTIVE",
        backup_state="VERIFIED",
        system_health="HEALTHY",
    )


def test_dashboard_preserves_required_scalper_visibility_and_reason() -> None:
    rendered = render_dashboard(_data(), width=180)

    for expected in (
        "XAUUSDm",
        "DEMO",
        "Bid 3600.100",
        "Ask 3600.300",
        "Spread 0.200",
        "M5 03:04",
        "EMA20 3598.200",
        "EMA50 3591.400",
        "RSI 61.3",
        "ATR 4.125",
        "WAIT",
        "ENTRY_EXTENDED",
        "Risk 3.75%",
        "Lot 0.01",
        "Day P/L -$1.25",
        "Position 0/1",
        "Loss Streak 0",
        "EXECUTION",
        "Epoch 12",
    ):
        assert expected in rendered
    assert "Entry extended hai" in rendered


def test_wait_blocked_and_open_trade_are_visually_distinct() -> None:
    waiting = render_dashboard(_data(), width=180)
    blocked = render_dashboard(
        replace(
            _data(),
            decision_action="BLOCKED",
            decision_reason="SPREAD_TOO_HIGH",
            execution_permission="BLOCK",
            execution_reason="SPREAD_TOO_HIGH",
        ),
        width=180,
    )
    open_trade = OpenTradeView(
        direction="BUY",
        entry=3590.0,
        current=3610.0,
        original_stop=3580.0,
        current_stop=3598.0,
        broker_tp=3625.0,
        primary_target=3605.0,
        expansion_target=3625.0,
        runner_target=3640.0,
        current_r=2.0,
        manager_action="RUNNER",
        manager_reason="RUNNER_EARNED_BY_CONTINUATION",
    )
    managing = render_dashboard(
        replace(_data(), managed_trade=open_trade, position_count=1, decision_action="OPEN_TRADE"),
        width=180,
    )

    assert "🟡 WAIT" in waiting
    assert "🔴 BLOCKED" in blocked
    assert "SPREAD_TOO_HIGH" in blocked
    assert "📈 OPEN TRADE" in managing
    assert "Runner 3640.000" in managing
    assert "RUNNER_EARNED_BY_CONTINUATION" in managing


def test_plain_text_fallback_keeps_meaning() -> None:
    rendered = render_dashboard(_data(), emoji=False, width=180)
    assert "[MARKET]" in rendered
    assert "[DECISION]" in rendered
    assert "[WAIT] WAIT" in rendered
    assert "[EXEC]" in rendered


def test_dashboard_shows_research_liveness_without_granting_authority() -> None:
    rendered = render_dashboard(
        replace(
            _data(),
            learning_state="ACTIVE",
            discovery_state="HEALTHY",
            candidate="CAND_123",
            candidate_stage="PROPOSED",
            suppression_reason="—",
        ),
        width=180,
    )
    assert "Learning ACTIVE" in rendered
    assert "Discovery HEALTHY" in rendered
    assert "CAND_123" in rendered
    assert "PROPOSED" in rendered


def test_dashboard_is_read_only_presentation_module() -> None:
    source = inspect.getsource(dashboard_module)
    assert "order_send(" not in source
    assert "MetaTrader5" not in source
    assert "evaluate_risk(" not in source
    assert "evaluate_execution_permission(" not in source
