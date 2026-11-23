---
name: service-owner-uid-intake-rule-silent-quarantine
description: "A file-based intake that rejects request files owned by the service's own uid silently quarantines every request from a client that runs as the service account, and the client only reports a pending request. Use when: (1) a client command is accepted but no result ever comes and no error shows, (2) a quarantine directory gains an entry at each submit time, (3) only the service account fails while ordinary users work, (4) you must remove an owner-uid rule from one intake path, or (5) a request counter sums files by directory."
category: debugging
date: 2026-11-20
version: "1.0.0"
user-invocable: false
tags: [file-rendezvous, intake, quarantine, owner-uid, service-account, request-result, silent-failure, in-flight-counter, copy-per-path]
---

# Service Owner-UID Intake Rule Silently Quarantines Requests

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-20 |
| **Objective** | Find and remove an intake trust check that refuses the service's own uid, without a service-versus-user code path in the client. |
| **Outcome** | Successful. One rule, copied into several intake paths, was fixed in each path. |

A file-rendezvous service reads request files from a drop directory and writes result files
to a result directory. If the intake rejects a request file whose owner is the service uid
(an "owner is invalid" trust check), a client that runs as the service account is admitted
by nothing. The intake moves the request to a quarantine directory that the client cannot
read. The client sees no refusal. It prints "pending, no result" and exits.

## When to Use

- A client command is accepted, then no result ever arrives and no error shows.
- The quarantine directory gains one entry at the submit time of each failed request.
- Only the service account fails. Ordinary users work.
- You remove an owner-uid rule from one intake path. Other paths can hold a copy.
- A counter sums files by directory to limit in-flight requests.

## Verified Workflow

### Quick Reference

```bash
# 1. Reproduce as the service account, then as an ordinary user. Compare.
# 2. Check the quarantine directory for a new entry at the submit time.
ls -l --time=birth <quarantine-dir> | tail
# 3. Find every copy of the rule in all intake paths.
grep -rnE "owner|st_uid|getuid|geteuid" <intake-code-dir>
```

### Suggested Approach

1. **Classify the signature.** Request accepted, no result, no error, a quarantine entry at
   the submit time, and only the service account fails. This points to an owner-uid check
   and not to a stalled service.
2. **Remove the owner-uid special case.** Do not add a new mechanism. Request files and
   result files are usually separated already by directory and by canonical name. Location
   and type tell them apart. The owner uid does not need to.
3. **Keep the other checks.** Keep the result-side checks (service owner, group, mode), the
   mode, group, link-count, size, and name checks on requests, and the check that the
   payload uid equals the file owner.
4. **Search every intake path for the same rule.** A rule that one author copies into each
   path gets fixed one path at a time. Fix all paths in one change, or list each path
   that remains.
5. **Re-check each counter that sums files by directory.** After the owner rule is gone,
   a count of service-owned files charges the service-uid requester for every result.
   Count request records only.
6. **Design a client-visible refusal.** A silent quarantine is a defect. The service must
   write a refusal result that the client can read. This is a protocol change. Track it as
   a separate item.
7. **Keep one client code path.** A user-facing command has no service-versus-user branch.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Fix the owner rule in one intake path only. | The same rule was in other paths. Each path failed the same way later. | Search all intake paths for the rule before you close the defect. |
| 2 | Remove the owner rule and keep the in-flight counter unchanged. | The counter counted service-owned result files and charged the service-uid requester. | Count request records only. |

## Results & Parameters

### Expected Output

- A request from the service account produces a result, as for an ordinary user.
- The quarantine directory gains no entry for a valid request.
- The in-flight count does not rise when results exist.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private service | Three intake paths fixed after an earlier fix covered a fourth path. | Details withheld. |

## References

- [cross-principal-file-publish-cap-chown](cross-principal-file-publish-cap-chown.md)
- [shared-fs-group-directory-provisioning](shared-fs-group-directory-provisioning.md)
