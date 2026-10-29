# Post-Merge CI Failure Attribution — Notes

Privacy-safe supporting evidence for `post-merge-ci-failure-attribution.md`. Guidance that the
skill needs for operation is in the main file; this file keeps the source detail.

## Source context

- Date: 2026-10-26.
- Setting: an autonomous single-issue worker lane resumed after a provider outage. Its read-only
  refresh found the lane's deliverable pull request already merged about a day earlier. The
  governing instruction required watching default-branch CI to green before the final report.
- Default-branch shape at that time: a large sharded test matrix (approximately thirty shards),
  several integration matrices, and an aggregate required gate. Many unrelated merges landed in
  the same window (more than one hundred commits between the merge and the refreshed head).

## Observed evidence

1. Check runs at the merge commit, deduped to the latest attempt per job name, showed failures in
   the aggregate gate, in two umbrella jobs, in two integration-matrix shards, and in two test
   shards.
2. The identical deduped failing job-name set appeared at the parent commit on the default branch,
   which contained only unrelated merges. The gate log at both commits carried the same cascade
   line: "required job did not succeed: `<upstream job>`". The named upstream job failed at both
   commits.
3. The test-shard numbers differed between the two commits (for example two shards on the parent
   and two different shard numbers at the merge commit), while the failed-node lines in the logs
   were the same single flaky stateful-store test in both runs. Later unrelated commits changed
   the fixture seeding for that same family and the failure shape disappeared.
4. A base-to-head compare reported the default branch ahead of the merge commit, so the merge was
   an ancestor of the current head. Every check at the current head concluded success or skipped.
5. The lane's own change touched a read-only CI verifier script, its dedicated unit tests, and
   documentation — no area near any failing job.

## Decisions that the evidence changed

- The red rollup at the merge commit did not move the disposition to blocked. The parent job-set
  diff, the cascade message, the log node identity, the later unrelated repairs, and the green
  current head classified the failures as pre-existing foreign-owned breakage.
- The report kept the delivered disposition with the attribution evidence recorded. No writes, no
  label changes, no reruns, and no repair attempts on the default branch followed.

## Commands used

The generic `gh api` calls in the main file's Quick Reference are the exact shape used:

- `commits/<sha>/check-runs?per_page=100`, with the jq group-by-name / max-by-started-at dedupe;
- `gh run view --job <job-id> --log-failed` for failed-node and cascade lines;
- `repos/<owner>/<repo>/compare/<merge>...main` for ancestry.

One-shell-per-command pipelines with `/tmp` files and `diff` made the two job-name sets easy to
re-check after each foreign merge landed.

## Twin-lane same-SHA incident (2026-10-26)

A second case exercised the lane-identity precondition. Identifiers are omitted under the privacy
rules.

1. A completion report for a merged change listed the check runs at the merge commit. One
   workflow name appeared twice with different conclusions: one failure, one success.
2. The failing run had event `pull_request` and the default branch as its head branch display.
   Its display title named a promotion pull request — a lane that promotes the default branch to
   another long-lived branch — whose head was updated to the merge SHA. The successful run had
   event `push` on the default branch.
3. The failing run's failed jobs were a subset of the sharded matrix plus the aggregate gate. The
   gate log carried a cascade line that only echoed the shard failures: "required job did not
   succeed: `<job>`". The failed-node lines named tests in areas that the merged change did not
   touch, with signatures such as an unclassified service-path policy, a visible-command inventory
   drift from an unrelated feature merge, and a release-context classification mismatch.
4. The same workflow at every later default-branch head concluded success, and the merged change
   remained an ancestor of the current head. The promotion lane's failures belonged to that
   lane's own promotion candidate and pre-dated any judgment about the merge.
5. Classification: foreign-lane failure, not the merge's. The merge's attribution used the
   push-event default-branch runs, which were green at the merge commit and at later heads. The
   delivered disposition stood; no rerun and no repair followed. The promotion lane's failures
   stayed with the process that owns that lane.

Lane-identity observation: the check-runs listing at one commit mixes lanes, and a
latest-per-name dedupe can promote a red foreign-lane attempt over a green push-lane attempt of
the same workflow. The event field and the head branch are the lane key: read both before any
parent-commit comparison. A promotion pull request that re-targets each new default-branch head
re-runs at every merge SHA, so every merge commit on such a repository can carry this shape.
