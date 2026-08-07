---
name: python-module-move-all-surface-sweep
description: "Use when: (1) moving a Python module into a package, (2) renaming an import path used by tests, shell commands, documentation, templates, or CI, (3) a migration needs proof that packaging metadata, module entry points, patch seams, and operational references all moved together."
category: architecture
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [python, module-migration, imports, entrypoints, packaging, stale-references]
---

# Python Module Move All-Surface Sweep

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-07 |
| **Objective** | Complete a Python module move across code, packaging, tests, automation, templates, and operator documentation without leaving dormant references. |
| **Outcome** | The module moved with history preserved, both import and `python -m` execution worked, and an all-surface search found no unintended old references; local validation passed. |
| **Verification** | verified-local |

## When to Use

- Moving `<source-root>/tool.py` to `<package>/__init__.py` or another package module.
- Changing a dotted import path that appears in monkeypatch strings or mock targets.
- Shell scripts, task runners, CI, templates, or runbooks invoke the old module path.
- Unit tests pass after a move but packaging, coverage, or installed execution still fails.

## Verified Workflow

### Quick Reference

```bash
git mv <old-module-path> <new-module-path>

rg -n --hidden \
  --glob '!<historical-docs>/**' \
  --glob '!<generated-or-vendored>/**' \
  'old\.module\.path|old/module/path' .

python -m new.module.path --help
<package-manager> run pytest <focused-tests>
<package-manager> run <validation-task>
```

### Detailed Steps

1. Inventory the old path in tracked filenames and content before moving anything. Search both dotted (`old.module`) and slashed (`old/module`) forms.
2. Use `git mv` for the structural move so history and review intent remain visible.
3. Preserve module execution when it is part of the public contract. Add or update `__main__.py` so `python -m new.module` delegates to the package's `main()` without duplicating business logic.
4. Update packaging metadata: package discovery, console-script targets, included package data, and coverage source paths. Verify the installed or locked environment, not only source-tree imports.
5. Sweep every active reference surface:
   - Python imports and re-exports;
   - string-based monkeypatch and mock targets;
   - shell scripts and task-runner recipes;
   - CI and configuration files;
   - operational documentation and examples;
   - template files and generated-command sources.
6. Exclude historical records only through narrow, documented globs. Do not exclude an entire documentation tree when it contains active runbooks.
7. Run behavioral entrypoint checks using `sys.executable -m new.module --help` or a safe smoke command. Import success alone does not prove module execution or packaging is correct.
8. Re-run the old-path search and require zero unintended matches. Review each intentional historical match rather than filtering it away implicitly.

### Minimal `__main__.py`

```python
from __future__ import annotations

from . import main


if __name__ == "__main__":
    raise SystemExit(main())
```

### External-Binary Test Preflight

When an entrypoint test depends on an external executable, prove that the candidate binary works rather than only checking that a path exists:

```python
import subprocess


subprocess.run(
    [binary, "--version"],
    check=True,
    capture_output=True,
    text=True,
    timeout=5,
)
```

Use `check=True` or inspect `returncode` immediately. Otherwise a broken executable can silently satisfy the fixture and make later failures misleading.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Search only `*.py` | Updated imports and source references | Missed shell invocations, task recipes, templates, configuration, and runbooks | Search every active text surface in both dotted and slashed forms. |
| Exclude all documentation | Removed noisy historical hits by skipping the docs tree | Active operator examples retained the old command | Exclude only explicitly historical subtrees. |
| Replace dotted paths only | Rewrote `old.module.path` | Slash-form paths and filenames remained stale | Search and replace dotted, slashed, and tracked-filename forms separately. |
| Validate imports only | Imported the new package successfully | `python -m`, console scripts, or package discovery could still be broken | Exercise each supported entrypoint from the installed environment. |
| Accept a binary path without checking its exit status | Used `check=False` and ignored the return code | A present but broken executable passed preflight | Use `check=True` or assert the return code immediately. |

## Results & Parameters

### Completion Checklist

```yaml
structure:
  - tracked move is visible in git status
  - old source path is absent
python:
  - imports resolve from the new path
  - string patch targets reference the defining or consumer module intentionally
  - python -m execution works when supported
packaging:
  - package discovery includes the destination
  - console-script targets and package data are current
  - coverage sources use the new path
operations:
  - shell, task-runner, CI, docs, and templates use the new command
verification:
  - old dotted and slashed references have no unintended matches
  - focused tests and full validation pass
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private Python service repository | Script-to-package migration | Active references across code, tests, automation, configuration, templates, and documentation were migrated; module execution and the full local suite passed. Identifying details were intentionally generalized. |

## References

- [Python CLI entry-point patterns](python-cli-dry-run-and-entrypoint-patterns.md)
- [Logical and physical rename boundaries](logical-model-family-rename-with-storage-exceptions.md)
