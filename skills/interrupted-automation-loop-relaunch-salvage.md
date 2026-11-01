---
name: interrupted-automation-loop-relaunch-salvage
license: BSD-3-Clause
description: "Restart a crashed or throttled multi-attempt automation loop without losing in-flight worker output or self-aborting on a false dirty-tree reading. Use when per-item workers edit isolated Git worktrees, an earlier attempt ended abnormally, and more restarts are planned; also use before you relaunch a worker whose death left no visible forge record, because an interrupted worker can publish work and then remove the evidence of that publication."
category: tooling
date: 2026-10-12
version: "1.1.0"
user-invocable: false
verification: verified-local
tags:
  - automation-loop
  - crash-recovery
  - relaunch
  - worktree
  - salvage
  - git-stash
  - commit-salvage
  - orphan-session
  - liveness
  - intake-gate
  - dirty-tree
  - supervisor
---

# Relaunch Salvage for an Interrupted Automation Loop

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-10-12 |
| **Objective** | Restart a crashed multi-attempt automation loop whose per-item workers edit isolated Git worktrees, with zero loss of in-flight output and no self-abort on a false dirty-tree reading. |
| **Outcome** | Successful — in-flight output from a killed attempt was preserved as commits on five worker branches (27 file changes, including content that had existed only as stash entries); the next attempt resumed every claimed work item, and no further attempt self-aborted on a false dirt reading after the preflight gate was corrected. |
| **Verification** | verified-local — salvage commits verified by blob identity; restart behavior observed across supervised attempts on a live multi-tenant automation host; the step-0 discovery predicate was added after a case where a self-erasing publication hid a non-empty worker (v1.1.0). |

## When to Use

- You supervise repeated attempts of a per-issue or per-item automation loop, and each worker edits one isolated Git worktree on its own branch.
- An earlier attempt ended abnormally — rate limit, tool crash, host stop — while some workers were mid-flight.
- A wrapper script decides from the intake state whether a new attempt may start (a preflight cleanliness gate).
- Some workers run as sessions on a shared agent-service daemon, so terminating the loop does not terminate them.
- One worker died and you are about to relaunch or replace it. Establish what it produced before you decide it produced nothing; see step 0.

## Verified Workflow

### Quick Reference

```bash
# 0. Before you call a dead worker empty, prove it produced nothing. A forge
#    comment list and an open-PR list are NOT sufficient: a publication step can
#    delete its own source records. Check all four surfaces:
gh pr list --search "<item>" --state all --json number,state     # forge PRs
ls <primary-project>/.worktrees | grep -i "<item>"               # worktrees
git ls-remote --heads origin | grep -i "<item>"                  # unpushed? then
                                                                 # this stays empty
git -C <worktree> log --oneline origin/main..HEAD                # committed work
git -C <worktree> status --short                                 # uncommitted work

# 1. Salvage BEFORE any relaunch: commit in-flight work onto each worker branch.
#    Stage tracked edits (`git add -u`) plus explicitly named new source files.
#    Never `git add -A` here: durable-state directories (build journals) and
#    virtual environments can sit untracked in the tree and must stay out.
cd <worker-worktree> && git status --porcelain
git add -u && git add <explicit-new-source-files> && git commit -m "salvage <item>"

# 2. Never preserve resumable output as a stash entry. A resumed worker cannot
#    see a stash; it regenerates or collides. For pre-existing stashes: restore
#    each onto its branch as a commit, verify blob ids, archive the entries,
#    and only then drop them.

# 3. Gate each restart with the tool's own intake predicate, read from the
#    tool's source — e.g. intake acceptance was:
git status --porcelain --untracked-files=no   # tracked changes only; untracked
    # build/ state never blocks; the operator checkout is not inspected at all.

# 4. Check worker liveness before salvaging or relaunching. Require BOTH:
#    worktree file mtimes idle and the session store's last-update age older
#    than an idle floor (~10 min). Never relaunch into a live writer.

# 5. Stop a supervisor by its recorded PID and verify with `kill -0`. A
#    `pkill -f <script path>` pattern also matches the probing command line
#    that contains the same path — the probe kills itself.
```

### Suggested Approach

0. Establish the true produced-state before any relaunch. "No new comments and no open pull request" does not prove that a worker produced nothing, because a publication step can be self-erasing: a plan-finalization step published a verified digest to the item body and then deleted its own two sealed source comments under an allowlist. A later reader saw a clean item and a clean forge, and would have restarted a lane that already held a signed commit and about 3 000 lines of uncommitted refinement. Enumerate all four surfaces — forge records, worktree directory, remote branch tips, and the local commits and working tree inside a discovered worktree — and treat "no evidence on the forge" as unproven rather than empty. When work exists, resume it instead of restarting: keep the branch, finish the incomplete edits, and require the new worker to reproduce the verification receipts itself, because the dead worker's receipts cannot be trusted for a tree you changed.
1. Treat loop death as partial. The loop process, a wrapper supervisor, and each worker are separate processes. Workers that run as sessions on a shared service daemon keep writing after the loop exits, and you usually cannot kill them because the daemon serves other tenants. Plan to salvage around them rather than through them.
2. Salvage onto branches before every restart. Commit tracked worker output (`git add -u`) and explicitly named new source files onto each worker's own branch. Keep untracked durable state (for example a `build/` journal tree) out of the commit; the next attempt reuses that state on disk. If output survives only in stash entries, restore each entry onto its branch as a commit, verify the restored blobs against the stash diff, keep an archive copy, and drop the stash afterward — a resumed worker cannot discover stash entries, so preservation that it cannot see is loss.
3. Copy the intake cleanliness predicate verbatim from the tool's source. Do not approximate it. An over-approximating preflight (plain `git status --porcelain`, which counts untracked build output as dirt) self-aborted five consecutive restart attempts in one session. An under-approximating preflight can relaunch a worker into a live tree. Run the tool's exact command — in this intake, `git status --porcelain --untracked-files=no`, evaluated over the intake worktrees only.
4. Require a double signal for worker liveness: worktree file mtimes AND the durable session store's last-update timestamps. When both are below an idle floor (about 10 minutes), treat the worker as dead, then salvage. When a writer has stayed active past a stale ceiling (about 90 minutes), alert the operator and do not relaunch into that tree.
5. Space attempt starts with a quiet floor when rate-limit pressure caused the stop, and classify the limit before reacting. See [github-shared-token-lockout-rate-limit-diagnosis](github-shared-token-lockout-rate-limit-diagnosis.md).
6. Do not guess branch publication names. Local run-scoped worker branches (for example names carrying a per-run nonce suffix) can map to shorter remote publication names. Read the mapping from the tool's source, push to the mapped remote names, and verify remote tips after the push.
7. Track progress from operator-owned logs and durable state, not from harness-bound handles; see [detached-launch-survives-harness-restart](detached-launch-survives-harness-restart.md) for the launch-side discipline.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Preserve in-flight output as git stashes | Rescuing a killed attempt left 6 stash entries across the worker worktrees | A resumed implementer could not see the stash entries and regenerated the work; stashes are invisible to the next attempt's planning and checkout logic | Preserve recoverable output as commits on each worker branch; restore legacy stashes to commits with blob verification before dropping them |
| Plain-porcelain preflight gate | The supervisor ran `git status --porcelain` per intake worktree and refused to launch on any output | Untracked `build/` journal directories counted as dirt, so five consecutive attempts self-aborted within seconds — the tool's real gate never checks them | Take the intake predicate from the tool's source (`--untracked-files=no`, tracked-only); over-approximation starves restarts, under-approximation relaunches into dirt |
| `pkill -f` on the supervisor script path | Sent the termination signal by pattern-matching the supervisor's script path | The probing shell's own command line contained the same path pattern, so the probe received SIGTERM together with the supervisor | Record and kill supervisors by PID; verify death with `kill -0 <pid>` from a command line that cannot self-match |
| Assume loop death implies worker death | Post-crash salvage started from the assumption that no writer was active | Orphaned worker sessions on the shared service daemon kept producing edits after the loop exited; salvage raced live writers | Check companion liveness signals (worktree mtime plus session-store update age) before any salvage or relaunch |
| Read an empty forge as an empty worker | Judged a dead worker by counting new comments and open pull requests on the item | The worker had published a verified digest to the item body and deleted its own sealed source comments, so the forge looked untouched while a signed commit and about 3 000 lines of unstaged work sat in a local worktree | Enumerate worktrees, remote tips, local commits, and the working tree before declaring a lane empty (step 0); resume the work you find rather than restarting it |

## Results & Parameters

### Configuration

```yaml
liveness:
  idle_floor_minutes: 10        # dual signal (worktree mtime + session-store age)
  stale_writer_alert_minutes: 90  # live writer older than this blocks relaunch
salvage:
  stage: tracked-only-plus-explicit-new-source-files
  never_stage: [build-journal-dirs, virtualenvs, lockfiles-you-do-not-own]
  preserve_before_drop: archive-of-restored-stash-diffs
relaunch:
  quiet_floor_seconds: [600, 1800]  # space attempt starts under rate-limit pressure
```

### Expected Output

- Every worker branch contains all recoverable in-flight output as commits; no stash-only content remains.
- Each interrupted worker is classified as empty or non-empty from all four surfaces, not from forge records alone.
- The preflight outcome agrees with the tool's own intake acceptance on every worktree.
- Each new attempt starts only after workers below the idle floor on both liveness signals.
- Restart attempts resume claimed items instead of regenerating or duplicating them.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Private automation host | Three-day supervision of a 35-item per-issue automation loop across 11 supervised attempts, with rate-limit deaths, a corrected preflight gate, and a 27-file-change salvage | See [notes](interrupted-automation-loop-relaunch-salvage.notes.md). |

## References

- [github-shared-token-lockout-rate-limit-diagnosis](github-shared-token-lockout-rate-limit-diagnosis.md)
- [detached-launch-survives-harness-restart](detached-launch-survives-harness-restart.md)
- [tooling-git-recover-stashed-work-after-concurrent-branch-reset](tooling-git-recover-stashed-work-after-concurrent-branch-reset.md)
- [git-worktree-parallel-execution-lifecycle](git-worktree-parallel-execution-lifecycle.md)
- [Git worktree documentation](https://git-scm.com/docs/git-worktree)
- [Git stash documentation](https://git-scm.com/docs/git-stash)
