# PR CI Failure Triage — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Force-push rollup showed cancelled old-head runs | [immutable source documenting ProjectOdyssey PR #5380](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/pr-ci-failure-triage-preexisting-vs-introduced.md) | `verified-local` readback | Retained exact-head filtering |
| Concurrency superseded failed-job rerun | [ProjectHephaestus PR #1073](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1073) | `verified-ci` | Retained newest-applicable-run rule |
| Markdownlint/security failures mislabeled pre-existing | [immutable source case index](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/pr-ci-failure-triage-preexisting-vs-introduced.md) | `verified-ci` | Retained execution evidence over diff intuition/labels |
| Coverage genuinely failed on main | [immutable source documenting ProjectKeystone PR #552](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/pr-ci-failure-triage-preexisting-vs-introduced.md) | `verified-ci` | Retained separate-fix/tracking governance path |
| Duplicate stale commit broke all sanitizers | [immutable source documenting ProjectKeystone PR #436](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/pr-ci-failure-triage-preexisting-vs-introduced.md) | `verified-local` | Retained branch reconstruction rather than tip amend |
| Generated Node harness exceeded hosted argv budget | [ProjectOdyssey PR #5762](https://github.com/HomericIntelligence/Odyssey/pull/5762) | `verified-ci`: failing 254-test run then passing 259-test run | Retained stdin transport and hosted-Linux regression |
| Base-updated long-lived branch: branch test asserted semantics trunk had retired, a lockstep workflow/validator pair was half-moved, and local-only host windows duplicated a pristine trunk failure set | monorepo merge-failure triage outside the host org; 32-way sharded pytest, signed-commit rulesets, staged shard planner | `verified-ci`: all required checks green after the ported test, atomic pair, and FYI dispositions | Retained file-provenance classes, atomic-pair rule, and pristine-base attribution oracle |
| Path-filtered required check failed on two PRs with exit 4 before any test count; identical sibling PRs on the same base that stayed outside the `paths:` filter showed no run | serving-stack repository outside the host org; fixed-selector ownership-policy job with an uploaded evidence directory | `verified-ci`: the rebased branches' path-filtered job (and its sibling job) went green with no diff change; the failing PRs' other ~50 checks were green throughout | Added trigger-filter audit, stale-plan-input classification, evidence-artifact diagnostic, and the main-repaired base-update resolution |
| Aggregate gate failed its report step on a producer output key absent from `needs.<job>.outputs` while every upstream succeeded; the identical drop reproduced across reruns inside the run and in one fresh run, then resolved only by rebasing onto the workflow world current main carried | deployment-lifecycle repository outside the host org; an umbrella gate reading `toJSON(needs)` of an outputs-producing policy job | `verified-ci`: a same-era green run of the same workflow carried the key; after the base update the exact head went green with the diff unchanged | Added the dropped-producer-output attribution order, the stored-output rerun-inheritance rule, the fresh-run-regeneration rule, and the platform-change resolution class |
| Green twins on identical trees misclassified an introduced deterministic failure as a flake: every compared lane ran a narrower event-scoped profile that never executed the failing node | golden-rendering CI in a model-serving repository outside the host org; event-scoped test profiles (narrow pull-request profile, wider promotion profile) over a sharded planner | `verified-ci`: the narrow profile selected 7994 items in every green compared run, the wide profile selected 14876 items and included the failing node; a one-value queue-size config change broke a golden rendering deterministically on both lanes that ran it | Added the green-twin coverage gate, the empty-comparison rule, and the classify-from-content-determinism fallback |
| Red default-branch CI at and after a squash merge looked merge-caused while a task gate required watching main CI to green | fleet-worker delivery lane in a public model-serving-infrastructure repository; 32-way sharded pytest with per-push and batched default-branch runs | `verified-ci`: per-commit run lookup returned empty for the merge commit even after its run existed; branch enumeration showed the first red predated the merge by several commits including its direct parent; every sampled failed job carried an identical node set from one concurrency test module disjoint from the merged patch; the owning lane's labeled fix at a newer tip took the branch run green | Added the merge-sha run bracket, the sparse-run empty-lookup rule, the post-merge collated-node-set test, and the adoption boundary for another lane's breakage |
| Post-merge promotion-profile red classified pre-existing outside delivery scope carried a follow-up-issue obligation, while an aggregate tracker already owned the failing group | single-issue worker lane in a public batch-scheduler infrastructure repository; a release-train red tracker with a curated group ledger | `verified-ci`: the tracker's ledger already named the same red run, the attributing commit, and the merged pull request under an existing group; no new issue was filed and the worker report referenced the group | Added the open-tracker dedupe gate before filing classified pre-existing failures |
| Rebased pull request whose touched test files stayed red in one checkout; the identical failure set reproduced at the pristine base commit and hosted checks were green | anonymized repository, shared host whose configured temp root is group-writable; a fail-closed service-path guard refused every test that created a temp tree | `verified-local`: 63 of 63 failing node identities matched per file at the base commit and at the rebased head; the focused tests covering the conflict resolutions passed; the hosted merge state moved from `DIRTY` to `BLOCKED` | Added the environment-attributed pass-through row, the fail-closed navigation row, the rebase-gate subset of the pristine-base oracle, and the "no added failure, not green" evidence rule |
| A guard the branch adds reads the locally bound deployment context and refused a promotion fixture whose cluster carried one pool record; the same node passed at the pristine base commit | anonymized release-authoring repository under review; promotion manifests compared against an operator-bound context that named three models while the fixture carried one | `verified-local`: the node failed at the reviewed head and passed at the pristine base commit under the same interpreter, temp root, and umask; reverting only the fixture repair failed the node again; the production context file named the refused model and the release binder already refused a manifest that lacked a policy-model record; after the repair the module went to 146 passed and the hosted required check passed | Added the context-dependent-guard row, its production-configuration check, and the accepted-shape success node requirement |

## Rebase gate on a red-on-this-host checkout

A session rebased one pull request in its own checkout and resolved two conflicts. The brief
required the touched test files to pass before a gated force-with-lease push. Under the first
command, 63 of 447 node identities failed. The representative traceback came from a fail-closed
service-path guard that refused an ancestor directory with group-write bits, so every test that
created a temp tree failed the same way. A detached baseline worktree at the pristine base commit,
under the same command, produced the same 63 identities, and the sorted per-file `FAILED` lists
were equal. The focused tests that covered the two resolutions passed at both heads.

Two decisions made this a pass-through. The comparison was per node and per file, so an equal
count could not hide a swap. The report named the equality, the counts, the root cause, and the
hosted merge-state change from `DIRTY` to a review-bound state, and did not call the files green.
The refused value was one configuration variable, the temp root. Relocating it to an owner-only
directory and rerunning both heads was the cheaper branch. This session adjudicated first because
the base comparison was already complete.

## Follow-up tracker dedupe detail

A single-issue worker lane merged a docs-only squash commit and found the post-merge
promotion-profile run red on the release candidate. Triage classified the red as
pre-existing breakage: an earlier merged pull request had added CLI subcommands
without the matching contract-golden update, disjoint from the worker's files. The
lane's scope rule forbade adopting the repair, so the residual obligation was a
follow-up issue. Before filing, the lane searched open issues and found the
release-train red tracker whose curated ledger already listed the same validation
run, the attributing commit, and the merged pull request under an existing group. The
lane filed nothing and referenced the tracker group in its final report, which kept
one failure line under one owner and avoided a duplicate that would have raced the
owning lane's record.

## Post-merge main red bracket detail

A delivery lane merged a tests-and-docs squash commit while the default branch's CI was
already red. The gate required green main CI before the final report. A per-commit
workflow-run lookup for the merge commit returned an empty list even minutes after the
push, which first read as "no run, no evidence"; enumerating the branch's runs exposed
the real picture: the workflow ran only on some pushes, the merge's own run appeared
seconds after the push, and the oldest red run sat on an ancestor several commits
behind the merge, including its direct parent. The last green run sat further behind,
so the red window opened before the delivery lane ever pushed. Collating `FAILED` node
identities from sampled failed jobs of the oldest red run, the merge's run, and the
current tip run showed one test module, set-identical across all three windows, in an
area (a concurrent credential store) disjoint from the merged files. The bracket plus
the identical pre-merge signature classified the red as pre-existing breakage; the
lane did not adopt the repair. A peer lane landed a fix commit whose message named the
failing area at a newer tip within the hour, and that tip's branch run went green,
which discharged the watch-to-green gate with the repair's run identifier as evidence.
The attribution report carried: the last-green and first-red commit and time pair, the
sparse-run empty-lookup warning, the collated node set across the three windows, and
the patch-surface disjointness as supporting context.

## Dropped producer output detail

The upstream fan-in listed every required job as `success`, but the gate's summary step
failed because the job-outputs map it read was missing one producer key. The producer job
had concluded success and its log showed the emit step writing the value, so the drop was
downstream of the producer. A green run of the same workflow from a few hours earlier
carried the key, and a cohort of later runs on unrelated branches failed the same step the
same way; the cohort bracketed a platform-side window. A rerun of the failed gate kept the
stored outputs, and re-running the producer job itself in a new attempt of the same run
dropped the key again, which confirms that job reruns inherit the run's stored job outputs.
A close/reopen of the PR assigned a fresh run ID and the drop still reproduced, which
classified the first cause as a platform behavior change rather than run-local corruption.
Resolution came from a recorded base update: current main already carried a workflow whose
gate no longer depended on the dropped output, and the rebased head went green with the PR
diff unchanged. The resolution echoes the half-moved lockstep-pair rule: when a gate
contract and the platform disagree, move the branch to the contract world that matches. Do
not edit the files the gate happens to read to satisfy the old world.

## Stale plan inputs detail

The check pinned a fixed case list in-repo. A rename on main left the base copy naming a
removed parametrized test, so collection aborted with a usage error (`UsageError`, pytest
exit 4, "no tests ran") before any test total. The failure log collapsed to that one line;
the uploaded evidence directory's selection record (source SHA, zero collected cases, full
pinned list) named the mismatch directly. `git log -S <missing-selector> -- <pinned-list>`
located the renaming change, and `git log -1 origin/main -- <pinned-list>` showed current
main already carried the corrected selector. The path filter had hidden the failure from
main and from every PR whose diff stayed outside the `paths:` list, so no run-based
comparison could classify it. Remediation was a recorded base update to the repaired main,
giving a green exact-head run with an unchanged PR diff.

## Vacuous green-twin detail

A one-value queue-size configuration change invalidated the golden rendering of a scheduling plan.
The failing node executes only inside an event-scoped promotion profile; every ordinary
pull-request lane and every recent main run selected the narrower profile, which the sharded
planner reported as 7994 items, against 14876 items for the promotion profile. Two delivery lanes
shared an identical tree and failed the same golden at the same line; main and both lanes' other
checks stayed green. The initial triage read lane color instead of coverage, declared the failure
an environmental flake, planned hermetic harness sealing, and filed a defect report against the
wrong mechanism. The error surfaced when the green runs' logs were searched for the failing node
id: the node never appeared in any of them, so the comparison set was empty. Reclassification:
deterministic and introduced; a corrective note went onto the report, and the golden state was
regenerated. The now-verify procedure: before a green lane scores as comparison evidence, search
its logs for the failing node id (`gh run view --job <job> --log` per shard) or compare the
selected-test counts the planner prints; a lane that never ran the node does not compare.

## Classification record

| Check | PR head/run | Main head/run | Signature comparison | Class | Action |
| --- | --- | --- | --- | --- | --- |
| Fill per failure | Immutable SHA and URL | Immutable SHA and URL | Same/different/not applicable | Evidence-based label | Fix/rerun/follow-up/wait |

## E2BIG detail

`E2BIG` arises at `execve`: combined arguments and environment exceed the platform budget before the
child runtime executes. Moving generated JavaScript to stdin retains code semantics while shrinking
argv. Test the largest intended payload and verify stderr/stdout parsing still works.

## Evidence boundary

The cases establish the classification workflow on GitHub Actions. Live required contexts,
administrative policy, merge-preview semantics, and runner limits can change and must be re-read.

## Stale version pin on an unchanged file

A learn-delivery pull request passed every content check on its three changed files and failed one
repository-wide guard. The guard compares a version literal held in the test against the version
field in a knowledge entry. The entry read one minor version above the literal.

Bracket evidence, gathered read-only:

- The literal last changed when it was written; the entry changed later in a merge that bumped the
  version and did not update the literal.
- A run at the bump commit's parent passed.
- The run at the bump commit failed, and so did the run at the delivery base, which already
  contained the bump.
- The merge was an ancestor of the delivery base, so the pull request inherited the failure.

Disposition: pre-existing and foreign-owned. The literal was outside the pull request's write
allowlist, so no repair was made. The bracket evidence went onto the pull request as a comment, and
the change stood on its own passing checks. The distinguishing signal was that the failing guard
touched a file the change never modified and the expected value did not move with the tree — a
regression would have shown the asserted value and the tree moving together.

## Mount-reported directory metadata

A shared-storage mount reported `st_nlink=1` for a directory that held a child directory. A local
POSIX filesystem reports `2` for that shape.

Probe output on the affected mount:

```text
/parent        nlink=1
/parent/child  nlink=1
```

The change under test edited a workflow file and a test helper. The offending assertions sat in two
files the change never touched: a provenance guard that rejects `links < 2` on a directory identity,
and two test helpers that assert `st_nlink >= 2` after resolving a directory.

The failure set was 61 nodes in one module. Each node reported one of `object_auth_invalid` with
reason `directory_identity`, or `assert 1 >= 2`. Because every test that creates a directory passes
through the same guard, one mount property produced the whole set.

Attribution followed the oracle rule:

1. Same module at the pristine base commit in a clean detached worktree: same counts.
2. Exactly those failing node ids replayed against the changed worktree: set difference empty in
   both directions.
3. Hosted CI on the pull request: zero failures, including the lint and type-check jobs.

Disposition: environment-attributed pass-through. No assertion was relaxed. The probe output, the
base comparison, and the hosted result went into the pull request body.

The counter-signal matters. The same error label also appears for a real identity change. A probe
value of `2` with a continuing failure means the guard is correct and the tree moved.

## Concurrent-writer wait detail

| Signal | Detail | Verification |
| --- | --- | --- |
| Same prompt, two sessions | Two attended sessions received an identical request to fix every failing check on one promotion pull request. Both classified the same 8 red checks as pre-existing `main` defects, because the pull request was a `main` to release-lane promotion and its head was the `main` tip. Neither session could fix it on the pull request branch. | `verified-local`: pre-session check rollup and the other session's own report, both read from the forge. |
| The other lane moved | Between 15:41 and 19:46 the default branch advanced about 20 times. Each push was a repair for one of the classified reds (a pin test, a process-wide stub leak, a fixture, an ADR map), and each push re-ran the same workflows at increasing timestamps. | `verified-local`: branch commit enumeration and run listing by branch. |
| A quiet window did not prove the lane finished | The tip held unchanged for 25 minutes on three occasions. On the third, a push landed 1 minute after the window closed. In the same session, an earlier 12-minute quiet window was followed by four pushes in 13 minutes. | `verified-local`: the wait loop's own per-minute state log. |
| Zero published reviews | The watched pull request held 0 published reviews for the whole session (4 hours 5 minutes). The other session drove to merge without a review round, so the review count never became a useful second signal. | `verified-local`: repeated `pulls/<N>/reviews` count reads. |
| Outcome | The artifact merged at 19:39, during the wait, by the concurrent lane. The waiting session made no code change and reported the delivered state. | `verified-ci`: pull request state read showing a merge 17 minutes before the final verification read. |

Disposition: the session stayed read-only, recorded the concurrent-writer
window, and added Section 9.3 with a two-signal, 45-minute quiet test.
