from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3

import pytest

from goldswingtraderai.decisions.opportunity import Opportunity
from goldswingtraderai.decisions.trade_plan import (
    PlanState,
    PlanTarget,
    RRClass,
    StopQuality,
    TargetRole,
    TradePlan,
)
from goldswingtraderai.domain.enums import Direction, OpportunityStage, StrategyFamily
from goldswingtraderai.domain.ids import (
    new_episode_id,
    new_opportunity_id,
    new_trade_plan_id,
)
from goldswingtraderai.persistence import (
    RuntimeStateRepository,
    StateIntegrityError,
    StateStore,
)
from goldswingtraderai.risk import CooldownState, EpisodeRiskState, new_risk_day


NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)


def _opportunity() -> Opportunity:
    return Opportunity(
        opportunity_id=new_opportunity_id(),
        episode_id=new_episode_id(),
        direction=Direction.BUY,
        stage=OpportunityStage.READY,
        created_at_utc=NOW - timedelta(minutes=10),
        updated_at_utc=NOW,
        opportunity_score=81.0,
        thesis_score=84.0,
        source_families=(StrategyFamily.TREND_PULLBACK_CONTINUATION,),
    )


def _plan(opportunity: Opportunity) -> TradePlan:
    primary = PlanTarget(
        role=TargetRole.PRIMARY,
        price=2350.0,
        quality=82.0,
        source="H1:SWING",
        rr=1.7,
    )
    expansion = PlanTarget(
        role=TargetRole.EXPANSION,
        price=2360.0,
        quality=88.0,
        source="H4:LIQUIDITY",
        rr=2.7,
    )
    return TradePlan(
        plan_id=new_trade_plan_id(),
        opportunity_id=opportunity.opportunity_id,
        episode_id=opportunity.episode_id,
        family=StrategyFamily.TREND_PULLBACK_CONTINUATION,
        direction=Direction.BUY,
        state=PlanState.READY,
        signal_price=2333.0,
        approved_entry_reference=2334.0,
        invalidation_level=2327.0,
        invalidation_source="M15:PROTECTED_LOW",
        initial_stop=2326.0,
        stop_buffer=1.0,
        stop_quality=StopQuality.ROBUST,
        original_r_price=8.0,
        immediate_obstacle=None,
        primary_target=primary,
        expansion_target=expansion,
        runner_target=None,
        broker_tp_target=expansion,
        rr_class=RRClass.GOOD,
        path_quality=78.0,
        plan_quality=86.0,
        created_at_utc=NOW,
        reason="PLAN_READY",
    )


def test_state_store_roundtrip_and_event_journal(tmp_path) -> None:
    store = StateStore(tmp_path / "state.db")
    saved = store.save_record(
        "example",
        "one",
        {"value": 7, "status": "OK"},
        event_type="EXAMPLE_SAVED",
    )
    loaded = store.load_record("example", "one", expected_schema_version=1)

    assert loaded is not None
    assert loaded.payload == {"status": "OK", "value": 7}
    assert loaded.checksum == saved.checksum
    assert store.event_count("example") == 1
    store.integrity_check()


def test_checksum_corruption_fails_closed(tmp_path) -> None:
    path = tmp_path / "state.db"
    store = StateStore(path)
    store.save_record("risk_day", "scope", {"equity": 100.0})

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE state_records SET payload_json=? WHERE namespace=? AND record_key=?",
            ('{"equity":1.0}', "risk_day", "scope"),
        )

    with pytest.raises(StateIntegrityError):
        store.load_record("risk_day", "scope")
    with pytest.raises(StateIntegrityError):
        store.integrity_check()


def test_runtime_state_survives_restart_with_lineage_intact(tmp_path) -> None:
    path = tmp_path / "runtime.db"
    first = RuntimeStateRepository(StateStore(path), "123456:XAUUSDm")
    opportunity = _opportunity()
    plan = _plan(opportunity)
    risk_day = new_risk_day(NOW, 80.0, manual_reset_enabled=True)
    cooldown = CooldownState(
        consecutive_losses=3,
        triggered_at_utc=NOW - timedelta(minutes=5),
        cooldown_until_utc=NOW + timedelta(minutes=25),
    )
    episode = EpisodeRiskState(
        episode_id=opportunity.episode_id,
        entries_taken=1,
        losses=1,
    )

    first.save_risk_day(risk_day)
    first.save_cooldown(cooldown)
    first.save_episode_risk(episode)
    first.save_active_opportunity(opportunity)
    first.save_trade_plan(plan)

    # New repository object simulates process restart; no in-memory state is reused.
    restored = RuntimeStateRepository(StateStore(path), "123456:XAUUSDm")
    bundle = restored.load_recovery_bundle()

    assert bundle.risk_day == risk_day
    assert bundle.cooldown == cooldown
    assert bundle.active_opportunity == opportunity
    assert bundle.trade_plan == plan
    assert bundle.episode_risk == episode


def test_recovery_rejects_trade_plan_opportunity_identity_mismatch(tmp_path) -> None:
    repository = RuntimeStateRepository(StateStore(tmp_path / "runtime.db"), "scope")
    opportunity = _opportunity()
    other = _opportunity()
    mismatched_plan = _plan(other)

    repository.save_active_opportunity(opportunity)
    repository.save_trade_plan(mismatched_plan)

    with pytest.raises(StateIntegrityError, match="identity mismatch"):
        repository.load_recovery_bundle()


def test_clear_active_records_does_not_delete_risk_history(tmp_path) -> None:
    repository = RuntimeStateRepository(StateStore(tmp_path / "runtime.db"), "scope")
    opportunity = _opportunity()
    repository.save_risk_day(new_risk_day(NOW, 30.0))
    repository.save_active_opportunity(opportunity)
    repository.save_trade_plan(_plan(opportunity))

    repository.clear_trade_plan()
    repository.clear_active_opportunity()
    bundle = repository.load_recovery_bundle()

    assert bundle.risk_day is not None
    assert bundle.active_opportunity is None
    assert bundle.trade_plan is None
