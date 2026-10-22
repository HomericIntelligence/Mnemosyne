---
name: shared-fs-group-directory-provisioning
description: "Provision a POSIX group-writable setgid directory on shared storage so each group member's new files keep the group. Use when: (1) a team needs a shared drop area on a cluster or shared filesystem, (2) ownership or write failures occur for group members, or (3) you must size available capacity before team use."
category: tooling
date: 2026-10-21
version: "1.0.0"
user-invocable: false
tags: [posix, permissions, setgid, group, shared-storage, provisioning, umask, quota]
---

# Shared-Filesystem Group Directory Provisioning

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-21 |
| **Objective** | Create one directory on shared storage where every member of a team group can write, and new entries inherit that group without a later manual fix. |
| **Outcome** | Successful. One directory with mode `2775` owned by the team group served every group member, verified with `ls -ld` and a capacity check on the containing mount. |

## When to Use

List the conditions in which to use this skill:

- Create a shared area for a team or service group on a cluster or shared filesystem.
- Group members report permission-denied or wrong-group files in a shared area.
- Answer a capacity question for a directory before large team artifacts move in.

## Verified Workflow

### Quick Reference

Verify the group and membership first, then set ownership and the setgid group-writable mode, then verify the result:

```bash
getent group TEAM_GROUP        # group exists; who are the members
id -nG                         # current user is a member, or use an admin path
mkdir -p PATH
chgrp TEAM_GROUP PATH
chmod 2775 PATH                # 2 = setgid: new entries inherit TEAM_GROUP
ls -ld PATH                    # expect drwxrwsr-x ... TEAM_GROUP
df -h PATH                     # capacity: a directory has no separate quota by default
```

### Suggested Approach

1. Bind the group before a write. `getent group` shows the group record and its
   member list. `id -nG` shows the active group list for the current user. If
   the user is not a member, `chgrp` fails; request group addition or an
   administrator action instead of a permission workaround.
2. Use mode `2775` (or `2770` for team-only access). The setgid bit makes each
   new file and subdirectory inherit the directory group. `chmod g+s` adds the
   same bit to an existing directory. A recursive setgid repair is only useful
   on directories, for example `find PATH -type d -exec chmod g+s {} +`.
3. Verify with `ls -ld`. Expect `drwxrwsr-x` with the team group name.
4. For a capacity question, inspect the mount, not the directory. A directory
   has no size limit of its own except when the filesystem enforces per-tree or
   per-user quotas. `df -h PATH` and `stat -f PATH` show the mount capacity.
   When quota tools are absent or unsupported by the mount type (for example a
   virtiofs share), the effective capacity is the free space of the mount, and
   a hard limit needs storage-side policy, not a client change.

Keep these failure modes in view:

- A member's default umask of `022` removes group-write permission on new
  files. Members use umask `002` for shared work, or they repair with
  `chmod g+w`. The setgid bit controls the group, not the mode.
- A copied tree does not always keep the setgid bit or the group. `cp -a` or
  `cp -p` keeps modes; a plain `cp` follows the bits of the new parent for
  ownership but uses the umask for the mode.
- Group changes do not reach existing sessions. A user must start a new
  session, or run `newgrp TEAM_GROUP`, before a new membership applies.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | The direct approach was successful. | N/A | No change was necessary. No POSIX quota tools (`quota`, `repquota`) were available on the share type in use; this absence is normal for some mount types and changes how capacity questions must be answered. |

## Results & Parameters

### Configuration

- Mode `2775`: team group can write, world can read. Use `2770` for team-only.
- Umask `002` for users who keep shared work group-writable.

### Expected Output

- `ls -ld PATH` reports `drwxrwsr-x <owner> TEAM_GROUP`.
- New files and subdirectories under `PATH` report group `TEAM_GROUP`.
- `df -h PATH` reports the mount total, used, and available capacity.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Cluster shared-storage share | Provisioned a team model-artifact directory for a POSIX group; capacity question answered from the mount, which had no visible per-user quota tooling. | See [notes.md](../skills/shared-fs-group-directory-provisioning.notes.md). |

## References

- [GNU coreutils: Directory Setuid and Setgid](https://www.gnu.org/software/coreutils/manual/html_node/Directory-Setuid-and-Setgid.html)
- [Related skill](slurm-shared-storage-artifact-relocation.md) for moving large artifact trees into such a directory.
