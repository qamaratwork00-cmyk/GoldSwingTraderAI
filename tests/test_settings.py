from __future__ import annotations

import pytest

from goldswingtraderai.config.settings import ConfigError, Settings


def _clear(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "GSTAI_ENV",
        "GSTAI_PREFERRED_SYMBOL",
        "GSTAI_SYMBOL_ALIASES",
        "GSTAI_MANUAL_RESET_ENABLED",
        "GSTAI_STATE_DIR",
        "GSTAI_LOG_LEVEL",
        "GSTAI_ALLOWED_ACCOUNT_LOGIN",
        "GSTAI_ALLOWED_SERVER",
        "GSTAI_RUNTIME_MODE",
        "GSTAI_STATE_MODE",
        "GSTAI_MT5_MAGIC",
        "GSTAI_MT5_DEVIATION_POINTS",
        "GSTAI_MT5_COMMENT_PREFIX",
        "GSTAI_RESTORE_CHECKPOINT",
        "GSTAI_HEALTHY_SPREAD_BASELINE",
        "GSTAI_SESSION_NEWS_FILE",
        "GSTAI_SESSION_NEWS_TTL_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_defaults_are_small_and_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    settings = Settings.from_env(env_file=None)

    assert settings.preferred_symbol == "XAUUSDm"
    assert settings.symbol_aliases == ("XAUUSDm", "XAUUSD")
    assert settings.manual_reset_enabled is False
    assert settings.runtime_mode.value == "READINESS"
    assert settings.state_mode.value == "EXISTING"
    assert settings.session_news_file is None
    assert settings.session_news_ttl_seconds == 1800


def test_demo_guard_is_not_a_runtime_toggle(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("GSTAI_REQUIRE_DEMO", "false")

    settings = Settings.from_env(env_file=None)

    assert not hasattr(settings, "require_demo_account")


def test_preferred_symbol_must_be_in_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("GSTAI_PREFERRED_SYMBOL", "XAUUSDm")
    monkeypatch.setenv("GSTAI_SYMBOL_ALIASES", "XAUUSD")

    with pytest.raises(ConfigError, match="preferred symbol"):
        Settings.from_env(env_file=None)


def test_optional_account_identity_is_validated(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("GSTAI_ALLOWED_ACCOUNT_LOGIN", "123456")
    monkeypatch.setenv("GSTAI_ALLOWED_SERVER", "Broker-Demo")

    settings = Settings.from_env(env_file=None)

    assert settings.allowed_account_login == 123456
    assert settings.allowed_server == "Broker-Demo"


def test_session_news_snapshot_configuration_is_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("GSTAI_SESSION_NEWS_FILE", "./state/session-news.json")
    monkeypatch.setenv("GSTAI_SESSION_NEWS_TTL_SECONDS", "900")

    settings = Settings.from_env(env_file=None)

    assert settings.session_news_file is not None
    assert settings.session_news_file.as_posix().endswith("state/session-news.json")
    assert settings.session_news_ttl_seconds == 900


def test_live_mode_requires_explicit_broker_write_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("GSTAI_RUNTIME_MODE", "PRIMARY")

    with pytest.raises(ConfigError, match="GSTAI_MT5_MAGIC"):
        Settings.from_env(env_file=None)


def test_live_mode_accepts_explicit_write_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("GSTAI_RUNTIME_MODE", "STANDBY")
    monkeypatch.setenv("GSTAI_MT5_MAGIC", "26091801")
    monkeypatch.setenv("GSTAI_MT5_DEVIATION_POINTS", "20")
    monkeypatch.setenv("GSTAI_STATE_MODE", "INITIALIZE")

    settings = Settings.from_env(env_file=None)

    assert settings.runtime_mode.value == "STANDBY"
    assert settings.state_mode.value == "INITIALIZE"
    assert settings.mt5_magic == 26091801
    assert settings.mt5_deviation_points == 20


def test_restore_mode_requires_an_explicit_checkpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("GSTAI_STATE_MODE", "RESTORE")

    with pytest.raises(ConfigError, match="GSTAI_RESTORE_CHECKPOINT"):
        Settings.from_env(env_file=None)


def test_invalid_log_level_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("GSTAI_LOG_LEVEL", "VERBOSE")

    with pytest.raises(ConfigError, match="GSTAI_LOG_LEVEL"):
        Settings.from_env(env_file=None)


def test_safe_summary_contains_no_authority_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    summary = Settings.from_env(env_file=None).safe_summary()
    joined_keys = " ".join(summary).lower()

    assert "password" not in joined_keys
    assert "token" not in joined_keys
    assert "secret" not in joined_keys
    assert "api_key" not in joined_keys
