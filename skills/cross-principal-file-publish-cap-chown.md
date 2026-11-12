---
name: cross-principal-file-publish-cap-chown
description: "A non-root service cannot publish a per-requester file by transferring ownership with fchown to the requester's uid: Linux grants an owner change to a different uid only to CAP_CHOWN holders, so every cross-principal publish fails with EPERM, and a test suite that derives both principals from its own effective uid turns the transfer into a self-chown and never observes the failure. Use when: (1) a publish step fails with a permission error only for requests owned by other accounts, (2) a protocol specifies requester-owned result files that the service writes, (3) you design a two-principal file handoff, or (4) the suite is green while the live path fails for foreign owners."
category: debugging
date: 2026-11-11
version: "1.0.0"
user-invocable: false
tags: [fchown, chown, eperm, capabilities, cap-chown, ownership, publish, requester, cross-principal, test-blindness, geteuid]
---

# Cross-Principal File Publish Needs CAP_CHOWN

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-11 |
| **Objective** | Publish result files on behalf of another principal without a root-only ownership transfer, and test the cross-principal path so it cannot silently pass. |
| **Outcome** | Successful — the failure class was measured on a live lane, the design defect was separated from a wrong first patch (which was reverted), and a design that needs no cross-uid chown was selected. |

A publish path that gives each result file to its requester with
`os.fchown(fd, requester_uid, gid)` requires a capability the service does
not hold. Linux allows a process to change a file's group to a group it
belongs to, but an owner change to a **different uid** needs `CAP_CHOWN`.
A service principal without that capability gets `EPERM` on every request
whose requester is not the service itself. The suite misses the class when
its fixtures derive both principals from `os.geteuid()`: the transfer
becomes a self-chown, which always succeeds.

## When to Use

- A publish or result step fails with a wrapped permission error, and only
  for requests whose owner differs from the service account.
- A protocol or docstring promises "requester-owned" files that the service
  writes.
- You are designing or reviewing a two-principal file handoff (result
  records, receipts, delivered secrets, drop-box replies).
- A permission-related suite passes while the live path fails for foreign
  owners.

## Verified Workflow

### Quick Reference

```bash
# 1. Confirm the failing call is the ownership transfer (wrapped error or strace).
strace -f -e trace=fchown,fchownat -p <service-pid>

# 2. Measure the capability boundary of the publishing process.
grep CapEff /proc/<service-pid>/status        # 0000000000000000 means no capabilities
python3 - <<'PY'
import os
fd = os.open("<results-dir>/probe", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=None)
try:
    os.fchown(fd, <foreign-uid>, -1)   # EPERM without CAP_CHOWN
except PermissionError as e:
    print("owner transfer:", e)
try:
    os.fchown(fd, -1, <own-auxiliary-gid>)   # succeeds: group change to an own group
except PermissionError as e:
    print("group transfer:", e)
PY
```

### Suggested Approach

1. **Separate the two predicates before patching.** Read the writer's
   transfer target and the reader's ownership requirement. A writer that
   chowns to the requester and a reader that compares against the same
   requester are *consistent* — and both require `CAP_CHOWN`. A writer and
   reader that name different principals disagree, and no one-line change
   fixes both. Patching one side while misreading the other breaks a
   guard test and must be reverted.
2. **Prefer a design that needs no cross-uid chown.** Two shapes keep the
   no-list directory boundary intact:
   - **Service-owned record keyed by the requester's id.** The service
     keeps ownership (transfer to itself is a no-op), the file mode stays
     `0600`, and the requester reads through a parent it can traverse but
     not list, by exact name. This changes who can read every record: any
     process at the service uid can. That is usually already true, but it
     is a trust decision to record.
   - **Mediated read.** The file stays service-owned and never leaves the
     service; the requester asks the service (status route, control
     socket) for the record. The trust boundary is unchanged.
   - Holding `CAP_CHOWN` in the publisher is the remaining option. It adds
     a privileged binary to the hot path; do not pick it by default.
3. **Test the cross-principal case explicitly.** A suite that runs as one
   uid cannot see this failure class. Give the fixture a requester uid
   distinct from the effective uid (`os.geteuid() + k`), or mock the
   ownership boundary, and assert the publish succeeds and the record
   reads back. When a suite *refuses* foreign requesters on another path,
   note that the success path for a foreign requester is still untested.
4. **Clean up failure side effects.** If the publish fails after a claim
   or lease is taken, release it on the failure path, or the stuck record
   blocks a retry of the same id and only the service uid can remove it.

Continue with the selected design without waiting for a capability grant;
a missing `CAP_CHOWN` is a design constraint, not a missing permission.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| One-line fix: transfer to the service uid instead | Claimed the reader already required the service owner, so the writer should match | The reader compared the file owner against its requester argument, and an existing guard test asserted foreign requesters are refused; the patch broke the guard and rested on a misreading | Read the writer and reader predicates, and the guard tests, before changing a trust boundary; revert the wrong patch and restate the diagnosis |
| Trust the green suite | The publish tests passed while every foreign-owner request failed live | Fixtures set both principals from the effective uid, so `fchown` was a self-chown that always succeeds; no test exercised a foreign requester succeeding | Derive the two principals from different uids (or mock the boundary) whenever a protocol transfers ownership |

## Results & Parameters

### Configuration

| Design option | Ownership transfer needed | Trust boundary | Notes |
| -------------- | ------------------------- | -------------- | ----- |
| Service-owned, keyed by requester id | Self-chown (no-op) | Widens read access to the service uid | Record the decision; keep `0600` and a no-list parent |
| Mediated read | None | Unchanged | Requester reads through the service; no direct file access |
| CAP_CHOWN publisher | Cross-uid chown | Adds a privileged step | Last resort; audit the binary |

Probe inputs: `<foreign-uid>` — any uid that is not the publishing
process's effective uid and not root; `<own-auxiliary-gid>` — a group the
process belongs to.

### Expected Output

- A publish path that succeeds for every requester without root.
- A test that fails on the defective design (cross-uid chown) and passes on
  the selected one, run as an unprivileged user.
- No stranded claims or leases after a publish failure.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A shared-cluster source lane | One fix cycle: result publication failed for every foreign-owner request; live probes measured `EPERM` on the owner change with `CapEff` zero, while the group change succeeded | Generalized evidence in [notes](./cross-principal-file-publish-cap-chown.notes.md) |

## References

- [publish-anchor-files-fully-configured](publish-anchor-files-fully-configured.md) — the publication sequence this failure sits inside (`fchown` before rename), and the reader-visibility rule.
- [directory-repair-leaf-only](directory-repair-leaf-only.md) — the ownership-and-mode normalization scope for service directories; the same "do not cross the boundary you validate" discipline.
