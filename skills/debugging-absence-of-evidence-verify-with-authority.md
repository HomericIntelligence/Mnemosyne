---
name: debugging-absence-of-evidence-verify-with-authority
license: BSD-3-Clause
description: "Do not conclude that an operation completed or failed from a missing log line, a missing file, or an unchanged value. Use when you are about to state a diagnosis in a shared thread from indirect artifacts, or when a teammate corrects an earlier inference."
category: debugging
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [diagnosis, inference, log-level, status-check, correction, shared-thread, read-only]
---

# Absence of Evidence Is Not Completion Proof

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Avoid publishing a wrong diagnosis that other lanes then build on. |
| **Outcome** | Operational. An inference from a removed journal file was wrong and was corrected within minutes by a status-only check. |

## When to Use

- A log line you expected is missing, and you want to say the code did not run.
- A state file disappeared (a journal, lock, or marker), and you want to say the operation finished.
- A stored value did not change, and you want to say nothing happened, or that a rotation succeeded.
- Several agents work on the same fault, and your post will steer them.

## Verified Workflow

### Quick Reference

```text
Missing log line  -> check the log level, and look for any other line of that level, first.
Missing file      -> find which code paths delete it (success path, restore path, manual script).
Unchanged value   -> ask the authority; do not infer from your local copy.
Authority check   -> one status-only call (HTTP code only; no body, no key in output).
Wrong earlier claim -> post a correction with the evidence, in the same thread.
```

### Suggested Approach

1. Mark each claim as observed or inferred. Write "inferred" in the post when it is an inference, and list what would prove it.
2. For a missing artifact, read the code paths that remove it. If more than one path removes it, the absence does not identify the path.
3. Ask the owner of the truth. For a credential, that is the service that accepts or rejects it. Use a status-only request and record the time and the code.
4. If the answer contradicts you, say so first and plainly, then give the new evidence. Tell others which workarounds to keep. Do not delete old copies or stop mitigations on an unproven claim.
5. State limits you could not check (an unreachable host, a log you may not read) so others know what remains open.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Journal gone, so registration done | Read a missing lifecycle journal plus an unchanged stored key as a completed registration. | Another script or a retry could also remove the journal. The service still rejected the key. | Verify with the authority. |
| No summary line, so the pass never ran | Read a missing INFO line as a dead loop. | The log level hid INFO lines. | Check the level first. |

## Results & Parameters

```text
Status-only check: send one authenticated request; record UTC time and HTTP code only.
200 = accepted; 401 = rejected; no connection = report as unverified, not as failure.
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private multi-agent debugging session (identifiers withheld) | A diagnosis from a removed journal was corrected by a status check and a teammate. | Correction posted in the same thread. |

## References

- Related: `daemon-request-loop-failure-visibility`, `debugging-diagnose-before-fixing-stale-blocker-claims`.
