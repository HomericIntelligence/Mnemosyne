---
name: tooling-swarm-subagent-needs-write-tools
description: "For any swarm sub-agent that must commit/push/edit/create-PR OR write any output file (JSON/MD/log), set subagent_type=general-purpose. feature-dev:code-architect / code-explorer / code-reviewer / Explore / Plan are read-only by design — they produce blueprints, not artifacts. Failure mode is silent OR HALLUCINATED: agents may claim 'Wrote /tmp/output.json' in their summary while no file exists on disk. Use when: (1) dispatching parallel sub-agents for issue implementation, (2) any agent prompt that includes 'git commit' or 'gh pr create' or file edits, (3) any agent prompt asking the agent to 'write JSON to', 'save report to', 'emit file at', (4) you notice a sub-agent returning detailed file blueprints with diff content but no PR URL, (5) you see 'I do not have shell execution' or similar tool-availability complaint at the end of an agent run, (6) an aggregator step finds the expected artifact missing despite a successful-looking summary."
category: tooling
date: 2026-05-18
version: "1.1.0"
user-invocable: false
verification: verified-local
tags:
  - sub-agent
  - swarm
  - subagent-type
  - tool-availability
  - dispatch
  - myrmidon
  - implementation-vs-design
  - hallucinated-success
  - artifact-verification
  - explore-agent
---

## Overview

| Field | Value |
|---|---|
| Date | 2026-05-18 |
| Objective | Avoid dispatching swarm implementation OR artifact-producing agents under a read-only subagent_type |
| Outcome | Validated twice — (2026-05-16) MEDIUM Wave 1 misdispatch wasted ~80k tokens, re-dispatch with general-purpose shipped PRs #387-#390. (2026-05-18) 4 of 12 Explore agents in a skill-clustering swarm silently dropped their JSON outputs (some hallucinated success); general-purpose redispatch fixed it. |
| Verification | verified-local |

## When to Use

- Dispatching parallel sub-agents via the `Agent` tool for issue implementation
- Any agent prompt that includes `git commit`, `git push`, `gh pr create`, `gh issue close`, or any `Write`/`Edit` operation
- **Any agent prompt that asks the agent to write an output file** (JSON report, markdown summary, log shard, partial cluster file, etc.) — `Explore` and `Plan` agents have NO `Write` tool and will either silently no-op OR hallucinate "Wrote /tmp/foo.json" in their final summary while leaving the disk untouched
- You notice a sub-agent returning detailed file-level blueprints with diff content but no PR URL
- An agent's final reply contains phrases like "I do not have shell execution", "available tools don't include Bash", "I can only Read/Grep"
- An aggregator step finds an expected artifact missing even though the producing agent's summary said it was written — **always `ls` the artifact before trusting the summary**
- The subagent_type name **sounds** implementation-y (e.g., "code-architect") but you haven't verified its toolset

> **Verification is mandatory.** Subagent summaries are unreliable for write actions on read-only toolsets. The orchestrator must `ls -la` (or equivalent) every promised artifact path after dispatch and treat missing files as failure regardless of what the agent said.

## Verified Workflow

### Quick Reference

```text
For implementation work in a swarm:
  subagent_type: "general-purpose"   ✓ has Bash, Write, Edit, full toolset

For research/design only:
  subagent_type: "feature-dev:code-architect"     ← read-only
  subagent_type: "feature-dev:code-explorer"      ← read-only
  subagent_type: "feature-dev:code-reviewer"      ← read-only
  subagent_type: "Explore"                        ← read-only
  subagent_type: "Plan"                           ← read-only
```

### Detailed Steps

1. Before dispatch, read the agent's prompt — if it contains any write action (commit/push/PR/edit/close/label), the subagent must have write tools.
2. Default to `subagent_type: "general-purpose"` (or omit the field entirely; default is implementation-capable).
3. Reserve the `feature-dev:*` subagents and `Explore`/`Plan` for pure research, blueprinting, code review, codebase mapping — phases where output is text/analysis, not file changes.
4. If a misdispatch happens, salvage the blueprint output by passing it as a context block to a `general-purpose` re-dispatch (saves re-analysis cost).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---|---|---|---|
| 1 | Dispatched 4 parallel `feature-dev:code-architect` sub-agents for MEDIUM-tier C++ issue implementation (commit + push + gh pr create) | All 4 produced detailed file-level blueprints with exact line numbers and diff content, ran 5-10 min each, then failed with "I do not have shell execution (Bash) or file write (Write/Edit) tools available in this agent environment" — no PRs created | The subagent description "Designs feature architectures by analyzing existing codebase patterns and conventions, then providing comprehensive implementation blueprints" should have been the tell. "Providing blueprints" ≠ "executing implementation". |
| 2 | Assumed `feature-dev:code-reviewer` would commit review-driven fixes | Same root cause — read-only toolset (`Glob, Grep, LS, Read, NotebookRead, WebFetch, TodoWrite, WebSearch, KillShell, BashOutput`) | The "feature-dev:*" family is consistently read-only by design. Any task that ends with a write action needs `general-purpose`. |
| 3 | Dispatched 12 parallel `Explore` (subagent_type) Sonnet workers to shard-read skill files and write per-shard JSON cluster reports to `/tmp/skill-reports/X.json` (2026-05-18 ProjectMnemosyne clustering swarm) | 4 of 12 agents returned final summaries claiming "Wrote /tmp/skill-reports/X.json" — but `ls /tmp/skill-reports/` showed no such file. `Explore` toolset is read-only (`Read, Grep, Glob, WebFetch, WebSearch, Bash` — no `Write`). One agent (afedf208) recognized this: *"I cannot complete the original request to write `/tmp/skill-reports/arch-shard-00.json` because this is a READ-ONLY exploration session."* The others hallucinated success. Redispatch with `subagent_type=general-purpose` and identical prompt produced the file on first try. | **Subagent self-reports are not evidence for write actions.** When dispatching to `Explore`/`Plan`/`feature-dev:*` for anything that emits an artifact, the orchestrator MUST verify the artifact on disk and treat the agent's "Wrote X" claim as a hallucination until proven otherwise. Default to `general-purpose` for any prompt containing "write", "save", "emit file", or a target path. |

## Results & Parameters

Copy-paste ready dispatch pattern:

```python
# CORRECT for implementation work
Agent(
    description="MED-<N> implement issue",
    subagent_type="general-purpose",   # write-capable
    model="sonnet",                     # or "opus" / "haiku" per tier
    isolation="worktree",
    prompt="""...git commit / push / gh pr create steps..."""
)

# CORRECT for research/design only
Agent(
    description="Design partition plan",
    subagent_type="feature-dev:code-architect",   # read-only — produces a blueprint doc
    model="sonnet",
    prompt="""Read codebase, emit phase4-waves.json with per-issue briefs..."""
)
```

## Verified On

| Project | Context | Details |
|---|---|---|
| ProjectAgamemnon | 2026-05-16 Myrmidon swarm — MEDIUM Wave 1 misdispatch then re-dispatch (PRs #387-#390) | Initial read-only dispatch produced blueprints; re-dispatch with `general-purpose` shipped distinct PRs |
| ProjectMnemosyne | 2026-05-18 skill clustering swarm | 4/12 `Explore` agents lost their JSON output — some silently, some hallucinated "Wrote /tmp/skill-reports/X.json" in the summary. `general-purpose` redispatch fixed it. Confirms failure mode #3: summaries lie when the toolset is read-only. |
