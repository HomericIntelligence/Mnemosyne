---
name: daemon-request-loop-failure-visibility
license: BSD-3-Clause
description: "Make a daemon's per-request processing loop show why a request fails. Use when a background service admits requests but never answers them, when one failing request seems to block all later requests, when a pass summary never appears in the log, or when a bounded pass over a shared request dropbox shows a constant capacity-refusal count while other requesters hang, or when two live processors with different code versions serve one shared request queue."
category: debugging
date: 2026-10-29
version: "1.2.0"
user-invocable: false
verification: verified-local
tags: [daemon, request-loop, exception-handling, logging, timeout, result-slot, observability, privacy]
---

# Daemon Request Loop Failure Visibility

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Make every failure inside a periodic request-processing pass visible, bounded, and isolated per request, without leaking secrets into logs. |
| **Outcome** | Operational. One change set added a connect timeout, per-request containment, and a warning-level summary. It makes the hidden reason visible; it does not fix the root cause by itself. |

## When to Use

- A service accepts a request (a result slot or marker appears) but never writes a result, and the log is silent.
- One bad request seems to stop the rest of the queue, because an uncaught error ends the whole pass each cycle.
- The pass summary line never appears in the log. Check the log level before you decide that the pass does not run.
- An external connection (database, remote service) in the loop has no explicit timeout.
- A pass takes at most N requests from a shared dropbox, the capacity-refusal counter is constant, and requests from other requesters wait until the client times out.
- Two live processors poll the same request dropbox. A request leaves the queue, no result appears, and the other processor never saw it.

## Verified Workflow

### Quick Reference

```text
Per request:   catch Exception last; count it; log the exception TYPE NAME only; continue.
Never log:     exception text or traceback arguments (they can quote credentials or DSNs).
Summary line:  WARNING when any failure counter is non-zero; INFO only when all clean.
Connects:      pass an explicit bounded timeout to every external connect.
Admission:     create the result slot after the fallible connect, or clean it up on failure.
Do not catch:  BaseException (cancellation and shutdown must pass through).
Selection:     take up to N per requester in rotation; skip names that already have a result.
Refusal:       publish a typed refusal result, so the client returns at once.
Ownership:     one live processor per queue; fence the other before you patch one.
```

### Suggested Approach

1. Read the loop's `except` list. List every exception family that can leave the function. Any family that is not in the list ends the pass for all later requests. Add one final `except Exception` per request that counts and logs the type name, then continues.
2. Decide the log level from the operator's view. If the service logs at WARNING, an INFO summary is invisible. A missing INFO line is not evidence that the code did not run. See `debugging-absence-of-evidence-verify-with-authority`.
3. Add a bounded timeout to each external connect. A library default (often 60 s) multiplied by a queue of requests can stall the whole cycle. A timeout error is usually an I/O error subclass, so it joins the existing transient counter. Check this before you add a new branch.
4. Order side effects. If admission creates a durable result slot before a fallible connect, a failure leaves an empty slot that clients wait on. Create the slot after the connect, or remove or mark it on failure. If the order cannot change, state in the change that failures can still leave an empty slot.
5. Add one test for the contract: two queued requests, the first raises an unexpected error, the second still runs; the log shows the type name and the counter; the secret text in the exception is absent from the log.
6. Select fairly when each pass is bounded. Sorting names and taking the first N lets one requester's unanswered backlog fill the whole window. Rotate or round-robin across requesters, and skip names that already have a result. Diagnose it with the per-pass counters: a constant capacity-refusal count, and a per-owner count of records against records with a result, show one owner with a large unanswered backlog at the head of the sorted list.
7. Answer every refusal. A capacity refusal that publishes no result leaves the record in flight, so the backlog never drains. Publish a typed refusal result. Check that an older client prints any refusal code it does not know and exits.
8. For an urgent unblock, delete only the unanswered records of the over-capacity owner. Never delete result records or the records of other owners. The pass then runs at once, but the selection and refusal fix is the durable repair.
9. Expect noise. A warning for every non-progress counter can repeat each cycle when a counter stays non-zero. Accept it while the cause is unknown, then tune.
10. Serve the queue with one processor. When a second processor with different code runs on the same dropbox, each one admits some requests. A request file that is gone with an empty result slot was consumed by whichever processor admitted it, and only that processor can publish its result. Stop or fence the other processor before you patch one. A patch in a checkout is not live until the patched process restarts: check the process start time against the patch time before you conclude that a patch does not work.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read the missing summary line as proof of a dead loop | Treated the absence of an INFO line as evidence that the pass never completed. | The service logs at a higher level, so INFO lines never show. | Check the log level and look for any other INFO line before you reason from absence. |
| Rely on the existing `except` list | Assumed the listed families cover all failures. | A database-driver error is not an I/O error, so it escaped and ended the pass. | Add a final catch per request and log the type name. |
| Take the first N sorted names each pass | Relied on sorted order to bound the pass. | One requester's unanswered backlog filled the window every pass, and other requesters hung. | Select per requester in rotation. |
| Refuse at capacity without a result | Counted the refusal and moved on. | The record stayed in flight, and the backlog never drained. | Publish a typed refusal result. |
| Log the exception message for context | Considered printing the error text. | Connection errors can quote the DSN or credential file. | Log the type name only. |
| Patch one of two live processors | Patched a checkout and restarted one processor while a second processor with other code still polled the queue | The second processor admitted some requests and failed them, so the patch had no effect on those and the requester waited | One processor per queue; fence the other before the patch, and check the process start time after it |

## Results & Parameters

```yaml
per_request_catch: Exception            # not BaseException
log_on_failure: "request failed: <TypeName>"   # no text, no traceback arguments
summary_level: WARNING_if_any_nonzero_failure_counter
connect_timeout_s: 15                   # bounded; choose below the cycle interval
single_processor_per_queue: true        # fence the other before you patch one
```

Expected result: one failing request adds one counter and one warning line, and later requests still run in the same pass.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private service (identifiers withheld) | A credential-fulfillment loop that admitted requests and published no result | The change was reviewed and tested locally; production confirmation was pending at authoring time. |

## References

- Related: `preserve-primary-failure-diagnostics` (keep the primary failure when a probe also fails).
