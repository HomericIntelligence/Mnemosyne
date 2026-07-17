---
name: python-repo-modernization-workflow
description: "Modernize a Python repository with mixed legacy and modern practices, following the target's product requirements. Use when: (1) a Python repo mixes legacy and modern tooling, (2) packaging/typing/CI need alignment without breaking public behavior, (3) release artifacts must be verified outside the checkout"
category: tooling
date: 2026-07-16
version: "1.0.0"
user-invocable: false
tags: [python, modernization, packaging, typing, migration]
---

# Python Repository Modernization

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-16 |
| **Objective** | Standard workflow for modernizing a Python repository without breaking public behavior |
| **Outcome** | Operational — migrated from the Athena `python-repo-modernization` skill into standard knowledge |

## When to Use

- A Python repository has mixed legacy and modern practices. Modernization follows the target's product requirements; it is not a mechanical conversion to one package layout.

## Required reference

Prepare Hephaestus at `$HOME/.agent_brain/automation` by following Athena's canonical dependency-resolution contract exactly. Report repository, SHA, and trust basis; any preparation or revalidation failure is blocking. Use the resolved checkout to study current policy, typing, testing, CI, security, and release patterns. Substitute the target repository's package name, source layout, commands, and publication model everywhere.

## Verified Workflow

### Detailed Steps

1. Establish a green or honestly documented baseline: imports, tests, coverage, lint, typing, build, installed-artifact smoke test, dependency audit, and workflow state.
2. Read public API and compatibility requirements before moving modules or removing shims.
3. Fix correctness and circular-import issues with regression tests first.
4. Select flat or `src/` layout based on the target's import and packaging needs; do not impose the reference layout.
5. Align tests with behavioral boundaries. Require focused unit/error tests and integration or installed-artifact tests where they catch distinct failures.
6. Centralize tool configuration and commit the authoritative dependency lock.
7. Add typed-package metadata only when the package ships inline types.
8. Add fail-fast pre-commit and required GitHub checks (see the GitHub Actions for Python knowledge entry).
9. Build the actual release artifacts, inspect contents, install them outside the checkout, and verify public imports/commands.
10. Document supported versions, installation, upgrades, compatibility, release, and rollback.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Layout-first conversion | Imposing `src/` layout because the reference used it | Broke the target's import contract | Choose layout from the target's import and packaging needs |
| Coverage gaming | Excluding hard modules to keep the coverage number | Hid untested correctness risks | Never lower coverage merely to pass; justify exclusions with tests |

## Results & Parameters

### Guardrails

- Preserve public behavior unless a breaking change and migration are explicitly approved.
- Do not hide failing tests, lower coverage merely to pass, or exclude hard modules without tested justification.
- Do not mix environment managers over one site-packages tree.
- Never claim PyPI or another registry publication without a real authenticated publish result.

### Expected Output

Return the resolved reference SHA, baseline, modernization decisions, compatibility impact, files changed, exact gate results, artifact inspection/install evidence, and remaining release actions.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Athena | Shipped as the `python-repo-modernization` plugin skill; applied across HomericIntelligence Python repositories | Migrated 2026-07-16 |

## References

- Athena dependency-resolution contract: `docs/dependency-resolution.md` in HomericIntelligence/Athena
- Related: [github-actions-python-required-checks.md](github-actions-python-required-checks.md)
