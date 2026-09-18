from __future__ import annotations

from uuid import UUID

import pytest

from goldswingtraderai.domain.ids import EntityId, new_id, new_opportunity_id


def test_id_round_trip() -> None:
    entity_id = EntityId("OPP", "0" * 32)
    assert str(entity_id) == "OPP_" + ("0" * 32)
    assert EntityId.parse(str(entity_id)) == entity_id


def test_new_id_uses_kind_and_uuid_hex() -> None:
    entity_id = new_id("PLAN", uuid_factory=lambda: UUID(int=1))
    assert entity_id.kind == "PLAN"
    assert entity_id.value == UUID(int=1).hex


def test_invalid_id_rejected() -> None:
    with pytest.raises(ValueError):
        EntityId.parse("bad-id")


def test_factory_ids_are_unique() -> None:
    assert new_opportunity_id() != new_opportunity_id()
