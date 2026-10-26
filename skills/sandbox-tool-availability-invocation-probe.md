---
name: sandbox-tool-availability-invocation-probe
license: BSD-3-Clause
description: "Determine whether an execution capability is really available before you report that work is blocked. Use when a sandboxed code runtime rejects a tool as unknown, when name or property inspection contradicts that rejection, or when the sandbox catalog can differ from the tools the host harness exposes natively."
category: tooling
date: 2026-10-25
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [sandbox, runtime, tool-availability, invocation-probe, blocker-report, graceful-degradation, agent-harness, execution-capability]
---

# Probe Tool Availability by Invocation, Not by Inspection

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-25 |
| **Objective** | Report that an execution capability is unavailable only after an authoritative probe fails on every interface the host harness exposes. |
| **Outcome** | Operational. One blocked report was replaced by live delivery after a direct invocation outside the sandboxed runtime succeeded. Earlier name and property inspection had given false evidence in both directions: it reported unavailable names as present, and it could not see the native interface at all. |
| **Verification** | verified-local: each probe below ran in a live agent session; the failure and the recovery both occurred on the same host. See [notes](sandbox-tool-availability-invocation-probe.notes.md). |

## When to Use

- A sandboxed code runtime rejects a tool with an unknown-tool or not-registered error.
- You are about to report that work is blocked because execution appears unavailable.
- A name or property inspection (existence checks, a `typeof`-style probe, object introspection) of the runtime's proxy contradicts an earlier invocation failure.
- A session was restarted or relaunched, and the interface mix of the new turn can differ from the old turn.

## Verified Workflow

### Quick Reference

The authoritative probe is one invocation per interface:

```bash
# Inside the sandbox: invoke the tool once through the sandbox API.
# Outside the sandbox: invoke the same capability as a direct call of the host harness.
# Both results together decide the availability report.
echo <harmless-marker>    # a zero-side-effect invocation is enough
```

Rule: **invocation is registration.** A capability is available only where an invocation succeeds. A name that resolves, a property that exists, or an alias that inspects as callable proves nothing about the per-turn catalog.

### Suggested Approach

1. Do not trust inspection of a proxy. A sandboxed runtime can expose proxy objects in which every plausible name — a primary name and each guessed alias — inspects as present and callable, while every invocation through the proxy fails with an unknown-tool error. Inspection answers the question "does this name resolve", not "is this tool registered for this turn".
2. Probe each interface once. The sandbox catalog of a hosted agent is fixed for a turn, and it can omit tools that the host harness exposes as direct native calls. If a sandbox invocation fails, run the same zero-side-effect invocation through the native interface of the harness before you report anything.
3. Report blockers with interface precision. State each interface that you probed and its result: sandbox invocation failed, native invocation failed, or native invocation succeeded. "The tool is missing" is wrong when only one interface lacks it.
4. Do not loop probes. Retrying a failed invocation, or guessing more alias names, returns the same result from a fixed catalog and consumes turns. One invocation per interface per turn is conclusive; escalation is the answer to a confirmed failure, not repetition.
5. Deliver read-only work first. While every interface is unavailable, complete each review, inventory, and drafted command that does not depend on execution. A later unblock then costs one probe and one continuation.

Define completion by evidence: each interface probed once, the results recorded, and the availability conclusion stated per interface.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Reporting a hard blocker from sandbox evidence alone | Reported that execution was unavailable because the sandboxed runtime rejected the executor tool across several turns | The host harness exposed the same capability as a direct native call in a later turn; one direct invocation succeeded and the blocked work ran | A sandbox rejection describes the sandbox catalog only. Probe the native interface before you declare work blocked. |
| Verifying availability by name and property inspection | Enumerated the runtime's proxy for the executor name and each guessed alias; every name inspected as present | The inspection report was a false positive: each invocation through an inspected name still failed with the unknown-tool error | Inspection of a proxy is not evidence of registration. Only invocation is authoritative. |
| Repeated probing across turns | Retried invocation and alias probes after each failure, expecting the catalog to change | The per-turn catalog is fixed; each retry returned the same error and consumed session budget until a new turn offered a different interface | Probe once per interface per turn. Continue with read-only work or a blocker report instead of repeating the same probe. |

## Results & Parameters

### Configuration

The probe set that decides an availability report:

1. One zero-side-effect invocation through the sandbox API of the runtime.
2. One zero-side-effect invocation as a direct call of the host harness.
3. A record of both results before any report.

### Expected Output

- One of three conclusions, with the failed or successful interfaces named: available in the sandbox, available only through the native interface, or unavailable on every interface.
- A blocker report that states probe evidence instead of a bare "tool missing" claim.
- Read-only deliverables completed during unavailability, so a later unblock is a single continuation.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A hosted multi-session agent environment | A sandboxed code runtime rejected the shell executor while property inspection of its proxy reported every alias as callable; a direct harness-level invocation succeeded after a relaunch and unblocked signed commit, push, and pull-request work | [notes](../skills/sandbox-tool-availability-invocation-probe.notes.md) |

## References

- [Shared-repository interruption yield](shared-repo-interruption-yield-to-peer-pr.md) — probe live state before you decide between resuming and yielding; the same evidence-first rule applies to capability
