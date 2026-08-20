---
name: pytest-coverage-threshold-and-enforcement
description: "Use when consolidating pytest coverage thresholds, diagnosing local-versus-CI coverage drift, adding Cobertura-backed per-module floors, raising a floor with targeted branch tests, securing report parsing, backstopping intentionally omitted modules, unlocking optional-dependency tests, or repairing lcov/geninfo CI. Keep one aggregate source of truth; measure branch_rate from XML before setting module floors; treat existing-but-unusable reports as failures; and distinguish a subset run's aggregate-gate failure from test failure."
category: testing
date: 2026-08-05
version: "2.0.0"
user-invocable: false
license: BSD-3-Clause
history: pytest-coverage-threshold-and-enforcement.history
verification: mixed
tags: [pytest, coverage, branch-coverage, fail-under, cobertura, per-module-floor, secure-xml, ci, lcov, optional-dependencies]
---

# Pytest Coverage Thresholds and Enforcement

## Overview

Coverage gates stay reliable when configuration has one aggregate threshold, CI produces explicit
machine-readable reports, and any stricter per-module policy reads those reports securely. The
canonical workflow below covers consolidation, merge-preview drift, branch-floor measurement,
omitted-module backstops, optional dependencies, and native lcov collection.

Verification remains `mixed`: the core and v1.2/v1.3 additions are verified in CI, the v1.4
branch-floor raise is verified locally, and the v1.5 fail-closed Cobertura-loader design remains
unverified. Project-specific results and commands are indexed in
[the notes](./pytest-coverage-threshold-and-enforcement.notes.md); exact prior content is in
[history](./pytest-coverage-threshold-and-enforcement.history).

## When to Use

- `--cov-fail-under` appears in CI, `addopts`, and `[tool.coverage.report]` with divergent values.
- CI coverage is lower than local because GitHub tests a merge-preview tree containing new main
  files absent from the PR head.
- Aggregate coverage hides a critical module with weak tests.
- A per-module floor needs to be raised through tests rather than by guessing a percentage.
- A subset run says “required coverage not reached” even though all selected tests passed.
- A coverage validator passes when XML is missing, malformed, unsafe to parse, or lacks required
  class/line/branch data.
- Live CLI/TTY modules are intentionally omitted and need an import/integration backstop.
- `pytest.importorskip()` hides branches because the relevant optional dependency is absent in CI.
- `generate_coverage.sh` fails from build-path, CMake source, gcov-version, or `.gcda` link errors.

## Verified Workflow

### Quick Reference

```bash
# Locate every aggregate threshold and override.
rg -n 'cov-fail-under|fail_under|override-ini=addopts' \
  pyproject.toml .github/ scripts/ tests/

# Full repository run: keep this as the aggregate source-of-truth path.
pytest --cov=<package> --cov-report=term-missing \
  --cov-report=xml:coverage.xml --cov-report=html

# Isolated module measurement without the repository aggregate gate.
pytest -o addopts='' tests/path/test_target.py \
  --cov=<package.module> --cov-branch --cov-report=term-missing \
  --cov-report=xml:/tmp/target-coverage.xml

# Read the authoritative rates from Cobertura rather than terminal combined %.
jq -n --arg note 'Use a secure XML parser in production; inspect class branch-rate and line-rate'

# Validate TOML after editing a floor.
python -c 'import tomllib; print(tomllib.load(open("coverage.toml", "rb")))'
```

### 1. Establish one aggregate threshold

Make `[tool.coverage.report].fail_under` the canonical aggregate floor. Remove redundant
`--cov-fail-under` values from workflow commands and `addopts`; keep report selection in `addopts`
only if the project intentionally wants it for every test invocation. Before editing, inspect
`--override-ini=addopts=` because CI may deliberately bypass repository defaults.

Run the full suite and record its actual percentage before choosing a floor. The threshold should be
at or below a stable baseline, not rounded above it. If the task is planning-only, verify that any
consistency checker accepts the proposed absence of redundant flags; do not assume it does.

Also trace documentation/config consistency checks before assuming removal is valid. Some projects
accept absence of the redundant flag but separately require a documented `<N>%+ test coverage`
pattern. Treat isolated test-fixture values as test inputs, not snapshots of live configuration.

### 2. Produce explicit reports and diagnose preview-tree drift

Configure terminal, XML, and HTML reports deliberately. Coverage on a pull request may run against
GitHub's synthetic merge of PR head and current main. A main-only executable module can lower the
denominator even though it is absent locally. Reproduce or inspect the merge-preview tree and compare
the per-file table before changing policy.

Adding a genuinely non-measured file to `[tool.coverage.run].omit` can be correct when it is present
only after merging with main and already covered by another backstop. Record why. Do not use omit to
hide an ordinary under-tested module.

### 3. Add per-module floors from Cobertura

Parse Cobertura `<class>` entries into normalized repository-relative file names and their
`branch-rate` and `line-rate`. Match configured files exactly, fail when a configured module is
missing, and use branch rate when the report provides branch data; otherwise use line rate. Store
floors in a small reviewed TOML file.

Set an initial floor several percentage points below a repeatedly measured stable rate when the goal
is regression protection. The original cases used a 3–4 percentage-point margin. This is a heuristic,
not a universal constant; highly deterministic modules may justify tighter bounds.

### 4. Raise a floor by testing uncovered branches

First disable global `addopts` for the isolated measurement. Otherwise an aggregate floor can print
`FAIL Required test coverage ...` after all selected tests pass and obscure the relevant module.
Read the `N passed` summary separately from coverage policy.

Use Cobertura's `branch-rate` as authoritative. The terminal percentage often combines statements
and branches and can differ materially. `NN->exit` in `term-missing` denotes the false side of a
branch, so write a test that exercises that condition rather than adding arbitrary lines. Re-run the
same isolated command, read the new XML, then set the floor no higher than the measured branch rate.
Finally run the full suite and the module-floor checker.

### 5. Fail closed on unusable reports

This design is proposed and remains unverified. One loader should serve aggregate and module parsing
and use a hardened XML implementation. Model at least these distinct failures:

- report path missing or unreadable;
- secure parser dependency unavailable;
- malformed or prohibited XML;
- root/attributes have invalid types or ranges;
- required aggregate or configured module data is absent;
- duplicate or ambiguous normalized module names.

Every failure must produce a nonzero CLI exit and, if JSON output is supported, `passed: false` with a
typed diagnostic. Never convert “report exists but cannot be interpreted” into skip/pass. Test each
failure at both parser and CLI boundaries.

Use stable machine codes such as `coverage_file_missing`, `parser_unavailable`,
`report_unparseable`, and `coverage_data_absent`, with `coverage: null`. Do not fall back from the
secure parser to the standard XML parser when the dependency is missing; return actionable install
guidance instead.

### 6. Backstop omissions and optional dependencies

For an intentionally omitted live CLI/TTY module, add an integration test that imports it and checks
critical startup wiring under realistic dependencies. Omission is not exemption from regression
testing. Keep the rationale next to the omit pattern.

For console smoke, `<script> --help` with a short timeout (the cited cases used five seconds) avoids
hanging on live behavior. Parametrize imports over every omitted module and freeze the reviewed omit
set so list growth requires an explicit test update.

Search for `pytest.importorskip`. Install the appropriate optional group in the CI job before counting
those tests as coverage. Then add targeted tests for the newly reachable branches. A passing run that
skips the optional path is not evidence that the path works.

### 7. Repair native lcov/geninfo collection sequentially

Resolve and pass canonical absolute `PROJECT_ROOT` and `BUILD_DIR` values. Configure CMake from the
actual source directory, choose the gcov binary matching the compiler used to produce `.gcno/.gcda`,
and only then address `geninfo` filesystem/link errors. `--ignore-errors` may be used for a precisely
understood, documented toolchain condition; it must not become a blanket success switch. Re-run from
a clean instrumented build and inspect that captured files are nonempty and belong to the project.

The cited Ubuntu 24.04/lcov 2.0 case ultimately required
`--ignore-errors negative,mismatch,version,gcov` after those root causes were established. Copy that
list only for the same diagnosed toolchain conditions.

### 8. End-to-end acceptance

1. Full tests pass at the aggregate floor.
2. XML/HTML/terminal reports are produced at the declared paths.
3. Every configured module appears and meets its floor.
4. A synthetic below-floor value fails both human and JSON interfaces.
5. Missing/malformed XML fails closed.
6. Omitted modules pass their import/integration backstop.
7. CI and local commands differ only where explicitly documented.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Duplicate gates | Thresholds in workflow, `addopts`, and coverage config | Values drifted and diagnostics disagreed | Keep one aggregate source of truth |
| Guess a new floor | Used terminal combined percentage | Policy compares branch rate, which differed | Read Cobertura `branch-rate` first |
| Trust subset exit status | Selected tests passed but aggregate gate failed | Global `addopts` measured the whole-package policy on a subset | Use `-o addopts=''` for diagnosis, then run full gates |
| Skip malformed reports | Treated parser failure as no data | Broken evidence passed policy | Use one secure loader and fail closed |
| Omit without a backstop | Excluded live/TTY modules | Import-time regressions became invisible | Add integration coverage for omitted code |
| Ignore optional skips | Counted a green suite as path coverage | `importorskip` never exercised the feature | Install the optional group and target its branches |
| Add broad lcov ignores | Suppressed geninfo errors immediately | Real path/toolchain problems stayed hidden | Fix root, build dir, and gcov pairing in order |

## Results & Parameters

| Parameter | Rule |
| --- | --- |
| Aggregate floor | `[tool.coverage.report].fail_under` only |
| Isolated diagnosis | `pytest -o addopts='' ... --cov-branch --cov-report=xml:<path>` |
| Module metric | Cobertura `branch-rate`; fall back to line rate only without branch data |
| Floor selection | At or below measured rate; 3–4 pp margin was stable in cited cases |
| Missing configured module | Hard failure |
| Missing/malformed/untrusted XML | Hard failure; JSON reports `passed: false` |
| Intentional omit | Documented reason plus import/integration backstop |
| Optional path | Install dependency, assert it did not skip, then measure |

## Verified On

- 2026-08-05 and earlier cited cases: consolidation, per-module measurement, optional-dependency,
  and CI remediation evidence ranged from local to CI as indexed in
  [the notes](./pytest-coverage-threshold-and-enforcement.notes.md).
- The proposed unified secure-loader contract remains unverified.

## Companions

- [Case notes](./pytest-coverage-threshold-and-enforcement.notes.md)
- [Version history and exact superseded snapshot](./pytest-coverage-threshold-and-enforcement.history)
