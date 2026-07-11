---
name: tooling-stale-issue-target-migrated-file
description: "Resolve GitHub issues that name a file which no longer exists in the named repo (deleted or migrated). Use when: (1) an issue or brief references a file/module you cannot find, (2) planning work whose target may have moved between repos in a consolidation, (3) a cross-repo coordinated-update issue predates a migration."
category: tooling
date: 2026-07-10
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [git, planning, migration, cross-repo, github-issues]
---

# Resolving Stale Issue Targets After Cross-Repo File Migration

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-10 |
| **Objective** | Plan ProjectAgamemnon issue #337, which named `ProjectKeystone/src/keystone/maestro_client.py` — a file that no longer exists |
| **Outcome** | Successful: traced the deletion via git history, confirmed zero remaining callers in the named repo, and redirected the plan to the canonical successor (`clients/python/src/agamemnon_client/client.py`, class `AgamemnonClient`) |
| **Verification** | verified-local — every tracing command below was executed in the session and produced the cited evidence |

## When to Use

- A GitHub issue, brief, or plan names a file that `find`/`ls` cannot locate in the named repository
- Working in a multi-repo mesh where modules are periodically consolidated between repos (e.g. Keystone → Agamemnon orchestration migration)
- A "coordinated update" issue references a companion repo and you must decide whether that repo still needs a change
- A plan reviewer asks for the concrete target of a change and the issue's stated target is ambiguous

## Verified Workflow

### Quick Reference

```bash
# 1. Confirm the file is really gone from the named repo (exclude worktrees/build copies)
find <named-repo> -name "<file>" -not -path "*/.worktrees/*" -not -path "*/build/*"

# 2. Ask git why: history of the exact path (works for deleted files)
git -C <named-repo> log --oneline -5 -- <path/to/file>
# Look for "remove"/"migrate"/"move" commits — that commit message usually names the successor

# 3. Prove no residual callers remain in the named repo
grep -rn "<endpoint-or-symbol>" <named-repo>/src <named-repo>/scripts

# 4. Locate the canonical successor (CLAUDE.md migration notes, or grep the sibling repo)
grep -rn "<ClassName>\|<file-stem>" <successor-repo>/CLAUDE.md <successor-repo>/clients <successor-repo>/src
```

### Detailed Steps

1. **Exclude noise first.** `find` across a repo with `.worktrees/`, `.claude/worktrees/`, or `build/` directories returns dozens of stale copies of the deleted file; filter those paths out or you will conclude the file still exists.
2. **Use `git log -- <path>` on the deleted path.** Git keeps history for deleted files; the removing commit (here: `7ae7061 "chore: remove MaestroClient and its tests from Keystone"`) is the authoritative record and usually states where the code went.
3. **Grep the named repo for the symbols/endpoints the issue describes.** Zero hits proves the repo needs no companion change — record that command and its empty output as evidence in the plan.
4. **Find the canonical successor.** Check the consuming repo's CLAUDE.md/README migration notes first (they often document the consolidation explicitly), then grep for the class name or module stem.
5. **State the redirect in the plan with the evidence chain** (deleting commit hash, empty-grep command, successor file:line). Reviewers accept a target change only when the evidence is cited, and the PR body should note why the originally named repo needs no change.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Naive `find` across the named repo | `find ProjectKeystone -name maestro_client.py` | Returned 25 matches — all stale copies inside `.worktrees/` and `.claude/worktrees/` agent worktrees, none canonical | Always exclude worktree/build dirs, or check `src/` directly; agent-heavy repos accumulate stale worktree copies |
| Trusting the issue text as the change target | Planned against "ProjectKeystone maestro_client.py" as written | The file had been deleted from Keystone after the issue was filed; a plan targeting it is unimplementable and gets NOGO'd | Issues in multi-repo meshes go stale; verify the target exists before writing any plan section |

## Results & Parameters

Evidence chain produced in the session (ProjectAgamemnon issue #337):

```bash
git -C ~/ProjectKeystone log --oneline -5 -- src/keystone/maestro_client.py
# 7ae7061 chore: remove MaestroClient and its tests from Keystone

grep -rn "/v1/agents\|/v1/tasks\|/v1/teams\|/v1/chaos" ~/ProjectKeystone/src ~/ProjectKeystone/scripts
# (no output — zero residual callers)
```

Successor located via ProjectAgamemnon CLAUDE.md ("httpx — used by MaestroClient (in clients/python/src/agamemnon_client/)") → class `AgamemnonClient` at `clients/python/src/agamemnon_client/client.py:34`.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectAgamemnon | Issue #337 planning (pagination client update); redirected target from deleted Keystone file to canonical `agamemnon_client` | Session 2026-07-10 |
