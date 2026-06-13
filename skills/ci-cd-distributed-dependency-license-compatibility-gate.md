---
name: ci-cd-distributed-dependency-license-compatibility-gate
description: "Use when: (1) NOTICE/license attribution is maintained manually but no CI verifies that new or transitively-upgraded distributed deps stay license-compatible; (2) building a stdlib-only license drift-guard that scans the DISTRIBUTED dependency set (base + runtime extras, never dev) from importlib.metadata Requires-Dist; (3) resolving a package's license across License-Expression (PEP 639 SPDX) -> trove Classifier -> freeform License field; (4) implementing a two-tier allowlist (blanket permissive set + per-package NOTICE-justified copyleft entries such as PyGitHub/LGPL or defusedxml/PSF); (5) wiring an advisory-on-main / blocking-on-PR CI job that installs the project's full runtime extras on a bare setup-python runner; (6) deciding NOT to add a pre-commit hook because the check requires a full extras install that dev environments lack."
category: ci-cd
date: 2026-06-12
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [license-compatibility, notice, spdx, copyleft, pip-licenses, license-allowlist, requires-dist, importlib-metadata, pep639, pep508, packaging, drift-guard, ci-gate, github-actions, advisory-vs-blocking, fail-loud]
---

# CI/CD Distributed Dependency License Compatibility Gate

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-12 |
| **Objective** | Machine-enforce that no distributed dependency under a copyleft/NOTICE-incompatible license silently enters the shipped tree. NOTICE held correct manual license determinations (BSD/MIT/Apache base; LGPL/PSF as non-vendored optional extras) but pip-audit only checks CVEs, not licenses — leaving license drift undetected on every new dep or upgrade. |
| **Outcome** | Successful — `scripts/check_license_compatibility.py` (stdlib + `packaging` only) implemented with two-tier allowlist, marker-matrix scope, FAIL LOUD semantics, and advisory/blocking CI split. All tests pass locally; bare-venv CI scenario reproduced. |
| **Verification** | verified-local — tests pass locally and bare-venv `pip install -e .[all]` + script scenario reproduced; full GitHub CI run was still in progress when captured. |

## When to Use

- A NOTICE file or license attribution list is maintained by hand but no CI job verifies that newly added or upgraded distributed dependencies remain compatible.
- You want a single stdlib-only script (no pip-licenses, no third-party license scanners) that derives its dep list from the already-installed package metadata (`importlib.metadata.Requires-Dist`) rather than parsing `pyproject.toml` or a lockfile — so the scan always matches what CI actually installed.
- A project distinguishes between a permissive base install and copyleft-tolerant optional extras (e.g. LGPL networking libs, PSF-licensed XML parsers) and those extras are explicitly NOTICE-justified — the gate must enforce that distinction without blocking the extras themselves.
- You need a CI design decision: the check requires `.[all]` installed, which dev/pre-commit environments usually lack, so it belongs exclusively in CI (not pre-commit).
- You want a progressive severity policy: advisory (exit 0) when running on `main` or a scheduled job, blocking (exit 1) only on pull requests — so main can never be silently broken.

## Verified Workflow

### Quick Reference

```bash
# 1. Scope: install the project with all runtime extras on a bare setup-python runner
pip install -e ".[all]"

# 2. Run the license compatibility check
python3 scripts/check_license_compatibility.py

# On a PR (GITHUB_EVENT_NAME=pull_request): exits 1 if any incompatible dep is found
# On main/schedule: exits 0 (advisory — logs warnings, does not block)

# 3. Acceptance checks (copy-paste):
#    a) A copyleft dep (e.g. GPL-3.0) added to base install → exit 1 on PR, exit 0 on main
#    b) "MIT OR GPL-3.0" License-Expression → allowed (OR-semantics, MIT is permissive)
#    c) defusedxml with PSF-2.0/Python-2.0 → allowed (per-package ALLOWED_EXTRA_COPYLEFT)
#    d) PSF-2.0 on an unknown package → rejected (not in blanket PERMISSIVE)
#    e) bare venv (Linux, py3.14): tomli/tzdata skipped (markers exclude current env), all
#       installed deps classified compatible
```

### Detailed Design

#### Step 1 — Scope to distributed deps only

```python
import importlib.metadata as md
from packaging.requirements import Requirement

DIST = "your-package-name"           # the project's own dist name
RUNTIME_EXTRAS = {"all", "automation", "github", "nats", "toml", "xml", "schema"}
# Never include "dev" — GPL dev tools (yamllint, bats) are structurally unreachable
# from the distributed package.

raw_reqs = md.metadata(DIST).get_all("Requires-Dist") or []
# Raises PackageNotFoundError if DIST is absent → catch it and exit 2 with install hint
```

#### Step 2 — Marker matrix (catch platform/python-gated deps)

Evaluate each requirement's marker across:
- Python versions: `{3.10, 3.13}` (floor and ceiling of supported range)
- Platforms: `{linux/Linux, win32/Windows, darwin/Darwin}`
- Extras: the full `RUNTIME_EXTRAS` set

A dep like `tomli; python_version < "3.11"` is IN SCOPE on the 3.10 row even when CI runs 3.14. A dep like `tzdata; sys_platform == "win32"` is IN SCOPE on the Windows column even when CI runs Linux.

```python
from packaging.markers import default_environment

PYTHON_VERSIONS = ["3.10", "3.13"]
PLATFORMS = [
    ("linux",  "Linux"),
    ("win32",  "Windows"),
    ("darwin", "Darwin"),
]

def in_scope(req: Requirement) -> bool:
    if req.marker is None:
        return True   # unconditional dep, always in scope
    for pyver in PYTHON_VERSIONS:
        for (sys_plat, os_name) in PLATFORMS:
            for extra in RUNTIME_EXTRAS:
                env = {**default_environment(),
                       "python_version": pyver,
                       "sys_platform": sys_plat,
                       "os_name": os_name,
                       "extra": extra}
                if req.marker.evaluate(env):
                    return True
    return False

def installable_now(req: Requirement) -> bool:
    """True if this dep would be installed in the CURRENT interpreter/platform."""
    if req.marker is None:
        return True
    return req.marker.evaluate({**default_environment(), "extra": next(iter(RUNTIME_EXTRAS), "")})
```

Use `installable_now` to distinguish: a dep that IS in scope (matrix) but NOT installable now (current env excludes it) → skip with note (not a hard error). A dep that IS installable now but has no metadata → exit 2 (FAIL LOUD coverage hole).

#### Step 3 — Three-field license resolution (most-standardized first)

```python
def resolve_license(pkg_name: str) -> list[str]:
    """Return list of SPDX-ish license IDs. List because OR-expressions yield multiple."""
    meta = md.metadata(pkg_name)

    # 1. License-Expression (PEP 639 SPDX) — e.g. "MIT", "Apache-2.0", "LGPL-3.0-only OR ..."
    expr = meta.get("License-Expression")
    if expr:
        # Split on " OR " to handle disjunctive expressions
        return [part.strip() for part in re.split(r"\s+OR\s+", expr, flags=re.IGNORECASE)]

    # 2. Trove classifiers — e.g. "License :: OSI Approved :: MIT License"
    classifiers = meta.get_all("Classifier") or []
    trove_ids = []
    for c in classifiers:
        if c.startswith("License ::"):
            trove_id = TROVE_TO_SPDX.get(c)   # mapping table
            if trove_id:
                trove_ids.append(trove_id)
    if trove_ids:
        return trove_ids

    # 3. Freeform License field — normalize via alias table
    freeform = meta.get("License") or ""
    normalized = LICENSE_ALIASES.get(freeform.strip(), freeform.strip())
    return [normalized] if normalized else ["UNKNOWN"]
```

Key mapping entries to include in `TROVE_TO_SPDX`:
- `"License :: OSI Approved :: MIT License"` → `"MIT"`
- `"License :: OSI Approved :: Apache Software License"` → `"Apache-2.0"`
- `"License :: OSI Approved :: BSD License"` → `"BSD-3-Clause"`
- `"License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)"` → `"LGPL-3.0"`
- `"License :: OSI Approved :: Python Software Foundation License"` → `"PSF-2.0"`
- `"License :: OSI Approved :: ISC License (ISCL)"` → `"ISC"`

#### Step 4 — Two-tier allowlist

```python
# Tier 1: blanket permissive — no per-package annotation needed
PERMISSIVE = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC"}
# NOTE: do NOT put PSF-2.0 or Python-2.0 here — PSF is allowed only for defusedxml
# (per-package NOTICE entry). Keeping it out of PERMISSIVE ensures any OTHER package
# that ships PSF is flagged for explicit NOTICE review.

# Tier 2: per-package copyleft/non-standard licenses explicitly allowed by NOTICE
ALLOWED_EXTRA_COPYLEFT: dict[str, set[str]] = {
    "pygithub": {"LGPL-3.0", "LGPL-3.0-only", "LGPL-3.0-or-later", "LGPL"},
    # Include SPDX-canonical forms (LGPL-3.0-only, LGPL-3.0-or-later) so that a future
    # PyGitHub release shipping PEP 639 License-Expression (which wins over trove) is
    # still allowed without a NOTICE update.
    "defusedxml": {"PSF-2.0", "Python-2.0"},
}

def is_compatible(pkg_name: str, license_ids: list[str]) -> bool:
    """OR-semantics: compatible if ANY disjunct is permissive or per-package allowed."""
    pkg_lower = pkg_name.lower()
    per_pkg = ALLOWED_EXTRA_COPYLEFT.get(pkg_lower, set())
    return any(lid in PERMISSIVE or lid in per_pkg for lid in license_ids)
```

#### Step 5 — FAIL LOUD (never silent no-op)

```python
try:
    raw_reqs = md.metadata(DIST).get_all("Requires-Dist") or []
except md.PackageNotFoundError:
    print(f"FATAL: {DIST} not installed. Run: pip install -e '.[all]'", file=sys.stderr)
    sys.exit(2)

if not raw_reqs:
    print(f"FATAL: {DIST} has no Requires-Dist — metadata is empty or install is broken.",
          file=sys.stderr)
    sys.exit(2)

# For each dep that IS installable now but has no metadata:
for dep_name in installable_now_deps:
    try:
        md.metadata(dep_name)
    except md.PackageNotFoundError:
        print(f"FATAL: {dep_name} should be installed (marker matches current env) "
              f"but has no metadata. Run: pip install -e '.[all]'", file=sys.stderr)
        sys.exit(2)
```

#### Step 6 — Advisory / blocking split

```python
import os

event = os.environ.get("GITHUB_EVENT_NAME", "")
is_pr = event == "pull_request"

# ... run scan, collect incompatible_deps list ...

if incompatible_deps:
    for pkg, lids in incompatible_deps:
        print(f"INCOMPATIBLE: {pkg} ({', '.join(lids)}) — not in allowlist", file=sys.stderr)
    if is_pr:
        sys.exit(1)   # blocking on PRs
    else:
        print("WARNING: incompatible deps found (advisory — not blocking on main/schedule)",
              file=sys.stderr)
        sys.exit(0)   # advisory on main

sys.exit(0)
```

#### Step 7 — CI job wiring

```yaml
# In security.yml (or wherever license checks live):
- name: Check out repository
  uses: actions/checkout@<SHA>  # grep existing workflows for the repo-standard pin
  with:
    fetch-depth: 0              # hatch-vcs needs full history to compute version

- name: Set up Python
  uses: actions/setup-python@<SHA>  # grep for repo-standard pin — do NOT introduce divergent SHA
  with:
    python-version: "3.13"
    cache: pip

- name: Install runtime deps (bare pip, NOT pixi)
  run: pip install -e ".[all]"
  # Bare setup-python + pip, NOT inside pixi. pip+pixi co-managing site-packages
  # causes lockfile churn and is an unsupported configuration.

- name: License compatibility check
  run: python3 scripts/check_license_compatibility.py
```

#### Step 8 — [all]-completeness regression test

Parse `pyproject.toml` and assert every `RUNTIME_EXTRAS` member (except the self-referential `all`) appears in the `[all]` aggregate string. Prevents a future extra omitted from `[all]` from silently skipping the gate.

```python
import tomllib, pathlib

def test_all_extras_covered():
    data = tomllib.loads(pathlib.Path("pyproject.toml").read_text())
    all_str = " ".join(data["project"]["optional-dependencies"]["all"])
    for extra in RUNTIME_EXTRAS - {"all"}:
        assert extra in all_str, f"Extra '{extra}' missing from [all] aggregate"
```

#### Step 9 — Test-loading convention for scripts/ without `__init__.py`

```python
# In tests/unit/scripts/test_check_license_compatibility.py:
import sys
from pathlib import Path

# parents[0]=test file, [1]=scripts/, [2]=unit/, [3]=tests/, [4]=repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
# Verify this resolves to the real repo root inside a git worktree — it does.
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| `sys.exit("FATAL: ...")` with a string message | Called `sys.exit` with a string error description to exit with a non-zero code | `SystemExit.code` is the STRING, not `2`; tests asserting `.code == 2` always fail because the string is truthy but not equal to the integer `2` | `print(msg, file=sys.stderr)` THEN `sys.exit(2)`. Never pass a string to `sys.exit` when tests check the numeric exit code. |
| Not handling the package itself being absent | Called `md.metadata(DIST)` without a try/except, assuming the package would always be installed in CI | `PackageNotFoundError` propagated as an unhandled traceback, crashing the script with exit code 1 (not 2) and a confusing stack trace instead of an actionable install hint | Catch `PackageNotFoundError` on the DIST lookup; emit a clear install hint (`pip install -e '.[all]'`) then `sys.exit(2)`. |
| Marker-matrix included tomli/tzdata but bare venv couldn't install them | Initial design exited 2 ("coverage hole") whenever a dep that was in-scope via the matrix was absent from the current venv | A dep whose marker excludes the current interpreter (e.g. `tomli; python_version < "3.11"` on py3.14) is correctly absent — exiting 2 was a false failure blocking every CI run | Compute `installable_now` by evaluating the marker for the CURRENT env. Only FAIL LOUD when an installable-now dep has no metadata; skip-with-note when the marker excludes the current interpreter. |
| Pre-commit hook wrapping the license check | Added a pre-commit hook (`pixi run --environment default python3 scripts/check_license_compatibility.py`) to catch violations before push | The default dev env lacks the `.[all]` install, so the hook crashed on every local commit, blocking developers (POLA violation). Making it silent-pass would create a forbidden no-op. | DROP the pre-commit hook entirely. A check requiring a full extras install belongs ONLY in the CI job that installs `.[all]`. CI is the single authoritative gate for this check. |
| PSF in both PERMISSIVE and per-package ALLOWED_EXTRA_COPYLEFT | Put `Python-2.0` in the blanket `PERMISSIVE` set AND `PSF-2.0`/`Python-2.0` in `defusedxml`'s per-package entry | The per-package entry became dead code for the `Python-2.0` spelling (PERMISSIVE matched first), and the intended scoping — PSF allowed only for defusedxml — was silently defeated. Any OTHER package with `Python-2.0` would pass without review. | Keep each license identifier in ONE tier. PSF is per-package (NOTICE allows it only for defusedxml), so remove all PSF/Python-2.0 spellings from `PERMISSIVE`. Verify the alias/trove tables don't map other packages to those IDs. |
| Incomplete LGPL spellings in per-package allowlist | Initial ALLOWED_EXTRA_COPYLEFT for pygithub had only `LGPL-3.0` and `LGPL` (trove-derived spellings) | If a future PyGitHub release ships PEP 639 `License-Expression: LGPL-3.0-only` (which wins over the trove classifier in the resolution order), `is_compatible` returns False and the gate red-flags the very dep it's designed to allow | Include SPDX-canonical forms matching what PEP 639 would emit: `LGPL-3.0-only` and `LGPL-3.0-or-later` alongside `LGPL-3.0` and `LGPL`. Mirror the spellings already documented in NOTICE. |

## Results & Parameters

### Allowlist configuration

```python
# Tier 1 — blanket permissive (no per-package annotation required)
PERMISSIVE = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC"}

# Tier 2 — per-package copyleft/non-standard, NOTICE-justified
ALLOWED_EXTRA_COPYLEFT = {
    "pygithub":   {"LGPL-3.0", "LGPL-3.0-only", "LGPL-3.0-or-later", "LGPL"},
    "defusedxml": {"PSF-2.0", "Python-2.0"},
}
```

### Marker matrix

```python
PYTHON_VERSIONS = ["3.10", "3.13"]    # floor and ceiling of supported range
PLATFORMS = [
    ("linux",  "Linux"),
    ("win32",  "Windows"),
    ("darwin", "Darwin"),
]
RUNTIME_EXTRAS = {"all", "automation", "github", "nats", "toml", "xml", "schema"}
# "dev" is intentionally EXCLUDED — GPL dev tools are structurally unreachable from the dist
```

### Advisory / blocking exit-code rule

| Event | Exit code if violations found | Rationale |
|-------|-------------------------------|-----------|
| `pull_request` | 1 (blocking) | Prevents merging new incompatible deps |
| `push` to main, `schedule`, any other | 0 (advisory) | Logs warnings without breaking main for pre-existing issues |
| Package not installed / Requires-Dist empty / installable-now dep missing | 2 (always fatal) | A silent no-op is worse than a false failure |

### Acceptance checks

```bash
# a) Copyleft dep (GPL-3.0) in base install, running on a PR:
GITHUB_EVENT_NAME=pull_request python3 scripts/check_license_compatibility.py
# Expected: exit 1, stderr lists the offending package

# b) Same scenario on main:
GITHUB_EVENT_NAME=push python3 scripts/check_license_compatibility.py
# Expected: exit 0, stderr shows WARNING

# c) "MIT OR GPL-3.0" License-Expression:
# Expected: allowed (OR-semantics — MIT disjunct matches PERMISSIVE)

# d) PSF-2.0 on defusedxml:
# Expected: allowed (per-package ALLOWED_EXTRA_COPYLEFT)

# e) PSF-2.0 on an unknown package:
# Expected: rejected (not in PERMISSIVE; not in per-package allowlist)

# f) bare venv, Linux, py3.14, full `pip install -e .[all]`:
# Expected: tomli skipped (python_version < 3.11 marker, not installable now),
#           tzdata skipped (sys_platform == win32 marker, not installable now),
#           all other installed deps classified compatible, exit 0
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1219, PR #1252 | `scripts/check_license_compatibility.py` implemented with stdlib + `packaging`; two-tier allowlist; marker-matrix scope; FAIL LOUD semantics; advisory/blocking CI split; `[all]`-completeness regression test; all unit tests pass locally; bare-venv scenario reproduced |
