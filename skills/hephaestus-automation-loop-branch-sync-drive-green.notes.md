---
name: hephaestus-automation-loop-branch-sync-drive-green.notes
license: BSD-3-Clause
---

# Notes: Hephaestus Automation Loop Branch Sync and Drive-Green Scope

Supporting evidence for the v1.5.0 findings in
[hephaestus-automation-loop-branch-sync-drive-green](hephaestus-automation-loop-branch-sync-drive-green.md).
All identifiers generalized: one organization repository, one issue, one PR, one operator
host, one coordinating agent. Pipeline module paths are mechanism anchors in the automation
source, not project identifiers.

## Mechanism anchors (automation source)

- `hephaestus/automation/pipeline_github_jobs.py` (~line 348): the merge job maps a malformed
  auto-merge enable result to `auto_merge_malformed`.
- `hephaestus/automation/pipeline_github_merge_mutations.py` `enable_auto_merge()`
  (~lines 21-80): returns `AutoMergeEnableResult(enabled=False, malformed=True)` when the
  `gh` auto-merge mutation cannot complete. The observed crash source: the mutation ran with a
  working directory that no longer resolves to a git repository (mount-boundary
  `fatal: not a git repository (or any parent up to mount point /mnt)`). The same transport
  warning appears earlier in runs as `auto-merge disable failed` — non-fatal there, fatal in
  merge_wait.
- `hephaestus/automation/pipeline/stages/merge_wait.py` (~line 197): merge_wait completes the
  item with `auto_merge_malformed`, which is terminal for the run. Because the stage fails
  before it reads check results, a post-GO loop can neither merge nor fail back to
  implementation for CI repair.
- `hephaestus/automation/pipeline/stages/pr_review_threads.py`: round-0 review job requests,
  thread-read RuntimeError warnings, and the reconciliation that posts answers and resolves
  threads.
- `hephaestus/automation/pipeline/stages/implementation.py`: `addressing N review thread(s)`,
  `requesting commit+push job`, and `implement budget exhausted (2/2)` — the budget is
  per-run; a relaunch refreshes it.
- Lane state: `<repo>.git/hephaestus-source-workspaces/<issue>-impl.json` (receipt with
  `revision`), `<issue>-impl-terminal.json` (terminal record when the lane freezes), and
  `<repo>.git/hephaestus-repository-intake.run.lock` (the cross-run lease; checked with
  `flock -n` before each relaunch).
- Workflow label gate: `LABELS: ${{ toJSON(github.event.pull_request.labels.*.name) }}` then
  `grep -q '"state:implementation-go"'` — payload-sourced, not live.

## Empirical timeline (one lane, two days, 20 runs)

- 12 review rounds in total. Findings per round:
  1 (nitpick), 5 (1 major), 3, 3, 3, 1, 2 (with a rebase-driven major after main advanced
  mid-round), 1, 1, 1, 1, 0. Round 12 was the zero-finding round and the loop applied
  `state:implementation-go` itself.
- `FAIL:commit_push_refresh_invalid`: 5 deterministic reproductions on commit+push jobs that
  carried real commits. Verified each time with `git ls-remote`: the push landed
  (`origin == lane head`). 2 real pushes succeeded (a vacuous reconcile commit and one
  rebase+fix batch), which proves the refresh binding rejects the post-push state, not the
  push. Twice the fail-close hit the pipeline's own push with zero external interference.
- `FAIL:source_workspace_recovery_receipt_invalid`: reproduced where a successful push
  invalidated the lane receipt before the next adoption. One occurrence froze the lane at
  `source_workspace_terminal` with a terminal record while the worktree still held one
  unpublished test-coverage commit — recovered by pushing it manually (dry-run first,
  fast-forward), answering and resolving the thread with commit evidence, then archiving both
  records.
- `FAIL:implement_exhausted (2/2)`: one run bounced from pr_review (thread-read RuntimeError)
  back into implementation and exhausted the per-run implement budget; a clean relaunch
  refreshed the budget and the lane continued.
- After GO: two consecutive runs died at merge_wait with `FAIL:auto_merge_malformed` (one in
  2.6 s). The coordinator armed GitHub native auto-merge directly; the `autoMergeRequest`
  (squash) stayed armed across three subsequent fix pushes and merged the PR when the required
  checks converged green.
- Post-merge, the main-branch push-triggered CI runs at the merge commit were all successful.

## Recovery cycle used (per fail-closed run)

1. Read the summary disposition line: `FAIL:<signature>` plus per-stage attempts.
2. Verify publication before anything else: `git ls-remote origin <branch>`;
   `git -C <lane> log origin/<branch>..HEAD --oneline | wc -l` (unpublished);
   `git -C <lane> status --porcelain | wc -l` (dirty).
3. Publish any unpublished fast-forward commits manually (dry-run first; signed), then answer
   and resolve the matching review threads with commit evidence.
4. Archive — never delete — the lane records into a per-run directory under
   `hephaestus-source-workspaces-archive/<issue>-<date>/run<N>/` (receipt, and the terminal
   record when present).
5. Remove the preserved worktree only after step 2 shows 0 unpublished and 0 dirty.
6. Check the intake lease with `flock -n <lock> true` and relaunch clean.

## Review-thread handling evidence

- 32 review threads total on the PR; all answered with commit evidence and resolved. The loop
  resolved most of them itself during reconciliation; the coordinator resolved the remainder
  when a run died between commit and reconciliation.
- One major finding was environmental: main advanced mid-round and made the PR dirty (content
  conflicts in two files). The implementing model rebased onto the new main and resolved both
  conflicts inside the same round. The coordinator verified with
  `git merge-tree --write-tree origin/main origin/<branch>` (clean tree) and with
  `mergeStateStatus` moving DIRTY to BLOCKED before resolving the thread.
- Two packaging rebases onto advancing main occurred across the lane; normal review rounds
  followed each.

## Post-GO drive-green evidence (coordinator-owned)

- Fresh checks after the GO label: 25 real failures in one profile from a single cause — a new
  test module was not registered in the test-tier inventory, so the tier lists stopped
  partitioning the root modules and every partition/wiring check failed closed. Fix: register
  the module; validated by loading the inventory directly.
- Next cycle: three content violations from the lane itself — formatter drift in two files, an
  invalid-argument-type error (a call site passed a process-control exception to an
  Exception-only helper; fixed per the helper's documented contract), and an unused `noqa`.
  The full lint and type gates ran locally before the push.
- Next cycle: the pinned pre-commit formatter reformatted one extensionless file that the
  project-glob format check could not see. `pre-commit run --all-files` matched CI exactly
  afterward, and the repair commit message documented the cause.
- Label-gate noise: label-event-triggered and stale-payload runs failed fast with
  "The state:implementation-go label is not applied." Do not count these as CI failures.
  Classify by reading one failing job log: gate failures name the label within seconds;
  content failures run minutes and name files.

## Label-event run semantics evidence (v1.6.0 drive-green cycle)

- After a review at a fixed head, applying the GO state label started the gated run itself
  (the workflow trigger list included `labeled`): the run's payload carried the label, the
  provenance job passed in seconds, and the full matrix ran green. No repair push was needed.
  This corrects the earlier note: label events for other labels (before GO) still fail fast;
  the label event for the GO label does not.
- The same PR minutes earlier, with the GO label absent: a synchronize run showed gated jobs
  as `skipping` at the job level, while a separate provenance job failed fast with the
  label-not-applied step error. Both signatures are gate noise, not content failures.
- A required aggregated check failed in about 16 s with only "Require all upstream jobs to
  have succeeded"; the aggregate had no defect of its own. The upstream lint job failed in
  about 12 s on formatter drift: the locked project formatter joined one wrapped return
  statement to one line that an older local formatter had left split. Repair with the locked
  formatter (`<pm> run --locked ... ruff format <file>`), re-verify with `--check .`, then
  amend and re-sign the commit.
- An unrelated hosted-runner test (a real multi-member process-group reaping test) failed the
  same way on the default branch minutes before the PR's run; the PR's final run passed it.
  Treat a matching default-branch failure as flake evidence, record it on the PR, and rerun
  the failed job after the real repair lands.

## Coordinating-agent policy notes

- Agent posts on the PR and discussions used one unique stable identity per repository policy.
- Every coordinator commit was signed and carried `Signed-off-by`; pushes were fast-forward
  only (no force push was needed on the lane).
- The lane receipts and terminal records remain archived per-run for audit.
