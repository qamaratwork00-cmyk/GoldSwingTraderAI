"""Verify the new Documents manual without changing the legacy docs contract."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
_METADATA_FIELDS = ("**Status:**", "**Version:**", "**Authority:**")

_REQUIRED_FILES = (
    "Documents/README.md",
    "Documents/GLOSSARY.md",
    "Documents/CODER_GUIDE.md",
    "Documents/PROJECT_BUILD_AND_RECOVERY_GUIDE.md",
    "Documents/FINAL_BUILD_PROMPT.md",
    "Documents/SETUP_AND_RUN_GUIDE.md",
    "Documents/USER_MANUAL.md",
    "Documents/00-foundation/PROJECT_VISION.md",
    "Documents/00-foundation/SYSTEM_CONTRACT.md",
    "Documents/00-foundation/ARCHITECTURE.md",
    "Documents/00-foundation/BUILD_PHASES.md",
    "Documents/20-trading-decisions/TRADE_PLAN.md",
    "Documents/30-risk-execution/EXECUTION_AND_BROKER_SAFETY.md",
    "Documents/40-research-learning/RESEARCH_AND_VALIDATION.md",
    "Documents/50-operator/DASHBOARD_AND_UX.md",
    "Documents/60-engineering/MODULE_STRUCTURE.md",
    "Documents/60-engineering/FILE_AND_TEST_CATALOG.md",
    "Documents/60-engineering/CODING_STANDARD.md",
    "Documents/60-engineering/SYSTEM_HEALTH_AND_DIAGNOSTICS.md",
    "Documents/60-engineering/TESTING_AND_VERIFICATION.md",
    "Documents/60-engineering/RELEASE_CHECKLIST.md",
    "Documents/60-engineering/FINAL_RELEASE_AUDIT.md",
    "Documents/90-governance/DOCUMENTATION_STANDARD.md",
    "Documents/90-governance/CONTENT_COVERAGE_MATRIX.md",
    "Documents/90-governance/DOCUMENTATION_AUDIT.md",
    "Documents/90-governance/DESIGN_DECISIONS.md",
    "Documents/90-governance/OPEN_QUESTIONS.md",
)

_REQUIRED_MARKERS: dict[str, tuple[str, ...]] = {
    "Documents/README.md": (
        "## Authority rule",
        "FILE_AND_TEST_CATALOG.md",
        "DEMO Guard",
    ),
    "Documents/CODER_GUIDE.md": (
        "Phase 1",
        "Phase 10",
        "Phase 11",
        "Phase 12",
        "DEMO Guard",
        "Feature-to-code traceability",
    ),
    "Documents/00-foundation/BUILD_PHASES.md": (
        "Phase 1",
        "Phase 9",
        "Phase 10",
        "Phase 11",
        "Phase 12",
    ),
    "Documents/90-governance/DOCUMENTATION_STANDARD.md": (
        "Preservation-first",
        "affected-graph",
        "freeze",
    ),
    "Documents/60-engineering/TESTING_AND_VERIFICATION.md": (
        "Evidence ladder",
        "Controlled evidence boundary",
        "test_dashboard.py",
    ),
}


def _relative_link_errors(path: Path, text: str) -> list[str]:
    """Return broken local Markdown links from one document."""

    errors: list[str] = []
    for raw_target in _MARKDOWN_LINK.findall(text):
        target = raw_target.split("#", 1)[0].strip().strip("<>")
        if (
            not target
            or target.startswith("#")
            or "://" in target
            or target.startswith("mailto:")
        ):
            continue
        if not (path.parent / target).exists():
            errors.append(f"{path}: broken link -> {raw_target}")
    return errors


def check_documents_manual(repository_root: Path) -> list[str]:
    """Return structural violations for the new documentation manual."""

    root = repository_root.resolve()
    documents_root = root / "Documents"
    if not documents_root.is_dir():
        return [f"missing new documentation root: {documents_root}"]

    errors: list[str] = []
    for relative in _REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required Documents file: {relative}")

    all_markdown = sorted(documents_root.rglob("*.md"))
    all_text = "\n".join(path.read_text(encoding="utf-8") for path in all_markdown)

    for relative, markers in _REQUIRED_MARKERS.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{relative}: missing required marker: {marker}")

    for path in all_markdown:
        text = path.read_text(encoding="utf-8")
        errors.extend(_relative_link_errors(path, text))
        if path == documents_root / "README.md":
            continue
        for field in _METADATA_FIELDS:
            if field not in text:
                errors.append(f"{path}: missing document metadata field: {field}")

    package_root = root / "src" / "goldswingtraderai"
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root).as_posix()
        if relative not in all_text and path.name not in all_text:
            errors.append(f"source module is not named in Documents: {relative}")

    for path in sorted((root / "scripts").glob("*.py")):
        relative = path.relative_to(root).as_posix()
        if relative not in all_text and path.name not in all_text:
            errors.append(f"script is not named in Documents: {relative}")

    for path in sorted((root / "tests").glob("test_*.py")):
        if path.name not in all_text:
            errors.append(f"test module is not named in Documents: {path.name}")

    return errors


def main(argv: list[str] | None = None) -> int:
    """Run the new-manual structural verifier."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repository_root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the root containing this script)",
    )
    args = parser.parse_args(argv)
    errors = check_documents_manual(args.repository_root)
    if errors:
        print("Documents manual contract FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Documents manual contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
