# Notes: directory-repair-leaf-only

Supporting detail for the main entry. Nothing here is required for operation.

## Incident evidence shape (generalized)

A production audit of a shared cluster root recorded:

1. The public root mode changed from the declared `0o2755` to `0o700` twice,
   hours apart, with the set-group-ID bit dropped. Deployed inputs were
   identical across both events. The path was an ancestor of a private core
   chain that an ensure-style helper created on startup of a non-production
   lane.
2. A `dev`/qualification chain appeared below the same public root at `0755`,
   created by a `mkdir(parents=True)`-style call at the caller umask across a
   missing boundary root.
3. A transition lock file appeared directly inside the public root: a
   protected mutation accepted a context whose deployment root was the public
   root itself (an ambient/fallback-derived context), and the guard never
   checked the lane boundary before its first effect.

Root-cause: the helper recursion ran the private normalization
(`fchown` + `fchmod 0700`) on every existing ancestor, and the publish path
fabricated missing boundary roots at umask modes. Both writer classes are
covered by the leaf-only rule even though the exact originating automation
for the earliest event stayed a bounded hypothesis.

## Verify pattern

For each harm shape, the regression test is a plain temporary-directory test:

- ancestor-preservation: create `root` at the declared public mode with
  setgid, call the helper for `root/<lane>/leaf`, assert the root mode and
  `(st_uid, st_gid)` are unchanged and the leaf is at `0o700`;
- refusal: place a regular file in the chain, assert `PermissionError` names
  the file and creates nothing below it;
- boundary: bind a deployment root equal to the public root, assert the guard
  refuses before the lock file exists and the message carries the lane name
  and the public root path;
- publish: point a publish call at a missing boundary root, assert a refusal
  that names the boundary ("cluster root"), and assert the boundary stays
  absent; a second arm asserts a created shared directory carries `0o2755`.

The tests run on local temporary directories only; no shared filesystem or
privileged identity is necessary for the behavior proof.
