---
name: ci-markdownlint-all-files-repo-wide-blocks-prs
description: "CI markdownlint / pre-commit gates that run --all-files lint the WHOLE repo tree, not the PR diff, so one pre-existing malformed file anywhere fails the required check on EVERY open PR — even diff-clean ones. Use when: (1) a PR is BLOCKED by a failing markdownlint or pre-commit required check but `gh pr diff --name-only` shows its own diff is clean, (2) multiple unrelated PRs all go red on the same lint job at once, (3) a local `pre-commit run --files <your-diff>` passes but CI's all-files run still fails, (4) deciding whether to keep editing your PR or to open a separate cleanup PR to delete a stray file, (5) the failing job log cites a filename (e.g. a stray LEARNINGS/scratch .md at repo root) that you never touched."
category: ci-cd
date: 2026-06-12
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [ci-cd, markdownlint, pre-commit, all-files, repo-wide, ci-blocked, required-checks, stray-file, ci-debug, github-actions]
---

# CI markdownlint / pre-commit `--all-files` is repo-wide and blocks every PR

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-12 |
| **Objective** | Diagnose why a clean-diff PR's `markdownlint` required check is red, and unblock it (and every other queued PR) correctly. |
| **Outcome** | Successful — root cause was a stray file outside the PR diff; deleting it in a separate cleanup PR turned the gate green for all queued PRs. |
| **Verification** | verified-ci |

`markdownlint-cli2` and `pre-commit run --all-files` in ProjectHephaestus CI lint
the **entire repository tree**, not the changed files of the PR. Therefore a
single pre-existing malformed file *anywhere* in the repo makes those *required*
checks FAIL on **every open PR simultaneously** — including PRs whose own diff is
completely clean. "CI green" in such a repo is a REPO-WIDE property, not a diff
property. A passing local `pre-commit run --files <your-diff>` does NOT predict
CI, because CI's all-files invocation also lints files outside your diff.

## When to Use

- A PR is BLOCKED by a failing `markdownlint` / `pre-commit` required check, but
  `gh pr diff <N> --name-only` shows the PR diff is clean.
- Several unrelated PRs all turn red on the same lint job at the same time.
- A local `pre-commit run --files <changed-files>` passes but CI's all-files run fails.
- The failing job log cites a filename you never touched (often a stray scratch /
  LEARNINGS / agent-artifact `.md` accidentally committed to the repo root).
- You are about to re-run CI or re-edit your own change to "fix" a lint failure
  that your diff did not cause.

## Verified Workflow

When a clean-diff PR is blocked on `markdownlint` / `pre-commit`, do NOT assume
your change is at fault. Read the job log, identify the cited file, confirm it is
outside your diff, then fix it in its own cleanup PR.

### Quick Reference

```bash
# 1. Find the failed required-checks run for your branch.
gh run list --branch <branch> --json conclusion,name,databaseId,workflowName \
  --jq '.[] | select(.conclusion=="failure")'

# 2. Pull the failing job log and read WHICH files the violations cite.
gh run view <runId> --log-failed
#   or, for a specific job:
gh run view --job <jobId> --log | grep -iE 'MD0[0-9]+|error|Summary'

# 3. Confirm the cited files are OUTSIDE your PR diff.
gh pr diff <N> --name-only        # your PR's changed files
#   If the lint errors are in files NOT listed here -> pre-existing repo debt, not your PR.

# 4. Delete/fix the offending file in its OWN small cleanup PR (unblocks EVERY queued PR).
git checkout -b fix/unblock-ci-stray-file
git rm <stray-file.md>
git commit -S -m "fix: remove stray file failing repo-wide markdownlint gate"
gh pr create --title "[Fix] Unblock CI: remove stray markdownlint-failing file" \
  --body "$(printf 'Removes a stray file failing the repo-wide markdownlint gate.\n\nCloses #<n>\n')"
gh pr merge --auto --squash

# 5. After the cleanup PR lands on main, rebase your PR onto the new main.
git fetch origin && git rebase origin/main && git push --force-with-lease
```

### Detailed Steps

1. **Do not assume your change broke it.** A repo-wide lint gate fails on debt
   that lives anywhere in the tree, independent of your diff.
2. **Read the failing job log**, not just the check name. Find the failed run via
   `gh run list --branch <branch>`, then `gh run view <runId> --log-failed`. Note
   the cited filenames and rule codes (e.g. MD009 trailing-spaces, MD031
   blanks-around-fences, MD032 blanks-around-lists, MD022 blanks-around-headings).
3. **Diff-check the cited files.** Run `gh pr diff <N> --name-only`. If the cited
   files are absent from your diff, the blocker is pre-existing repo debt.
4. **Fix it in its own small cleanup PR** that deletes/repairs the offending file.
   Because the gate is repo-wide, one cleanup PR unblocks *every* queued PR at
   once — not just yours.
5. **Rebase your PR** onto the new main after the cleanup lands; the gate goes
   green.
6. **Caveat — trust the CI log, not local all-files output.** A local
   `pre-commit run --all-files` may *also* report failures (e.g. skill-catalog,
   dependency-sync) that actually PASS in CI due to environment differences.
   Diagnose from the CI job log, not from local all-files noise.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Blame the PR | Assumed the clean-diff PR (#1013) itself was broken and re-edited its `SKILL.md` | The diff touched only `docs/plugin-installation.md` + the SKILL.md; the 11 markdownlint errors were all in an unrelated stray file (`LEARNINGS_ISSUE_768.md` at repo root) | The blocker was repo debt outside the diff — editing the PR's own files can never fix it |
| Re-run CI | Re-triggered the failing `markdownlint` required-checks job hoping for a flake | The failure was deterministic: the stray file is malformed every run; re-running re-lints the whole tree and fails identically | Repo-wide lint failures are not flakes; read the log for the cited filename instead of retrying |
| Trust local all-files | Ran `pre-commit run --all-files` locally and saw skill-catalog / dependency-sync failures, started chasing them | Those checks PASS in CI due to environment differences; they were a red herring unrelated to the actual blocker | Trust the CI job log, not local all-files output, when identifying what is truly blocking |
| Fix inside the PR | Considered bundling the stray-file deletion into PR #1013 | Would still leave PRs #1019 and #1022 blocked on the same file; coupling cleanup to one feature PR delays everyone | Delete the stray file in a SEPARATE cleanup PR (#1021) — one fix unblocks every queued PR at once |

## Results & Parameters

Concrete instance (HomericIntelligence/ProjectHephaestus), verified end-to-end in CI:

| Item | Value |
|------|-------|
| Affected PR | #1013 (docs-only: rewrote `skills/github-actions-python-cicd/SKILL.md` to pixi+ruff+hatch-vcs) |
| PR #1013 diff | `docs/plugin-installation.md`, `skills/github-actions-python-cicd/SKILL.md` (clean) |
| Failing run | `Required Checks` run id 27052321992 (2026-06-06), `markdownlint` job, `Summary: 11 error(s)` |
| Stray file (root cause) | `LEARNINGS_ISSUE_768.md` — per-issue automation scratch file committed to repo ROOT, unrelated to #1013 |
| Rule codes hit | MD009 (trailing-spaces), MD031 (blanks-around-fences), MD032 (blanks-around-lists), MD022 (blanks-around-headings) |
| Other PRs blocked by same file | #1019, #1022 |
| Cleanup PR | #1021 — `[Fix] Unblock CI on main: remove stray LEARNINGS file + fix .pixi cache poisoning` (deleted the file) |
| Resolution | After #1021 landed on main and #1013 rebased, `markdownlint` went green; #1013 merged at 2026-06-12T06:36:44Z, all checks green |

Key invariant: in this repo `markdownlint-cli2` and `pre-commit run --all-files`
operate on the whole tree. A clean local `pre-commit run --files <diff>` is NOT a
predictor of CI; only the CI all-files run is authoritative.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PR #1013 / cleanup PR #1021 (issue #719) — markdownlint required gate, 11 errors on a non-diff stray file; green after the stray file was removed | verified-ci via `gh run view` + merged-green confirmation |
