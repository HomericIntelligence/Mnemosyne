---
name: swarm-agent-status-misread-as-premature-exit
license: BSD-3-Clause
description: "Distinguish agent progress from termination before retrying delegated work. Use when short status updates, stale transcripts, or polling cause duplicate dispatches."
category: tooling
date: 2026-05-25
version: "1.1.1"
user-invocable: false
verification: verified-local
tags:
  - swarm
  - sub-agent
  - parallel-agents
  - run_in_background
  - duration_ms
  - status-misread
  - premature-retry
  - duplicate-pr
  - branch-collision
  - myrmidon
---

# Swarm Agent Status Misread as Premature Exit

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-25 |
| **Objective** | Stop misreading in-progress status updates from parallel swarm sub-agents as terminal completions and prevent duplicate dispatches |
| **Outcome** | Successful — diagnostic rules and re-dispatch gate confirmed against a 4-agent swarm session |
| **Verification** | verified-local |

## When to Use

- A parallel swarm agent's notification arrives with short `duration_ms` (under 60,000 ms) and `result` text contains "waiting", "polling", "monitoring", or "stand by".
- You are deciding whether to re-dispatch an apparently-stuck swarm agent that hasn't reported completion yet.
- You are auditing a multi-agent swarm session for duplicate dispatches that caused PR or branch collisions.
- The parent agent feels tempted to dispatch a retry within the first minute of a parallel agent's life.

## Verified Workflow

### Quick Reference

Use the host's current agent status and progress records to distinguish ongoing
work, completion, and failure. Notification wording, elapsed time, and file
modification times are clues; none alone proves the lifecycle state.

### Suggested Approach

1. Read the host's documented lifecycle state and available task result. The
   historical timing and notification patterns below may differ on other hosts.
2. If the task is running, wait according to its expected work and continue
   independent work. A short update or a stale transcript alone is not a reason
   to start an overlapping writer.
3. If work has ended or cannot progress, inspect its output and preserve its
   branches and worktrees. Resume or reassign only the remaining scope.
4. When state is unclear, inspect bounded progress metadata or contact the
   existing worker. Resolve ownership before another writer uses its files.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Re-dispatching after a "waiting" result | Treated "background poll is running, I'll wait" as a completion and launched a retry | The agent was still polling — both originals and retries ran concurrently, producing duplicate PRs and branch collisions | Check the current lifecycle state before retrying; wording alone does not prove liveness |
| Treating short-duration notification as completion | Read `result` text without checking `duration_ms`; under-60s status flush mistaken for terminal exit | Intermediate harness flushes can surface a `result` string while the agent is still running; only terminal notifications mean exit | Use timing as context for this harness, not as a general completion rule |
| Assuming same agent-id reported twice | Believed the harness emits multiple notifications per agent | The harness fires ONE terminal notification per agent-id; a "second" one is actually a different agent (the retry you dispatched) | Correlate host lifecycle events by task identity; notification semantics depend on the host |
| Reading transcript JSONL to "check progress" | Opened the subagent JSONL file to see what the agent was doing | The JSONL is forensic, not live status; reading it overflows the parent context and tells you nothing about whether the agent is still running | Prefer bounded progress metadata; inspect a limited transcript excerpt when it helps resolve uncertainty |

## Results & Parameters

**Concrete data from the 4-agent ProjectHephaestus Part 2 swarm session (2026-05-25):**

| Agent | When dispatched | Final notification | duration_ms | Final result | All retries needed? |
| ------- | ----------------- | -------------------- | ------------- | --------------- | --------------------- |
| Site 1 original (`ac2c0882d3dfced16`) | 18:54 | ~19:54 | ~3,500,000 (58 min) | "No work to do — task is complete" (no-op detection) | No |
| Site 2 original (`a0dde4c525b4f292b`) | 18:54 | ~20:08 | ~4,500,000 (75 min) | "Issue #579 is already closed" (no-op detection) | No |
| Site 3 original (`a84bf4e3120662fbe`) | 18:54 | ~19:45 | ~3,000,000 (50 min) | PR #587 opened (real work) | No |
| Site 4 original (`a103b58740ca62f1e`) | 18:54 | ~19:15 | ~1,200,000 (20 min) | PR #584 opened (real work) | No |

All 4 originals were still running when their short status messages arrived. Three unnecessary retries were dispatched (Sites 1, 2, 4) which caused:

- 1 duplicate PR (#586) closed manually as a duplicate.
- 1 duplicate `TestImplLoopStrictRubric` test class that a retry agent had to deduplicate.
- 1 forced `-v2` branch suffix to dodge a branch-name collision.
- Wasted compute on 3 retry agents.

**Diagnostic table — still running vs. exited prematurely:**

| Indicator | Still running | Exited prematurely |
| ----------- | ----------------- | -------------------- |
| `status` field | `in_progress` | `completed` |
| `duration_ms` | growing over time | terminal, often < 60,000 for fast no-op but > 1,200,000 for wait-on-PR |
| `result` text | "waiting", "polling", "monitoring", "stand by" — no PR URL | "Done"/"Complete" with concrete PR URL, OR explicit "FATAL"/"exit 1"/"timed out" |
| Worktree state | locked + transcript file still being written | locked + transcript stops growing |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Part 2 multi-repo audit remediation swarm — 4 parallel Site agents dispatched to wait on a baseline PR; parent misread 3 status updates as completions and re-dispatched, causing PR #586 duplicate and `TestImplLoopStrictRubric` deduplication work | Session 2026-05-25, issue #588 |

## Related Skills

- [[multi-repo-pr-orchestration-swarm-pattern]] — established the parallel-direct-Agent pattern; this skill adds the anti-quit-early constraint that prevents duplicate dispatches from racing the originals.
- [[audit-driven-remediation-workflow]] — the v1.2.0 amendment adds cross-module duplication audit; this skill is the related "swarm process hygiene" lesson learned during that remediation.
