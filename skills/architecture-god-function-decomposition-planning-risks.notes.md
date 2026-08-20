# Notes: God-Function and God-Class Decomposition Planning Risks

Supporting evidence for
[`architecture-god-function-decomposition-planning-risks`](./architecture-god-function-decomposition-planning-risks.md).
The exact prior content is in
[history](./architecture-god-function-decomposition-planning-risks.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| ProjectHephaestus #1180 god-function plan | [immutable source at the #3335 base](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/architecture-god-function-decomposition-planning-risks.md) | unverified | Kept current-tree measurement, arithmetic, wiring, sentinel, and test-path rules |
| R1 line-cap corrections | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/architecture-god-function-decomposition-planning-risks.md) | unverified | Kept AST-span distinction and multi-helper arithmetic |
| ProjectHephaestus #1462 god-class plan | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/architecture-god-function-decomposition-planning-risks.md) | unverified | Kept patch seam, helper/collaborator, and dependency analysis |
| ProjectHephaestus #1464 circular-import review | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/architecture-god-function-decomposition-planning-risks.md) | unverified | Kept leaf relocation and explicit re-export pattern |

## Case Details

### Function-level planning

Issue-cited spans no longer matched the current source. Several proposed one-helper extractions could
not meet the line cap after counting retained signature, docstring, and call-site lines. Other plan
blocks defined helpers without invoking them. Poll-loop extraction also needed more than a Boolean:
continue, retry, completion, and abort states affected different caller control flow.

The source contained an empty-replies edge and a return-type change that planning prose initially
missed. These observations motivate explicit signal enumeration and source rereading, but they do
not verify a final implementation.

### Class-level planning

The oversized class had extensive tests patching private methods on an instance. Deleting moved
methods would break those seams even if the collaborator was otherwise correct, so the reviewed
plan retained thin delegation stubs. Some methods called many sibling helpers and were poor
collaborator boundaries; others formed more cohesive responsibilities. The canonical skill keeps
the coupling count as evidence rather than a hard numeric threshold.

### Circular-import review

A proposed collaborator needed a helper defined at module scope in the god module. Importing that
module from the collaborator introduced a cycle. The correction moved the helper to a leaf module,
imported the leaf from both sides, and re-exported under the original name for compatibility. The
review identified the design issue; no executed end-to-end extraction is claimed.

## Verification Boundary

All four cases are planning/review evidence. They establish failure modes and gates, not green
runtime behavior. Any implementation must re-measure its own base, run import smoke tests, exercise
every sentinel branch, preserve patch/subclass callers, and run the relevant full suite.

## Compaction Disposition

- Kept in main: every distinct trigger, AST metric, arithmetic rule, sentinel contract, seam rule,
  collaborator decision, cycle fix, and unverified status.
- Moved here: case-specific measurements, review sequence, and observed planning errors.
- Archived only: large replacement blocks, exact old line tables, and repeated checklists.
