# Automation God-Package Shim-First Decomposition — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Consolidate four Claude-agent modules around one canonical owner | [ProjectHephaestus issue #1441](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1441) | `verified-local`: Ruff, mypy, 145 focused tests | Retained explicit re-export and sorted `__all__` guidance |
| Move three state modules into `state/` | [ProjectHephaestus issue #1443](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1443) | `verified-local`: Ruff, mypy, 2,284 automation tests | Retained whole-test-tree patch-seam sweep and selective shim/canonical targets |
| Cross-test patching after symbol moves | [ProjectHephaestus issue #1813](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1813) | `verified-local`: 41-test automation-loop suite | Retained runtime lookup-context rule |
| Proposed 52-file split into eight domains | [ProjectHephaestus issue #1177](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1177) | `unverified`: plan only | Preserved as scale context, not executed evidence |

## Migration inventory

For each moved module, record:

| Field | Required evidence |
| --- | --- |
| Canonical destination | Domain and dependency direction |
| Public exports | Explicit symbol list and `__all__` |
| Old-path shim | Identity smoke result |
| Internal importers | Canonical target or justified shim retention |
| Patch/monkeypatch sites | Runtime lookup target after move |
| Logger/reload/caplog sites | Canonical module identity |
| Optional-extra boundary | Base import remains dependency-light |
| Focused/full checks | Command and observed result |

## Nuance from executed cases

- A flat-path patch remained correct when execution still occurred in the flat shim context; a
  canonical-path patch was required when moved code called its sibling directly.
- Imported-into names were the source of four failures missed by the nearest-module plan.
- Explicit `name as name` shims did not require F401 suppression; adding one would trigger RUF100.
- Ruff's RUF022 sorting takes precedence over visual domain grouping inside `__all__`.
- Boundary tests must be read before updating allowlists; path and direction matter.

## Evidence boundary

The merge, three-module split, and patch corollary are locally verified. The 52-file decomposition
remains a proposal and must be re-inventoried against the current repository before implementation.
