---
name: shared-fs-group-directory-provisioning
description: "Provision the right shared-filesystem directory mode, and place user-owned entries below it correctly. Use when: (1) a team needs a shared drop area on a cluster or shared filesystem, (2) ownership or write failures occur for group members, (3) the service account must read files that another user wrote, (4) per-user entries share one parent with service-private records, (5) a declared path manifest or an inventory check must accept the new entries, or (6) you must size available capacity before team use."
category: tooling
date: 2026-10-21
version: "1.1.0"
user-invocable: false
tags: [posix, permissions, setgid, sticky, group, shared-storage, provisioning, umask, quota, per-user, path-manifest, identity-encapsulation]
---

# Shared-Filesystem Directory Provisioning

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-21 |
| **Objective** | Select the correct shared directory mode for one writer relationship, and give the consumer path to each user-owned entry. |
| **Outcome** | Operational. Mode `2775` served one team group. Mode `3733` served many users who write one parent that a service account reads. Mode `2750` served one user's entry that the service group reads. |

## When to Use

- Create a shared area for a team or service group on a shared filesystem.
- Group members report permission denied or wrong-group files in a shared area.
- A service account cannot read files that users write, or it reads a file that another user must not overwrite.
- Several users stage entries in one parent that also holds service-private records.
- A declared path manifest, attestation, or repair tool must accept the new entries.
- Answer a capacity question for a directory before large artifacts move in.

## Verified Workflow

### Quick Reference

Select the mode from the writer and reader relationship. Do not copy one mode to a different relationship:

| Writers | Reader | Parent mode | Entry mode | Purpose |
| --- | --- | --- | --- | --- |
| One team group | That group | `2775` (`2770` for team-only) | umask `002` | Group-writable team area |
| Many users | One service account | `3733` (setgid + sticky + write/execute) | `2750` or `750`, owner is the user | Per-user drop area |
| Any | Any | A mode that hides the parent | — | Isolation of one user's entries |

Verify each step:

```bash
getent group TEAM_GROUP        # the group exists
id -nG                         # the current user is a member
install -d -m 2775 PATH        # team area, or -m 3733 for a many-user parent
install -d -m 2750 PARENT/USER # one user's entry below a 3733 parent
ls -ld PATH PARENT/USER        # expect drwxrwsr-x, or drwxrws-wt, or drwxr-s---
```

### Suggested Approach

1. Decide the writer set first. One group that shares work needs `2775` with umask `002`. Many users who each own their files, and one service account that reads them, need a parent that is group-writable, group-executable, not group-readable, and sticky. Mode `3733` gives that parent.
2. Bind the group before a write. `getent group` shows the record. `id -nG` shows the current group list. If the user is not a member, request an administrator action. Do not work around the group.
3. Use setgid for inheritance. The setgid bit makes each new file and subdirectory inherit the parent group. The service account then reads user files without a per-user group. `chmod g+s` adds the bit to an existing directory. A recursive setgid repair applies to directories only, for example `find PATH -type d -exec chmod g+s {} +`.
4. Use the sticky bit when many users write one parent. The sticky bit lets a user remove or rename only its own entries. The service account cannot replace another user's entry. Add it together with setgid: mode `3733` shows as `drwx-ws-wt`.
5. Choose the entry mode from the reader. An entry that the service group must read takes `2750` (`drwxr-s---`), so other users get no traversal. An entry that only its owner uses takes `0750`. Do not use `0700`; the service account then cannot traverse it.
6. Check the identity of the reader against the mode. The sticky bit stops deletion, not reading. A parent that ordinary users can list reveals the names of other users' entries. Use group-write plus group-execute without group-read (`rwx-wx` style) when names must stay private.
7. Keep service-private records out of the shared parent. A private record directory below the same parent keeps mode `0700` and its own owner. Only the parent changes mode. Change the mode check that runs for the parent, not the one for the private records.
8. Update the declared path manifest and the inventory or attestation tool together with the mode. Use one component token for a user name in a glob-style manifest, not a pattern that also matches the private record names. A token that cannot overlap another pattern prevents an ambiguous-policy refusal. The token must also refuse a name that starts a segment with a dot, `.intake*`, or `../`.
9. Verify with `ls -ld` and with the tool that consumes the path. Expect `drwxrwsr-x` for `2775`, `drwxrws-wt` for `3733`, and `drwxr-s---` for `2750`.
10. For a capacity question, inspect the mount, not the directory. `df -h PATH` and `stat -f PATH` show mount capacity. A directory has no size limit of its own unless the filesystem enforces tree or user quotas.

Keep these failure modes in view:

- A default umask of `022` removes group write from new files and group execute from new directories. Members use umask `002` for shared work, or repair with `chmod g+w`. The setgid bit sets the group, not the mode.
- A copied tree does not always keep the setgid bit or the group. `cp -a` and `cp -p` keep modes. A plain `cp` uses the umask for the mode.
- Group changes do not reach existing sessions. Start a new session or run `newgrp TEAM_GROUP`.
- A mode check that demands `0700` and owner equality on the shared parent rejects every user-written parent. Update that check with the mode change.
- A path manifest that lists only service-owned names refuses the new user entries, and an ambiguous match stops the attestation. Change the manifest in the same change.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Setgid alone for many users | Used `2775` for a parent that many users and one service account share. | The group write lets one user delete or rename another user's entry. Group read also reveals the names of other users' entries. | Add the sticky bit for many writers. Use `3733` to hide the names without stopping the service account. |
| Entry mode `0700` | Gave each user a private entry below a group-writable parent. | The service account is not the entry owner, so it cannot traverse the entry, and every read fails. | Use group-execute for the reader: `2750` with the service group. |
| Manifest unchanged | Changed the directory mode but kept the manifest patterns for service-owned names only. | The attestation and repair path classified the new entries as unknown or ambiguous and refused the tree. | Update the manifest, the token, and the mode check in one change. |

## Results & Parameters

### Configuration

```yaml
team_area:
  mode: 0o2775            # 0o2770 for team-only access
  umask: 0o002
many_user_parent:
  mode: 0o3733            # setgid + sticky + write/execute
  entry_mode: 0o2750      # owner is the user, group is the service group
service_private_child:
  mode: 0o700
```

### Expected Output

- `ls -ld` reports `drwxrwsr-x` for the team area, `drwxrws-wt` for the many-user parent, and `drwxr-s---` for one user entry.
- New files and subdirectories inherit the parent group.
- A user cannot delete or rename another user's entry.
- The service account reads every user entry that uses the group-execute mode.
- The attestation or inventory tool accepts the new entries without an ambiguity error.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Anonymized shared-storage deployments | Team artifact directory provisioned with mode `2775`. Capacity question answered from the mount, which had no visible per-user quota tooling. | See [notes.md](shared-fs-group-directory-provisioning.notes.md). |
| Anonymized service deployment | Many-user staging parent changed to mode `3733`, with private record directories kept at mode `0700` and the path manifest updated in the same change. | See [notes.md](shared-fs-group-directory-provisioning.notes.md). |

## References

- [GNU coreutils: Directory Setuid and Setgid](https://www.gnu.org/software/coreutils/manual/html_node/Directory-Setuid-and-Setgid.html)
- [POSIX.1-2017: Sticky bit on directories](https://pubs.opengroup.org/onlinepubs/9699919799/)
- [Related skill](slurm-shared-storage-artifact-relocation.md) for moving large artifact trees into such a directory.