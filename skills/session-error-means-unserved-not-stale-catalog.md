---
name: session-error-means-unserved-not-stale-catalog
description: "Diagnose a session or job that reports its provider model as unavailable when another session uses the same model list correctly. Use when: (1) one session or job fails with a model-unavailable or no-route error while a sibling works, (2) the reporter says both sessions have the same model list, (3) the provider catalog lists an entry that the serving endpoint refuses, (4) an entry is published with a switch turned off because its backend has no live replicas, or (5) a member list appears truncated to a smaller count than the published set."
category: debugging
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - model-availability
  - unserved-model
  - catalog-visibility
  - session-pinning
  - disabled-entry
  - live-replicas
  - provider-error
  - diagnosis
---

# A Session Error Means an Unserved Entry, Not a Stale Catalog

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Find why one session reports its provider model as unavailable while another session with the same model record works. |
| **Outcome** | Successful. The published catalog was correct. The failing session named an entry that had no live replicas, so the host had hidden it. The repair moved the session to a served entry. |

## When to Use

- One session or job fails with a model-unavailable, no-route, or not-in-the-serving-set error, while a sibling session uses the same provider without error.
- The reporter says both sessions use the same model list, so the catalog looks like the shared fault.
- The provider catalog lists an entry that the serving endpoint refuses.
- A publisher sets a selectable switch to off for an entry whose backend has no live replicas.
- A member list shows fewer entries than the publisher emits.

## Verified Workflow

### Quick Reference

```bash
# 1. Read the session's own stored model. It is the ground truth.
#    Compare the failing session record against a working session record.

# 2. Read the publisher's output directly. Do not judge it by the member list.
#    Run the publisher module and print every entry it registers, with its switch.

# 3. Compare three sources: published entries, served ids, live counts.
#    served ids come from the serving endpoint; live counts from the status record.
```

### Suggested Approach

1. Read the failing session's stored model record. Treat it as ground truth for what
   that session will request. Do not infer it from a title, a transcript, or the
   current session.
2. Compare it with a session that works. Identical records rule out a per-session
   configuration fault. A different entry is the first cause candidate.
3. Read the publisher output directly. Run the publisher and print each entry with
   its visibility switch and state. A large published set that reaches the host as
   a small set is not a truncation bug. The host removes entries that the publisher
   marked not selectable.
4. Confirm the state independently. Send one minimal request to each suspect entry
   through the serving endpoint. A refusal that names the serving set proves the
   entry is not served. Do not trust only the status record or the catalog list.
5. Separate the three states before you name a cause:
   - **declared**: the release inventory names it;
   - **published**: the catalog lists it;
   - **served**: the endpoint accepts it now.
   Only *served* can accept a request. A gap between published and served is
   normal when a backend is down.
6. Repair the session, not the catalog. Point the session at an entry that is
   served. Do not force a not-selectable entry to appear. If the publisher hid it
   because no backend is live, making it selectable again only moves the failure.
7. Verify by one real turn. Read the session outcome and require a succeeded
   state. A stored model change alone does not prove recovery.
8. Report the three states to the reporter. The common premise, that both sessions
   share a model list, is usually true and not the fault. The fault is the selected
   entry.

**Distinguish this from the opposite case.** Another entry in this corpus teaches
how to keep a degraded entry selectable when the host hides it by state word. Apply
that entry only when the backend *is* served and the user must still reach it. When
the entry has no live backend, hiding it is correct and the fix belongs to the
session. Decide from the serving probe, not from the word shown in the list.

**Selection endpoints can accept an unserved entry.** Some hosts validate a model
change against a different set than the one that hides the entry. The change is
accepted and the failure appears on the next turn. When a repair path includes a
selection command, confirm the stored value, then confirm one real turn.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ---------- | ---------------- | --------------- | ---------------- |
| Blame the catalog | Started from the premise that both sessions shared one model list, so the list was stale or broken | The catalog was current and the publisher emitted every entry. The failing session named an entry with zero live backends | Read the session's stored model first; a shared list is not a shared fault |
| Treat the short list as truncation | Counted the member list, saw fewer entries than the publisher emitted, and suspected a host cap | The host returned only selectable entries. The publisher had switched the others off because their backends were down | Run the publisher and count what it registers before you suspect a cap |
| Repair by forcing the entry visible | Planned to turn the switch on for the failing entry | Serving the entry needs a live backend, which did not exist. The entry would fail on the first request again | Fix the session for an unserved entry; force visibility only for a served one |
| Trust the status record alone | Read the published status counts and stopped | The record is a publication, not an admission test. One direct request per suspect entry gives decisive proof | Probe the serving endpoint; use the status record to explain the count |
| Change the stored model and stop | Wrote the new model to the session and assumed recovery | The selection endpoint accepted the value. A failed turn state from before the change still read as failure | Require one succeeded turn before you report a repair |
| Mutating test on the real session | Sent a down entry to the live selection endpoint to confirm the mechanism | The endpoint accepted it and the session then failed one turn before the repair | Use a scratch session for this probe, or expect to restore and re-verify |

## Results & Parameters

### Configuration

```yaml
diagnosis:
  session_record: stored provider and model id     # ground truth
  sibling_record: a session that works             # control
  publisher: run it and print entries with switch  # what is offered
  serving_probe: one minimal request per entry     # what is served now
  status_record: live counts per entry             # why a switch is off
states:
  declared: in release inventory
  published: in catalog list
  served: accepted by the serving endpoint now
repair:
  unserved_entry: point the session at a served entry
  served_but_hidden: see the visibility-gate rule instead
  completion: one succeeded turn after the change
```

### Expected Output

- The failing and working sessions differ only in the stored model entry.
- The publisher emits the full declared set, with a switch off for each entry that has no live backend.
- The member list holds only the served entries, so the count matches the live count.
- A direct request to a hidden entry is refused and names the serving set.
- After the repair, the session reports a succeeded turn.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Self-hosted model gateway and its agent-host provider extension | One session reported its model as unavailable while a sibling session used the same provider. The catalog held 14 declared entries, 2 served, and the failing session named one of the 12 unserved ones | [notes](session-error-means-unserved-not-stale-catalog.notes.md) |

## References

- [extension-visibility-field-must-be-the-gating-field](extension-visibility-field-must-be-the-gating-field.md) — the opposite branch: keep a *served* but degraded entry selectable.
- [automation-loop-random-model-pool-operation](automation-loop-random-model-pool-operation.md) — a catalog status value is neither liveness nor an exclusion order.