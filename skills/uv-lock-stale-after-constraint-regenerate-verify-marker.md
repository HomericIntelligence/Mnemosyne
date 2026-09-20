---
name: uv-lock-stale-after-constraint-regenerate-verify-marker
license: BSD-3-Clause
description: "Regenerate a stale uv lock after dependency constraints or platform markers change; inspect branch drift, normalized metadata, and the actual freshness check."
category: ci-cd
date: 2026-07-17
version: "1.1.1"
user-invocable: false
verification: verified-local
tags:
  - uv
  - uv-lock
  - lockfile
  - lock-freshness
  - uv-lock-check
  - pyproject
  - dependency-constraint
  - version-specifier
  - requires-dist
  - environment-marker
  - platform_system
  - sys_platform
  - tzdata
  - windows-only
  - branch-drift
  - regenerate
  - nogo
  - pep508
  - pre-commit
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/ed1bd4f54fd4aaba446af92c8b3ab9aff2589ae3/skills/uv-lock-stale-after-constraint-regenerate-verify-marker.history"
history-cleanup-date: "2026-09-20"
---

# uv.lock Stale After a Constraint Change: Regenerate and Verify the Lock Signals

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-17 |
| **Objective** | Fix a deterministic lock-freshness NOGO where `pyproject.toml` gained/changed a dependency constraint (a version specifier on a Windows-only `tzdata` entry) but `uv.lock` was not regenerated, and verify the fix with concrete lock-file signals rather than "looks right". |
| **Outcome** | Root cause was branch drift, not a source bug: the stale PR branch was 27 commits behind `main`, and its committed `uv.lock` did not reflect the `pyproject.toml` specifier. `main` already carried both the constraint and a fresh lock (`uv lock --check` exit 0, "Resolved 88 packages"). For a new remediation task, pin a branch to current `main`, regenerate `uv.lock`, then assert the specifier landed in `requires-dist` and the marker normalized to `sys_platform == 'win32'`. |
| **Verification** | verified-local — `uv lock --check` reproduced the fresh/stale distinction; marker normalization and `requires-dist` specifier confirmed by inspecting `uv.lock`. CI GO on the successor PR is a separate gated step. |

## When to Use

- A `pyproject.toml` dependency line gained a version specifier or a platform/environment marker (e.g. `"tzdata; platform_system == 'Windows'"` → `"tzdata>=2026.2,<2027; platform_system == 'Windows'"`) and `uv.lock` was committed **without regeneration**.
- CI / a plan review issues a **deterministic NOGO for a stale lockfile**, or the `uv-pre-commit` `uv-lock --check` hook (the read-only freshness gate, `args: [--check]`) fails locally.
- You need to prove the lock now matches metadata by **specific signals**, not by eyeballing the diff.
- An active task needs a constraint and fresh lock from `main`, or a new remediation task needs a fresh main pin for regeneration.
- You are tempted to hand-edit `uv.lock` (never do this — it is resolver-owned output).

## Root Cause (the non-obvious part)

A stale lock NOGO after a constraint change is usually **branch drift**, not a code defect. Verify before "fixing":

```bash
# Is the constraint + a fresh lock ALREADY on main?
git show main:pyproject.toml | grep -n <package>
git rev-list --left-right --count origin/main...origin/<pr-branch>   # e.g. 27  2  → branch is 27 behind
```

If `main` already has the constraint and `uv lock --check` on `main` returns exit 0, the defect is scoped to the drifted branch. Do not rebase it solely because it is old. An active task can rebase only when it needs that main content to continue. For a new remediation task, pin a fresh branch to `main`; this is cleaner than resolving a generated-lock merge conflict on the drifted branch. For a completed PR without a reported conflict, let CI/CD integrate with main.

## uv Marker Normalization (verify, don't assume)

uv rewrites PEP 508 markers into its own canonical form in `uv.lock`. `platform_system == 'Windows'` (the form you write in `pyproject.toml`) is stored as **`sys_platform == 'win32'`** in the lock. This is not a bug and not "wrong scope" — it is uv's normalization, and it is what the freshness check enforces. Corroborate against another Windows-only dep already in the tree (e.g. `colorama` shows the same `sys_platform == 'win32'` in `uv.lock`) so a reviewer expecting the literal `platform_system == 'Windows'` in the lock does not raise a false finding.

## Verified Workflow

1. **Diagnose drift before editing.** Confirm whether `main` already carries the constraint + a fresh lock:

   ```bash
   git fetch origin
   git show main:pyproject.toml | grep -n <package>
   uv lock --check        # on main: expect "Resolved N packages", exit 0
   ```

2. **Choose the branch for the task.** A new remediation task can start from current
   `main` to avoid the old branch's generated-lock conflict. For an existing task, rebase
   when required dependency content, a reported conflict, or an explicit request calls
   for it; preserve the task's intended work:

   ```bash
   git checkout -b <issue>-regenerate-uv-lock origin/main
   ```

3. **Ensure the constraint is present** in `pyproject.toml` (re-apply it if you started from a `main` that predates it):

   ```bash
   grep -n <package> pyproject.toml
   # e.g. "tzdata>=2026.2,<2027; platform_system == 'Windows'"
   ```

4. **Regenerate the lock with the plain resolver** — not `--upgrade`, which gratuitously churns unrelated packages. `uv lock` re-resolves only the declared metadata change:

   ```bash
   uv lock
   ```

   Use `uv lock --upgrade-package <name>` / `uv lock --upgrade` ONLY for a deliberate version bump, never as the default refresh.

5. **Assert the two concrete lock signals** — this is the acceptance evidence:

   ```bash
   grep -n '<package>' uv.lock
   ```

   - Dependency-graph entries carry the normalized marker: `{ name = "<pkg>", marker = "sys_platform == 'win32'" }`.
   - The `[package.metadata] requires-dist` entry carries the specifier from `pyproject.toml`:
     `{ name = "<pkg>", marker = "sys_platform == 'win32'", specifier = ">=2026.2,<2027" }`.

6. **Run the freshness gate** exactly as CI does (read-only, must exit 0):

   ```bash
   uv lock --check                       # "Resolved N packages", exit 0
   uv run pre-commit run uv-lock --all-files   # CI-parity: astral-sh/uv-pre-commit uv-lock --check
   ```

7. **Deliver a consistent manifest and lock.** When publication is requested, follow the repository signing and DCO policy. Keep the delivered revision internally consistent; publication is not a prerequisite to a local repair.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Hand-edit `uv.lock` | Added a specifier or changed a marker in resolver output | The edit could differ from `uv lock` output, and `uv lock --check` could fail locally or in CI | Regenerate the lock file |
| Use `uv lock --upgrade` for a routine refresh | Upgraded all packages for a declared-metadata change | The command produced a large unrelated diff and risked untested versions | Use plain `uv lock` for a declared-metadata change |
| Hand-merge a lock conflict on a branch far behind `main` | Rebasing required manual selection of generated lock content | An `--ours` or `--theirs` choice could corrupt resolver output | Start a new branch from `main` and run `uv lock` |
| Treat the normalized marker as a scope defect | Expected `platform_system == 'Windows'` in the lock instead of `sys_platform == 'win32'` | `uv` normalizes the marker representation | Validate marker meaning instead of requiring the source literal |

## Results & Parameters

**Evidence (verified-local):**

- `git rev-list --left-right --count origin/main...origin/<pr-branch>` → `27  2` (branch drift is the root cause).
- `uv lock --check` on `main`: `Resolved 88 packages`, exit 0 (main's lock was already fresh).
- `grep -n tzdata uv.lock` on the fresh lock: dependency entries `marker = "sys_platform == 'win32'"`; `requires-dist` entry carries the specifier.
- CI GO on the successor PR is produced by the head-bound strict-review gate on the PR head — a separate, externally-authored gated step; do not hand-assert it.

**Copy-ready parameters:**

```bash
git fetch origin
git rev-list --left-right --count origin/main...origin/<pr-branch>
git show main:pyproject.toml | grep -n <package>
git checkout -b <issue>-regenerate-uv-lock origin/main
uv lock                                   # plain re-resolve; NOT --upgrade
grep -n '<package>' uv.lock               # expect sys_platform == 'win32' + specifier in requires-dist
uv lock --check                           # read-only freshness gate; exit 0
uv run pre-commit run uv-lock --all-files # CI-parity hook run
```

## Related

- [[dependabot-lockfile-rebase-regenerate-resign]] — rebasing a *bot* dep-bump PR whose lock+manifest went DIRTY (conflict + re-sign); this entry is the fresh-branch regeneration path for a stale (not conflicting) lock.
- [[python-sca-pip-audit-update-transitive-lock]] — regenerate a lock to clear a *transitive CVE* (`uv lock --upgrade-package`); different trigger (security) but same "regenerate, never weaken/hand-edit" principle.
- [[ci-cd-pixi-lock-version-skew-regeneration]] — the pixi analogue where the lock *format version* skews with the writer binary.
- [[dependency-manifest-single-source-of-truth]] — keeping declared constraints aligned across manifests (the upstream cause of many lock refreshes).
- [[lockfile-and-release-pipeline-management]] — broad lock-drift recovery across pixi/cargo/npm; this entry is the uv-specific constraint-change + marker-verification case.
