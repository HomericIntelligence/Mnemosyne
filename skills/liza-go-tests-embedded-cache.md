---
name: liza-go-tests-embedded-cache
description: "Run and debug Liza Go tests in local/sandboxed environments. Use when Go tests fail on missing embedded contracts or skills, cannot write the default Go cache, or show flaky internal/gitenv timeout behavior during Liza validation."
category: testing
date: 2026-05-16
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - liza
  - go
  - tests
  - embedded
  - gocache
---

# Liza Go Tests Embedded Cache

## Overview

Objective: run Liza's Go tests reliably while validating source changes from a sandboxed or restricted local environment.

Outcome verified locally: focused Liza test suites passed after refreshing embedded assets and setting `GOCACHE` to a writable path.

## When to Use

- Liza Go tests fail with `pattern contracts/*.md: no matching files found`.
- `go test` fails with permission errors under `~/Library/Caches/go-build`.
- A Liza change touches orchestration, commands, embedded assets, or agent behavior and needs local verification.
- A full `go test ./...` or pre-push hook fails once in `internal/gitenv` with a one-second timeout, but focused reruns may distinguish a flaky timeout from a real regression.

## Verified Workflow

### Quick Reference

```bash
make sync-embedded
GOCACHE=/tmp/liza-go-build-cache go test ./internal/ops ./internal/agent ./internal/commands
GOCACHE=/tmp/liza-go-build-cache go test ./internal/gitenv -run TestOutputWithTimeout_ReturnsStdoutOnly -count=1 -v
GOCACHE=/tmp/liza-go-build-cache go test ./internal/gitenv -count=1
```

### 1. Refresh embedded files first

Run `make sync-embedded` before testing or building when Liza source expects generated embedded copies.

The `internal/embedded` package uses `go:embed` patterns for generated content such as contracts, skills, and support docs. If those generated copies are absent, unrelated package tests fail during compile.

### 2. Use a writable Go build cache

Set `GOCACHE` to a path that the current sandbox can write:

```bash
GOCACHE=/tmp/liza-go-build-cache go test ./internal/ops ./internal/agent ./internal/commands
```

This avoids false failures from permission-denied writes to the default user cache path.

### 3. Test focused packages first

For orchestration and handoff changes, start with the packages that cover the behavior:

```bash
GOCACHE=/tmp/liza-go-build-cache go test ./internal/ops ./internal/agent ./internal/commands
```

If the full suite or a pre-push hook fails in `internal/gitenv`, rerun that package and the named failing test directly before blaming the current change:

```bash
GOCACHE=/tmp/liza-go-build-cache go test ./internal/gitenv -run TestOutputWithTimeout_ReturnsStdoutOnly -count=1 -v
GOCACHE=/tmp/liza-go-build-cache go test ./internal/gitenv -count=1
```

### 4. Report validation honestly

If focused suites pass but full `go test ./...` fails once on the `internal/gitenv` one-second timeout, document:

- the failing command,
- the failing test name,
- the focused rerun results,
- whether the failure is related to the files changed.

Do not hide the full-suite failure in the PR or handoff.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Attempt 1 | Ran bare `go test` in the sandbox | The default Go build cache was outside the writable sandbox | Set `GOCACHE=/tmp/liza-go-build-cache` |
| Attempt 2 | Ran tests before refreshing embedded assets | Generated embedded copies were missing | Run `make sync-embedded` first |
| Attempt 3 | Treated a single full-suite `internal/gitenv` timeout as conclusive | The test has a one-second timeout and passed on focused rerun | Rerun the named test and package with `-count=1`, then document the evidence |
| Attempt 4 | Waited for a hook with an unrelated timeout to pass | The hook did not distinguish unrelated flaky validation from the change under review | Push with explicit documentation only after focused validation passes |

## Results & Parameters

Verified commands:

```bash
make sync-embedded
GOCACHE=/tmp/liza-go-build-cache go test ./internal/ops ./internal/agent ./internal/commands
GOCACHE=/tmp/liza-go-build-cache go test ./internal/gitenv -run TestOutputWithTimeout_ReturnsStdoutOnly -count=1 -v
GOCACHE=/tmp/liza-go-build-cache go test ./internal/gitenv -count=1
```

Observed caveats:

- Full `go test ./...` previously hit an unrelated `internal/gitenv` one-second timeout once.
- Direct focused reruns of the failing `internal/gitenv` test and package passed.
- `make sync-embedded` was required before build/test because `internal/embedded` expects generated `contracts`, `skills`, and `support-docs` copies.

## Verified On

| Project | Evidence |
| --- | --- |
| `liza-mas/liza` | Used while validating Liza PR `https://github.com/liza-mas/liza/pull/70` |
