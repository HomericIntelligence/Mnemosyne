---
name: library-product-import-boundary-enforcement-test
license: BSD-3-Clause
description: "Enforce a library-vs-product import boundary with regression tests and CI install-string guards. Use when: (1) gating a heavy product subpackage (curses/pydantic/fcntl) behind an optional extra so base `import pkg` stays lean, (2) writing a test that asserts `import pkg` does not pull forbidden modules, (3) a CI import-surface test gives false failures because pytest itself preloads the forbidden dependency, (4) pip-based CI jobs collect product-layer tests and must install the product extra after moving deps out of base."
category: testing
date: 2026-07-01
version: "1.1.0"
user-invocable: false
verification: verified-ci
history: library-product-import-boundary-enforcement-test.history
tags: []
---

## Overview

When a heavy "product" layer (CLI/automation code with deps like `curses`,
`pydantic`, `fcntl`) is co-located in the same distribution as a lean utility
"library", the base `import pkg` surface must stay cheap. If product modules
leak into the base import path, every consumer of the library pays the cost of
loading the product's dependency tree, and the dependency arrow that an ADR
declares (product → library, never the reverse) silently rots.

This skill captures two complementary regression tests that enforce the
boundary mechanically, the CI install-string guard needed once product
dependencies move out of the base dependency set, plus the hard-won gotchas
that make them correct rather than flaky. It was learned driving
**ProjectHephaestus PR #997 (issue #711)** to green CI — documenting and
gating `hephaestus.automation` as an opt-in product layer behind a
`[automation]` optional extra, with the contract written in
`docs/adr/0001-automation-library-boundary.md` — then amended after
**ProjectHephaestus PR #1730 (issue #1728)** fixed CI collection failures from
pip jobs that did not install that extra.

The two tests:

1. **Import-surface test (subprocess-isolated)** — assert `import pkg` does NOT
   add forbidden modules to `sys.modules`. Runs in a fresh interpreter because
   pytest pre-pollutes `sys.modules`.
2. **Static import-grep test** — walk the library tree and flag any
   `from pkg.product` / `import pkg.product` line, proving the dependency arrow
   points only one way.

## When to Use

Use this skill when:

- You are gating a heavy product subpackage (`curses`/`pydantic`/`fcntl`-style
  deps) behind an optional extra so the base `import pkg` stays lean.
- You need a test that asserts `import pkg` does not pull forbidden modules into
  `sys.modules`.
- A CI import-surface test gives false failures because **pytest itself**
  preloads the forbidden dependency (e.g. `pydantic`) before your assertion
  runs.
- A dependency such as `pydantic` was intentionally moved from base
  dependencies into a product optional extra, and pip-based CI jobs now fail
  during pytest collection with `ModuleNotFoundError`.
- Workflow tests need to lock down `pip install -e ".[dev,...,automation]"`
  strings so future CI edits do not accidentally test product modules without
  product dependencies.
- You want to enforce a one-way dependency arrow declared in an ADR (product →
  library, never library → product) with a mechanical regression test rather
  than code review vigilance.

## Verified Workflow

The boundary is documented in an ADR (e.g. `docs/adr/0001-...`) and enforced by
two tests placed under the **mirrored** test path
(`tests/unit/validation/`, not `tests/unit/` root) per the
test-tree-mirrors-package convention.

### Quick Reference

| Goal | Technique | Critical detail |
| --- | --- | --- |
| Assert `import pkg` stays lean | Subprocess import-surface test | Run in `sys.executable -c`, parse a printed `LEAKED:` line — never in-process |
| Forbidden modules list | `curses`, `pydantic`/`pydantic.*`, `pkg.product.*` | NEVER include `fcntl` — stdlib `pathlib` loads it transitively on POSIX |
| One-way dependency arrow | Static grep over `LIB_ROOT.rglob("*.py")` | Skip paths whose parts contain the product package name |
| Gate heavy deps | `[project.optional-dependencies] automation = [...]` | Don't duplicate base deps (e.g. `tzdata`) into the extra |
| CI collectors for product tests | `pip install -e ".[dev,schema,automation]"` / `pip install -e ".[dev,automation]"` | Add the product extra to pip jobs that import product modules; do not re-add the dep to base |
| Keep docs honest | ADR / test-docstring / pyproject must agree | Verify enumerated facts (script counts) against the actual codebase |

**1. Subprocess-isolated import-surface test.** Run the import in a fresh
interpreter and parse a printed marker. Doing this in-process is meaningless:
pytest already imports `pydantic`, so `sys.modules` is pre-polluted and the
assertion false-passes.

```python
import subprocess
import sys

code = (
    "import sys\n"
    "before = set(sys.modules)\n"
    "import hephaestus  # noqa: F401\n"
    "after = set(sys.modules)\n"
    "new = after - before\n"
    "leaked = sorted(m for m in new if m == 'curses' or m == 'pydantic' "
    "or m.startswith('pydantic.') or m.startswith('hephaestus.automation'))\n"
    "print('LEAKED:' + ','.join(leaked))\n"
)
result = subprocess.run(
    [sys.executable, "-c", code],
    check=True,
    capture_output=True,
    text=True,
)
leaked_line = next(
    line for line in result.stdout.splitlines() if line.startswith("LEAKED:")
)
leaked = [m for m in leaked_line[len("LEAKED:"):].split(",") if m]
assert not leaked, f"import hephaestus leaked forbidden modules: {leaked}"
```

**2. Static import-grep test.** Walk the library tree, skip the product
subpackage itself, and flag any direct import of the product layer. This proves
the arrow points only one way (`automation → library`, never the reverse).

```python
from pathlib import Path
import hephaestus

LIB_ROOT = Path(hephaestus.__file__).parent
violations = []
for py in LIB_ROOT.rglob("*.py"):
    if "automation" in py.relative_to(LIB_ROOT).parts:
        continue  # the product layer may import the library; skip it
    for lineno, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if s.startswith(("from hephaestus.automation", "import hephaestus.automation")):
            violations.append(f"{py.relative_to(LIB_ROOT)}:{lineno}: {s}")
assert not violations, "library imports product layer:\n" + "\n".join(violations)
```

**3. Gate the heavy deps behind an optional extra.** In `pyproject.toml`, the
product layer's dependencies install only via `pkg[automation]`:

```toml
[project.optional-dependencies]
automation = ["pydantic>=2", ...]
```

The base `import pkg` surface stays lean; `pip install pkg[automation]` pulls
the product deps.

**4. The `fcntl` stdlib transitive-load trap (key gotcha).** `fcntl` cannot be
in the forbidden list. Python stdlib `pathlib` transitively loads `fcntl` on
POSIX, so asserting `import pkg` doesn't load `fcntl` gives a
platform-dependent false failure. The contract is about modules the package's
code imports **directly** (`curses`, `pydantic`), not stdlib transitive loads.
Keep the ADR Consequences section and the test docstring consistent — remove
`fcntl` from both so the documentation matches the actual assertion.

**5. Doc / test / config consistency (review findings).**

- ADR enumerated facts must match reality: the ADR listed seven console scripts
  including a non-existent `hephaestus-audit-prs`; the actual count is six.
  Verify enumerated facts against the codebase before claiming them.
- Don't add redundant deps to the optional extra: `tzdata` was already a base
  dependency for library code, so it did not belong in `[automation]`.
- Place the new tests under the mirrored path `tests/unit/validation/`, not
  `tests/unit/` root, per the test-structure-mirrors-package requirement.

**6. Keep pip-based CI collectors in sync with the optional extra.** If pytest
collects product-layer tests, importing those modules during collection is
enough to require the product dependencies. Once a dependency like `pydantic`
has intentionally moved from base into `[automation]`, the fix is to add the
extra to those CI install commands, not to put the dependency back in base.

ProjectHephaestus PR #1730 used these exact workflow strings:

```yaml
# .github/workflows/test.yml unit/matrix jobs
pip install -e ".[dev,schema,automation]"

# .github/workflows/_required.yml unit-tests job
pip install -e ".[dev,schema,automation]"

# .github/workflows/_required.yml integration job
pip install -e ".[dev,automation]"
```

Guard the strings with workflow regression tests so the install contract fails
locally before CI collection fails:

```bash
pixi run pytest tests/unit/ci/test_workflows.py::TestAutomationExtraInstall -v --override-ini=addopts=
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| In-process import-surface check | Asserted forbidden modules absent from `sys.modules` inside the pytest process | pytest preloads `pydantic`, so `sys.modules` is already polluted → assertion meaningless / false-passing | Run the check in a fresh interpreter via `subprocess.run([sys.executable, "-c", ...])` and parse a printed marker |
| Forbid `fcntl` in the surface assertion | Added `fcntl` to the leaked-module list | stdlib `pathlib` transitively loads `fcntl` on POSIX → platform-dependent false failure | Only forbid modules the package imports directly (`curses`, `pydantic`); exclude stdlib transitive loads |
| `tzdata` in `[automation]` extra | Listed `tzdata` under the optional automation extra | `tzdata` was already a base dependency for library code → redundant | Don't duplicate base deps into optional extras; audit the base list first |
| Tests at `tests/unit/` root | Placed new boundary tests in `tests/unit/` directly | Project requires the test tree to mirror package structure (`validation/`) | Place enforcement tests under the mirrored subdir, e.g. `tests/unit/validation/` |
| ADR listed seven scripts | ADR enumerated console scripts including non-existent `hephaestus-audit-prs` | Drifted from reality (six scripts) → review caught it | Verify enumerated facts in ADRs against the actual codebase before claiming them |
| CI jobs kept installing only `.[dev,schema]` / `.[dev]` | Main moved `pydantic` out of base into `[automation]`, but unit/matrix jobs still installed `pip install -e ".[dev,schema]"` and integration installed `pip install -e ".[dev]"` | Pytest collection imported `hephaestus.automation.*` and failed with `ModuleNotFoundError: No module named 'pydantic'` | Add the product extra to every pip-based CI job that collects product-layer tests |
| Re-adding `pydantic` to base | Considered treating CI failure as a missing base dependency | That would undo the intentional library/product boundary and make lean base installs pull product deps again | Preserve the boundary; fix the CI environment that exercises product modules |
| Targeted pytest without clearing repo addopts | Ran a partial pytest command without `--override-ini=addopts=` | The repo coverage gate tripped even though the focused workflow test was the intended verification | For focused local verification in this repo, use `--override-ini=addopts=` |
| First pixi run under sandbox DNS limits | `pixi run pytest ...` failed with `curl: (6) Could not resolve host: github.com` | Dependency resolution needed network access outside the sandbox | Re-run the same verification with network approval; do not treat DNS failure as test failure |

## Results & Parameters

**Outcome:** ProjectHephaestus PR #997 (issue #711) merged green on 2026-06-12.
The `hephaestus.automation` product layer is now documented in
`docs/adr/0001-automation-library-boundary.md`, gated behind the
`[automation]` optional extra, and enforced by two regression tests under
`tests/unit/validation/`. ProjectHephaestus PR #1730 (issue #1728) later
extended the same boundary to CI: pip-based workflow jobs that collect
automation tests install `[automation]`, and workflow regression tests lock the
install strings down.

**Parameters / knobs:**

| Parameter | Value used | Notes |
| --- | --- | --- |
| Forbidden modules | `curses`, `pydantic`, `pydantic.*`, `pkg.product.*` | Modules the package imports *directly*; never stdlib transitive loads |
| Excluded from forbidden list | `fcntl` | `pathlib` loads it on POSIX — would cause platform-dependent false failure |
| Import-surface isolation | `subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)` | Fresh interpreter; parse the `LEAKED:` line from stdout |
| Grep skip rule | `"automation" in py.relative_to(LIB_ROOT).parts` | Product layer may import library; skip it |
| Optional extra | `[project.optional-dependencies] automation = [...]` | Heavy deps install only via `pkg[automation]` |
| Test location | `tests/unit/validation/` | Mirror the package structure, not `tests/unit/` root |
| Unit/matrix CI install | `pip install -e ".[dev,schema,automation]"` | Required when unit collection imports automation modules and schema tests still need schema deps |
| Required unit install | `pip install -e ".[dev,schema,automation]"` | Same collection boundary in `_required.yml` |
| Required integration install | `pip install -e ".[dev,automation]"` | Integration jobs import automation but do not need schema extra |

**ProjectHephaestus PR #1730 verification:**

```text
pixi run pytest tests/unit/ci/test_workflows.py::TestAutomationExtraInstall -v --override-ini=addopts=
# 2 passed

pixi run pytest tests/unit/ci/test_workflows.py tests/unit/automation/test_claude_timeouts.py tests/unit/automation/test_timeout_cli_threading.py tests/unit/automation/test_package_imports.py -v --override-ini=addopts=
# 168 passed

gh pr checks 1730
# all checks passed
```

**Two short test bodies (verbatim).** Import-surface check:

```python
code = (
    "import sys\n"
    "before = set(sys.modules)\n"
    "import hephaestus  # noqa: F401\n"
    "after = set(sys.modules)\n"
    "new = after - before\n"
    "leaked = sorted(m for m in new if m == 'curses' or m == 'pydantic' "
    "or m.startswith('pydantic.') or m.startswith('hephaestus.automation'))\n"
    "print('LEAKED:' + ','.join(leaked))\n"
)
result = subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)
# parse the LEAKED: line, assert empty
```

Static grep core:

```python
LIB_ROOT = Path(hephaestus.__file__).parent
for py in LIB_ROOT.rglob("*.py"):
    if "automation" in py.relative_to(LIB_ROOT).parts:
        continue
    for lineno, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if s.startswith(("from hephaestus.automation", "import hephaestus.automation")):
            violations.append(...)
assert not violations
```
