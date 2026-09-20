---
name: review-coordination-parallel-serial-subagent-dispatch
license: BSD-3-Clause
description: "Coordinate review fixes by shared state and dependencies. Use isolated ownership, suitable worker capability, and per-thread evidence when delegation helps."
category: ci-cd
date: 2026-07-03
version: "1.1.0"
user-invocable: false
tags:
  - github-pr-review
  - parallel-dispatch
  - serial-coordination
  - file-grouping
  - model-tier
  - sub-agent
  - haiku
  - sonnet
  - opus
  - review-thread
  - inline-comment
  - fix-coordination
  - domain-knowledge
  - hephaestus-advise
  - thread-aggregation
  - file-collision
  - same-file-serialization
  - different-file-parallelization
  - difficulty-based-routing
  - backward-pass
  - ml-implementation
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/review-coordination-parallel-serial-subagent-dispatch.history"
history-cleanup-date: "2026-09-20"
---

# Review Coordination: Parallel-Serial Sub-Agent Dispatch

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-03 |
| **Objective** | Coordinate multiple specialized sub-agents to fix GitHub PR review inline comments in parallel, avoiding file collisions through file-based serialization, routing tasks to model tiers by difficulty, and aggregating results for verification. |
| **Outcome** | Verified on PR #5538 (issue #5515): four critical backward-pass bugs fixed in ResNet-18 CIFAR-10 training implementation. Package compiled with `--Werror`, all fixes passed human review, commit cb3deb5c landed clean. |
| **Verification** | verified-local |
| **Version** | 1.0.0 |

## When to Use

- A PR has 3+ inline review comments that need fixes
- Review threads are independent and touch different files (parallelize)
- Review threads are in the same file (serialize to avoid concurrent edits)
- You need to avoid race conditions on same-file edits by multiple agents
- Unfamiliar domain behavior benefits from relevant source and knowledge retrieval
- You want to select worker capability according to task complexity
- Fixes require compilation or formatting verification after applying changes
- You need aggregated results (thread_id, one-liner, verification) before committing

## Verified Workflow

### Quick Reference

Group review findings by shared state and dependencies. When delegation is available
and authorized, give independent groups separate owners. Serialize overlapping writes
or use isolated worktrees with deliberate integration. Different files can still
share a behavioral dependency.

### Suggested coordination

1. Bind findings to the current PR revision. Record the thread identifier, file,
   underlying behavior, and evidence; line numbers are lookup hints.
2. Choose local work or delegation from complexity, host capacity, and available
   capabilities. Select models for the reasoning needed, not fixed line thresholds.
3. Give each worker a bounded scope, source revision, relevant findings, existing
   authorization, and meaningful verification targets. Optional knowledge retrieval
   can help with unfamiliar domains; missing advice does not block source inspection.
4. Integrate completed independent groups when ready. Wait where shared changes or
   tests depend on another group. Resolve failures and continue toward the requested
   outcome rather than ending at dispatch or the first implementation.
5. Report actual changes and evidence per thread. Commit or publish when the task
   authorizes it; preserve applicable signing and merge requirements.

A reusable dispatch prompt:

```text
Resolve these review findings for [revision] within [owned scope]: [findings].
Inspect current source and relevant domain guidance when useful. Use the task's
existing authorization for routine choices. Verify the affected behavior using the
available authorized process. Continue independent work if one finding is blocked.
Return each thread's disposition, change, evidence, and unresolved limitation.
```

Detailed historical tool calls, result shapes, and model choices are in
[case notes](./review-coordination-parallel-serial-subagent-dispatch.notes.md).

## Real Example: PR #5538 (ResNet-18 Backward Pass)

### Parsed Threads

| Thread ID | File | Line | Comment | Difficulty |
|-----------|------|------|---------|------------|
| c1 | resnet18_backward.mojo | 120 | avgpool2d_backward receives output instead of input; should use `fwd.s4b2_cache.block_out` not `fwd.gap` | Simple |
| c2 | resnet18_backward.mojo | 240 | relu_backward masks on output; should mask on input `fwd.bn1_pre_relu` not `fwd.relu1_out` | Simple |
| c3 | resnet18_impl.mojo | 380 | cross_entropy requires logits.shape() == targets.shape(); tests pass one-hot labels `(4, 10)` not integers `(4,)` | Medium |
| c4 | resnet18_backward.mojo | 500 | Deferred BN write-back block reverts running stats to pre-forward snapshots; delete 48 lines | Hard |

### Grouping

**Sequential Group 1** (resnet18_backward.mojo):
- c1, c2, c4 all in same file → dispatch ONE agent for all three

**Parallel Group 1** (resnet18_impl.mojo):
- c3 in different file → dispatch separate agent

### Dispatch

```
Agent 1 (Opus, hard + simple = Hard group):
  "Fix 3 review comments in resnet18_backward.mojo: avgpool2d input tensor (c1), relu mask input (c2), deferred BN deletion (c4)"

Agent 2 (Sonnet, medium):
  "Fix 1 review comment in resnet18_impl.mojo: test label one-hot conversion (c3)"
```

### Results

| Thread ID | File | Summary | Verification |
|-----------|------|---------|--------------|
| c1 | resnet18_backward.mojo | Changed `fwd.gap` → `fwd.s4b2_cache.block_out` | `mojo build` ✓ |
| c2 | resnet18_backward.mojo | Changed `fwd.relu1_out` → `fwd.bn1_pre_relu` | `mojo build` ✓ |
| c3 | resnet18_impl.mojo | One-hot label conversion from integers `(4,)` to `(4, 10)` | `mojo test` ✓ |
| c4 | resnet18_backward.mojo | Deleted 48-line stats revert block | `mojo build` ✓ |

**Commit**: cb3deb5c ✓

## Failed Attempts (Anti-Patterns)

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|---------|-----------|------------|
| Dispatch all 4 threads in parallel without grouping | Multiple agents edited same file (`resnet18_backward.mojo`) concurrently | Race condition: agents #1 and #4 both tried to edit lines 120 and 500, rebase conflicts on second push | Group by file first; serialize same-file edits |
| Dispatch one sub-agent per thread, all in parallel | Agent #1 fixed c1, agent #2 fixed c2 with no knowledge of c1's context; agent #4 didn't know c1/c2 were already done | Agents conflicted on same file; incorrect fixes due to missing context of sibling fixes | Prompt each agent with ALL threads for its file in one call |
| Haiku sub-agent attempted hard-difficulty (48-line deletion) | Haiku couldn't understand context; deleted wrong lines | Manual rework needed; wasted cycle | Select sufficient reasoning capability for the semantic risk of the refactor |
| Prompt didn't invoke `/hephaestus:advise` | Sub-agents guessed at domain concepts; thread c4 (BN stats) fix was incorrect | Without understanding running-mean EMA semantics, agent couldn't justify deletion | Inspect relevant source and available domain advice when the concepts are unfamiliar |
| Aggregated results without verification step | Assumed all fixes compiled | One fix introduced a compile error that blocked CI | Add explicit "verify compilation" step before commit |

## Verified Extension: Issue #1814 (ProjectHephaestus, 2026-07-04)

**Session context**: Addressed 4 inline review comments on PR #1814 (planning and plan-review stages) in parallel sub-agents with sequential coordination.

**Workflow extension**:
- **Synchronous completion guarantee**: Used `run_in_background: false` on all sub-agent dispatches to ensure coordinator has all results before verification gates (tests, pre-commit).
- **Same-file serialization with sequential dispatch**: When multiple review threads target the same file (e.g., `planner_review_loop.py` had 2 threads), created ONE sequential sub-agent instead of parallel agents, avoiding edit races.
- **Independent-file parallelization**: Threads on different files (`base.py` vs `test_zero_io_imports.py`) were dispatched as separate parallel sub-agents (different model tiers by difficulty).
- **Sub-agent model selection**: Simple symbol-removal (Haiku), medium docstring addition (Sonnet), hard architectural export guard (Opus).
- **Verification gate post-completion**: After all sub-agents finished, ran full test suite (115 tests) + pre-commit hooks to catch any compile/lint errors before commit.

**Outcome**: All 4 review comments addressed in one session cycle; 115 tests passing; pre-commit hooks passing; PR merged clean (commit 2352687).

## Results & Parameters

- Ownership: one active writer per shared edit surface, or isolated integration.
- Concurrency: independent work within the host's available capacity.
- Worker result: thread identifier, affected file, disposition, concise change,
  executed verification, and any coverage gap.
- Evidence: reported commands and revisions, not an assumed successful compile.
- Model choice: current task complexity and available capability; historic provider
  names and thresholds in the notes are observations, not routing requirements.

---

**See Also**:
- `parallel-agent-swarm-dispatch-patterns.md` — general swarm coordination patterns
- `pr-review-loop-orchestration-agent-patterns.md` — LLM reviewer loops and thread resolution contracts
