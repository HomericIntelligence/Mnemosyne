---
name: hephaestus-write-secure-planning-guardrails
description: "Planning guardrails for migrating ProjectHephaestus automation state writers from deprecated github_api.write_secure imports to hephaestus.io.utils.write_secure while preserving compatibility aliases and patch seams. Use when: (1) planning a canonical import migration from a compatibility wrapper, (2) retaining an old module symbol as an identity re-export, (3) writing AST guards for deprecated imports and attribute usage."
category: architecture
date: 2026-06-26
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - projecthephaestus
  - planning
  - write-secure
  - compatibility
  - re-export
  - patch-seam
  - ast-guard
  - state-persistence
---

# ProjectHephaestus Write Secure Planning Guardrails

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-26 |
| **Objective** | Capture planning risks from a ProjectHephaestus issue #1402 plan to migrate automation state writers from `hephaestus.automation.github_api.write_secure` to canonical `hephaestus.io.utils.write_secure` while preserving compatibility and test patch seams. |
| **Outcome** | Planning artifact only. The implementation and CI were not executed in this session; every claim here is a reviewer checklist until verified against current `main`. |
| **Verification** | unverified |

This skill records the risky assumptions in a planning-stage refactor, not a completed fix. The plan's line numbers and grep evidence were useful hints, but they must be re-anchored to symbols and verified against the live tree before implementation.

## When to Use

- Planning or reviewing a ProjectHephaestus change that replaces imports from `hephaestus.automation.github_api.write_secure` with `hephaestus.io.utils.write_secure`.
- Keeping an old module-level symbol as a compatibility alias while removing a wrapper body.
- Deciding whether a patch seam such as `hephaestus.automation.github_api.io_write_secure` can be collapsed.
- Adding regression guards for deprecated imports or `github_api.write_secure` attribute usage.
- Testing state persistence code paths that should write JSON atomically with `0o600` permissions.
- Reviewing a plan that cites exact file coordinates for `github_api.py`, `_reviewer_base.py`, `implementer_state.py`, or tests.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Proposed Workflow

This section uses the validator-required `## Verified Workflow` heading, but the authoritative verification level is the frontmatter value `unverified`. The steps below are proposed guardrails for issue #1402-style work, not proof that the migration has already passed.

### Quick Reference

```bash
# Re-anchor the issue and plan against the live checkout before editing.
gh issue view 1402 --repo HomericIntelligence/ProjectHephaestus --json title,body

# Find deprecated import and attribute paths. Treat grep as discovery, not proof.
rg -n "from hephaestus\\.automation\\.github_api import .*write_secure|github_api\\.write_secure|io_write_secure" \
  hephaestus tests

# After implementation, the only allowed github_api write_secure reference should be
# the compatibility alias/export inside hephaestus/automation/github_api.py and tests
# that intentionally verify the alias.
rg -n "github_api\\.write_secure|from hephaestus\\.automation\\.github_api import .*write_secure" \
  hephaestus tests

# Proposed focused verification for the migrated state writers and guard.
pixi run pytest \
  tests/unit/automation/test_reviewer_base.py \
  tests/unit/automation/test_implementer_state.py \
  tests/unit/automation/test_github_api.py \
  tests/unit/automation/test_import_boundaries.py

pixi run ruff check hephaestus/ tests/
pixi run mypy hephaestus/
```

### Detailed Steps

1. **Re-fetch issue scope before treating it as authoritative.** The issue title, body, and affected-file list were treated as scope in the planning session but were not re-fetched there. Fetch issue #1402 or otherwise inspect the current issue metadata before accepting the plan's file list.

2. **Re-anchor every cited line number by symbol or content.** Coordinates such as `github_api.py:995`, `_reviewer_base.py`, `implementer_state.py`, and named test files are hints. Open the current files and locate `write_secure`, `io_write_secure`, `BaseReviewer._save_state`, and `ImplementationStateManager.save` by symbol/content before editing.

3. **Move production automation state writers to the canonical import.** Call sites such as `BaseReviewer._save_state` and `ImplementationStateManager.save` should import `write_secure` from `hephaestus.io.utils`, not from `hephaestus.automation.github_api`. The deprecated module should not remain the production dependency path.

4. **Preserve `github_api.write_secure` as an identity compatibility alias.** External callers may still import `hephaestus.automation.github_api.write_secure`. Do not delete the symbol unless compatibility evidence proves it is safe. The compatibility binding should be an alias to the canonical function, not a wrapper with its own behavior, and it should remain exported via `__all__`.

5. **Keep `io_write_secure` until every patch seam is audited.** Existing code and tests may patch `hephaestus.automation.github_api.io_write_secure`, including `gh_pr_review_post` behavior. Do not collapse `io_write_secure` merely because `write_secure` is now canonical; first verify every internal use and every test patch target.

6. **Make the import guard AST-based and alias-aware.** A string grep is not enough. The guard should scan `ast.ImportFrom` for `from hephaestus.automation.github_api import write_secure`, `ast.Import` aliases for `import hephaestus.automation.github_api as github_api`, `from hephaestus.automation import github_api as gh`, and `ast.Attribute` uses such as `github_api.write_secure` or `gh.write_secure` when the name resolves to the deprecated module.

7. **Test behavior, permissions, and compatibility identity.** Add focused tests that assert JSON round-trip and `0o600` permissions for `BaseReviewer._save_state` and `ImplementationStateManager.save`; assert `hephaestus.automation.github_api.write_secure is hephaestus.io.utils.write_secure`; assert `io_write_secure` remains a patchable seam where production code still uses it; and assert the AST regression guard rejects deprecated imports and simple alias attribute usage.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Delete `github_api.write_secure` after moving internal imports | The plan could be read as "all call sites move, so the old symbol can vanish" | First-party grep cannot prove no third-party caller imports `hephaestus.automation.github_api.write_secure`; deleting it is a compatibility break | Keep `github_api.write_secure` as a direct identity alias and `__all__` export unless external compatibility evidence says otherwise |
| Collapse `io_write_secure` into `write_secure` | Treat both names as redundant after canonicalizing state writers | Tests and `gh_pr_review_post` may patch `hephaestus.automation.github_api.io_write_secure`; collapsing it can remove a live patch seam | Preserve `io_write_secure` until all call sites and tests that patch it are audited |
| Guard only `ImportFrom` nodes | AST regression test catches `from hephaestus.automation.github_api import write_secure` only | Code can still use `import hephaestus.automation.github_api as github_api` or `from hephaestus.automation import github_api as gh` followed by `.write_secure` | Scan import aliases and attribute usage, including simple aliases that resolve to `github_api` |
| Treat absence of `retry_with_exponential_backoff` in grep as semantic proof | A grep showed the symbol absent in the checked-out tree | Absence in one checkout proves only the current filesystem state, not historical intent, issue metadata, or external references | Use grep absence only as current-tree evidence; re-fetch issue context and inspect history if that symbol affects scope |
| Implement from exact plan line numbers | The plan cited current coordinates such as `github_api.py:995` | Line numbers drift as soon as nearby code changes or another PR lands | Re-locate by stable symbol names and unique content before editing |

## Results & Parameters

### Reviewer Risk Checklist

```text
- [ ] `github_api.write_secure` is still present, exported, and identity-equal to `hephaestus.io.utils.write_secure`.
- [ ] Production automation state writers import canonical `hephaestus.io.utils.write_secure` directly.
- [ ] `io_write_secure` remains available for existing `github_api` internals/tests that patch it.
- [ ] The deprecated import guard catches ImportFrom, Import aliases, from-package aliases, and `.write_secure` attribute use.
- [ ] Persistence tests assert JSON round-trip and `0o600` permissions for both migrated state writers.
- [ ] Issue #1402 metadata and current file contents were re-read before implementation.
```

### Unverified External Inputs From the Planning Session

- GitHub issue #1402 title/body/affected-file list were treated as scope but not re-fetched in the planning turn.
- First-party grep cannot prove no third-party imports of `github_api.write_secure` exist.
- File coordinates for `github_api.py`, `_reviewer_base.py`, `implementer_state.py`, and tests were plan-time coordinates, not stable edit anchors.
- The plan proposed `pytest`, `ruff`, `mypy`, and `rg` verification commands but did not execute the implementation or CI.

### Minimal Compatibility Shape

```python
# hephaestus/automation/github_api.py
from hephaestus.io.utils import write_secure as io_write_secure

write_secure = io_write_secure

__all__ = [
    # existing exports...
    "io_write_secure",
    "write_secure",
]
```

The exact local code shape may differ, but the invariants are stable: `github_api.write_secure` is an identity alias for the canonical function, and `io_write_secure` remains as the patch seam while existing internals/tests depend on it.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Planning phase for GitHub issue #1402, replacing deprecated automation state `write_secure` imports with canonical `hephaestus.io.utils.write_secure` | unverified planning capture only; no implementation or CI run in the source session |
