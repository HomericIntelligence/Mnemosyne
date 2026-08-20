---
name: pre-commit-hooks-and-linting-config
description: "Use when adding, configuring, debugging, or enforcing pre-commit and lint hooks; reconciling local/CI tool versions and environments; diagnosing formatter, staged-file, hook-stage, file-scope, or pass_filenames false greens; or deciding whether a lint finding may be suppressed."
category: tooling
date: 2026-07-13
version: "3.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-precommit
history: pre-commit-hooks-and-linting-config.history
tags: [pre-commit, linting, ruff, mypy, bandit, markdownlint, ci, pixi, hooks, formatting]
---

# Pre-commit Hooks and Linting Configuration

## Overview

Use pre-commit as the local entry point for the same deterministic checks that CI
requires. A green substitute command is not evidence that the actual hook, stage,
environment, file scope, or required CI step passed.

The corpus is `verified-ci` overall; newer checker and commit-abort patterns are
`verified-precommit`. Per-case status is retained in [the notes](./pre-commit-hooks-and-linting-config.notes.md).
Full superseded versions are in [history](./pre-commit-hooks-and-linting-config.history).

## When to Use

- Adding or changing `.pre-commit-config.yaml`, a linter, hook revision, `files:`,
  `exclude:`, `stages:`, `pass_filenames:`, or repository lint configuration.
- CI fails although a related local command passed, especially formatter versus
  linter, skipped-hook, environment, or full-diff scope mismatches.
- TOML is malformed, Ruff differs from a lockfile, Bandit scans the wrong target,
  mypy sees an untracked file, or a local executable shadows the project version.
- A formatter changes files in CI, a commit appears not to advance `HEAD`, or a
  `commit-msg` hook is configured but never runs.
- Removing a duplicate CI lint job or changing an exclusion that may be
  load-bearing.
- A lint suppression, `--exit-zero`, or `continue-on-error` is proposed.

## Core Rules

1. Make `.pre-commit-config.yaml` the lint entry point and invoke it from CI.
2. Pin hook revisions exactly and keep them aligned with lockfiles/tool versions.
3. Run the actual hook and stage; `ruff check` does not run `ruff format`, and
   `pre-commit run --all-files` does not run `commit-msg` hooks.
4. Before push, cover the entire PR diff or all files—not only files from the last
   edit or sub-agent.
5. Formatter mutation means failure until the changes are staged and the exact
   command passes without a diff.
6. Suppress only a documented false positive with the narrowest scope. Never hide
   a required gate with `--exit-zero`, `continue-on-error`, or a permanent skip.
7. Match hook invocation to tool ownership: directory-scanning tools usually need
   `pass_filenames: false`; per-file tools should accept filenames.

## Verified Workflow

### 1. Reproduce the exact gate

Read the workflow, hook entry, repository task, and lockfile before changing code.
Capture the hook ID, stage, environment, file selector, tool version, and CI
command. Then run the same command locally:

```bash
pre-commit run <hook-id> --all-files --show-diff-on-failure
pre-commit run --from-ref origin/main --to-ref HEAD --show-diff-on-failure
pre-commit run --all-files --show-diff-on-failure
```

If CI uses Pixi or another environment, preserve it exactly:

```bash
pixi run --environment lint pre-commit run --all-files --show-diff-on-failure
```

Do not inherit `SKIP=` from an advisory job when a separate required job runs the
same hook without it. Reproduce the required job's no-skip command.

### 2. Separate lint, format, parse, and type checks

```bash
pixi run ruff check --fix .
pixi run ruff format .
pixi run --environment lint ruff format --check .
pre-commit run check-toml --all-files
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"
pixi run mypy <path> --explicit-package-bases --python-version 3.10
```

Ruff's checker and formatter share a binary but enforce different contracts.
`per-file-ignores` is lint-only; use the tool's `exclude` setting for generated
files that format must also ignore. TOML parsing catches duplicate tables that a
linter may never reach.

For `uv.lock`, read the locked Ruff version and require
`astral-sh/ruff-pre-commit` at exactly `rev: v<locked-version>`. Run any repository
parity checker after updating either side.

### 3. Configure hook stages explicitly

```yaml
default_install_hook_types: [pre-commit, commit-msg]
```

Install and exercise each stage:

```bash
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit run --hook-stage commit-msg --commit-msg-filename <message-file>
```

`--all-files` skips `commit-msg`; its input is a message file, not repository
paths. Test both a valid and invalid message.

### 4. Choose filename behavior from the tool contract

Directory-scanning tools that own their targets must not receive pre-commit's
changed filenames:

```yaml
- id: bandit
  entry: pixi run bandit -r src --ini .bandit --severity-level medium
  language: system
  pass_filenames: false
  files: ^(src|tests)/.*\.py$
```

The `files:` expression still decides when the hook triggers. `pass_filenames:
false` prevents appended filenames from overriding `.bandit` targets/recursion.
Use the same pattern for a repo-local `pixi.toml` policy checker that locates the
root itself:

```yaml
- id: check-pixi-policy
  entry: python scripts/check_pixi_policy.py
  language: system
  files: ^pixi\.toml$
  pass_filenames: false
```

For a pip-audit task checker, anchor task values to begin with `pip-audit` so a
dependency pin such as `pip-audit = ">=2.7,<3"` is not parsed as a command. Scan
only non-comment lines for `--ignore-vuln`; examples in ledger comments are not
active suppressions. Do not claim a policy is enforced before hook wiring exists.

### 5. Diagnose environment and working-tree traps

- If a Pixi task cannot find an entry point or behaves differently, compare
  `command -v <tool>`, `pixi run command -v <tool>`, and versions. Refresh the
  editable install with the repository's development-install task.
- Pre-commit may inspect untracked files. In a multi-commit workflow, move an
  intentionally later test outside the worktree, commit the implementation, then
  restore it; never weaken mypy to ignore the mismatch.
- Stage generated lockfiles before commit if pre-commit's temporary stash would
  conflict with them.
- After scripted, generated, or delegated edits, run from merge base to `HEAD` or
  all files. A literal `--files` list is only an iterative development check.

### 6. Treat commit failure before signature failure

If `git commit -S` returns nonzero, first prove a new commit exists:

```bash
git log -1 --format='%H %G? %s'
git diff --cached --name-only
git reflog -3
```

If `HEAD` did not move and files remain staged, a hook aborted the commit;
signature output describes the parent commit and may show an unrelated key. Fix
the hook, re-stage formatter changes, and commit again. Do not restart signing
agents or amend the parent before establishing that a commit was created.

### 7. Change CI or exclusions safely

Before removing a duplicate standalone lint job:

1. Confirm its exact job name is not a required branch-protection/ruleset context.
2. Confirm the replacement pre-commit job runs the same or stronger check.
3. Pre-scan every newly included file; auto-fixers do not fix every violation.
4. Update documentation that names the removed job.

Before removing an exclusion, enumerate matching tracked files. If tracked files
exist, the exclusion is load-bearing until those files pass or are intentionally
handled. Do not infer from directory names alone.

### 8. Tool-specific decisions

- Bandit: use AST scanning, explicit `--ini .bandit`, and a meaningful threshold
  such as `--severity-level medium`; never replace it with grep.
- golangci-lint v2: include top-level `version: "2"` and migrate keys to the v2
  schema; validate with the real v2 binary.
- markdownlint MD060: `--fix` may leave table alignment unchanged. Normalize table
  separators and cells with a reviewed transformation, then rerun markdownlint.
- Ruff `I001`: sort the complete import block; `RUF059`: replace an intentionally
  unused unpack target with `_`; `B904`: use `raise ... from err` inside an
  exception handler; `C901`: extract a cohesive helper rather than suppressing
  complexity.
- `detect-private-key`: first prove the match is a documented false positive,
  then apply the narrowest hook-level exclusion; never disable the scanner.
- mypy in hyphenated or namespace layouts: invoke per file with
  `--explicit-package-bases` when module discovery cannot represent the path.
- pygrep with exclusions: prefer a `language: system` script when the decision
  needs both matching and exclusion logic.
- Go-backed hooks: use repository-supported installation or pinned release
  artifacts; do not compile opportunistically in every hook run.
- `.editorconfig`: set `root = true`, LF, final newline, charset, and file-type
  indentation; preserve Markdown trailing spaces if the corpus uses hard breaks.

## Copy-ready Baseline

```yaml
default_install_hook_types: [pre-commit, commit-msg]

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: <exact-tag>
    hooks:
      - id: check-toml
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v<exact-locked-version>
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Before pushing:

```bash
pre-commit run --from-ref origin/main --to-ref HEAD --show-diff-on-failure
pre-commit run --all-files --show-diff-on-failure
git diff --check
```

Use the exact CI environment wrapper when one exists. Success means exit code 0
and no uncommitted formatter changes.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Checker as formatter evidence | Ran `ruff check` only | It never executes `ruff format` | Run both checker and formatter check |
| All-files as message evidence | Used `pre-commit run --all-files` for `commit-msg` | Message hooks use a different stage and input | Invoke `--hook-stage commit-msg` with a message file |
| Filename injection | Kept `pass_filenames: true` for a directory scanner | Appended paths override configured targets | Set false while retaining a trigger `files:` regex |
| Skipped-hook green | Trusted local `SKIP=<hook>` | A required CI step may enforce the hook | Reproduce the exact no-skip required command |
| Per-edit push check | Checked only the latest file list | Misses earlier/delegated changes and whole-tree checks | Run from merge base or all files |
| Premature GPG debugging | Investigated signing before checking `HEAD` | An aborted commit leaves only the parent's signature | Verify `HEAD`, index, and reflog first |
| Broad suppression | Added a wide ignore or success override | Hides actionable defects and weakens the gate | Fix or narrowly document a proven false positive |
| Premature CI deletion | Removed a job before ruleset review | Leaves an impossible required context | Audit required contexts first |
| Auto-fix trust | Assumed formatter mutation completed the repair | Some rules, including table layout, remain | Inspect the diff and rerun the exact hook |

## Results & Parameters

The result is a reproducible local gate whose command, environment, stage, and
file scope match required CI. The principles and most patterns are `verified-ci`.
The Pixi policy-checker,
Bandit filename, and commit-abort diagnoses were verified locally or through
pre-commit as identified in the notes; do not upgrade them to CI evidence without
a supporting run. Repository-specific commands and versions are examples, not
universal defaults.

## References

- [Detailed case index and evidence](./pre-commit-hooks-and-linting-config.notes.md)
- [Version history and full superseded content](./pre-commit-hooks-and-linting-config.history)
- [pre-commit documentation](https://pre-commit.com/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [mypy documentation](https://mypy.readthedocs.io/)
- [golangci-lint v2 migration](https://golangci-lint.run/product/migration-guide/)
