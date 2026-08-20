# Notes: Check If Work Already Shipped Before Planning

Supporting evidence for
[`planning-check-already-shipped-before-planning`](./planning-check-already-shipped-before-planning.md).
The exact prior skill is archived in
[history](./planning-check-already-shipped-before-planning.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Merged fix discovered before replanning (issue #1291 / PR #1308) | [immutable source at the #3335 base](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-ci | Kept merged-PR and main-content verification rule |
| Uncommitted sibling-worktree implementation (issue #1357) | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-local | Kept worktree inventory and subset-versus-full-gate boundary |
| Large extraction already delivered under another ADR | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-local | Kept destination/source/residual/build acceptance mapping; cross-repo CI remained unverified |
| Retrospective plan rejected | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-local | Kept forward-looking closeout requirement |
| Placeholder plan while tests ran | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-local | Kept complete-at-handoff artifact rule |
| False “foreign WIP” provenance claim | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-local | Kept independent source/wiring provenance commands |

## Case Details

### Merged and worktree-only implementations

The merged-fix case used issue/PR search, main-branch source inspection, and tests to avoid duplicate
implementation. A separate case showed why this is insufficient by itself: the requested behavior
already existed in an uncommitted sibling worktree, so ordinary `git log` on main showed nothing.
The durable sequence is repository sync, worktree/status inventory, symbol search, and then tests.

### Extraction epic already delivered

The case checked target source presence, source-repository directory absence, residual symbol hits,
and build/test labels. The issue's earlier LOC estimate did not match landed counts. Some paths were
feature-guarded and sibling-repository claims rested on a local checkout rather than hosted CI.
Those boundaries are why the canonical skill requires criterion-by-criterion evidence and does not
promote a local sibling build to cross-repository CI proof.

### Plan-review failures

One artifact accurately described shipped work but contained no future actors or gates, so it was a
status report rather than an implementation plan. A subsequent artifact withheld content while a
background process ran, making the delivered plan effectively empty. The correction is to emit the
complete known plan and label a pending command honestly.

In the provenance case, three test failures were called foreign because the `.cpp` files were
untracked. The current worktree's `CMakeLists.txt` was modified to wire them into the build, so the
premise was false even if the final scope decision could still be defensible. Source provenance and
build-wiring provenance must be checked separately.

## Compaction Disposition

- Kept in main: cheap premise checks, immutable-base evidence, worktree discovery, acceptance
  mapping, provenance, closeout planning, cross-repo separation, and count consistency.
- Moved here: case sequence, old counts, review outcomes, and evidence limitations.
- Archived only: full transcripts, path inventories, and superseded wording.
