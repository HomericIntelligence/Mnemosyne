---
name: ci-workflow-discovery-yaml-suffix-parity
license: BSD-3-Clause
description: "Unify GitHub Actions workflow discovery across .yml and .yaml. Use when: (1) inventory or checkout validation recognizes only one YAML suffix, (2) README parsing and pre-commit triggers drift from filesystem discovery, (3) compatibility helpers duplicate workflow glob logic."
category: ci-cd
date: 2026-08-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [github-actions, workflow-inventory, yaml, yml, discovery, pre-commit, pathlib]
---

# CI Workflow Discovery YAML Suffix Parity

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Make one collector authoritative for GitHub Actions workflow discovery while keeping inventory documentation and trigger filters consistent for `.yml` and `.yaml`. |
| **Outcome** | A reviewed implementation pattern and boundary-test matrix; implementation and CI validation are pending. |
| **Verification** | unverified |

GitHub Actions accepts both `.yml` and `.yaml`, so every layer that discovers, documents, or
reacts to workflow files must share the same suffix contract. Fixing the filesystem glob alone
leaves silent gaps if README parsing or pre-commit path filters still recognize only `.yml`.

## When to Use

- A repository inventory reports `.yml` workflows correctly but ignores `.yaml` files.
- Checkout validation, documentation drift checks, and direct file validation use different
  discovery helpers.
- An exported suffix-specific helper cannot be removed without an avoidable compatibility break.
- A pre-commit inventory hook does not run when a `.yaml` workflow changes.
- A README workflow table parser matches filenames ending in `.yml` only.

## Verified Workflow Status

No end-to-end workflow has been verified. The design below comes from a reviewed
ProjectHephaestus implementation plan and must remain a proposal until its focused and CI suites
pass.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until CI confirms.

### Quick Reference

```python
import re
import sys
from pathlib import Path

_WORKFLOW_GLOBS = ("*.yml", "*.yaml")
_WORKFLOW_SUFFIXES = frozenset({".yml", ".yaml"})
_TABLE_FILENAME_RE = re.compile(
    r"\|\s*\[?([a-zA-Z0-9_.-]+\.ya?ml)\]?[^|]*\|"
)


def collect_workflow_files(paths: list[str]) -> list[Path]:
    """Return deduplicated .yml and .yaml files from files or directories."""
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            if path.suffix in _WORKFLOW_SUFFIXES:
                files.append(path)
        elif path.is_dir():
            for pattern in _WORKFLOW_GLOBS:
                files.extend(sorted(path.glob(pattern)))
        else:
            print(f"WARNING: Path not found: {path}", file=sys.stderr)

    seen: set[Path] = set()
    result: list[Path] = []
    for workflow_file in files:
        key = workflow_file.resolve()
        if key not in seen:
            seen.add(key)
            result.append(workflow_file)
    return result
```

Use one regex shape in path-trigger configuration as well:

```yaml
files: ^(\.pre-commit-config\.yaml|\.github/workflows/(README\.md|.*\.ya?ml))$
```

### Detailed Steps

1. Define the accepted suffix set once for direct-file filtering and a small tuple of glob
   patterns for directory scans. Do not use a broad `*.yaml*` pattern.
2. Make one collector accept both files and directories. For files, reject unsupported suffixes;
   for directories, scan both explicit patterns.
3. Deduplicate with `Path.resolve()` keys so the same file supplied directly and through a
   directory appears once. Preserve the original `Path` object and first-seen order in the
   returned list.
4. Keep an exported legacy helper when callers may import it, but turn it into a compatibility
   wrapper over the canonical collector. It may reshape the result, such as returning basenames,
   but must not own another glob.
5. Route inventory comparison and checkout validation through the canonical collector. This
   prevents one consumer from gaining suffix support while another remains stale.
6. Update adjacent recognition layers in the same change:
   - README table parsing: match `\.ya?ml`.
   - Pre-commit selectors: match `.*\.ya?ml`.
   - Help text and diagnostics: say `.yml and .yaml`, not `*.yml`.
7. Add behavior-first tests for directory discovery, direct files, deduplication, README parsing,
   documented inventory, undocumented `.yaml`, and the exact pre-commit selector contract.
8. Run the focused workflow tests, then the surrounding CI-helper suite.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Independent suffix-specific helpers | Inventory used a `.yml` glob while checkout validation used a separate collector. | The two consumers could recognize different workflow sets and drift again after a local fix. | Discovery authority should live in one collector; compatibility helpers should delegate. |
| Change only the filesystem glob | Add `*.yaml` discovery but leave README parsing and pre-commit selectors unchanged. | `.yaml` becomes discoverable but cannot be documented reliably and may not trigger the inventory hook. | Treat discovery, documentation parsing, triggers, and diagnostics as one suffix contract. |
| Remove the old exported helper | Delete a helper after repository grep finds no internal callers. | Package exports are compatibility surfaces even when the current repository has no caller. | Preserve the export as a thin wrapper unless a breaking change is intentional. |
| Deduplicate by raw path text | Compare `Path` objects exactly as supplied. | Relative, absolute, and directory-discovered references to the same file can survive as duplicates. | Deduplicate by resolved identity while returning the first original path. |

## Results & Parameters

Target contract:

```yaml
accepted_suffixes: [.yml, .yaml]
directory_scan: non-recursive
unsupported_direct_files: ignored
missing_paths: warning_to_stderr
deduplication_key: resolved_path
result_order: first_seen
legacy_exports: delegate_to_canonical_collector
readme_filename_pattern: "\\.ya?ml"
precommit_filename_pattern: ".*\\.ya?ml"
```

Boundary-test matrix:

| Case | Expected result |
|------|-----------------|
| Directory contains `ci.yml` and `release.yaml` | Both files are returned. |
| Same workflow passed directly and through its directory | One result is returned. |
| Direct `README.md` or unrelated YAML-adjacent suffix | Ignored. |
| README documents both suffixes | Inventory is in sync. |
| Undocumented `.yaml` workflow | Reported as missing documentation. |
| `.yaml` workflow changes | Inventory pre-commit hook selector matches. |

Suggested verification commands:

```bash
<package-manager> pytest <workflow-test-path> -v
<package-manager> pytest <ci-helper-test-directory> -v
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Reviewed implementation plan for shared workflow discovery and suffix parity | Not implemented; local and CI validation pending. |
