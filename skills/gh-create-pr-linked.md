---
name: gh-create-pr-linked
license: BSD-3-Clause
description: "Create a GitHub pull request and link an existing tracking issue when appropriate. Use when partial delivery of the issue is accepted with explicit operator authorization — add a Closure disposition section to the body and hold it separate from the keyword you write."
category: ci-cd
date: 2026-03-19
version: "1.3.0"
user-invocable: false
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/gh-create-pr-linked.history"
history-cleanup-date: "2026-09-20"
---

# Create PR Linked to Issue

Create a pull request with automatic issue linking.

## When to Use

- After completing implementation work
- Ready to submit changes for review
- Need to link PR to GitHub issue

### Quick Reference

```bash
# Create PR linked to issue (preferred)
gh pr create --title "Title" --body "Closes #<issue-number>"

# Verify link appears
gh issue view <issue-number>  # Check Development section
```

## Workflow

1. **Verify changes committed**: `git status` shows clean
2. **Push branch**: `git push -u origin branch-name`
3. **Create PR**: `gh pr create --title "Title" --body "Closes #<number>"`
4. **Verify link**: Check issue's Development section on GitHub
5. **Monitor CI**: Watch checks with `gh pr checks`

## PR Preparation

- Link the PR to an existing issue when it tracks the requested work
- All changes committed and pushed
- Branch has upstream tracking
- Clear, descriptive title
- If no tracking issue exists, a self-contained PR description can state the problem and verification

## Closes vs Refs

A closing keyword (`Closes`, `Fixes`, `Resolves`) closes the issue on merge and claims a fix.
Choose the keyword from what the change proves, not from habit.

| Change | Body keyword | After merge |
| -------- | -------------- | ------------- |
| Fixes the cause of the issue | `Closes #N` | The issue closes itself. |
| Adds only diagnostics or evidence; the cause is not proven (for example an intermittent failure whose log lacks timestamps or the failing stage) | `Refs #N` | Comment what evidence now exists and what to watch for. Move the issue to the next milestone. Do not close it. A later failure then names the stage, and the real fix gets its own PR. |
| Fixes only some items listed in the issue and no operator authorization is on the table yet | `Refs #N` | Create or reuse a follow-up issue for the uncovered items, and name its number in the PR body, before the PR merges. Do not write `Closes #N` — the merge would close an issue with its work open. |
| Fixes only some items listed in the issue and the operator/owner has explicitly authorized closing it with the delivered subset | `Closes #N` | Write a `## Closure disposition (operator decision, YYYY-MM-DD)` section in the PR body that enumerates delivered and undelivered items; that is the merge's authority, not the keyword on its own. Anyone reading the closed issue later must see the authorization recorded. |
| Last open child of a tracker or release epic | `Closes #N` on the child | Close the tracker only when its last open child is closed. |

Failure mode: a diagnostics-only PR that said `Closes` was flagged as a major finding, because
the issue would close with the cause unknown.

## Closure disposition (operator decision)

Some repositories gate every PR body with a regex such as `^Closes #N$` and reject
any merge without it. When this gate is red but the issue is not actually done,
the gate does not tell you the work is done. It tells you the body is rejected
as written, and `Refs #N` fails the same gate.

When the operator/owner authorizes closing an under-delivered issue:

1. Stop before writing the `Closes` line.
2. Record the authority: who authorized it, on what date, and which items of
   the issue remain undelivered.
3. Put that in a `## Closure disposition (operator decision, YYYY-MM-DD)`
   section in the PR body, itemized, with an explicit `undelivered:` line
   naming where those items are tracked (a new issue, an existing issue,
   or "untracked by operator decision").
4. Write the `Closes #N` line only after the section is written.

Failure modes to avoid:

- Writing `Closes #N` without the disposition section and without authorization —
  the issue will close with undelivered work, with no record of who accepted it.
- Writing `Refs #N` to dodge the gate and then expecting the merge — the gate
  will reject it.
- Inventing the authority: the PR body names only an operator/owner who said
  "merge it as closed". If no such authorization exists, deliver the remaining
  items first, or split the PR.

Verify your body satisfies the forge before merge:

```bash
gh pr view <pr> --json body --jq '.body' | grep -E '^Closes #'
gh pr view <pr> --json mergeStateStatus,reviewDecision
```

## Error Handling

| Problem | Solution |
| --------- | ---------- |
| No upstream branch | `git push -u origin branch-name` |
| Issue not found | Verify issue number exists |
| Auth failure | Run `gh auth status` |
| Link not appearing | Add "Closes #ISSUE-NUMBER" to body |

## Branch Naming Convention

Example format when the repository uses issue-based branches: `<issue-number>-<description>`

Examples:

- `42-add-bracket-parser`
- `73-fix-graph-layout`

## References

- See CLAUDE.md for complete git workflow

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | YYYY-MM-DD |
| **Objective** | Skill objective |
| **Outcome** | Success/Operational |

## Verified Workflow

Steps that worked:
1. Step 1
2. Step 2

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Direct approach worked when the repo had no body gate | PR merged with `Closes` for a partially-delivered issue without an explicit authorization note | The issue tracker closed with undelivered acceptance items and no record of who accepted partial delivery | Treat the keyword as a claim the merge enforces only when the operator's disposition is recorded in the body |

## Results & Parameters

Copy-paste ready configurations and expected outputs.
