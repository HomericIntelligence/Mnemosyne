---
name: documentation-markdownlint-table-cell-pipe-escape
description: "Use when: (1) markdownlint reports MD056/table-column-count
  'Expected: N; Actual: N+2; Too many cells' on a single row that visually has
  the correct number of `|` separators, (2) the offending row contains an inline
  code span with GitHub Actions / shell / template syntax using `||` or `|` such
  as `${{ a && '1' || '0' }}` or `cmd | other`, (3) you assumed backticks would
  protect `|` inside a table cell but markdownlint still counts them as cell
  separators, (4) CI is failing across multiple PRs on the same pre-existing
  file and you need to confirm it is not a PR-introduced regression before
  rebasing"
category: documentation
date: 2026-05-18
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - markdownlint
  - MD056
  - tables
  - inline-code
  - pipe-escape
  - ci-unblocking
  - github-actions
---

# Markdownlint Table Cell Pipe Escape Inside Inline Code

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-18 |
| **Objective** | Fix markdownlint MD056 firing on a 4-column table row whose only "extra cells" come from `\|\|` inside a backtick-wrapped GitHub Actions expression |
| **Outcome** | Fixed by escaping `\|\|` as `\|\|` (each pipe backslash-escaped) inside the inline code span; 0 markdownlint errors locally; CI confirmation pending on PR #1755 |
| **Verification** | verified-local (CI lint job pending on HomericIntelligence/ProjectMnemosyne#1755) |

## When to Use

Apply this pattern when:

1. **MD056 fires on a table row with backticks containing `|`** — counterintuitive because the inline code span looks like it should protect the pipe
2. **CI error reads** `MD056/table-column-count Table column count [Expected: 4; Actual: 6; Too many cells, extra data will be missing]` — the delta (Actual - Expected) equals the number of literal `|` chars inside backticks on that row (each `|` adds one phantom cell; `||` adds two)
3. **Multiple open PRs all fail on the same file/line** — strong signal the bug is in `main`, not PR-introduced; verify before rebasing
4. **The cell renders correctly on GitHub** — GitHub Flavored Markdown renders the inline code fine, so the bug is invisible until markdownlint runs in CI

## Verified Workflow

### Quick Reference

Copy-paste fix: inside an inline code span (between backticks) inside a markdown table cell, escape every `|` as `\|`.

```markdown
<!-- BEFORE (MD056 fires: 4-column table, this row has 6 cells) -->
| Attempt | Tried | Why Failed | Lesson |
| ------- | ----- | ---------- | ------ |
| GHA expr | Used `${{ inputs.x && '1' || '0' }}` | n/a | n/a |

<!-- AFTER (passes MD056) -->
| Attempt | Tried | Why Failed | Lesson |
| ------- | ----- | ---------- | ------ |
| GHA expr | Used `${{ inputs.x && '1' \|\| '0' }}` | n/a | n/a |
```

The HTML entity `&#124;` also works but renders as the entity itself inside backticks (since backticks suppress entity decoding), so `\|` is preferred for table cells with inline code.

### Step 1 — Diagnose

Read the CI error carefully. The format is:

```text
<file>:<line>:<col> MD056/table-column-count Table column count [Expected: N; Actual: M; Too many cells, ...]
```

If `M - N == count of '|' inside backticks on that line`, this is your bug.

### Step 2 — Confirm not PR-introduced

Before rebasing or blaming a PR, diff the failing file against `main`:

```bash
gh pr diff <PR_NUM> --repo <owner>/<repo> -- <failing-file>
```

If the file is unchanged in every failing PR, the bug is in `main` and needs its own fix PR. Do not rebase.

### Step 3 — Apply escape

Replace each `|` inside backticks on the offending row with `\|`. Leave structural pipes (the cell separators) alone.

### Step 4 — Validate locally

```bash
markdownlint-cli2 --config .markdownlint.yaml <file>
```

Expect exit code 0.

### Step 5 — Land the fix

Single-file PR; CI on every open PR that branches from a fixed `main` will go green after rebase.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Assumed PR-introduced regression | Saw 5 open PRs (#1751, #1752, #1753, #1754, #1724) all failing markdownlint on the same file and assumed one of them introduced it; planned to rebase each | The failing file (`skills/ci-cd-gated-debug-instrumentation-workflow-dispatch.md`) was untouched by every PR — the bug had been merged to main earlier and only surfaced after a markdownlint version bump | Always `gh pr diff <num> -- <file>` to confirm a PR changed the failing file before blaming/rebasing the PR |
| Wrapped expression in HTML code tags | Tried using HTML `<code>...</code>` markup instead of backticks, hoping HTML would protect the pipe characters | markdownlint MD056 tokenizes the row on `\|` before HTML parsing — bare pipe inside HTML code tags is still counted as a cell separator | Tag substitution does not help; backslash-escape each pipe individually |
| Used HTML entity for pipe | Replaced pipes with `&#124;` inside the backticks | Backticks render the entity verbatim — readers see the literal entity text instead of a pipe in the rendered table | Use `&#124;` only outside backticks; inside inline code, use backslash-escape |
| Tried `--fix` on markdownlint-cli2 | Ran `markdownlint-cli2 --fix '**/*.md'` hoping autofix would handle MD056 | MD056 has no autofix implementation — `--fix` reports 0 modifications and the error persists | Manual escape required; do not waste time on autofix for MD056 |

## Results & Parameters

### Reproducer

```markdown
| A | B | C | D |
| - | - | - | - |
| x | y | `cmd \|\| other` | z |
```

`markdownlint-cli2 --config .markdownlint.yaml file.md` → exit 0.

Without the backslashes, same row → `MD056 Expected: 4; Actual: 6`.

### Tooling versions verified

| Tool | Version | Result |
| ---- | ------- | ------ |
| markdownlint-cli2 | 0.20.0 (local) | 0 errors after escape |
| markdownlint-cli2 | 0.22.1 (CI) | confirmation pending on PR #1755 |
| markdownlint | 0.40.0 (CI underlying) | confirmation pending |

### When NOT to use this skill

- If the error is `Expected: N; Actual: N-K` (too FEW cells), this is unrelated — usually a missing trailing `|` on the row.
- If `M - N` does not equal the count of `|` inside backticks, look for additional unescaped `|` elsewhere on the line.
- For bulk fixes across hundreds of files, see `markdown-linting-bulk-table-format-fix` instead.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectMnemosyne | PR #1755 — `fix/markdownlint-table-pipe-escape` unblocks 5 other PRs (#1751, #1752, #1753, #1754, #1724) | File: `skills/ci-cd-gated-debug-instrumentation-workflow-dispatch.md` line 107 |
