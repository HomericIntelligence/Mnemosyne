---
name: worktree-parallel-agent-execution
description: "Use when: (1) resolving 3+ independent GitHub issues simultaneously with sub-agents, (2) mass-rebasing many PR branches in parallel without collision, (3) triaging issues by complexity then executing LOW items in a single parallel wave, (4) avoiding merge conflicts when multiple agents work on the same repo, (5) splitting ONE multi-part GitHub issue into N independent parallel sub-tasks with hot-file ownership coordination."
category: tooling
date: 2026-05-07
version: "1.1.0"
user-invocable: false
verification: verified-ci
history: worktree-parallel-agent-execution.history
tags: [parallel-agents, worktree, wave-execution, batch, rebase, issue-triage, automation, split-issue, hot-file-coordination]
---
# Worktree Parallel Agent Execution

## Overview

| Field | Value |
| ------ | ----------- |
| **Date** | 2026-05-07 |
| **Objective** | Launch N parallel sub-agents in isolated worktrees for parallel issue/PR execution AND single-issue splitting |
| **Outcome** | verified-ci (PRs #1932, #1933 merged from #1887 split); consolidates 5 prior skills |
| **Verification** | verified-ci |
| **History** | [changelog](./worktree-parallel-agent-execution.history) |

Covers launching multiple sub-agents in parallel, each in a dedicated git worktree, to achieve
3-8x speedup on independent work. Includes wave-based dependency management, batch sizing,
rebase-in-parallel patterns, issue triage by complexity, branch collision avoidance, and
**splitting a single multi-part issue into N independent sub-tasks with hot-file ownership**
(v1.1.0).

## When to Use

**Ideal for:**
- Multiple independent issues (3+) — code refactoring, test additions, config changes
- Batch work where issues touch different files/modules (no shared-state conflicts)
- Time-critical sprints (release prep, technical debt, CI unblocking)
- Issues with clear dependency chains (parallelize independent waves)
- Mass-rebasing many PR branches after a large main merge
- **One multi-part issue with 2+ independent remediation items** (use Phase 0 hot-file split)

**Not suitable for:**
- Issues requiring shared state or coordinated changes across files
- Single complex issue requiring sequential reasoning
- Issues touching the same files (high conflict risk) — UNLESS split via Phase 0 hot-file ownership
- More than 2 sub-tasks for a single issue (coordination cost dominates throughput gain)

## Verified Workflow

### Quick Reference

```bash
# Splitting a single multi-part issue into 2 parallel sub-tasks (v1.1.0):
gh issue view <N> --comments  # Survey true remaining scope
gh repo view --json squashMergeAllowed,rebaseMergeAllowed,mergeCommitAllowed  # Detect merge policy
grep -E '^\[(feature\.|environments)' pixi.toml  # Discover pixi env names
git worktree add ~/<repo>-worktrees/<issue>-a -b <issue>-a main
git worktree add ~/<repo>-worktrees/<issue>-b -b <issue>-b main
# Dispatch 2 opus sub-agents in parallel (background mode, don't poll)
# After completion, if second PR needs rebase:
cd <second-worktree> && git fetch origin && git rebase origin/main
pre-commit run --files <changed>  # MANDATORY after conflict resolution
git push --force-with-lease

# One-shot: launch N agents in parallel with worktree isolation
# (send all Task tool calls in a SINGLE message for true parallelism)

# Rebase all open PRs
gh pr list --state open --json number --jq '.[].number' | \
  while read pr; do gh pr merge "$pr" --auto --rebase; done

# Check PR states after rebase
gh pr list --state open --json number,mergeStateStatus --limit 70 | python3 -c "
import json,sys; prs=json.load(sys.stdin)
by_s={}
[by_s.setdefault(p['mergeStateStatus'],[]).append(p['number']) for p in prs]
[print(f'{s}: {len(n)}') for s,n in sorted(by_s.items())]
"
```

### Phase 0: Splitting a Single Issue with Shared Docs/Config Files (v1.1.0)

Use this phase when a single multi-part GitHub issue has 2 truly independent remediation items
that you want to land as separate PRs. Foundation: ProjectScylla #1887 split into PRs #1932
(log↔span correlation) and #1933 (span depth + OTLP docs).

**Step 0.1 — Survey the issue's TRUE remaining scope (don't trust the title):**

```bash
gh issue view <N> --comments        # check for "still out of scope" / "partial progress" comments
gh pr list --search "<keywords> in:title" --state merged --limit 10  # see what already landed
```

Foundation work (already-merged scaffold PRs) often shrinks the remaining scope by 50%+.

**Step 0.2 — Build a hot-file ownership matrix BEFORE dispatch:**

| File | Sub-task A | Sub-task B | Rule |
|------|-----------|-----------|------|
| `cli/main.py` | OWNS | — | Only A may edit |
| `pyproject.toml` | — | OWNS | Only B may edit |
| `docs/dev/<topic>.md` | APPEND-ONLY | APPEND-ONLY | Both append; neither modifies existing sections |
| `<module>/foo.py` | — | OWNS | Only B may edit |

Every file touched by both agents must either have a single owner OR be append-only. Shared
config files (`pyproject.toml`, `pixi.toml`, CI YAML) almost always need single ownership.

**Step 0.3 — Detect repo merge policy ONCE, pass to both briefs:**

```bash
gh repo view --json squashMergeAllowed,rebaseMergeAllowed,mergeCommitAllowed
```

If `rebaseMergeAllowed=false`, briefs must use `gh pr merge --auto --squash` — the default
`--rebase` (from CLAUDE.md guidance) will fail.

**Step 0.4 — Detect pixi env names from `pixi.toml` (don't assume `dev`):**

```bash
grep -E '^\[(feature\.|environments)' pixi.toml
# Brief should say "use `pixi run` (default env)" OR list discovered env names
```

**Step 0.5 — Create one worktree per sub-task off latest main:**

```bash
git worktree add ~/<repo>-worktrees/<issue>-<a-name> -b <issue>-<a-name> main
git worktree add ~/<repo>-worktrees/<issue>-<b-name> -b <issue>-<b-name> main
```

**Step 0.6 — Dispatch parallel opus agents in background mode (don't poll):**

Each agent brief MUST include:
- Worktree absolute path (DO NOT cd out of it)
- Verified file paths and line numbers (don't make agent re-discover)
- Hot-file ownership table from Step 0.2
- "Append-only to shared docs" rule
- Detected merge method from Step 0.3 (`--squash` vs `--rebase`)
- Detected pixi env from Step 0.4
- Mandatory `pre-commit run --all-files` before push
- Critical: "Do NOT modify 'still TODO' / 'out of scope' lists in shared docs — the OTHER
  agent's work may obsolete those lines and cause a stale-bullet rebase conflict"

**Step 0.7 — On completion notification, second PR may need rebase:**

```bash
cd <second-worktree>
git fetch origin && git rebase origin/main
# resolve conflicts (typically end-of-file markdown-lint blank-line issues)
pre-commit run --files <changed-files>   # CRITICAL — see Failed Attempt #14
git add <files> && git rebase --continue
git push --force-with-lease
```

**Step 0.8 — Don't auto-clean worktrees** (Safety Net blocks `--force` removal). Either let
the user clean up OR produce a script for them to run.

### Hot-file ownership rules (must be in every brief)

1. ONE owner per shared config file (`pyproject.toml`, `pixi.toml`, `cli/main.py`, CI YAML)
2. Shared docs: APPEND-ONLY — never edit existing sections; add new H2/H3 at end-of-file
3. Each agent's docs append should be small — 20-200 lines max
4. Neither agent may delete bullets from "still TODO" / "out of scope" lists — those may be
   in-scope for the other agent and cause stale-bullet rebase conflicts
5. Run `pre-commit run --files <changed>` AFTER any manual conflict resolution before push

### Why two-agents is the sweet spot for one issue

| Sub-tasks | Coordination cost | Throughput gain | Verdict |
|-----------|-------------------|-----------------|---------|
| 1 | None | 1x | No split needed |
| 2 | Low (1 hot-file matrix) | ~1.7x | **Sweet spot** |
| 3 | High (3 pairwise matrices) | ~2.0x | Marginal — usually not worth it |
| 4+ | Very high (6+ matrices) | <2.5x | File-conflict risk dominates |

### Phase 1: Plan Wave-Based Execution

Organize issues into dependency waves before launching any agents:

```
Wave 1 (No deps):     #485 + #487  → 1 PR  (quick wins — run immediately)
Wave 2 (Foundation):  #479, #478   → 2 PRs (P0 work — run immediately)
Wave 3 (After W2):    #489, #488   → 2 PRs (depends on #479/#478 merging)
Wave 4 (Independent): #481, #486   → 2 PRs (run immediately)
```

**Key insight:** Waves 1, 2, and 4 can all run concurrently. Wave 3 waits for Wave 2 to merge.

### Phase 2: Issue Triage by Complexity (for large batches)

When processing 10+ issues, classify first with 2-3 parallel Explore agents:

```bash
# Fetch all open issues
gh issue list --repo ORG/REPO --state open --limit 100 --json number,title,body,labels

# Launch 2-3 classification agents in parallel, splitting issues by number range
# Each returns: issue number, title, complexity (LOW/MEDIUM/HIGH), justification
```

**Classification heuristics:**

```yaml
LOW (< 30 min):
  - Adding entries to .gitignore
  - Creating boilerplate docs (CONTRIBUTING, CHANGELOG, SECURITY)
  - Creating GitHub templates (issue, PR)
  - Pinning action versions to SHA
  - Fixing trailing commas or typos
  - Adding .editorconfig / .pre-commit-config.yaml
  - Removing dead code references
  - Adding simple fields to existing scripts

MEDIUM (1-3 hours):
  - DRY refactoring across 3+ files
  - Adding CI pipeline steps (linting, type checking)
  - Creating JSON schemas
  - Auditing and relocating orphaned files

HIGH (3+ hours):
  - Creating pyproject.toml / pixi.toml (packaging foundation)
  - Building test infrastructure from scratch
  - Tasks with 3+ blocking dependencies
```

**Before launching:** Verify LOW issues don't touch the same files.

### Phase 3: Launch Parallel Sub-Agents with Worktree Isolation

**Critical rule:** Send ALL agent Task tool calls in a SINGLE message for true parallelism.

**Agent instruction template:**

```
Execute [Wave N / Issue #XXX]: [brief description]

CRITICAL: Use a dedicated git worktree to avoid colliding with other agents.

1. Create worktree FIRST:
   git worktree add <project-root>/worktrees/<unique-name> -b <unique-branch>
   cd <project-root>/worktrees/<unique-name>
   (OR use Agent(isolation: "worktree") for automatic management)

2. [Specific implementation steps — include exact file paths, function names, etc.]

3. Run tests: pixi run python -m pytest <test-path> -v
4. Run pre-commit: pre-commit run --all-files
5. Commit: git commit -m "type(scope): description\n\nCloses #XXX"
6. Push: git push -u origin <branch>
7. Create PR: gh pr create --title "..." --body "Closes #XXX"
8. Enable auto-merge: gh pr merge --auto --rebase
9. Report PR URL and status

Do ALL work from inside the worktree. Each agent must use a UNIQUE worktree path and branch.
```

**Required per-agent constraints:**
- Unique worktree directory (e.g., `worktrees/issue-XXX-description`)
- Unique branch name (`<issue-number>-<description>`)
- Detailed, step-by-step instructions (agents have no context of other agents)
- Explicit file paths and line counts where possible

### Phase 4: Mass Rebase with Parallel Agents

For mass-rebasing many PR branches (50-70+ PRs), use batched agents:

```bash
# Check current state
gh pr list --state open --json number,mergeStateStatus,headRefName --limit 70 | python3 -c "
import json,sys
prs = json.load(sys.stdin)
by_state = {}
for p in prs:
    by_state.setdefault(p['mergeStateStatus'],[]).append(p['number'])
for s,n in sorted(by_state.items()):
    print(f'{s}: {len(n)} - {sorted(n)[:10]}')
"

# Enable auto-merge on all PRs missing it
for pr in <list>; do gh pr merge "$pr" --auto --rebase; done
```

**Agent prompt for rebase batches:**

```
CRITICAL: Use a dedicated git worktree to avoid colliding with other agents.

Create your worktree FIRST:
  git worktree add worktrees/rebase-batch-N <stable-branch>
  cd worktrees/rebase-batch-N

Then for each PR in your batch [PR1, PR2, PR3, PR4]:
  git fetch origin <branch> -q
  git switch -c tmp-bN-<pr> origin/<branch> -q
  git rebase origin/main
  # If CONFLICT: git rebase --abort, report PR number for manual resolution
  git push --force-with-lease origin HEAD:<branch> -q
  git switch <stable-branch> -q
  git branch -d tmp-bN-<pr>

When done:
  cd <repo-root>
  git worktree remove worktrees/rebase-batch-N
```

**Optimal batching:**

```yaml
prs_per_agent: 3-4     # Sequential within agent, parallel across agents
agents: 3-4            # All launch simultaneously in one wave
total_prs: 13-70       # Scales well
```

**Temp branch naming (must be unique across agents):**

```
Batch 1 agent:  tmp-b1-<issue>   # e.g., tmp-b1-4833
Batch 2 agent:  tmp-b2-<issue>   # e.g., tmp-b2-4863
Main session:   tmp-<issue>      # e.g., tmp-4889
```

### Phase 5: Handle Branch Conflicts

```bash
# Error: fatal: 'fix-baseline-ci-errors' is already used by worktree at '...'
# Option A: Work in the worktree directly
git stash
cd worktrees/rebase-batch2  # do work here
cd /repo && git stash pop

# Option B: Create a separate worktree for your own work
git worktree add worktrees/main-work origin/my-branch
```

### Phase 6: Resolve Rebase Conflicts Programmatically

**Decision tree for common conflict types:**

| File | Resolution |
| ------ | ----------- |
| `CLAUDE.md`, config files | Take `--ours` always |
| CI workflow YAML | Take `--ours` unless branch is adding the workflow |
| Deleted file (modify/delete) | Honor the deletion with `git rm <file>` |
| Test files | Keep both sides' additions |
| Python scripts | Merge both features when both add distinct functionality |

```python
# Take ours (HEAD/main) — generic helper
def take_ours(content):
    result = []
    in_ours = in_theirs = False
    for line in content.split('\n'):
        if line.startswith('<<<<<<<'):
            in_ours = True
        elif line.startswith('=======') and in_ours:
            in_ours = False; in_theirs = True
        elif line.startswith('>>>>>>>') and in_theirs:
            in_theirs = False
        elif in_ours:
            result.append(line)
        elif not in_theirs:
            result.append(line)
    return '\n'.join(result)
```

### Phase 7: Monitor and Merge

```bash
# Monitor progress
gh pr list --state open --json number,mergeStateStatus --limit 70

# Check all PRs for conflicts BEFORE spawning agents
for pr in $(gh pr list --state open --json number --jq '.[].number'); do
  branch=$(gh pr view $pr --json headRefName --jq '.headRefName')
  git fetch origin "$branch" 2>/dev/null
  conflicts=$(git merge-tree --merge-base origin/main origin/main "origin/$branch" 2>&1 | grep -c "CONFLICT")
  echo "PR#$pr: $conflicts conflicts"
done

# Verify all issues closed after merge
gh issue list --limit 20 --json number,title,state \
  --jq '.[] | select(.number >= 478 and .number <= 489) | "\(.number): \(.state) - \(.title)"' | sort -n
```

### Alternative: Cherry-Pick Pattern

Instead of each agent creating its own PR, agents commit in worktrees and the main session cherry-picks:

```bash
# Launch agents with isolation: "worktree" — each commits in their worktree
# After all agents complete:

# Stash any uncommitted main work first
git stash push -m "main work" -- file1 file2

# Cherry-pick all worktree commits sequentially
git cherry-pick <hash1> && git cherry-pick <hash2> && git cherry-pick <hash3>

# Resolve any conflicts
# (read conflict markers, edit to resolve, git add, git cherry-pick --continue)

# Run full verification
pixi run pytest tests/ -v
pixi run ruff check <package>/
pixi run mypy <package>/
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Sequential agent execution | Launch one agent, wait, then launch next | 10 issues × 3 min = 30 min total; no parallelism benefit | Launch all independent agents in ONE message with multiple Task tool calls |
| Agents working on main branch | Multiple agents working on main or shared branches | Merge conflicts when agents push simultaneously; race conditions on git state | Each agent gets its own worktree in `worktrees/` directory |
| Parallel agents without worktree isolation | Both agents shared the same working tree | Agents left stale rebase-in-progress state (`.git/rebase-merge/`) from each other's abandoned rebases | Always assign each parallel rebase agent a dedicated `git worktree` |
| Overly generic agent instructions | "Fix issues #479, #478, #481 in parallel" | Agents waste time exploring; inconsistent approach | Provide detailed step-by-step with exact file paths, function names, expected line counts |
| 1 PR per agent for 13 PRs | Spawned 13 individual agents | Excessive agent spawn overhead; 5-agent-per-wave limit means 3 waves minimum | Batch 3-4 PRs per agent — 4 agents handle 13 PRs in 1 wave |
| Shared temp branch prefix across agents | Agent 1 and Agent 2 both used `tmp-r2-*` prefix | Agents created conflicting temp branch names | Include unique batch ID in prefix: `tmp-b1-<N>`, `tmp-b2-<N>` |
| Spawned agents while parent was in plan mode | Agents completed analysis but couldn't execute | Plan mode is inherited by sub-agents — they can only read files | Always exit plan mode BEFORE spawning execution agents |
| Content filter on governance doc | Sub-agent tried to write Contributor Covenant text | API content filtering policy blocked output (twice) | Governance/conduct documents may trigger content filters — handle in main session with shorter adapted text |
| Sub-agent retrospective | Asked completed agents to run /learn | Agents are one-shot — context is gone after returning | Sub-agents cannot run follow-up commands; capture learnings from main session instead |
| Branch already exists from failed agent retry | Retry agent tried to create same branch name | Previous failed agent had already pushed the branch | Use `-v2` suffix or delete remote branch before retrying |
| Post-completion error treated as failure | Agents showed `failed` with `classifyHandoffIfNeeded is not defined` | Error occurs AFTER agent completes successfully; it's a cleanup bug | Verify by checking `gh pr view PR_NUMBER --json state` — if MERGED, agent succeeded |
| Cherry-pick of pixi.toml changes | Agent removed `version` line; base had different version | CONFLICT because both sides modified same region | When agents modify shared config files, expect cherry-pick conflicts |
| git stash pop after cherry-picks | Stashed SECURITY.md conflicted with cherry-picked version | Both stash and cherry-pick modified same file | Use `git add` to mark conflict resolution, not `git checkout --` (blocked by safety net) |
| `pixi run -e dev` in agent brief (split-issue dispatch) | Used `dev` env name from instinct/CLAUDE.md convention | Repo had envs `default`/`lint`/`docs`, no `dev` — agent commands failed | Brief should say "use `pixi run` (default env)" OR have agent grep `pixi.toml` for env names FIRST |
| `gh pr merge --auto --rebase` (default from CLAUDE.md) | Standard merge command | Repo had rebase merging disabled — `--rebase` rejected | Detect with `gh repo view --json squashMergeAllowed,rebaseMergeAllowed` ONCE, pass to all briefs |
| Both agents append to same docs file end-of-file | Each appended new H2 section at EOF — different lines, "no conflict" | Agent A's PR removed a "still out of scope" bullet that B's work was making in-scope; B's rebase produced stale-bullet conflict | "Append-only to shared docs" is necessary but NOT sufficient — also forbid editing "still TODO"/"out of scope" lists; the other agent may obsolete those lines |
| Trusting local pre-commit pass after manual rebase conflict resolution | Resolved markdownlint conflict, force-pushed without rerunning hooks | Manual edit during conflict resolution introduced missing-blank-line; CI markdownlint failed | Always run `pre-commit run --files <changed>` AFTER manually resolving rebase conflicts, BEFORE force-push |

## Results & Parameters

### Proven Scale Metrics

| Session | Issues/PRs | Agents | Time | Speedup |
| --------- | ----------- | -------- | ------ | --------- |
| ProjectScylla PR sprint | 10 issues, 9 PRs merged | 6-8 agents | 15-20 min | 6-8x |
| ProjectScylla test/refactor | 3 issues, 4 PRs | 3 agents | 5 min | 3x |
| ProjectMnemosyne LOW issues | 12 issues, 12 PRs | 12 agents | 6 min | ~5x |
| ProjectHephaestus batch | 19 issues, 16 implemented | 10 agents | ~3 min | ~6x |
| ProjectOdyssey rebase v1.0 | 70 PRs rebased | 3 agents | 45 min | — |
| ProjectOdyssey rebase v1.1 | 13 PRs rebased | 4 agents | 7 min | — |
| ProjectScylla #1887 split | 1 issue → 2 PRs (#1932, #1933) | 2 agents | ~30 min wall | ~1.7x |

### Agent Configuration

```python
Task(
    subagent_type="general-purpose",
    description="Short task description (3-5 words)",
    prompt="""Detailed prompt with worktree instructions...""",
    run_in_background=True  # CRITICAL for parallel execution
)
# OR
Agent(isolation="worktree")  # Automatic worktree management
```

### Worktree Placement Convention

```
<project-root>/worktrees/           # All agent worktrees go here
├── issue-XXX-description/          # Per-issue worktrees
├── rebase-batch1/                  # Rebase batch worktrees
└── rebase-batch2/
```

### Key Branch Protection Settings

Main branch must have:
- Require pull request before merging
- Require status checks to pass
- Enable auto-merge with rebase

This ensures agents cannot push directly to main.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectScylla | 10 issues resolved, 9 PRs merged, ~1,335 lines eliminated | parallel-issue-resolution-with-worktrees 2026-02-13 |
| ProjectScylla | 3 issues, 193 new tests, 4 PRs | parallel-worktree-workflow 2025-02-09 |
| ProjectMnemosyne | 35 issues triaged, 12 LOW executed in parallel, PRs #959-#971 | tooling-parallel-worktree-bulk-issue-execution 2026-03-24 |
| ProjectHephaestus | 34 issues triaged, 19 resolved in parallel batch | tooling-parallel-worktree-issue-batch 2026-03-24 |
| ProjectOdyssey | 70 PRs rebased (v1.0) and 13 PRs (v1.1) | parallel-rebase-agent-worktree-isolation 2026-03-15/27 |
| ProjectScylla | Issue #1887 (JSON-logging/tracing/metrics) split into PRs #1932 (squash-merged green, 22 checks) and #1933 (~24 checks after markdownlint fix) | 2026-05-07 — verified-ci foundation for v1.1.0 split-issue pattern |
