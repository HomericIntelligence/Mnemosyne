---
name: parallel-agent-swarm-dispatch-patterns
description: "Dispatch and verify parallel specialist agents with explicit ownership, bounded tasks, dependency-aware waves, and live artifact checks. Use for 5+ independent tasks, prior stall/fabrication, hot-file contention, staged transformations, audit remediation, or a dependency gate that tempts workers to stop before their actual task."
category: tooling
date: 2026-05-31
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
history: parallel-agent-swarm-dispatch-patterns.history
tags: [swarm, dispatch, worktree, ownership, dependency, verification, orchestration]
---

# Parallel Agent Swarm Dispatch Patterns

## Overview

Parallelism is safe when the coordinator owns the dependency graph and every executor owns a
disjoint artifact set. Prompts must define an executable outcome, stop conditions, verification,
publication protocol, and a compact report. The coordinator independently checks remote state and
artifacts; an agent’s success message is not evidence.

Campaign cases and quantitative observations are indexed in
[`parallel-agent-swarm-dispatch-patterns.notes.md`](parallel-agent-swarm-dispatch-patterns.notes.md).
The complete prior source is archived in
[`parallel-agent-swarm-dispatch-patterns.history`](parallel-agent-swarm-dispatch-patterns.history).

## When to Use

- Five or more tasks can be isolated by worktree and file ownership.
- Earlier agents stalled, returned plans instead of implementation, or reported nonexistent PRs.
- Several issues share a hot file or one transformation must complete before implementation.
- Audit findings need one independently revertible PR per theme.
- A strict dependency chain invites many workers to poll the same gate.
- The first prompt instruction is a wait/poll loop and workers may treat gate failure as task end.

## Verified Workflow

### 1. Re-grade before dispatch

Issue text describes filing-time state. Before assigning work, inspect current main, open PRs,
existing implementation, file size/shape, and dependency status. Classify each task as already done,
still valid, scope-reduced, blocked, or obsolete. Rebuild waves from live evidence.

Use one sequential state-machine executor for a tightly ordered chain. Use concurrent executors only
when their write sets and merge dependencies are disjoint. Bundle multiple issues into one executor
when they all edit a hot file; do not send competing agents to resolve predictable conflicts later.

### 2. Define ownership and outcome

Every dispatch includes:

```text
objective and exact issue/PR identity
isolated worktree and branch
exclusive writable paths
explicit out-of-scope paths
dependency/precondition and what to do if it fails
implementation requirement (not merely plan/research)
test, lint, signing, push, and PR protocol
closing keyword policy
required report: URL, head SHA, checks, residual risks
```

Scope work to one coherent artifact or bounded set. State a practical change budget and instruct the
agent to stop and report if correctness requires crossing ownership. For a partial fix use
`Refs #N`; reserve `Closes #N` for the PR that satisfies the entire issue.

### 3. Match executor capability to work

Use read-only specialists for triage, inventory, and review. Use write-capable executors for code,
tests, commits, and PRs. Route mechanical, fully specified edits to a lightweight executor; use a
stronger specialist for conflict resolution, architecture, or ambiguous CI diagnosis. Keep the
coordinator focused on graph decisions, evidence reconciliation, and exception handling.

Subagents may not be able to spawn another tier. If nested delegation is unavailable, the root
coordinator performs all fan-out. Never encode an architecture that depends on undeclared recursive
delegation.

### 4. Make the prompt executable

Open with an action verb: implement, test, commit, push, and open the PR. Put hard constraints before
context. Include copy-ready commands only when they are repository-correct. Require real evidence
for documentation or generated reports; forbid invented issue numbers, logs, metrics, and links.

For pre-commit, define a bounded diagnostic path. If a hook appears hung, inspect its process and
output, wait only within the stated budget, then stop and report the exact command/state. Do not
bypass required hooks or let every low-risk executor spend the wave repeatedly running a redundant
global suite when CI is the declared gate; still run all checks required by repository policy.

### 5. Harden dependency gates

A precondition is not the task. Use a capped loop, explicit success branch, and an unconditional
continuation directive:

```bash
ready=false
for attempt in 1 2 3 4 5; do
  if <dependency-check>; then ready=true; break; fi
  sleep <bounded-seconds>
done
test "$ready" = true || { echo 'BLOCKED: dependency not ready'; exit 2; }
```

Immediately after the gate, state: “Do not stop here; proceed to Step 1.” Finish with an absolute
rule that success means the implementation PR exists and is verified, not that the gate passed.
When many tasks wait on the same chain, one sequential agent is usually better than N polling agents.

### 6. Gate phase transitions

For a bulk transformation followed by implementation, stop between phases. Verify artifact count,
schema/parsing, expected diff scope, duplicates, and source coverage before dispatching consumers.
Treat malformed or missing artifacts as a blocked wave, not something downstream agents should
guess around.

### 7. Verify every report independently

Before redispatching a quiet executor, search for its branch/PR. A merged PR means it succeeded; an
open PR may still be active; absence permits redispatch. After a report:

```bash
gh pr view <pr> --repo <owner>/<repo> \
  --json state,headRefName,headRefOid,mergeable,statusCheckRollup
gh pr diff <pr> --repo <owner>/<repo> --name-only
```

Confirm the named files, source issue, commit signature, checks, and merge state. Parse structured
artifacts with their actual parser. After a claimed rebase, compare the PR’s content and head—not
only its mergeable flag—to the requested intent.

### 8. Merge in dependency-aware waves

Do not open the next dependent wave until predecessor artifacts are merged and revalidated on
current main. Rebase queued work when its base changes, rerun scoped checks, and update the wave
graph for new conflicts or already-landed work. Preserve isolated worktrees for failures and report
their paths rather than discarding evidence.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Vague prompt | Said only “help with issue” | Executor planned or broadened scope | Specify artifact, action, tests, publication |
| Shared hot file | Gave one file to many agents | Predictable conflict/rebase churn | Bundle hot-file work under one owner |
| Invented identifier | Required a close without supplying ID | Closing semantics became false | Coordinator supplies verified IDs |
| Gate as task | Put wait loop first without continuation | Worker exited after waiting | Cap loop and explicitly continue |
| Concurrent chain wait | Assigned one poller per dependent task | Slots were consumed without progress | Use one sequential state machine |
| Trusted report | Accepted “PR done” | PR was absent, stale, or wrong | Query remote head, diff, and checks |
| Immediate redispatch | Replaced a silent worker | Duplicated already-published work | Search branch/PR state first |
| Unbounded hook | Waited indefinitely on local hook | One worker stalled the wave | Diagnose with budget; never bypass |
| Nested fan-out | Required unsupported delegation | Second-level work never launched | Root coordinator owns fan-out |

## Results & Parameters

```text
task ID and live-state grade
dependency wave and predecessor PRs
executor capability and isolated worktree
exclusive paths and hot-file owner
change budget and stop condition
required validation and publication protocol
poll attempts/delay/deadline where applicable
branch, PR URL, head SHA, changed paths, check states
coordinator verification and next-wave disposition
```

## Verified On

- Multi-wave issue, audit-remediation, and dependency-chain dispatches through 2026-05-31.
- Verification remains `verified-local`; campaign-specific CI results are classified in notes.
