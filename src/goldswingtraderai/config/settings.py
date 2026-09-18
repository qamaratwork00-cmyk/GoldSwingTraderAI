"""Validated runtime settings for GoldSwingTraderAI V1.

Only non-secret configuration belongs here. Authority-bearing credentials must be
supplied through secure/local mechanisms in the later adapter phase and must not
be added to committed configuration templates.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(ValueError):
    """Raised when runtime configuration violates a frozen V1 contract."""


_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}
_VALID_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}


def _parse_bool(name: str, raw: str) -> bool:
    value = raw.strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    raise ConfigError(f"{name} must be a boolean value, got {raw!r}")


def _parse_optional_int(name: str, raw: str | None) -> int | None:
    if raw is None or not raw.strip():
        return None
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer when provided") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be positive when provided")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable, secret-free V1 runtime settings."""

    environment: str
    preferred_symbol: str
    symbol_aliases: tuple[str, ...]
    require_demo_account: bool
    manual_reset_enabled: bool
    state_dir: Path
    log_level: str
    allowed_account_login: int | None = None
    allowed_server: str | None = None

    @classmethod
    def from_env(cls, env_file: str | Path | None = ".env") -> "Settings":
        """Load and validate settings from environment variables.

        Loading `.env` is optional and local-only. Existing process variables win.
        """

        if env_file is not None:
            load_dotenv(dotenv_path=env_file, override=False)

        preferred_symbol = os.getenv("GSTAI_PREFERRED_SYMBOL", "XAUUSDm").strip()
        aliases_raw = os.getenv("GSTAI_SYMBOL_ALIASES", "XAUUSDm,XAUUSD")
        aliases = tuple(dict.fromkeys(part.strip() for part in aliases_raw.split(",") if part.strip()))

        require_demo = _parse_bool(
            "GSTAI_REQUIRE_DEMO", os.getenv("GSTAI_REQUIRE_DEMO", "true")
        )
        manual_reset = _parse_bool(
            "GSTAI_MANUAL_RESET_ENABLED",
            os.getenv("GSTAI_MANUAL_RESET_ENABLED", "false"),
        )
        log_level = os.getenv("GSTAI_LOG_LEVEL", "INFO").strip().upper()
        allowed_server = os.getenv("GSTAI_ALLOWED_SERVER")
        if allowed_server is not None:
            allowed_server = allowed_server.strip() or None

        settings = cls(
            environment=os.getenv("GSTAI_ENV", "development").strip() or "development",
            preferred_symbol=preferred_symbol,
            symbol_aliases=aliases,
            require_demo_account=require_demo,
            manual_reset_enabled=manual_reset,
            state_dir=Path(os.getenv("GSTAI_STATE_DIR", ".state")).expanduser(),
            log_level=log_level,
            allowed_account_login=_parse_optional_int(
                "GSTAI_ALLOWED_ACCOUNT_LOGIN", os.getenv("GSTAI_ALLOWED_ACCOUNT_LOGIN")
            ),
            allowed_server=allowed_server,
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        """Validate the non-negotiable Phase-1/V1 configuration contract."""

        if not self.require_demo_account:
            raise ConfigError(
                "GSTAI_REQUIRE_DEMO cannot be disabled in V1; positive DEMO verification is required"
            )
        if not self.preferred_symbol:
            raise ConfigError("GSTAI_PREFERRED_SYMBOL cannot be empty")
        if not self.symbol_aliases:
            raise ConfigError("GSTAI_SYMBOL_ALIASES must contain at least one symbol")
        if self.preferred_symbol not in self.symbol_aliases:
            raise ConfigError("preferred symbol must also be present in GSTAI_SYMBOL_ALIASES")
        if self.log_level not in _VALID_LOG_LEVELS:
            raise ConfigError(
                f"GSTAI_LOG_LEVEL must be one of {sorted(_VALID_LOG_LEVELS)}, got {self.log_level!r}"
            )
        if self.state_dir == Path(""):
            raise ConfigError("GSTAI_STATE_DIR cannot be empty")

    @property
    def logging_level(self) -> int:
        return getattr(logging, self.log_level)

    def safe_summary(self) -> dict[str, object]:
        """Return only fields safe to log or display publicly."""

        return {
            "environment": self.environment,
            "preferred_symbol": self.preferred_symbol,
            "symbol_aliases": list(self.symbol_aliases),
            "require_demo_account": self.require_demo_account,
            "manual_reset_enabled": self.manual_reset_enabled,
            "state_dir": str(self.state_dir),
            "log_level": self.log_level,
            "allowed_account_login": self.allowed_account_login,
            "allowed_server": self.allowed_server,
        }
