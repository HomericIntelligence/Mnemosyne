---
name: python-sca-pip-audit-update-transitive-lock
description: "Resolve GitHub Actions Python SCA / security-dependency-scan pip-audit failures caused by vulnerable transitive dependencies in a uv.lock OR pixi.lock file, including stale-lock propagation across sibling PRs after a red-main dep-fix merges. Use when: (1) python-sca or pip-audit fails with only a summary in the job log, (2) the failing package is transitive through a dev tool, (3) uv --locked reproduction needs cache paths redirected in a restricted sandbox, (4) a red-main dependency fix merged but sibling PRs branched before it still fail pip-audit on the OLD vulnerable lock (a plain rebase does not regenerate the lock), (5) a pixi.lock at format v7 fails CI's older pinned pixi with 'Lock-file version 7 is newer than supported'."
category: ci-cd
date: 2026-06-28
version: "1.1.0"
user-invocable: false
verification: verified-ci
history: python-sca-pip-audit-update-transitive-lock.history
tags:
  - github-actions
  - python-sca
  - security-dependency-scan
  - pip-audit
  - uv
  - uv-lock
  - pixi-lock
  - pixi-update
  - lockfile
  - lockfile-propagation
  - lock-format-v7
  - ci-pixi-version
  - dependency-scanning
  - transitive-dependency
  - cachecontrol
  - msgpack
  - pydantic-settings
---

# Python SCA Pip-Audit Transitive Lockfile Remediation

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-19 |
| **Objective** | Resolve GitHub Actions Python SCA failures from a vulnerable transitive dev dependency in a locked uv environment without weakening or bypassing pip-audit. |
| **Outcome** | Downloaded the pip-audit artifact, identified the exact advisory and fixed version, traced the vulnerable package through dev dependency metadata, refreshed only the affected package in `uv.lock`, reran the CI-equivalent audit with redirected caches, and confirmed GitHub checks passed. v1.1.0 generalizes the same principle to `pixi.lock`: targeted lock regeneration to clear a transitive CVE, plus two fleet-scale dimensions — propagating a lock fix to sibling PRs and unblocking a v7-lock-vs-old-CI-pixi read failure. |
| **Verification** | verified-ci |

> **Same principle, two lock formats.** The core idea — *clear a transitive CVE by regenerating the lock to pick up the patched version, never by weakening pip-audit* — applies identically to **uv.lock** and **pixi.lock**. The original workflow below is uv-centric; the **Pixi Lock Dimensions** section generalizes it to pixi (`pixi update <pkg>` is the pixi analogue of `uv lock --upgrade-package <pkg>`), and adds two fleet-scale failure modes seen across HomericIntelligence repos.

## When to Use

- A GitHub Actions `python-sca` or pip-audit job fails with a terse log such as `Found 1 known vulnerability in 1 package`.
- The workflow uploads a `pip-audit-report` artifact and the job log does not print the full JSON details.
- The vulnerable package is not declared directly in `pyproject.toml`, but comes from a dev tool such as `pip-audit`.
- A uv-managed project uses `uv run --locked --extra dev ...` in CI and needs a minimal lockfile remediation.
- Local reproduction fails in a restricted sandbox because pip-audit or uv tries to write caches under a read-only home directory.
- **(pixi)** A `pixi`-managed project's required `security/dependency-scan` (pip-audit) fails on a vulnerable transitive pin in `pixi.lock` and needs a minimal targeted bump.
- **(propagation)** A red `main` was fixed by a dependency-bump PR that regenerated the lock, and after merging it, every OTHER open PR branched before the fix still fails `security/dependency-scan` because it carries the OLD vulnerable lock — a plain `git rebase onto main` does NOT regenerate the lock.
- **(v7 read block)** A PR ships a `pixi.lock` at format v7 and the ENTIRE pipeline fails at `pixi install` with `× Lock-file version 7 is newer than supported … Maximum supported version: 6 (pixi v0.67.2)` because CI pins an older pixi that cannot read v7.

## Verified Workflow

### Quick Reference

```bash
# 1. Pull the failing job log.
gh run view <run-id> --job <job-id> --log

# 2. Download the pip-audit artifact; the log may contain only the summary.
gh run download <run-id> -n pip-audit-report -D /tmp/<audit-dir>
python3 -m json.tool /tmp/<audit-dir>/pip-audit.json

# 3. Reproduce with the exact CI command, redirecting caches if home is restricted.
env UV_CACHE_DIR=/tmp/<case>-uv-cache XDG_CACHE_HOME=/tmp/<case>-xdg-cache \
  uv run --locked --extra dev python -m pip_audit \
  --local --format=json --output=/tmp/<case>-pip-audit-before.json

# 4. Trace whether the vulnerable package is transitive.
env UV_CACHE_DIR=/tmp/<case>-uv-cache XDG_CACHE_HOME=/tmp/<case>-xdg-cache \
  uv run --locked --extra dev python -m pip show <vulnerable-package> <parent-package> pip-audit

# 5. Refresh only the vulnerable package in uv.lock.
env UV_CACHE_DIR=/tmp/<case>-uv-cache XDG_CACHE_HOME=/tmp/<case>-xdg-cache \
  uv lock --upgrade-package <vulnerable-package>

# 6. Re-run the CI-equivalent audit and confirm it is clean.
env UV_CACHE_DIR=/tmp/<case>-uv-cache XDG_CACHE_HOME=/tmp/<case>-xdg-cache \
  uv run --locked --extra dev python -m pip_audit \
  --local --format=json --output=/tmp/<case>-pip-audit-fixed.json

git diff -- uv.lock
```

### Detailed Steps

1. **Inspect the failing SCA job log first.** Use `gh run view <run-id> --job <job-id> --log`. If the workflow is still running, wait until the log and artifacts are available before editing. The log may only show the pip-audit summary, not the vulnerable package details.

2. **Download and inspect the uploaded audit artifact.** Use `gh run download <run-id> -n pip-audit-report -D /tmp/<audit-dir>` and read `pip-audit.json`. The artifact is the source of truth for package name, installed version, advisory ID, and fixed version.

3. **Reproduce locally with the exact CI command.** Match the workflow invocation instead of improvising flags. For uv projects, that may be `uv run --locked --extra dev python -m pip_audit --local --format=json --output=...`. In restricted environments, redirect both `UV_CACHE_DIR` and `XDG_CACHE_HOME` to `/tmp` so pip-audit does not fail writing to a read-only home cache.

4. **Trace the transitive source before changing dependencies.** If the package is not direct, inspect installed metadata with `pip show`. The important fields are `Required-by` on the vulnerable package and on its parent package. This distinguishes a project runtime dependency from a dev-tool dependency.

5. **Prefer a targeted lock refresh when a fixed release exists.** Use `uv lock --upgrade-package <vulnerable-package>` rather than broad resolver churn. Review `git diff -- uv.lock` and confirm only the intended package/version changed.

6. **Re-run the CI-equivalent pip-audit command.** The expected terminal result is `No known vulnerabilities found`. Inspect the output JSON as well; the fixed package should show the remediated version and no vulnerabilities.

7. **Run affected tests or static checks, commit only the lockfile if that is the only change, push, and confirm GitHub SCA passes.** Do not merge based on local output alone if the required CI job is the gate.

## Pixi Lock Dimensions (v1.1.0)

Everything above maps to pixi: the `pixi.lock` analogue of `uv lock --upgrade-package <pkg>` is `pixi update <pkg>` (a minimal targeted bump). The pip-audit advisory table goes to `$GITHUB_STEP_SUMMARY`, **not stdout** — reproduce locally to see `Found N known vulnerability… <pkg> <ver> <GHSA> <fixed-ver>`. Two fleet-scale failure modes seen this session:

### Dimension 1 — Stale-lock-after-main-fix propagation (the fleet dimension)

When a red `main` is fixed by a dependency-bump PR that adds/raises a constraint **and regenerates the lock**, merging that fix unblocks `main` — but every OTHER open PR branched before it still carries the OLD vulnerable lock and keeps failing the required `security/dependency-scan` (pip-audit). **A plain `git rebase onto main` does NOT regenerate the lock**, so the vulnerable pin persists. The fix, per PR, is to REGENERATE the lock so it picks up the patched version. There are two sub-cases:

- **Constraint already allows the patched version** (e.g. `pydantic-settings >=2.0`, but the lock pins `2.13.1` which has `GHSA-4xgf-cpjx-pc3j`). A plain `pixi lock` re-solves with locked content and does **NOT** bump — you must run `pixi update <package>` (e.g. `pixi update pydantic-settings` → `2.14.2`) for a minimal targeted bump.
- **Fix added an explicit pin in `pixi.toml`** (e.g. an explicit `msgpack >= 1.2.1` for `GHSA-6v7p-g79w-8964`, transitive via `cachecontrol`). Here, rebasing onto the fixed `main` brings the pin in, and a `pixi install` / `pixi lock` re-solve picks it up. (Even so, confirm the lock actually changed — a no-op rebase leaves the old pin.)

**Batch this as one lock-regen sub-agent per repo** across the open PRs.

```bash
# Reproduce the advisory (table is in $GITHUB_STEP_SUMMARY, not stdout):
pixi run pip-audit            # or the repo's exact CI command; read "Found N known vulnerability…"

# Sub-case A — constraint already allows the patch: targeted bump (plain `pixi lock` will NOT bump):
pixi update pydantic-settings
grep -nE "name: *\"?pydantic-settings|pydantic-settings *[=@]" pixi.lock   # confirm 2.13.1 -> 2.14.2

# Sub-case B — fix added an explicit pin upstream on main: rebase brings the pin, then re-solve:
git rebase origin/main
pixi install                  # or `pixi lock`
grep -nE "name: *\"?msgpack|msgpack *[=@]" pixi.lock        # confirm 1.1.2 -> 1.2.1

git diff -- pixi.lock         # verify ONLY the intended package/version changed
```

### Dimension 2 — Pixi lock-format v7 that CI's pinned pixi cannot read (a hard CI-read block)

A PR shipping a `pixi.lock` at **format v7** fails the **ENTIRE** pipeline (every job, at `pixi install`) when the repo's CI pins an older pixi that can't read v7:

```text
× Lock-file version 7 is newer than supported … Maximum supported version: 6 (pixi v0.67.2)
```

This is **NOT** the v6/v7 churn issue (see `tooling-pixi-lockfile-churn-self-reference`) — it's a *read incompatibility* that bricks all checks. **FIX: bump the CI `pixi-version` in the workflows** (e.g. `v0.67.2` → `v0.70.2`) to a pixi that reads v7.

Verify the bump is **SAFE on main first**: a newer pixi reads OLDER v6 locks fine — `pixi install --locked` against a v6 lock exits `0` (warn-only, does NOT rewrite), so the bump won't red a v6 `main`. Ecosystem precedent: a sibling repo already ran `v0.70.2` with v7 locks.

```bash
# Find every pin (workflows AND composite actions — see the churn skill's gotcha):
grep -rn "pixi-version" .github/

# Safety check on main BEFORE bumping: newer pixi reads a v6 lock without rewriting it:
pixi install --locked        # against a v6 lock: exits 0, warn-only, no rewrite

# Bump the pin (example): v0.67.2 -> v0.70.2 in all matched locations.
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Weaken or bypass SCA | Considered treating the pip-audit failure as noise | The vulnerable package had a fixed release, so suppression would hide a real remediable advisory | Keep the SCA job fail-closed when a fixed version exists; update the lockfile instead |
| Rely on job log summary only | Read the log line `Found 1 known vulnerability in 1 package` | The log did not print the package, advisory, or fixed version details | Download the `pip-audit-report` artifact and inspect `pip-audit.json` |
| Assume the package is direct | Looked for the vulnerable package in project dependency declarations | The package was transitive through a dev tool and not declared by the project | Use `pip show` metadata to trace `Required-by` before changing manifests |
| Run pip-audit with default cache paths | Ran the CI-equivalent command in a restricted sandbox | pip-audit attempted to write under a read-only home cache and raised `OSError: [Errno 30] Read-only file system` | Redirect both `UV_CACHE_DIR` and `XDG_CACHE_HOME` to writable `/tmp` paths |
| Broad dependency refresh | Could have run a full uv lock update | Full resolver churn increases review risk and can change unrelated packages | Use `uv lock --upgrade-package <package>` for a minimal lockfile change |
| Plain `pixi lock` to clear a transitive CVE | Ran `pixi lock` expecting it to pick up the patched `pydantic-settings 2.14.2` | The constraint (`>=2.0`) already allowed the patch, so `pixi lock` re-solved with **locked content** and kept the vulnerable `2.13.1` pin | Use `pixi update <pkg>` (the pixi analogue of `uv lock --upgrade-package`) for a minimal targeted bump when the constraint already permits the fixed version |
| Plain rebase-onto-fixed-main to propagate a lock fix | Rebased a sibling PR onto a `main` whose dep-fix had merged, expecting the vulnerable lock to clear | `git rebase onto main` does NOT regenerate the lock; the old vulnerable pin persisted and `security/dependency-scan` kept failing | Explicitly regenerate the lock per PR — `pixi update <pkg>` (constraint allows patch) or rebase-then-`pixi install` when the fix added an explicit `pixi.toml` pin; always `git diff -- pixi.lock` to confirm it actually changed |
| Shipped a v7 `pixi.lock` against CI's older pinned pixi | Pushed a PR carrying a `pixi.lock` at format v7 while CI pinned `v0.67.2` | The WHOLE pipeline died at `pixi install` with `Lock-file version 7 is newer than supported … Maximum supported version: 6` — a read-incompatibility, not churn | Bump the CI `pixi-version` (e.g. `v0.67.2` → `v0.70.2`) across all `.github/` pins; verify safety first — a newer pixi reads v6 locks via `pixi install --locked` (exit 0, warn-only, no rewrite), so it won't red a v6 `main` |

## Results & Parameters

In the verified case, GitHub Actions `python-sca` ran:

```bash
uv run --locked --extra dev python -m pip_audit \
  --local --format=json --output=pip-audit.json
```

The artifact identified:

| Field | Value |
|-------|-------|
| Package | `msgpack` |
| Vulnerable version | `1.1.2` |
| Advisory | `GHSA-6v7p-g79w-8964` |
| Fixed version | `>=1.2.1` |
| Transitive source | `msgpack` required by `CacheControl`; `CacheControl` required by `pip-audit` |
| Minimal fix | `uv lock --upgrade-package msgpack` |
| Lockfile result | `msgpack` updated from `1.1.2` to `1.2.1` in `uv.lock` |

Restricted-sandbox reproduction and fix commands:

```bash
env UV_CACHE_DIR=/tmp/pr254-uv-cache XDG_CACHE_HOME=/tmp/pr254-xdg-cache \
  uv run --locked --extra dev python -m pip_audit \
  --local --format=json --output=/tmp/pr254-pip-audit-fixed.json

env UV_CACHE_DIR=/tmp/pr254-uv-cache XDG_CACHE_HOME=/tmp/pr254-xdg-cache \
  uv lock --upgrade-package msgpack
```

Expected post-fix audit result:

```text
No known vulnerabilities found
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Inference360 | PR #254, head `4086627`, 2026-06-19 | `python-sca`, `validate`, `sast`, `secrets`, and CodeQL passed after the targeted `uv.lock` update |
| Telemachy | 23 PRs (lock-propagation sweep), 2026-06-28 | `pydantic-settings 2.13.1 → 2.14.2` via `pixi update pydantic-settings` (constraint `>=2.0` already allowed the patch; plain `pixi lock` would not bump). Cleared `GHSA-4xgf-cpjx-pc3j` on `security/dependency-scan` across all sibling PRs after the red-main dep-fix merged |
| Telemachy | PR #288, 2026-06-28 | v7-lock read block: bumped CI `pixi-version` `v0.67.2 → v0.70.2` so the pinned pixi could read the v7 `pixi.lock`; verified safe on main (`pixi install --locked` against a v6 lock exits 0, warn-only, no rewrite); sibling-repo precedent already ran v0.70.2 with v7 locks |
| Agamemnon | 7 PRs (lock-propagation sweep), 2026-06-28 | `msgpack 1.1.2 → 1.2.1` (`GHSA-6v7p-g79w-8964`, transitive via `cachecontrol`) via rebase onto `main` after PR #434 added the explicit `msgpack >= 1.2.1` pin; `pixi install` re-solve picked it up; `security/dependency-scan` green across siblings |

## References

- [tooling-pixi-lockfile-churn-self-reference](tooling-pixi-lockfile-churn-self-reference.md) — the v6/v7 lockfile *churn / format* angle (distinct from the v7 *read-incompatibility* block documented here)
- [dependabot-lockfile-rebase-regenerate-resign](dependabot-lockfile-rebase-regenerate-resign.md) — rebase + lock-regenerate + re-sign mechanics for dependency PRs
- [automation-multi-repo-pr-sweep-rebase-resolve](automation-multi-repo-pr-sweep-rebase-resolve.md) — the multi-repo PR sweep harness for batching the per-repo lock-regen sub-agents
