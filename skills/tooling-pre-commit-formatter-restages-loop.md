---
name: tooling-pre-commit-formatter-restages-loop
description: 'Detect and fix the silent-formatter-restage bug where a pre-commit
  formatter (mojo-format, ruff format, black, prettier, custom shell hooks) rewrites
  staged files during the hook but does not re-stage them. The commit succeeds with
  pre-formatter content while the formatter''s output sits unstaged in the working
  tree. Use when: git status shows an unstaged whitespace/blank-line diff immediately
  after a successful commit, CI fails on a pre-commit check the second push around,
  or a custom shell-script hook calls a formatter without an explicit `git add` at
  the end.'
category: tooling
date: 2026-05-11
version: 1.0.0
user-invocable: false
---
## Overview

| Field | Value |
| ------- | ------- |
| **Goal** | Avoid silently dropping pre-commit formatter output so commits include the formatted content, not the pre-format content |
| **Context** | A pre-commit hook that mutates files (formatter, fixer, prettifier) must explicitly re-stage them via `git add`. The `pre-commit` framework does this automatically when invoked via `pre-commit run`, but custom shell-script `.git/hooks/pre-commit` drivers usually don't. |
| **Trigger** | `git status` shows unstaged whitespace/blank-line/indent diff immediately after a clean `git commit` that exited 0 with all hooks passing |
| **Output** | Either an amended commit that includes the formatter output, or a hook script that re-stages the modified files so the bug stops happening |

## When to Use

1. You ran `git add <file>` followed by `git commit`, the commit succeeded, and `git status` immediately shows a fresh unstaged diff in the file(s) you just committed
2. The unstaged diff is pure formatting — blank lines around imports, trailing-whitespace stripping, indent normalization, quote-style changes — i.e. the kind of change a formatter would make
3. CI fails on a pre-commit check after a green local commit, and the failure points at formatting changes in the file you just pushed
4. You maintain a custom shell-script hook (e.g. `scripts/mojo-format-compat.sh`, `scripts/format-and-lint.sh`) that calls a formatter on `$@` but does not end with a re-stage loop
5. A teammate reports "I committed and pushed but CI keeps complaining about formatting on the same file"

**Do NOT use when:**

- The unstaged diff after commit is in a file you didn't touch (different root cause — likely an editor saving on focus loss or another tool watching the tree)
- The pre-commit framework's `pre-commit run` was used and it shows `files were modified by this hook` and exits non-zero (that's working-as-designed — re-run will pick it up)
- The diff includes real semantic changes, not just whitespace (then the formatter rewrote logic — different bug)

## Verified Workflow

### Quick Reference

```bash
# Diagnose: after a successful commit, check immediately
git status

# If unstaged changes appear in files you just committed:
git diff                              # confirm it's only formatting

# Fix path A — not yet pushed (preferred):
git add <files>
git commit --amend --no-edit

# Fix path B — already pushed, auto-merge enabled:
git add <files>
git commit -m "fix(format): apply pre-commit formatter output"
git push

# Prevent recurrence: patch the offending hook to re-stage (see below)
```

### Diagnosing the loop

1. Reproduce: `git add <file>` then `git commit -m "test"` on a file the formatter touches
2. Immediately run `git status` — if the file shows as modified again, you have the bug
3. Run `git diff` — confirm the diff is purely the formatter's idiom (e.g. blank line between import blocks for `mojo format`, quote normalization for `black`)
4. Inspect which hook caused it. Pre-commit framework hooks log `<hook id>........Passed` even when they mutate files silently. Look for hooks whose `entry:` invokes a formatter without an explicit re-stage step.

### Patching a custom shell-script hook

The minimal fix at the bottom of the hook script:

```bash
# Inside the hook script, after running the formatter on the file list:
for f in "$@"; do
  if ! git diff --quiet -- "$f"; then
    git add "$f"
  fi
done
```

This catches every file the formatter modified and re-stages it before the hook exits. The hook still exits 0, the commit proceeds, and the index now contains the formatted content.

### Using the pre-commit framework correctly

When using `pre-commit` (the framework, not the git lifecycle event), it auto-restages files modified by hooks during `pre-commit run --hook-stage commit` — which is what `.git/hooks/pre-commit` (installed via `pre-commit install`) invokes. The auto-restage path:

```yaml
- id: mojo-format
  entry: scripts/mojo-format-compat.sh
  language: script
  files: '\.mojo$'
  stages: [pre-commit]
  # pre-commit framework re-stages modified files automatically
  # ONLY when invoked via `pre-commit run` (which the installed
  # .git/hooks/pre-commit does). If a custom .git/hooks/pre-commit
  # bypasses the framework, you lose the auto-restage.
```

If your repo has a hand-rolled `.git/hooks/pre-commit` that calls formatters outside the framework, either (a) replace it with `pre-commit install` so the framework runs, or (b) add the re-stage loop above to the hand-rolled script.

### CI-side surfacing

To prevent silent drops from reaching `main`, run pre-commit in CI with the diff visible:

```yaml
- name: pre-commit
  run: pixi run pre-commit run --all-files --show-diff-on-failure
```

`--show-diff-on-failure` makes the formatter's output appear as a failing diff in the CI log instead of being silently overwritten by the next push.

### Verification

After patching the hook, verify the loop is broken:

```bash
# Intentionally stage an unformatted file
echo "import a;import b" >> tests/foo.mojo  # or any formatter-triggering change
git add tests/foo.mojo
git commit -m "test: verify re-stage"

# Expected: commit succeeds AND git status is clean
git status                       # should report "nothing to commit, working tree clean"
git show --stat HEAD             # the formatted content is in the commit
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust `git commit` exit status | Assumed exit 0 means the formatter's output was committed | Exit 0 only means the hook succeeded; the formatter writes to the working tree, not the index, and the hook exits before any re-stage happens | A clean exit from a formatting hook says nothing about whether the formatted content reached the commit |
| Expect the formatter to fail the commit | Assumed `mojo format` / `black` / `prettier` would exit non-zero when they rewrote a file | These formatters write changes silently and exit 0 by design — they're "fixers," not "checkers" | Distinguish fixer hooks (mutate-and-exit-0) from checker hooks (read-and-exit-nonzero); only checkers fail the commit on issues |
| `git stash --keep-index` + re-apply | Stashed unstaged tree, ran formatter, popped the stash | Overcomplicated — the formatter still writes to the working tree, the stash doesn't capture its output, and the stash bookkeeping is easy to forget on hook errors | Don't reach for `stash` to solve a re-stage problem; `git add` after the formatter is the right primitive |
| Add `pass_filenames: false` to silence the hook | Tried to make the hook scope smaller so it touched fewer files | The hook still mutated whatever it did touch; just moved the bug | Scope reduction doesn't fix a re-stage gap; only an explicit `git add` does |

## Results & Parameters

### Symptom-to-fix lookup

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| `git status` shows unstaged whitespace diff right after commit | Custom hook formatter without re-stage | Patch hook with `git add` loop |
| CI pre-commit check fails on a file you just committed | Local hook mutated file, didn't re-stage; CI re-runs formatter and sees a diff | Amend commit with re-staged files, push |
| `pre-commit run --all-files` keeps reporting "files were modified" forever | Hook is non-idempotent OR you're running outside `pre-commit run` | Run inside framework; check hook idempotency |
| Only some files re-stage, others don't | Hook uses positional `$1` instead of `"$@"` | Loop over `"$@"` in the re-stage block |

### Minimal hook script template (Mojo example)

```bash
#!/usr/bin/env bash
# scripts/mojo-format-compat.sh
set -euo pipefail

# Skip on GLIBC-incompatible hosts (warn, don't fail commit)
if ! pixi run mojo --version >/dev/null 2>&1; then
  echo "[mojo-format] mojo unavailable on this host; skipping" >&2
  exit 0
fi

# Format every file passed by pre-commit
for f in "$@"; do
  pixi run mojo format "$f"
done

# CRITICAL: re-stage anything the formatter modified
for f in "$@"; do
  if ! git diff --quiet -- "$f"; then
    git add "$f"
  fi
done

exit 0
```

### Verification of the fix (ProjectOdyssey, 2026-05-11)

- Before patch: `git add tests/shared/test_imports.mojo && git commit -m "..."` → commit succeeded, `git status` showed 1-line unstaged diff (blank line between import blocks added by `mojo format`)
- After patch (hypothetical, since we hot-fixed by amending): same workflow → commit succeeds AND `git status` reports clean tree; the blank line is in the commit
- CI on the amended commit passes `pre-commit run --all-files --show-diff-on-failure` without further changes

### Verification status

- **verified-local** (observed and resolved during ProjectOdyssey PR #5388 commit on 2026-05-11)
- Not yet verified-CI for the prevention patch (i.e. modified `mojo-format-compat.sh` with re-stage loop has not been merged to ProjectOdyssey at time of writing)

### Cross-reference

- `mojo-format-non-blocking` — covers the GLIBC-skip path of the same hook
- `fix-precommit-pass-filenames` — different bug in the same hook surface (file scoping, not re-staging)
- `consolidate-pre-commit-excludes` — related cleanup of the same config file
