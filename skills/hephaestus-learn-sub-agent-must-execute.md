---
name: hephaestus-learn-sub-agent-must-execute
description: "Dispatching /hephaestus:learn sub-agents reliably: prompts must say EXECUTE not plan, and the caller must check `gh pr list --head skill/<name>` before re-dispatching to avoid duplicate work. Use when: (1) launching parallel skill-creation agents, (2) a sub-agent returned 'Plan written to /tmp/plans/...' instead of a PR URL, (3) re-dispatching an agent for a task that may have already partially executed."
category: tooling
date: 2026-05-11
version: "1.0.0"
verification: verified-ci
user-invocable: false
tags: []
---

# Skill: /hephaestus:learn Sub-Agent Must Execute, Not Plan

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-05-11 |
| **Objective** | Dispatch `/hephaestus:learn` sub-agents so they reliably ship a PR instead of returning a plan, and avoid duplicate re-dispatch when the first run partially succeeded. |
| **Outcome** | Resolved — 5/5 skill PRs shipped in one session after applying the corrected dispatch pattern (PRs #1668-#1672 against HomericIntelligence/ProjectMnemosyne). |
| **Verification** | verified-ci — workflow used live to ship 5 sibling skill PRs through ProjectMnemosyne's CI. |

## When to Use

- Launching parallel skill-creation agents via `/hephaestus:learn`.
- A sub-agent returned `Plan written to /tmp/plans/...md` (or similar "Ready to execute on approval" summary) instead of a PR URL.
- Re-dispatching an agent for a task that may have already partially executed in a prior run.

## Verified Workflow

### Quick Reference

Corrected sub-agent dispatch template (drop this verbatim at the top of the prompt):

```text
EXECUTE the /hephaestus:learn skill-creation workflow for ProjectMnemosyne.
Do NOT return a plan. Do NOT ask for approval. If a step blocks you, fix
it and continue. Only stop if it is genuinely impossible. If the PR already
exists from a prior run, verify it and report its URL.

**End state required:** open or merged PR against
`HomericIntelligence/ProjectMnemosyne` adding `skills/<name>.md`,
`python3 scripts/validate_plugins.py` reporting valid, auto-merge enabled
(try --rebase first, fall back to --squash — rebase merging is disabled
on this repo), worktree cleaned up. Report the PR URL.

**Pre-flight you must do (read-only):**
<update shared clone; check `gh pr list --head skill/<name>` for existing PR>
<search for matching skills to amend>

**Execute:** <numbered steps with explicit bash blocks>
```

### Detailed Steps

1. **Write the dispatch prompt with three explicit directives at the top:**
   1. `EXECUTE the /hephaestus:learn skill-creation workflow ...` (verb forward, not "please run").
   2. `Do NOT return a plan. Do NOT ask for approval.`
   3. `If a step blocks you, fix it and continue. Only stop if it is genuinely impossible.`

2. **Bake a pre-flight read-only block into every dispatch.** The sub-agent must, before doing anything else:

   ```bash
   git -C "$HOME/.agent-brain/ProjectMnemosyne" fetch origin --prune
   git -C "$HOME/.agent-brain/ProjectMnemosyne" checkout main
   git -C "$HOME/.agent-brain/ProjectMnemosyne" pull --ff-only origin main
   gh pr list --repo HomericIntelligence/ProjectMnemosyne --state all \
     --head skill/<branch-name> --json number,state,url
   ```

   If the PR exists in any state, the agent reports the URL and skips to cleanup.

3. **Caller-side: always run the PR-list check before re-dispatching a stuck agent.**

   ```bash
   gh pr list --repo HomericIntelligence/ProjectMnemosyne --state all \
     --head skill/<branch-name> --json number,state,url
   ```

   A "plan-style summary" from the first run does NOT mean nothing shipped — several of the agents that returned plans in this session had already created the PR.

4. **Dispatch agents in parallel via multiple `Agent(...)` calls in a single tool-use turn.** Bound the parallelism (5 simultaneous worked here); the failures were in prompting, not concurrency.

5. **Resume prompts** (when a first dispatch returned a plan) should always include the line:

   ```text
   If the PR already exists from a prior run, verify it and report its URL.
   ```

6. **Merge command must fall back from rebase to squash** — ProjectMnemosyne has rebase merging disabled:

   ```bash
   PR_NUMBER=$(gh pr list --repo HomericIntelligence/ProjectMnemosyne \
     --head skill/<name> --json number --jq '.[0].number')
   gh pr merge "$PR_NUMBER" --auto --rebase --repo HomericIntelligence/ProjectMnemosyne 2>/dev/null \
     || gh pr merge "$PR_NUMBER" --auto --squash --repo HomericIntelligence/ProjectMnemosyne
   ```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Bare `/learn` prompt | "Execute the /learn workflow ... session learnings to capture: ..." | 3 of 5 agents wrote a plan file at `/tmp/plans/...md` and stopped at "Ready to execute on approval" | Add explicit "EXECUTE NOW. Do NOT return a plan. Do NOT ask for approval." directives at the top of the prompt. |
| Skipped pre-flight check before re-dispatch | Re-launched agent with the same prompt assuming the first run failed | Agent reported "Task already complete from a prior run" because the original dispatch DID create the PR despite returning a plan-style summary | Always run `gh pr list --head skill/<name>` before re-dispatching; the plan-style summary doesn't mean nothing shipped. |
| `gh pr merge --auto --rebase` only | Used rebase merging strategy in the merge command | ProjectMnemosyne has rebase merging disabled; command rejected with GraphQL error | Fall back to `--squash` if `--rebase` fails. Pattern: `gh pr merge --auto --rebase 2>/dev/null \|\| gh pr merge --auto --squash`. |
| Dispatched 5 agents serially | Sequential `Agent()` calls awaiting each | Wasted ~10 minutes of wall-clock per agent | Dispatch all independent agents in a single tool-use turn with multiple `Agent()` calls; they run in parallel. |

## Results & Parameters

**Working sub-agent prompt template** (substitute `<name>` and the per-skill content blocks):

```text
EXECUTE the /hephaestus:learn skill-creation workflow for ProjectMnemosyne.
Do NOT return a plan. Do NOT ask for approval. If a step blocks you, fix
it and continue. Only stop if it is genuinely impossible. If the PR already
exists from a prior run, verify it and report its URL.

**End state required:** open or merged PR against
`HomericIntelligence/ProjectMnemosyne` adding `skills/<name>.md`,
`python3 scripts/validate_plugins.py` reporting valid, auto-merge enabled
(try --rebase first, fall back to --squash — rebase merging is disabled
on this repo), worktree cleaned up. Report the PR URL.

**Pre-flight you must do (read-only):**

1. Update the shared clone and check for any prior PR with this branch name:
   ```bash
   git -C "$HOME/.agent-brain/ProjectMnemosyne" fetch origin --prune
   git -C "$HOME/.agent-brain/ProjectMnemosyne" checkout main
   git -C "$HOME/.agent-brain/ProjectMnemosyne" pull --ff-only origin main
   gh pr list --repo HomericIntelligence/ProjectMnemosyne --state all \
     --head skill/<name> --json number,state,url
   ```
   If a PR already exists in any state, report its URL and skip to cleanup.

2. Search for existing skills covering this topic; AMEND if a clear match
   exists (preserve previous version in `.history`), otherwise CREATE NEW.

**Execute:**

1. Create worktree at /tmp/mnemosyne-skill-<name>.
2. Write skills/<name>.md with the required frontmatter and sections.
3. Validate: `python3 scripts/validate_plugins.py`.
4. Commit, push, open PR, arm auto-merge (rebase || squash).
5. Clean up worktree.
6. Report the PR URL.
```

**Auto-merge fallback command:**

```bash
PR_NUMBER=$(gh pr list --repo HomericIntelligence/ProjectMnemosyne \
  --head skill/<name> --json number --jq '.[0].number')
gh pr merge "$PR_NUMBER" --auto --rebase --repo HomericIntelligence/ProjectMnemosyne 2>/dev/null \
  || gh pr merge "$PR_NUMBER" --auto --squash --repo HomericIntelligence/ProjectMnemosyne
```

## Verified On

This session dispatched 5 skill-creation sub-agents against `HomericIntelligence/ProjectMnemosyne`. After applying the corrected prompt pattern, all 5 skills shipped:

- #1668 — `bash-globstar-test-discovery-pitfall` (open, auto-merge)
- #1669 — `justfile-build-recipe-silent-noop` (merged)
- #1670 — `podman-compose-mount-clone-aware` (merged)
- #1671 — `mojo-sanitizer-build-scope-and-tcmalloc-incompat` (merged)
- #1672 — `modular-6433-vs-6413-failure-triage` (open, auto-merge)
