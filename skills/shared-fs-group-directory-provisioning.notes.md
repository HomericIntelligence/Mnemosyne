# Notes: shared-fs-group-directory-provisioning

Supporting evidence for the main skill. Generalized; environment names removed.

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

## Reusable checks

```bash
df -h PATH      # human-readable total/used/available for the mount
stat -f PATH    # filesystem type, total/free blocks, inode counts
mount | grep PATH_MOUNT  # mount type and options (quota flags, etc.)
```

## Boundaries

- POSIX quota tools are meaningful only on filesystems that track quotas. A
  FUSE-backed share may not implement them; absence of output is not proof that
  a storage-side policy does not exist.
- Setgid covers group inheritance only. Mode inheritance follows each writer's
  umask.
