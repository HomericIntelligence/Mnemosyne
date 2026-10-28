---
name: uv-lock-revision-downgrade-scratch-check
license: BSD-3-Clause
description: "Protect a pinned uv.lock revision from a silent downgrade. Use when a lockfile consistency check or locked sync rewrites the lock revision instead of only reading it, when the installed uv writes an older lock revision than the file pins, or when a lock diff must contain only the intended dependency change."
category: tooling
date: 2026-10-28
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - uv
  - uv-lock
  - lockfile
  - lock-revision
  - downgrade
  - version-skew
  - uv-lock-check
  - uv-sync
  - scratch-copy
  - minimal-diff
  - pyproject
---

# uv Lock Revision Downgrade from Read-Only Checks: Verify on a Scratch Copy

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-28 |
| **Objective** | Keep an intentionally pinned `uv.lock` schema revision byte-stable while adding one dependency and running the lock checks and locked sync that the workflow needs. |
| **Outcome** | `uv lock --check` is not side-effect-free when the installed uv writes an older lock revision than the file pins: after the pinned header was restored by hand, the check silently rewrote `revision = 5` to `revision = 3`. A plain `uv lock` regeneration rewrote the same revision and reformatted metadata. The working practice: add the dependency surgically to the manifest and the lock package table, restore the header line, prove the check on a scratch copy of the manifest and lock, then run the locked sync once in the real tree and inspect the header again. |

## When to Use

- The lock header pins a revision that is newer than the installed uv writes (header `revision = 5`, local uv writes `revision = 3`).
- `git diff uv.lock` gained a revision change with no dependency change after a check or sync.
- A review or repository policy needs a minimal lock diff with only the new dependency.
- You are about to trust `uv lock --check` as a read-only gate and need to confirm that for your uv version.

## Verified Workflow

1. Detect the skew before any command that resolves packages. Read the lock header and the tool version:

```bash
head -2 uv.lock          # version = 1 / revision = N
uv --version
```

2. Add the dependency surgically. Edit `pyproject.toml`, then add the matching `[[package]]` entry and its `requires-dist` line to `uv.lock` by hand. Do not run a plain `uv lock` regeneration when the diff must stay minimal (see Failed Attempts).

3. Restore the pinned header if a check or regeneration downgraded it. Change only the `revision` line. Leave the dependency entries in place.

4. Prove the check on a scratch copy, so the real tree cannot be mutated:

```bash
mkdir -p "$TMPDIR/lockcheck"
cp pyproject.toml uv.lock "$TMPDIR/lockcheck/"
cd "$TMPDIR/lockcheck"
uv lock --check          # exits 0 when consistent
head -2 uv.lock          # confirm the copy kept the pinned revision
```

If the copy's header changed, the command rewrites locks at this tool version. Do not run it in the real tree.

5. Sync the real environment once and re-inspect:

```bash
uv sync --locked --extra dev
grep -m1 '^revision' uv.lock     # still the pinned revision
git diff uv.lock                 # only the intended dependency lines
```

### Quick Reference

```bash
head -2 uv.lock                          # pinned revision
cp pyproject.toml uv.lock "$TMP/lockcheck/"
(cd "$TMP/lockcheck" && uv lock --check && head -2 uv.lock)
grep -m1 '^revision' uv.lock             # unchanged in the real tree
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| 1 | Regenerate the lock with plain `uv lock` to add one dependency | The resolver rewrote `revision = 5` to `revision = 3` and reformatted metadata; a one-line change became a lock-format migration | Hand-edit the manifest and the lock package table when the diff must stay minimal; leave the header untouched |
| 2 | Treat `uv lock --check` as read-only and run it in the real tree to confirm a hand-restored header | The check resolved packages and downgraded the revision again, in place; the rewrite surfaced only in a later diff review | A freshness gate is not side-effect-free under revision skew; prove it on a scratch copy first |

## Results & Parameters

- Skew signature: header `revision = 5`; installed uv writes `revision = 3` while resolving the same package set.
- Scratch-copy check: exit 0, "Resolved N packages", header unchanged on the copy. The real-tree sync is then safe to run.
- Real-tree sync: "Checked N packages" with no header change; the lock diff held only the new dependency entry and its `requires-dist` line.
- Restore operation: one header line (`revision = 5`); no other lock content changed.
- Verification: verified-local; the check and sync ran against a disposable copy and the real tree, and the header stayed pinned after both.
