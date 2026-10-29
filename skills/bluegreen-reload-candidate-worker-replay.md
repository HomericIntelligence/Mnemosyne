---
name: bluegreen-reload-candidate-worker-replay
license: BSD-3-Clause
description: "Reload a front-end gateway by blue/green handoff while workers are live, and read the real rejection reason. Use when: (1) an in-place gateway restart times out or reports a release mismatch, (2) the front-end log says the candidate worker readiness timed out and the active generation remains serving, (3) you must load a front-end change without a cold restart, (4) a dashboard shows no entries for the new generation."
category: debugging
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [blue-green, gateway-reload, candidate-readiness, worker-registration, handoff, dashboard-lag]
---

# Blue/Green Reload With Live Workers

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Switch a gateway to a new generation without a cold stop, and diagnose a rejected candidate from the right log. |
| **Outcome** | Operational. A reload with live workers was rejected twice because no worker registered on the candidate. After the active workers were replayed onto the candidate in the readiness window, the handoff completed in the same allocation. |

A candidate generation starts on an idle slot. The front waits until every
worker that the active generation holds is registered on the candidate. Nothing
registers them by default. With live workers the candidate always times out and
the active generation keeps serving. The restart command then waits for its own
timeout and prints a message that looks like a release-name mismatch.

## When to Use

- A restart command with a wait ends in a timeout and exit code 1.
- The gateway log shows `candidate rejected` and `reload rejected; active
  generation remains healthy`.
- You must apply a front-end change without a drain or a cold restart.

## Verified Workflow

### Quick Reference

```bash
# Real reason is in the gateway lifecycle log, not in the CLI timeout text:
grep -n "candidate rejected\|reload rejected\|phase=candidate" <gateway log>
# Handoff with workers: start the candidate without waiting, replay workers, then wait.
<admin> gateway restart --no-wait
<replay active workers to the candidate slot>      # same records, same labels
# done when the discovery record has a new started_at and the same allocation id
```

### Suggested Approach

1. Check the reload marker of the live job first. A job that lacks it cannot
   reload in place.
2. Start the candidate with a no-wait restart. Read the active slot and the
   candidate slot from the discovery record; the slot ports come from the
   deployment context.
3. Read the active service's worker list and post each record unchanged to the
   candidate service (the service answers 409 for a known identity). Do not
   rewrite labels: a worker must never look like it runs another release.
4. Poll the candidate worker list until it matches, then wait for the discovery
   record to change. Confirm the allocation id is unchanged.
5. Verify the front end with a status-only request and the model list. Expect
   the dashboard entries for the new generation about one minute later.
6. A restart that is rejected is safe: the active generation keeps serving.
   Read the lifecycle log and fix the cause before you retry.
7. Code of a separate long-lived process (a pool supervisor, a credential
   routine) is not necessarily reloaded by a front-end handoff. Check which
   processes start in the candidate before you rely on a reload for a patch.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Restart with a wait while workers were live | Ran the admin restart with its wait | The candidate had no workers, readiness timed out, and the CLI printed a timeout that named a release path | The cause is in the lifecycle log; read it first |
| Reload to load a supervisor patch | Reloaded the front end after patching the supervisor module | The handoff replaced the front runtime, not the pool supervisor process | Prove which process loads the changed code before you choose the reload |
| Judge the reload by the dashboard | Looked at the dashboard right after the handoff | The generation entries lagged about one minute | Verify with the discovery record and a status-only request |

## Results & Parameters

### Configuration

```yaml
slots: "blue = base port + stride, green = base port + 2 * stride (from the context)"
replay_window_s: 170
handoff_wait_s: 240
success: "new started_at in the discovery record, same allocation id, model list not empty"
```

### Expected Output

The candidate worker list equals the active list, the record changes, and the
retired generation drains empty and is reaped.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Production, 2026-10 | One worker replayed; the handoff completed in about one minute. |

## References

- [release-activation-with-live-old-release-outage](release-activation-with-live-old-release-outage.md) — why a live activation needs care
