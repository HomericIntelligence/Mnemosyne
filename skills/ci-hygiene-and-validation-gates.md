---
name: ci-hygiene-and-validation-gates
description: "Use when adding lightweight CI guards for deprecated identifiers, schema drift, stale scripts, tracked files under ignored build directories, or local-to-CI discoverability; or when a named required check is green but asserts nothing. Verify the premise first, preserve pinned check contexts, choose warning versus hard failure from the invariant, mirror the exact CI environment, and prove enforcement with both clean-pass and synthetic-fail tests."
category: ci-cd
date: 2026-06-20
version: "2.0.0"
user-invocable: false
license: BSD-3-Clause
verification: verified-ci
history: ci-hygiene-and-validation-gates.history
tags: [ci, validation, regression-guard, required-check, schema, deprecation, stale-script, gitignore, two-sided-test]
---

# CI Hygiene and Validation Gates

## Overview

Small file-scan gates catch important drift before compilation, but only when their decision is
reachable and enforced. A green required check can still be dead code; a useful script can already
be wired; a heuristic detector should warn while a true invariant must fail.

The patterns remain `verified-ci`. Reusable decisions are here, project incidents in
[the notes](./ci-hygiene-and-validation-gates.notes.md), and exact prior content in
[history](./ci-hygiene-and-validation-gates.history).

## When to Use

- Deprecated names must not reappear after cleanup.
- Schema validation currently runs only in pre-commit or only on passed filenames.
- `scripts/*.py` contains possible orphaned utilities.
- A required check computes or prints a verdict but cannot fail.
- A check passes in a rich local environment but crashes or no-ops in the actual CI install.
- A gitignored `build/` or `dist/` directory must never contain tracked package inputs.
- An issue requests CI wiring that a prior PR may already have delivered.
- A new job name might be pinned in a live ruleset.

## Verified Workflow

### Quick Reference

```bash
# Find existing wiring before adding anything.
rg -n '<script-or-context>' .github/workflows/ justfile .pre-commit-config.yaml scripts/

# Inspect required contexts before rename/delete.
gh api repos/<owner>/<repo>/rulesets --paginate

# Whole-repository tracked-file invariant.
git ls-files build/
git check-ignore -v build/

# Execute repository checks exactly as CI does.
pre-commit run <hook-id> --all-files
```

### Pattern 1: deprecation regression guard

Search only relevant source/test roots, exclude generated/vendor paths, and filter comments or
docstrings only when the policy permits mentions there. Use the regex dialect actually invoked:
basic grep alternation is `\|`; extended grep is `|`. Prefer a small tested script when exclusions,
encodings, or language syntax make a pipeline ambiguous.

```bash
PATTERN='OldName1\|OldName2\|OldName3'
if grep -rn "$PATTERN" shared/ tests/ --include='*.mojo' \
    | grep -vE '^([^:]+:)?[[:space:]]*#' | grep -q .; then
  echo 'FAILED: deprecated identifier found'
  exit 1
fi
```

Use ASCII output in portable CI logs. Test with a clean tree and an injected forbidden identifier;
a clean pass alone cannot prove the failure path.

### Pattern 2: standalone schema validation

Run the schema tool against the complete canonical config inventory, not only changed filenames.
Place it in an existing syntax/static job when possible and install its real dependencies. Ensure
globs that match nothing fail or are handled explicitly rather than silently validating zero files.
Test valid, malformed, schema-invalid, and undiscovered-file cases.

### Pattern 3: stale-script discovery

Build a reference graph from tracked workflow, task-runner, hook, test, and script files. Normalize
module imports separately from executable filenames. Because legitimate one-time scripts may be
unreferenced, report candidates and exit zero unless repository policy defines a complete executable
registry. A heuristic discovery tool is not an invariant gate.

### Pattern 4: repair a dead required gate in place

Read the live ruleset before deleting or renaming a context. If the context is pinned, either make
the existing job enforce its named contract or coordinate the ruleset change first. Trace every
branch from computed verdict to process exit.

Mirror exact CI installation and invocation. A convenient pixi environment can mask a missing
declared dependency in `pip install -e .`; `--no-deps` can turn a policy assertion into an import
crash under `set -e`. Use the repository-pinned tool version and a proven command such as
`pixi install --locked`, not a newer local flag.

Two-sided verification is mandatory:

1. clean fixture exits zero;
2. inject one targeted violation and require nonzero;
3. restore and require zero again;
4. assert the synthetic path reaches the intended diagnostic, not an unrelated crash.

### Pattern 5: tracked files under an ignored scratch directory

The invariant is tracking, not on-disk existence. Long-running tools may continually regenerate
ignored logs, so deleting them is unrelated and potentially destructive. A whole-repo checker uses
`git ls-files <dir>/`, exits nonzero for any row, and runs with `pass_filenames: false` and
`always_run: true`. Confirm the ignore rule with `git check-ignore -v`.

This is a hard failure because a tracked scratch artifact can enter packaging. Test clean and
synthetic tracked-file states. Never use cleanup commands as the enforcement mechanism.

### Pattern 6: already-wired behavior

Before editing workflows, search by script, task, and context. If CI already runs the script, do not
duplicate it or close the issue with no improvement. Add a concise cross-reference above the local
just/Make recipe pointing to the existing CI job when discoverability is the actual gap. Verify the
comment and the workflow invocation reference the same canonical script.

### Final gate audit

For every new or repaired gate record: invariant, scope, exclusions, trigger, environment,
dependencies, required-context ownership, clean result, synthetic-failure result, and rollback. Run
the repository required suite after restoring all synthetic changes.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Single raw grep | Scanned without syntax-aware exclusions | Comments produced false positives | Define dialect and exclusions explicitly |
| New workflow for each guard | Added another standalone workflow | Increased context and maintenance drift | Prefer an existing compatible required job |
| Hard-fail stale discovery | Treated every orphan candidate as invalid | Legitimate setup scripts blocked commits | Heuristics warn; proven invariants fail |
| Delete a pinned job | Removed a no-op required check | PRs waited forever for its context | Repair in place or update ruleset first |
| Verify only clean pass | Saw green and called the gate fixed | Dead gates are also green | Require a targeted synthetic failure |
| Test in rich environment | Used pixi instead of the actual CI install | Missing dependency was masked | Mirror exact install and interpreter |
| Use unverified tool flag | Chose `pixi lock --check` | Pinned pixi did not have proven support | Use commands verified on the pinned version |
| Delete ignored logs | Cleaned `build/` repeatedly | Producer recreated them; tracking was the real risk | Guard `git ls-files`, preserve runtime state |
| Soft-warn true invariant | Copied stale-script exit-zero behavior | Tracked package contamination passed | Hard-fail objective invariants |
| Rewire already-wired script | Added a duplicate CI invocation | Prior PR already owned the gate | Search first; close only the discoverability gap |

## Results & Parameters

| Pattern | Exit policy | Essential test |
| --- | --- | --- |
| Deprecated identifier | Nonzero on scoped source hit | Clean plus injected name |
| Schema inventory | Nonzero on parse/schema/missing inventory | Valid plus malformed/invalid/zero-file |
| Stale-script discovery | Normally zero with candidate report | Known referenced and orphan fixtures |
| Required gate | Preserve pinned context; nonzero on contract breach | Exact CI clean/injected/restore sequence |
| Ignored scratch directory | Nonzero when `git ls-files <dir>/` is nonempty | Synthetic tracked fixture |
| Already-wired issue | No duplicate job; local cross-reference | Search confirms one canonical invocation |

## Verified On

- CI-backed implementations covered all six retained patterns.
- Exact project commands and outcomes are indexed in the notes.

## Companions

- [Case notes](./ci-hygiene-and-validation-gates.notes.md)
- [Version history and exact superseded snapshot](./ci-hygiene-and-validation-gates.history)
