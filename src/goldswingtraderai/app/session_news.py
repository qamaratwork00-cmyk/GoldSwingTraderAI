"""Strict provider-neutral session/news handoff for the live runtime.

The runtime intentionally does not select a commercial calendar vendor. This
adapter defines the boundary that an accepted provider process can populate:
one atomically replaced JSON snapshot is read on every cycle, scoped to the
connected account/server/symbol, then converted through the existing session
and news permission owners. Any malformed, mis-scoped or future-dated input
raises so ``LiveStartupRuntime`` converts it to explicit UNKNOWN authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from goldswingtraderai.intelligence.news import (
    NewsFacts,
    ProviderHealth,
    RawScheduledEvent,
    normalize_news_facts,
)
from goldswingtraderai.risk.permissions import (
    BrokerSessionFacts,
    ClosureKind,
    SessionNewsPermission,
    combine_session_news_permission,
    evaluate_market_permission,
    evaluate_news_permission,
)

if TYPE_CHECKING:
    from goldswingtraderai.app.recovery_mt5 import MT5RecoveryTruth
    from goldswingtraderai.domain.market import MarketSnapshot


MAX_SNAPSHOT_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class SessionNewsObservation:
    """Authoritative session/news result shared by startup and live cycles."""

    permission: SessionNewsPermission
    news: NewsFacts | None = None
    holiday_context: bool = False


@dataclass(frozen=True, slots=True)
class FileSessionNewsProvider:
    """Read and validate one operator-managed session/news JSON snapshot.

    The file is an input handoff, not a credential store or a broker authority
    of its own. A separate provider process should write a complete temporary
    file and atomically replace the configured path. The runtime never writes
    this file and never treats a missing file as clear/safe.
    """

    path: Path
    freshness_ttl: timedelta = timedelta(minutes=30)

    def __post_init__(self) -> None:
        if not str(self.path).strip():
            raise ValueError("session/news snapshot path cannot be empty")
        if self.freshness_ttl <= timedelta(0):
            raise ValueError("session/news freshness TTL must be positive")

    def __call__(
        self,
        market: MarketSnapshot,
        recovery_truth: MT5RecoveryTruth,
        now_utc: datetime,
    ) -> SessionNewsObservation:
        _require_utc(now_utc)
        payload = self._read_payload()
        self._validate_scope(payload, market, recovery_truth)

        provider = _required_text(payload, "provider")
        provider_health = _enum_value(
            payload,
            "provider_health",
            ProviderHealth,
        )
        fetched_at_utc = _timestamp(payload.get("fetched_at_utc"), "fetched_at_utc")
        if fetched_at_utc is not None and fetched_at_utc > now_utc:
            raise ValueError("fetched_at_utc cannot be in the future")

        raw_events = payload.get("events")
        if not isinstance(raw_events, list):
            raise ValueError("events must be a JSON array")
        events = tuple(_parse_event(item) for item in raw_events)
        news = normalize_news_facts(
            events,
            provider=provider,
            provider_health=provider_health,
            fetched_at_utc=fetched_at_utc,
            as_of_utc=now_utc,
            freshness_ttl=self.freshness_ttl,
        )

        session_payload = _required_mapping(payload, "session")
        session = _parse_session(session_payload)
        market_permission = evaluate_market_permission(session, now_utc)
        news_permission = evaluate_news_permission(news, now_utc)
        permission = combine_session_news_permission(
            market_permission,
            news_permission,
        )
        return SessionNewsObservation(
            permission=permission,
            news=news,
            holiday_context=session.holiday_context,
        )

    def _read_payload(self) -> dict[str, Any]:
        try:
            size = self.path.stat().st_size
            if size > MAX_SNAPSHOT_BYTES:
                raise ValueError("session/news snapshot exceeds the size limit")
            raw = self.path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("session/news snapshot cannot be read as JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("session/news snapshot root must be a JSON object")
        if type(payload.get("schema_version")) is not int or payload["schema_version"] != 1:
            raise ValueError("unsupported session/news snapshot schema_version")
        return payload

    @staticmethod
    def _validate_scope(
        payload: Mapping[str, Any],
        market: MarketSnapshot,
        recovery_truth: MT5RecoveryTruth,
    ) -> None:
        scope = _required_mapping(payload, "scope")
        account_login = _required_int(scope, "account_login")
        server = _required_text(scope, "server")
        symbol = _required_text(scope, "symbol")
        expected_account = recovery_truth.snapshot.account
        if (
            account_login != expected_account.login
            or server != expected_account.server
            or symbol != recovery_truth.snapshot.symbol
            or symbol != market.meta.symbol
        ):
            raise ValueError("session/news snapshot scope does not match live broker facts")


def _parse_event(value: Any) -> RawScheduledEvent:
    data = _as_mapping(value, "event")
    return RawScheduledEvent(
        provider_event_id=_required_text(data, "provider_event_id"),
        title=_required_text(data, "title"),
        currency=_required_text(data, "currency"),
        scheduled_at_utc=_required_timestamp(data, "scheduled_at_utc"),
        impact=_required_text(data, "impact"),
    )


def _parse_session(data: Mapping[str, Any]) -> BrokerSessionFacts:
    return BrokerSessionFacts(
        tradeable=_required_bool(data, "tradeable"),
        schedule_verified=_required_bool(data, "schedule_verified"),
        next_close_utc=_timestamp(data.get("next_close_utc"), "next_close_utc"),
        next_close_kind=_optional_enum(data, "next_close_kind", ClosureKind),
        reopened_at_utc=_timestamp(data.get("reopened_at_utc"), "reopened_at_utc"),
        reopen_kind=_optional_enum(data, "reopen_kind", ClosureKind),
        clean_completed_m5_since_reopen=_optional_nonnegative_int(
            data,
            "clean_completed_m5_since_reopen",
            default=0,
        ),
        execution_normalized=_optional_bool(data, "execution_normalized", default=True),
        unresolved_gap_or_reconciliation=_optional_bool(
            data,
            "unresolved_gap_or_reconciliation",
            default=False,
        ),
        weekend_gap_assessed=_optional_bool(
            data,
            "weekend_gap_assessed",
            default=True,
        ),
        holiday_context=_optional_bool(data, "holiday_context", default=False),
    )


def _required_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    return _as_mapping(value, key)


def _as_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _required_bool(payload: Mapping[str, Any], key: str) -> bool:
    value = payload.get(key)
    if type(value) is not bool:
        raise ValueError(f"{key} must be a JSON boolean")
    return value


def _optional_bool(payload: Mapping[str, Any], key: str, *, default: bool) -> bool:
    if key not in payload:
        return default
    return _required_bool(payload, key)


def _required_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if type(value) is not int:
        raise ValueError(f"{key} must be a JSON integer")
    return value


def _optional_nonnegative_int(
    payload: Mapping[str, Any],
    key: str,
    *,
    default: int,
) -> int:
    value = default if key not in payload else _required_int(payload, key)
    if value < 0:
        raise ValueError(f"{key} cannot be negative")
    return value


def _enum_value(
    payload: Mapping[str, Any],
    key: str,
    enum_type: type[Any],
) -> Any:
    value = _required_text(payload, key).upper()
    try:
        return enum_type(value)
    except ValueError as exc:
        choices = ", ".join(item.value for item in enum_type)
        raise ValueError(f"{key} must be one of {choices}") from exc


def _optional_enum(
    payload: Mapping[str, Any],
    key: str,
    enum_type: type[Any],
) -> Any | None:
    if key not in payload or payload[key] is None:
        return None
    return _enum_value(payload, key, enum_type)


def _required_timestamp(payload: Mapping[str, Any], key: str) -> datetime:
    value = _timestamp(payload.get(key), key)
    if value is None:
        raise ValueError(f"{key} is required")
    return value


def _timestamp(value: Any, key: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be an ISO-8601 UTC string or null")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{key} is not a valid ISO-8601 timestamp") from exc
    _require_utc(parsed)
    return parsed.astimezone(timezone.utc)


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("session/news timestamps must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("session/news timestamps must be UTC")
