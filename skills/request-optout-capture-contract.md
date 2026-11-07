---
name: request-optout-capture-contract
license: BSD-3-Clause
description: "Design and document a client opt-out header that stops payload capture while metering, audit, and billing continue. Use when: (1) a gateway, proxy, or SDK stores raw request and response bodies by default, (2) users must be able to suppress stored content for a sensitive request, (3) an opt-out header needs strict values and a fail-closed rejection before any side effect, (4) the opt-out interacts with an unrelated header that has a similar name, or (5) one path such as a batch runner cannot send the header."
category: architecture
date: 2026-11-06
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - opt-out
  - privacy
  - request-header
  - capture
  - payload-storage
  - fail-closed
  - header-validation
  - metering
  - audit-ledger
  - batch
  - documentation
---

# Request Opt-Out Capture Contract

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-06 |
| **Objective** | Give a client one reliable header that stops storage of request and response content, and document the true limits of that header. |
| **Outcome** | A reference documentation page and a linked summary were added to a gateway service. The capture path already had the behavior. The change made the contract explicit: accepted values, two rejection rules, what capture stops, what continues, and the batch limitation. |
| **Verification** | verified-local. The documentation build passed in strict mode. The described behavior is covered by existing tests for the accepted values, the unknown value, the duplicate header, and the suppressed trace. |

## When to Use

- A service stores raw request and response bodies for diagnosis, and a user
  needs to suppress that storage for one request.
- A reviewer asks whether an opt-out header covers metering, logs, or audit.
- One client path, such as a batch queue runner, builds its own headers and
  cannot pass the user header.
- Two headers have similar names, for example one selects capacity and one
  selects capture.

## Verified Workflow

### Quick Reference

| Decision | Rule |
| ------- | ------ |
| Default state | Capture. An absent header stores content. |
| Set | `true`, `1`, `yes`. |
| Clear | `false`, `0`, `no`. |
| Normalization | Ignore letter case and outer whitespace only. |
| Unknown value | Refuse the request before any side effect, such as generation or metering. |
| Header sent more than one time | Refuse the request. |
| Forwarding | Remove the header before the request goes to the inner service. |
| Metering, billing, audit event | Continue. The audit event carries no content. |
| Internal client path with fixed headers | Document that it cannot opt out, or add the header to that path. |

### Suggested Approach

1. **Find the capture decision.** Locate the one function that reads the
   opt-out marker. Confirm the default when the header is absent. The safe
   default for a diagnostic trace is capture, because a missing header must
   not hide a fault.

2. **Make the parser strict and typed.** Accept only the listed truth values
   after the two normalizations of case and outer whitespace. Raise one typed
   error for every other input, including the empty value and whitespace only.
   The message must name the header and the accepted values. A silent
   fallback to capture is the defect this rule prevents.

3. **Reject before side effects.** Parse the header before generation, before
   metering, and before the trace directory exists. Check the request's
   complete header list, not one lookup, so a duplicate header is visible. A
   client library that merges default and per-call headers can send one
   `false` copy and one `true` copy. A single-value lookup hides that case.

4. **Keep the non-content records.** Do not suppress token counts, billing
   rows, or the access event. State in the documentation that the opt-out
   removes content, not the fact of the request. A user who expects full
   anonymity must not get it by accident.

5. **Strip before forwarding.** Put the header in the list of headers that the
   proxy removes. The inner service then has no path that acts on a user
   header.

6. **Check every path that reaches the inner service.** A queue or batch
   runner that sets its own headers usually passes a fixed set and drops the
   user header. Trace the user headers through that runner. If the runner
   cannot pass the header, document the limitation. Do not claim coverage that
   the runner does not have.

7. **Separate headers with similar intent.** A capacity or routing header
   that contains the word `private` selects a resource and does not change
   capture. Give each header its own sentence in the documentation, and show
   one example that sets both.

8. **Put the contract in one page.** Keep the reference in one owner page.
   Mark it with the lifecycle state and the owning record. Link it from the
   user guide, the documentation index, the site navigation, and the component
   page that owns the capture. Short summaries in other pages must link to the
   owner page and not repeat the value table.

9. **Verify.** Run the documentation build in strict mode. Confirm that each
   relative link resolves and that the anchor exists. Do not add a test that
   asserts prose. The behavior tests for the values and the rejections already
   exist in the code that owns the parser.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| One bullet in the user guide | Kept the whole contract as one item in a long "how it works" section | The bullet omitted the duplicate-header rule, the empty-value rule, the interaction with the similar capacity header, and the batch limitation | When a header changes data retention, give it its own page and link it from every entry point |
| Assume the batch path inherits user headers | Expected the queue runner to pass the opt-out header because the user set it | The runner builds a fixed header set from the job record, so the opt-out never reaches the proxy and the trace is stored | Trace the header through each client path before you document coverage |
| Relative link with the wrong depth | Used one parent step from a nested component page to the new top-level page | The strict build refused the broken target and stopped the build | Count the path depth against the built page tree, and let the strict build confirm it |

## Results & Parameters

### Configuration

```yaml
# Parser contract for the opt-out marker.
header: x-request-capture-optout
truthy: [true, "1", yes]
falsy: [false, "0", no]
normalize: [strip, lower]
on_unknown: reject_before_side_effects
on_duplicate: reject_before_side_effects
forward_to_inner_service: false
continues_on_optout: [metering, access_event_without_content]
```

### Expected Output

- A valid truthy value stores no request or response body and writes an access
  event with a private flag.
- An unknown value and a duplicate header each answer a rejection status with
  a message that names the header. No body is stored and no usage row is
  written.
- The inner service receives no copy of the header.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Gateway service with per-user diagnostic traces | Documentation change for an existing parser and capture path | The owner page, the user guide, and the component page now state the contract. The source detail is in [notes](request-optout-capture-contract.notes.md). |

## References

- [Document agent-provider data boundaries](documentation-agent-provider-data-boundaries.md)
- [Privacy policy code-grounded inventory guard](privacy-policy-code-grounded-inventory-guard.md)
- [CLI flag validation to prevent a silent no-op](cli-flag-validation-prevent-silent-noop.md)