---
name: license-compatibility-ci-gate-pip-licenses
description: "Plan a machine-enforced license-compatibility CI gate / NOTICE-drift / SPDX-allowlist check for a pixi-based Python repo using the stdlib (importlib.metadata + packaging) instead of pip-licenses. Use when: (1) building a CI job that blocks PRs introducing license-incompatible dependencies, (2) wiring such a gate as a pixi task that CI and pre-commit both invoke, (3) a license gate false-fails the clean tree because an env scan surfaced GPL dev tools (yamllint, bats-core) that NOTICE permits dev-only, (4) a metadata-reading gate silently passes because the package isn't installed or a runtime extra (nats-py) is absent, (5) license metadata is inconsistent across packages (trove classifier vs License-Expression vs freeform License) and an exact-string match false-fails, (6) deciding how to scope the gate to DISTRIBUTED deps (Requires-Dist) excluding the dev extra, (7) a platform-gated dependency (tzdata on Windows) is silently dropped from a Linux-runner scan."
category: ci-cd
date: 2026-06-12
version: "1.0.0"
user-invocable: false
verification: unverified
tags: []
---
# License-Compatibility CI Gate (stdlib importlib.metadata, distributed-scope, pixi-wired)

A planning-stage design for a license-compatibility CI gate on a pixi-managed Python
repo. The gate enumerates only the **distributed** dependency set from the package's own
`Requires-Dist` metadata (excluding the `dev` extra), resolves each dependency's license
across three metadata fields, and checks it against a two-tier allowlist that mirrors
`NOTICE`. It uses the Python standard library (`importlib.metadata` + `packaging`) rather
than `pip-licenses`, scopes to what the project *ships* (not the whole CI environment),
wires itself as a **top-level pixi task** that delegates into the feature env, and is
engineered to **fail loud** rather than silently pass when its inputs are missing.

## Overview

| Item | Details |
| ------ | --------- |
| Objective | Block PRs that add a license-incompatible *distributed* dependency, without false-failing on dev-only copyleft tools (yamllint, bats-core) that NOTICE permits, and without silently passing when metadata/extras are absent |
| Scope | Dependency enumeration from `Requires-Dist`, three-field license resolution, two-tier (permissive + per-package copyleft) allowlist, top-level pixi task delegating to the feature env, isolated advisory-on-main/blocking-on-PR CI job + pre-commit hook |
| Approach | stdlib `importlib.metadata` + `packaging.requirements` over `pip-licenses`; distributed-scope over environment scan; fail-loud over silent-pass; `pip install -e ".[all]"` for coverage |
| Outcome | A gate that passes the current clean tree, fails on genuinely incompatible shipped deps, and errors (never no-ops) when blind |
| Verification | unverified |

> **Warning:** This skill records a **plan** (ProjectHephaestus issue #1219, re-planned
> twice after reviewer NOGOs: v1 pip-licenses, v2 stdlib metadata, and this v3 adding pixi
> task-wiring + fail-loud + `[all]` coverage). It was **never executed** — no CI run, no
> tests, no gate invocation. Treat every claim as a hypothesis until CI confirms.

## When to Use

1. You are building a CI job that blocks PRs introducing license-incompatible dependencies
   in a pixi Python repo with a `NOTICE` file.
2. You need to wire that gate as a **pixi task** that both CI and a pre-commit hook invoke,
   and you are unsure whether the task is visible across pixi environments.
3. A license gate false-fails the clean tree because an env-wide scan surfaced GPL dev tools
   (yamllint, bats-core) that `NOTICE` explicitly permits as dev-only.
4. A metadata-reading gate silently passes (`exit 0`) because the package isn't installed by
   dist name, `Requires-Dist` is empty, or a runtime extra (e.g. `nats-py`) is not installed.
5. License metadata is inconsistent across packages (trove `Classifier ::` vs
   `License-Expression` vs freeform `License`) and an exact-string match false-fails a package.
6. You are deciding how to scope the gate to the **distributed** deps (`Requires-Dist`)
   excluding the `dev` extra.
7. A platform-gated dependency (e.g. `tzdata` under `platform_system == 'Windows'`) is
   silently dropped from a Linux-runner scan.

## Verified Workflow

**Verification did NOT occur.** This skill is plan-stage only — nothing below was executed,
no CI ran, no tests passed. This heading exists solely to satisfy the marketplace validator's
required-section check. The actual, honest content lives under **## Proposed Workflow** below
and is explicitly marked as an unvalidated hypothesis. Do not read the presence of this
heading as evidence of validation.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until
> CI confirms.

### Quick Reference

```toml
# pixi.toml — define the gate as a TOP-LEVEL task that DELEGATES into the feature env.
# A task under [feature.lint.tasks] is ONLY visible in envs that include `lint`;
# `pixi run --environment default <task>` would fail "command not found".
# Mirror the repo's existing cross-env delegation pattern (pixi.toml:18):
#   audit = "pixi run --environment lint pip-audit"
[tasks]
license-scan = "pixi run --environment lint python3 scripts/check_license_compatibility.py"
# CI and pre-commit then call `pixi run license-scan` with NO --environment flag.
```

```python
# Enumerate DISTRIBUTED deps from the package's own metadata (NOT an env scan).
# FAIL LOUD if metadata is missing — a metadata-reading gate that finds nothing must NOT exit 0.
import sys
import importlib.metadata as im
from packaging.requirements import Requirement

DIST_NAME = "HomericIntelligence-Hephaestus"      # the installed dist name
RUNTIME_EXTRAS = {"all", "automation", "github", "nats", "toml", "xml", "schema"}  # NO dev

reqs = im.metadata(DIST_NAME).get_all("Requires-Dist") or []
if not reqs:                                       # empty == teeth-less no-op gate
    sys.exit(2)                                    # blindness is an ERROR, not "all clear"

distributed = []
for raw in reqs:
    r = Requirement(raw)
    if r.marker is None or _marker_ok(r.marker):   # base dep OR any-satisfiable across matrix
        distributed.append(r.name)

for name in distributed:
    try:
        meta = im.metadata(name)                   # do NOT `continue` past this
    except im.PackageNotFoundError:
        sys.exit(2)                                # declared-but-uninstalled == coverage gap
```

```python
# Marker evaluation needs a PLATFORM matrix — {extra, python_version} alone drops platform-gated deps.
_PY = ("3.10", "3.13")
_PLAT = (("linux", "Linux"), ("win32", "Windows"), ("darwin", "Darwin"))

def _marker_ok(marker) -> bool:
    for e in RUNTIME_EXTRAS:
        for pyver in _PY:
            for sys_platform, platform_system in _PLAT:
                if marker.evaluate({
                    "extra": e, "python_version": pyver,
                    "sys_platform": sys_platform, "platform_system": platform_system,
                }):
                    return True          # ANY-satisfiable == in scope
    return False
```

```python
# Resolve a license across THREE fields in priority order — exact-string match is wrong.
def resolve_license(meta) -> str:
    if expr := meta.get("License-Expression"):                 # 1. already SPDX
        return expr
    for c in meta.get_all("Classifier") or []:                 # 2. OSI trove tail via table
        if c.startswith("License :: OSI Approved ::"):
            tail = c.split("::")[-1].strip()
            if tail in TROVE_TO_SPDX:
                return TROVE_TO_SPDX[tail]
    if free := meta.get("License"):                            # 3. freeform via alias table
        return LICENSE_ALIASES.get(free.strip(), free.strip())
    return "UNKNOWN"

# OR-expressions are COMPATIBLE if ANY disjunct is permissive. Do NOT reject on substring.
def is_permissive(spdx: str) -> bool:
    return any(d.strip() in PERMISSIVE for d in spdx.split(" OR "))
```

### Detailed Steps

#### 1. Wire the gate as a TOP-LEVEL pixi task that delegates into the feature env (the #1 trap)

A task defined under `[feature.lint.tasks]` is **only visible in environments that include
the `lint` feature**. Invoking it from another env fails:

```text
$ pixi run --environment default sast
sast: command not found        # sast lives in [feature.lint.tasks]; invisible in `default`
```

(VERIFIED during planning.) The fix is to declare the gate as a **top-level `[tasks]`** entry
(visible in every environment) that **delegates** to the feature env — exactly mirroring the
repo's existing pattern at `pixi.toml:18`:

```toml
audit = "pixi run --environment lint pip-audit"
```

Then CI and the pre-commit hook call `pixi run license-scan` with **no** `--environment`
flag. **Before wiring any pixi task into CI + pre-commit, grep how existing cross-env tasks
(like `audit`) are declared — do not assume a feature task is globally runnable.**

#### 2. Make the gate FAIL LOUD — never silent-pass

A gate that enumerates deps from `importlib.metadata.metadata(DIST).get_all("Requires-Dist")`
returns an **empty list** if the package isn't installed under its dist name or metadata is
absent → the scan finds zero deps → `exit 0` → a teeth-less gate that **always passes**. Two
loud guards:

- `sys.exit(2)` when `Requires-Dist` is empty/missing.
- `sys.exit(2)` when a declared distributed dep has **no resolvable metadata** — do **not**
  `continue` past `PackageNotFoundError`, which silently drops coverage.

Lock both with unit tests asserting `SystemExit.code == 2`. **Any gate whose "all clear" path
is reachable when its inputs are missing is a false-confidence gate; make blindness an error.**

#### 3. Reconcile installed-set vs declared-set; install `[all]` for coverage

VERIFIED during planning: in the local `default` pixi env, `nats-py` (the `nats` extra) is
**not** installed while `pygithub` / `jsonschema` / `defusedxml` are. A scan that only
classifies *installed* packages silently skips uninstalled runtime extras — exactly the
copyleft-bearing ones the gate targets. Fix:

- The CI job must `pip install -e ".[all]"` (the repo's established extra-install pattern at
  `test.yml:92` / `_required.yml:543/556`) **before** scanning.
- The loud-failure guard from step 2 then turns any **still-missing declared dep** into a hard
  error.

**A license/dep gate must reconcile the DECLARED distributed set (from `Requires-Dist`)
against the INSTALLED set and fail on the gap, not scan whatever happens to be present.**

#### 4. Evaluate markers across a platform matrix

`Requirement.marker.evaluate({"extra": e, "python_version": v})` omits platform vars, so a dep
gated `platform_system == 'Windows'` (e.g. `tzdata`) evaluates `False` on a Linux runner and is
**dropped** from the scanned set — a silent platform blind spot. Evaluate each marker across a
small `{python_version} × {sys_platform/platform_system}` matrix and treat **any-satisfiable**
as in-scope. **When using markers to select a dependency subset, evaluate permissively across
platforms/pythons or you silently exclude platform-gated deps.**

#### 5. Scope to distributed deps, never an env scan (carried from v1→v2)

The v1 design ran `pip-licenses --with-system`, which scans the whole installed environment and
surfaced GPL **dev** tools (`yamllint`, `bats-core`) that `NOTICE` permits dev-only — so the
gate **false-failed the clean tree** (reviewer CRITICAL). Enumerate only the **distributed** set
from `Requires-Dist`: base deps (`marker is None`) plus runtime extras, **excluding the `dev`
extra** (so GPL dev tools are structurally unreachable). `packaging` is normally already a base
dep, so this adds no new dependency.

#### 6. Resolve licenses across three fields (metadata is inconsistent) (carried)

Verified live during planning, license metadata is *not* uniform — `pygithub` exposes **only**
a trove tag (no SPDX expr, no freeform). A robust resolver checks three fields in priority
order: (1) `License-Expression` (already SPDX), (2) the OSI trove `Classifier ::` tail mapped
via `TROVE_TO_SPDX`, (3) freeform `License` mapped via `LICENSE_ALIASES`. The v1 bug was an
exact-string match against one assumed spelling.

#### 7. OR-expression semantics + two-tier allowlist (carried)

`MIT OR GPL-3.0` is **compatible** — split on ` OR ` and pass if **any** disjunct is permissive
(the v1 inverted-OR bug rejected it). Allowlist is two-tier:

- **PERMISSIVE** (any package): `{MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, ISC, Python-2.0}`.
- **ALLOWED_EXTRA_COPYLEFT** (per-package, NOTICE-justified): `{pygithub: {LGPL-3.0, LGPL},
  defusedxml: {PSF-2.0, Python-2.0}}`.

PSF must **not** be blanket-permissive (a v1 bug) — scope LGPL/PSF exceptions per package so a
new copyleft dep is still caught.

#### 8. Test against REAL metadata; unmapped license fails loud (carried)

Call `resolve_license(importlib.metadata.metadata(pkg))` on actually-installed packages to pin
the true schema — synthetic-only tests with author-assumed spellings are a tautology. An unmapped
license resolves to its raw string and (if not permissive) **false-fails** with a hint to extend
the tables — a deliberate false-fail over false-pass for a gate.

#### 9. CI + pre-commit wiring (carried)

- **Isolated sibling CI job** — one scan's failure must not block other CI checks.
- **Advisory on main, blocking on PR** — branch on `GITHUB_EVENT_NAME`: exit `1` on
  `pull_request`, exit `0` otherwise. (Coverage/blindness errors exit `2` **always**.)
- **Edit `.github/workflows/*.yml` via `sed`/append, not the Edit tool** — the pre-commit
  security hook blocks Edit-tool writes to workflow files.
- **Pre-commit hook** scoped `files: ^(pyproject\.toml|pixi\.toml|pixi\.lock|NOTICE)$`,
  `pass_filenames: false`.

### Risks / most-uncertain assumptions (reviewer focus)

1. **pip-installing extras into a pixi-locked env may desync.** The plan does
   `pip install -e ".[all]"` into the pixi `lint` env, but `setup-pixi` runs with
   `locked: true`. Whether pip and pixi co-managing the same site-packages is stable on the
   runner is **unverified** — they can desync.
2. **Nested `pixi run` is assumed but unverified.** The top-level task delegates
   `pixi run --environment lint python3 ...`, while the CI job *also* does
   `pixi run --environment lint pip install`. Nesting `pixi run` inside a step that already set
   up the `lint` env is assumed to work but not validated end-to-end.
3. **Hand-listed platform matrix in `_marker_ok`.** It enumerates linux/win32/darwin only; an
   exotic marker var (`implementation_name`, `platform_machine`) still evaluates against
   defaults and could mis-select a dep.
4. **`[all]`-aggregation coupling.** The plan assumes `[all]` aggregates **every** runtime
   extra; if a runtime extra is omitted from `[all]` in `pyproject`, its deps are never
   installed and the loud-failure guard will (correctly) **fail CI** — a pyproject-maintenance
   coupling the design relies on.
5. **Line-number anchors will drift.** `pixi.toml:18/104`, `security.yml:19-55`,
   `_required.yml:543/556`, `test.yml:92`, `.pre-commit-config.yaml:179-185`, `NOTICE:18/51/74`
   are plan-time reads.
6. **`DIST_NAME` must match exactly.** `HomericIntelligence-Hephaestus` must match the installed
   dist name for `importlib.metadata`; only observed locally.

### Externals relied on without full verification

- That **pip-installing extras into a pixi-locked env is stable on CI**.
- That **nested `pixi run`** works as composed (task delegates to `lint` inside a step that
  already set up `lint`).
- That `packaging.requirements.Requirement` / `Marker.evaluate` is available at the pinned
  `packaging` floor.
- SPDX OR-expression spellings beyond the one observed (`Apache-2.0 OR BSD-2-Clause`).
- That `[all]` truly aggregates **all** runtime extras.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Attempt 1 | Defined the gate task under `[feature.lint.tasks]`, invoked with `--environment default` | `command not found` — a feature task is invisible in environments that don't include that feature | Use a top-level `[tasks]` entry that **delegates** into the feature env, like `audit = "pixi run --environment lint pip-audit"` (pixi.toml:18) |
| Attempt 2 | Metadata-reading scan returned `[]` when the package/metadata was absent | The scan found zero deps → `exit 0` → a teeth-less gate that always passes | `sys.exit(2)` on empty `Requires-Dist` **and** on any uninstalled declared dep — make blindness an error |
| Attempt 3 | Scanned only the *installed* packages | Uninstalled runtime extras (e.g. `nats-py`) were silently skipped — the copyleft deps the gate targets | CI installs `.[all]` first, and the loud-failure guard hard-fails on any still-missing declared dep |
| Attempt 4 | `marker.evaluate` with only `{extra, python_version}` | A platform-gated dep (`tzdata`, Windows) evaluates False on the Linux runner and is dropped | Evaluate markers across a `python × platform` matrix; any-satisfiable == in scope |
| Attempt 5 | `pip-licenses --with-system` environment-wide scan (v1) | Surfaces GPL **dev** tools (yamllint, bats-core) that NOTICE permits dev-only → gate false-fails the clean tree | Scope to **distributed** deps via `Requires-Dist`; exclude the `dev` extra; prefer stdlib `importlib.metadata` |
| Attempt 6 | Exact-string license match against one assumed SPDX spelling (v1) | pygithub exposes only a trove classifier (no SPDX, no freeform) → false-fails | Resolve across `License-Expression` → trove `Classifier` (via `TROVE_TO_SPDX`) → freeform `License` (via `LICENSE_ALIASES`) |
| Attempt 7 | Reject if any copyleft substring appears anywhere in the expression (v1) | `MIT OR GPL-3.0` (permissive side choosable) wrongly rejected — inverted OR | Split on ` OR ` and pass if **any** disjunct is permissive |
| Attempt 8 | Put PSF in the blanket-permissive set (v1) | Any future PSF-licensed dep would silently pass | Per-package `ALLOWED_EXTRA_COPYLEFT` map (pygithub→LGPL, defusedxml→PSF), not a blanket entry |

## Results & Parameters

### Proposed parameters (all UNVERIFIED — plan stage)

```text
top-level task        license-scan = "pixi run --environment lint python3 scripts/check_license_compatibility.py"
DIST_NAME             = "HomericIntelligence-Hephaestus"   # importlib.metadata target
RUNTIME_EXTRAS        = {all, automation, github, nats, toml, xml, schema}   # NO dev
PERMISSIVE            = {MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, ISC, Python-2.0}
ALLOWED_EXTRA_COPYLEFT= {pygithub: {LGPL-3.0, LGPL}, defusedxml: {PSF-2.0, Python-2.0}}
marker matrix         _PY = (3.10, 3.13) × _PLAT = (linux/Linux, win32/Windows, darwin/Darwin)
exit codes            2 = blind / coverage-gap (ALWAYS)
                      1 = violation on PR (blocking)
                      0 = violation on main (advisory)
CI install step       pip install -e ".[all]"   (test.yml:92 / _required.yml:543/556 pattern)
```

### CI job (proposed)

```text
job timeout-minutes : 10
triggers            : pull_request + push:[main] + schedule + workflow_dispatch
invocation          : pixi run license-scan   (NO --environment flag; top-level task delegates)
install step        : pip install -e ".[all]" before scanning (coverage)
exit code           : 2 always on blind/coverage-gap; else 1 on pull_request, 0 otherwise
isolation           : sibling job (independent of other CI checks)
workflow edits      : via sed/append, NOT the Edit tool (pre-commit security hook blocks it)
```

### Pre-commit hook (proposed)

```text
files          : ^(pyproject\.toml|pixi\.toml|pixi\.lock|NOTICE)$
pass_filenames : false
invocation     : pixi run license-scan   (top-level task; no --environment flag)
```

### Resolver field priority

```text
1. License-Expression   (already SPDX)            e.g. "Apache-2.0 OR BSD-2-Clause", "MIT"
2. Classifier tail      via TROVE_TO_SPDX table    e.g. "MIT License" -> MIT, LGPL tag -> LGPL
3. License (freeform)   via LICENSE_ALIASES table  e.g. "PSFL" -> PSF-2.0
```

### Observed metadata schema (live, during planning)

```text
pyyaml     : Classifier "License :: OSI Approved :: MIT License"  (trove only)
packaging  : License-Expression "Apache-2.0 OR BSD-2-Clause"      (SPDX only)
pydantic   : License-Expression "MIT"                             (SPDX only)
pygithub   : Classifier "...LGPL..." tag                          (trove only; NO SPDX/freeform)
defusedxml : License "PSFL"                                       (freeform)
```

### Observed install gap (live, during planning)

```text
default pixi env: pygithub/jsonschema/defusedxml INSTALLED; nats-py (nats extra) NOT installed
=> scan must `pip install -e ".[all]"` then loud-fail on any still-missing declared dep
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1219 plan R2 (second re-plan after NOGO; planning only, not executed) | unverified — plan stage; adds pixi-wiring + loud-failure + [all]-coverage to v2 stdlib approach |
| ProjectHephaestus | Issue #1219 plan R1 (first re-plan after NOGO; planning only) | unverified — superseded v1 pip-licenses with stdlib importlib.metadata distributed-scope |

## References

- `importlib.metadata` (stdlib) — `metadata(dist).get_all("Requires-Dist")`, three license fields
- `packaging.requirements.Requirement` / `packaging.markers.Marker.evaluate`
- pixi cross-env task delegation pattern — `audit = "pixi run --environment lint pip-audit"` (pixi.toml:18)
- ProjectHephaestus issue #1219 — license-compatibility CI gate (planning)
- ProjectMnemosyne PR #2355 — v1 pip-licenses planning skill (superseded)
- ProjectMnemosyne PR #2361 — v2 stdlib metadata planning skill (superseded by this v3)
- [SPDX License List](https://spdx.org/licenses/)
- [PyPA core metadata spec](https://packaging.python.org/en/latest/specifications/core-metadata/)
