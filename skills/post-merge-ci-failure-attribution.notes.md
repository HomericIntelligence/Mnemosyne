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
   line: "required job did not succeed: <upstream job>". The named upstream job failed at both
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
