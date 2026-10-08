# Notes: changed-path-gate-deletion-classification

Supporting evidence for the main skill. Generalized and privacy-safe.

## Measured case (generalized)

A pull request removed a CI policy module, its declaration file, and all related
plumbing. The same change also removed the module's path from the deployment-input
inventory's exclude list, on the theory that a nonexistent file needs no exclusion.

- Local verification had covered the changed workflows, the checker CLI on
  hand-picked surviving paths, the test modules, and static checks. All green.
- The first hosted run failed in the classification job:
  `production input is unclassified: <deleted module path>`.
- Root cause: the gate classifies the complete change set of the pull request.
  The change set contains `D <module path>`. With the exclude row removed, no
  rule covered that path, and the gate fails closed.
- Fix: restore the exclude row. The inventory file became byte-identical to the
  base (net-zero diff), so it also left the pull request's changed-path list.
- Re-verification: the full 12-path diff including both deletions classified
  cleanly with every contract validator selected; the hosted gate passed on the
  next run; the merge landed.

Also on this change: a base-update rebase intersected the gated area on both
sides (the target branch had refreshed gate data for the removed mechanism; the
task branch removed the mechanism). Deletions won for removed machinery;
surviving routing rows from the target side were merged, confirmed by a full-set
smoke on the post-rebase diff.

## Generalization boundary

The rule applies to any fail-closed membership gate over a change set:

- deployment-input or production-candidate inventories;
- ownership gates (`CODEOWNERS`-style) that require every changed path to have an owner;
- coverage or test-selection gates keyed on changed paths.

The parameters change per gate (input format, row meaning, verdict vocabulary),
but the decision does not: keep the deleted path classified, and smoke the gate
on the exact complete change set, including deletions.

## Verification evidence retained in session records

Exact commands, run identifiers, and before/after failure sets are retained in
the delivery records of the change (pull request body and its review carriers),
not copied here.
