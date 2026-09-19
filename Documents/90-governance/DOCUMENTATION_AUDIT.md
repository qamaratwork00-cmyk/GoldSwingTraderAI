# GoldSwingTraderAI — Documentation Audit

**Status:** CANDIDATE FOR ADOPTION  
**Version:** 0.1-audit-protocol  
**Authority:** Structural review of the new Documents manual

## 1. Audit purpose

This audit checks whether the new manual is complete as a documentation system.
It does not claim that the software is DEMO-certified or that the strategy is
profitable.

The audit protects four boundaries:

1. old meaning is preserved or explicitly superseded;
2. every implementation file has a navigation and proof destination;
3. diagrams, links and metadata remain structurally usable;
4. deterministic software evidence is not confused with live broker evidence.

## 2. Audit flow

~~~mermaid
flowchart TB
    INVENTORY["Inventory source, tests and documents"] --> COVERAGE["Check destination and ownership"]
    COVERAGE --> STRUCTURE["Check metadata, links and diagrams"]
    STRUCTURE --> SEMANTICS["Review authority, phases and safety meaning"]
    SEMANTICS --> EVIDENCE["Run documentation and code checks"]
    EVIDENCE --> ADOPTION["Human adoption decision"]
~~~

The first four checks are documentation work. The last check is a release
decision and must remain explicit.

## 3. Automated checks

Run from the repository root:

~~~text
python scripts/verify_documents_manual.py .
python scripts/verify_documentation.py .
python -m pytest -q tests/test_documents_manual_contract.py tests/test_documentation_contract.py
~~~

The first command checks the new manual. The second deliberately checks the
legacy docs contract and must continue to pass while the two sets coexist.
Neither command replaces a human reading of the architecture and safety
contracts.

## 4. Manual review checklist

- [ ] Every substantive document has a purpose, authority and evidence boundary.
- [ ] The README reading order reaches every major subsystem.
- [ ] Phase 1–9, Phase 10, Phase 11 and Phase 12 are not blended.
- [ ] The runtime diagram shows parallel intelligence and ordered permission.
- [ ] The broker-write path contains DEMO Guard, Intent and reconciliation.
- [ ] Closed-candle chronology and M1 scope are visible.
- [ ] Unknown data, unknown ownership and corrupt state fail safely.
- [ ] Persistence, restart and two-machine coordination are visible.
- [ ] Dashboard and operator impact are described for each safety-facing area.
- [ ] Research cannot silently become live authority.
- [ ] The exact file/test catalog covers the current tree.
- [ ] Release documents state what is still external proof.

## 5. Preservation review

For a rewrite or migration, compare the source subject against
CONTENT_COVERAGE_MATRIX.md. Confirm that the new destination retains:

- rationale and constraints;
- negative rules and hard gates;
- source/test names;
- state transitions;
- restart and failure behaviour;
- dashboard and research consequences;
- unresolved questions and superseded decisions.

If a useful rule is absent, the audit fails even when the Markdown renders
correctly.

## 6. Current result fields

| Check | Result | Evidence |
|---|---|---|
| New-manual file inventory | PASS | Documents/ tree |
| Metadata coverage | PASS | verify_documents_manual.py |
| Local link coverage | PASS | verify_documents_manual.py |
| Source/test filename coverage | PASS | verify_documents_manual.py |
| Legacy docs compatibility | PENDING AT ADOPTION | verify_documentation.py |
| Diagram semantic review | PENDING HUMAN REVIEW | Architecture and topic files |
| Preservation review | PENDING HUMAN REVIEW | CONTENT_COVERAGE_MATRIX.md |
| Manual adoption | PENDING | Owner decision |

## 7. Adoption decision

The reviewer must choose one explicit outcome:

| Outcome | Meaning |
|---|---|
| ADOPT | Documents becomes the canonical current manual |
| ADOPT WITH LEGACY REFERENCE | Documents is canonical; old docs/ remains clearly historical |
| REVISE | Specific documentation defects must be corrected |
| HOLD | The manual is structurally sound but an external or governance decision is missing |

The result belongs in the release evidence and in the repository change
description. Do not silently change the authority relationship.
