from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from goldswingtraderai.app.main import _resolve_session_news_provider
from goldswingtraderai.app.session_news import FileSessionNewsProvider
from goldswingtraderai.config import RuntimeMode, RuntimeStateMode, Settings
from goldswingtraderai.domain.enums import HardDecision


NOW = datetime(2026, 9, 18, 18, 30, tzinfo=timezone.utc)


def _facts() -> tuple[SimpleNamespace, SimpleNamespace]:
    account = SimpleNamespace(login=123456, server="Broker-Demo")
    market = SimpleNamespace(meta=SimpleNamespace(symbol="XAUUSD"))
    recovery = SimpleNamespace(
        snapshot=SimpleNamespace(
            account=account,
            symbol="XAUUSD",
        )
    )
    return market, recovery


def _payload(*, fetched_at_utc: datetime | None = NOW) -> dict[str, object]:
    return {
        "schema_version": 1,
        "provider": "test-calendar",
        "provider_health": "VERIFIED",
        "fetched_at_utc": None if fetched_at_utc is None else fetched_at_utc.isoformat(),
        "scope": {
            "account_login": 123456,
            "server": "Broker-Demo",
            "symbol": "XAUUSD",
        },
        "session": {
            "tradeable": True,
            "schedule_verified": True,
            "next_close_utc": (NOW + timedelta(hours=2)).isoformat(),
            "next_close_kind": "DAILY",
            "execution_normalized": True,
            "unresolved_gap_or_reconciliation": False,
            "weekend_gap_assessed": True,
            "holiday_context": False,
        },
        "events": [],
    }


def _write(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_file_provider_returns_authoritative_clear_observation(tmp_path: Path) -> None:
    path = tmp_path / "session-news.json"
    _write(path, _payload())
    market, recovery = _facts()

    result = FileSessionNewsProvider(path)(market, recovery, NOW)

    assert result.permission.decision is HardDecision.PASS
    assert result.permission.market.reason == "SESSION_OPEN"
    assert result.permission.news.reason == "NEWS_CLEAR"
    assert result.news is not None
    assert result.news.required_event_truth_available is True


def test_stale_verified_snapshot_is_not_treated_as_news_clear(tmp_path: Path) -> None:
    path = tmp_path / "session-news.json"
    _write(path, _payload(fetched_at_utc=NOW - timedelta(minutes=31)))
    market, recovery = _facts()

    result = FileSessionNewsProvider(path)(market, recovery, NOW)

    assert result.permission.decision is HardDecision.UNKNOWN
    assert result.permission.news.reason == "NEWS_SAFETY_UNKNOWN"
    assert result.news is not None
    assert result.news.health.value == "STALE"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("symbol", "XAUUSDm"),
        ("server", "Other-Demo"),
        ("account_login", 987654),
    ],
)
def test_scope_mismatch_is_rejected(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    path = tmp_path / "session-news.json"
    payload = _payload()
    scope = payload["scope"]
    assert isinstance(scope, dict)
    scope[field] = value
    _write(path, payload)
    market, recovery = _facts()

    with pytest.raises(ValueError, match="scope"):
        FileSessionNewsProvider(path)(market, recovery, NOW)


def test_future_fetch_time_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "session-news.json"
    _write(path, _payload(fetched_at_utc=NOW + timedelta(seconds=1)))
    market, recovery = _facts()

    with pytest.raises(ValueError, match="future"):
        FileSessionNewsProvider(path)(market, recovery, NOW)


def test_launcher_resolves_configured_file_provider(tmp_path: Path) -> None:
    settings = Settings(
        environment="test",
        preferred_symbol="XAUUSD",
        symbol_aliases=("XAUUSD",),
        manual_reset_enabled=False,
        state_dir=tmp_path,
        log_level="INFO",
        runtime_mode=RuntimeMode.PRIMARY,
        state_mode=RuntimeStateMode.INITIALIZE,
        mt5_magic=26091801,
        mt5_deviation_points=20,
        session_news_file=tmp_path / "session-news.json",
        session_news_ttl_seconds=900,
    )

    provider = _resolve_session_news_provider(settings, None)

    assert isinstance(provider, FileSessionNewsProvider)
    assert provider.path == settings.session_news_file
    assert provider.freshness_ttl == timedelta(minutes=15)
