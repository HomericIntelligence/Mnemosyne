---
name: cross-repo-script-and-library-porting
description: "Port scripts, libraries, or skills between repositories without downgrading the destination. Use for dependency-layer migrations, diverged implementations, dependency elimination, source shims, licensed upstream skill adaptation, or staged code absent from the target."
category: tooling
date: 2026-05-19
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
history: cross-repo-script-and-library-porting.history
tags:
  - porting
  - cross-repo
  - dependency-elimination
  - re-export
  - compatibility
  - licensing
  - sequential-prs
  - skills
---

# Cross-Repository Script and Library Porting

## Overview

Port behavior, not files blindly. Audit what the destination already provides, map dependencies and
contracts, compare divergent implementations, adapt to destination conventions, and migrate in
dependency order. Clean the source only after destination CI is green and compatibility shims have
an explicit consumer and removal plan.

The workflow has CI evidence across library, script, and skill migrations. Detailed case metrics and
source links are in
[cross-repo-script-and-library-porting.notes.md](cross-repo-script-and-library-porting.notes.md),
and the complete previous guide is in
[cross-repo-script-and-library-porting.history](cross-repo-script-and-library-porting.history).

## When to Use

- Porting utility scripts or a full library into another repository.
- Two repositories have diverged and the destination may already contain newer behavior.
- Removing a heavy SDK by using an already-supported CLI/subprocess boundary.
- Splitting a large migration into dependency-layer PRs.
- Porting an Apache-2.0/MIT skill or Agent Skills Standard artifact with attribution.
- Preserving source import paths through thin re-export wrappers after a successful port.
- A completed staging copy never reached the intended target repository.

## Verified Workflow

### 1. Bind source and destination state

Record immutable SHAs, licenses, active branches, and dirty state in both repositories. Inventory
the destination before copying:

```bash
rg -n 'entry_points|console_scripts|target_function|TargetClass' pyproject.toml src tests scripts
git ls-files scripts src tests
```

Search by intent and public symbols, not filename alone. An apparent missing file may already exist
as a newer command, helper, or module.

### 2. Build a behavior/dependency matrix

For each candidate unit, record:

| Surface | Source | Destination | Port decision |
| --- | --- | --- | --- |
| Public API/CLI | Signature, flags, exit codes | Existing contract | Preserve or adapt explicitly |
| Internal dependencies | Imports and helper calls | Available equivalents | Reuse, replace, or layer first |
| Configuration | Env, files, defaults | Destination conventions | Translate |
| Tests | Success/failure behavior | Existing suite | Merge by behavior |
| Packaging | Entry points/dependencies | Canonical manifest | Update authoritative source |
| License/attribution | Source license and notices | Destination policy | Preserve required notices |

Reject any source change that removes a destination-only fix, security control, platform branch,
or public behavior unless that removal is deliberate and reviewed.

### 3. Port in dependency order

Typical layering:

1. pure data types and exceptions;
2. low-level process/filesystem/network adapters;
3. reusable services;
4. orchestrators and public APIs;
5. CLI/scripts and packaging;
6. source compatibility shims and later cleanup.

Each PR should compile/test independently or declare a precise dependency on the preceding PR. Do
not land a public wrapper whose imported implementation does not yet exist.

### 4. Adapt to destination conventions

- Use the destination's subprocess wrapper, logging, exceptions, path resolver, and CLI parser.
- Update the canonical dependency manifest and lockfile together.
- Preserve supported Python versions and type-checking policy.
- Replace production assertions used for narrowing with explicit exceptions.
- Avoid importing source-repository configuration or private infrastructure.

When replacing an SDK with a CLI, preserve structured data and failures:

```python
result = subprocess.run(
    ["gh", "api", endpoint],
    stdin=subprocess.DEVNULL,
    capture_output=True,
    text=True,
    check=False,
)
if result.returncode != 0:
    raise RuntimeError(f"GitHub query failed: {result.stderr.strip()}")
payload = json.loads(result.stdout)
```

Use argument arrays, existing authentication, validated JSON, and bounded execution. Do not replace
a typed SDK with shell-string interpolation or silently weaker error handling.

### 5. Merge divergent features instead of overwriting

Diff source and destination at function/test level. Classify each delta as source-only feature,
destination-only feature, equivalent implementation, incompatible policy, or obsolete behavior.
Add missing behavior to the destination's current structure and merge test cases. The destination
is the base; source files are evidence, not replacements.

### 6. Preserve compatibility only where consumed

After target CI passes, a source-repository shim may re-export moved symbols:

```python
"""Compatibility import; canonical implementation lives in target_package.module."""

from target_package.module import PortedClass as PortedClass

__all__ = ["PortedClass"]
```

Verify identity, import behavior, packaging, and downstream consumers. A shim that requires an
undeclared cross-repository dependency is not compatibility. Link a removal condition rather than
leaving permanent ambiguous ownership.

### 7. Adapt upstream skills with license and format provenance

Before copying an external skill:

- confirm repository and per-file license compatibility;
- inspect hooks, executable helpers, hardcoded paths, tool names, and frontmatter;
- search the destination corpus and open PRs for overlapping intent;
- merge into the canonical skill when overlap is substantive;
- preserve required copyright/license attribution;
- translate format and capabilities without inventing host-specific guarantees.

Do not import SessionStart hooks merely to force discovery when native skill retrieval already
provides it. Hook behavior is a product decision, not part of content porting by default.

### 8. Verify both repositories

In the destination, run focused tests, full relevant suite, lint, format, type checks, package build,
install/import/CLI smoke tests, and CI. In the source, run shim identity/import tests and downstream
checks. Confirm the lockfile corresponds to the canonical manifest and no private paths or credentials
entered copied content.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Copy source tree over destination | Deletes destination-only fixes and conventions | Diff behavior and implement on destination base |
| 2 | Start coding before destination audit | Duplicates existing commands/modules | Search by intent, API, entry point, and tests first |
| 3 | Port orchestrator before dependencies | Imports unresolved or requires temporary stubs | Migrate in dependency layers |
| 4 | Update local environment file only | CI installs from another canonical manifest | Update authoritative manifest and lockfile |
| 5 | Replace SDK with shell string | Quoting, injection, and error semantics regress | Use argv subprocess and structured validation |
| 6 | Delete source immediately after copy | Destination may not be merged or consumers migrated | Wait for green target CI, then shim and clean separately |
| 7 | Create duplicate skill for overlapping intent | Retrieval fragments and guidance diverges | Merge into canonical artifact |
| 8 | Copy upstream content without attribution | Violates license/provenance obligations | Audit license and preserve required notices |
| 9 | Treat staging copy as target truth | It may predate destination fixes | Rebase conceptually onto live destination |

## Results & Parameters

- Record immutable source and destination SHAs for every migration.
- Keep PRs dependency-ordered and independently testable; source cleanup is final.
- Destination behavior and conventions win unless the port intentionally changes them.
- Required gates: supported-runtime test matrix, lint/format, types, package/install smoke, lockfile,
  and CI.
- Source shims use explicit re-exports and remain only while consumers need them.
- External skills require overlap search, license audit, format adaptation, and attribution.

## Evidence Boundary

The indexed ports passed their recorded CI/local gates, but dependencies, licenses, host contracts,
and destination baselines vary. Re-run inventories and legal/technical compatibility checks for each
new source/destination pair.
