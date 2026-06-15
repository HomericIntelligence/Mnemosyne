---
name: ci-cd-missing-dependency-in-ci
description: "Handle missing system dependencies in CI containers. Use when: (1) CI fails with FileNotFoundError for system binaries, (2) subprocess calls crash in containerized CI, (3) validate scripts need graceful degradation."
category: ci-cd
date: 2026-06-12
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [ci, docker, container, git, subprocess, error-handling]
---

# CI/CD Missing Dependency Handling

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-12 |
| **Objective** | Fix CI failure where git binary was not available in CI container |
| **Outcome** | Fixed with two-layer defense: Python try/except plus shell command guard |
| **Verification** | verified-local |

## When to Use

- CI fails with FileNotFoundError for system binaries
- subprocess.run() calls crash in containerized CI environments
- Validation scripts need graceful degradation for optional tools

## Verified Workflow

### Quick Reference

Python: catch FileNotFoundError in subprocess calls. Shell: guard optional commands with command -v.

### Detailed Steps

1. Identify the failing call from CI logs
2. Add Python try/except FileNotFoundError with from None (ruff B904)
3. Add shell command -v guard in calling script
4. Validate locally with full test suite
5. Push and verify CI passes

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Python try/except alone | Wrapped subprocess call | Shell script treated ManifestError as hard failure | Need defense in both layers |
| sed to fix formatting | Used sed on Python file | Replaced ALL occurrences not just target | Use str_replace for targeted edits |

## Results & Parameters

Files modified: scripts/inferencex.py and scripts/validate.sh

Validation: 533 tests passed, 16 skipped, 80.09 percent coverage

Key: ruff B904 requires raise from None in except blocks
