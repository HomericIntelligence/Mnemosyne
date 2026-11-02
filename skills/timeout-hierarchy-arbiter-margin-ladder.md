---
name: timeout-hierarchy-arbiter-margin-ladder
description: "Size a multi-stage request-path timeout hierarchy around one total arbiter with a fixed guardian margin per hop. Use when: (1) chained stages (front door, proxy, router, runner) each bound the same request with their own timeout, (2) an outer stage can fire before an inner stage reports (inverted ladder) or at the same instant (tie), (3) a launcher never passes a knob so an image or library default applies invisibly, (4) a hardcoded outer literal matches a configurable inner default that deployments override."
category: architecture
date: 2026-11-02
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [timeout-hierarchy, arbiter-margin, inverted-ladder, guardian-timeout, image-default, request-path, serving-gateway, explicit-over-inherited]
---

# Timeout Hierarchy: One Arbiter Plus Margin Steps

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-02 |
| **Objective** | Keep exactly one total timeout budget per request path so the innermost stage reports each timeout, outer stages only outlive it, and every deployed value is visible in configuration. |
| **Outcome** | Successful. An inverted ladder (outer guardian below the inner total), a tie race between two equal values, and an invisible image default were all removed by deriving the hierarchy from one arbiter value plus a fixed per-hop margin. |
| **Verification** | verified-local — the failure shapes were reproduced against the deployed configuration; the fix passed the owning module test suite, renderer contract tests, type and lint gates, and a behavior review; production exercise pending. |

## When to Use

- Chained stages (public front door, proxy, router, batch runner, client) each apply their own timeout to one request.
- An outer stage can time out before an inner stage reports (inverted ladder) or at the same instant (tie), so the client sees a transport termination where the inner stage had its own terminal answer ready.
- One layer's timeout is idle-gap (caps a stall in a stream) while another's is total (caps the whole request), and the two semantics could be conflated.
- A launcher or renderer never passes a timeout flag, so behavior follows an image or library default that no review chose; failures cluster at exactly that default value with no configured source.
- A hardcoded outer literal was matched to an inner stage's default, while deployments can override that default.

## Verified Workflow

### Quick Reference

Pick one total arbiter (the innermost total budget `T`), then set the stage `n` hops above it to `T + n * M` with a margin `M` taken from existing platform evidence:

```text
router request total = T          # the only true arbiter
proxy read-idle      = T + 1*M    # idle-gap guardian
front guardians      = T + 2*M    # header wait and stream idle gap
runner read          = T + 3*M
client budgets       > T + 3*M    # documented requirement, not derived
```

### Suggested Approach

1. **Name exactly one total arbiter.** The innermost stage that bounds the whole request (for a serving chain, the router's request timeout) is the only arbiter. Every outer stage is a guardian: it must never terminate work that the arbiter would still serve. If a design names two total budgets for the same request, the design has two arbiters and neither report is deterministic.
2. **Pick the margin from platform evidence, not aesthetics.** Reuse a value the platform already trusts to cover propagation and teardown, such as an existing drain or handoff bound that equals budget-plus-margin. One margin per hop keeps the ladder inspectable: `stage(n) = T + n * M`. In the verified case, an existing drain default of `T + 60 s` supplied `M = 60 s`.
3. **Require strict inequalities; a tie races the arbiter.** An outer value equal to the inner total lets the outer stage win the race at the boundary, so clients see a transport termination exactly where the inner stage would have answered with its own diagnosable error. Only `outer > inner` by at least one margin makes the reporting stage deterministic.
4. **Match semantics per stage; do not equate total with idle-gap.** A read-idle timeout caps a stall inside a continuing stream; a request timeout caps the request end to end. An idle value at an outer stage is a wedge detector, not a second arbiter — size it above the inner total so the inner total always fires first on a dead request.
5. **Prefer explicit over inherited for every knob that can kill traffic.** If a launcher never passes a flag, the behavior is an image or library default that no review chose and no configuration diff shows. Decide the value the platform wants and render it explicitly, or record the inheritance as a deliberate, documented decision. Verify the flag exists in the pinned artifact (read its argument definitions or `--help` output) before you render it.
6. **Derive outer guardians from the configured arbiter value, never from its default.** A literal that matches today's default inverts the day a deployment overrides it. Read the context at stage startup, compute `T + n * M`, and wire the results through creation-time parameters with a test-override seam instead of monkeypatched module constants.
7. **Verify the reporting stage per layer.** Each timeout path answers which stage reported it (status code, telemetry counter, or log shape). Route-level tests must show the innermost stage answering first in healthy operation; outer margins must be unreachable during those runs.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Keep equal timeout values at two layers | Proxy and runner read timeouts equal to the router total (`7200 == 7200`) | At the boundary the outer stage races the arbiter; clients see a transport cut instead of the router's terminal answer | Only strict inequalities produce a deterministic reporting stage |
| Match a hardcoded outer literal to the inner default | A front guardian fixed at `600 s` because the proxy default was `600 s` | The deployment overrode the proxy to `7200 s`; the front silently became the arbiter and aborted two-hour requests at ten minutes | A default is not a contract; derive the outer value from the configured inner value |
| Leave a life-or-death knob to the image default | The launcher never passed the queue-wait flag, so the router image default (`60 s`) applied | Queued requests died at exactly the default with no configured cause; the failure was attributed to capacity for a long time | An inherited default is an unreviewed policy decision; render it explicitly or record the deliberate inheritance |

## Results & Parameters

### Configuration

```text
# Ladder parameters after the fix, one arbiter + margin steps:
arbiter_total_s:      7200   # router request timeout (context value)
guardian_margin_s:      60   # from the platform's existing drain precedent
proxy_read_idle_s:    7260   # arbiter + 1 margin
front_guardians_s:    7320   # arbiter + 2 margins, computed at startup
runner_read_s:        7380   # arbiter + 3 margins
queue_wait_s:           60   # rendered explicitly from config; no image inheritance
# derivation sketch at the outer stage:
front_guardians = float(context.arbiter.request_timeout_s) + 2 * guardian_margin_s
```

### Expected Output

- Telemetry or status codes attribute every timeout to the innermost stage; outer margins are never recorded as reached in healthy operation.
- Configuration diffs show the queue-wait value as a reviewed platform decision.
- Re-tuning the arbiter moves every derived guardian without code edits; only the context value and the margin constant change.
- Route-level tests pass with the same expectation: the innermost stage answers each timeout, and outer stages release resources on time through generation or cancellation paths.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A layered serving gateway platform | Request-path ladder rebuild: context-derived front guardians, explicit queue knob, per-hop margin from the drain precedent | [notes](../skills/timeout-hierarchy-arbiter-margin-ladder.notes.md) |

## References

- [Derive a Pin From Its Source of Truth, Not From a Literal](derive-pin-from-source-of-truth-not-hardcoded-literal.md) — adjacent rule for pins and versions; this entry extends it to configured timeout budgets.
- [Serialized-Identity Digest: Re-Admit or Exclude After Additive Fields](descriptor-digest-readmission-additive-fields.md) — when the explicit knob must leave existing identities unchanged.
