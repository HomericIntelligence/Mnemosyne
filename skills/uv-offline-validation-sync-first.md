---
name: uv-offline-validation-sync-first
license: BSD-3-Clause
description: "Run Python project validation with uv when network access is unavailable. Use when: (1) `uv run --offline` still tries to synchronize a locked environment, (2) a missing locked wheel blocks offline tests, or (3) `--no-sync` may select the wrong pytest executable."
category: tooling
date: 2026-08-05
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - uv
  - offline
  - validation
  - sync
  - pytest
  - ruff
  - ty
  - python-environment
---

# uv Offline Validation: Synchronize Before Running

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-08-05 |
| **Objective** | Run focused Python validation locally without relying on network access or accidentally using system tooling. |
| **Outcome** | A `uv sync --extra dev` bootstrap made focused tests and static checks runnable offline; the full suite remained unconfirmed when its final result was unavailable. |
| **Verification** | verified-local |

## When to Use

- `uv run --offline` reports that it needs to install or synchronize a locked dependency.
- A locked wheel such as `grpcio` is absent from the local cache and network access is deliberately disabled.
- `uv run --offline --no-sync` completes unexpectedly, but its test runner may be from the system environment rather than the project environment.
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
```

### Detailed Steps

1. Start with the intended project extra, not an ad-hoc system install. For a repository that declares its test and lint tools in a `dev` extra, bootstrap it with `uv sync --extra dev`.
2. If `uv run --offline` fails before the requested command starts, inspect the synchronization error. A missing lockfile artifact means the environment was not fully materialized; offline mode cannot download the missing wheel.
3. Do not treat `--no-sync` as a fix. It suppresses synchronization, which can cause the command to resolve a global `pytest` or another incompatible interpreter when the project virtual environment is absent or incomplete.
4. When using `--no-sync` for diagnosis, run Python through uv and print `sys.executable`; then invoke `python -m pytest --version`. Confirm both resolve to the expected project environment before trusting results.
5. After a successful sync, rerun only the intended checks with `--offline`: focused tests first, then Ruff lint, Ruff format check, and Ty type checking.
6. Report collection and execution separately. A successful collection count is not a full-suite success unless the run returns a final passing result.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Offline run before environment bootstrap | Ran `uv run --offline` while a locked dependency wheel was unavailable locally. | uv still needed to synchronize the lock and could not obtain the absent artifact without network access. | `--offline` prohibits downloads; it does not replace a completed `uv sync`. |
| Bypass sync with `--no-sync` | Used `uv run --offline --no-sync` before confirming the project environment existed. | The command can fall back to a system `pytest` that has different Python or dependency versions. | Verify `sys.executable` and use `python -m pytest` before accepting results. |
| Treat collection as suite success | Collected the repository test suite, then waited for a full result that did not reliably return. | Collection proved discovery only, not passing execution. | State the collected count and leave full-suite status unconfirmed. |

## Results & Parameters

| Parameter | Observed result |
| --- | --- |
| Project setup | `uv sync --extra dev` was required before offline validation was reliable. |
| Focused CLI tests | 41 tests passed locally. |
| Static checks | Ruff check, Ruff format check, and Ty passed locally. |
| Full-suite collection | 831 tests were collected. |
| Full-suite execution | No reliable final result returned; do not report it as passing. |
| Network and cluster scope | No cluster commands were run. |

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Comet | Local CLI review and validation session | Used a development extra, local environment, and offline runs only. |
