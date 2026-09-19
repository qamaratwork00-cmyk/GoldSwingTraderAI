from pathlib import Path

from scripts.verify_documentation import check_documentation


def test_frozen_documentation_contract_is_consistent() -> None:
    repository_root = Path(__file__).resolve().parents[1]

    assert check_documentation(repository_root) == []
