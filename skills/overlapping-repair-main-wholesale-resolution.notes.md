# Notes: overlapping-repair-main-wholesale-resolution

Supporting evidence for
[overlapping-repair-main-wholesale-resolution](./overlapping-repair-main-wholesale-resolution.md).
Identifiers are generalized; mechanisms, measurements, and decision branches
are complete.

## Case

A worker branch lived across seventeen main commits during multiple forced
interruptions. At reconciliation, a trial merge (`git merge-tree
--write-tree`) cataloged exactly two content conflicts and one clean
auto-merge of a generated block. The three cases below are the decision
branches the workflow encodes.

### Case 1 — content-identical overlap (keep one side + the better comment)

The branch had changed a fixture to `parent.mkdir(parents=True, exist_ok=True)`
with a comment naming the root cause (a pool-independent release identity).
Main landed the identical one-liner, without the comment, one day later.
Resolution: content-identical; keep the comment because it carries the
invariant. Either mechanism is equally correct; the deciding input was the
rationale text.

### Case 2 — divergent repair of the same defect class (main wholesale + additive port)

A cluster-identity change made release identifiers pool-independent. The
branch repaired eight broken fixtures by differentiating one input
(control-revision helper) and added an explicit pin that a pool-only contract
edit now reports drift reason `context_changed`. Main repaired the same
eight fixtures by differentiating a different input (a surrogate image
identifier) and pinned only `release_changed`, never `context_changed`.
Resolution:

- Take main's file wholesale. Main owns the invariant; a double repair would
  encode two different identity mechanisms in one fixture set and mask
  future regressions in either.
- Enumerate branch-unique additions from the branch history of the file. One
  pin (`context_changed` for a pool-only contract edit) expresses behavior
  main's repair leaves uncovered; it was re-applied as a new, separately
  named additive test placed beside main's same-family test, not merged into
  it.
- Drop the branch's redundant `release_changed` coverage; main's version
  already covers the same mechanism through a genuine release change.
- Verification: the module ran green at the merged tree.

### Case 3 — generated artifact auto-merged clean (semantic equality proof)

A generated CLI contract block had been regenerated on the branch and
separately blessed on main; the textual three-way merge produced no
conflict. Correctness proof, not inspection: the repository's own generator
was run at the merged tree and both blocks were compared as parsed data
(literal evaluation), which returned equality. A text comparison fails this
check even for an identical artifact, because the formatter normalizes quote
style and wrapping between generation and commit.

## Decision branches the case adds

1. **Classify before resolving.** Identical overlap, divergent repair
   overlap, and unrelated overlap take different resolutions; the trial
   merge catalog plus per-file history decides which.
2. **Wholesale, not union, for divergent repairs.** Main's mechanism wins by
   ownership; the branch survives only through ported unique coverage with
   new names.
3. **Additive porting avoids the next conflict.** Re-applied coverage gets a
   new test name beside main's same-family test; folding it into main's test
   guarantees the same conflict at the next sync.
4. **Derived artifacts need a semantic gate.** Clean auto-merge text is not
   correctness; regeneration plus structural equality is the minimum proof.

## Provenance

- Source session: an implementation-review cycle on an internal pull request
  reconciled against a fast-moving main, 2026-10-27. Behavior verification at
  the merged tree: three background suites, 185 + 980 + 888 tests passed.
- Privacy review: repository, pull-request, issue, and commit identifiers are
  omitted; mechanism descriptions and counts are kept because they carry the
  decision value.
