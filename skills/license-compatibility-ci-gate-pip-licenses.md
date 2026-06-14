---
name: license-compatibility-ci-gate-pip-licenses
description: "Plan a machine-enforced license-compatibility CI gate for a Python (pixi-based) repo whose NOTICE asserts dependency-license compatibility by hand. Use when: (1) a NOTICE file claims 'all bundled deps are permissively licensed' with no automated check and you want CI to catch drift, (2) you are adding a pip-licenses allowlist gate alongside existing pip-audit/SAST scans, (3) you must allow specific NOTICE-justified copyleft extras (e.g. PyGithub LGPL-3.0) without permitting copyleft generally, (4) you want advisory-on-main / blocking-on-PR rollout so adopting the gate does not retroactively redden main, or (5) you are reviewing such a plan and need its known correctness risks (license-string spelling variance, substring copyleft scan, dev-tool false-fails)."
category: ci-cd
date: 2026-06-12
version: "1.0.0"
user-invocable: false
verification: unverified
tags: []
---

# License-Compatibility CI Gate (pip-licenses)

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-06-12 |
| Objective | Plan a CI gate that mechanically verifies the license-compatibility claims a NOTICE file makes by hand, for a pixi-based Python repo |
| Outcome | Implementation plan only — design captured, NOT executed |
| Verification | **unverified** — no CI run, no tests executed; treat every claim as a hypothesis |

> **Warning:** This skill records a *plan* for ProjectHephaestus issue #1219 that was
> never executed. No CI ran, no unit test ran, no `pip-licenses` invocation was
> observed. Everything below — especially the license strings, flags, and exit-code
> behavior — is a design assumption pending validation.

## When to Use

- A repo ships a `NOTICE` that asserts "all dependencies are permissively licensed"
  (with hand-maintained exceptions like `PyGithub` LGPL-3.0) and nothing enforces it.
- You want a license gate that lives **next to** existing `pip-audit` / SAST jobs,
  not folded into them.
- You need to permit a *named* copyleft dependency that NOTICE already justifies,
  while still failing on any *new, unjustified* copyleft dep.
- You want to adopt the gate without instantly reddening `main`.
- You are reviewing a license-gate plan and need the reviewer-facing risk list.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a
> hypothesis until CI confirms.

### Quick Reference

```text
1. CI job: ISOLATED sibling job (not a step) mirroring the pip-audit job shape:
   checkout -> setup-pixi (locked) -> run pixi task -> if: always() summary.
2. Tool placement: pip-licenses in [feature.lint.pypi-dependencies] (PyPI-only;
   no conda-forge guarantee) AND in the pip `dev` extra (pip-only contributors).
3. Source of truth: read the RESOLVED tree via `pip-licenses --format=json`.
   NEVER re-parse NOTICE prose and assert it against itself (tautology).
4. Two-tier allowlist:
     - PERMISSIVE set: MIT / BSD / Apache / PSF / ISC -> allowed for ANY package.
     - COPYLEFT map: explicit {package: license} for NOTICE-justified extras
       (e.g. pygithub: LGPL-3.0). A copyleft dep NOT in the map -> FAIL.
5. Rollout: advisory-on-main / blocking-on-PR via exit code keyed on
   GITHUB_EVENT_NAME (exit 1 only on pull_request, else exit 0).
6. Lock it: unit test over SYNTHETIC json (never the real tree) + pre-commit hook
   scoped files: ^(pyproject\.toml|pixi\.toml|pixi\.lock|NOTICE)$, pass_filenames: false.
```

**Design rationale, step by step:**

1. **Isolated sibling job.** Add a separate CI job, not a step grafted onto an
   existing scan. If license scanning shares a job with CVE/SAST scans, one
   scanner's failure (or its broader permissions) blocks every other check.
   Mirror the existing `pip-audit` job exactly: `checkout` → `setup-pixi` with the
   lockfile → run the pixi task → an `if: always()` summary step.

2. **Tool placement in two homes.** `pip-licenses` is a PyPI-only package with no
   conda-forge guarantee, so it belongs in `[feature.lint.pypi-dependencies]` for
   the pixi-managed CI env. Also list it in the pip `dev` extra in `pyproject.toml`
   so pip-only contributors who never touch pixi still get the tool.

3. **Read the resolved tree, not the prose.** The gate must call
   `pip-licenses --format=json` and classify the actually-installed dependency
   tree. Re-parsing NOTICE text and checking it against NOTICE is a tautology that
   can never catch real drift — the whole point is to detect when the installed
   tree diverges from what NOTICE claims.

4. **Two-tier allowlist.** A permissive set (MIT/BSD/Apache/PSF/ISC) is allowed for
   *any* package. A separate explicit `{package: license}` copyleft map enumerates
   the specific NOTICE-justified non-vendored extras (e.g. `pygithub: LGPL-3.0`).
   The asymmetry is deliberate: permissive licenses are fine everywhere; copyleft
   is fine *only* for the exact packages NOTICE already vouches for. A brand-new
   copyleft dependency absent from the map fails the gate.

5. **Advisory-on-main / blocking-on-PR.** Compute a conditional exit code from
   `GITHUB_EVENT_NAME`: exit 1 (block) on `pull_request`, exit 0 (advisory) on
   `push`/`schedule`. This lets the team adopt the gate immediately without a
   retroactive red `main` while still blocking new violations at the PR boundary.

6. **Lock the logic.** A unit test must exercise the parse/classify logic against
   *synthetic* JSON fixtures — never the live dependency tree, which drifts and
   makes the test flaky. Add a pre-commit hook scoped to the files that can change
   the dependency surface: `files: ^(pyproject\.toml|pixi\.toml|pixi\.lock|NOTICE)$`,
   with `pass_filenames: false`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Combine all scanners in one CI job | Put license scan as a step on the existing CVE/SAST job | One scan's failure blocks every check; broader job permissions leak to the license step | Give the license gate its own isolated sibling job |
| Edit workflow with the Edit tool | Modify `.github/workflows/*.yml` directly | A pre-commit security hook blocks tool-driven edits to workflow YAML | Append/patch workflow files via `sed`/append, not the Edit tool |
| Bump pinned tool version in workflow only | Changed the pinned `pip-licenses` version in the workflow but not its test copy | The test silently keeps asserting the stale pinned value | Dual-update: change the version in the workflow AND in the test that pins it |
| Re-parse NOTICE prose | Read NOTICE text and assert it against itself | Tautology — comparing NOTICE to NOTICE can never detect drift | Classify the RESOLVED dependency tree (`pip-licenses --format=json`) instead |
| Exact-string license membership | Test each dep's license string for membership in a hardcoded `ALLOWED_LICENSES` set | pip-licenses strings are NOT canonical SPDX — "MIT License" vs "MIT", "Apache Software License", "GNU Lesser General Public License v3 (LGPLv3)" — so the set false-passes or false-fails | Normalize/canonicalize (or SPDX-map) license strings before the membership test; do not rely on raw equality |
| Substring copyleft scan | `is_permissive` returns False whenever any COPYLEFT_MARKER substring (e.g. "GPL") appears | "GPL" matches LGPL/AGPL but also misfires on dual licenses like "MIT OR GPL-3.0" — rejected even though MIT is choosable | Parse OR/dual licenses; a permissive *option* should satisfy the gate, not be overridden by any single copyleft marker |
| No-op string split bug | `license_str.replace(";", ";")` to prep multi-license splitting | Replacing ";" with itself is dead code — the split does nothing meaningful even though pip-licenses separates multiple licenses with ";" | Actually split on the real separator and classify each license independently; review for no-op `.replace` calls |
| Scan the full env | `pip-licenses --with-system` to include everything | Surfaces GPL dev/build tools (yamllint, bats-core) that NOTICE explicitly says are acceptable as dev tools — gate false-fails on tooling | Scope the gate to runtime/distributed deps only; exclude dev tooling NOTICE permits |
| Trust `/dev/stdin` piping unchecked | Pipe `pip-licenses` JSON via `--input /dev/stdin` inside the pixi-wrapped CI shell | Unverified that `/dev/stdin` input works under the pixi shell wrapper on the runner | Verify the I/O path on the actual runner, or write to a temp file in `build/` instead of relying on `/dev/stdin` |

> **Note:** Some rows above are prior-team learnings; others are self-identified
> risks in *this* plan. Because the plan was never executed, the self-identified
> rows (exact-string membership, substring copyleft scan, no-op split, full-env
> scan, `/dev/stdin`) are hypothesized failure modes, not observed ones.

## Results & Parameters

All values below are **PROPOSED**, read from the codebase at plan time, and
**not verified** by any run.

- **Tool pin:** `pip-licenses>=4.0,<6` in `[feature.lint.pypi-dependencies]` and in
  the pip `dev` extra.
- **Cache key:** `pixi-lint-*` (mirrors the existing lint env cache).
- **Job timeout:** `timeout-minutes: 10`.
- **Triggers:** `pull_request` + `push: [main]` + `schedule` + `workflow_dispatch`.
- **Conditional exit:** `EXIT_CODE = 1` on `pull_request`, else `0`
  (advisory-on-main / blocking-on-PR).
- **Pre-commit scope:** `files: ^(pyproject\.toml|pixi\.toml|pixi\.lock|NOTICE)$`,
  `pass_filenames: false`.

**Allowlist (proposed):**

- PERMISSIVE set (any package): MIT, BSD, Apache, PSF, ISC.
- COPYLEFT map (named exceptions only): `pygithub: LGPL-3.0`.

**Most uncertain assumptions (reviewer-facing risks):**

1. **License-string spelling is the #1 correctness risk.** pip-licenses strings are
   not standardized SPDX and vary by metadata source. A hardcoded exact-match set
   will miss spellings and either false-pass or false-fail.
2. **Substring copyleft scan misfires on OR-licenses.** `"GPL" in license_str` is
   crude; `is_permissive` returns False on "MIT OR GPL-3.0" even though MIT is
   choosable.
3. **Dead-code split bug.** `license_str.replace(";", ";")` is a no-op; multi-license
   strings may not split as intended.
4. **`--with-system` / `/dev/stdin` unverified.** `--with-system` pulls dev/build
   tools (yamllint, bats — GPL but NOTICE-permitted) causing false-fails unless
   scoped to runtime deps; `/dev/stdin` piping under the pixi shell is unconfirmed.
5. **Line-number anchors may drift.** Cited anchors — `security.yml:18/39/57`,
   `pixi.toml:90/92/104`, `pyproject.toml:58`, `.pre-commit-config.yaml:182` — were
   read at plan time; treat as approximate.
6. **Judgment call on PSF/extras.** `defusedxml` (PSF-2.0) and `nats-py` (Apache)
   appear in NOTICE but the draft COPYLEFT map lists only `pygithub`; PSF-2.0 was
   folded into the permissive set instead — a debatable classification worth flagging.

**External things relied on WITHOUT direct verification:** the pip-licenses output
schema/field names (`"Name"`, `"License"`); its `--with-system` and `--format=json`
flags; the exact license strings pip-licenses emits per dependency; and that
`/dev/stdin` input works under the pixi-wrapped CI shell.

## Verified Workflow

None — this plan was never executed. There is no verified workflow. See
**Proposed Workflow** above; every step there is an unverified hypothesis pending
a CI run. This heading exists only to record that verification did not occur.

## Verified On

| Repo | Context | Status |
|------|---------|--------|
| ProjectHephaestus | Issue #1219 plan (planning only, not executed) | unverified — plan stage |
