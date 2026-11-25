---
name: ci-secrets-scan-fixture-history-squash
license: BSD-3-Clause
description: "Clear a required secrets scan that flags a secret-shaped test fixture in a pull request, and keep a history rewrite from dropping the fix. Use when a history-wide scanner such as Gitleaks fails on a literal in a test file, when the fix commit still fails because the flagged commit stays in history, or when an amend or soft-reset squash may leave the fix out of the pushed commit."
category: ci-cd
date: 2026-11-25
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - secrets-scan
  - gitleaks
  - test-fixtures
  - history-rewrite
  - force-with-lease
  - git-amend
---

# Secrets Scan Flags a Test Fixture: Clear It and Verify the Pushed Commit

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-25 |
| **Objective** | Make a required secrets scan pass when a test fixture looks like a credential, without weakening the scan, and prove that the pushed commit holds the fix. |
| **Outcome** | Operational. After the fixture moved to run-time construction and the branch history was rewritten, the scan and all other required checks passed. |

## When to Use

- A required job runs a secrets scanner over the full history (for example `gitleaks detect` after a full-depth checkout) and fails on a literal in a test file.
- The new code redacts, detects, or handles secrets, so its tests need credential-shaped input.
- You pushed a fix commit and the same job still fails. The log names the older commit, not the fix.
- You rewrote a branch with an amend or a soft-reset squash, and a reviewer or a diff shows the fix is not in the pushed commit.

## Verified Workflow

### Quick Reference

```bash
# 1. Read the scanner log. Note the rule, the file, the line, and the commit it names.
gh run view <run-id> --log-failed | grep -E "RuleID|File:|Line:|Commit:"

# 2. Build the value at run time so no secret-shaped literal sits in the source.
#    FIXTURE_SECRET = "abcdefgh" + "12345678"

# 3. Rewrite the branch so that no commit holds the literal, then check the pushed tree.
git add <fixed-files> && git commit --amend --no-edit     # or squash the branch
git show HEAD:<test-file> | grep -c "<old-literal>"        # expect 0
git log -p origin/main..HEAD | grep -c "<old-literal>"     # expect 0
git push --force-with-lease=<branch>:<old-head> origin <branch>
```

### Suggested Approach

1. Read which commit the scanner reports. A history-wide scan reads every commit of the branch. A new commit that removes the literal does not clear a finding in an earlier commit.
2. Prefer run-time construction of the fixture (string concatenation or a generated value). It keeps the scan strict and needs no allowlist entry. Use an allowlist only when the owner of the scan policy approves it. Do not weaken the rule for the whole repository to pass one fixture.
3. Rewrite your own unmerged branch so that no commit contains the literal. Squash the commits, or fix each flagged commit. Update the remote with a lease pinned to the old head. Never use a plain force push.
4. Stage the fix before you commit. After `git reset --soft <base>` or `git commit --amend`, unstaged edits stay in the working tree and do not enter the commit. `git status` should be clean, and `git show HEAD:<file>` should show the fix.
5. Check the pushed head, not the working tree. Confirm the remote head equals the local head, then search the whole branch diff for the old literal.
6. A rewrite changes the head. Arm auto-merge again on the new head, and tell reviewers that the change is a content change. Re-run review when the rewrite changed code, not only fixtures.
7. Wait for the scan on the new head. Read its log if it fails again; a second finding is a different literal.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Fix-forward commit | Added a commit that removed the literal. | The scanner reads every commit, and the flagged commit stayed in history. | Rewrite the unmerged branch so that no commit holds the literal. |
| Squash without staging | Ran a soft reset, made one commit, and force-pushed. The edit was still unstaged. | The pushed commit kept the old literal. A reviewer found it from the empty diff against the previous head. | Stage the fix, then check `git show HEAD:<file>` before the push. |
| Trust a clean working tree | Checked the local file and not the pushed commit. | The local file was correct, but the commit was not. | Check the committed content and the branch-wide diff. |

## Results & Parameters

### Configuration

- Scanner: history-wide scan with a full-depth checkout (`fetch-depth: 0`).
- Push form: `git push --force-with-lease=<branch>:<old-head> origin <branch>`.
- Fixture form: concatenate the secret-shaped pieces in the test module, with a comment that says why.

### Expected Output

- The scan job passes on the new head.
- `git log -p <base>..HEAD` has no match for the old literal.
- The remote head equals the local head, and the auto-merge request names the new head.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A skill-and-script repository with a required history-wide secrets scan | A new helper whose tests used credential-shaped input | The first scan failed on a test literal. The second push still held the literal because the fix was unstaged. The third push passed every required check. |

## References

- [Secrets scan planning](ci-gitleaks-pixi-managed-secrets-scan-planning.md)
- [Stage only your own files](tooling-stage-only-your-own-files-in-shared-worktree.md)
