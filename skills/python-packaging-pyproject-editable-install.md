---
name: python-packaging-pyproject-editable-install
description: "Maintain pyproject-based Python packaging across VCS-derived versions, editable installs, console entry points, watcher migration, trusted publishing, and runtime package data. Use when a pull adds scripts but commands are missing, distribution/import names differ, templates vanish from artifacts, metadata races workers, or source-to-wheel/sdist parity needs proof."
category: tooling
date: 2026-07-20
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: mixed
history: python-packaging-pyproject-editable-install.history
tags: [python-packaging, pyproject, hatch-vcs, editable-install, entry-points, package-data, pypi]
---

# Python Packaging, Pyproject, and Editable Installs

## Overview

Packaging is a multi-surface contract: build backend, VCS version source, installed distribution
metadata, editable entry points, non-Python assets, wheel/sdist contents, and publishing identity
must agree. Validate the installed and built artifacts, not merely the source tree.

Cases and verification boundaries are indexed in
[`python-packaging-pyproject-editable-install.notes.md`](python-packaging-pyproject-editable-install.notes.md).
The complete prior source is in
[`python-packaging-pyproject-editable-install.history`](python-packaging-pyproject-editable-install.history).

## When to Use

- Migrating a hardcoded project version to Git-tag-derived hatch-vcs.
- A newly merged `[project.scripts]` command is missing after pull.
- CLI inventory by `def main` misses differently named callables.
- Replacing unmaintained `pytest-watch`/`docopt` with `pytest-watcher`.
- Publishing hatchling/hatch-vcs artifacts to PyPI via trusted publishing.
- Templates/JSON/YAML exist in source but are absent at runtime or from built artifacts.
- Workers start immediately after editable rebuild and resource metadata appears stale.
- A coordinator must fail before GitHub access or worker construction when resources are invalid.

## Verified Workflow

### 1. Migrate versioning as one invariant

Change all VCS-version surfaces together:

```toml
[project]
dynamic = ["version"]

[build-system]
requires = ["hatchling", "hatch-vcs"]

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.hooks.vcs]
version-file = "<package>/_version.py"
```

Remove the static project version. Ignore and lint-exclude the generated version file. At runtime,
call `importlib.metadata.version(<distribution-name>)`; the distribution name may differ from the
import package. Keep hatch-vcs as a build-system dependency rather than an unrelated runtime/dev
dependency.

Update consistency scripts to parse pyproject with `tomllib` and validate the dynamic-version
invariant. Where a canonical development version is needed, derive it from `git describe` with an
installed-metadata fallback; do not parse a removed static string.

### 2. Refresh editable installs after metadata changes

A source import succeeding does not prove entry-point metadata was regenerated. After pulling a
change to `[project.scripts]`, build hooks, dependencies, or package data, rerun the project’s editable
install:

```bash
pixi run dev-install
# or, for projects without that task:
python -m pip install -e .
```

Then inspect the environment’s `entry_points.txt`, run `which <command>`, invoke `--help`, and confirm
the installed version/head. Do not reinstall globally or blame shell PATH before checking the active
environment’s metadata.

### 3. Inventory console scripts from pyproject

Parse `[project.scripts]` as the authoritative name-to-callable map. Import each target, resolve the
exact callable (including `*_main`), and test a harmless contract such as `--help`, `--version`, or a
documented JSON mode. Grepping only `def main` misses valid entry points.

### 4. Migrate the watcher and lock together

Replace `pytest-watch` with a supported watcher in the dependency manifest, regenerate the lock, and
verify the invocation contract. `pytest-watcher` retains `ptw` but may require an explicit path such
as `ptw .`. Confirm the unwanted transitive dependency is gone from the resolved environment.

### 5. Configure trusted publishing coherently

Ensure `[project].name` exactly matches the PyPI project. Build wheel and sdist with the locked
backend, validate both, and configure the release job with `id-token: write` and the intended protected
environment. Register the matching trusted publisher, including pending publisher setup for a new
project. Do not fall back to a long-lived upload token merely because OIDC is incomplete.

### 6. Treat runtime data as package API

Identify every non-Python asset read by `importlib.resources`, Jinja loaders, or direct paths. Add it
to backend include rules and ensure package layout matches loader expectations. Build wheel and sdist
from one source revision, normalize the sdist’s distribution-root prefix, and compare the full source
asset path set to both artifact member sets. Do not freeze one expected asset count; path equality
catches additions and omissions.

Run an installed-artifact smoke test outside the repository so source-tree files cannot mask missing
package data.

### 7. Distinguish missing assets from editable metadata races

If data is absent on disk or from artifacts, fix packaging/source checkout. If assets exist but a
worker spawned immediately after `uv sync`/editable rebuild reports `PackageLoader` failure, avoid
metadata-dependent lookup for repository-owned templates: derive a filesystem loader path from the
module’s `__file__`. Preserve template syntax/rendering errors rather than converting every failure
to “missing directory.”

### 8. Fail before side effects

At the shared coordinator entry point, render one context-free catalog/template before GitHub calls,
worktree creation, or worker construction. Classify missing directory/file separately from template
parse/render errors and preserve the cause. Test operation ordering so invalid resources produce no
external calls and valid resources proceed exactly once.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Partial hatch-vcs migration | Removed static version only | Build/runtime/check scripts disagreed | Change all version surfaces together |
| Import-name metadata | Queried version by package name | Distribution used a different name | Use `[project].name` |
| Pull-only entry point | Expected editable metadata to self-refresh | Command remained absent | Reinstall editable project |
| `def main` inventory | Grepped function declarations | `*_main` entry points were missed | Parse `[project.scripts]` |
| Source-tree asset test | Ran loader only from checkout | Unpackaged files masked wheel omission | Test installed artifact outside repo |
| Fixed asset count | Asserted one historical number | New valid assets broke or omissions hid | Compare exact path sets |
| PackageLoader after rebuild | Relied on transient metadata | Workers raced editable metadata | Use module-relative filesystem loader |
| Late preflight | Checked templates after worker/GitHub setup | Long runs did no-op work | Render before side effects |
| Long-lived PyPI token | Bypassed incomplete OIDC setup | Added unnecessary secret | Complete trusted-publisher contract |

## Results & Parameters

```text
distribution name, import package, VCS tag pattern, generated version path
build-system backend/requirements and parsed dynamic-version invariant
editable environment, entry-point mapping, installed version/head
watcher dependency/command and lock delta
PyPI project, environment, trusted-publisher identity, OIDC permissions
source asset roots and normalized wheel/sdist member sets
installed-artifact smoke environment
resource loader path and error classification
coordinator preflight ordering and zero-side-effect failure proof
```

## Verified On

- ProjectHephaestus hatch-vcs, distribution-name, consistency, editable entry-point, and CLI inventory
  fixes; ProjectScylla build/publish flows.
- Coordinator resource preflight and exact artifact-parity case was planning-only when recorded.
- Verification is `mixed`; case-level status remains explicit in notes/history.
