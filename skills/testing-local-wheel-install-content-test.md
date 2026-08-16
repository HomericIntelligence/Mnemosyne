---
name: testing-local-wheel-install-content-test
license: BSD-3-Clause
description: "Design a fail-closed Python artifact lane that proves deterministic wheel and sdist builds, exact safe archive inventories, complete wheel RECORD integrity, and isolated install/upgrade/uninstall behavior. Use when: (1) package CI only samples archive members or smoke-imports an installed wheel, (2) reproducibility must be checked under controlled build inputs, (3) wheel RECORD rows and archive path safety need complete validation, (4) current-wheel, current-sdist, upgrade, and uninstall contracts must run outside the checkout, (5) a required CI job and release workflow must select the same dedicated artifact suite."
category: testing
date: 2026-08-05
version: "2.0.0"
user-invocable: false
verification: unverified
history: testing-local-wheel-install-content-test.history
tags:
  - python-packaging
  - wheel
  - sdist
  - reproducible-builds
  - archive-integrity
  - record-integrity
  - lifecycle-testing
  - clean-install
  - upgrade
  - uninstall
  - pytest-markers
  - ci-gating
  - hatch-vcs
  - uv-venv
---

# Deterministic Python Artifact Integrity and Lifecycle Tests

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-05 |
| **Objective** | Replace sampled wheel checks with a dedicated, fail-closed artifact lane covering reproducible wheel/sdist builds, complete safe manifests, every wheel `RECORD` row, and the installed package lifecycle. |
| **Outcome** | A behavior-complete, reusable implementation contract was produced. It keeps packaging metadata authoritative, shares controlled builds across tests, and separates current-wheel, current-sdist, upgrade, and uninstall environments. |
| **Verification** | `unverified` — the workflow is based on a reviewed implementation design; its end-to-end tests and CI run have not yet been observed. |
| **History** | [changelog](./testing-local-wheel-install-content-test.history) |

## When to Use

- A required build job proves only that a wheel can be built or imported, but does not prove byte reproducibility or the full shipped inventory.
- Packaging tests assert a few expected paths or forbidden prefixes, allowing unexpected files, missing files, duplicate members, or unsafe archive paths to escape.
- A wheel's `RECORD` is trusted without checking that it covers every member exactly once and that every non-self digest and size matches the payload.
- An editable checkout, repository working directory, or inherited `PYTHONPATH` could satisfy an install smoke test without using the artifact under test.
- The release path should repeat the artifact contract before publication, while the ordinary integration lane should avoid rebuilding the same artifacts.
- A dynamic-version build generates a package file such as `_version.py` that is absent from the source tree but required in both distribution formats.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until
> local execution or CI confirms the reproducible-build, integrity, and lifecycle contracts.

### Quick Reference

```bash
# The dedicated suite owns all expensive build and installed-artifact checks.
<runner> pytest <integration-tests> \
  --override-ini="addopts=" \
  --basetemp=build/pytest-artifacts \
  -v --strict-markers -m artifact

# Keep the ordinary integration lane from rebuilding the artifacts.
<runner> pytest <integration-tests> \
  --override-ini="addopts=" \
  --basetemp=build/pytest-integration \
  -v --strict-markers -m "not nightly and not artifact"
```

### 1. Keep packaging metadata authoritative

Do not duplicate the build backend's package-selection rules in production code. Derive the test
inventory from the configured source package tree, exclude only cache and bytecode artifacts, and
add build-generated package files explicitly. Treat top-level sdist inclusions and wheel metadata
files as small, exact test constants beside the corresponding archive tests.

### 2. Build controlled artifacts once per pytest session

Create a typed test helper and a session-scoped fixture that build:

- two current-version wheel/sdist pairs in distinct output directories; and
- one lower-version wheel for the upgrade contract.

Before building, fail closed when the build frontend or environment runner is unavailable. Do not
call `pytest.skip`: a required artifact gate that silently skips its tooling is not a gate.

Remove `PYTHONPATH` and fix every practical build input:

```python
env.update(
    {
        "LC_ALL": "C.UTF-8",
        "PYTHONHASHSEED": "0",
        "SETUPTOOLS_SCM_PRETEND_VERSION": version,
        "SOURCE_DATE_EPOCH": "<fixed-unix-epoch>",
        "TZ": "UTC",
    }
)
```

Run the build from outside the repository working directory, send each build to its own output
directory, and require exactly one requested artifact per format. Compare both the filenames and
streaming SHA-256 digests of the two current wheels and the two current sdists.

### 3. Derive the complete source-package inventory

Enumerate every regular file below the configured package root. Exclude paths containing
`__pycache__` and suffixes such as `.pyc` or `.pyo`, then add the build-generated version module.
The inventory should be expressed in repository-relative POSIX paths so it compares directly with
both archive formats.

```python
source_files = {
    path.relative_to(repo_root).as_posix()
    for path in package_root.rglob("*")
    if path.is_file()
    and "__pycache__" not in path.parts
    and path.suffix not in {".pyc", ".pyo"}
}
source_files.add("<package>/_version.py")
```

### 4. Validate every sdist member before comparing the manifest

Inspect every tar member before trusting its normalized name:

1. Reject absolute names and any `..` path component.
2. Require one common archive root and strip exactly that root.
3. Reject duplicate stripped names.
4. Reject symbolic links, hard links, devices, FIFOs, and unsupported member types.
5. Ignore directory entries only; collect every regular file.
6. Compare the resulting set for exact equality with:
   `source package files + configured top-level files + PKG-INFO`.

Exact equality is the important property: positive samples and forbidden-prefix checks cannot
detect arbitrary extra files or omissions outside the sample.

### 5. Validate the complete wheel manifest and `RECORD`

Reject duplicate, absolute, and traversal ZIP member names before reading metadata. Derive exactly
one `.dist-info` prefix, then require exact equality with:

```text
source package files
+ METADATA
+ WHEEL
+ entry_points.txt
+ configured license files
+ RECORD
```

Preserve the separate console-script parity check: the parsed `console_scripts` section in
`entry_points.txt` must equal the build configuration's script table.

Parse `RECORD` as CSV and validate the full bijection and payload integrity:

- every row has exactly three fields;
- row paths are unique;
- the set of row paths equals the set of wheel members;
- only the `RECORD` self-entry has empty digest and size fields;
- every other digest uses `sha256` and URL-safe base64 without assuming padding is present;
- each decoded digest equals `sha256(member_bytes).digest()`; and
- each decimal size equals the member byte length.

### 6. Test each installed-package lifecycle state in isolation

Create a fresh virtual environment with the current interpreter for each contract. Give it a run
directory outside the checkout, remove `PYTHONPATH`, and invoke Python and console scripts by their
absolute virtual-environment paths.

Before the first install in every environment, prove both the importable package and distribution
metadata are absent. Then run three independent contracts:

| Environment | Contract |
|-------------|----------|
| Current wheel | Install the current wheel directly, assert its exact version, and run representative base-layer scripts. |
| Current sdist | Install the current sdist directly, assert its exact version, and run the same scripts. |
| Upgrade/uninstall | Install the previous wheel, assert the old version, upgrade to the current wheel, assert only current distribution metadata remains, run scripts, uninstall, then prove package code, metadata, and scripts are absent. |

Use scripts that belong to the base package rather than an optional product extra. Execute each
with `--help`, require exit status zero, and assert recognizable usage output. The upgrade test does
not replace the direct current-wheel test: it exercises a different installation path and can hide
clean-install failures.

### 7. Route one fail-closed CI lane

Register an `artifact` pytest marker and route it through the existing required build job. Preserve
the required job's identifier, checkout depth, locked environment setup, timeout, condition, and
aggregate-gate membership. Change only its test command.

Add workflow-structure tests that prove:

- the required build job invokes `-m artifact` with a `build/` base temp directory;
- the ordinary integration job selects `not nightly and not artifact`;
- the aggregate required-check gate still needs the build job; and
- the release integration command includes artifact tests before publication.

Keep any existing installed-CLI lane that covers optional extras; the artifact lane has a separate
purpose: reproducibility, complete archive integrity, direct sdist installation, upgrade, and
uninstall.

### 8. Verify in focused layers

Run reproducibility, manifest/`RECORD`, clean-install, lifecycle, fail-closed/tooling, and workflow
routing tests separately before running the complete artifact marker. Finish with focused lint and
type checks for the test helpers. Store pytest base directories and virtual environments under the
repository's build directory.

## Verified Workflow

No end-to-end workflow is verified yet. The executable procedure is intentionally documented under
**Proposed Workflow** until the focused artifact suite and CI pass. This explicit placeholder is
retained because Mnemosyne's current registry validator requires the `Verified Workflow` heading
even for `verification: unverified` skills.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Sampled wheel assertions | Checked a handful of package and metadata paths plus forbidden repository prefixes | Samples do not prove complete membership and miss arbitrary unexpected or omitted files | Derive the package inventory and require exact manifest equality for both wheel and sdist |
| Skip when build tooling is missing | Used `pytest.skip` when `python -m build` or the environment runner was unavailable | A required CI gate could pass without exercising any artifact behavior | Required tooling discovery must raise or fail, and its fail-closed behavior needs explicit tests |
| Install smoke from the checkout | Ran import probes with the repository as the working directory or inherited `PYTHONPATH` | Source files or an editable install could satisfy the probe instead of the built artifact | Run absolute venv binaries from a non-checkout directory, strip `PYTHONPATH`, and prove pre-install absence |
| Trust archive member names | Compared normalized member strings without rejecting links, duplicate names, absolute paths, or traversal | Malformed archives can overwrite, alias, or escape expected paths while still matching selected names | Validate every raw member and type before stripping the sdist root or reading wheel payloads |
| Trust `RECORD` presence | Asserted only that `RECORD` existed | A present file can omit members, duplicate paths, or contain wrong hashes and sizes | Require a one-to-one row/member mapping and validate every non-self SHA-256 digest and byte size |
| Use upgrade as the current-wheel smoke | Installed the old wheel and upgraded to current, then treated that as current-wheel install coverage | Upgrade state can retain files or metadata and does not prove installation into an empty environment | Keep direct current-wheel, direct current-sdist, and upgrade/uninstall contracts in separate venvs |
| Run artifact tests in every integration lane | Left expensive build tests in the general integration selection and also added a dedicated build job | The same artifact matrix runs repeatedly and obscures which required job owns the contract | Give artifact tests a dedicated marker, exclude it from ordinary integration, and retain it in release validation |

## Results & Parameters

### Controlled build parameters

| Parameter | Contract |
|-----------|----------|
| Current version | Fixed test-only version used for two wheel/sdist builds |
| Previous version | Lower fixed version used for the upgrade wheel |
| `SOURCE_DATE_EPOCH` | One fixed Unix timestamp shared by every controlled build |
| `PYTHONHASHSEED` | `0` |
| `SETUPTOOLS_SCM_PRETEND_VERSION` | Exact current or previous test version |
| Locale / timezone | `LC_ALL=C.UTF-8`, `TZ=UTC` |
| Build isolation | Repository-defined; with `--no-isolation`, assert required backends are already installed |
| Artifact discovery | Exactly one `*.whl` and, when requested, one `*.tar.gz` per output directory |

### Exact inventory equations

```text
sdist regular files
= source_package_files
+ configured_sdist_top_level_files
+ PKG-INFO

wheel members
= source_package_files
+ <dist-info>/METADATA
+ <dist-info>/WHEEL
+ <dist-info>/entry_points.txt
+ configured <dist-info>/licenses/*
+ <dist-info>/RECORD
```

### Verification promotion

Keep this skill at `unverified` until the actual artifact lane executes end-to-end. Promote it to
`verified-local` only after every focused test, the full `-m artifact` suite, lint, and type checks
pass locally. Promote it to `verified-ci` only after observing the required build job and release
path pass with these checks selected.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Reviewed artifact-lane design; implementation and CI execution pending | [Session notes and proposed acceptance commands](./testing-local-wheel-install-content-test.notes.md) |

## Related

- [[python-packaging-pyproject-editable-install]] — dynamic versioning, editable installs, and
  console-script configuration.
- [[testing-source-package-asset-contract-mirroring]] — source/package-data equality when runtime
  assets have separate source and packaged copies.
- [[ci-release-pipeline-must-mirror-required-pr-gate]] — why release workflows must repeat checks
  that can otherwise be bypassed by non-PR release paths.
