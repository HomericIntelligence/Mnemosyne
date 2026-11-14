---
name: pr-ci-failure-triage-preexisting-vs-introduced
description: "Classify red PR checks as introduced, pre-existing, flaky, environmental, stale-commit, or status-rollup artifacts before fixing or rerunning. Use after rebases/force-pushes, unrelated failures, merge-preview coverage changes, or hosted-only process-launch errors. Also use when the required check is a fan-in gate reported by a ruleset, when the failing symbol on the base was deliberately removed, when a base update turns a green branch red without a textual conflict, when grouped or sharded logs hide individual failed node identities, when failures reproduce only on the local host, or when a path-filtered check fails on stale in-repo plan inputs that main already repaired. Also use when an aggregate gate fails its own report step because a producer job output key is absent from `needs` while every upstream job succeeded. Also use when a green comparison lane may never execute the failing node because event-scoped profiles or shard planners select different test sets on identical trees. Also use when the default branch's CI is red at or immediately after your squash merge and a task gate requires green main CI before you report, or when per-commit run lookups return empty because the branch does not run every push. Also use when only some failing nodes reproduce on a pristine trunk worktree, or when a test fails as an absent exception because a derived identity stopped covering the edited dimension. Also use when a pre-existing classification leaves a follow-up-issue obligation while an aggregate tracker may already own the failing group — dedupe against open trackers before filing. Also use when a rebase or push gate must decide whether a red local run of the change's own test files belongs to the rebased head or reproduces unchanged at the pristine base commit. Also use when a content guard fails with an expected-versus-actual version or constant mismatch that you did not edit, or when your change's own content checks pass but one repository-wide guard fails on an unchanged file. Also use when a second lane drives the identical artifact from the identical prompt and pushes or reruns checks during your session. Also use when a fail-closed guard asserts a stat invariant such as a directory `st_nlink >= 2` and a whole module goes red on this host, because a shared-storage mount can report metadata values a local filesystem cannot produce. Also use when a guard that the branch adds reads a host-bound input such as the local deployment context and refuses a test fixture built to an older shape that passed at the base commit."
category: ci-cd
date: 2026-11-07
version: "2.14.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
tags:
  - ci-failure
  - triage
  - check-runs
  - preexisting
  - concurrency
  - flaky
  - stale-commit
  - merge-preview
  - ruleset
  - fan-in-gate
  - undefined-symbol
  - e2big
  - post-merge-hybrid
  - file-provenance
  - host-window
  - shard-logs
  - paths-filter
  - stale-plan-inputs
  - evidence-artifact
  - job-outputs
  - test-profile-selection
  - green-twin-coverage
  - post-merge-main-red
  - sparse-workflow-runs
  - partial-reproduction
  - fixture-identity-collision
  - follow-up-tracker-dedupe
  - rebase-attribution
  - local-red-main-green
  - stale-version-pin
  - content-guard-mismatch
  - unedited-file-failure
  - mount-reported-metadata
  - impossible-stat-value
  - directory-nlink
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-ci-failure-triage-preexisting-vs-introduced.history"
history-cleanup-date: "2026-09-20"
---

# PR CI Failure Triage: Pre-Existing vs Introduced

## Overview

Classify each failing check against the PR's current head and current main before changing code.
A PR rollup can show cancelled runs from an old SHA; an unrelated-looking failure can still be
introduced; and main can be genuinely broken. Evidence determines whether to fix in scope, rerun a
known flake, repair main separately, or create an explicit follow-up.

This workflow is verified in CI across the indexed cases. Detailed run links and edge cases are in
[pr-ci-failure-triage-preexisting-vs-introduced.notes.md](pr-ci-failure-triage-preexisting-vs-introduced.notes.md),
and the complete prior version is in
[pr-ci-failure-triage-preexisting-vs-introduced.history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pr-ci-failure-triage-preexisting-vs-introduced.history).

## When to Use

- Required checks are red and scope ownership is unclear.
- A force-push or rerun left cancelled/superseded runs in the PR rollup.
- The failing job appears unrelated to the diff.
- A crash signature looks flaky or infrastructure-specific.
- Coverage measures a synthetic merge tree rather than the feature branch alone.
- A stacked/rebased PR needs fresh checks without a code change.
- Several sanitizers fail identically after a rebase.
- CodeQL and validation fail for different reasons.
- Tests depend on host filesystem auto-detection.
- Hosted Linux raises `E2BIG` before a generated `node -e` harness starts.
- Checks go red only after a base update merged current main into the branch, while main's own CI is green.
- Shard or grouped step output fails without listing the individual `FAILED` node identities.
- Tests fail on the local host but pass on the hosted runners.
- The failing workflow is path-filtered (`on.pull_request.paths`), so it is absent from
  main's run history and from PRs whose diffs stay outside the filter — and a check with
  pinned in-repo plan inputs (a fixed selector or case list) dies before any test count
  with a usage-style error.
- A required aggregate gate fails in its own report or summary step because an upstream
  job output key is absent from `needs.<job>.outputs`, while the producer job and every
  other upstream concluded success — and re-running the gate or the producer job inside
  the same run does not restore the key.
- The green comparison lanes may never execute the failing node: event-scoped test
  profiles or shard planners select different sets on identical trees.
- Your squash merge just landed on the default branch, the branch's CI is red at or
  after your merge commit, and a task gate requires green main CI before you report —
  so you must decide whether your merge caused the red before you adopt the repair.
- A per-commit workflow-run lookup returns empty for the merge commit or its boundary
  commits because the default branch does not get a run at every push.
- A module fails on both trunk and the branch, but with different failing counts, so a
  set-level "also fails on main" statement hides branch-introduced nodes.
- A test fails as an absent exception rather than a wrong value, because a derived
  identity no longer covers the dimension its fixture edits.
- Your triage classifies red as pre-existing and a scope rule forbids the repair,
  leaving a follow-up-issue obligation, while an aggregate tracker may already record
  the same failing group.
- You resolved a rebase and must decide whether the touched test files pass before
  a gated push, but the same files fail identically at the pristine base commit on
  this host while the hosted checks are green. The failure set then gates neither
  head, and every delta belongs to the reviewed resolution.
- A fail-closed guard asserts a stat invariant (`st_nlink >= 2` on a directory) and a whole
  module goes red on this host, so you suspect the tests before the mount.
- A guard that the branch adds reads a host-bound input, such as the local deployment context,
  and refuses a test fixture built to an older shape that the same node accepted at the base
  commit.

## Verified Workflow

### 1. Bind every observation to a SHA

```bash
PR_JSON=$(gh pr view "$PR" --repo "$REPO" --json headRefOid,baseRefOid,url)
PR_HEAD=$(printf '%s' "$PR_JSON" | jq -r .headRefOid)
MAIN_HEAD=$(gh api "repos/$REPO/commits/main" --jq .sha)
printf 'pr=%s main=%s\n' "$PR_HEAD" "$MAIN_HEAD"
```

Do not rely on a cached browser rollup or run from a rebased-out commit. Re-read after any push.
Avoid environment tokens that shadow the authenticated GitHub CLI identity.

### 2. Inspect check runs for exact commits

```bash
gh api "repos/$REPO/commits/$PR_HEAD/check-runs" \
  --jq '.check_runs[] | [.name,.status,.conclusion,.details_url] | @tsv'
gh api "repos/$REPO/commits/$MAIN_HEAD/check-runs" \
  --jq '.check_runs[] | [.name,.status,.conclusion,.details_url] | @tsv'
```

Classify per check name and workflow:

| PR head | Main head | Initial class |
| --- | --- | --- |
| Fails | Passes | PR-introduced or merge interaction |
| Fails identically | Fails | Pre-existing/systemic candidate |
| Cancelled/superseded | Current head has newer run | Rollup artifact |
| New check only on PR | No main run | New-check; inspect policy and merge preview |
| Fails; sibling PRs on the same base show no run | No main run; workflow is path-filtered and the diff touches the filter | Trigger-scoped failure; classify from the check's inputs, not from run history |
| Intermittent signature | Main/PR history mixed | Flake/infrastructure candidate |

“Unrelated diff” is supporting context, not classification evidence. A path filter can
empty the comparison set entirely: when the workflow only runs for diffs that touch its
`paths:` list, neither main nor unaffected PRs carry any run for these inputs, so the
absence of a main failure is expected and says nothing about ownership.

### 3. Filter cancelled and stale runs

List workflow runs with `head_sha`, event, attempt, status, and conclusion. A concurrency group can
cancel an in-flight rerun when a newer run starts. Only the newest applicable run for the current
head should influence resolution.

Use the check-runs API for authoritative status. `gh pr checks --json` supports a narrow field set;
do not assume it exposes arbitrary run metadata.

### 4. Compare workflow history on main

Inspect several recent main runs for the same workflow. One failed main run can be transient; a
repeated identical failure establishes systemic rot more strongly. Compare logs, runner image,
dependency versions, and failing test IDs.

If the required job evaluates a merge-preview commit, reproduce that tree or use GitHub's merge
commit SHA. A coverage drop can arise from interaction with main even when the branch-alone suite
passes.

Before a green run counts as comparison evidence, confirm the run executed the failing node.
Event-scoped test profiles (a narrower pull-request profile and a wider promotion profile) or
shard planners can select different test sets on identical trees. When every green lane in the
comparison ran only a profile that never selects the node, the comparison is empty: it classifies
nothing. Check coverage by searching each compared run's logs for the failing node id
(`gh run view --job <job> --log`), or by comparing the selected-test counts the harness prints.
Classify an empty comparison from content determinism — the assertion, the config, the diff —
not from lane color.

### 5. Classify known failure signatures before rerunning

- Compiler/JIT crash or SIGABRT with identical historical flakes: infrastructure candidate; capture
  signature and recurrence first.
- All sanitizer jobs fail on the same unexpected feature: inspect branch history for a stale
  duplicate commit already represented on main.
- CI-only path discovery: replace ambient filesystem probing with explicit deterministic inputs.
- `E2BIG` before Node logs appear: `execve` rejected argument/environment size; Node code never ran.
- Path-filtered check whose plan inputs are pinned in-repo (a fixed selector, node list, or
  case file): a rename or removal on main makes those inputs stale, and every base that
  predates the input repair fails with an exit before any test count. Diff the pinned input
  against the current tree — `git log -S <missing-selector> -- <input-file>` names the
  change that renamed it, and `git log -1 --format=%H origin/main -- <input-file>` shows
  whether current main already carries a corrected input. When the failure log collapses to
  one usage-style line, download the job's uploaded evidence artifacts; the harness's
  selection or execution record usually names the collected-vs-selected mismatch directly:

  ```bash
  gh run download <failed-run-id> -n <evidence-artifact-name>
  ```

- Content guard whose expected value is a literal in the test and whose actual value comes from the
  tree: a mismatch on a version, constant, or count that your diff never touched is a stale pin.
  A version-bump merge that did not update the literal reds the default branch from that merge on.
  Bracket it before touching the guard: a run at the bump commit's parent is green, runs at the
  bump commit and at every later base are red, and the literal's history shows no change since the
  pin was written. The difference between a stale pin and a regression is only whether the
  asserted expected value moved with the tree.

- Aggregate gate fails its own report step on a `needs.<job>.outputs` key that is absent
  while every upstream job succeeded: attribute the dropped producer output before any
  rerun. Re-execution inside the same run inherits stored job outputs, so a rerun cannot
  repair a propagation drop.

An aggregate gate usually reads its inputs through `toJSON(needs.<producer>.outputs)`. When
that map lacks a key the producer demonstrably wrote — the producer job concluded success
and its log shows the emit step writing the value — the source tree is not the cause.
Attribute the drop in this order:

1. Producer provenance: the producer job succeeded and its emit step logged the value. The
   output existed at job level; the failure is downstream propagation.
2. Window bracket: find a same-era green run of the same workflow whose gate consumed the
   present key (another branch, or main before the first failure). A cohort with the key
   present at time T1 and absent from a set of later runs at T2 isolates a platform-side
   window or behavior change. It does not name a product defect.
3. Re-execution identity: do not repair by rerunning jobs inside the same run. Each job
   rerun in one run inherits the run's stored job outputs — even when the producer job
   re-executes. Only a fresh run ID (close and reopen the PR, or a new push) regenerates
   the stored outputs. Verify with a fresh run before you accept a repair theory.
4. Fresh-run reproduction classifies the failure: if the identical key stays absent in a
   fresh run, the first cause is a platform behavior change, and the old gate contract
   can fail for every old-world run from then on. Resolve by a recorded base update when
   current main already carries a workflow that does not depend on the dropped output, or
   by changing the workflow contract. Record the platform evidence with the base-update
   record. Do not patch the PR's files to mask a gate the platform can no longer satisfy.

For generated harnesses, stream code over stdin instead of `node -e <large-script>`:

```python
subprocess.run(
    ["node"],
    input=generated_javascript,
    text=True,
    capture_output=True,
    check=False,
)
```

Test with realistic large payloads on hosted Linux; local `ARG_MAX` and environment size differ.

### 6. Attribute post-base-update failures by file provenance

A base update that merges current main into the branch can turn a green branch red without a
textual conflict. Before you change code, establish which parent owns each side of the failing
content:

```bash
OLD_BASE=<recorded-previous-base>
PRE_UPDATE=<branch-head-before-the-update>
git diff "$OLD_BASE"..HEAD -- <failing-test-file>
git diff "$OLD_BASE"..HEAD -- <subject-source-files>
git diff "$OLD_BASE".."$PRE_UPDATE" -- <subject-source-files>
```

| Evidence | Class | Action |
| --- | --- | --- |
| Test file carries branch-only deltas, subject source is identical to trunk, and the branch never carried companion source | Stale branch assertion against current trunk semantics | Port the test's intent onto trunk's semantics; retire it when trunk supersedes the coverage |
| The update took one half of a lockstep pair, such as a workflow and the script that consumes its output, from different eras | Half-moved pair | Move the pair atomically to all-old or all-new, then rerun the pair's own checks |
| Subject source carries branch deltas and reverting them removes the failure | Genuine PR regression | Fix minimally in scope |
| The same nodes fail set-identically on a pristine trunk worktree on this host, and trunk CI is green | Host/environment window | Report FYI with the reproduction evidence; do not patch the PR for it |
| The identical failing node set reproduces at the pristine base commit on this host while hosted CI is green, and a gated mutation (push, merge, delivery) must proceed | Environment-attributed pass-through | Record the per-file failure-set equality and the representative root cause, then proceed without weakening any check. The gate proves that the resolution adds no failure, not that the host is green |
| The host root cause is a metadata value that a local filesystem cannot produce, such as a directory `st_nlink` that stays at `1` after gaining a child, and a guard asserts `st_nlink >= 2` | Mount-reported metadata | Prove it with one directory probe, record the probe output beside the failure-set equality, and keep the guard unchanged. Do not relax the assertion to accept the mount |
| The host root cause is a fail-closed trust check on an ancestor path, and one configuration value (for example the temp root) can reach it | Fail-closed navigation | Relocate that value to a compliant location and rerun the identical commands on both heads. Adjudicate the failure set when navigation is unavailable or slower than proving equality; keep the value pinned and recorded |
| Only some of the failing nodes reproduce on a pristine trunk worktree; the rest pass there | Mixed attribution: the reproducing nodes are pre-existing, the others are branch-introduced | Split the failure set per node. Repair the branch-introduced nodes; report the reproducing nodes with their counts and do not fold them into one "fails on trunk" claim |
| The asserted failure is an absent exception or a no-op, and the guard that should raise now compares equal because a mid-stream change removed the changed dimension from a derived identity | Fixture identity collision | Repair the fixture so it still distinguishes the two sides on the dimension the guard now reads, and assert the invariant the guard protects — not the label the old identity model produced |
| A guard that the branch adds reads a host-bound input, such as the local deployment context, and refuses a test fixture built to an older, narrower shape; the same node passes at the pristine base commit and the refused value is one the production configuration really requires | Fixture drifts behind a newly context-dependent guard | Keep the guard and repair the fixture to the shape the host-bound input admits. Confirm the production configuration carries the refused value before you choose this class. If it does not, the guard is over-strict and belongs on the narrower surface instead. Either way, add a success node for the accepted shape: the refusal node alone passes without the repair, so it does not pin the regression |

Keep one pristine worktree at the recorded base with a synced environment as the attribution
oracle. A failure that reproduces there is not introduced by the branch. When the failure involves
filesystem ownership, modes, or ACL semantics, prefer the hosted-runner result: a local mount can
force modes, mask ACL behavior, or change user identity, so chmod-based assumptions can fail in
either direction.

A shared-storage mount can also report metadata values that a local filesystem cannot produce. The
common shape is a directory `st_nlink` that stays at `1` after the directory gains a child, where a
local POSIX filesystem reports `2`. Code that asserts the invariant (`st_nlink >= 2`, or a
same-object guard that rejects `links < 2`) then fails closed on a tree that is correct. A whole
module can go red from this one cause, because every test that creates a directory hits it.

Recognize it before you debug the tests:

```bash
D=$(mktemp -d); mkdir -p "$D/parent/child"
stat -c '%n nlink=%h' "$D/parent"     # local fs: 2; the reported shape: 1
```

One command separates the two classes. When the probe reports `1`, the failure is environmental and
no branch change can fix it. Every failing node shares the metadata signature, and the same set
fails at the pristine base. Do not weaken the assertion and do not rewrite the guard to accept the
mount: the check is correct, and hosted CI on a native filesystem is the authority. Record the probe
output, the per-file failure-set equality, and the hosted result in the PR, then proceed. This is the
pass-through case, not a pass.

The reverse also holds. When the probe reports `2` and the guard still fails closed, the cause is a
real identity change, and the guard is doing its job. Distinguish the two by the probe, not by the
error label; both produce the same `directory_identity`-style message.

When you design the guard rather than triage it, `directory-identity-check-stable-stat-fields`
covers which stat fields are safe to compare.

A rebase gate is one application of the oracle. After the rebase, the touched test files can be red
only in this checkout. Before the push, compare the failing node sets of both heads under one
environment pin:

```bash
git log --oneline <base>..HEAD            # the replayed commits
echo <owner-only-scratch-root>            # one TMPDIR value for both runs; satisfies a refused check
git worktree add --detach <base-worktree> <base>
# run the same test command on the touched files in each tree, then:
grep -E '^(FAILED|ERROR)' <base-log> | sort > base.txt
grep -E '^(FAILED|ERROR)' <head-log> | sort > head.txt
diff base.txt head.txt                    # empty means the sets are equal per file
```

An empty delta with hosted CI green is environment-attributed. Any surplus node is
branch-introduced. Report the counts per file, the representative root cause, and the pin. Do not
repair the phantom set, and do not call the red set green.

Claim reproduction per node, never for a set. Run the same module in both worktrees and compare the
node identities, then count each side:

```bash
(cd "$PRISTINE_WORKTREE" && pytest <module> -q) | tail -1   # e.g. 1 failed, 52 passed
(cd "$BRANCH_WORKTREE"   && pytest <module> -q) | tail -1   # e.g. 10 failed, 44 passed
```

A smaller failing count on trunk means the surplus belongs to the branch, even when the module
fails on both sides. A set-level statement such as "these tests also fail on main" is true for one
node and false for the other eight, so it silently under-attributes the branch. State the two counts
and the per-node split.

A derived identity that stops covering a dimension breaks fixtures in a specific way. When a guard
compares identities and the newer identity model no longer includes the edited dimension, two
fixtures that used to differ now compare equal, the guard returns early, and the test fails as an
absent exception rather than a wrong value. Confirm the collision before you touch assertions:

```bash
python3 -c "import sys; sys.path.insert(0,'tests')
from <fixture_module> import <builder>
a, b = <builder>(...old...), <builder>(...new...)
print('same identity:', <identity_attr>(a) == <identity_attr>(b))"
```

If they are equal, the fixture is no longer describing two distinct states. Change the fixture to
edit a dimension the identity still covers, and re-express the assertion in terms of the invariant
the guard exists to protect. Do not rewrite the assertion to match whatever the early return now
produces: that converts a lost test into a passing test that proves nothing.

Diagnose from the failing node identity, not from a shard or step summary. Grouped step output can
withhold individual `FAILED` lines until the job ends, and sharding splits the parametrized cases
of one test across jobs, so any single job under-reports the failing set. Wait for the job to end,
then extract node identities:

```bash
gh run view --job <JOB_ID> --log-failed
```

An exit before any test count, for example a pytest usage exit with zero reported tests, names a
plan-stage failure: missing planner input, collection error, or workflow rejection. Read its first
error line directly instead of guessing from the shard list.

### 7. Inspect branch content for stale duplicate commits

```bash
git log --oneline --decorate origin/main..HEAD
git diff --stat origin/main...HEAD
git cherry -v origin/main HEAD
```

If a stale commit duplicates a fix already on main, rebuild the branch from current main with only
the real payload. Do not amend an arbitrary tip when the unwanted commit is lower in history.

### 8. Resolve according to evidence

- PR-introduced: fix within scope and add regression coverage.
- Merge interaction: rebase/update, reproduce merge preview, and fix the interaction.
- Confirmed flake: rerun only failed jobs after recording the signature.
- Pre-existing required failure: fix main separately when practical; otherwise use only an
  explicitly authorized governance path and file a linked tracking issue.
- Concurrent writer on the same artifact: when a second lane drives the
  identical task on the identical pull request, and that lane pushes, reruns
  checks, or publishes review rounds during your session, do not write. The
  shared head moves under you, your check reads go stale on each push, and both
  lanes repair the same reds. Ask the requester to name one owner, and until
  then stay read-only and let the active writer finish (Section 9.3).
- Trigger-scoped stale-plan-input failure already repaired on current main: take a base
  update under the repository's task-base policy (record the reason plus old and new base
  and head commits, then rebind verification to the new head). Do not patch the PR's own
  files to mask a check that main already fixed.
- Pre-existing stale-pin guard failure on an unedited file: do not edit the expected value to reach
  green. The literal belongs to the merge that moved the tree, and a narrow-scoped lane that
  rewrites it hides the defect and expands scope. Record the bracket evidence in the PR, name the
  owning change, and keep the disposition on the strength of the change's own passing checks. Edit
  the literal only when the pin is in your write allowlist and the task owns it.
- Rollup artifact: no code change; wait for/read the current-head run.
- New-check failure: fix the check or product contract; do not compare it to a nonexistent main run.

After any fix/rebase, repeat SHA and check-run binding. Surface classification and evidence in the
PR, not only stderr or a private note.

### 9. Attribute post-merge main red by a merge-sha bracket

The default branch's CI can be red at or immediately after a clean squash merge even
when every PR check was green: the first red run can predate the merge (a broken main
that swallowed your commit), and a gate that requires watching main CI to green then
tempts you to adopt a repair that another lane owns. Bracket before attributing.

Default-branch workflows can be sparse: the branch does not get a run at every push,
and a merge's own run can appear seconds after the merge push. A per-commit run lookup
(`gh run list --commit <sha>`) can therefore return empty for the merge commit and for
its boundary commits. Enumerate by branch and map the run head SHAs onto history order:

```bash
gh run list --branch main --workflow <WF> --limit 60 \
  --json databaseId,headSha,status,conclusion,createdAt \
  --jq '.[] | select(.conclusion=="success" or .conclusion=="failure")
        | "\(.headSha[0:10]) \(.conclusion) \(.createdAt)"'
git log --oneline -20 origin/main
```

- Bracket the merge commit: the newest green run and the oldest red run on the branch.
  A first red whose commit is an ancestor of the merge — including the merge's direct
  parent — predates it; main was already broken.
- Collate the failing node identities across a sample of failed jobs
  (`gh api repos/<user>/<repo>/actions/jobs/<job-id>/logs`, keep the `FAILED` lines).
  One module failing set-identically in the pre-merge red run, the merge's own run, and
  the current tip run is a pre-existing failure line, not spread from your patch.
- Compare the failing set against your patch surface. A set disjoint from every file
  your merge touched is supporting context only; the bracket and the identical
  pre-merge signature are the attribution evidence.

| Evidence | Class | Action |
| --- | --- | --- |
| First red commit is an ancestor of the merge; the failing node set is identical before and after | Pre-existing main breakage | Do not adopt the repair inside your delivery scope; record the bracket, the node set, and the owning fix when it lands; report attribution |
| First red is your merge commit and its failing nodes intersect your patch surface | Merge-introduced | Check out a worktree, diagnose from the failing-node evidence, deliver a repair PR |
| No run exists at the merge commit or its boundary commits | Sparse coverage | Classify from the run bracket around the gap; never treat a missing run as green |
| The failing group classifies as pre-existing breakage outside delivery scope, and a scope rule obliges a follow-up issue | Follow-up tracking obligation | Search open issues for an aggregate tracker (a train-red or umbrella issue) whose body or ledger comments already name the failing run or group; when an owner exists, record the bracket, the node set, and the tracker reference in the report and do not file; file a new issue only when no open record owns the group |

Under a "watch main CI green" gate with pre-existing breakage, the owning lane usually
lands a repair commit at a newer tip (a fix naming the failing area). Watch that tip's
run to green and record its identifier as the gate evidence; the green belongs to the
repair, not to your patch.

### 9.3 Wait out a concurrent writer on the same artifact

A task can reach two agent sessions at the same time: one session is asked to
fix the red checks on a pull request while another session drives the same pull
request, or two lanes are dispatched to the same issue. The symptoms are:

- the default branch advances while you work: `git log --oneline <your-base>..origin/main`
  gains commits that name the same failing nodes;
- the pull request head changes under you: pushes land while you inspect;
- checks re-run for heads you have not seen: the same workflow name appears
  repeatedly at increasing timestamps;
- a review has not been published yet, but runs and pushes keep coming.

Do not compete with the active writer. Do not start a worktree, do not fix the
same nodes, and do not publish a review round, a comment, or a label. Your
check reads go stale on each push, and both lanes repair one red set.

Confirm the instruction with the requester. Give the three states:

- **wait**: the attended session stays read-only and rechecks at long
  intervals (tens of minutes), then takes the remainder when the writer goes
  quiet;
- **proceed anyway**: the session starts work at once, knowing the other
  session may publish against a stale head;
- **safe parts only**: the session does the PR-side no-code work (an approval
  marker on the pull-request body, a classification report) and changes no
  source.

When the requester picks "wait", watch for quiet with a cadence that changes
with the signal, and record what you observed:

- one quiet observation, for example a single unchanged `main` tip, does not
  prove the other lane is finished;
- a tip that held unchanged for 25 minutes on three successive occasions, with
  a push on the fourth, showed that a quiet window in an active session is not
  exhaustion;
- a lane that pushes every 10 to 30 minutes can be silent for 15 to 20 minutes
  without being finished.

A robust quiet test needs a long window and two signals, not one. Require
about 45 minutes with both signals unchanged:

- `gh api repos/<user>/<repo>/commits?sha=main&per_page=1 --jq '.[0].sha'`
  (the default-branch tip), and
- `gh api repos/<user>/<repo>/pulls/<N>/reviews?per_page=100 --jq 'length'`
  (the count of published reviews on the pull request under review).

Sample every few minutes by default and less often (for example every 15
minutes) while a lane is still active. Guard the sample with a short timeout,
because the forge read can hang:

```bash
while :; do
  rev=$(timeout 60 gh api repos/<user>/<repo>/commits?sha=main&per_page=1 --jq '.[0].sha' 2>/dev/null)
  rn=$(timeout 60 gh api repos/<user>/<repo>/pulls/<N>/reviews?per_page=100 --jq 'length' 2>/dev/null)
  cur="${rev:0:8}:$rn"
  if [ "$cur" = "$last" ]; then stable=$((stable+1)); else stable=0; fi
  last="$cur"
  [ "$stable" -ge 45 ] && { echo "IDLE after 45 quiet minutes: $cur"; break; }
  sleep 60
done
```

After the quiet window, rebind everything before you act:

1. Read the current pull request head. Any diagnosis, failing-node list, or
   artifact binding you made against an older head is stale.
2. Re-run the failure collection for the new head. The overlap is partial:
   fixes land in waves, so most of your earlier list is already closed and a
   few nodes remain.
3. Check the remaining reds against open work: search open pull requests by
   title and issue labels, and check open issues for a tracker that already
   owns the group before you file one.
4. Verify whether the artifact already merged while you waited. If it did,
   stop: a merged target needs no review round, comment, or label, and a later
   verification read of one that merged is a report of the delivered state,
   not new work. See `pr-drive-stop-on-already-merged.md`.

Note the limit of this rule. It does not replace the workflow that binds one
review publisher per round. Two terminals published a few seconds apart fork
the review history, and the correct repair is a supersession, not silence;
see `agents-pr-review-forked-terminal-verdict-supersession.md`.

### Guidance retained from an absorbed history

Distinguish a workflow setup failure from a product failure before replacing a
CI action. Inspect the selected action or hook revision and reproduce its actual
invocation. An old failure at one version does not establish a permanent ban on
that action or on commit-based pins. Preserve required-check coverage when changing
the tool invocation.

History cleanup: 2026-09-20. The [prior source](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/ci-cd-pipeline-maintenance-patterns.history)
retains its original evidence limits. This migration does not establish new
operational verification.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Trust `PREEXISTING_CI_NOISE` label | Prior sweeps found many labels wrong | Query exact PR/main check runs |
| 2 | Treat unrelated diff as proof | Dependency, merge, and policy interactions cross file scope | Use SHA-bound execution evidence |
| 3 | Count cancelled old-SHA runs as failures | Force-push/concurrency superseded them | Filter by current head and newest applicable run |
| 4 | Rerun before classifying | New run can hide signature or cancel another run | Capture logs/history first |
| 5 | Assume one failed main run proves rot | It may be a transient flake | Inspect repeated main history |
| 6 | Amend tip to remove stale lower commit | Wrong commit remains in branch | Rebuild/cherry-pick real payload onto current main |
| 7 | Debug generated Node program after `E2BIG` | Kernel rejected argv before Node started | Send harness through stdin |
| 8 | Test CI path auto-detection only locally | Host layout differs | Inject explicit paths and test missing/ambiguous cases |
| 9 | Satisfied a stale branch assertion by changing source after a base update | The update had taken trunk's source while the branch's test asserted semantics trunk had deliberately retired | Diff test and subject source against the old base; port the test's intent onto trunk semantics |
| 10 | Diagnosed the failing set from shard and step summaries | Grouped logs and parametrized splits withheld node identities; the visible rows were not the complete set | Wait for job end; extract `FAILED` nodes with `gh run view --job <job> --log-failed` |
| 11 | Took trunk's half of a lockstep workflow/validator pair during conflict resolution | The surviving branch half rejected every trunk-shaped evidence on prefix checks | Move producer/consumer halves atomically; rerun the pair's own checks |
| 12 | Treated a local-only failure as a PR defect | The same nodes failed set-identically on a pristine trunk worktree; hosted CI was green | Bind local failures to the pristine-base oracle before attribution |
| 13 | Classified a path-filtered check from main's history alone | The workflow runs only for diffs that touch its `paths:` list, so main carried no failure and same-base unaffected PRs carried no run at all — the comparison set was empty while a stale pinned selector made every filtered base fail | Check the workflow's trigger filter first; for in-repo plan inputs, diff the pinned selector against the tree and read the job's uploaded evidence artifacts, then remediate a main-repaired input by a base update |
| 14 | Re-ran the failed aggregate gate, then re-ran the producer job, to republish a `needs` output key the gate missed | The same key stayed absent in every attempt of the same run; job reruns inherit the run's stored job outputs even when the producer re-executes | Capture the producer's emit evidence and bracket a same-era green-run window first; regenerate stored outputs only through a fresh run ID, and when the drop persists there, treat it as a platform behavior change and move the branch to the gate world main already carries |
| 15 | Declared a deterministic introduced failure flaky because green twins carried an identical tree | Every green lane ran an event-scoped profile that never selected the failing node; only the failing wider-profile lane executed it | A green lane is comparison evidence only after its logs contain the failing node id or its selected-test count covers the node's profile; classify empty comparisons from content determinism |
| 16 | Treated red main CI right after the merge as merge-caused and prepared a repair inside the delivery scope | The branch's workflow runs were sparse: a per-commit run query returned empty for the merge commit and hid that the first red run predated the merge by several commits, and every sampled failed job carried an identical node set in one module disjoint from the patch | Enumerate runs by branch and bracket the merge commit before attributing; compare the failing node set across the pre-merge red, the merge's run, and the tip; never treat a missing run as green, and do not adopt pre-existing breakage another lane owns |
| 17 | Prepared a new issue for a classified pre-existing failure without checking open trackers | An aggregate tracker already listed the same validation run and failing group in its curated ledger; a duplicate would have raced the owning lane's record and split one failure line across two owners | Before filing a classified pre-existing failure, search open issues by the failing node or module and by tracker keywords; when a ledger already owns the group, reference it in the report and file nothing |
| 18 | Re-ran a touched test file to confirm a rebase, hit a fail-closed ancestor-path refusal in every test that created a temp tree, and treated the red file as a mergeability blocker | The same refusal reproduces at the pristine base commit on this host. The failure set was equal for the touched files, so the rebased head added no failure, and the refusal never reaches the hosted checks | Before the push, run the touched files on a pristine base worktree under one environment pin. An equal failure set with green hosted CI is pass-through evidence. When one configuration value controls the refusal, navigate it and rerun both heads instead of adjudicating each node |
| 19 | Read a `directory_identity` failure on a large module as a defect and started to debug which tests were wrong | A shared-storage mount reported `st_nlink=1` for a directory that held a child, so every fail-closed `st_nlink >= 2` guard rejected a correct tree; the same set failed at the pristine base and hosted CI was green | Probe the mount with one `mkdir` plus `stat` before reading any test. The probe separates mount-reported metadata from a real identity change, which produce the same error message |

## Results & Parameters

- Authoritative identity: exact PR head and current main head SHAs.
- Primary status source: check-runs API per commit; workflow history supplies recurrence evidence.
- Green-twin coverage gate: a compared green run is evidence only if its log contains the
  failing node id, or a selected-test count covering the node's profile.
- Rerun policy: failed jobs only, and only after a flake classification is recorded.
- Generated harness transport: stdin for large scripts; avoid platform-dependent argv budgets.
- Final gate: current-head required checks, not cancelled or stale runs.
- Resolution record: check name, PR/main result, log signature, classification, action, and linked
  issue/repair when outside scope.
- Post-update provenance diffs: old base to head for the failing test and its subject source, plus
  old base to the pre-update branch head to detect companion source the update dropped.
- Attribution oracle: one pristine worktree at the recorded base with a synced environment.
- Node identity: `gh run view --job <JOB_ID> --log-failed` after the job ends; shard and step
  summaries are not exhaustive. An exit before any test count is a plan-stage signature, not a
  test verdict.
- Trigger audit for a red check with no main history: read the workflow's `on:` block for a
  `paths:` filter before comparing runs; classify from the check's pinned inputs and its
  uploaded evidence artifacts (`gh run download <run-id> -n <evidence-name>`), not from an
  empty run comparison.
- Main-repaired stale input: `git log -1 origin/main -- <input-file>` differing from the
  base copy means current main may already carry the repair; remediate by a recorded base
  update, not by PR-side workarounds.
- Dropped producer output attribution order: producer emit evidence, same-era green-run
  window bracket, rerun-inheritance rule, fresh-run reproduction verdict.
- Fresh-run regeneration: job reruns inside one Actions run share stored job outputs; a
  close/reopen cycle or a new push assigns a fresh run ID and regenerates them.
- Platform-change resolution: an identical output drop that persists in a fresh run
  classifies as a platform behavior change; remediate by a recorded base update to the
  workflow world current main carries, or by a workflow contract change.
- Merge-sha run bracket: enumerate default-branch workflow runs by branch with head SHA,
  conclusion, and creation time; per-commit run lookups are sparse and a run can post
  seconds after the merge push. An oldest red commit that is an ancestor of the merge
  predates it.
- Post-merge collated node set: identical `FAILED` identities across the pre-merge red,
  the merge's own run, and the current tip, disjoint from the patch surface, is a
  pre-existing failure line; patch-surface disjointness is supporting context only.
- Adoption boundary: pre-existing breakage another lane owns stays outside the delivery
  scope; a newer-tip green run after an owning repair commit discharges a
  watch-to-green gate, recorded as the repair's evidence rather than your patch's.
- Rebase gate evidence: the per-file failure sets of the base and head runs under one
  pin, an empty delta, the representative root cause, and the hosted CI state. The
  gate result is "no added failure", not "green".
- Navigation rule: when one configuration value controls a fail-closed refusal, move
  that value and rerun both heads instead of adjudicating each node; record the value.
- Mount metadata probe: `mkdir -p D/parent/child; stat -c '%n nlink=%h' D/parent`. A value
  of `1` classifies the failure as mount-reported metadata; `2` keeps it a real identity change.
  Record the probe output with the failure-set equality.
- Concurrent-writer quiet test: two signals must hold unchanged for about 45 minutes
  before you treat a second lane as finished. The default-branch tip alone is
  insufficient, and a 25-minute quiet window is not; the other lane pushed one
  minute after the third such window in one observed session.

## Evidence Boundary

The decision method is CI-verified across the indexed GitHub cases. Exact administrative options,
required-check policy, runner limits, and merge-preview behavior are repository-specific; inspect
live rules and current runs before acting.
