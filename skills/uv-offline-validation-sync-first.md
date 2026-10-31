---
name: uv-offline-validation-sync-first
license: BSD-3-Clause
description: "Synchronize a uv project environment before running validation, and keep it intact. Use when: (1) `uv run --offline` still tries to synchronize a locked environment, (2) a missing locked wheel blocks offline tests, (3) `--no-sync` may select the wrong pytest executable, (4) a later `uv run` removes extras that an earlier `uv sync --extra` installed, or (5) a plain `uv run <tool>` resolves a host-installed tool because the project keeps that tool only in an extra."
category: tooling
date: 2026-08-05
version: "1.3.0"
user-invocable: false
verification: verified-local
tags:
  - uv
  - offline
  - validation
  - sync
  - extras
  - pytest
  - ruff
  - ty
  - python-environment
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/uv-offline-validation-sync-first.history"
history-cleanup-date: "2026-09-20"
---

# uv Offline Validation: Synchronize Before Running

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-08-05; amended 2026-10-31 |
| **Objective** | Run Python validation against the intended project environment, whether or not network access is available. |
| **Outcome** | A completed `uv sync` makes focused tests and static checks runnable offline; `--no-sync` on the follow-up command keeps that environment, including its extras, unchanged. |
| **Verification** | verified-local |

## When to Use

- `uv run --offline` reports that it needs to install or synchronize a locked dependency.
- A locked wheel such as `grpcio` is absent from the local cache and network access is deliberately disabled.
- `uv run --offline --no-sync` completes unexpectedly, but its test runner may be from the system environment rather than the project environment.
- A command run after `uv sync --extra <name>` fails with a missing module, or a tool that was installed is no longer found.
- A plain `uv run <tool>` reports a successful build and install of the project, then fails with a `ModuleNotFoundError` for the project package itself. The project keeps that tool only in an extra, so uv synchronized the default dependencies and resolved a host-installed tool from `PATH`.
- You need a defensible local validation report that distinguishes focused checks from an uncompleted full suite.

## Verified Workflow

Verified locally only — CI validation pending. `--offline` prevents network access, but it does not by itself prevent uv from synchronizing an environment.

### Quick Reference

```bash
# Bootstrap the project environment while dependencies are available.
uv sync --extra dev

# Thereafter, run project tools without network access.
uv run --offline pytest <focused-test-path> -q
uv run --offline ruff check .
uv run --offline ruff format --check .
uv run --offline ty check

# If diagnosis requires --no-sync, prove the executable still belongs to .venv.
uv run --offline --no-sync python -c 'import sys; print(sys.executable)'
uv run --offline --no-sync python -m pytest --version

# No pre-synchronized environment, and the tool lives only in an extra:
# request the extra on the run itself.
uv run --locked --extra dev pytest <focused-test-path> -q

# After a deliberate sync with every needed extra, keep that environment.
uv run --no-sync pytest <focused-test-path> -q

# A helper that needs only its own extra should not remove other packages.
uv sync --extra <helper-extra> --inexact
```

### Detailed Steps

1. Use the intended project environment. When network access is authorized, a repository with tools in a `dev` extra can prepare it with `uv sync --extra dev`. Offline, use available cached artifacts and report missing dependencies while continuing useful independent work.
2. If `uv run --offline` fails before the requested command starts, inspect the synchronization error. A missing lockfile artifact means the environment was not fully materialized; offline mode cannot download the missing wheel.
3. Decide whether `--no-sync` applies by environment state. When the project environment is absent or incomplete, `--no-sync` suppresses synchronization and the command can resolve a global `pytest` or another incompatible interpreter. When the environment is already complete and was deliberately synchronized with the extras the later commands need, `--no-sync` is correct, because without it `uv run` synchronizes toward the default extra set and removes those extras again.
4. Confirm the environment before trusting results. Run Python through uv and print `sys.executable`; then invoke `python -m pytest --version`. Both must resolve to the expected project environment. This check is what separates the two cases in step 3.
5. When no environment was synchronized before, request the extra on the run itself instead of relying on lookup. A tool that the project declares only in an extra is not installed by a plain `uv run <tool>`: uv synchronizes the default dependencies (and can report a successful project build), skips the tool, and resolves a host-installed executable of the same name from `PATH`. That host executable runs against the host interpreter, so the failure appears inside the project suite as a `ModuleNotFoundError` for the project package, for example at `conftest` import. Pass the extra directly: `uv run --locked --extra dev pytest <focused-test-path> -q`. Evidence: this wrong-executable selection reproduced deterministically on a second identical run.
6. After a successful sync, run the relevant checks with `--offline`. Focused tests, Ruff, and Ty are examples; select tools that the repository actually uses.
7. When a helper script, task runner, or continuous-integration job runs its own `uv sync`, consider `--inexact`. An exact sync removes packages that another command installed, including test and lint tools, so the helper can leave the repository unable to validate.
8. In continuous integration, install the extras that the later steps need, then use `--no-sync` for each following `uv run`. Give a test step the extras it imports, not only the extras a build step needs.
9. Report collection and execution separately. A successful collection count is not a full-suite success unless the run returns a final passing result.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Offline run before environment bootstrap | Ran `uv run --offline` while a locked dependency wheel was unavailable locally. | uv still needed to synchronize the lock and could not obtain the absent artifact without network access. | `--offline` prohibits downloads; it does not replace a completed `uv sync`. |
| Bypass sync with `--no-sync` | Used `uv run --offline --no-sync` before confirming the project environment existed. | The command can fall back to a system `pytest` that has different Python or dependency versions. | Verify `sys.executable` and use `python -m pytest` before accepting results. |
| Treat collection as suite success | Collected the repository test suite, then waited for a full result that did not reliably return. | Collection proved discovery only, not passing execution. | State the collected count and leave full-suite status unconfirmed. |
| Plain `uv run` for a tool declared only in an extra | Ran `uv run pytest` with no extra flags on a project whose pytest sits in a `dev` extra, with no pre-synchronized environment. | uv synchronized the default dependencies and reported a successful project build, but pytest was never installed; uv resolved a host `pytest` from `PATH`, and its interpreter failed at `conftest` import with `ModuleNotFoundError: No module named <project package>`. The failure reproduced deterministically on re-run. | Request the extra on the run itself: `uv run --locked --extra dev pytest <path> -q`. The extra on `uv run` selects the project interpreter. A successful project build report does not prove that the requested tool came from the project environment. |
| Plain `uv run` after installing extras | Synchronized with an extra, then ran a test command without `--no-sync`. | `uv run` synchronized toward the default extra set and removed the extra, so the suite failed to import a declared base dependency. | `uv run` does not inherit earlier extras; add `--no-sync` after a deliberate sync. |
| Exact `uv sync` inside a build helper | Ran an exact sync for one extra inside a local build script. | The sync removed the test and lint packages that another command had installed. | Use `--inexact` for a helper that only needs to add its own extra. |

## Results & Parameters

| Parameter | Observed result |
| --- | --- |
| Project setup | `uv sync --extra dev` was required before offline validation was reliable. |
| Focused CLI tests | 41 tests passed locally. |
| Static checks | Ruff check, Ruff format check, and Ty passed locally. |
| Full-suite collection | 831 tests were collected. |
| Full-suite execution | No reliable final result returned; do not report it as passing. |
| Follow-up invocation | `uv run --no-sync` kept the synchronized extras; a plain `uv run` removed them. |
| Tool declared only in an extra | `uv run --locked --extra dev pytest <path> -q` selected the project interpreter and ran the tests; plain `uv run pytest` resolved a host `pytest` and failed at `conftest` import. |
| Helper-script sync | `--inexact` left unrelated installed packages in place. |
| Network and cluster scope | No cluster commands were run. |

## Verified On

| Context | Details |
| --- | --- |
| Local CLI review and validation | Used a development extra, a local environment, and offline runs only. |
| Local desktop application build | Confirmed the extra-stripping and `--inexact` behavior while adding a multi-platform build and release pipeline. See [notes](uv-offline-validation-sync-first.notes.md). |
| Local delegated test run on a fresh checkout | Confirmed the host-tool fallback and the extra-on-the-run remedy for a tool declared only in an extra. See [notes](uv-offline-validation-sync-first.notes.md). |
