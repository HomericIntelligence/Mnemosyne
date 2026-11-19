---
name: client-response-id-mismatch-masks-size-limit-rejection
description: "Diagnose a client error that says the response id differs from the request id when only large requests fail. Use when a one-shot local request/response protocol fails for multi-document commands while single-document commands work."
category: debugging
date: 2026-11-18
version: "1.0.0"
user-invocable: false
tags:
  - request-response
  - request-id
  - size-limit
  - invalid-request
  - audit-log
  - client-error-masking
  - debugging
---

# A Response-ID Mismatch Can Hide a Request-Size Rejection

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Find the real cause when a client reports that the response id differs from the id it sent. |
| **Outcome** | Operational. Source reading and audit evidence agree on one cause: the server refused the request before it parsed it, so it answered with an id that it made itself. A live reproduction with a request above the limit was not run. |

## When to Use

- A client reports "response id differs from request id" and the same service answers other commands.
- Only commands that embed several documents or large inputs in one request fail. Commands with one input succeed.
- The same failure occurs for every account, so a permission fault is unlikely.
- The server audit has no line for the id that the client sent.

## Verified Workflow

### Quick Reference

```bash
# 1. Measure what the client sends, as compact JSON, and compare it with the server cap.
python3 -c 'import json,sys; print(len(json.dumps(json.load(open(sys.argv[1])),separators=(",",":")).encode()))' input.json
# 2. Look for audit lines with an empty action, empty arguments, a near-zero duration,
#    and an id that the client never sent.
grep -c "$CLIENT_REQUEST_ID" audit.jsonl   # expect 0 when the server never read the request
```

### Suggested Approach

1. **Read the mismatch as a symptom.** A server that rejects a request before it parses the body cannot echo the client id. It generates a new id. A client that compares ids first reports the mismatch and never shows the server error text.
2. **Find the pre-parse rejections.** Read the server code that runs before parsing: the byte cap, the newline framing rule, and the one-request-per-connection rule. Look for the cap constant and for the error code it returns.
3. **Measure the request.** Serialize the inputs the way the client does and add the envelope. If one input is under the cap and two or more are over it, the cap is the cause.
4. **Confirm in the audit.** Look for rejection lines that have no action, empty arguments, and the server-made id. The count of such lines should match the number of failed commands. The client ids are absent.
5. **Pick the repair by owner.** The client should treat the pre-parse rejection code like the authentication rejection code in its id check, so the real error shows. Separately, the owner can send large inputs by reference or raise the cap. Until then, run the single-input form of the command on each input and compare the results outside the service.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Account comparison | Ran the same command from a privileged and an unprivileged account | Both fail the same way; the cause is the request, not the caller | A failure that is identical for all callers is a protocol or size fault |
| Search by client id | Looked for the client id in the server audit | The server never read the request, so it never logged that id | Absence of the id is the evidence, not a gap |
| Trust from passing commands | Argued that the path works because single-input commands passed | Those requests were only a little under the cap | Compare each request size with the cap before you trust a pass |
| Retry | Repeated the failing command | The request size does not change on retry | Do not retry a deterministic size rejection |

## Results & Parameters

### Configuration

```yaml
evidence:
  server_cap_bytes: 16384        # per-request cap read from server source
  single_input_compact_bytes: 12000-14500   # fits with envelope margin
  two_input_compact_bytes: 24000-28500      # over the cap
  audit_signature: [empty action, empty arguments, phase rejected, code invalid_request, server-made id]
```

### Expected Output

- A verdict that names the cap, the measured request size, and the matching count of server-made ids in the audit.
- A repair note for the owner: id-check exemption, by-reference inputs, or a higher cap.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared-cluster inference deployment | Administrator command service on a local socket | Two-document compare command failed with an id mismatch; source cap and audit signature explained it. No live reproduction. |

## References

- [Prove liveness before you report an outage](prove-long-running-process-liveness.md)
