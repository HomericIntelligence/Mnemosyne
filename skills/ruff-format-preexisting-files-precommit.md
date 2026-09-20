---
name: ruff-format-preexisting-files-precommit
license: BSD-3-Clause
description: "Handle formatter edits to pre-existing files after pre-commit; inspect unstaged changes and preserve unrelated work when selecting commit scope."
category: tooling
date: 2026-06-20
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [pre-commit, ruff-format, staging, git-add, amend, style-drift, preexisting-files]
---

# Ruff-Format Reformats Pre-existing Files — Stage and Commit Them

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-20 |
| **Objective** | Avoid a CI pre-commit failure caused by unstaged ruff-format changes to pre-existing files after a feature branch implementation |
| **Outcome** | Successful — staging the reformatted files and amending the feature commit produces a clean `pre-commit run --all-files` on the second run and passes CI |
| **Verification** | verified-local — confirmed on ProjectTelemachy PR #285 (issue #283); 73/73 tests pass after including the ruff-format changes |

## When to Use

- You implemented a feature by adding new files (e.g. `src/telemachy/mcp_server.py`, `tests/test_mcp_server.py`) and then ran `pre-commit run --all-files` to verify everything is clean before committing.
- The `ruff-format` hook reports `Failed` and lists reformatted files that you **did not author or touch** during the feature — e.g. `tests/test_cli.py`, `tests/test_release_workflow.py`.
- Running `pre-commit run --all-files` a second time immediately reports `Passed` (the hook already applied its changes to the working tree), but `git diff --name-only` shows those files as modified and unstaged.
- This is NOT the same as `ci-precommit-whole-dir-format-drift-blocks-unrelated-commits`, where `origin/main` itself has drift and blocks every commit — here, main is clean and the drift is accumulated minor style inconsistency in pre-existing files (trailing whitespace, quote style, etc.) that ruff has newly flagged.
- This is NOT the same as `ci-ruff-format-collapses-handwrapped-comprehensions`, where YOUR OWN edit changed a comprehension's rendered length.
- Inspect formatter changes and choose an appropriate delivery scope: include necessary formatting in the current change or isolate independent drift. Preserve unrelated user edits and applicable hooks.

## Verified Workflow

### Quick Reference

```bash
# 1. If an authorized repository-wide check selected all files:
pre-commit run --all-files

# If ruff-format reports "Failed" and lists files you did not author:
# 2. Check what was modified in the working tree:
git diff --name-only

# 3. Inspect the diff and stage only reviewed formatter changes in scope:
git diff -- tests/test_cli.py tests/test_release_workflow.py
git add -- tests/test_cli.py tests/test_release_workflow.py

# 4. Fold into the feature commit (if not yet pushed):
git commit --amend --no-edit
# OR create a dedicated style commit if the feature commit is already pushed:
git commit -m "style: apply ruff-format to pre-existing files"

# 5. Verify clean:
pre-commit run --all-files  # should show all Passed now
```

### Detailed Steps

1. **Recognize the signature.** After running `pre-commit run --all-files`, the hook output shows:
   ```
   Ruff Format Python......................................................Failed
   - hook id: ruff-format
   - files were modified by this hook
   tests/test_cli.py reformatted
   tests/test_release_workflow.py reformatted
   ```
   The listed files are NOT files you worked on during the feature.

2. **Understand what happened.** `pre-commit run --all-files` scans the **entire repository**, not just staged files. The `ruff-format` hook applied its changes directly to the working tree. Running it a second time shows `Passed` — the changes are already in place on disk. The problem is they are **unstaged**.

3. **Check what is modified.** Run `git diff --name-only` to see the full list of files ruff touched. Do not rely on memory — ruff may have touched more files than the hook output listed. Compare against `git diff --cached --name-only` (staged files) to identify the gap.

4. **Stage reviewed changes explicitly.** Compare the diff with the pre-format state and stage only the intended formatter edits. Broad staging can include unrelated tracked or untracked work.

5. **Amend or create a style commit.** If the feature commit has not been pushed:
   ```bash
   git commit --amend --no-edit
   ```
   If the feature commit is already pushed and you do not want to force-push, create a separate commit:
   ```bash
   git commit -m "style: apply ruff-format to pre-existing files"
   ```

6. **Re-run to confirm clean.** `pre-commit run --all-files` should now report all `Passed`. This is the state CI will see.

7. **Verify proportionately.** Inspect the formatter diff for semantic changes. Use relevant tests when the diff or formatter behavior leaves uncertainty.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Only stage authored files and commit | `git add src/telemachy/mcp_server.py tests/test_mcp_server.py && git commit` | Pre-commit (or CI) will re-run `ruff-format --check` on all files; the unstaged reformats are still in the working tree as unclean changes and will fail the next check | Inspect formatter changes after the run and stage only reviewed changes within the chosen scope |
| Run `pre-commit run --all-files` a second time and assume clean | Saw `Passed` on the second run and concluded nothing needed to be done | The second run passes because ruff already reformatted the files in-place, but those changes are **unstaged** and invisible to the commit; CI will reformat them again and fail | A second-run `Passed` does not mean the changes are staged — check `git diff --name-only` |
| Skip or bypass pre-commit | Considered `git commit --no-verify` to avoid the hook | Bypassing hooks hides the problem from CI; the CI pre-commit job will fail with the same reformats | Stage the reformatted files; never use `--no-verify` unless explicitly authorised |

## Results & Parameters

**Context:** ProjectTelemachy, PR #285 (issue #283), branch `283-auto-impl`. The feature added `src/telemachy/mcp_server.py` and `tests/test_mcp_server.py`. After implementation, `pre-commit run --all-files` triggered `ruff-format` to reformat two pre-existing test files:

- `tests/test_cli.py`
- `tests/test_release_workflow.py`

Neither file was authored or touched during the feature. The reformats were minor style drift (trailing whitespace, quote style normalization) accumulated since those files were last committed.

**The fix:**

```bash
git add tests/test_cli.py tests/test_release_workflow.py
git commit --amend --no-edit
pre-commit run --all-files  # all Passed
```

**Outcome:** 73/73 tests pass. Pre-commit reports clean. CI passes.

**Distinction from related skills:**

- `ci-precommit-whole-dir-format-drift-blocks-unrelated-commits` — `origin/main` ITSELF has committed drift; a separate `chore(lint)` PR can isolate independent drift; include minimal formatting in the current change when necessary. Here, main is clean and the drift is only in the local working tree after ruff runs.
- `ci-ruff-format-collapses-handwrapped-comprehensions` — YOUR OWN edit (clause deletion) caused a comprehension to shorten, triggering ruff to collapse it. Here, you did not touch the reformatted files at all.
- `pre-commit-hooks-and-linting-config` — Comprehensive reference for hook configuration; section "PRE-COMMIT FORMATTER RE-STAGE" covers the same action at a glance but without the diagnostic steps or failure modes documented here.

**Verified On:**

| Project | Scenario | Result |
| ------- | -------- | ------- |
| ProjectTelemachy | PR #285 issue #283 — feature added 2 new files; ruff reformatted 2 pre-existing test files | Staged + amended; 73/73 tests pass; pre-commit clean |
