---
name: opencode-context-limit-receipt-recovery
description: "Recover an OpenCode session after a context-limit warning, degenerate output, or an incomplete tool call. Use when narrative and tool receipts disagree, tool-like markup appears as plain text, or a compression attempt fails and work must resume without inventing actions."
category: tooling
date: 2026-11-18
version: "1.0.0"
user-invocable: false
verification: verified-local
license: BSD-3-Clause
tags: [opencode, context-limit, compaction, recovery, tool-receipts, degenerate-output, evidence]
---

# OpenCode Context-Limit Receipt Recovery

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-18 |
| **Objective** | Restore a safe action boundary after a context or output failure without losing durable state or inventing completed work. |
| **Outcome** | Operational. A smaller complete compression call succeeded after an oversized attempt failed. Actual tool receipts and live reads then separated executed actions from narrative. |

## When to Use

- The host reports a maximum-context or output-token emergency and requires compression.
- Assistant output repeats tokens, contains tool-like markup as plain text, or claims an action without a tool result.
- A compression call fails because its input is incomplete or too large.
- A compressed summary, assistant narrative, and direct tool or forge evidence disagree.
- You must resume delegated work, external mutations, or a completion report after one of these failures.

## Verified Workflow

### Quick Reference

```text
Context emergency       -> finish only an atomic step, then compress closed history.
Compression input fails -> retry once with smaller, complete arguments; do not continue exploration.
Tool-like text          -> unverified until an invocation, result, or live state confirms it.
Failed tool result      -> attempted; read back the outcome and side effects.
Assistant narrative     -> a lead to verify, never proof of an action or current state.
After compression       -> build the action ledger, read live state, then resume.
```

### Suggested Approach

1. **Establish the recovery boundary.** Finish only an atomic operation that cannot safely stop midway. Then use the host compression tool before normal exploration. Keep the newest active user instruction outside the compressed range when possible. A stale pending task must not displace that instruction.
2. **Repair a failed compression call.** If the tool reports incomplete input, replace the attempt with one smaller, complete call. Select older resolved history, preserve the active work and required block references, and confirm the tool's success receipt. Do not emit a summary as ordinary assistant text and call it compression.
3. **Build an action ledger from receipts.** Pair each claimed action with its actual tool invocation and result, delegated-session identifier, file write, or forge readback. Tool-shaped prose is not an invocation. Without an invocation and result, classify the action as unverified until live state or independent evidence resolves it. A failure receipt proves an attempt, not success; its side effects also need readback.
4. **Read current state before another mutation.** Query the live artifact, branch, work item, or worker registry. Use tool receipts to decide what happened and live reads to decide what is true now. Treat summaries and assistant claims as leads when they conflict with those sources. Read back an uncertain external write before retrying it; this reduces duplicate side effects and can show that a retry is unnecessary.
5. **Revalidate delegated evidence before use.** Check that an expected artifact exists and that its identity, schema, and decisive claims bind to the current target. If a worker says that it reconstructed a report from a transcript, treat its execution claims as unverified until direct evidence supports them. Apply the delegated-claim and forge-readback rules in the references.
6. **Resume only evidenced pending work.** Select one bounded next action from the reconciled state. Record each resulting state change after its receipt. Do not report completion while the live scope still contains open work, and do not relaunch a worker whose actual launch receipt or live registration already exists.
7. **Degrade safely if compression is unavailable.** Stop nonessential mutations and produce a compact durable checkpoint of receipts, live state, and pending work. Do not claim that compression occurred.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Compress with an oversized argument | Continued normal work after repeated context warnings, then supplied an incomplete oversized compression call. | The tool rejected the input and no compression occurred. | Compress first. After `tool.input-incomplete`, use a smaller complete argument and verify the success receipt. |
| Treat tool-shaped prose as dispatch | Emitted tool-like markup and later described a triage lane as launched. | The transcript had no actual invocation, and live reconciliation found no worker. The claimed launch could not count as executed. | Classify an unconfirmed dispatch as unverified; resolve it through receipts and live worker state. |
| Trust degenerate completion prose | Repeated output fragments and then stated that no work remained. | Direct inventory still showed open work, so the statement was false. | Rebuild pending work from live state and receipts, never from degenerate narrative. |

## Results & Parameters

### Configuration

```yaml
recovery_order:
  - finish_atomic_step_if_needed
  - compress_closed_history
  - build_receipt_ledger
  - reconcile_live_state
  - resume_one_bounded_action
compression_retry: smaller_complete_arguments
action_evidence: actual_tool_invocation_result_or_independent_live_evidence
current_state_evidence: live_readback
summary_and_narrative: leads_only
failed_tool_result: attempted_outcome_and_side_effects_require_readback
uncertain_external_write: read_back_before_retry
active_user_instruction: preserve_outside_compression_when_possible
```

### Expected Output

- A confirmed compression result, or an explicit durable-checkpoint fallback.
- An action ledger that separates completed actions, failed attempts, and actions that never executed.
- A live-state inventory that supersedes conflicting narrative.
- No phantom worker launch, duplicate external write, or unsupported completion claim.
- The next action binds to the current user request and verified pending work.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| OpenCode V2 | Long multi-lane coordination session, 2026-11 | Privacy-safe source boundary and observations are in [notes](opencode-context-limit-receipt-recovery.notes.md). |

## References

- [OpenCode compaction trigger with a fixed token budget across window sizes](opencode-compaction-trigger-window-budget.md) — prevention through configuration; this entry covers recovery after the limit is reached.
- [OpenCode V2 Prior-Session Evidence Recovery](tooling-opencode-v2-prior-session-evidence-recovery.md) — read-only transcript recovery when the needed session evidence is absent.
- [Campaign Handoff Prompt Authoring](campaign-handoff-prompt-authoring.md) — durable handoff content and mutable-state readback.
- [Verify a Completion Report Against the Forge](verify-completion-report-against-forge.md) — completion claims require artifact readback.
- [Verify Delegated Agent Claims and Run the Full Suite Before Pushing](verify-delegated-agent-claims-run-full-suite.md) — decisive delegated claims require direct evidence.
