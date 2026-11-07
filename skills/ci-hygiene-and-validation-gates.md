---
name: ci-hygiene-and-validation-gates
description: "Design lightweight CI guards, diagnose checks that pass without enforcing their intended invariant, or move an existing gate from required CI to a warning."
category: ci-cd
date: 2026-06-20
version: "2.2.0"
user-invocable: false
license: BSD-3-Clause
verification: verified-ci
tags: [ci, validation, regression-guard, required-check, schema, deprecation, stale-script, gitignore, two-sided-test, warn-downgrade, gate-owner, anti-suppression-guard]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/ci-hygiene-and-validation-gates.history"
history-cleanup-date: "2026-09-20"
---

# CI Hygiene and Validation Gates

## Overview

Small file-scan gates catch important drift before compilation, but only when their decision is
reachable and enforced. A green required check can still be dead code; a useful script can already
be wired; a heuristic detector should warn while a true invariant must fail.

The patterns remain `verified-ci`. Reusable decisions are here, project incidents in
[the notes](./ci-hygiene-and-validation-gates.notes.md), and exact prior content in
[history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/ci-hygiene-and-validation-gates.history).

## When to Use

- Deprecated names must not reappear after cleanup.
- Schema validation currently runs only in pre-commit or only on passed filenames.
- `scripts/*.py` contains possible orphaned utilities.
- A required check computes or prints a verdict but cannot fail.
- A check passes in a rich local environment but crashes or no-ops in the actual CI install.
- A gitignored `build/` or `dist/` directory must never contain tracked package inputs.
- An issue requests CI wiring that a prior PR may already have delivered.
- A new job name might be pinned in a live ruleset.
- A required check must change to a warning, for example when an owner moves a
  digest or evidence check from required CI to a release-acceptance step.

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

Two-sided verification is useful when adding or changing enforcement:

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

### Pattern 7: downgrade a required gate to a warning

Use this pattern only when the user or an owner asks for warning-only behavior. Do
not choose it to make a red check green. Before you change the exit code, record the
owner of each remaining failure.

1. Grep the repository for an anti-suppression guard. A required workflow and a test
   can both reject `continue-on-error`, `ignore_errors`, or a soft exit. Find the
   restriction and the allowed alternative before you plan a downgrade:

   ```bash
   grep -rnE "continue-on-error|forbid.?suppress|ignore_errors" .github/ tests/
   ```

2. Separate the check from its caller. A script may be a library that another check
   imports, or a step that a different required job runs. Grep each workflow for the
   script path and for the job it belongs to. Classify the real required context,
   not the file name.

3. Divide the verdicts into three classes and give each class a decision owner.

   | Class | Result | Owner of the decision |
   | --- | --- | --- |
   | Digests, checksums, and recorded-versus-observed identity | Warning to standard error, plus a list in the summary artifact | The named acceptance step |
   | Malformed, missing, or oversized evidence; input cannot be read | Failure | The check |
   | Objective invariant, such as a signature, a shape, or a required field | Failure | The check |

4. Keep one warning format and one place that writes it. A helper with a stable
   prefix makes the warning greppable in logs and in the summary.

5. Find every test that pins the old contract. A test can count the number of warning
   call sites or assert the non-zero exit. Change those tests with the source, and add
   one case that proves the warning path returns zero.

6. State the loss. A warning does not block a change. Record which file or record the
   acceptance step must read, for example a `warnings` array in an evidence summary.

```text
Digest difference  -> WARNING + summary list, exit 0
Bad evidence shape -> FAIL
Signed provenance  -> FAIL (required)
```

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
| Soft-fail by `continue-on-error` | Marked a step optional to stop the red check | An anti-suppression guard and tests rejected the step | Downgrade inside the script and keep the evidence shape fail-closed |
| Warning with no owner | Removed the failure and printed a message | No step read the message, so the difference was lost | Name the acceptance step that reads the summary list |
| Classify by file name | Treated a shared library as the required gate | Another check imported the library | Map each script to its real required job first |

## Results & Parameters

| Pattern | Exit policy | Essential test |
| --- | --- | --- |
| Deprecated identifier | Nonzero on scoped source hit | Clean plus injected name |
| Schema inventory | Nonzero on parse/schema/missing inventory | Valid plus malformed/invalid/zero-file |
| Stale-script discovery | Normally zero with candidate report | Known referenced and orphan fixtures |
| Required gate | Preserve pinned context; nonzero on contract breach | Exact CI clean/injected/restore sequence |
| Ignored scratch directory | Nonzero when `git ls-files <dir>/` is nonempty | Synthetic tracked fixture |
| Already-wired issue | No duplicate job; local cross-reference | Search confirms one canonical invocation |
| Warning downgrade | Zero on a byte or identity difference; nonzero on bad evidence shape and on the objective invariant | One warning case and one failure case per class |

## Verified On

- CI-backed implementations covered all six retained patterns.
- The warning-downgrade pattern comes from a planning review, not from a merged
  change. Its class table and anti-suppression step are read from live repository
  behavior. Treat the result as planned guidance until a downgrade merges.
- Exact project commands and outcomes are indexed in the notes.

## Companions

- [Case notes](./ci-hygiene-and-validation-gates.notes.md)
- [Version history and exact superseded snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/ci-hygiene-and-validation-gates.history)
