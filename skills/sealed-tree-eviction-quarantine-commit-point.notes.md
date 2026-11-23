# Notes: sealed-tree-eviction-quarantine-commit-point

Privacy-safe supporting evidence for the main entry. No repository names,
hostnames, paths, issue identifiers, or customer identifiers.

## Source session

A development session implemented a disk-capacity eviction policy for a model
deployment control plane. Pulled model trees are sealed on purpose: files mode
0444, directories mode 0555. The implementation merged after review, with the
full related test set green locally (180 tests across five modules) and all
hosted checks green on the merge commit.

## Design decisions that carried the lesson

1. **Record placement.** The lifecycle record (pull time, deprecation
   timestamp, last-loaded timestamp, deletion stamp) lives in a sibling
   `.lifecycle/` directory beside the sealed trees, never inside them. A design
   review amendment moved it there after the first draft placed it inside the
   deletion target.
2. **Commit point.** `evict` performs exactly one `os.rename` of the sealed
   tree to `.evicting-<slug>-<4 hex bytes>` and then does chmod-unlock removal,
   cookbook cleanup, and image cleanup. Every removal helper treats
   `PermissionError` as "chmod and retry" and `FileNotFoundError` as success.
3. **Stale-quarantine reclaim.** The start of every eviction pass removes
   leftover `.evicting-*` directories, so a killed pass self-heals.
4. **Zero-state guard.** Candidacy requires all of: no replica entries, no
   donor entries, a status record whose live, pending-jobs, and desired counts
   are all zero (unreadable or non-dictionary means live), and a desired-state
   record that is absent or has zero replicas (unreadable or non-dictionary
   means live). The guard documents a one-pass race window between the guard
   read and the rename.
5. **Bounded name patterns.** Cookbook cleanup matches the exact
   `<slug>.yaml` plus a strict `<slug>-<8 lowercase hex>.yaml` revision
   pattern; a loose `<slug>-*` glob would also match unrelated names.
6. **Sufficiency belongs to the caller.** The eviction helper evicts ordered
   candidates (oldest last-loaded first, capped per pass) until a space probe
   passes or the list is done, and returns a count; the admission caller
   re-checks space and fails with its capacity error if needed.

## Test evidence (generalized)

Dedicated unit suites covered, among other cases:

- sealed-mode removal: a tree with 0444 files and 0555 directories is fully
  removed through the quarantine rename; no half tree remains under the live
  name;
- derived-output removal: the exact-name and revision-suffix artifacts are
  removed while a non-matching name survives;
- stale-quarantine cleanup: a pre-existing `.evicting-*` directory is removed
  by the next pass;
- live-state matrix: each live signal alone blocks eviction; junk and
  unreadable records count as live; a missing record means the artifact is
  never a candidate;
- end-to-end capacity path: a deprecated model is evicted before a fresh pull
  is accepted, and a pull with no evictable candidate fails with the capacity
  error while the stale artifact survives.

The suite ran green locally at the merge head, and the hosted CI ran the same
suites green across all shards before merge.

## Related review notes

- Review accepted the one-pass TOCTOU window with a docstring note; no second
  lock was added because the workload tolerates a deferred eviction.
- A follow-up review commit made artifact unlinking best-effort: an eviction
  that cannot finish cleanup still records the rename as the commit point.
