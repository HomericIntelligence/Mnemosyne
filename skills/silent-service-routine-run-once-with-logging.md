---
name: silent-service-routine-run-once-with-logging
license: BSD-3-Clause
description: "Diagnose a service routine that fails silently by running the same routine once, outside the service, with exception logging. Use when: (1) a request is consumed and no result is written, (2) the service log shows no line for a routine that should run, (3) an earlier stage of a loop raises and the later stage never runs, (4) a peer concludes that a routine works or does not work from a missing log line."
category: debugging
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [silent-failure, swallowed-exceptions, log-level, reconcile-loop, run-once, read-only-probe, diagnosis]
---

# Diagnose a Silent Service Routine by Running It Once

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Find the hidden reason that a service routine does not complete, without guessing from a missing log line. |
| **Outcome** | Operational. Two separate silent faults hid a credential-fulfilment routine: an earlier stage aborted the loop before the routine ran, and the routine swallowed per-request failures. A single manual pass with exception logging named the reasons in one minute. |

A missing log line has three possible meanings: the routine did not run, it ran
and failed silently, or the log level hides its message. Treat the absence as no
evidence. Counters, result files and a controlled run give evidence.

## When to Use

- A queue entry leaves its directory and no result appears.
- The service log shows a generic line such as `could not reconcile state:
  <ExceptionType>` and nothing else.
- Two agents disagree because one reads a missing line as success and one as
  failure.

## Verified Workflow

### Quick Reference

```text
1. Read-only probes first: the database route (connect, one lookup), the queue, the result slots.
2. Check the log level: does any INFO line from that service appear? If not, INFO is hidden.
3. Run the routine once from a node with a working route, logging every exception type.
4. Compare: same routine, same input, different node => the fault is the node or the environment.
```

### Suggested Approach

1. Read the loop order. If a stage that runs earlier can raise, the later stage
   never runs. In the observed case the status-publication stage raised on an
   unknown pool and ended every pass before the credential stage.
2. List the exception classes that the routine catches. Any class outside the
   list escapes and ends the pass for all remaining requests. A class inside the
   list may increment a counter and log nothing.
3. Probe read-only: connect to the database through the same route, look up the
   requester, and list the queue and the result slots with sizes and times.
4. Build the service object the way its entry point does, call the routine once
   outside the service, and enable logging at INFO to the terminal. Print only
   exception types, request-name prefixes and bounded messages. Never print
   credentials or connection strings.
5. Read the counters. Each failure counter names a different cause class; the
   per-request lines name the reason.
6. Keep the local diagnostic patch as small as possible: one warning line per
   failure branch, no behavior change. File the main fix: log failures at a
   visible level, write a terminal error result, and bound every external call
   with a timeout.
7. Do not infer success from a side effect (a removed journal, an unchanged
   stored key). Check the final state that matters, for example the key id in the
   gateway's key snapshot.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read the missing INFO line as proof that the routine never ran | Grepped the service log for the pass summary | The service logs at WARNING; the summary is INFO | Check whether any INFO line appears before you draw a conclusion |
| Trust a peer's inference of success | Accepted that registration finished because a journal file was gone | The key id was absent from the key snapshot | Verify the end state, not a side effect |
| Wait for the service to show a reason | Re-ran the client and waited | The service admitted the request before its database step and swallowed the failure | Reproduce the routine outside the service |

## Results & Parameters

### Configuration

```yaml
probe: "connect + one lookup + queue listing + result-slot sizes"
manual_pass: "service object built as by its entry point; routine called once; INFO to terminal"
print_only: "exception type, request-name prefix, counters"
```

### Expected Output

A counters line such as `service_state=<n> transient=<n> progress=<n>` and one
warning line per refused request with its exception type.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Credential fulfilment, 2026-10 | One manual pass named three refusal reasons; the gateway-node path stayed unexplained until visibility was added. |

## References

- [silent-boundary-observability-exception-classification](silent-boundary-observability-exception-classification.md) — classify swallowed boundary exceptions
- [python-logging-and-silent-error-patterns](python-logging-and-silent-error-patterns.md) — logging patterns for silent errors
- [comet-user-credential-lifecycle-diagnosis](comet-user-credential-lifecycle-diagnosis.md) — credential lifecycle signatures
