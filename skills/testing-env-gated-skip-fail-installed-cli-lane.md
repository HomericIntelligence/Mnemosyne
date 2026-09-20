---
name: testing-env-gated-skip-fail-installed-cli-lane
license: BSD-3-Clause
description: "Detect installed CLI test skips when CI promises an installation but missing commands silently remove coverage."
category: testing
date: 2026-07-17
version: "1.0.1"
user-invocable: false
verification: unverified
tags:
  - pytest-skip
  - silent-skip
  - skip-to-fail
  - env-gate
  - console-scripts
  - entry-points
  - installed-artifact
  - fresh-venv
  - wheel
  - path-resolution
  - required-checks-gate
  - ci-lane
  - signal-fidelity
  - dry
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/ed1bd4f54fd4aaba446af92c8b3ab9aff2589ae3/skills/testing-env-gated-skip-fail-installed-cli-lane.history"
history-cleanup-date: "2026-09-20"
---

# Env-Gated Skip-to-Fail Plus Installed-Artifact CLI Test Lane

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-17 |
| **Objective** | Plan the fix for a MINOR audit finding (ProjectHephaestus issue #2173): console-binary `--help`/`--version`/`--json` checks silently `pytest.skip` when the script is not on `PATH`, so nothing guarantees the ~40 `[project.scripts]` binaries are ever exercised; add an installed-artifact test lane. |
| **Outcome** | Reviewed implementation plan: one `_resolve_binary()` seam replacing 5 duplicated skip blocks, a `<PKG>_REQUIRE_CLI=1` skip-to-fail gate enabled in all existing integration lanes, and a new required `installed-cli-tests` job (wheel → fresh venv → strict rerun). Design-stage entry; the plan's PR carries the execution. |
| **Verification** | unverified — the plan cites live file/line evidence from the target repo, but the composed change had not merged when this was written. |

## When to Use

- A test suite exercises installed console binaries via `subprocess` + `shutil.which(cmd)` and every miss is a `pytest.skip` — green CI cannot be distinguished from "all CLI checks skipped".
- A repo audit reports CLI help/version/machine-output checks "skip when scripts are absent from PATH" and asks for an installed-artifact lane.
- You need the lane's subprocesses to prove the *installed wheel* works, not the source checkout that happens to be the CWD.
- The repo's CI has an aggregator gate job (e.g. `required-checks-gate`) whose `needs:` completeness is enforced by a unit test, so adding a lane has a mandatory wiring step.
- Skip lattices mix legitimate platform skips (e.g. Windows lacking `curses`/`fcntl`) with availability skips — only the availability skips should become env-gated failures.

## Verified Workflow

### 1. One resolver seam, skip by default, fail under the env gate

Replace every duplicated `shutil.which` + `pytest.skip` block with a single helper in the test module:

```python
REQUIRE_CLI_ENV = "<PKG>_REQUIRE_CLI"

def _resolve_binary(command: str) -> str:
    binary = shutil.which(command)
    if binary is None:
        message = f"{command} not on PATH — install the package or run under the project env"
        if os.environ.get(REQUIRE_CLI_ENV) == "1":
            pytest.fail(f"{message} (skip forbidden: {REQUIRE_CLI_ENV}=1)")
        pytest.skip(message)
    return binary
```

- Developer checkouts without an install keep skipping (no local friction); CI lanes that install first export the env var and can never silently lose coverage again.
- The `str` (not `str | None`) return removes per-site `assert binary is not None` mypy-narrowing noise (cf. [[mypy-shutil-which-optional-narrowing]]).
- Keep platform-legitimate skips (win32 `curses`/`fcntl`) out of this gate — they are correct skips, not coverage loss.
- Add self-tests for the gate itself: `pytest.raises(pytest.skip.Exception)` on a bogus command without the env var, `pytest.raises(pytest.fail.Exception)` with it.

### 2. Enable the gate wherever the install step guarantees the binaries

Every CI lane that runs `<package-manager> sync`/install before pytest has the scripts in the venv `bin/` on `PATH`, so `<PKG>_REQUIRE_CLI=1` cannot false-positive there. Set it as step-level `env:` in each integration lane (required workflow, cross-version matrix, release mirror). This converts a future install-step regression from silent green to a loud red.

### 3. Installed-artifact lane: wheel → fresh venv → strict rerun

New CI job modeled on the sibling integration job:

```yaml
- uses: <checkout-action>
  with:
    fetch-depth: 0        # setuptools-scm/hatch-vcs derive the version
    fetch-tags: true      # from git tags; a shallow checkout builds a wrong wheel
- run: <build-tool> build --wheel
- run: |
    <venv-tool> venv build/cli-venv
    WHEEL=(dist/*.whl)
    <pip-tool> install --python build/cli-venv/bin/python "${WHEEL[0]}[<extra>]" pytest <conftest-deps>
- env:
    <PKG>_REQUIRE_CLI: "1"
  run: |
    export PATH="$PWD/build/cli-venv/bin:$PATH"
    build/cli-venv/bin/pytest tests/integration/test_cli_entry_points.py \
      --override-ini="addopts=" -v --strict-markers
```

Why the subprocesses genuinely exercise the wheel even with the source checkout as CWD:

- `shutil.which` resolves to the fresh venv's shebang scripts because its `bin/` is prepended to `PATH`.
- A console script's `sys.path[0]` is the venv `bin/` directory, not the CWD, so `import <pkg>` resolves to the installed wheel — provided the test's subprocess env pops `PYTHONPATH` (keep/add that in the shared subprocess-env helper).
- Install extras the CLIs need (product-layer extra) plus whatever the root `conftest.py` imports (check its top-level imports — a missing `pyyaml`-style dep fails collection, not the CLIs).
- `--override-ini="addopts="` neutralizes coverage addopts so the fresh venv does not need `pytest-cov`.

### 4. Wire the lane into the aggregator gate

If a unit test enforces the aggregator's `needs:` completeness (every non-exempt job must appear), add the new job id there; the test turns "forgot to make it required" into a red build. No branch-protection/ruleset edit is needed when the aggregator is the protected context.

### 5. Scope checks before claiming doc/inventory churn

Verify what meta-checks actually compare before editing docs: a workflow-inventory check that diffs on-disk `.yml` *files* against a README table is unaffected by a new job in an existing file; a required-checks doc that describes the gate generically ("~20 jobs") needs no enumeration edit.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Considered | Making missing binaries always fail (no env gate) | Breaks developer checkouts that run tests without installing the package | Skip-by-default + CI-side env gate keeps local ergonomics while making CI strict |
| Considered | Only adding the installed lane, leaving existing lanes ungated | Existing editable-install lanes could silently regress to all-skips if the install step changed | The gate is nearly free in every lane whose install step guarantees the binaries — set it everywhere it cannot false-positive |
| Considered | Asserting installed-ness via in-process `import` checks in the new lane | pytest inserts the test package root (repo root when `tests/__init__.py` chains exist) into `sys.path`, so in-process imports can resolve to the checkout, not the wheel | Only the console-script *subprocesses* (venv shebang + popped `PYTHONPATH`) are trustworthy installed-artifact evidence |

## Results & Parameters

- Target evidence (ProjectHephaestus): 5 duplicated skip sites in `tests/integration/test_cli_entry_points.py`; ~40 entries under `[project.scripts]`; aggregator completeness enforced by `tests/unit/ci/test_required_checks_gate.py` (`_unwired_jobs`).
- Env gate name pattern: `<PKG>_REQUIRE_CLI` with the literal value `"1"`; anything else keeps skip semantics.
- Fresh venv lives under the repo's designated scratch dir (`build/` in Hephaestus) so temp-file policy checks stay green.
- Related entries: [[testing-local-wheel-install-content-test]] (wheel *content* assertions — complementary, different intent), [[ci-cd-canonical-install-check-inline-build]] (canonical `install` check design; shares the "a skipping check emits green without testing" principle), [[testing-env-leak-local-fail-ci-pass]] (PATH/env divergence between local and CI), [[mypy-shutil-which-optional-narrowing]].

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #2173 implementation plan (design-stage; PR pending) | Plan grounded in live greps of `test_cli_entry_points.py`, `_required.yml`, `test.yml`, `release.yml` |
