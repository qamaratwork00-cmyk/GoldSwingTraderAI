from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import nan

import pytest

from goldswingtraderai.config.settings import ConfigError, Settings
from goldswingtraderai.execution.checks import ExecutionCheckConfig
from goldswingtraderai.decisions.opportunity import Opportunity, OpportunityConfig, transition_opportunity
from goldswingtraderai.domain.enums import Direction, OpportunityStage, StrategyFamily
from goldswingtraderai.domain.ids import new_episode_id, new_opportunity_id
from goldswingtraderai.intelligence.candle_structure import StructureConfig
from goldswingtraderai.intelligence.confluence import ConfluenceConfig
from goldswingtraderai.intelligence.indicators import QuantConfig
from goldswingtraderai.intelligence.liquidity import LiquidityConfig
from goldswingtraderai.intelligence.technical import TechnicalConfig
from goldswingtraderai.intelligence.news import (
    EventTier,
    NewsFacts,
    ProviderHealth,
    RawScheduledEvent,
    normalize_news_facts,
)
from goldswingtraderai.management.manager import TradeManagerConfig
from goldswingtraderai.research.discovery import DiscoveryConfig
from goldswingtraderai.research.learning import LearningConfig
from goldswingtraderai.research.management_replay import ManagementReplayAssumptions
from goldswingtraderai.risk.state import CooldownState, new_risk_day


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)


def _opportunity(*, updated_at_utc: datetime = NOW) -> Opportunity:
    return Opportunity(
        opportunity_id=new_opportunity_id(),
        episode_id=new_episode_id(),
        direction=Direction.BUY,
        stage=OpportunityStage.ARMED,
        created_at_utc=NOW,
        updated_at_utc=updated_at_utc,
        opportunity_score=70.0,
        thesis_score=72.0,
        source_families=(StrategyFamily.TREND_PULLBACK_CONTINUATION,),
    )


def test_nonfinite_runtime_configuration_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GSTAI_HEALTHY_SPREAD_BASELINE", "nan")

    with pytest.raises(ConfigError, match="HEALTHY_SPREAD_BASELINE"):
        Settings.from_env(env_file=None)


def test_opportunity_scores_and_time_must_remain_valid() -> None:
    with pytest.raises(ValueError, match="scores"):
        Opportunity(
            opportunity_id=new_opportunity_id(),
            episode_id=new_episode_id(),
            direction=Direction.BUY,
            stage=OpportunityStage.ARMED,
            created_at_utc=NOW,
            updated_at_utc=NOW,
            opportunity_score=nan,
            thesis_score=70.0,
            source_families=(StrategyFamily.TREND_PULLBACK_CONTINUATION,),
        )

    opportunity = _opportunity()
    with pytest.raises(ValueError, match="backwards"):
        transition_opportunity(opportunity, OpportunityStage.WAITING, NOW - timedelta(minutes=1))


def test_nonfinite_opportunity_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        OpportunityConfig(discover_score=nan)


def test_nonfinite_component_configuration_is_rejected() -> None:
    factories = (
        lambda: ExecutionCheckConfig(normal_spread_ratio=nan),
        lambda: StructureConfig(swing_reversal_atr=nan),
        lambda: LiquidityConfig(cluster_atr_fraction=nan),
        lambda: TechnicalConfig(zone_atr_fraction=nan),
        lambda: ConfluenceConfig(trendline_near_atr=nan),
        lambda: QuantConfig(quiet_ratio=nan),
        lambda: TradeManagerConfig(protect_min_r=nan),
        lambda: DiscoveryConfig(minimum_mean_strength_r=nan),
        lambda: LearningConfig(r_scale=nan),
        lambda: ManagementReplayAssumptions(barrier_spread_price=nan),
    )
    for factory in factories:
        with pytest.raises(ValueError, match="finite"):
            factory()


def test_future_news_fetch_is_rejected_and_equal_time_events_are_stable() -> None:
    event_time = NOW + timedelta(minutes=30)
    raw = (
        RawScheduledEvent("b", "Retail Sales", "USD", event_time, "high"),
        RawScheduledEvent("a", "Retail Sales", "USD", event_time, "high"),
    )
    with pytest.raises(ValueError, match="future"):
        normalize_news_facts(
            raw,
            provider="fixture",
            provider_health=ProviderHealth.VERIFIED,
            fetched_at_utc=NOW + timedelta(seconds=1),
            as_of_utc=NOW,
        )

    facts = normalize_news_facts(
        raw,
        provider="fixture",
        provider_health=ProviderHealth.VERIFIED,
        fetched_at_utc=NOW,
        as_of_utc=NOW,
    )
    assert facts.events[0].event_id == "a"
    assert facts.events[1].event_id == "b"
    assert facts.events[0].tier is EventTier.TIER_2


def test_risk_state_rejects_nonfinite_values_and_partial_cooldown() -> None:
    with pytest.raises(ValueError, match="finite"):
        new_risk_day(NOW, nan)
    with pytest.raises(ValueError, match="together"):
        CooldownState(triggered_at_utc=NOW)


def test_news_facts_reject_duplicate_event_ids() -> None:
    event = RawScheduledEvent("same", "CPI", "USD", NOW, "critical")
    facts = normalize_news_facts(
        (event,),
        provider="fixture",
        provider_health=ProviderHealth.VERIFIED,
        fetched_at_utc=NOW,
        as_of_utc=NOW,
    )
    with pytest.raises(ValueError, match="unique"):
        NewsFacts(
            provider=facts.provider,
            health=facts.health,
            fetched_at_utc=facts.fetched_at_utc,
            mapping_version=facts.mapping_version,
            events=(facts.events[0], facts.events[0]),
            windows=facts.windows,
            required_event_truth_available=True,
        )
