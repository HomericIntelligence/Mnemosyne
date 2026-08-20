# Refactor Extraction Plan Unverified Assumptions — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Twelve-function repository-management cluster extraction with old-path re-exports | [ProjectHephaestus issue #1360](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1360) | `unverified`: plan produced, no implementation or tests | Retained patch lookup, line drift, frozen invariant, cycle, and lint review rules |
| Pipeline planning/review stage extraction against serialized dependencies | [ProjectHephaestus issue #1814](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1814) | `unverified`: plan and source reads only | Retained explicit assumed-symbol inventory and post-merge compatibility probe |
| Promote `_apply_state_label` into shared state vocabulary | [ProjectHephaestus issue #1814](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1814) | `unverified`: R0 NOGO and R1 revision, not implemented | Retained pure-return helper, import-surface, observable ordering, and exact-test applicability rules |
| Corpus compaction | [Mnemosyne issue #3335](https://github.com/HomericIntelligence/Mnemosyne/issues/3335) | Batch validation only; does not verify source refactors | Project-specific detail moved here; complete prior main remains only in history |

## Assumption ledger template

| Claim | Current evidence | Dependency/source | Implementation probe | Failure response |
| --- | --- | --- | --- | --- |
| Re-export preserves patch path | Whole-repository lookup inventory | Current base SHA | Identity and focused patch test | Retarget runtime lookup |
| Frozen count becomes N+1 | Executable invariant body | Current validator/test | Recompute authoritative inventory | Revise all coupled consumers |
| No import cycle | Proposed import graph | Landed modules | Import smoke and type/lint checks | Extract/reorient leaf |
| Dependency type/constructor exists | Epic or issue prose only | Unmerged issue | Read merged signature first | Revise plan |
| Existing test verifies promotion | Test name or family resemblance | Test source | Trace exact symbol execution | Add focused behavior test |

## Nuance retained

- `from old.module import symbol` creates an independent binding. Re-export identity alone does not
  make patches on `old.module.symbol` intercept it.
- A fully mocked method test constrains patchability and caller behavior, not the method's internal
  log wording or call order.
- A shared helper that returns transition data keeps vocabulary modules import-clean; executor
  callables pull I/O policy into the wrong layer.
- Boundary-test relevance is empirical: inspect actual importer sets and the test's configured root.
- “Copy then adapt” and “move” have different preservation semantics and must not be conflated.

## Evidence boundary

All source cases are planning artifacts. Repository reads verified selected current facts, not the
proposed extractions. The skill remains unverified until an implementation and CI evidence are
linked.
