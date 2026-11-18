---
name: third-party-contribution-follow-target-repo-rules
description: "Use before you file an issue or open a pull request in a repository that you do not own. The target repository's rules override your local defaults for attribution, sign-off, commit style, and PR template. Also covers a minimal reproducer PR that fails by design."
category: tooling
date: 2026-11-18
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [upstream-contribution, attribution, dco, contributing-guide, reproducer-pr, draft-pr, privacy]
---

# Third-Party Contribution: Follow the Target Repository's Rules

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Report a defect and add a minimal reproducing test in a public repository that you do not own, without breaking its rules or leaking private data |
| **Outcome** | The issue and a draft PR were filed. A local default (an AI-attribution line) broke the target's rules and was removed from the PR body. One planned reproducer split did not fail and was changed before filing |
| **Verification** | verified-local — one session. The failing test ran against the default-branch tip. No maintainer review had happened at the time of writing |

## When to Use

- You must file an issue or PR in a repository outside your own organization.
- Your local policy adds attribution lines, footers, trailers, or labels to commits and PR bodies.
- You want to show a defect with the smallest possible test, and the fix is not part of the change.
- An automated agent does the work. It follows your local defaults unless you tell it otherwise.

## Verified Workflow

### Quick Reference

```bash
# 1. Read the target's rules before the first commit.
grep -n -i -E 'attribution|co-authored|signed-off|dco|generated|AI ' CONTRIBUTING.md .github/*template* 2>/dev/null
cat .pre-commit-config.yaml            # a hook can reject a commit message

# 2. Check for duplicates and confirm the defect on the default-branch tip.
gh issue list -R OWNER/REPO --state all --search "<symptom>"
gh pr list    -R OWNER/REPO --state all --search "<symptom>"

# 3. Run the reproducer on the default-branch tip. Record the failing output.
```

### Steps

1. Read the contribution guide, the issue and PR templates, and the hook configuration. Do this
   before the first commit. The rules in these files win over your local defaults.
2. Confirm the defect in the current source of the default branch. Search open and closed issues
   and PRs. Stop and report if a duplicate or a fix exists.
3. Remove local defaults that the target does not accept. An attribution trailer or a "generated
   by" line is the usual case. Check the commit message and the PR body. A hook may only check
   one of them. If a banned line is already in a PR body, edit the body and report the edit.
4. Check which identity becomes public. A DCO sign-off, a fork, and the PR author use the
   configured Git and forge identity. Use a no-reply address. Tell the owner before the push.
5. Keep private data out of every public text: internal hostnames, job or ticket IDs, internal
   paths, internal repository names, and customer details. Write "observed in a production
   deployment".
6. Write the issue with one idea per sentence. Use these sections: summary, affected code with the
   commit, cause, steps to reproduce, expected result, actual result, impact, fix direction.
7. Make the reproducer the smallest unit that reaches the defect. If the real code path cannot be
   called without a large refactor, call the library function that the path calls, and say so in
   the PR.
8. Run the reproducer on the default-branch tip. Confirm that it fails for the stated reason. A
   test that passes does not show the defect.
9. If the test fails by design, open the PR as a draft. State this in the PR body. Link the issue
   with a reference, not a closing keyword.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Local attribution default | Added the local attribution trailer and footer, as in the owner's own repositories | The target bans AI attribution. A hook rejected the commit message. The PR body kept the footer | Read the target's rules first. Check both the commit message and the PR body |
| First planned reproducer | Split the input after the first unit, as the plan said | The split fell on a clean boundary and the test passed | Run the test on the default-branch tip. Choose the split that triggers the failure |
| Hook-only check | Trusted the hook to catch every rule break | The hook covered commit messages and did not cover the PR body | A hook does not replace reading the guide |

## Results & Parameters

```text
Reproducer PR shape:
  files changed        1 (test only)
  test size            about 10-20 lines
  draft                yes, when the test fails by design
  PR body              problem, "no fix in this PR", test command, failing output, issue reference
  commit               signed off with the configured identity; no banned attribution
  issue text           no internal names, paths, IDs, or hosts
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A public Rust gateway project | Defect issue plus draft test-only PR | The attribution rule and the failing split were found during the session. The footer was removed from the PR body |
