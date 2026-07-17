---
name: github-actions-python-required-checks
description: "Create or repair required GitHub Actions checks and tag releases for a Python repository using Hephaestus as the control-pattern reference. Use when: (1) a Python repo needs a required merge gate, (2) CI must be brought up to fail-closed policy, (3) a tag-only release workflow is needed"
category: ci-cd
date: 2026-07-16
version: "1.0.0"
user-invocable: false
tags: [github-actions, python, ci, required-checks, release]
---

# GitHub Actions for Python Repositories

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-16 |
| **Objective** | Standard workflow for setting up fail-closed required checks and tag-only releases in Python repositories |
| **Outcome** | Operational — migrated from the Athena `github-actions-python-cicd` skill into standard knowledge |

## When to Use

- Creating or repairing required checks in a Python repository.
- Setting up a tag-only release workflow.
- The target repository remains authoritative for its languages, package layout, commands, and release channel.

## Required reference

Prepare Hephaestus at `$HOME/.agent_brain/automation` by following Athena's canonical dependency-resolution contract exactly. Report repository, SHA, and trust basis; any preparation or revalidation failure is blocking. Read the resolved checkout's current `_required.yml`, release workflow, `.github/CODEOWNERS`, and local policies. Treat them as control-pattern guidance, not copy-ready package commands.

## Verified Workflow

### Discover the target contract

Read `AGENTS.md`, manifests, lockfiles, task runners, existing workflows, supported Python classifiers, test layout, release documentation, GitHub Actions settings, and rulesets. Determine:

- Bootstrap and locked-install command.
- Formatting, lint, typing, unit/integration, build, install-smoke, and security commands.
- Supported runners/Python matrix.
- Artifact and publication channel.
- Required PR policy and branch-protection contexts.

Ask when these sources conflict; never substitute Hephaestus package paths.

### Required workflow design

1. Use `.github/workflows/_required.yml` as the canonical merge gate.
2. Pin third-party Actions to immutable commits with readable version comments.
3. Set least-privilege permissions, timeouts, and concurrency cancellation.
4. Fail closed: no `continue-on-error`, swallowed exit codes, or advisory replacement for a gate.
5. Separate meaningful jobs such as lint, tests, build/package, install smoke, dependency/security scans, workflow schema, version/lock sync, and PR policy.
6. Fan every gating job into `required-checks-gate` with `if: always()` and explicit result checks.
7. Use a tag-only release workflow that reruns the release contract and publishes only validated artifacts.
8. Put `CODEOWNERS` at `.github/CODEOWNERS` and cover workflows, package metadata, source, tests, scripts, and policy files.
9. Verify workflows against the GitHub schema and inspect live Actions/ruleset configuration.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Copying reference commands | Reusing Hephaestus package commands in the target repo | Package names, layouts, and runners differed | The reference provides control patterns; the target defines every command |
| Advisory gates | `continue-on-error: true` on flaky jobs | The merge gate stopped gating | Fail closed; fix or quarantine flakes explicitly |

## Results & Parameters

### Expected Output

Report the resolved reference SHA, discovered target contract, jobs and contexts created, pin and permission choices, commands run, live settings still requiring operator action, and rollback.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Athena | Shipped as the `github-actions-python-cicd` plugin skill; applied across HomericIntelligence Python repositories | Migrated 2026-07-16 |

## References

- Athena dependency-resolution contract: `docs/dependency-resolution.md` in HomericIntelligence/Athena
- Related: [python-repo-modernization-workflow.md](python-repo-modernization-workflow.md)
