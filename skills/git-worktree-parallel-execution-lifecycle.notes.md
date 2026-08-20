# Git Worktree Parallel Execution Lifecycle Notes

Supporting case evidence for
[`git-worktree-parallel-execution-lifecycle.md`](git-worktree-parallel-execution-lifecycle.md).
The byte-exact prior main is archived once in the history companion and is not duplicated here.

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Split one issue across isolated owners | ProjectScylla [issue #1887](https://github.com/HomericIntelligence/Scylla/issues/1887), [PR #1932](https://github.com/HomericIntelligence/Scylla/pull/1932), and [PR #1933](https://github.com/HomericIntelligence/Scylla/pull/1933) | verified-ci | Successful split with explicit ownership |
| Remote branch collision and partial contamination | ProjectAgamemnon [PR #386](https://github.com/HomericIntelligence/Agamemnon/pull/386), [PR #398](https://github.com/HomericIntelligence/Agamemnon/pull/398), and [PR #401](https://github.com/HomericIntelligence/Agamemnon/pull/401) | verified-ci | Unique branch names; rebuild contaminated branch by cherry-pick |
| Shared-checkout contamination | ProjectAgamemnon [PR #407](https://github.com/HomericIntelligence/Agamemnon/pull/407), [PR #409](https://github.com/HomericIntelligence/Agamemnon/pull/409), and [PR #410](https://github.com/HomericIntelligence/Agamemnon/pull/410); ProjectOdyssey [PR #5363](https://github.com/HomericIntelligence/Odyssey/pull/5363) | verified-ci | Dedicated worktrees; consolidate already-tangled commits |
| Closed `cherry=+` branch was superseded | ProjectHephaestus [PR #586](https://github.com/HomericIntelligence/Hephaestus/pull/586); content via [#583](https://github.com/HomericIntelligence/Hephaestus/pull/583), [#585](https://github.com/HomericIntelligence/Hephaestus/pull/585), and [#587](https://github.com/HomericIntelligence/Hephaestus/pull/587) | verified-local | PR/content/path evidence over cherry count |
| Foreign repository under a worktree-looking path | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/git-worktree-parallel-execution-lifecycle.md) of the ProjectHephaestus cleanup audit, 2026-06-15 | verified-local | Remote mismatch made directory out of scope |
| Cross-process create race | ProjectHephaestus [issue #1567](https://github.com/HomericIntelligence/Hephaestus/issues/1567), [PR #1568](https://github.com/HomericIntelligence/Hephaestus/pull/1568) | verified-local; CI pending at capture | Reusable `fcntl.flock` helper around sweep/allocation |
| Submodule worktree removal refusal | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/git-worktree-parallel-execution-lifecycle.md) of the Odysseus cleanup, 2026-07-13; ProjectOdyssey [PR #5582](https://github.com/HomericIntelligence/Odyssey/pull/5582) context | verified-local | Plain remove and deinit failed; force command handed to user |
| First-writer-wins shared branch | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/git-worktree-parallel-execution-lifecycle.md) of the ProjectHephaestus design review, 2026-07-26 | unverified | Proposed typed ownership/admission contract |
| NUL-safe porcelain parser | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/git-worktree-parallel-execution-lifecycle.md) of the ProjectHephaestus cleanup plan, 2026-08-06 | unverified | Proposed `--porcelain -z` stateful parser |

## Detailed Evidence

The cross-process race occurred when two separate CI-driver subprocesses swept the same issue and
both attempted `git worktree add` for one path. Each process had its own `threading.Lock`, so both
passed the path-existence preflight. The remediation extracted a reusable advisory file-lock helper
and guarded the whole sweep. Local evidence recorded 2,017 unit tests plus clean mypy and Ruff;
GitHub CI was still pending when captured, so the main skill remains `unverified` rather than
promoting the mixed body of evidence.

The submodule cleanup case established that a clean worktree can still be unremovable when it has
initialized submodules. `git submodule deinit -f` did not make plain `git worktree remove` succeed.
Because force removal and branch deletion were safety-blocked, the operator received exact commands
and executed them. This is procedural evidence, not a claim that force cleanup is universally safe.

The branch-ownership and delimiter-safe parser entries are design reviews. Their invariants are
kept in the main because omitting them changes implementation decisions, but their unverified status
must remain visible until a shipped implementation and behavior tests exist.

## Provenance

- Superseded main SHA-256:
  `a72e336252a0c5601cbff5611f3aacd26fe7091f5b6e7a3033e8588147c8e261`
- Issue #3335 base: `1ae0cb498e5250c341c2a4bf585f97e2a28060af`
- Old/new version: `1.7.0` → `2.0.0`
