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
| Stale import found only by lint after the rebase | Anonymized hosted monorepo PR, 2026-10 (see below) | verified-local | Restore or delete the import in the commit that uses it; amend `HEAD` only when `HEAD` is that commit |
| Scripted resolver dropped adjacent numbered steps | Mnemosyne merge-wave stack integration, 2026-11 (see below) | verified-local | Preserve each whole conflict side or a verified union, then diff the heading and step inventory against both stages before every push in a stack |

## Stale Import Found Only by Lint

Evidence from an anonymized hosted monorepo rebase of a 20-commit branch. The
rebase finished with no conflict markers. `ruff check` then reported two
defects:

- one symbol was missing (`F821`) because the conflict resolution took the trunk
  import line and dropped a symbol that a later replayed commit used;
- one import became unused (`F401`) because a replayed commit removed its last
  use.

Both appearances were in commits other than `HEAD`. A `git commit --amend` on
`HEAD` made lint pass. It also attached the repair to the unrelated last commit.
A cleanup amend that touched the same import line also reverted the real repair.
An interactive rebase with `edit` on the causing commit produced clean history.

The local test run reported 188 failures against a 193-failure baseline at
trunk. Every residual failure came from an environment guard, because the test
host root was group-writable. The branch failures were a strict subset. Report
the environment cause and give the suite to CI.

| Silent import and baseline repairs | Anonymized hosted monorepo PR rebase, 2026-10 | verified-local | Place each repair in the causing commit; compare failure nodes at a refreshed base |
| Union of two competing guards | Comet [PR #3654](https://github.com/LLM360/comet/pull/3654) rebased onto a trunk commit from [#3636](https://github.com/LLM360/comet/issues/3636), 2026-11 | verified-local | Keep the trunk design; delete the replayed side's duplicate guard, helper, state, parser, and tests |
| Delete-side block conflict | Comet [PR #3792](https://github.com/LLM360/comet/pull/3792) rebased onto trunk at 2026-10 | verified-local | Take the deletion when the commit retires the artifact; grep the final tree for the deleted name |
| Armed auto-merge fired on the delivery head | Anonymized hosted monorepo PR, 2026-11 (see below) | verified-ci | Read the arm state before the push; a self-merge names its own PR and needs a close-out, not a second rebase |
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
- Comet PR #3654 (2026-11): a 2-commit branch conflicted with a trunk commit that
  landed a different design for one failure mode. The branch added a fail-closed
  serve-argument capability guard with a `permanent_error` state; trunk added a
  fail-open validator with a `permanent_block` state. The rebase kept both guards,
  both states, both exit-code parsers, and both test sets, and it compiled. The
  union signature was a nonempty diff against trunk in files that trunk had fully
  superseded. The resolution kept the trunk validator and block state, added one
  drift note for the branch's extra digest check, deleted the duplicate guard,
  helper, parser, and six tests, and removed three files that trunk had retired.
  1,116 focused tests passed with lint and format clean; the supervisor and
  configuration files then matched trunk exactly. The pull request stayed open at
  the new head and needed a fresh review because the earlier review approval was
  bound to the old head SHA.

- Semantic Audit for v2.4.0: kept the earlier v2.0.0 compaction, then added the
  clean-merge union-of-both-guards branch with its conflict table row, failed
  attempt, and case note. No verified evidence was upgraded.

## Delete-Side Block Conflict

Comet PR #3792 (2026-10) conflicts in one installer script. One replayed commit
deletes a per-model limit table because the gateway now publishes the value in a
server response. Trunk added new entries inside that same table. Both sides assert
opposite intent for one artifact: keep it and extend it, or retire it.

The correct residual is the deletion. Keeping trunk's entries would leave half a
retired table, and the branch tests assert the table name is absent. A whole-file
search for the name found no other reference, and the script passed a syntax
check. The branch tests passed.

Two tests failed in a later module. The same two nodes also failed on a clean
checkout of the recorded trunk revision, so the rebase did not cause them. Report
the count and the node names, and compare node sets. Matching totals alone can
mask a branch-only node.
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
- Anonymized hosted monorepo pull request (2026-11): a rebase-only task on a
  `CONFLICTING` pull request that carried a delivered approval label at its old
  head. Two changed files, one text conflict, where the target side had added a
  new warning note in the same test and moved the asserted record index by one.
  The resolution kept both intents: the target side's ordering plus the branch's
  record-content assertions reindexed to the new position. A local check
  confirmed the branch's slot formula equalled the production helper, so no
  reviewed behavior changed. During the conflict loop, a plain
  `git rebase --continue` opened the editor and blocked until the command
  timeout killed it. The retry confirmed no `index.lock` remained and a complete
  `rebase-merge` directory, then continued with both editor overrides. The
  replay produced an unsigned commit (`%G?` = `N`) where the old head was
  signed, so the commit was re-signed with `-S -s` before the push. The push used
  a lease pinned to the observed old head. All 47 checks passed, 3 were skipped.
  The pull request carried an auto-merge request armed by an operator before the
  task started; it was not read before the push. When the new head's checks went
  green, that request merged the pull request at the new head. The merged commit
  was byte-identical to the prepared head for both changed files. The trunk
  commit subject named the same pull request. The worktree was removed and one
  delivery comment recorded the head move, the resolution, the approval-label
  scope, and the merge. Evidence limit: the merge is a real outcome, but it
  bypassed the intended re-review at the new head, so it is not evidence that a
  re-review passed there.

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

## v2.6.0 — `AA` from two independent implementations (§ add-add-superset-compare)

Two lanes implemented one issue in parallel and each created the same three
scripts. The second lane to push hit `CONFLICT (add/add)` on all three.

The trunk copy was larger on two of three files, but the replayed copy was larger
on none — which is not the signal. The signal was the direction of the diff:

- trunk-vs-replayed showed only additions (reader helpers, an argument parser, a
  required digest and profile flag);
- replayed-vs-trunk showed only removals (a narrower gate with no weights or
  profile verification).

That made the trunk copy the superset and the issue's required property
(cross-shard agreement on weights and profile) was absent from the replayed copy.
Rebasing the replayed branch would have reproduced the trunk code. Re-landing the
replayed copy would have regressed the gate. The lane was closed with the
two-direction diff quoted as evidence.

The same session produced the mirror case worth separating: a branch that had
been reviewed as a superset was re-landed as one commit on a trunk model that had
shipped first, where the trunk's split of the compared fields was kept and only
the branch's unique entry points were added. Both cases share one rule: prove
which copy is the superset, then keep it. Which artifact to write in depends on
whether the trunk copy is the reviewed model.

## v2.7.0 — a scripted resolver kept only the first line of one side

A dependency-ordered stack of ten amendments targeted one consolidated skill.
Each branch was rebased onto the previous branch and its conflicts were resolved
with a small script. The script read the conflict block, took the chosen side,
and appended only its first list element. One resolution dropped three adjacent
numbered workflow steps that were present on both sides.

The result was a valid file. It parsed, passed the repository validator, and
passed the focused tests. No test pinned the step inventory, so CI reported
success. The loss was visible only when the numbered-step list was compared with
the predecessor: the sequence jumped from 6a to 11. The same stack later
restored the steps while resolving a different conflict, so the trunk had a
temporary regression between the two merges.

The durable rules from the case:

1. A programmatic resolver must preserve each whole side, or a union it can
   justify. Never index a single element of a multi-line side.
2. Compare the result's heading list, numbered-step sequence, and table-row
   count with both conflict stages. A missing element needs an intentional
   deletion reason.
3. Run that comparison before every push in a stack. A later branch's repair
   does not undo an earlier branch's merge.
