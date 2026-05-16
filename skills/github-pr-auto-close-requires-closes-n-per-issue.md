---
name: github-pr-auto-close-requires-closes-n-per-issue
description: "GitHub only auto-closes issues from a PR when each issue has its own closing keyword (`Closes #N`) in the PR body or merge-commit message. Comma-list, markdown-table, and bullet-list formats fail silently — issues stay open after merge. Use when: (1) writing a bundle PR that closes many issues, (2) auditing why issues didn't close after a merged PR, (3) writing a PR-body template for sub-agents, (4) explaining why `closes #A, #B, #C` only closed #A."
category: tooling
date: 2026-05-16
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [github, pull-requests, issue-management, bundle-pr, closing-keywords]
---

# GitHub PR Auto-Close Requires `Closes #N` Per Issue

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-16 |
| **Objective** | Ensure bundle PRs that claim to close many issues actually trigger GitHub's auto-close on merge |
| **Outcome** | Use period-separated `Closes #N. Closes #M.` footer at top of PR body; never rely on comma-lists, markdown tables, or bullet lists |
| **Verification** | verified-ci |

## When to Use

- Writing a bundle PR body that lists many closing issues
- Auditing why issues remained open after a merged PR claimed to close them
- Writing a PR-body template for sub-agents / Myrmidon swarm output
- Explaining why `closes #A, #B, #C` only closed `#A`
- Reviewing a PR before merge to confirm GitHub will actually close the referenced issues

## Verified Workflow

### Quick Reference

```markdown
# Always prepend a Closes footer to bundle PR bodies:
**Closes:** Closes #97. Closes #106. Closes #114. ... Closes #N.

---

<rest of body>
```

### What GitHub Auto-Closes

GitHub scans the **PR body** and the **merge-commit message** (the squash-commit message for squash-merged PRs) for these patterns, requiring **one keyword per issue**:

- `close #N`, `closes #N`, `closed #N`
- `fix #N`, `fixes #N`, `fixed #N`
- `resolve #N`, `resolves #N`, `resolved #N`

### What GitHub Does NOT Auto-Close

1. **Comma-separated list with one keyword:** `closes #97, #152, #237, #246` — only closes `#97`.
2. **Markdown table referencing issues:** `| #N | <commit-sha> | description |` — none auto-close because no closing keyword precedes `#N`.
3. **Bullet list without keyword per item:** `- #N: description` — none auto-close.
4. **Closing keyword in branch commit messages of a squash-merged PR:** GitHub scans the PR body and the merged squash-commit message, NOT individual branch commits.

### Detailed Steps

1. **Draft your bundle PR body normally** (summary, test plan, table of changes, etc.).

2. **Prepend a `**Closes:**` footer at the top of the PR body**, with one period-separated `Closes #N.` per issue:

   ```markdown
   **Closes:** Closes #97. Closes #106. Closes #114. Closes #152. Closes #237. Closes #246. Closes #256. Closes #311. Closes #341. Closes #346.

   ---

   ## Summary
   ...
   ```

3. **Verify before merge** using GraphQL:

   ```bash
   gh api graphql -f query='
     query { repository(owner: "ORG", name: "REPO") {
       pullRequest(number: N) {
         closingIssuesReferences(first: 50) { nodes { number } }
       }
     }}'
   ```

   The `closingIssuesReferences` list must include every issue you intend to close. If any is missing, edit the PR body to add `Closes #N.` before merging.

4. **After merge, audit:** any issue that should have closed but is still open requires `gh issue close N --comment "Closed via PR #M (merged commit <sha>)"`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Comma-separated single keyword | `closes #97, #152, #237, #246` in body | Only `#97` closed — GitHub's parser binds the keyword to the first issue only | Use `Closes #97. Closes #152. Closes #237. Closes #246.` |
| Markdown table with issue column | `\| #N \| commit \| desc \|` rows | Zero auto-close (no closing keyword precedes `#N` in any table cell) | Add a `Closes #N.` line per issue at top of body in addition to the table |
| Bullet list without keyword | `- #N: description` items | Zero auto-close — `#N` references issues but lacks a closing keyword | Same — explicit `Closes #N` keyword per issue |
| Trusting branch commit messages on squash-merge | Branch commits each had `closes #N` in footer | GitHub uses PR body + merge-commit message; individual branch commits are ignored when squash-merged | Move all `Closes #N` into PR body before merge |

## Results & Parameters

**Root cause:** GitHub's auto-close parser requires each issue reference to be **immediately preceded** by a closing keyword (`close[s|d]`, `fix[es|ed]`, `resolve[s|d]`). The parser tokenizes the PR body and looks for `<keyword> #<number>` adjacency. A comma after the first issue terminates the binding; markdown table cells contain `#N` but no preceding keyword; branch commit messages are not scanned on squash-merge.

**Recommended format for bundle PRs** — prepend at the top of PR body:

```markdown
**Closes:** Closes #97. Closes #106. Closes #114. Closes #152. Closes #237. Closes #246.

---

<rest of PR body>
```

Period-separated `Closes #N. Closes #M.` is unambiguous and parses correctly because each `Closes` is adjacent to exactly one `#N`.

### Concrete impact from 2026-05-16 sweep

After 7 bundle PRs merged, audit via GraphQL `closingIssuesReferences` showed:

| PR | Issues claimed in body | Auto-closed by GitHub | Required manual close |
|---|---|---|---|
| Keystone #555 | 3 (explicit `Closes #N`) | 3 | 0 |
| Charybdis #249 | 9 | 9 | 0 |
| Odysseus #283 | 5 | 5 | 0 |
| Nestor #78 | 10 (table) | 1 | 9 |
| Mnemosyne #1717 | 6 (table) | 0 | 6 |
| Telemachy #241 | 10 (table) | 0 | 10 |
| Hermes #640 | 7 (table) | 0 | 7 |

**32 issues required manual `gh issue close` with citation comments** to actually close, despite the PRs claiming to close them via markdown-table syntax.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectAgamemnon, ProjectArgus, ProjectHermes, ProjectMnemosyne, ProjectNestor, ProjectTelemachy, ProjectProteus, ProjectCharybdis, ProjectKeystone, AchaeanFleet, Odysseus | 2026-05-16 PR sweep — 11 bundle PRs, 32 issues needed manual close after the table-syntax PRs merged | Audited via GraphQL `closingIssuesReferences` post-merge |
