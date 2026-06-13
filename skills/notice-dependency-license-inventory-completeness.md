---
name: notice-dependency-license-inventory-completeness
category: documentation
date: 2026-06-12
version: "1.1.0"
history: notice-dependency-license-inventory-completeness.history
user-invocable: false
verification: verified-local
tags:
  - notice
  - license-inventory
  - third-party-dependencies
  - pyproject
  - drift-guard
  - pep508
  - pep503
  - regression-test
  - tzdata
  - spdx
  - documentation-completeness
  - conditional-dependency
description: 'Keep a legal NOTICE / third-party-license inventory in sync with [project].dependencies, and guard the sync with a regression test. Use when: (1) a NOTICE / ATTRIBUTION / license-inventory file claims to be a complete runtime dependency-license list but a conditional/platform-gated dependency (e.g. "tzdata; platform_system == \"Windows\"") is declared in pyproject.toml yet missing from the doc; (2) writing a license string into a legal doc — lead with the verified SPDX token from authoritative metadata (PyPI info.license), not a colloquial string like "Public domain"; (3) building a doc-vs-pyproject drift guard test that must use exact PEP 508 name parsing + PEP 503 normalization, NOT substring matching; (4) a section-scoped text parser silently returns an empty block because it matched the section header''s OWN underline rule instead of the terminating one.'
---

# NOTICE: Dependency License Inventory Completeness

Keep a legal `NOTICE` / third-party-license inventory in sync with
`pyproject.toml [project].dependencies`, and guard the sync with a regression
test so a future dependency addition cannot silently leave the inventory stale.

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-12 |
| **Objective** | Close a real completeness gap in a legal NOTICE inventory (a Windows-only conditional runtime dep declared in pyproject but absent from NOTICE), then add a PEP 508/503-correct regression guard so the inventory can never silently drift again |
| **Outcome** | Successful — NOTICE entry added (leading with the verified SPDX token), RED→GREEN regression guard at `tests/unit/scripts/test_notice_runtime_completeness.py`, ruff/mypy clean, adjacent suites green |
| **Verification** | verified-local — CI validation pending (the new pytest guard passes locally with ruff+mypy clean; the PR's CI had not yet gone green at capture time) |

## When to Use

- A `NOTICE` / `ATTRIBUTION` / license-inventory file **claims to be a complete**
  runtime dependency-license list, but a conditional / platform-gated dependency
  (e.g. `tzdata; platform_system == "Windows"`) is declared in
  `pyproject.toml [project].dependencies` yet missing from the doc.
- You are writing a license string into a **legal document** and need to lead with
  a verified SPDX token rather than a colloquial string ("Public domain").
- You want a **doc-vs-pyproject drift guard** test that fails if any declared
  runtime dependency is absent from the NOTICE inventory — using exact PEP 508
  name parsing + PEP 503 normalization, NOT substring matching.
- A section-scoped text parser **silently returns an empty block** because it
  matched the section header's OWN underline rule instead of the terminating one.

## The Core Problem

A `NOTICE` file's "Third-party runtime dependencies" section listed only
`packaging`, `pyyaml`, and `pydantic`. But `pyproject.toml [project].dependencies`
also declares:

```toml
"tzdata; platform_system == 'Windows'"
```

This is a Windows-only **conditional runtime dependency** — present because
`hephaestus.github.rate_limit` uses `zoneinfo.ZoneInfo`, which needs the IANA tz
database that CPython does **not** bundle on Windows. Because the NOTICE claimed
to be a *complete* inventory, this was a genuine completeness gap, not a cosmetic
omission. (Provenance: `tzdata` was added in ProjectHephaestus PRs #534/#536/#538
for issue #539 to make `zoneinfo` work on Windows. Cross-reference the existing
skill `python-import-patterns-and-compatibility-guards`.)

The two failure modes a naive fix introduces are equally important to the fix
itself: (a) leading the legal entry with an **unverified, non-SPDX** license
string, and (b) writing a guard test that uses **substring matching** instead of
exact PEP 508/503 comparison.

## Verified Workflow

### Quick Reference

```bash
# 1. Find every declared runtime dependency and compare against the NOTICE block
grep -nE "^\s*\"" pyproject.toml | sed -n '/dependencies/,/]/p'   # inspect [project].dependencies
grep -nE "Third-party runtime dependencies" -A12 NOTICE            # inspect the NOTICE block

# 2. Verify the license token against authoritative ground truth (NOT memory)
curl -s https://pypi.org/pypi/tzdata/json | python -c "import sys,json;print(json.load(sys.stdin)['info']['license'])"
#   -> Apache-2.0    (and the project ships licenses/LICENSE_APACHE)

# 3. RED: the guard fails naming the missing dep BEFORE the NOTICE edit
pixi run python -m pytest tests/unit/scripts/test_notice_runtime_completeness.py -v --no-cov
#   -> NOTICE 'Third-party runtime dependencies' omits: ['tzdata']

# 4. Edit NOTICE (lead with the SPDX token), then GREEN
grep -nE "tzdata +Apache-2\.0" NOTICE                              # license token specifically present
pixi run python -m pytest tests/unit/scripts/test_notice_runtime_completeness.py -v --no-cov

# 5. Quality gates (run the CONFIGURED mypy task — no extra path arg)
pixi run ruff check . && pixi run mypy
pixi run python -m pytest tests/unit/scripts/test_dependency_floor_consistency.py tests/unit/scripts/test_sdist_contents.py -v --no-cov
```

### Detailed Steps

#### 1. Add the missing dependency to the NOTICE block, leading with the SPDX token

Verify the license against authoritative ground truth before writing it: PyPI
metadata `https://pypi.org/pypi/tzdata/json` reports `info.license == "Apache-2.0"`,
and the project ships `licenses/LICENSE_APACHE`. The public-domain nature of the
IANA tz **data** is true but secondary, so it belongs in a parenthetical, not as
the leading token.

House style matters: every other NOTICE entry uses an SPDX token
(`Apache-2.0 OR BSD-2-Clause`, `MIT`), so a colloquial string like
"Public domain" would diverge. Follow the existing conditional-dep convention
(the repo's `tomli  MIT (used only on Python < 3.11; ...)` line) with a
Windows-only parenthetical. Final line:

```text
tzdata        Apache-2.0 (packaging; bundles public-domain IANA tz database
              data — installed only on Windows: platform_system == 'Windows')
```

#### 2. Add a regression guard scoped to [project].dependencies

Place it at `tests/unit/scripts/test_notice_runtime_completeness.py`. It fails if
**any** `[project].dependencies` distribution is absent from the NOTICE runtime
block. Key design points:

- **Parse the bare PEP 508 distribution name** by mirroring the neighbor test's
  `_find_dep` (`tests/unit/scripts/test_dependency_floor_consistency.py`): split on
  `;` to drop the env marker, then split on the version operator. Strip operators
  **longest-first** with this tuple and break on the first hit:
  `("<=", ">=", "==", "!=", "~=", "<", ">", "=")` — so `"=="` is never eaten as
  `"="` + `"="`.
- **PEP 503-normalize BOTH sides** (dependency name and every NOTICE token):
  `re.sub(r"[-_.]+", "-", name).lower()`. Compare via exact membership in a
  normalized token **set** — NOT case-insensitive substring matching (substring
  matching false-passes on short names and false-fails on abbreviations).
- **Load pyproject.toml** with the tomllib/tomli version guard.
- **Repo root** from a test under `tests/unit/scripts/` is
  `Path(__file__).resolve().parents[3]` (worktree-safe — `parents[4]` resolves to
  `.worktrees/`).
- **Scope to `[project].dependencies` ONLY**; extras live in a separate NOTICE
  section and are intentionally out of scope. Document this boundary in the test
  docstring so it doesn't read as "fully guarded".
- **Assert the runtime block was FOUND and is NON-EMPTY** before asserting
  membership, so a future NOTICE reformat fails loudly instead of vacuously
  passing.

```python
import re
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[3]  # tests/unit/scripts/ -> repo root


def _canonical(name: str) -> str:
    """PEP 503 canonical form: lowercase, runs of -_. collapsed to a single -."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _dist_name(spec: str) -> str:
    """Bare PEP 508 distribution name: 'tzdata; platform_system == "Windows"' -> 'tzdata'."""
    spec = spec.split(";", 1)[0]  # drop the environment marker
    for op in ("<=", ">=", "==", "!=", "~=", "<", ">", "="):  # longest-first
        if op in spec:
            spec = spec.split(op, 1)[0]
            break
    return spec.strip()
```

#### 3. Drive it RED → GREEN (TDD)

The guard must **fail naming the missing dep** before the NOTICE edit, then
**pass** after it. Confirmed: it failed with
`NOTICE 'Third-party runtime dependencies' omits: ['tzdata']`, then passed once
the NOTICE line was added.

#### 4. Verify the license token specifically (not just presence)

`grep -nE "tzdata +Apache-2\.0" NOTICE` must hit — presence of the name is not
enough; the SPDX token must be the leading one. Then confirm ruff + mypy are clean
and adjacent suites (`test_dependency_floor_consistency.py`,
`test_sdist_contents.py`) stay green.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Block parser skipped only the header LINE | Scoped the section between the header and the next `====` rule, but advanced past only the header text line | The next `====` search matched the header's OWN underline rule immediately, so the extracted block was empty and the test failed with "NOTICE runtime-dependencies block is empty" instead of the intended "tzdata missing" | When scoping a section between a header and the NEXT horizontal rule, consume the header's underline rule first (`re.match(r"={5,}\s*\n", rest)` then advance past it). The non-empty-block assertion is what surfaced this — it earned its keep |
| Lead the entry with "Public domain" | Wrote the colloquial, unverified license string as the leading token (from prior plan-review findings) | Diverges from the SPDX house style every other entry uses, and was never checked against ground truth | Verify against PyPI `info.license` + the bundled `LICENSE_*` file and lead with the SPDX token (`Apache-2.0`); put the public-domain-data note in a parenthetical |
| Case-insensitive SUBSTRING membership | `dep.lower() in notice_text.lower()` for the completeness check | False-passes on short names (a 3-letter dep name appearing inside unrelated prose) and false-fails on abbreviations | Exact PEP 503-normalized **set** membership: normalize both sides with `re.sub(r"[-_.]+", "-", name).lower()` and compare set membership |
| Pass the test path to `pixi run mypy` | Ran `pixi run mypy tests/unit/scripts/test_notice_runtime_completeness.py` | The configured mypy task already globs `tests/`, so the extra arg produced a spurious "Duplicate module named ..." error | Run the configured mypy task with NO extra path arg; it already covers the file (373 source files, clean) |
| `parents[4]` for repo root | Computed project root from test depth assuming one extra level | In a git worktree `parents[4]` resolved to `.worktrees/`, not the repo root | From `tests/unit/scripts/` the correct depth is `parents[3]` (worktree-safe) |
| (Noted residual edge, not a current defect) | Block-token set also includes the parenthetical PROSE words | A dependency whose normalized name exactly equals a prose word in the block could false-pass | Inert for `packaging`/`pyyaml`/`pydantic`/`tzdata`; note it for implementer awareness — a future tightening could tokenize only the first column |

## Results & Parameters

### Final NOTICE line

```text
tzdata        Apache-2.0 (packaging; bundles public-domain IANA tz database
              data — installed only on Windows: platform_system == 'Windows')
```

### PEP 508 operator-strip tuple (longest-first, break on first hit)

```python
("<=", ">=", "==", "!=", "~=", "<", ">", "=")
# longest-first so "==" is never eaten as "=" + "="
```

### PEP 503 normalization regex

```python
re.sub(r"[-_.]+", "-", name).lower()   # apply to BOTH the dep name and every NOTICE token
```

### Repo-root note

```python
# tests/unit/scripts/test_notice_runtime_completeness.py
REPO_ROOT = Path(__file__).resolve().parents[3]  # parents[4] -> .worktrees/ (wrong)
```

### tomllib / tomli version guard

```python
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
```

### Verification commands

```bash
grep -nE "tzdata +Apache-2\.0" NOTICE
pixi run python -m pytest tests/unit/scripts/test_notice_runtime_completeness.py -v --no-cov
```

### Scope boundary (document in the test docstring)

- Guard covers `[project].dependencies` ONLY.
- Optional extras (`[project.optional-dependencies.*]`) live in a separate NOTICE
  section and are intentionally out of scope, so the test does not read as
  "fully guarded".
- Assert the runtime block was FOUND and NON-EMPTY before asserting membership —
  a future NOTICE reformat then fails loudly instead of vacuously passing.

### Provenance

`tzdata` was added in ProjectHephaestus PRs #534/#536/#538 (issue #539) for
`zoneinfo.ZoneInfo` support on Windows. Cross-reference the existing skill
`python-import-patterns-and-compatibility-guards`.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Issue #1218 / PR #1254 | NOTICE `tzdata` entry + `tests/unit/scripts/test_notice_runtime_completeness.py`; verified-local (ruff/mypy/adjacent suites green locally; CI pending at capture) |
