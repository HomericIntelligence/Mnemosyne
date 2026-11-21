---
name: sealed-artifact-dir-owner-approved-add
description: "Add one large verified artifact to a shared directory of sealed artifacts whose mode is deliberately read-only. Use when: (1) a copy of a multi-gigabyte image into a mode 555 shared directory fails with permission denied, (2) you are tempted to chmod or work around the read-only mode."
category: tooling
date: 2026-11-18
version: "1.0.0"
user-invocable: false
tags: [shared-storage, permissions, read-only, sealed-artifacts, checksum, trap, scheduler, content-addressed]
---

# Add an Artifact to a Sealed Read-Only Shared Directory

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Place one verified build artifact in a shared directory of sealed artifacts without leaving the directory writable or the file half-copied. |
| **Outcome** | Operational. One owner-approved script copies, verifies, and re-seals in one run. |

## When to Use

- A verified image or filesystem artifact of tens of gigabytes must join a shared directory of sealed artifacts.
- The directory mode is `555`, so even the owner cannot create files, and the copy fails with permission denied.
- You consider `chmod`, a different target directory, or another workaround.

## Verified Workflow

### Quick Reference

The read-only mode is deliberate. Do not loosen it on your own. Ask the human owner first.
After approval, run one script as a scheduler job on a CPU node, not on the login node:

```bash
src_sum=$(sha256sum "$SRC" | cut -d' ' -f1)        # 1. record source checksum
orig_mode=$(stat -c %a "$DIR")
trap 'chmod "$orig_mode" "$DIR"' EXIT              # 4. restore mode, even on failure
chmod u+w "$DIR"                                   # 2. this directory only, no -R
tmp="$DIR/.tmp.$$.${NAME}"
cp "$SRC" "$tmp"                                   # 3. temporary name, same directory
final="$DIR/${NAME}-${src_sum}.img"
[ ! -e "$final" ] || { rm -f "$tmp"; exit 1; }     # 5. never overwrite
mv -n "$tmp" "$final"                              # 5. content-addressed final name
[ "$(sha256sum "$final" | cut -d' ' -f1)" = "$src_sum" ] || exit 1   # 6. compare
chmod --reference="$SIBLING" "$final"              # 7. same file mode as siblings
# 8. after the trap: stat -c %a "$DIR" equals $orig_mode; no .tmp.* file remains
```

### Suggested Approach

1. Stop at the permission error. Report it to the owner and ask for approval. Continue other independent work.
2. Put steps 1 through 8 in one script so no step is done by hand. Run it as a scheduler job on a CPU node.
3. Treat a failed source probe or a checksum mismatch as a stop: no copy at all, or remove the temporary file and do not publish the final name.
4. Group owner: a group different from the sibling artifacts is acceptable only if the file is world-readable.
5. Record the final path, size, and checksum on the tracking issue, not in the pull request under review.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Loosen the mode alone | Run `chmod` on the sealed directory without asking | The read-only mode protects sealed artifacts on purpose | Ask the owner first |
| Manual chmod, copy, chmod back | Three separate shell steps | A failed copy left the directory writable | Restore the mode with a trap |
| Recursive mode change | `chmod -R u+w` on the directory | Unseals every sibling artifact | Change only the one directory |
| Copy straight to the final name | Reader saw a partial file | A reader could use a half-written artifact | Copy to a temporary name, then rename |

## Results & Parameters

| Check | Expected |
| ------- | ---------- |
| Copy checksum | Equals the source checksum |
| Final name | Contains the checksum; no existing file overwritten |
| File mode | Same as sibling artifacts |
| Directory mode | Original mode (for example `555`) restored |
| Leftovers | No temporary file in the directory |
