---
name: tooling-pixi-lockfile-churn-self-reference
description: "Stop perpetual `pixi.lock` regeneration in Python projects that combine a self-referential `[pypi-dependencies]` editable path entry with `hatch-vcs` dynamic versioning. Use when: (1) every `pixi install` / `pixi run` rewrites `pixi.lock` even on a clean tree with no manifest edits, (2) pre-commit hooks fail because `pixi.lock` is perpetually dirty, (3) `pixi.toml` declares the package itself under `[pypi-dependencies]` with `path = \".\"` and `editable = true`, and (4) `pyproject.toml` uses `dynamic = [\"version\"]` with `[tool.hatch.version] source = \"vcs\"` (hatch-vcs). The combination makes pixi treat the source-of-truth version as changed on every invocation."
category: tooling
date: 2026-05-28
version: "1.1.0"
user-invocable: false
verification: verified-ci
history: tooling-pixi-lockfile-churn-self-reference.history
tags:
  - pixi
  - pixi-lock
  - lockfile-churn
  - hatch-vcs
  - dynamic-version
  - editable-install
  - pypi-dependencies
  - self-reference
  - pre-commit
  - no-build-isolation
  - lockfile-v7
  - ci-pin-completeness
  - composite-action
  - requires-pixi
---

# Pixi Lockfile Churn from Self-Reference + hatch-vcs

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-28 |
| **Objective** | Eliminate perpetual `pixi.lock` churn caused by combining a self-referential editable `[pypi-dependencies]` entry with `hatch-vcs` dynamic versioning in the same Python project. |
| **Outcome** | Two proven approaches: (A) localized fix — remove self-package entry + `pixi run dev-install`; (B) permanent format fix — migrate to lockfile v7 (Pixi >=0.68.0) which eliminates source-dependency input hashes entirely. |
| **Verification** | verified-ci — PRs #457, #526, #530, #532 (approach A) and PR #675 (approach B) all merged with CI green |

## When to Use

- Every `pixi install` or `pixi run <task>` rewrites `pixi.lock` on a clean tree with no manifest edits.
- Pre-commit fails repeatedly because `pixi.lock` shows up as dirty even though no human edited it.
- `pixi.toml` contains a self-referential editable entry like:

  ```toml
  [pypi-dependencies]
  mypackage = { path = ".", editable = true }
  ```

- And `pyproject.toml` declares:

  ```toml
  [project]
  dynamic = ["version"]

  [tool.hatch.version]
  source = "vcs"
  ```

- `git checkout -- pixi.lock` is blocked by a safety/pre-commit hook so manual cleanup fails.

## Verified Workflow

Two proven approaches are documented below.

## Approach A — Localized Fix (Remove Self-Reference)

Use when you cannot or do not want to bump Pixi across the ecosystem yet. Faster to land, no ecosystem-wide coordination required.

### Quick Reference

```toml
# pixi.toml — REMOVE this section (or remove the self-entry only):
# [pypi-dependencies]
# mypackage = { path = ".", editable = true }   # ← delete this line

# pixi.toml — ADD a task that installs the package editable on demand:
[tasks]
dev-install = "pip install -e . --no-deps"
```

```bash
# After the change, set up a working environment:
pixi install --environment default
pixi run dev-install                   # one-off editable install of the package itself

# Pre-commit / CI invocation pattern:
pixi install --environment default
pixi run dev-install
pixi run pre-commit run --all-files

# Verify pixi.lock no longer churns:
git status --porcelain pixi.lock       # should be empty after `pixi install`
pixi install && git diff --stat pixi.lock   # should report zero changes
```

### Detailed Steps

1. **Confirm the failure signature.** On a clean tree:

   ```bash
   git status --porcelain pixi.lock      # empty
   pixi install
   git status --porcelain pixi.lock      # NOT empty ⇒ churn confirmed
   ```

2. **Verify the two preconditions both hold:**

   - `pixi.toml` has a `[pypi-dependencies]` entry pointing at `path = "."` with `editable = true`.
   - `pyproject.toml` has `dynamic = ["version"]` plus `[tool.hatch.version] source = "vcs"`.

   If only one holds, this skill does not apply — see the
   `lockfile-and-release-pipeline-management` skill for general drift recovery.

3. **Remove the self-referential entry from `pixi.toml`.** Delete the
   `mypackage = { path = ".", editable = true }` line (and the entire
   `[pypi-dependencies]` table if it becomes empty).

4. **Add a `dev-install` task** that installs the package editable without
   touching the lockfile and without `--no-build-isolation`:

   ```toml
   [tasks]
   dev-install = "pip install -e . --no-deps"
   ```

   `--no-deps` is essential: dependencies are still managed by pixi, the
   `pip` step only registers the editable package itself.

5. **Update CI and pre-commit invocations** to call `pixi install` followed by
   `pixi run dev-install` before running hooks/tests that import the package:

   ```yaml
   - run: pixi install --environment default
   - run: pixi run dev-install
   - run: pixi run pre-commit run --all-files
   ```

6. **Commit the new `pixi.lock` once,** then verify subsequent `pixi install`
   runs produce zero diff:

   ```bash
   pixi install
   git add pixi.toml pixi.lock
   git commit -S -m "fix(tooling): stop pixi.lock churn from self-reference + hatch-vcs"
   pixi install && git diff --exit-code pixi.lock   # must exit 0
   ```

7. **Do NOT try `[pypi-options] no-build-isolation = true`** as a fix —
   see Failed Attempts.

## Approach B — Permanent Fix: Migrate to Lockfile v7

Use when you are ready to coordinate a Pixi version bump across CI. This is the more durable fix because it eliminates the churn at the FORMAT level — lockfile v7 removes the source-dependency input hashes that cause the perpetual rewrite.

**Prerequisite:** Pixi >=0.68.0 (this session verified with 0.69.0).

### Quick Reference

```bash
# 1. Upgrade local Pixi to >=0.68.0, then run:
pixi lock
# Pixi prints: "the lock file is up-to-date but uses an older format (v6),
# re-solving all environments using locked content to upgrade to v7"

# 2. Verify the reflow is a pure format upgrade (no dependency drift):
git show HEAD:pixi.lock | grep -oE "(conda|pypi): [^ ]+" | sort -u > /tmp/old_pkgs.txt
grep -oE "(conda|pypi): [^ ]+" pixi.lock | sort -u > /tmp/new_pkgs.txt
diff /tmp/old_pkgs.txt /tmp/new_pkgs.txt   # must be empty

# 3. Add requires-pixi floor to pixi.toml [workspace]:
pixi workspace requires-pixi set ">=0.69.0"
# Or manually: add `requires-pixi = ">=0.69.0"` under [workspace] in pixi.toml

# 4. Bump ALL pixi-version pins in CI — grep the WHOLE .github/ tree:
grep -rn "pixi-version" .github/
# THIS MUST INCLUDE .github/actions/*/action.yml composite actions, not just workflows!

# 5. Commit and push as a single PR; CI must use >=0.69.0 to read the v7 lock.
```

### Detailed Steps

1. **Upgrade local Pixi** to >=0.68.0. Check version: `pixi --version`.

2. **Run `pixi lock`** (or `pixi install`). Pixi will detect the v6 format and print
   the upgrade message, then rewrite `pixi.lock` in v7 format.

3. **Verify the diff is a pure format upgrade.** The v7 reflow touches roughly half
   the lines (field reordering, new top-level `platforms:` block). Do NOT judge by
   line count — judge by the resolved package URL/hash SET:

   ```bash
   git show HEAD:pixi.lock | grep -oE "(conda|pypi): [^ ]+" | sort -u > /tmp/old.txt
   grep -oE "(conda|pypi): [^ ]+" pixi.lock | sort -u > /tmp/new.txt
   diff /tmp/old.txt /tmp/new.txt   # must be empty — zero dependency drift
   ```

4. **Add `requires-pixi = ">=0.69.0"` to `[workspace]`** in `pixi.toml`. This field
   is NOT a `version` field; the `check-version-single-source` pre-commit hook (which
   greps `^\s*version\s*=` under `[workspace]`) does NOT flag it. It gives any
   consumer running an older Pixi a clear error message instead of a confusing
   v7-unreadable failure.

   ```toml
   [workspace]
   requires-pixi = ">=0.69.0"
   # ... other fields ...
   ```

5. **Bump ALL Pixi version pins in CI.** This is critical — a v7 lockfile is
   UNREADABLE by older Pixi. Grep the ENTIRE `.github/` tree:

   ```bash
   grep -rn "pixi-version" .github/
   ```

   **CRITICAL:** This must include `.github/actions/*/action.yml` composite actions,
   not just `.github/workflows/*.yml`. Missing even one pin will cause CI failures
   of the form `workspace requires pixi '>=0.69.0', but I am 0.63.2`.

6. **Land as a single coordinated PR** that includes the v7 lockfile, the
   `requires-pixi` floor, and ALL updated CI pins together.

### Why v7 is More Durable

Lockfile v6 includes input hashes for source (path/editable) dependencies so pixi can
detect manifest changes. With `hatch-vcs`, the "version" part of those inputs resolves
differently on each invocation, so the hash always changes. Lockfile v7 removes these
source-dependency input hashes entirely, making the format immune to this class of
churn regardless of the build backend.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Keep the self-package entry in `[pypi-dependencies]` and add `[pypi-options] no-build-isolation = true` | CI (pixi v0.63.2) failed with `BackendUnavailable: Cannot import 'hatchling.build'` — pip's PEP 517 build subprocess could not see hatchling installed in the parent pixi env | `no-build-isolation` requires the build backend to be visible to the pip subprocess; pixi's environment isolation breaks that visibility. Don't reach for this flag to mask the self-reference problem |
| 2 | `git checkout -- pixi.lock` on a clean tree to undo the churn | A pre-commit/safety hook blocked the raw checkout | Manual `git checkout` of generated files isn't a reliable workaround when safety hooks are active — eliminate the source of churn rather than papering over it |
| 3 | Bumped only the 8 `setup-pixi` pins in `.github/workflows/` before adding `requires-pixi = ">=0.69.0"` | CI lint/unit-tests still failed: `workspace requires pixi '>=0.69.0', but I am 0.63.2` — a 9th pin was hardcoded in `.github/actions/setup-pixi-env/action.yml` composite action | Grep all of `.github/`, not just `.github/workflows/`. Composite actions are a separate, easily-missed location. The `requires-pixi` floor is what surfaced the missed pin — it turned a silent version mismatch into a loud, located error |
| 4 | Judged the v6→v7 lock diff by line count (~1200 lines changed) as "large/risky" | The diff looked like a large dependency change but was actually a pure format reflow (field reordering, new `platforms:` block) | Judge lockfile diffs by the resolved package URL/hash SET, not by line count. A format reflow can touch half the file while changing zero actual dependencies |
| 5 | Relied on the issue's stated "8 pins across 5 workflows" pin count | Undercounted: missed the composite action and miscounted per-file | Always re-derive counts from the live tree with `grep -rn "pixi-version" .github/` — don't trust documentation or issue descriptions for infrastructure counts |

## Results & Parameters

### Final `pixi.toml` Snippet (Approach B)

```toml
[workspace]
requires-pixi = ">=0.69.0"
# ... channels, platforms, etc. ...

# No self-reference under [pypi-dependencies] (either removed per Approach A,
# or churn is now prevented by the v7 lockfile format).
```

### Final CI Snippet (Approach B)

```yaml
- uses: prefix-dev/setup-pixi@v0.8.1
  with:
    pixi-version: v0.69.0   # must match requires-pixi floor; bump in ALL locations
```

**Locations to update:** `.github/workflows/*.yml` AND `.github/actions/*/action.yml`.

### CI / Pre-commit Invocation Order (Approach A)

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0          # hatch-vcs needs full history for git tags
  - uses: prefix-dev/setup-pixi@v0.8.1
  - run: pixi install --environment default
  - run: pixi run dev-install
  - run: pixi run pre-commit run --all-files
```

### Expected Output

- `pixi install` on a clean tree produces zero diff in `pixi.lock`.
- `pre-commit run --all-files` does not flag `pixi.lock`.
- `python -c "import mypackage; print(mypackage.__version__)"` returns the
  git-tag-derived version after `pixi run dev-install`.
- `pip show mypackage` lists the package as editable, installed from the
  repo path.

### Decision Matrix

| Symptom | Self-ref in `[pypi-dependencies]`? | `hatch-vcs` dynamic version? | Apply this skill? |
| --- | --- | --- | --- |
| `pixi.lock` churn on clean tree | yes | yes | **Yes** |
| `pixi.lock` churn on clean tree | yes | no | Partial — removing self-ref alone often suffices |
| `pixi.lock` churn on clean tree | no | yes | No — see `lockfile-and-release-pipeline-management` |
| `pixi.lock` drift vs `main` only | n/a | n/a | No — see `lockfile-and-release-pipeline-management` (section A) |

### Approach Selection

| Factor | Choose Approach A | Choose Approach B |
| --- | --- | --- |
| Speed to land | Faster (no ecosystem coordination) | Requires coordinated CI bump |
| Durability | Localized — other projects can still churn | Permanent — format-level fix |
| Ecosystem readiness | Pixi >=0.68.0 not yet adopted broadly | Pixi >=0.68.0 available everywhere |
| Risk | Low (narrow change) | Low if all pins are updated together |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | PRs #457, #526, #530, #532 (Approach A, merged 2026-05) | Removed `homericintelligence-hephaestus = { path = ".", editable = true }` from `[pypi-dependencies]`, added `dev-install` task, updated pre-commit workflow; CI green; `pixi.lock` stable across invocations |
| ProjectHephaestus | PR #675 (Approach B, Closes #455, merged 2026-05-28) | Migrated `pixi.lock` to v7 format using Pixi 0.69.0; added `requires-pixi = ">=0.69.0"` to `[workspace]`; bumped all `pixi-version` pins in `.github/workflows/` AND `.github/actions/setup-pixi-env/action.yml`; all Required Checks passed (lint, pixi-check, integration-tests, unit-tests, build, pr-policy, security); local `pixi install` from v7 lock shows zero churn; full unit suite 2771 passed / 2 skipped |

## References

- [lockfile-and-release-pipeline-management](lockfile-and-release-pipeline-management.md) — general lockfile drift recovery (different failure mode)
- [hatch-vcs-pyproject-auto-versioning-setup](hatch-vcs-pyproject-auto-versioning-setup.md) — initial hatch-vcs migration
- [pixi-cache-true-unreliable](pixi-cache-true-unreliable.md) — related pixi CI caveat
- [Pixi PyPI options docs](https://pixi.sh/latest/reference/project_configuration/#the-pypi-options-table)
- [hatch-vcs docs](https://github.com/ofek/hatch-vcs)
- [Pixi lockfile v7 changelog](https://github.com/prefix-dev/pixi/releases/tag/v0.68.0)
