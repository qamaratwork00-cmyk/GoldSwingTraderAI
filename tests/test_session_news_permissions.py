from __future__ import annotations

from datetime import datetime, timedelta, timezone

from goldswingtraderai.domain.enums import HardDecision, MarketState, NewsSafetyState
from goldswingtraderai.intelligence.news import (
    EventTier,
    EventWindow,
    NewsFacts,
    ProviderHealth,
)
from goldswingtraderai.risk import (
    BrokerSessionFacts,
    ClosureKind,
    NewsRecoveryFacts,
    combine_session_news_permission,
    evaluate_market_permission,
    evaluate_news_permission,
)


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)


def _session(
    *,
    close_in_minutes: int = 120,
    kind: ClosureKind = ClosureKind.DAILY,
    **changes,
) -> BrokerSessionFacts:
    values = {
        "tradeable": True,
        "schedule_verified": True,
        "next_close_utc": NOW + timedelta(minutes=close_in_minutes),
        "next_close_kind": kind,
    }
    values.update(changes)
    return BrokerSessionFacts(**values)


def _news(*windows: EventWindow, available: bool = True) -> NewsFacts:
    return NewsFacts(
        provider="TEST",
        health=ProviderHealth.VERIFIED if available else ProviderHealth.UNAVAILABLE,
        fetched_at_utc=NOW,
        mapping_version="test",
        events=(),
        windows=tuple(windows),
        required_event_truth_available=available,
    )


def test_daily_preclose_blocks_new_entry_at_t20_and_requires_flatten_at_t10() -> None:
    no_entry = evaluate_market_permission(_session(close_in_minutes=20), NOW)
    flatten = evaluate_market_permission(_session(close_in_minutes=10), NOW)

    assert no_entry.state is MarketState.PRE_CLOSE
    assert no_entry.decision is HardDecision.BLOCK
    assert no_entry.reason == "SESSION_PRE_CLOSE"
    assert not no_entry.flatten_required
    assert flatten.reason == "PRE_CLOSE_FLATTEN"
    assert flatten.flatten_required


def test_weekend_preclose_uses_sixty_and_thirty_minute_thresholds() -> None:
    no_entry = evaluate_market_permission(
        _session(close_in_minutes=60, kind=ClosureKind.WEEKEND), NOW
    )
    flatten = evaluate_market_permission(
        _session(close_in_minutes=30, kind=ClosureKind.WEEKEND), NOW
    )

    assert no_entry.reason == "SESSION_PRE_CLOSE"
    assert not no_entry.flatten_required
    assert flatten.reason == "PRE_CLOSE_FLATTEN"
    assert flatten.flatten_required


def test_daily_reopen_needs_one_clean_m5_and_weekend_needs_two_plus_gap_assessment() -> None:
    daily_wait = evaluate_market_permission(
        _session(
            reopened_at_utc=NOW - timedelta(minutes=4),
            reopen_kind=ClosureKind.DAILY,
            clean_completed_m5_since_reopen=0,
        ),
        NOW,
    )
    daily_ready = evaluate_market_permission(
        _session(
            reopened_at_utc=NOW - timedelta(minutes=6),
            reopen_kind=ClosureKind.DAILY,
            clean_completed_m5_since_reopen=1,
        ),
        NOW,
    )
    weekend_wait = evaluate_market_permission(
        _session(
            reopened_at_utc=NOW - timedelta(minutes=12),
            reopen_kind=ClosureKind.WEEKEND,
            clean_completed_m5_since_reopen=2,
            weekend_gap_assessed=False,
        ),
        NOW,
    )
    weekend_ready = evaluate_market_permission(
        _session(
            reopened_at_utc=NOW - timedelta(minutes=12),
            reopen_kind=ClosureKind.WEEKEND,
            clean_completed_m5_since_reopen=2,
            weekend_gap_assessed=True,
        ),
        NOW,
    )

    assert daily_wait.state is MarketState.REOPEN_WARMUP
    assert daily_wait.clean_m5_required == 1
    assert daily_ready.decision is HardDecision.PASS
    assert weekend_wait.state is MarketState.REOPEN_WARMUP
    assert weekend_ready.decision is HardDecision.PASS


def test_holiday_context_is_caution_not_fake_market_closure() -> None:
    result = evaluate_market_permission(_session(holiday_context=True), NOW)

    assert result.decision is HardDecision.PASS
    assert result.state is MarketState.HOLIDAY_CAUTION
    assert result.new_entries_allowed


def test_missing_verified_session_schedule_is_unknown_not_invented_clear() -> None:
    result = evaluate_market_permission(
        BrokerSessionFacts(
            tradeable=True,
            schedule_verified=False,
            next_close_utc=None,
            next_close_kind=None,
        ),
        NOW,
    )

    assert result.decision is HardDecision.UNKNOWN
    assert result.reason == "SESSION_SCHEDULE_UNKNOWN"


def test_tier_one_and_tier_two_windows_block_while_tier_three_has_no_hard_window() -> None:
    tier_one = EventWindow(
        tier=EventTier.TIER_1,
        start_utc=NOW - timedelta(minutes=15),
        end_utc=NOW + timedelta(minutes=15),
        event_ids=("CPI",),
    )
    tier_two = EventWindow(
        tier=EventTier.TIER_2,
        start_utc=NOW - timedelta(minutes=5),
        end_utc=NOW + timedelta(minutes=5),
        event_ids=("RETAIL",),
    )

    one = evaluate_news_permission(_news(tier_one), NOW)
    two = evaluate_news_permission(_news(tier_two), NOW)
    clear = evaluate_news_permission(_news(), NOW)

    assert one.state is NewsSafetyState.NEWS_BLACKOUT
    assert one.active_event_ids == ("CPI",)
    assert two.decision is HardDecision.BLOCK
    assert clear.decision is HardDecision.PASS


def test_missing_required_news_truth_is_unknown_not_silent_clear() -> None:
    result = evaluate_news_permission(_news(available=False), NOW)

    assert result.decision is HardDecision.UNKNOWN
    assert result.state is NewsSafetyState.NEWS_SAFETY_UNKNOWN


def test_severe_post_news_dislocation_needs_normalized_conditions_and_one_clean_m5() -> None:
    not_ready = evaluate_news_permission(
        _news(),
        NOW,
        NewsRecoveryFacts(
            active=True,
            severe_dislocation=True,
            execution_normalized=True,
            clean_completed_m5_after_event=0,
        ),
    )
    ready = evaluate_news_permission(
        _news(),
        NOW,
        NewsRecoveryFacts(
            active=True,
            severe_dislocation=True,
            execution_normalized=True,
            clean_completed_m5_after_event=1,
        ),
    )

    assert not_ready.state is NewsSafetyState.POST_NEWS_WARMUP
    assert not_ready.decision is HardDecision.BLOCK
    assert ready.state is NewsSafetyState.NEWS_CLEAR
    assert ready.decision is HardDecision.PASS


def test_combined_permission_preserves_preclose_flatten_authority() -> None:
    market = evaluate_market_permission(_session(close_in_minutes=8), NOW)
    news = evaluate_news_permission(_news(), NOW)
    combined = combine_session_news_permission(market, news)

    assert combined.decision is HardDecision.BLOCK
    assert combined.flatten_required
    assert "PRE_CLOSE_FLATTEN" in combined.reasons
