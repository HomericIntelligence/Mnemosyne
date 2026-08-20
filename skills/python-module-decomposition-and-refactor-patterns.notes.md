# Python Module Decomposition and Refactor Patterns — Case Notes

These notes retain project-specific provenance and detailed verification boundaries moved out of
the retrievable skill during Mnemosyne issue #3335. They do not duplicate the complete v1.16.0
snapshot, which is preserved in
[`python-module-decomposition-and-refactor-patterns.history`](./python-module-decomposition-and-refactor-patterns.history).

## Case Index

| Case | Source | Finding retained in the main skill | Verification status |
| ---- | ------ | ---------------------------------- | ------------------- |
| Function cluster extraction | [Scylla PR #1444](https://github.com/HomericIntelligence/Scylla/pull/1444) | Keep the public module stable while moving a cohesive function cluster | Merged; 1221→837 lines |
| Collaborator extraction | [Scylla PR #1230](https://github.com/HomericIntelligence/Scylla/pull/1230) | Extract responsibility-oriented classes with characterization tests | Merged; 1527→1105 lines |
| Single-responsibility seam | [Scylla PR #1145](https://github.com/HomericIntelligence/Scylla/pull/1145) | A single-method collaborator can be a legitimate boundary | Merged |
| Full module decomposition | [Scylla PR #1446](https://github.com/HomericIntelligence/Scylla/pull/1446) | Use a façade and focused modules rather than a monolith | Merged; 1488→142-line façade |
| Leaf-cycle break | [Scylla PR #1850](https://github.com/HomericIntelligence/Scylla/pull/1850) | Move shutdown symbols to a dependency-light leaf | Merged |
| Eager package export cycle | [Hephaestus PR #308](https://github.com/HomericIntelligence/Hephaestus/pull/308) | Remove eager `__init__.py` CLI re-exports | Merged |
| Immutable method | [Scylla PR #1311](https://github.com/HomericIntelligence/Scylla/pull/1311) | Replace mutation-plus-return with local immutable flow | Merged |
| Extensibility extraction | Scylla [PR #356](https://github.com/HomericIntelligence/Scylla/pull/356)–[PR #361](https://github.com/HomericIntelligence/Scylla/pull/361) | Extract, parameterize, then introduce a protocol when substitution is real | Merged |
| Reverse CLI delegation | [Hephaestus PR #674](https://github.com/HomericIntelligence/Hephaestus/pull/674) | Original entry point delegates so existing patch targets survive | Verified-local: 45 unchanged tests; 780 automation tests; ruff/mypy clean |
| Sibling-cycle extraction | [Hephaestus PR #714](https://github.com/HomericIntelligence/Hephaestus/pull/714) | Move patchable symbols top-level into an acyclic leaf | Verified-ci: 9 symbols; 3 deferred imports removed |
| Pipeline-step extraction | Scylla [PR #1457](https://github.com/HomericIntelligence/Scylla/pull/1457) / [issue #1430](https://github.com/HomericIntelligence/Scylla/issues/1430) | Split sequential stages and measure complexity before removing suppressions | Merged: three CC>15 functions reduced to CC≤8; 28 new tests; 4591 tests passed |
| Scanner allow-list | Scylla [PR #1440](https://github.com/HomericIntelligence/Scylla/pull/1440) / [issue #1399](https://github.com/HomericIntelligence/Scylla/issues/1399) | Scope a scanner positively with `Path.is_relative_to()` | Merged: 12 scope tests; 4333 tests passed |
| Stale lifecycle counter | [Hermes PR #522](https://github.com/HomericIntelligence/Hermes/pull/522) | Remove manual accounting after context-manager ownership moves | Project tests verified expected `[1]` rather than `[2]` |
| Legacy-code deletion | [Hephaestus PR #745](https://github.com/HomericIntelligence/Hephaestus/pull/745) | Prove zero callers and remove stale references with the dead code | Merged: 587-line script, helper, 480 test lines, and 8 stale references removed; 1093 Python + 26 shell tests passed |
| Substrate-first estimate | [Odyssey PR #5457](https://github.com/HomericIntelligence/Odyssey/pull/5457) | Read current implementation before accepting rewrite estimates | Verified-ci: estimate revised from about 5000 to 1400 lines; implementation added 937 |
| Parallel-phase cleanup | [Archived ecosystem evidence](./python-module-decomposition-and-refactor-patterns.history) | Integrate first, then remove temporary duplication and debt | General practice; no single run identified |
| God-class planning audit | [Hephaestus issue #1179](https://github.com/HomericIntelligence/Hephaestus/issues/1179) | Map state ownership, cross-calls, exports, type mode, and guard files | Unverified plan; implementation not part of that issue session |
| Provider dispatch plan | [Hephaestus issue #1196](https://github.com/HomericIntelligence/Hephaestus/issues/1196) | Prefer a helper for two providers and verify actual result/error contracts | Initial plan unverified; source review corrected false assumptions |
| Provider dispatch implementation | [Hephaestus issue #1196](https://github.com/HomericIntelligence/Hephaestus/issues/1196) | Check return codes at every caller and count nested mock calls | Verified-local: 157 focused tests, ruff, and mypy; CI pending in captured session |
| God-function planning | [Hephaestus issue #1180](https://github.com/HomericIntelligence/Hephaestus/issues/1180) | Verify arithmetic, docstring budget, loop spans, captured values, and full tuple returns | Reviewed plan approved after R0–R3; implementation unverified |
| Shared-state planning | [Hephaestus issue #1289](https://github.com/HomericIntelligence/Hephaestus/issues/1289) | Design write-back, shared-method placement, fixture migration, exports, and budget overhead | Unverified plan |
| Narrow-callable decomposition | Hephaestus [PR #1292](https://github.com/HomericIntelligence/Hephaestus/pull/1292) / [issue #1179](https://github.com/HomericIntelligence/Hephaestus/issues/1179) | Lambda-wrap injected host methods and patch each module lookup | Verified-ci: 3338→2404 lines; 146 existing + 22 new tests |
| Constructor/DRY refinement | Hephaestus [PR #1320](https://github.com/HomericIntelligence/Hephaestus/pull/1320) / [issue #1289](https://github.com/HomericIntelligence/Hephaestus/issues/1289) | Thin stubs, dynamic host values, identity-preserving dict updates, and structural-test updates | Verified-ci: 2404→1410 lines; 1600 tests; clean second pre-commit pass |
| Signature and patch audit | [Hephaestus issue #1289](https://github.com/HomericIntelligence/Hephaestus/issues/1289) review rounds R5–R7 | Source-read keyword-only parameters, returns, and all patch buckets | Planning evidence only; multiple fabricated signatures caught before implementation |
| Dynamic host path | Hephaestus closed [PR #2400](https://github.com/HomericIntelligence/Hephaestus/pull/2400) / [issue #1269](https://github.com/HomericIntelligence/Hephaestus/issues/1269) | Inject `Callable[[], Path]` when fixtures reassign a path after construction | Salvaged verified-local result; closed PR lost; four sibling tests exposed defect |
| Cohesive first slice | Hephaestus closed [PR #2396](https://github.com/HomericIntelligence/Hephaestus/pull/2396) | Pick the cluster with one shared field and defer C901 carriers | Partial/unverified; salvaged from closed PR |
| Three guard files | Hephaestus closed [PR #2418](https://github.com/HomericIntelligence/Hephaestus/pull/2418) | Discover and update every omit/smoke guard before adding a module | Partial/unverified; salvaged from closed PR |
| Budgeted façades and authority | [Archived reviewed design](./python-module-decomposition-and-refactor-patterns.history) | Apply family budgets, acyclic operation collaborators, and one approval mutation site | Unverified reviewed design; no implementation or CI run |

## Detailed Verification Boundaries

### Reverse Delegation and Import Cycles

ProjectHephaestus PR #674 reduced `implementer.py` from 872 to 702 lines and created a
236-line `implementer_cli.py`. The important result was not the line count: 45 pre-existing tests
continued unchanged because the original module retained the patchable entry-point surface.
ProjectHephaestus PR #714 separately proved that top-level symbol extraction can remove deferred
imports between sibling modules; its AST regression guard checked that three deferred imports did
not return.

ProjectScylla PR #1850 used a dependency-light `shutdown.py` leaf. ProjectHephaestus PR #308 fixed
the other common cycle shape: package initialization eagerly imported CLI modules which imported
back into the package. These are distinct repairs; moving a symbol and trimming package exports are
not interchangeable.

### Pipeline and Provider Boundaries

ProjectScylla PR #1457 extracted stages from three `llm_judge.py` functions, reduced each measured
complexity from above 15 to at most 8, and removed three `# noqa: C901` markers only after the new
measurement passed. Twenty-eight new tests and 4591 passing tests were reported.

The ProjectHephaestus issue #1196 planning review found that `AgentRunResult` had
`stdout`/`stderr`/`session_id`, not the proposed `returncode`, and that both `run_codex_session` and
`resume_codex_session` raised `CalledProcessError`. The corrected implementation normalized the
successful result to `CompletedProcess(returncode=0)`, caught the verified error at the boundary,
and left `TimeoutExpired` propagating. Removing a broad outer catch exposed exhausted
`side_effect` lists; one test needed a third subprocess result for a nested clean-status call. A
separate caller also needed an explicit nonzero-return guard. These facts were locally verified;
the captured session did not establish CI success.

### God-Class State and Test Seams

ProjectHephaestus PR #1292 extracted four collaborators from `CIDriver`: `PRDiscovery`,
`CICheckInspector`, `CIFixOrchestrator`, and `PostMergeProcessor`. It established four material
test seams:

- injected host methods need lambda wrapping so `patch.object` remains live;
- subprocess names imported into both host and collaborator need separate patches;
- moved cache attributes require updating every sibling fixture/access path;
- structural test `companions` lists must include modules receiving moved `AGENT_*` constants.

ProjectHephaestus PR #1320 preserved public patch targets with thin delegation stubs, propagated
test-time host assignments to collaborators, kept shared dict identity with in-place updates, and
left `_pr_is_failing` in the façade because `loop_runner.py` imported it. A local copy was preferred
over a collaborator-to-façade cycle. The change required `from __future__ import annotations` in
collaborators with PEP 604 annotations and a clean second pre-commit pass.

Issue #1289 planning rounds remain explicitly unverified. They found several errors before code:
`_retry_no_commit_once` was keyword-only and did not have the proposed `acquired_slot`; six stub
return types were wrong; `_mark_drive_green_learn_result` accepted keyword-only `succeeded` and no
`pr_number`; and `_gh_call` had 26 patch sites spread across test classes. Three worker methods did
really accept `acquired_slot`, proving that both omission and invention are risks. The durable rule
is source inspection, not the parameter-name mnemonic.

### Dynamic Values, First Slice, and Guard Ordering

The salvaged ProjectHephaestus #1269 / closed PR #2400 case captured `self.state_dir` by value in
`ArmingStateStore`. A fixture reassigned the host path after construction, so collaborator writes
and test reads diverged and four startup-sweep tests observed zero calls. The local repair injected
`lambda: self.state_dir` typed as `Callable[[], Path]`. Because the PR was closed/lost, this is not
CI evidence.

Closed PR #2396 supplied a partial first-slice heuristic: use an AST inventory of `self` attributes
to pick the most cohesive cluster and state explicitly when the first PR removes zero C901 markers.
Closed PR #2418 showed that the assumed guard path was wrong: the repository used
`tests/unit/validation/test_omit_allowlist.py`, plus an integration `OMITTED_MODULES` list and a
coverage omit glob. The proposed atomic guard-before-module commit ordering was not fully verified.

### Reviewed Façade Design

The v1.16.0 input was a reviewed design for decomposing five coupled ProjectHephaestus hotspots:
`Coordinator`, `PipelineGitHub`, `ReviewPhase`, `PrReviewStage`, and `CIFixOrchestrator`. It proposed
fixed primary/collaborator/family physical-line budgets, a DFS import-graph contract, narrow typed
operation records, and a single AST-counted approval mutation guarded by proof and fresh read-back.
No implementation, test execution, or CI result was supplied, so the retrievable skill retains
`verification: unverified`.

## Compaction Provenance

- Issue: HomericIntelligence/Mnemosyne #3335
- Immutable source: `1ae0cb498e5250c341c2a4bf585f97e2a28060af`
- Superseded version: v1.16.0
- Current version: v2.0.0
- Snapshot SHA-256: `27f760b2b2bbdbb6e8a09c9ea4243248644b80b8f7465713ff00b396f693b176`
- Materiality audit: triggers, commands, signatures, return/error rules, state ownership,
  patch-routing failures, import-cycle constraints, verification boundaries, and representative
  parameters remain retrievable; project paths, full case narratives, and detailed results moved
  here; the complete old main exists only in history.
