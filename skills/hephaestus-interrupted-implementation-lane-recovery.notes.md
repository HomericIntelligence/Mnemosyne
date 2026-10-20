---
name: hephaestus-interrupted-implementation-lane-recovery.notes
license: BSD-3-Clause
---

# Notes: Hephaestus Interrupted Implementation-Lane Recovery

Supporting evidence for
[hephaestus-interrupted-implementation-lane-recovery](hephaestus-interrupted-implementation-lane-recovery.md).
All identifiers generalized: one target repository, one long-running issue, one operator host.

## Mechanism anchors (automation source)

- `hephaestus/automation/pipeline/coordinator_sources.py`: the coordinator creates one
  `run_nonce=uuid.uuid4().hex` per run.
- `hephaestus/automation/pipeline/coordinator.py` (~lines 347-376):
  `_direct_issue_identity` sets `branch = "" if existing_pr is not None else
  f"{issue}-auto-impl-direct-{run_nonce}"`; the seeding path stores the nonce in
  `item.payload[DIRECT_SCOPE_WORKTREE_NONCE_KEY]`.
- `hephaestus/automation/pipeline/worker_pool.py` (~line 7585): the first-publication pre-intent
  raises `ValueError("The first-publication source branch changed.")`; the pipeline summary
  surfaces it as `BLOCKED:first_publication_discovery_failed`.
- `hephaestus/automation/repo_intake.py` (~line 769): the dirty-worktree refusal text is
  "repository-intake requires a clean tracked tree; " + the preserve/commit-or-stash instruction;
  `_reject_modified_intake_tree` scans every registered worktree fail-closed before issue work.
- `hephaestus/automation/source_worktree.py`: the `FirstPublicationStore` and the source-workspaces
  state dir enforce owner-only permissions; group-writable `.git` (mode 0775) reproduces
  `ValueError('pending rebase directory permissions are unsafe')` from `candidate()`; `chmod 755`
  on the common dir and on `hephaestus-source-workspaces` returns `candidate()` to a clean `None`.

## Empirical timeline (one issue, one day)

1. Run R1: implement job timed out at 5400 s with forward progress. Zombie implementer session
   detected on the lane; interrupted by agent API. Lane dirty (36+ paths).
2. Runs R2 (twice): intake died fast with `FAIL:clone exhausted after 2 attempts: repository-
   intake requires a clean tracked tree; preserve the tracked changes in <lane>, then commit or
   stash them`. Cause: the zombie-written paths. Fix: preserve, then clean.
3. Run R3 disposition attempt A: lane stashed to pristine, `HEAD` == receipt revision,
   start records retained. Result: `BLOCKED:first_publication_discovery_failed`. This falsified
   the "clean lane is resumable" hypothesis and confirmed the nonce binding.
4. Full record disposition (receipt + start trio + pending-rebases + terminal, archived not
   deleted) plus worktree removal; run R4 re-entered implementation normally and ran to its
   next decision point.
5. Run R5: second implementer timeout at 7200 s with forward progress -> raised
   `--implementer-timeout` to 14400 lane-relaunch; the disposition repeated cleanly.
6. Two later runs were stopped by an external signal at 45-95 minutes into the implementer job.
   Both reproduced signature 1 (zombie session) and were recovered with the same 7-step sequence.

## Signature 1 detail: the zombie implementer session

- The model-side session for the implement job survives: job timeout (budget exhaustion), the
  loop's own SIGINT teardown, and an external kill of the loop process.
- Detection: `git status --porcelain` or lane file mtimes advance after the run summary timestamp;
  `GET /api/session/active` on the agent serve daemon lists the session, and its recorded
  directory ends with the lane name (for example `...auto-<issue>-impl`).
- Neutralization: `POST /api/session/<id>/interrupt`. Response `{"interrupted":true}` plus absence
  from the active list confirms stoppage. A response `{"interrupted":false}` means the session
  already went idle; treat the lane state as authoritative and proceed.
- Boundaries: the serve daemon is shared infrastructure. Other operators' runs appear in the same
  active-session list; interrupting by anything but the lane-directory match risks foreign work.
- The lane records the loop left behind (`RESUMABLE` teardown) remain intact; the zombie writes
  continue ON TOP of them, which is why intake later dies on signature 2.

## Disposition record set

Move (never delete) these files to an archive directory:

```text
<clone-common-dir>/hephaestus-source-workspaces/
  <issue>-impl.json                                  # first-publication receipt
  <issue>-implementation-start.json                  # start record
  <issue>-implementation-start.pending.json          # pending start record
  <issue>-implementation-start.reservation.json      # reserved start record
  <issue>-impl-terminal.json                         # terminal record (only when present)
  pending-rebases/<issue>*                           # any pending-rebase entry for the issue
```

Not disposed: `<issue>-review.json` (publication/review journal for other stages) and the
`*.lock` files (they are flock artifacts, removed by the next run's lock acquire path).

## Preservation mechanics that work

- A signed WIP commit on the lane's current nonce branch survives `git worktree remove --force`
  because the branch ref is retained. Keep the branch even though its name is stale.
- `git stash push -u` from inside the lane also survives: `refs/stash` lives in the common dir,
  not in the worktree metadata.
- Either way, interrupt the zombie first; otherwise new writes land between preservation and the
  cleanliness check.

## Intake lane self-poison (signature 5)

Lane preparation can create its agent state dir (`DEFAULT_STATE_DIR`, observed as `build/`
including nested `.issue_implementer/locks/git-*.lock`) INSIDE the new lane worktree. The lane's
own `git status --porcelain` then reports untracked files and the lane poisons itself. Operator
shim: append `/build/` (or the observed state path) to `<clone-common-dir>/info/exclude`. This is
a host-side shim, not an automation patch.

## GraphQL budget probe (P6)

- `gh api rate_limit` reports a GraphQL remainder that lags the enforcement counters; during
  multi-run contention windows the enforcement side can be exhausted while REST shows thousands
  remaining.
- Authoritative probe: one real GraphQL call, for example
  `gh label list --limit 1 --json name --jq '.[0].name' -R <owner>/<repo>`.
- Observed contention windows under multiple concurrent runs: exhaustion from roughly minute 13
  to minute 55 of each hour; recovery once co-tenants' batches pass. Time a relaunch to the start
  of a quiet window.

## Fail-closed writer-recovery chain (five runs, one issue)

Identifiers generalized: one target repository, one issue with no dependency chain, one operator
host with a native v2 agent CLI behind a translator shim. The item had approved `state:plan-go`
(two review rounds) before the first implementation run.

Timeline of signatures:

1. Run R1: planned, reviewed, `state:plan-go`; died at the rebase writer with
   `FAIL:host signing configuration unavailable` right after lane creation (signature 6). Host fix:
   declared the operator's existing repo-local SSH-signing identity in the host-global git config
   (the key was already passphraseless, mode 0600).
2. Run R2: died in seconds with `FAIL:dirty_direct_claim_failed` (signature 7). Cause: the R1
   preserved lane worktree had been discarded with `git worktree remove --force` per the summary's
   discard instruction, while `hephaestus-source-workspaces/<issue>-impl.json`
   still recorded the path. Fix: `git worktree add --force <lane-path> <receipt-branch>` — the
   branch still pointed at the receipt revision and carried zero commits, so the probe then
   reported not-applicable and the run formed a fresh lane.
3. Run R3: the fresh run cut a new nonce branch and advanced the receipt to generation 2; the
   writer then failed with `initial implementation state failed: initial implementation record
   does not match` (signature 8). The stale `*-implementation-start.pending.json` still named the
   R1 branch and previous base revision. Fix: archived (moved, not deleted) the pending record.
4. Run R4: writer failed with `initial implementation history is unknown; use --rebase to
   continue` (signature 8, second half). Fix: relaunched with `--rebase`.
5. Run R5: intake OK -> lane -> rebase writer -> advise -> implement job claimed with a fresh
   budget. The recovery chain terminated in a working implementation run.

Mechanism anchors (automation source):

- `hephaestus/automation/pipeline/worker_pool.py` `_controlled_git_signing_env` /
  `_read_host_git_signing_config`: builds the writer env from
  `git config --global --null --get-regexp ^(user\.name|user\.email|gpg\.format|user\.signingkey)$`
  and returns the `host signing configuration unavailable` job error when any key is missing.
  `gpg.format` must be `ssh`; `_validated_signing_key` rejects non-absolute, symlink, missing, or
  group/other-writable key paths. The job env then injects `commit.gpgsign=true` and a trusted
  `gpg.ssh.program` found on the default search path.
- `hephaestus/automation/pipeline/worker_pool.py` `_git_claim_dirty_direct_continuation`: the
  probe reads the lane receipt through `SourceWorkspaceManager`; `_is_dirty` runs
  `git status --porcelain` in the receipt path and raises
  `SourceWorkspaceError("cannot inspect source workspace: <path>")` when the path is gone; the
  stage maps that to `dirty_direct_claim_failed`. A cleanly restored worktree at the receipt
  identity makes the probe return `{"dirty_direct_not_applicable": true}`.
- `hephaestus/automation/pipeline/worker_pool.py` `_initial_record_matches`: the writer compares a
  stored `<issue>-implementation-start*.json` record key-by-key against the current run identity
  (repository identity, issue, branch) plus a full-SHA `head_sha`; a mismatch raises
  `initial implementation record does not match`. An absent record yields the
  `initial implementation history is unknown; use --rebase to continue` job error, which is the
  sanctioned `--rebase` recovery prompt.

Disposition argument preserved: zero implementer commits existed at every failure point, so no
work was lost when the R1 nonce branch was retired. A lane WITH commits follows P1-P5 as written.

## Budget escalation evidence (budget-not-correctness)

- Default implementer budget: ~1200 s. Observed: a thinking model on a large issue reaches the
  deadline with clear forward progress (files written, tests added) but no commit+push.
- 5400 s -> timeout with progress; 7200 s -> timeout with progress; 14400 s lanes were still
  running when externally stopped. No correctness defect observed in any transcript; the
  constraint is wall-clock budget.
- Two consecutive timeouts with verified progress on the same issue justify the next doubling;
  a timeout with NO progress suggests a real stall and says to diagnose instead of raising budget.
