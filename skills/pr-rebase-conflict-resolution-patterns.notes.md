# PR Rebase and Conflict Resolution Patterns — Case Notes

These notes preserve project-specific evidence and worked-case provenance from
version 1.15.0. The complete v1.15.0 retrievable content is archived once in the
[history file](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-rebase-conflict-resolution-patterns.history).

## Case Index

| Case | Source | Status | Retained lesson |
| --- | --- | --- | --- |
| Large rebase queues | [Archived multi-repository queue sessions](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-rebase-conflict-resolution-patterns.history) | verified-ci / verified-local | Fix trunk first, isolate branches, serialize shared hot files |
| Stacked fixes | Mnemosyne [PR #1976](https://github.com/HomericIntelligence/Mnemosyne/pull/1976) / [PR #1978](https://github.com/HomericIntelligence/Mnemosyne/pull/1978); Odyssey [PR #3189](https://github.com/HomericIntelligence/Odyssey/pull/3189) | verified-ci / verified-local | Retargeting does not carry later fixes; prove and cherry-pick orphan commits |
| Full rewrite versus small delta | [Odysseus PR #64](https://github.com/HomericIntelligence/Odysseus/pull/64) | verified-local | Keep the coherent rewrite and port the small edit |
| Already-upstream add/add | Hephaestus [PR #967](https://github.com/HomericIntelligence/Hephaestus/pull/967), [issue #768](https://github.com/HomericIntelligence/Hephaestus/issues/768) | verified-local | Compare both versions and final diff; close if superseded |
| DIRTY with green checks / modify-delete | Hephaestus [PR #1014](https://github.com/HomericIntelligence/Hephaestus/pull/1014) / [PR #720](https://github.com/HomericIntelligence/Hephaestus/pull/720) | verified-ci | Conflict is the blocker; verify stale base before deletion |
| SHA-pin policy blocks required dependency | [Archived 2026-06-13 Mnemosyne session](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-rebase-conflict-resolution-patterns.history) | verified-ci | Rebase to inherit pinned workflow; empty commit cannot repair stale YAML |
| Parallel module extraction | Hephaestus [PR #1360](https://github.com/HomericIntelligence/Hephaestus/pull/1360) / [PR #1361](https://github.com/HomericIntelligence/Hephaestus/pull/1361) | verified-ci | Trunk source plus union of unique tests; 1,747 tests passed |
| Cross-PR semantic collision | Hephaestus [PR #1336](https://github.com/HomericIntelligence/Hephaestus/pull/1336) / [PR #1337](https://github.com/HomericIntelligence/Hephaestus/pull/1337), fix [PR #1340](https://github.com/HomericIntelligence/Hephaestus/pull/1340) / [issue #1339](https://github.com/HomericIntelligence/Hephaestus/issues/1339) | verified-local at capture | Prove common failure on trunk and fix once |
| AA without markers | [Odyssey PR #5500](https://github.com/HomericIntelligence/Odyssey/pull/5500) | verified-local | Use status codes and inspect `HEAD`/`REBASE_HEAD`; skip upstream-equivalent commits |
| Same-file serial train | [Archived Hephaestus issue/PR train](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-rebase-conflict-resolution-patterns.history) | verified-ci | Smallest diff first; union helpers and thin delegates; re-sign replayed commits |
| Mock/API divergence | Hephaestus [PR #1633](https://github.com/HomericIntelligence/Hephaestus/pull/1633), [issue #1405](https://github.com/HomericIntelligence/Hephaestus/issues/1405) | verified-ci | Regenerate tests against current implementation; 335 focused tests passed |
| False rebase success | [Hephaestus PR #1657](https://github.com/HomericIntelligence/Hephaestus/pull/1657) | verified-ci | Verify merge base and a known trunk-only symbol after push |
| Half-applied layered timeout contract | [Hephaestus PR #1657](https://github.com/HomericIntelligence/Hephaestus/pull/1657) | verified-ci | Check constants, readers, helpers, defaults, callers, and contract tests |
| Import-line union | [Hephaestus issue #1429](https://github.com/HomericIntelligence/Hephaestus/issues/1429) | verified-local | Union symbols, lint, and import at runtime |
| Dirty Inference Service checkout | [Archived Inference Service PR #289 evidence](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-rebase-conflict-resolution-patterns.history) | verified-ci | Preserve staged work, use `origin/master`, keep Warden names and `srun --mem=0`; 489 tests passed |
| HAProxy lifecycle reconciliation | [Archived 2026-07-07 Warden branch evidence](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-rebase-conflict-resolution-patterns.history) | verified-local | Keep `-sf` process replacement and master-CLI stats; 557 targeted and 1,227 pre-push tests passed; image validation unavailable |
| Silent complexity/test/policy/inventory drift | [Hephaestus PR #2056](https://github.com/HomericIntelligence/Hephaestus/pull/2056) | verified-local | Whole-tree lint, tests, whole-file policy search, and inventory hooks catch distinct defects |
| Content-derived test pins in a conflict | Anonymized monorepo PR train, 2026-10 (see below) | verified-local | Recompute pins from merged content; mirror assertions to computed truth, never guess invariants |
| Target merged at the delivery gate | Anonymized hosted monorepo PR, 2026-10 (see below) | verified-local | Re-read artifact state immediately before the mutation; a merged target gets content-equivalence proof and a stand-down, not a replay push |
| Every conflict resolves to the target side | Anonymized documentation-only PR, 2026-10 (see below) | verified-local | Prove the sibling delivery and the empty residual, close the PR, and do not resolve or push |

## Additional Ecosystem Evidence

- ProjectOdyssey: PR #3097 had 23 conflicts; PR #5348 required semantic
  resolution; PRs #5485/#5487 required optimizer numeric-equivalence checks, with
  the unproven Shampoo change deferred to #5491.
- ProjectScylla: PR #1931 ported a feature after #1929 decomposed `runner.py`;
  issue/PR chain #832 to #882 exercised deletion across a rebase.
- ProjectKeystone: PRs #577-#581 used decouple, port, then delete under ADR-015/016.
- ProjectNestor: PRs #83/#87/#94/#97/#99/#101 formed a serial hot-file train;
  #101 exposed accidental clang-format on CMake and the need for a local build.
- AchaeanFleet PR #661 exposed a TypeScript shadow/TDZ failure created only by
  combining two branches.
- Agamemnon PRs #419/#420/#421 and Odysseus PR #43 preserved extraction and NATS
  reconciliation behavior; Agamemnon #422 used an empty commit only to retrigger
  absent checks, not to repair stale workflow policy.
- Anonymized monorepo PR train (2026-10): a configuration union conflicted in two
  test files that pin content-derived values (a spec-hash map and a computed context
  identifier). The resolution recomputed every pin through the repository's own
  derivation against the merged configuration, mirrored adjacent semantic assertions
  to the computed merged truth, and converged on the first focused run: 824 tests
  passed after regeneration. Two invariants guessed by symmetry failed the computed
  values and were corrected, which established the no-guessing rule for semantic
  assertions under this class.
- Anonymized hosted monorepo PR (2026-10): a two-commit deliverable, 16 trunk
  commits behind, was rebased with a semantic union of two independent features in
  one build program (each side shifted the same positional parameters), the
  content-derived digest pin recomputed from the merged bytes, and one consumer
  test fixture updated for a new precondition the change introduced; 466 focused
  tests passed with lint and format clean. The mandated pre-push fetch then showed
  the pull request had squash-merged upstream minutes earlier through a parallel
  actor, and its source ref was already deleted. Equivalence was proven at content
  level: the upstream merge commit's copy of the conflicted program hashed
  byte-identically to the prepared resolution, the repository's own digest pin
  pointed at the same value, and the fixture update was present verbatim. No push
  occurred; zero unique work remained unretained. The stop path itself has no CI
  receipt because no delivery ran.
- Anonymized documentation-only pull request (2026-10): a three-file comment
  correction carried a delivered approval state at its reviewed head and an
  independent review that returned a positive verdict at that same head. The
  branch was reported `CONFLICTING` against a fast-moving target branch. A
  rebase onto the current target head conflicted in all three changed files,
  and each conflicting hunk showed the same corrected wording on both sides: two
  source files and one test case. A sibling pull request had already merged the
  same correction, with the same three changed paths, approximately 18 hours
  before the rebase attempt. Proof sequence: the sibling was `MERGED`, its merge
  commit was reachable from the target branch, the linked issue was `CLOSED` with
  the sibling in its closing references, the target branch text satisfied each
  acceptance criterion, and a search for the stale term in the three changed
  files returned only unrelated matches in an unrelated subsystem. Resolution:
  the rebase was aborted before any commit, the temporary worktree was removed,
  and no push occurred. The pull request was closed with a comment that listed
  the conflicts, the sibling merge commit and time, the issue closing reference,
  and the acceptance check. The delivered approval label stayed in place and was
  not edited. No new review round ran at a new head, because no new head existed.
  Evidence limit: the sibling merge time and the rebase attempt are recorded from
  the forge and local Git. No test run was necessary, because the change changed
  no behavior.

## Semantic Audit for v2.0.0

The compaction retained every materially distinct action from v1.15.0:

- triggers for single, stacked, mass, same-file, add/add, modify/delete, workflow-
  policy, full-rewrite, semantic-collision, and clean-but-broken rebases;
- the rebase inversion of ours/theirs, status-code diagnosis, both-stage reads,
  generated-file regeneration, import/test union, serial trains, superseded-PR
  detection, signature renewal, explicit force leases, and auto-merge re-arming;
- checks for current merge base, trunk-only behavior, markers, whole-tree lint,
  tests, type/build contracts, policy restatements, inventories, mocks, and layered
  APIs;
- named failed approaches and their corrective decisions;
- verification boundaries, including the unavailable Inference Service image
  validation and cases that were local-only at capture.

Repeated command transcripts, exact historical SHAs, long project narratives,
and duplicate tables moved here or remain in history. No unverified evidence was
upgraded.
