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
    ):
        monkeypatch.delenv(name, raising=False)


def test_defaults_are_small_and_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    settings = Settings.from_env(env_file=None)

    assert settings.preferred_symbol == "XAUUSDm"
    assert settings.symbol_aliases == ("XAUUSDm", "XAUUSD")
    assert settings.manual_reset_enabled is False


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
