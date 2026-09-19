"""Verify the frozen project documentation contract."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")

_REQUIRED_FILES = (
    "README.md",
    "docs/README.md",
    "docs/CODER_GUIDE.md",
    "docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md",
    "docs/FINAL_BUILD_PROMPT.md",
    "docs/SETUP_AND_RUN_GUIDE.md",
    "docs/USER_MANUAL.md",
    "docs/90-governance/DOCUMENTATION_STANDARD.md",
    "docs/00-foundation/ARCHITECTURE.md",
    "docs/60-engineering/MODULE_STRUCTURE.md",
    "docs/60-engineering/TESTING_AND_VERIFICATION.md",
    "docs/60-engineering/FINAL_RELEASE_AUDIT.md",
)

_REQUIRED_MARKERS: dict[str, tuple[str, ...]] = {
    "docs/README.md": (
        "## Repository implementation coverage",
        "## Authority rule",
        "DOCUMENTATION_STANDARD.md",
    ),
    "docs/CODER_GUIDE.md": (
        "## 8. Feature-to-code traceability",
        "DEMO Guard",
        "ReadinessDashboardData",
        "## 14. Documentation change gate",
    ),
    "docs/CHATGPT_PROJECT_BUILD_AND_RECOVERY_GUIDE.md": (
        "## Frozen documentation-completeness protocol",
        "Phase 1–9",
        "Phase 10",
        "Phase 11",
        "Phase 12",
    ),
    "docs/FINAL_BUILD_PROMPT.md": (
        "DOCUMENTATION_STANDARD.md",
        "## Large implementation sequence",
        "## Validation principles",
    ),
    "docs/90-governance/DOCUMENTATION_STANDARD.md": (
        "## 13. Preservation-first update rule",
        "## 16. Frozen completeness and freeze protocol",
        "## 17. Whole-project guide minimum",
        "## 18. Final documentation gate",
    ),
    "docs/60-engineering/MODULE_STRUCTURE.md": (
        "## File-level ownership index",
        "app/main.py",
        "execution/mt5_writer.py",
        "operator/dashboard.py",
    ),
    "docs/60-engineering/TESTING_AND_VERIFICATION.md": (
        "Evidence ladder",
        "Controlled evidence boundary",
        "test_dashboard.py",
    ),
}

_SOURCE_AREAS = (
    "config/",
    "domain/",
    "diagnostics/",
    "security/",
    "market_data/",
    "intelligence/",
    "strategies/",
    "decisions/",
    "risk/",
    "execution/",
    "management/",
    "persistence/",
    "app/",
    "operator/",
    "research/",
    "scripts/",
    "tests/",
)


def _is_redirect(path: Path) -> bool:
    """Return whether a Markdown file is an intentional compatibility redirect."""

    first_heading = next(
        (
            line.strip().lower()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("# ")
        ),
        "",
    )
    return "moved" in first_heading


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


def check_documentation(repository_root: Path) -> list[str]:
    """Return documentation-contract violations for ``repository_root``."""

    root = repository_root.resolve()
    errors: list[str] = []
    docs_root = root / "docs"
    if not docs_root.is_dir():
        return [f"missing documentation root: {docs_root}"]

    for relative in _REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing required documentation file: {relative}")

    for relative, markers in _REQUIRED_MARKERS.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{relative}: missing required marker: {marker}")

    docs_readme = root / "docs/README.md"
    if docs_readme.is_file():
        docs_text = docs_readme.read_text(encoding="utf-8")
        for source_area in _SOURCE_AREAS:
            if f"`{source_area}`" not in docs_text:
                errors.append(f"docs/README.md: source area is not covered: {source_area}")

    all_documentation = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(docs_root.rglob("*.md"))
    )
    package_root = root / "src" / "goldswingtraderai"
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root).as_posix()
        if relative not in all_documentation and path.name not in all_documentation:
            errors.append(f"source module is not named in documentation: {relative}")
    for path in sorted((root / "scripts").glob("*.py")):
        relative = path.relative_to(root).as_posix()
        if relative not in all_documentation and path.name not in all_documentation:
            errors.append(f"script is not named in documentation: {relative}")
    for path in sorted((root / "tests").glob("test_*.py")):
        if path.name not in all_documentation:
            errors.append(f"test module is not named in documentation: {path.name}")

    for path in sorted(docs_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        errors.extend(_relative_link_errors(path, text))
        if path.name == "README.md" or _is_redirect(path):
            continue
        for field in ("**Status:**", "**Version:**", "**Authority:**"):
            if field not in text:
                errors.append(f"{path}: missing document metadata field: {field}")

    return errors


def main(argv: list[str] | None = None) -> int:
    """Run the documentation verifier as a command-line tool."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repository_root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the root containing this script)",
    )
    args = parser.parse_args(argv)
    errors = check_documentation(args.repository_root)
    if errors:
        print("Documentation contract FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Documentation contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
