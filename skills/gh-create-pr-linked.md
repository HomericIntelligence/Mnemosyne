---
name: gh-create-pr-linked
license: BSD-3-Clause
description: "Create a GitHub pull request and link an existing tracking issue when appropriate."
category: ci-cd
date: 2026-03-19
version: "1.1.0"
user-invocable: false
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/e98a4da5d67f0766bc6b4bfaed1ab399fca90e9f/skills/gh-create-pr-linked.history"
history-cleanup-date: "2026-09-19"
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
| N/A | Direct approach worked | N/A | Solution was straightforward |

## Results & Parameters

Copy-paste ready configurations and expected outputs.
