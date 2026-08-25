---
name: learn
license: BSD-3-Clause
description: After experiments or debugging, use this skill to save reusable knowledge. When a team needs verified knowledge, use this skill.
user-invocable: false
---

# /learn

Save reusable session knowledge in the canonical skill. When no canonical
skill exists, create one.
Write all new or changed active technical prose according to the
[Mnemosyne ASD-STE100 writing policy](../../../../../docs/asd-ste100.md).
Apply the policy to all generated skill prose. Preserve exact technical
evidence and protected content.

Follow the complete `/learn` workflow in the root `AGENTS.md`. That workflow is
the authoritative source.

## Overview

| Item | Details |
| ------ | --------- |
| Date | 2025-12-29 |
| Objective | Store session knowledge in searchable flat skill files |
| Outcome | ✅ Operational |

## When to Use

- Complete an experiment, whether it succeeds or fails.
- Debug a difficult issue.
- Implement a new pattern.
- Preserve knowledge for the team.
- Respond to an automatic prompt from a configured hook.

## Required Workflow

1. Search existing skills and open pull requests by intent.
2. If a canonical skill exists, amend it. Do not create a sibling skill.
3. Keep concise reusable guidance in the main skill.
4. Keep no more than three examples that cover different decisions.
5. Put session evidence and long examples in the notes file.
6. Before replacement, archive the complete prior main skill in the history file.
7. Keep only the current version value in the main skill frontmatter.
8. Keep the main skill at or below 30,000 bytes.
9. If no canonical skill exists, create a new flat skill.
10. Before you commit, validate the change.
11. Commit the change.
12. Push the branch.
13. Create the pull request from an isolated worktree.

## Common Mistakes and Fixes

| Mistake | Symptom | Fix |
| --------- | --------- | ----- |
| Missing required frontmatter | "Missing required field" | Add all required fields |
| Vague description | Reviewers cannot identify the trigger | Add specific trigger conditions |
| Failed Attempts as prose | "should contain a table" | Use pipe-delimited table format |
| Missing frontmatter delimiters | "missing YAML frontmatter" | Add `---` delimiters at the start of the skill file |
| Wrong category | "Invalid category" | Use one of 9 approved categories |
| `## Workflow` instead of `## Verified Workflow` | "Missing Verified Workflow section" | Use exact header name |
| SessionEnd hook | Hook does not display messages to users | Use UserPromptSubmit hook instead |
| Committed without validating | PR fails CI | Before commit, run `uv run python scripts/validate_plugins.py` |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Duplicate skill | Created a sibling without an intent search | Retrieval returned competing guidance | Amend the canonical skill |
| Oversized main skill | Kept transcripts and long examples in the main file | Retrieval became inefficient | Move supporting evidence to notes |
| Missing archive | Replaced a canonical skill without history | The prior evidence became unavailable | Archive the prior main skill first |
| Optional Failed Attempts section | Omitted failure evidence | Users could repeat failed work | Require the Failed Attempts section |
| Committing without validation | Skipped the local checks | Invalid content reached the pull request | Before commit, run `just check` |

## Results & Parameters

This skill describes a workflow pattern. It has no runtime parameters.

## References

- [Athena](https://github.com/HomericIntelligence/Athena) supplies the installed command.
- Read the root `AGENTS.md` file for the current `/learn` workflow.
- Read `validation-workflow` for CI validation details.
- Read `documentation-patterns` for skill author guidance.
