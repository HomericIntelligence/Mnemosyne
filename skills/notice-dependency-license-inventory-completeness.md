---
name: notice-dependency-license-inventory-completeness
description: "When a hand-maintained NOTICE / license-inventory / attribution doc claims to be the COMPLETE list of runtime dependencies, it silently drifts from pyproject.toml's [project].dependencies — platform-conditional deps (e.g. tzdata; platform_system=='Windows') get missed because they only ship to one platform. Use when: (1) auditing or fixing a NOTICE/THIRD-PARTY/SBOM/attribution file for completeness, (2) any doc-vs-pyproject inventory that can drift, (3) planning a fix that should add a guard test diffing the doc against the dependency source of truth, (4) writing a license entry for tzdata or other IANA/public-domain-data packages."
category: documentation
date: 2026-06-12
version: "1.1.0"
history: notice-dependency-license-inventory-completeness.history
user-invocable: false
verification: unverified
tags:
  - notice
  - license-inventory
  - third-party
  - attribution
  - sbom
  - pyproject
  - platform-conditional-deps
  - pep-508
  - pep-503
  - tzdata
  - drift-detection
  - guard-test
---

# NOTICE / License-Inventory Completeness vs pyproject Dependencies

A hand-maintained NOTICE / license-inventory / attribution document that claims to be the
*complete* list of runtime dependencies silently drifts from the real source of truth —
`pyproject.toml [project].dependencies`. The highest-risk drift is **platform-conditional
dependencies** (PEP 508 environment markers like `; platform_system == 'Windows'`), because
they only install on one platform and are trivial to overlook in a manual inventory.

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-12 |
| **Objective** | Plan a fix for a NOTICE file that omitted a platform-conditional runtime dependency (`tzdata; platform_system == 'Windows'`) while claiming to be a complete inventory, and prevent silent recurrence |
| **Outcome** | Plan produced (and hardened in R1 after a plan-review NOGO): add the missing entry in the file's existing inline-parenthetical style, **leading with the PyPI-verified SPDX token** (`tzdata` → `Apache-2.0`), + add a regression guard test diffing `[project].dependencies` against the NOTICE inventory section using **exact PEP 503-normalized name matching** (not substring) |
| **Verification** | unverified — planning learning; the proposed guard-test workflow has not been executed in CI. The tzdata *license string itself* IS verified (PyPI `info.license == "Apache-2.0"` + bundled `licenses/LICENSE_APACHE`) |

## When to Use

- Auditing or fixing a `NOTICE` / `THIRD_PARTY_LICENSES` / `SBOM` / attribution file that
  asserts it is the COMPLETE runtime-dependency inventory
- Any documentation-vs-`pyproject.toml` inventory that can silently drift over time
- Planning a fix that should also add a regression GUARD TEST diffing the doc against the
  dependency source of truth, so the gap cannot recur
- Writing a license-attribution entry for `tzdata` or other IANA / public-domain-data
  packages (the timezone-data wheel, etc.)
- A dependency is **platform-conditional** (`; platform_system == 'Windows'`,
  `; python_version < '3.11'`) and may be missing from the manual inventory because it only
  ships to one platform

## The Core Problem

A NOTICE / license-inventory file that asserts it is a *complete* runtime-dependency
inventory is, in practice, a doc that drifts from `pyproject.toml [project].dependencies`.
The highest-risk drift is **platform-conditional dependencies** declared with PEP 508
environment markers, because they install on only one platform and are easy to miss when a
human eyeballs the dependency list on their own machine.

**Concrete instance (ProjectHephaestus):**

- `pyproject.toml [project].dependencies` declared `tzdata; platform_system == 'Windows'`
- `NOTICE` listed only `packaging`, `pyyaml`, and `pydantic` — `tzdata` was absent
- On Linux/macOS the omission is invisible (`tzdata` never installs there), so a developer
  reviewing the NOTICE on POSIX would never notice the gap

`tzdata` is the Windows companion to the project's POSIX-only import guards
(`curses` / `fcntl` / `grp`): it packages the IANA tz database so `zoneinfo.ZoneInfo` can
resolve timezones on Windows, which CPython does not bundle there (POSIX bundles it).

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until
> CI confirms. Verification level: unverified.

### Quick Reference

```bash
# 1. Enumerate the REAL runtime deps (the source of truth), markers and all.
python3 - <<'PY'
import tomllib
with open("pyproject.toml", "rb") as f:
    data = tomllib.load(f)
for spec in data["project"]["dependencies"]:
    print(spec)   # e.g. "tzdata; platform_system == 'Windows'"
PY

# 2. Diff against what the NOTICE inventory section actually lists.
#    Platform-conditional deps (anything after a ';' marker) are the prime suspects.
grep -nE "platform_system|python_version|sys_platform" pyproject.toml

# 3. VERIFY the license token against ground truth BEFORE writing the legal line.
#    A NOTICE is a legal attribution doc — never paste a license string from memory.
curl -s https://pypi.org/pypi/tzdata/json | \
  python3 -c "import sys,json;print(json.load(sys.stdin)['info']['license'])"
#    -> "Apache-2.0"   (cross-check the wheel's bundled LICENSE: licenses/LICENSE_APACHE)

# 4. Add the missing entry to NOTICE following the file's EXISTING style, LEADING
#    with the SPDX identifier (Apache-2.0), demoting public-domain IANA data to a
#    parenthetical. Match the inline parenthetical convention; do NOT invent a subsection.

# 5. Add/locate a guard test next to an existing pyproject-parsing test
#    (e.g. the dependency-floor-consistency test). Use EXACT PEP 503-normalized
#    SET membership — never substring. Run it.
pytest tests/unit -k "notice or license_inventory or dependency" -v

# 6. Prove BOTH presence AND the license token (not just the name):
grep -nE "tzdata +Apache-2\.0" NOTICE   # not just `grep tzdata NOTICE`
```

### Fix Pattern

**(a) Add the missing entry in the file's existing conventions, LEADING with the
PyPI-verified SPDX token.** A NOTICE is a legal attribution document, so the license string
is load-bearing: lead the entry with the **SPDX identifier** that matches the file's house
style (e.g. `Apache-2.0`, `MIT`, `Apache-2.0 OR BSD-2-Clause`) — never a prose/non-SPDX
token like "Public domain". Demote secondary nuance (e.g. the bundled public-domain IANA tz
*data*) to a parenthetical, mirroring how existing dual-nature entries are written. If other
conditional deps are noted inline like `tzdata Apache-2.0 (Windows only)`, match that
parenthetical style rather than adding a new "Platform-conditional dependencies" subsection.
POLA: the file's existing format is the contract.

- **Worked example:** `tzdata` → PyPI `info.license == "Apache-2.0"`, ships
  `licenses/LICENSE_APACHE`; so the entry leads `Apache-2.0` with the public-domain IANA tz
  database noted parenthetically — NOT the other way around.

**(b) Add a regression GUARD TEST** that parses `[project].dependencies`, reduces each spec
to its bare PEP 508 distribution name, PEP 503-normalizes it, and asserts each name appears
in the NOTICE's delimited inventory section via **exact, normalized SET membership — never a
substring check**. Reuse the repo's existing dependency-name parser if one exists (in
ProjectHephaestus this is `_find_dep` in
`tests/unit/scripts/test_dependency_floor_consistency.py`, which exists precisely to avoid
prefix collisions like `pytest` vs `pytest-cov`). Place the new test next to that existing
pyproject-parsing test so it reuses the same runner, repo-root resolution, and parsing
structure.

```python
import re
import tomllib
from pathlib import Path

# Strip the version operator the same way the repo's _find_dep parser does.
_VERSION_OPS = ("<=", ">=", "==", "!=", "~=", "<", ">", "=")


def _dist_name(spec: str) -> str:
    """'tzdata; platform_system == "Windows"' -> 'tzdata' (bare, PEP 503 normalized)."""
    name = spec.split(";", 1)[0].strip()          # drop the PEP 508 marker
    for op in _VERSION_OPS:                         # drop the version operator
        if op in name:
            name = name.split(op, 1)[0]
            break
    name = name.split("[", 1)[0].strip()           # drop extras, e.g. "pkg[ext]"
    return re.sub(r"[-_.]+", "-", name).lower()     # PEP 503 normalize


def test_notice_lists_every_runtime_dependency():
    root = Path(__file__).resolve().parents[3]  # verify this depth per repo layout
    with open(root / "pyproject.toml", "rb") as f:
        deps = tomllib.load(f)["project"]["dependencies"]

    notice = (root / "NOTICE").read_text()
    # Scope to the delimited runtime section ONLY (header .. next ==== rule).
    m = re.search(
        r"Third-party runtime dependencies\s*\n(.*?)\n=+", notice, re.DOTALL
    )
    assert m, "Runtime-dependencies section not found in NOTICE (formatting changed?)"
    section = m.group(1)
    assert section.strip(), "NOTICE runtime section parsed empty (formatting changed?)"

    # EXACT membership: normalize the NOTICE tokens the SAME way and compare as a set.
    notice_names = {
        re.sub(r"[-_.]+", "-", tok).lower()
        for tok in re.findall(r"[A-Za-z0-9][A-Za-z0-9._-]+", section)
    }
    required = {_dist_name(d) for d in deps}
    missing = sorted(required - notice_names)
    assert not missing, f"NOTICE is missing runtime deps: {missing}"
```

### Detailed Steps

1. **Read the doc's claim.** Confirm the file actually asserts completeness; that assertion
   is what makes the omission a bug rather than a stylistic choice.
2. **Extract the real source of truth.** Parse `[project].dependencies` with `tomllib`
   (stdlib ≥ 3.11; `tomli` on 3.10), keeping the full specifier including markers.
3. **Identify the gap, focusing on markers.** Anything with a `;` marker is the prime
   suspect. In the concrete case it was `tzdata; platform_system == 'Windows'`.
4. **Verify the license token against ground truth FIRST** (do this before writing the line):
   query PyPI JSON `https://pypi.org/pypi/<dist>/json` → `info.license`, cross-checked with
   the distribution's bundled LICENSE file. A NOTICE is a legal document — never paste a
   license string from memory/issue text (see Risk 3 below). For `tzdata` the verified token
   is `Apache-2.0`.
5. **Add the entry in the existing style, LEADING with the verified SPDX token** (see Fix
   Pattern (a)); demote secondary nuance (public-domain IANA data) to a parenthetical, not
   the primary token.
6. **Add the guard test** next to an existing pyproject-parsing test (see Fix Pattern (b)),
   using exact PEP 503-normalized SET membership (never substring), and asserting the section
   was found (non-empty) BEFORE asserting membership, so a NOTICE format change fails loudly
   instead of vacuously passing.
7. **Decide extras scope explicitly** (see Risk 4): the base guard covers
   `[project].dependencies` only, not `[project.optional-dependencies]`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust the manual NOTICE on POSIX | Reviewed the NOTICE inventory on a Linux dev box and judged it complete | Platform-conditional deps (`tzdata; platform_system == 'Windows'`) never install on POSIX, so the omission is invisible there | Diff the NOTICE against `[project].dependencies` programmatically; never eyeball a single-platform inventory |
| Case-insensitive substring match in the guard | `if name.lower() in notice.lower()` over the whole NOTICE | FALSE-PASS when a dist name is a substring of prose (or another package), and FALSE-FAIL when the NOTICE author abbreviates/case-shifts; import name ≠ distribution name for some packages | Match the bare PEP 508 *distribution* name as a whole word, scoped to the delimited runtime section, normalized per PEP 503 (lowercase, runs of `-_.` → single `-`) |
| Parse the runtime section by header alone | Assume the block runs from the `Third-party runtime dependencies` header to the next `====` rule, then match membership | If NOTICE formatting changes the delimiter, the parser silently scopes the wrong (possibly empty) region and the membership assertions pass vacuously | `assert` the section was actually found and non-empty BEFORE asserting membership, so a format change fails loudly |
| Take the tzdata license from memory/issue text | Wrote the attribution line citing "public-domain IANA data + Apache-2.0 packaging" sourced from the issue and prior-learnings block | The license string was not verified against the tzdata PyPI page / its distributed LICENSE; a NOTICE is a legal document and an unverified SPDX/license string is a defect | Confirm the SPDX/license string against the actual distributed package metadata before writing a legal-attribution line |
| Add a new "Platform-conditional dependencies" subsection | Considered grouping conditional deps under a fresh heading | Diverges from the file's existing inline-parenthetical convention; surprises future maintainers and complicates the guard's section parser | Match the existing inline style (e.g. `tzdata (Windows only)`); the file's format is the contract (POLA) |
| Guard only `[project].dependencies` and call it "fully guarded" | Wrote a guard over base deps and described the NOTICE as fully protected | The NOTICE also documents `[project.optional-dependencies]` extras in a separate section, which the guard does not cover; "fully guarded" over-claims | Decide extras coverage explicitly; if the guard covers base deps only, say so — don't imply total coverage |
| Wrote license string from issue/memory text | Used the issue's prose license wording directly in the NOTICE (leading with "Public domain") | Unverified legal string on a legal doc; "Public domain" is not an SPDX identifier and diverged from the file's house style | Verify against PyPI `info.license` + the bundled LICENSE; lead with the SPDX token (`Apache-2.0`), demote the public-domain nuance to a parenthetical |
| Substring membership in the guard test | `name.lower() in block.lower()` | Brittle: false-passes when a short dep name appears in prose, false-fails when the NOTICE abbreviates | Strip the `;`-marker + version operator to the bare name, PEP 503-normalize both sides, and compare as a SET |

## Results & Parameters

### Fix shape

- **Edit:** add `tzdata` to the NOTICE runtime-dependency inventory in the existing
  inline-parenthetical style, **leading with the verified SPDX token**, e.g.
  `tzdata Apache-2.0 (Windows only — IANA tz database for zoneinfo; bundled tz data is public domain)`.
- **Guard:** a regression test parsing `[project].dependencies`, reducing each spec to its
  PEP 503-normalized bare distribution name (strip `;`-marker + version operator), and
  asserting **exact, normalized SET membership** in the delimited NOTICE runtime section
  (after asserting the section is non-empty).

### License-verification one-liner (run BEFORE writing the legal line)

```bash
curl -s https://pypi.org/pypi/<dist>/json | \
  python3 -c "import sys,json;print(json.load(sys.stdin)['info']['license'])"
```

### tzdata license reference (VERIFIED in R1)

- **Verified license token: `Apache-2.0`** — PyPI `info.license == "Apache-2.0"`; the wheel
  ships `licenses/LICENSE_APACHE`. This is the token to lead the NOTICE entry with.
- `tzdata` packages the **IANA tz database**; that bundled *data* is itself **public domain**
  — but that is *secondary* nuance and belongs in a parenthetical, NOT as the primary token.
- It exists so `zoneinfo.ZoneInfo` can resolve timezone data on **Windows**, where CPython
  does not bundle the IANA database (POSIX systems bundle it). Hence the
  `platform_system == 'Windows'` marker — it is the Windows companion to the project's
  POSIX-only import guards (`curses` / `fcntl` / `grp`).

### Risks for the implementer (most-uncertain assumptions)

1. **Guard-test name-matching brittleness.** NOTICE uses human distribution names; import
   name ≠ distribution name for some packages, and authors may abbreviate/case-shift. A
   naive case-insensitive **substring** check FALSE-PASSes (dep name as a substring of prose
   or of another package, e.g. `pytest` inside `pytest-cov`) or FALSE-FAILs. Mitigation: strip
   the `;`-marker and version operator to the bare PEP 508 distribution name, PEP 503-normalize
   BOTH the dep names and the NOTICE tokens, scope to the delimited runtime section, and
   compare as a SET — never substring. Reuse the repo's existing dep-name parser (e.g.
   `_find_dep` in `tests/unit/scripts/test_dependency_floor_consistency.py`) so the two
   normalizations cannot drift apart.
2. **Section-delimiter parsing is fragile.** The test assumes the runtime block is bounded by
   the `Third-party runtime dependencies` header and the next `====` rule. A formatting
   change silently scopes the wrong region. Mitigation: assert the section was found
   (non-empty) before asserting membership, so a format change fails loudly, not vacuously.
3. **License-token correctness (NOW VERIFIED for tzdata).** A NOTICE is a legal document, so
   the verification must prove the *license string*, not just the package name. For `tzdata`
   the token was confirmed in R1: PyPI `info.license == "Apache-2.0"` + bundled
   `licenses/LICENSE_APACHE`. General rule for any new dep: verify against PyPI `info.license`
   + the bundled LICENSE, lead the entry with the SPDX identifier, and demote secondary
   nuance (e.g. bundled public-domain data) to a parenthetical — never lead with a non-SPDX
   prose token like "Public domain". Verification commands MUST prove the token, e.g.
   `grep -nE "tzdata +Apache-2\.0" NOTICE`, not just `grep tzdata NOTICE`.
4. **Scope-creep / over-claim risk.** The guard covers `[project].dependencies` only
   (unconditional + conditional runtime). It does NOT cover
   `[project.optional-dependencies]` extras, which the NOTICE documents in a separate
   section. Mitigation: decide explicitly whether the guard should also cover extras;
   covering only base deps must not be described as "fully guarded".

### Parsing notes

- Use `tomllib` (stdlib ≥ Python 3.11; `tomli` on 3.10) to read `[project].dependencies`
  rather than regex over raw TOML.
- Reduce each PEP 508 spec to a bare name the way the repo's `_find_dep` parser does: strip
  the `;`-marker, then strip the version operator from
  `("<=", ">=", "==", "!=", "~=", "<", ">", "=")`, then drop any `[extras]`; then PEP
  503-normalize: lowercase and collapse runs of `-_.` to a single `-`. Normalize the NOTICE
  tokens the SAME way and compare as a set — substring matching collides on prefixes
  (`pytest` vs `pytest-cov`).
- Verify the test's repo-root depth (`Path(__file__).resolve().parents[N]`) against the
  actual test location — in a git worktree an off-by-one resolves to `.worktrees/`.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Issue #1218 (planning) | NOTICE omitted `tzdata; platform_system == 'Windows'` while claiming a complete runtime inventory; plan = add entry in existing style + guard test diffing `[project].dependencies` vs NOTICE. Guard-test workflow NOT yet executed in CI (unverified). |
| ProjectHephaestus | Issue #1218 plan R1 (NOGO→resolved) | License verified via PyPI (`info.license == "Apache-2.0"` + bundled `licenses/LICENSE_APACHE`); entry now leads with the SPDX token, public-domain IANA data demoted to a parenthetical; guard switched from substring to exact PEP 503-normalized SET matching (reusing the `_find_dep` parser). |
