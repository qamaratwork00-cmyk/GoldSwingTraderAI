"""Validated runtime settings for GoldSwingTraderAI V1.

Only non-secret configuration belongs here. Authority-bearing credentials must be
supplied through secure/local mechanisms and must never be committed.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import TypeVar

from dotenv import load_dotenv


class ConfigError(ValueError):
    """Raised when runtime configuration violates a V1 configuration contract."""


_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}
_VALID_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
_EnumT = TypeVar("_EnumT", bound=StrEnum)


class RuntimeMode(StrEnum):
    """Explicit launcher mode; the safe default performs read-only readiness only."""

    READINESS = "READINESS"
    PRIMARY = "PRIMARY"
    STANDBY = "STANDBY"


class RuntimeStateMode(StrEnum):
    """How startup selects durable runtime state."""

    EXISTING = "EXISTING"
    INITIALIZE = "INITIALIZE"
    RESTORE = "RESTORE"


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
    if not isfinite(value) or value <= 0:
        raise ConfigError(f"{name} must be positive when provided")
    return value


def _parse_optional_nonnegative_int(name: str, raw: str | None) -> int | None:
    if raw is None or not raw.strip():
        return None
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer when provided") from exc
    if value < 0:
        raise ConfigError(f"{name} cannot be negative")
    return value


def _parse_optional_positive_float(name: str, raw: str | None) -> float | None:
    if raw is None or not raw.strip():
        return None
    try:
        value = float(raw.strip())
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number when provided") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be positive when provided")
    return value


def _parse_enum(name: str, raw: str, enum_type: type[_EnumT]) -> _EnumT:
    value = raw.strip().upper()
    try:
        return enum_type(value)
    except ValueError as exc:
        choices = ", ".join(item.value for item in enum_type)
        raise ConfigError(f"{name} must be one of {choices}, got {raw!r}") from exc


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable, secret-free V1 runtime settings.

    DEMO-only broker-write authority is intentionally not configurable. The
    positive DEMO guard is a runtime account-verification invariant, implemented
    at the broker/execution boundary rather than as an environment switch.
    """

    environment: str
    preferred_symbol: str
    symbol_aliases: tuple[str, ...]
    manual_reset_enabled: bool
    state_dir: Path
    log_level: str
    allowed_account_login: int | None = None
    allowed_server: str | None = None
    runtime_mode: RuntimeMode = RuntimeMode.READINESS
    state_mode: RuntimeStateMode = RuntimeStateMode.EXISTING
    mt5_magic: int | None = None
    mt5_deviation_points: int | None = None
    mt5_comment_prefix: str = "GSTAI"
    restore_checkpoint: Path | None = None
    healthy_spread_baseline: float | None = None
    session_news_file: Path | None = None
    session_news_ttl_seconds: int = 1800
    readiness_keep_alive: bool = True
    readiness_poll_seconds: float = 30.0

    @classmethod
    def from_env(cls, env_file: str | Path | None = ".env") -> "Settings":
        """Load and validate non-secret settings from environment variables."""

        if env_file is not None:
            load_dotenv(dotenv_path=env_file, override=False)

        preferred_symbol = os.getenv("GSTAI_PREFERRED_SYMBOL", "XAUUSDm").strip()
        aliases_raw = os.getenv("GSTAI_SYMBOL_ALIASES", "XAUUSDm,XAUUSD")
        aliases = tuple(dict.fromkeys(part.strip() for part in aliases_raw.split(",") if part.strip()))

        allowed_server = os.getenv("GSTAI_ALLOWED_SERVER")
        if allowed_server is not None:
            allowed_server = allowed_server.strip() or None

        restore_checkpoint_raw = os.getenv("GSTAI_RESTORE_CHECKPOINT")
        restore_checkpoint = (
            Path(restore_checkpoint_raw).expanduser()
            if restore_checkpoint_raw is not None and restore_checkpoint_raw.strip()
            else None
        )

        session_news_file_raw = os.getenv("GSTAI_SESSION_NEWS_FILE")
        session_news_file = (
            Path(session_news_file_raw).expanduser()
            if session_news_file_raw is not None and session_news_file_raw.strip()
            else None
        )

        settings = cls(
            environment=os.getenv("GSTAI_ENV", "development").strip() or "development",
            preferred_symbol=preferred_symbol,
            symbol_aliases=aliases,
            manual_reset_enabled=_parse_bool(
                "GSTAI_MANUAL_RESET_ENABLED",
                os.getenv("GSTAI_MANUAL_RESET_ENABLED", "false"),
            ),
            state_dir=Path(os.getenv("GSTAI_STATE_DIR", ".state")).expanduser(),
            log_level=os.getenv("GSTAI_LOG_LEVEL", "INFO").strip().upper(),
            allowed_account_login=_parse_optional_int(
                "GSTAI_ALLOWED_ACCOUNT_LOGIN", os.getenv("GSTAI_ALLOWED_ACCOUNT_LOGIN")
            ),
            allowed_server=allowed_server,
            runtime_mode=_parse_enum(
                "GSTAI_RUNTIME_MODE",
                os.getenv("GSTAI_RUNTIME_MODE", RuntimeMode.READINESS.value),
                RuntimeMode,
            ),
            state_mode=_parse_enum(
                "GSTAI_STATE_MODE",
                os.getenv("GSTAI_STATE_MODE", RuntimeStateMode.EXISTING.value),
                RuntimeStateMode,
            ),
            mt5_magic=_parse_optional_int("GSTAI_MT5_MAGIC", os.getenv("GSTAI_MT5_MAGIC")),
            mt5_deviation_points=_parse_optional_nonnegative_int(
                "GSTAI_MT5_DEVIATION_POINTS", os.getenv("GSTAI_MT5_DEVIATION_POINTS")
            ),
            mt5_comment_prefix=os.getenv("GSTAI_MT5_COMMENT_PREFIX", "GSTAI").strip(),
            restore_checkpoint=restore_checkpoint,
            healthy_spread_baseline=_parse_optional_positive_float(
                "GSTAI_HEALTHY_SPREAD_BASELINE",
                os.getenv("GSTAI_HEALTHY_SPREAD_BASELINE"),
            ),
            session_news_file=session_news_file,
            session_news_ttl_seconds=_parse_optional_int(
                "GSTAI_SESSION_NEWS_TTL_SECONDS",
                os.getenv("GSTAI_SESSION_NEWS_TTL_SECONDS", "1800"),
            )
            or 1800,
            readiness_keep_alive=_parse_bool(
                "GSTAI_READINESS_KEEP_ALIVE",
                os.getenv("GSTAI_READINESS_KEEP_ALIVE", "true"),
            ),
            readiness_poll_seconds=_parse_optional_positive_float(
                "GSTAI_READINESS_POLL_SECONDS",
                os.getenv("GSTAI_READINESS_POLL_SECONDS", "30"),
            )
            or 30.0,
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        """Validate the non-secret Phase-1/V1 configuration contract."""

        if not self.preferred_symbol:
            raise ConfigError("GSTAI_PREFERRED_SYMBOL cannot be empty")
        if not self.symbol_aliases or any(not alias.strip() for alias in self.symbol_aliases):
            raise ConfigError("GSTAI_SYMBOL_ALIASES must contain at least one symbol")
        if self.preferred_symbol not in self.symbol_aliases:
            raise ConfigError("preferred symbol must also be present in GSTAI_SYMBOL_ALIASES")
        if self.log_level not in _VALID_LOG_LEVELS:
            raise ConfigError(
                f"GSTAI_LOG_LEVEL must be one of {sorted(_VALID_LOG_LEVELS)}, got {self.log_level!r}"
            )
        if self.state_dir == Path(""):
            raise ConfigError("GSTAI_STATE_DIR cannot be empty")
        if self.runtime_mode is not RuntimeMode.READINESS:
            if self.mt5_magic is None:
                raise ConfigError(
                    "GSTAI_MT5_MAGIC is required for PRIMARY/STANDBY runtime mode"
                )
            if self.mt5_deviation_points is None:
                raise ConfigError(
                    "GSTAI_MT5_DEVIATION_POINTS is required for PRIMARY/STANDBY runtime mode"
                )
        if not self.mt5_comment_prefix or len(self.mt5_comment_prefix) > 12:
            raise ConfigError("GSTAI_MT5_COMMENT_PREFIX must contain 1-12 characters")
        if self.state_mode is RuntimeStateMode.RESTORE and self.restore_checkpoint is None:
            raise ConfigError(
                "GSTAI_RESTORE_CHECKPOINT is required when GSTAI_STATE_MODE=RESTORE"
            )
        if self.state_mode is not RuntimeStateMode.RESTORE and self.restore_checkpoint is not None:
            raise ConfigError(
                "GSTAI_RESTORE_CHECKPOINT is only valid when GSTAI_STATE_MODE=RESTORE"
            )
        if self.healthy_spread_baseline is not None and (
            not isfinite(self.healthy_spread_baseline) or self.healthy_spread_baseline <= 0
        ):
            raise ConfigError("GSTAI_HEALTHY_SPREAD_BASELINE must be positive when provided")
        if self.session_news_ttl_seconds <= 0:
            raise ConfigError("GSTAI_SESSION_NEWS_TTL_SECONDS must be positive")
        if self.readiness_poll_seconds <= 0 or not isfinite(self.readiness_poll_seconds):
            raise ConfigError("GSTAI_READINESS_POLL_SECONDS must be positive")
        if (
            self.runtime_mode is RuntimeMode.READINESS
            and self.state_mode is not RuntimeStateMode.EXISTING
        ):
            raise ConfigError(
                "GSTAI_STATE_MODE INITIALIZE/RESTORE requires PRIMARY or STANDBY runtime mode"
            )

    @property
    def logging_level(self) -> int:
        return getattr(logging, self.log_level)

    def safe_summary(self) -> dict[str, object]:
        """Return fields that are safe to log or display publicly."""

        return {
            "environment": self.environment,
            "preferred_symbol": self.preferred_symbol,
            "symbol_aliases": list(self.symbol_aliases),
            "manual_reset_enabled": self.manual_reset_enabled,
            "state_dir": str(self.state_dir),
            "log_level": self.log_level,
            "allowed_account_login": self.allowed_account_login,
            "allowed_server": self.allowed_server,
            "runtime_mode": self.runtime_mode.value,
            "state_mode": self.state_mode.value,
            "mt5_magic": self.mt5_magic,
            "mt5_deviation_points": self.mt5_deviation_points,
            "mt5_comment_prefix": self.mt5_comment_prefix,
            "restore_checkpoint": (
                None if self.restore_checkpoint is None else str(self.restore_checkpoint)
            ),
            "healthy_spread_baseline": self.healthy_spread_baseline,
            "session_news_file": (
                None if self.session_news_file is None else str(self.session_news_file)
            ),
            "session_news_ttl_seconds": self.session_news_ttl_seconds,
            "readiness_keep_alive": self.readiness_keep_alive,
            "readiness_poll_seconds": self.readiness_poll_seconds,
        }
