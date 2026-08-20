---
name: pytest-configuration-discovery-and-ci-pitfalls
description: "Diagnose pytest hangs, shadowed configuration, missing collection, plugin/addopts drift, partial-run coverage gates, stale CI paths, import-path gaps, mock/date leakage, and host-dependent expected values. Use when explicit tests pass but default CI collects fewer or fails differently."
category: testing
date: 2026-06-26
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
history: pytest-configuration-discovery-and-ci-pitfalls.history
tags: [pytest, configuration, discovery, testpaths, markers, pythonpath, coverage, ci]
---

# Pytest Configuration, Discovery, and CI Pitfalls

## Overview

Passing an explicitly named test proves execution, not default collection. Pytest behavior is a
product of the selected config file, rootdir, `testpaths`, markers, `pythonpath`, installed plugins,
and inherited `addopts`. Diagnose each layer with collection evidence before editing tests.

Detailed incidents are indexed in
[`pytest-configuration-discovery-and-ci-pitfalls.notes.md`](pytest-configuration-discovery-and-ci-pitfalls.notes.md).
The complete prior source is in
[`pytest-configuration-discovery-and-ci-pitfalls.history`](pytest-configuration-discovery-and-ci-pitfalls.history).

## When to Use

- CI hangs with asyncio daemon tasks waiting in epoll and no explicit assertion failure.
- Pytest warns that one configuration is ignored or `pytest.ini` and `pyproject.toml` coexist.
- Collection count is low, scripts imports fail, or default CI misses integration tests.
- A slim pytest installation inherits coverage/plugin flags it cannot satisfy.
- Unit/integration marker counts differ locally and in CI.
- A matrix points at renamed/deleted tests or a file passes explicitly but is absent by default.
- Flakes appear only in the full suite, on a future date, or on a different host path.
- Coverage fails on a deliberately partial marker run.

## Verified Workflow

### 1. Identify the effective configuration

```bash
pytest --trace-config
pytest --collect-only -q
find . -maxdepth 3 \( -name pytest.ini -o -name pyproject.toml -o -name setup.cfg \)
```

Consolidate to one authoritative pytest configuration. A nearer `pytest.ini` can shadow
`[tool.pytest.ini_options]` and produce the “ignoring pytest config” warning. After removal, rerun
trace and collection rather than assuming pyproject now wins.

### 2. Prove default collection

Compare default, marker, and explicit-path collection:

```bash
pytest --collect-only -q
pytest -m unit --collect-only -q
pytest -m integration --collect-only -q
pytest path/to/touched_test.py --collect-only -q
```

If explicit collection finds a file but default collection does not, move it into a configured
`testpaths` directory and update imports/references in the same change. Do not call an explicit-path
pass CI coverage. Include intended unit and integration roots in `testpaths`, and mark every
integration file consistently so bare pytest and marker-selected jobs share one inventory.

### 3. Fix import paths at the configuration boundary

Put stable import roots in pytest configuration, for example `pythonpath = [".", "scripts"]`, rather
than scattering `sys.path.insert` through tests. For isolated single-file collection where rootdir
still omits a scripts directory, add one narrowly scoped `conftest.py` guard before fixtures.

Before retaining an in-test path hack, prove whether the package-prefix import already resolves
under configured `pythonpath`; namespace packages often make the insertion redundant. Re-run the
single file and full collection after removal.

### 4. Align plugins with inherited addopts

A minimal `pip install pytest` job still reads repository `addopts`. If those flags include
`--cov`, `--asyncio-mode`, or other plugin options, either install the real test environment, install
every required plugin, or explicitly override addopts for the intentionally slim smoke command:

```bash
pytest -o addopts='' <smoke-target>
```

The override also disables inherited coverage and must not be reported as the full test gate. Prefer
the project’s locked environment to avoid dependency drift.

### 5. Place coverage gates on full-enough runs

Keep reporting configuration reusable, but place `--cov-fail-under` only on the full/unit suite that
exercises the measured package. Marker-selected integration or single-file runs naturally produce
partial coverage and should not inherit a repository-wide threshold.

### 6. Detect stale paths and watcher drift

For every matrix glob or hardcoded test path, expand it and fail if it matches zero files. Search all
workflow/script references before deleting or renaming. When replacing `pytest-watch` with
`pytest-watcher`, update the manifest and lock together and verify the retained `ptw` CLI contract.

### 7. Diagnose suite-only hangs and flakes

Run the suspected file alone, then with its nearest predecessor/group, then full suite with verbose
and timeout diagnostics. Class-level `patch.object` can leak across tests; scope patches to fixtures
or context managers and guarantee cleanup. Replace calendar dates and Unix timestamps that expire
with values relative to a frozen clock or explicit fixture.

An asyncio hang showing daemon tasks blocked in epoll is teardown/lifecycle evidence. Identify tasks
and fixtures that created them; do not merely raise CI timeout. Calibrate YAML fixture timeouts from
observed duration, such as a rounded multiple with a minimum floor, and update hardcoded assertions
that encode the old default.

### 8. Make expected values portable

Never bake an author machine’s absolute path or environment-derived literal into a golden value.
Derive expected output from the same production constant or fixture input used by the implementation,
then run the full parametrized test. A narrowed parameter subset can omit the host-sensitive case.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Explicit-path proof | Ran the stray test directly | Bypassed `testpaths` and hid zero CI collection | Compare default `--collect-only` |
| Dual config | Kept pytest.ini and pyproject settings | Nearer file shadowed intended options | Keep one authoritative config |
| Per-test path hack | Inserted scripts path in each test | Rootdir behavior stayed inconsistent | Configure pythonpath or narrow conftest guard |
| Slim pytest only | Installed pytest without addopts plugins | Inherited options were unrecognized | Use locked env or deliberate addopts override |
| Global fail-under | Put threshold in shared config | Partial runs failed despite healthy full coverage | Gate only full-enough suite |
| Cosmetic matrix | Left a deleted path in CI | Job ran zero intended tests | Assert each pattern matches files |
| Larger timeout | Raised the CI timeout on a hang | Leaked async tasks still never terminated | Fix task/fixture lifecycle |
| Class-level patch | Shared mock across test class | State leaked in full suite | Scope patch and guarantee cleanup |
| Host golden | Hardcoded local absolute path | CI host rendered a different value | Derive from production constant |

## Results & Parameters

```text
effective config file and rootdir
default/unit/integration/explicit collection counts
testpaths, markers, pythonpath, and addopts
installed pytest plugins and locked environment command
coverage target and which suite owns fail-under
matrix patterns with resolved file counts
isolated/group/full-suite reproduction order
pending asyncio task/fixture owner and timeout observations
host-derived fixture inputs and full parametrized result
```

## Verified On

- Configuration consolidation, collection, marker, import, coverage, timeout, mock/date, and host
  portability cases through 2026-06-26.
- Verification remains `verified-local`; individual CI-confirmed collection cases are identified in
  notes without upgrading all guidance.
