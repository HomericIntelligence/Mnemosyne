---
name: automation-free-tier-quota-exhaustion
description: "Classify free-tier model quota exhaustion during a long queue-owned automation run and resume after reset. Use when a multi-hour loop with free-tier role models fails mid-run, the fallback also reports quota failure, and items end blocked or failed."
category: tooling
date: 2026-11-27
version: "1.0.0"
user-invocable: false
tags: [automation-loop, free-tier, quota, model-provider, recovery, resume, exit-code]
---

# Automation Loop Free-Tier Quota Exhaustion

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-27 |
| **Objective** | Keep a long automation run recoverable when a hosted provider's free tier runs out before the backlog is done. |
| **Outcome** | Operational. One observed run ended after about 74 minutes with mixed dispositions. Provider quota exhaustion, not a code defect, caused most failures. |

## When to Use

- A queue-owned loop runs for hours with role models from a hosted provider's free tier.
- Agent jobs begin to fail with a free-usage-limit message.
- The provider-default fallback then fails with a quota or pre-paid-credits message.
- Many items end with `blocked` or `fail` dispositions while unrelated items still pass.
- The operator must decide whether to repair code, change models, or wait for reset.

Do not use this skill for a crash with no terminal dispositions. Use crash-recovery guidance for that case. Do not use it for a client that throttles its own calls to a reported budget; that is a different decision.

## Verified Workflow

### Quick Reference

| Log signature | Decision |
| ------------- | -------- |
| `free usage limit reached` on a configured role model | Mark the run quota-limited. Do not edit code. |
| Fallback also reports quota or credits required | Treat both signatures as one quota-exhaustion condition. Stop relaunching. |
| Harness has no quota-status command | Ask the operator for reset time or confirmation. Do not guess. |
| Reset confirmed | Relaunch with the same role models. Do not re-seed items by hand. |
| Summary has terminal dispositions and no traceback | Read exit code 1 as "not all items passed", not as a crash. |

### Suggested Approach

1. Read the structured run log before you act. Separate provider quota signatures from genuine defects such as worktree creation failures, poisoned durable records, or stale references in a plan.
2. Do not relaunch while the limit is active. A retry repeats the same failures and spends another wave of attempts.
3. Keep the role-to-model mapping unchanged on relaunch. The coordinator reads current forge labels and review threads, so it resumes only unfinished items. Manual re-seeding adds no value.
4. Treat a nonzero exit as a disposition result when the summary shows terminal dispositions. Report a crash only when a traceback or a boundary error is present.
5. Keep the log as evidence. List genuine defects separately. Do not hide them under a quota classification.
6. When the harness exposes no quota-status command, request the reset time from the operator. Record the limit instead of inventing a reset schedule.

If the log is incomplete, keep the classification provisional and report the missing evidence. If a genuine defect blocks an item independently of quota, repair that defect before the next wave.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Immediate relaunch with the same models | Planned to restart as soon as the run ended | The fallback model was also quota-limited, so a retry would repeat the same failures | Wait for reset, then resume |
| Read exit code 1 as a crash | Assumed a nonzero status meant the process died | The summary showed terminal dispositions for every admitted item and no traceback | Classify from the summary, not from exit status alone |

## Results & Parameters

### Configuration

```yaml
classification:
  primary_signature: "free usage limit reached"
  fallback_signature: "quota or pre-paid credits required"
  scope: provider-quota-not-code-defect
recovery:
  relaunch_before_reset: false
  reuse_role_models: true
  manual_reseed: false
  exit_code_1_with_terminal_dispositions: not-a-crash
```

### Expected Output

- One quota classification decision is recorded before any rerun.
- No relaunch happens while the provider reports quota exhaustion.
- On relaunch, only unfinished items are admitted.
- Genuine defects are listed separately from quota failures.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Public queue-owned automation host | One multi-hour backlog run over about two dozen items | The first free-limit signature appeared about 41 minutes into the run; the fallback quota signature appeared about 64 minutes in. Final dispositions were 3 pass, 14 fail, 7 blocked, and 1 pending. See [notes](automation-free-tier-quota-exhaustion.notes.md). |

## References

- [interrupted-automation-loop-relaunch-salvage](interrupted-automation-loop-relaunch-salvage.md) — crash salvage, a different trigger.
- [automation-loop-backlog-cost-scaling](automation-loop-backlog-cost-scaling.md) — cost sizing before a large wave, a different intent.
- [hephaestus-random-model-draw-launch-safety](hephaestus-random-model-draw-launch-safety.md) — launch-time model binding, a different phase.
