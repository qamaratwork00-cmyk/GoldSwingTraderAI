from pathlib import Path

from scripts.verify_documents_manual import check_documents_manual


def test_new_documents_manual_contract_is_consistent() -> None:
    repository_root = Path(__file__).resolve().parents[1]

    assert check_documents_manual(repository_root) == []
