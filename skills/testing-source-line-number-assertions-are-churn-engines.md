---
name: testing-source-line-number-assertions-are-churn-engines
license: BSD-3-Clause
description: "A test that asserts an exact SOURCE LINE NUMBER (`inspect.getsourcelines(fn)[1] == <literal>`, `fn.__code__.co_firstlineno == N`, or a doc `path:LINE function` reference pinned against the current source line) is a churn engine — REMOVE it and assert symbol presence/resolution instead. Any edit above the function shifts its line number and fails the test with zero behavior change; under concurrent merging the correct line is only knowable at the merge instant, so no PR author (human or agent) can pin it ahead of time. Use when: (1) a doc/regression test fails only because a line number drifted, (2) a PR keeps re-conflicting on a doc that hardcodes `file.py:NNN`, (3) you see `getsourcelines(...)[1]` or `co_firstlineno` compared to a constant in tests, (4) an automation loop keeps force-pushing a wrong-line-number CI fix, (5) you are designing the systemic guard that bans the anti-pattern. v1.1.0 adds the guard design: a blanket AST ban on any `getsourcelines/findsource(...)[1]` subscript or `.co_firstlineno` access in tests (compare-only checks miss variable indirection), a fence-aware `\\.py:\\d+` regex guard over living docs excluding point-in-time records (ADRs, release notes), and a pre-push CI-fix test gate that MUST treat pytest exit code 5 (no tests ran) as pass — otherwise deleting the churn-engine test deadlocks the gate against its own fix."
category: testing
date: 2026-07-16
version: "1.1.0"
user-invocable: false
verification: verified-ci
history: testing-source-line-number-assertions-are-churn-engines.history
tags:
  - line-number-assertion
  - getsourcelines
  - co-firstlineno
  - churn-engine
  - doc-guard
  - regression-test
  - merge-conflict
  - concurrency
  - symbol-presence
  - lint-guard
  - ast-guard
  - pre-push-test-gate
  - hephaestus
---

# Testing: Source-Line-Number Assertions Are Churn Engines

**History:** [changelog](./testing-source-line-number-assertions-are-churn-engines.history)

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-12 |
| **Objective** | Stop a doc/regression test that pinned each documented `path:LINE function` reference to the function's CURRENT source line (`inspect.getsourcelines(fn)[1]`) from manufacturing merge conflicts and stranding a PR across rebase rounds |
| **Outcome** | Successful — removed the test, stripped the volatile `:LINE` from the doc's function references (kept `path function` for navigation), removed the now-unused imports/list, and filed a systemic lint-guard follow-up. Merged into Hephaestus PR #2056 (commit `79f9ebb3`) which then had 0 real CI failures |
| **Verification** | verified-ci |

> **v1.1.0 (2026-07-16) — planning-stage additions.** The removal workflow above is
> `verified-ci` (Hephaestus PR #2056). The **Systemic Guard Design** section below is the
> reviewed implementation plan for the follow-up guard (Hephaestus #2122) and is
> **`unverified`** — the guards were designed against the live codebase (all cited
> file/line anchors grep-verified) but had not yet merged and run in CI when captured.
> Treat its design decisions as strong hypotheses until #2122's PR merges green.

## When to Use

- A doc or regression test fails **only** because a line number drifted — the referenced code has zero behavior change.
- A PR keeps re-conflicting on a doc that hardcodes `file.py:NNN`, and every rebase round the "correct" number moves again.
- You see `inspect.getsourcelines(x)[1]` (or `x.__code__.co_firstlineno`) compared to a literal constant anywhere under `tests/`.
- An automation loop / CI-fix mesh keeps force-pushing a branch that "fixes" a line number and then fails the exact test it was fixing.
- You are reviewing a new test that pins a documented `path:LINE symbol` reference against the live source line — flag it before it lands.
- **(v1.1.0, planning-stage)** You are implementing the systemic guard itself — an AST/lint ban, a doc-ref guard, or a pre-push test gate for a CI-fix mesh — and need the design decisions that keep the guard from being vacuous, false-positive-prone, or self-deadlocking.

## Verified Workflow

### Quick Reference

```bash
# 1. Find the offending assertions (the churn engines) across the test suite.
grep -rnE 'getsourcelines\([^)]*\)\[1\]|co_firstlineno' tests/

# 2. REMOVE the test that compares a line number to a literal / to a doc ref.
#    Then de-line the doc: keep `path function` for navigation, drop `:LINE`.
#    e.g.  `automation_loop.py:344 get_impl_resume_feedback_prompt`
#      →    `automation_loop.py get_impl_resume_feedback_prompt`

# 3. Delete the now-unused imports/data the test depended on, or ruff F401/F811 fails.
#    (inspect, re, the PROMPT_REFS list, the imported functions, etc.)
pixi run ruff check tests/ hephaestus/

# 4. Confirm the suite is green WITHOUT the line-number test.
pixi run pytest tests/unit/docs -q
```

### Detailed Steps

1. **Recognize the anti-pattern.** A test that does `inspect.getsourcelines(fn)[1] == <literal>`, `fn.__code__.co_firstlineno == N`, or parses a doc `` `path:LINE function` `` reference and asserts the `LINE` equals the function's current source line is asserting an **implementation detail (line position)**, not behavior. It is a churn engine.

2. **Understand why it is catastrophic under concurrency.** Any edit ABOVE the function — a new import, a comment, a reformat, a reorder — shifts its line number and fails the test with zero behavior change. The "correct" line is only knowable at the INSTANT OF MERGE (it depends on what else lands). No author, human or agent, can pin it ahead of time. Every sibling PR that merges and touches the referenced file moves the function's line (e.g. `get_impl_resume_feedback_prompt`: :338 → :342 → :344), re-failing the test on EVERY open PR carrying the doc. This manufactures merge conflicts out of nothing.

3. **Remove the test — do not chase the value.** Delete the assertion. If line references aid navigation, strip only the volatile `:LINE` from the doc and keep the STABLE `path function` part.

4. **Clean up the dependencies the test pulled in.** Remove the now-unused imports (`inspect`, `re`), any reference list (`PROMPT_REFS`), and the imported functions — otherwise ruff fails on unused imports (F401) or redefinitions.

5. **Prevent recurrence systemically.** File a lint/AST guard that REJECTS any `getsourcelines(...)[1]` or `co_firstlineno` compared to a literal in `tests/`. If line refs are wanted for navigation, GENERATE them via a self-healing pre-commit hook — never ASSERT them (blocking). Assert **symbol presence / resolution** instead: that the function imports and `hasattr(module, "fn")` resolves. See the **Systemic Guard Design** section below for the reviewed design of all three guards.

## Systemic Guard Design (v1.1.0 — planning-stage, unverified)

The reviewed implementation plan for Hephaestus #2122 (the follow-up filed by the verified fix
above). Three guards; each has a non-obvious design decision that a naive implementation gets
wrong.

### Guard 1 — AST ban in tests: blanket ban, not compare-only

The issue asks to reject `getsourcelines(...)[1] == <literal>`. Do NOT implement that literally:
a Compare-only check misses **variable indirection** —
`n = inspect.getsourcelines(f)[1]; assert n == doc_line` has no banned Compare node. When a
repo-wide grep shows zero current uses (run it first), ban ANY occurrence in `tests/` of:

- an `ast.Subscript` with constant index `1` over a call to `getsourcelines` **or** `findsource`
  (both return `(lines, lnum)` — `findsource` is the same hole under another name), and
- any `ast.Attribute` access of `co_firstlineno`.

Implementation notes that keep the guard sound:

- **Self-tests can't trip the guard.** Synthetic banned patterns inside the guard's own test file
  live in *string literals* passed to `ast.parse(...)`; string contents produce no
  `Subscript`/`Attribute` nodes, so no self-exemption is needed.
- **Add a synthetic-source negative test** (parse a string containing violations, assert they are
  collected) so a broken collector cannot pass vacuously — same pattern as
  `test_zero_io_imports.py::test_forbidden_detects_synthetic_forbidden_import`.
- **Ship an empty `_ALLOWLIST` frozenset** for future sanctioned uses, mirroring the repo's other
  AST guards, so an exemption is a reviewed one-line diff instead of a guard rewrite.
- `getsourcelines(...)[0]` (the source *text*) stays legal — only the line-number element is banned.

### Guard 2 — doc-ref guard: fence-aware regex over LIVING docs only

Regex `\.py:\d+` over `docs/**/*.md`, with two scoping decisions:

- **Skip fenced code blocks** (track ``` fence state per line). Example tool output like
  `file.py:12: error` inside a fence is legitimate and would false-positive.
- **Exclude point-in-time records** (`docs/adr/`, `docs/release-notes/`). ADR line refs are
  historical citations of the code *as it was decided*, not navigable claims that must track
  HEAD; forcing them to de-line rewrites history for zero benefit.

The generator hook (self-healing line refs) stays optional — YAGNI unless someone actually wants
line-precise navigation; `path function` refs are grep-able and stable.

### Guard 3 — pre-push CI-fix test gate: exit-code-5 is PASS, param IDs are truncated

The CI-fix mesh must re-run the failing tests locally before force-pushing. Parse failing pytest
node IDs from the CI logs (`FAILED|ERROR <path>::<node>` summary lines), then run exactly those in
the worktree and refuse the push on failure. Three decisions prevent the gate from fighting itself:

- **pytest exit code 5 ("no tests ran") is a PASS.** The fix/rebase may have legitimately
  *deleted* the failing test — that was exactly the #2056 remedy. Treating 5 as failure deadlocks
  the gate against the very fix this skill prescribes. Also drop node IDs whose file no longer
  exists in the worktree before invoking pytest.
- **Truncate parametrized IDs at `[`.** Running `test_a` instead of `test_a[param-1]` is a safe
  superset and survives param renames across the rebase; an exact stale param ID makes pytest
  error with "unknown node id" and falsely blocks the push.
- **Gate the agent CI-fix push path, not mechanical rebases of green PRs.** The mechanical-rebase
  path has no CI-failure logs in scope (it runs on BEHIND/green PRs) and already defers to the
  gated agent path on any conflict. Gate where the failure evidence exists.

Coverage-contract note (Hephaestus-specific but generalizable): when the orchestrator module is on
a coverage omit list, the log-parsing helper must be a module-level pure function with its own unit
tests (mocked `subprocess.run` for the gate method) — the omit list excuses the live loop, never
the helpers.

### Design pitfalls avoided (near-misses from the planning review)

| Naive design | Why it fails | Correct design |
|--------------|--------------|----------------|
| Ban only `getsourcelines(...)[1] == <literal>` Compare nodes | Variable indirection (`n = ...[1]; assert n == x`) has no banned Compare | Blanket-ban the subscript/attribute anywhere in `tests/` (safe when grep shows zero uses) |
| Guard only `getsourcelines` | `inspect.findsource(fn)[1]` returns the same line number | Ban both functions' `[1]` subscript |
| Regex-scan whole doc files | Fenced example output (`file.py:12: error`) false-positives | Track fence state; scan prose lines only |
| De-line ADRs too | ADRs are point-in-time records; their line refs are historical citations | Exclude `docs/adr/` and `docs/release-notes/` from the guard |
| Pre-push gate treats exit code 5 as failure | The fix that DELETES the churn-engine test "fails" the gate → self-deadlock | Exit code 5 (and vanished test files) = pass |
| Run exact parametrized node IDs from CI logs | Param renamed by the rebase → pytest "unknown node id" error blocks the push | Truncate at `[`; run the whole test function |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Bump the stale line number | Changed doc `:342` → `:344` to match the current source | The next merge touching the file shifted it again — endless churn | Fixing the value doesn't fix the design; the line number is a moving target under concurrency |
| Let the automation loop re-rebase it | The mesh's ci_fix_orchestrator rebased + force-pushed to "fix CI" | It computed the line wrong and pushed a branch failing the exact test it was fixing, then looped | Never assert a value only knowable at merge instant; never force-push a CI-fix without re-running the guard test locally |
| Keep the test, relax nothing | Treated the red test as a real regression to satisfy | The test guards documentation formatting against an implementation detail (line position), not behavior | Assert symbol presence / that the function RESOLVES (import + hasattr), never a line number |

## Results & Parameters

**The anti-pattern (observed on Hephaestus):**
`tests/unit/docs/test_automation_loop_architecture.py::test_issue_1929_prompt_line_refs_match_source_definitions` asserted every `` `path:LINE function` `` reference in a markdown doc exactly equals `inspect.getsourcelines(fn)[1]` — the function's CURRENT source line.

**Detection command (copy-paste):**

```bash
grep -rnE 'getsourcelines\([^)]*\)\[1\]|co_firstlineno' tests/
```

**The fix (verified-ci, merged in Hephaestus PR #2056, commit `79f9ebb3`):**

- REMOVE the test.
- Strip the volatile `:LINE` from the doc's function references; keep `path function` for navigation.
- Remove the now-unused imports / reference list the test depended on (or ruff fails on unused imports).
- Systemic prevention (filed as Hephaestus #2122): a lint/AST guard rejecting `getsourcelines(...)[1]` / `co_firstlineno` compared to a literal in `tests/`; GENERATE nav line refs via a pre-commit hook (self-healing), never ASSERT them (blocking).

**The durable rule:** documentation line references are for NAVIGATION (generate them, self-healing), not for ASSERTION (blocking). Assert the STABLE invariant — the symbol exists and resolves — never the volatile one (where it currently sits in the file).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PR #2056, commit `79f9ebb3` (follow-up guard filed as #2122) | Removed `test_issue_1929_prompt_line_refs_match_source_definitions`, de-lined the doc's `path:LINE function` refs to `path function`, dropped the unused `inspect`/`re`/`PROMPT_REFS` deps. PR then had 0 real CI failures after multiple rebase rounds that the line-number test had been re-failing |
