---
name: testing-source-package-asset-contract-mirroring
description: "Prevent source and packaged runtime asset drift. Use when: (1) a Python package ships manifests or scripts as package data, (2) a strict audit finds source/package contract differences, (3) model manifests must validate from both source and installed-asset locations, (4) container-backed validation is required for a full release gate."
category: testing
date: 2026-07-13
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [testing, package-data, asset-mirroring, manifests, scripts, strict-audit, container-validation]
---

# Source-Package Asset Contract Mirroring

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-13 |
| **Objective** | Eliminate drift between checked-in runtime contracts and their packaged copies after a strict repository audit identifies missing or stale assets. |
| **Outcome** | Successful: source and packaged manifests/scripts were made byte-identical, paired manifest validation was added, documentation routing was restored, and local plus container-backed validation passed. |
| **Verification** | verified-local; the full test suite and container-backed release gate passed locally, while CI was not observed. |

## When to Use

- A package distributes YAML manifests, shell scripts, templates, or similar runtime assets through package data.
- A source manifest validates but the installed package reads a separate stale or missing copy.
- A strict audit finds that tests compare selected assets only, allowing new asset types to drift unnoticed.
- Documentation added for an operational workflow is not discoverable through the repository's agent or contributor routing guide.
- Host validation cannot exercise required system binaries, but the repository provides a container-backed full validation command.

## Verified Workflow

### Quick Reference

```bash
# Discover every packaged runtime asset and its source counterpart.
find package/assets -type f | sort
find manifests scripts -type f | sort

# Add regression tests before synchronizing the assets.
pytest -q tests/test_package_assets.py tests/test_model_manifests.py

# Run quality gates, then the environment that contains required system tools.
ruff format --check package scripts tests
ruff check package scripts tests
mypy package scripts
just validate
```

### Detailed Steps

1. Map each packaged asset directory to its source-of-truth directory. Treat the source file and the package-data copy as one runtime contract, not two independently editable files.

2. Write a regression test that enumerates all packaged manifest files and compares each corresponding source file byte-for-byte. Do the same for packaged scripts, recursively, so new nested scripts cannot bypass the check.

3. For each model manifest, load and validate both copies. Assert that their parsed document structures match and that their raw bytes match. This catches both semantic divergence and formatting or generated-content drift.

4. Make the failing tests pass by adding missing package-data files and synchronizing stale copies from the reviewed source. Do not introduce a second generator unless the repository already has a supported generation path.

5. When adding a runbook or operational document, update the repository routing guide in the same change. Add a focused test that every documentation file has an explicit route where the repository enforces that contract.

6. Run formatter, linter, type checks, targeted asset and manifest tests, and the full test suite. Keep the checks scoped until the regression tests pass, then expand to the release gate.

7. Run the container-backed release command when host validation lacks a required system binary. Record the host limitation separately; container success is local evidence, not CI evidence.

8. Preserve verification honesty in follow-up documentation: state `verified-local` until a CI run is actually observed.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Checking selected top-level assets only | Compared a small hand-picked list of package files with source files | Newly added manifests and nested scripts were not covered, so drift remained possible | Enumerate the complete packaged asset tree and require a source counterpart for every runtime file |
| Validating only source manifests | Parsed and schema-validated files from the source directory | Installed-package execution resolves package data and can use a missing or stale copy | Validate source and package copies as a pair, then assert parsed and byte-level equality |
| Treating asset copies as documentation | Updated source contracts without synchronizing the package-data tree | Runtime behavior diverged even though source review looked correct | Package data is executable runtime input and needs the same regression protection as code |
| Running only host validation | Relied on host tests where a required system binary was absent | The full integration gate could not run on that host | Use the repository's container-backed validation path for system-tool evidence and report the distinction honestly |
| Adding a runbook without routing | Created operational documentation but did not update the repository guide | Agents and contributors could not discover the new contract through the required entrypoint | Treat routing metadata and its test as part of documentation delivery |

## Results & Parameters

### Contract Test Shape

```python
for packaged_asset in sorted(package_asset_root.rglob("*")):
    if packaged_asset.is_file():
        relative = packaged_asset.relative_to(package_asset_root)
        source_asset = source_root / relative
        assert source_asset.is_file()
        assert packaged_asset.read_bytes() == source_asset.read_bytes()
```

For structured manifests, test both representations:

```python
assert load_manifest(source_path) == load_manifest(packaged_path)
assert source_path.read_bytes() == packaged_path.read_bytes()
```

### Verification Order

| Check | Purpose |
|-------|---------|
| Targeted asset tests | Proves the regression test first fails on drift, then passes after synchronization |
| Formatting, linting, and typing | Keeps test hardening and supporting code within repository quality standards |
| Full test suite | Confirms the asset contract change does not regress broader behavior |
| Container-backed release gate | Exercises system-tool validation unavailable on the host |

### Evidence Boundary

Use `verified-local` when local focused checks, the full suite, and a container-backed release command pass, but no CI run has been observed. Upgrade to `verified-ci` only after inspecting the actual CI result for the change.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Internal Python inference platform | Strict audit remediation, verified-local | Byte-for-byte manifest and script mirrors, paired manifest validation, documentation routing coverage, static checks, full tests, and container-backed release validation passed locally. |
