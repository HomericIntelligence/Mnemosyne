---
name: shared-token-agent-identity-claim-coordination
description: "Coordinate many automated agents that share one forge credential, where every post shows one author. Use when parallel agent lanes must claim, communicate, and attribute work on issues, pull requests, and a discussion board without stealing each other's work."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: verified-local
license: BSD-3-Clause
tags: [agent-coordination, shared-token, identity-prefix, claim-post, discussion-board, attribution, collision-avoidance]
---

# Shared-Token Agent Identity and Claim Coordination

**Supporting cases:** [notes](./shared-token-agent-identity-claim-coordination.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Let many parallel agent lanes coordinate on one forge where a shared credential makes every commit, comment, and discussion post show the same author |
| **Outcome** | Operational — the pattern runs as a repository-level coordination contract for fleets of parallel agent lanes |
| **Verification** | verified-local |

## When to Use

- Many automated agents work in one repository and sign in with one shared credential,
  so the forge shows one author for every agent's comments and posts.
- Operators and sibling agents must attribute a post to its lane, and lanes must not
  create duplicate pull requests for work another lane owns.
- The repository has a discussion board with a dedicated section for agent
  coordination.
- You dispatch lanes in waves and each lane must announce its claim before it writes.

## Core Rule

Forge attribution fails under a shared token. Replace it with a content marker:

1. **One stable identity per task.** Each agent selects one unique name at dispatch
   (for example a role string plus an issue number) and prefixes every issue comment
   and discussion post with `[<name>]`. The name does not change for the life of the
   task. A new task gets a new name.
2. **Claim before write.** Before work starts, search the coordination categories for
   an applicable discussion. Post a claim in the form
   `[<name>] claiming #N - next step: <step>`. Create a new discussion only when no
   applicable one exists.
3. **Public-record discipline.** Treat every comment and post as a public record. No
   credentials, tokens, PII, or secrets. Keep posts short: state the goal first, then
   the result or the request. Plans live in the issue; implementations live in the
   pull request; discussion posts carry only coordination.
4. **Decision hold.** When an operator decision is necessary, post
   `[DECISION-NEEDED]` in the thread and hold that path until an answer arrives.

## Verified Workflow

### Quick Reference

```text
[<name>] claiming #<issue> - next step: <step>     # in the applicable discussion thread
[<name>] <comment body>                             # on every issue comment
[DECISION-NEEDED]                                   # hold the path until answered
```

### Suggested Approach

- Read the coordination section before creating a thread. Reuse keeps context in one
  place; one thread per issue is a habit to avoid, not a rule to follow.
- If another agent claimed the issue, coordinate in its thread. Do not create a second
  pull request for the same work.
- Choose the name at the moment ownership starts, not at first failure — an unclaimed
  lane that posts late forces readers to guess authorship across a shared identity.
- A lane that finds its assigned work already delivered (superseded, closed, or landed
  by another route) does not start new work: capture the evidence, give the durable
  learning step a chance, report the final disposition with its declared name, and
  stop.

If the repository has no coordination section, use the single nearest category and say
so in the first post; do not create a parallel channel outside the agreed record.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Implicit attribution | Parallel lanes posted on shared issues under one forge account without name prefixes | Operators could not tell strides apart; answers landed in the wrong lane's thread | Authorial identity must travel in the content when the forge identity is shared |
| Thread-per-issue habit | One open coordination discussion per issue by default | Context fragmented across many near-empty threads; duplicate claims went unnoticed | Search and reuse first; create a thread only when no applicable one exists |
| New PR instead of claim | A lane opened its own pull request for an issue a sibling had claimed | Two implementations raced for the same title and scope | The claim post names the owner; coordinate there instead of forking the work |

## Results & Parameters

### Configuration

```yaml
identity: "[<unique-name-per-task>]"
identity_lifetime: task-length
claim_format: "[<name>] claiming #N - next step: <step>"
decision_hold_format: "[DECISION-NEEDED]"
discussion_scope: dedicated-coordination-categories-only
content_rules:
  - public-record-discipline-no-secrets-no-PII
  - goal-then-result-or-request-one-or-two-sentences
  - plans-in-issues-implementations-in-pull-requests
```

### Expected Output

- Posts attributable to one lane each, despite one forge author.
- One owner per issue by claim, visible in one reused thread.
- Operator holds visible and honored by the blocker-post marker.
- No duplicate pull requests for claimed work.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A policy-bearing repository shared by parallel agent waves (identifier withheld under the privacy policy) | Repository contract adopted the shared-token identity-prefix rule, claim posts, coordination-category scope, and the decision-hold marker for fleet operation | See [notes](./shared-token-agent-identity-claim-coordination.notes.md) |

## References

- [Lane branch zero-ahead merge state check](lane-branch-zero-ahead-merge-check.md) — the
  sibling read-gate that stops re-implementation of delivered lane work
- [Clear open issue backlog with swarm subagents](clear-open-issue-backlog-myrmidon-swarm.md) —
  swarm waves whose lane claims and exclusive ownership this protocol formalizes
