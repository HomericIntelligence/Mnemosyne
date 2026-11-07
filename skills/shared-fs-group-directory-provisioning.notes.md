# Notes: shared-fs-group-directory-provisioning

Supporting evidence for the main skill. Generalized; product, environment, and account names removed.

## Session evidence (2026-10-21)

Trigger: provision a shared team directory for model artifacts on a multi-petabyte
shared cluster share.

Commands and observations (names generalized):

- `id -nG` showed the current user already in the team group.
- `getent group TEAM_GROUP` showed the team group record with member list.
- `mkdir -p PATH && chgrp TEAM_GROUP PATH && chmod 2775 PATH` succeeded.
- `ls -ld PATH` reported `drwxrwsr-x` owned by the team group.
- Capacity question: `df -h` on the mount reported a multi-PB total with a few
  hundred TB available. `quota -s` printed nothing and `repquota` was not
  installed. `stat -f PATH` reported the mount type as a FUSE/virtiofs share.
  Conclusion: the directory has no separate capacity; a per-tree limit requires
  storage-side enforcement.

## Session evidence (planning, 2026-11)

Trigger: an owner decision required a derived per-user source root below the
administrative root, so several users stage inputs in one parent that also holds
private service records.

- The parent already held private record directories with mode `0700` owned by
  the service account. The mode check for the parent demanded `0700` and owner
  equality, so every user-written parent would fail the same check.
- An established pattern in the same product used mode `3733` for
  many-writer parents that one service account reads.
- The declared path manifest needed a user-name token. The candidate token had
  to exclude the private record prefix and the dot-prefixed temporary names,
  because the matcher refuses two patterns that match one path.
- The entry mode below the shared parent was chosen as `2750` (setgid, group
  execute) so the service group reads the entry and other users get no
  traversal.
- Status: plan only. No implementation or test run produced the permissions
  evidence for this branch.

## Reusable checks

```bash
df -h PATH      # human-readable total/used/available for the mount
stat -f PATH    # filesystem type, total/free blocks, inode counts
ls -ld PATH     # mode, owner, group of the directory
stat -c '%a %U %G %n' PATH  # exact octal mode for a mode check
```

## Boundaries

- POSIX quota tools are meaningful only on filesystems that track quotas. A
  FUSE-backed share may not implement them. Absence of output is not proof that
  a storage-side policy does not exist.
- Setgid covers group inheritance only. Mode inheritance follows each writer's
  umask.
- The sticky bit stops deletion and rename by other users. It does not stop
  reading. Directory read permission controls name visibility.
- The many-user parent evidence is from planning against an existing mode check
  and manifest validator. Confirm the modes on the target filesystem before you
  rely on them.