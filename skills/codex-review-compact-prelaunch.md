---
name: codex-review-compact-prelaunch
description: "Prevent Codex automation-fleet plan-review context overflow. Use when: (1) a Codex-based Hephaestus fleet review session fails with 'input (...) is longer than the model's context length' or 'reviewer failures exhausted', (2) an auto-compact token limit installed mid-run does not rescue sessions that were already bound, or (3) a fleet relaunch must start review sessions under a new compact threshold."
category: tooling
date: 2026-11-19
version: "1.0.0"
user-invocable: false
verification: verified-local
license: BSD-3-Clause
tags:
  - codex
  - hephaestus
  - context-limit
  - auto-compact
  - plan-review
  - session-binding
---

# Codex Review Compact Prelaunch

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-19 |
| **Objective** | Stop plan-review context overflow in a Codex-based automation fleet by installing the compact limit before review sessions bind and resetting bound sessions after a limit change. |
| **Outcome** | Operational. A mid-run compact-limit change did not rescue already-bound sessions; pre-launch configuration plus `--reset-plan-review-session` starts review sessions under the new limit. |

## When to Use

- A Codex fleet review job fails with `codex_tool_or_provider_failure` or `reviewer failures exhausted`.
- The log shows `input (<N> tokens) is longer than the model's context length (<M> tokens)` for a review session.
- A compact token limit added to `config.toml` or the model catalog mid-run does not change the behavior of running jobs.
- A fleet relaunch must guarantee that every review session starts under the new compact threshold.

## Verified Workflow

### Quick Reference

```bash
# 1. Before the fleet starts: set the compact limit in the Codex home config
#    (Codex config keys; names follow the installed Codex version's schema)
#    model_auto_compact_token_limit = 700000

# 2. Launch with review-session reset so no stale session binding survives
hephaestus-automation-loop ... --agent codex --reset-plan-review-session ...
```

The rule: **a compact limit applies only to sessions that start after the config change.** Install the limit before the first review session binds, or reset the session binding so review jobs start fresh.

### Suggested Approach

1. **Distinguish the two reviewer failure modes first.** Read the loop log and job receipts. Context overflow shows an input-token count above the model's context length. SSE idle timeouts show `stream disconnected before completion: idle timeout waiting for SSE`. Overflow needs a compact limit and a session reset; idle timeouts are provider-level and retryable. Do not apply the overflow fix to timeout failures.
2. **Set the compact limit before launch.** Put the limit in the Codex home `config.toml` and mirror it in the model catalog entries for the roles that review. Choose a threshold that leaves room for one review round of output, such as 70 percent of the context window.
3. **Reset plan-review sessions after any limit change.** Pass `--reset-plan-review-session` on the relaunch. A review session that was bound before the change keeps its old, oversized history; a fresh session starts under the new limit.
4. **Relaunch rather than hot-patch a running fleet.** Stop the loop through its graceful shutdown path, apply the config, and start a new run. Check the launch log for the effective configuration before letting the fleet continue.
5. **Verify with fresh failure evidence.** After the relaunch, confirm that new review jobs either succeed or fail for a different reason. If overflow still appears with a session that started after the change, raise the threshold question: the limit may be too close to the window, or the session may have bound before the change.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Install a 700,000-token auto-compact limit in `config.toml` and the model catalog while the fleet kept running. | Already-bound review sessions kept their pre-change history. New limit did not apply to them; they still failed with `input (1119230 tokens) is longer than the model's context length (1048576 tokens)`. | Auto-compact applies at session start. Mid-run config changes do not retro-rescue bound sessions. |
| 2 | Keep waiting for review retries on the bound sessions after the config change. | Retries resumed the same oversized session, so each retry re-hit the same overflow. | Retry does not clear a binding. Reset the session or relaunch. |

## Results & Parameters

### Configuration

```toml
# codex-home/config.toml — threshold before launch, not mid-run
model_auto_compact_token_limit = 700000
```

```bash
# fleet launch flags that matter for this skill
--agent codex
--reset-plan-review-session
```

### Expected Output

- New review sessions start with an input size below the compact threshold.
- Context-overflow failures stop appearing for sessions created after the relaunch.
- Remaining reviewer failures, if any, are retryable provider errors such as SSE idle timeouts, not token-count overflows.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| LLM360/comet | 68-issue Codex fleet via Hephaestus automation loop | See [notes](codex-review-compact-prelaunch.notes.md). |

## References

- [OpenCode compaction trigger window budget](opencode-compaction-trigger-window-budget.md) — related compaction configuration for OpenCode, a different tool
- [OpenCode context-limit receipt recovery](https://github.com/HomericIntelligence/Mnemosyne/pull/4044) — recovery after a context failure, not pre-launch prevention
- [Codex CLI](https://github.com/openai/codex)
