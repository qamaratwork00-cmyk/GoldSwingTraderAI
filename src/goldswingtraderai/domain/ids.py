"""Typed, parseable identifiers for durable GoldSwingTraderAI lineage."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable
from uuid import UUID, uuid4

_ID_RE = re.compile(r"^(?P<kind>[A-Z][A-Z0-9_]{1,31})_(?P<value>[0-9a-f]{32})$")


@dataclass(frozen=True, slots=True, order=True)
class EntityId:
    """A stable typed identifier suitable for persistence and reconciliation."""

    kind: str
    value: str

    def __post_init__(self) -> None:
        kind = self.kind.strip().upper()
        value = self.value.strip().lower()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{1,31}", kind):
            raise ValueError(f"invalid entity-id kind: {self.kind!r}")
        if not re.fullmatch(r"[0-9a-f]{32}", value):
            raise ValueError(f"invalid entity-id value: {self.value!r}")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "value", value)

    def __str__(self) -> str:
        return f"{self.kind}_{self.value}"

    @classmethod
    def parse(cls, raw: str) -> "EntityId":
        match = _ID_RE.fullmatch(raw.strip())
        if match is None:
            raise ValueError(f"invalid entity id: {raw!r}")
        return cls(kind=match.group("kind"), value=match.group("value"))


def new_id(kind: str, uuid_factory: Callable[[], UUID] = uuid4) -> EntityId:
    return EntityId(kind=kind, value=uuid_factory().hex)


def new_snapshot_id() -> EntityId:
    return new_id("SNAP")


def new_decision_id() -> EntityId:
    return new_id("DEC")


def new_opportunity_id() -> EntityId:
    return new_id("OPP")


def new_episode_id() -> EntityId:
    return new_id("EP")


def new_trade_plan_id() -> EntityId:
    return new_id("PLAN")


def new_execution_intent_id() -> EntityId:
    return new_id("INTENT")


def new_trade_id() -> EntityId:
    return new_id("TRADE")


def new_controller_id() -> EntityId:
    return new_id("CTRL")
