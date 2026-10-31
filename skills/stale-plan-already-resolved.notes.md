# Session Notes: stale-plan-already-resolved

## Session Context

- **Date**: 2026-03-15
- **Issue**: ProjectOdyssey #4280 "Update CI Models pattern to use glob for part files"
- **Follow-up from**: #3458 (split test_googlenet_layers.mojo)
- **Branch**: 4280-auto-impl
- **PR created**: #4880

## What Happened

### Plan (from issue comment)

The implementation plan (written before the session started) said:

> **Current State** (verified): The "Models" CI group at line 234 uses `test_*_layers.mojo`

And requested:

> **Line 234**: Change pattern from `test_*_layers.mojo` → `test_*_layers*.mojo`

### Actual State Found

Reading the actual file:

```bash
grep -A3 '"Models"' .github/workflows/comprehensive-tests.yml
```

Output:
```yaml
- name: "Models"
  path: "tests/models"
  pattern: "test_*.mojo"
  continue-on-error: true
```

The pattern was already `test_*.mojo` — broader than even the requested `test_*_layers*.mojo`.
The plan's "before" state (`test_*_layers.mojo`) no longer existed.

### Root Cause of Staleness

The plan was created at a point in time when the Models group used `test_*_layers.mojo`.
Between plan creation and this session, another PR consolidated the pattern to `test_*.mojo`
(verified via `git log --oneline -- .github/workflows/comprehensive-tests.yml`).

### The Part Files

The issue plan also said "no `_partN` files yet — this is proactive prevention" but by the time
of this session, the part files already existed:

```
tests/models/test_googlenet_layers_part1.mojo
tests/models/test_googlenet_layers_part2.mojo
tests/models/test_googlenet_layers_part3.mojo
```

These were created by #3458 (the parent issue).

### Resolution

Since `test_*.mojo` already covers all part files:

1. Updated the YAML comment to explicitly state that `test_*.mojo` auto-discovers `_partN` files
2. Created PR #4880 with `Closes #4280`
3. Ran `python3 scripts/validate_test_coverage.py` — exits 0

### Change Made

```diff
- # test_googlenet_layers.mojo split into 3 parts (≤8 tests each)
+ # test_*.mojo glob auto-discovers all model tests including _partN split files
+ # (e.g., test_googlenet_layers_part1.mojo) without requiring manual CI updates.
```

## Key Diagnostic Commands Used

```bash
# Check if plan's "before" state exists
grep -n "test_\*_layers\.mojo" .github/workflows/comprehensive-tests.yml
# Result: empty → plan is stale

# Read actual current state
grep -A3 '"Models"' .github/workflows/comprehensive-tests.yml

# Check git history to understand when pattern changed
git log --oneline -20 -- .github/workflows/comprehensive-tests.yml

# Verify coverage still passes
python3 scripts/validate_test_coverage.py; echo "Exit: $?"
```

## 2026-10-26 — Relaunched worker found the durable plan eclipsed by a split delivery lane

### Session Context

- A coordinator relaunched a killed single-issue worker with a continue instruction after a
  fleet-wide provider outage.
- The tracked issue carried an actor-owned canonical plan (revision 4, written 8–19 days before)
  and the durable workflow label that the workflow applies only after an approved plan review.
- Ownership gate was clean: no open PR referenced the issue, no assignee, no in-progress label,
  no comment activity in 48 hours, and no worker branch or worktree.

### Evidence gate before any publication or write

The worker ran the workflow state inspection read-only and observed that the durable plan held an
artifact marker but no review-exchange carrier. Before preparing the protocol-mandated re-review,
the worker measured the current default-branch tip:

1. Site check — every symbol and constant that the plan's approach sections cited
   (`git grep '<cited symbol>' origin/main -- <scopes>`) returned zero matches repo-wide. Later
   merges in the same repair campaign had restructured the gate and deleted the machinery.
2. Create-target check — the plan's "files to create" already existed at the tip with the planned
   frozen contract, delivered weeks earlier through a split implementation lane
   (`git show origin/main:<path>`).
3. Modify-target check — the procedure document the plan would edit had been absorbed by another
   merged docs PR, and the shell gate the plan would amend had been reduced by the gate
   restructure.
4. Delivery search — `gh pr list --state merged --search '<issue number>'` surfaced the lane: the
   issue's one prior implementation PR had been closed unmerged by automation recovery, and its
   scope had been delivered across several smaller merged PRs; an open backlog tracker owned the
   remaining items.
5. End-goal check — the issue's terminal outcome (the blocked production delivery sequence) had
   completed: several goal-shaped delivery merges landed, and the latest showed the complete
   required gate set green (`gh pr checks <latest delivery PR>`).

### Outcome

- Disposition: stopped with the task's park report; zero forge writes, zero repository writes, no
  review verdict published over the stale plan. A verdict published from protocol momentum would
  have bound deleted code and contradicted the delivered state.
- The recommendation to close the tracked issue as delivered was routed to the coordinator
  authority; the worker kept within its single-issue scope and did not adopt the adjacent open
  backlog.
- Dedup comparison performed: one canonical entry covers plan/log staleness at fix time; one
  covers the planner's already-shipped check before writing a plan. Neither recorded the resume
  trigger (interruption relaunch plus a durable approval label) or the rule that a review exchange
  must not publish over a stale plan. This entry was amended with those two decision values.

## 2026-10 — Mutation-boundary premise decay on a release train

### Session Context

- **Date**: 2026-10
- **Repository**: external shared repository (unnamed), during an active release train with
  parallel fix workers
- **Trigger**: one captured promotion-gate CI run produced a failure inventory of four
  clusters; the session analyzed and prepared repairs over multiple hours

### What Happened

1. The session analyzed the four failure clusters from the captured run and prepared fixes
   in an isolated worktree pinned to the then-current default-branch tip.
2. From that hours-old analysis — without re-fetching — the session filed two repair issues
   and one tracker edit (a release-epic task list).
3. Before opening the fix PR, the session ran a boundary check (`git fetch`, `gh pr checks`,
   `git log <base>..origin/<default> -- <touched paths>`). The default branch had advanced
   ~30 commits during the session. The merged set contained fix PRs for **all four**
   clusters, including a product commit that repaired the deepest cluster (the same root
   cause the session's strongest probe evidence had established) and a harness commit for
   the flaky cluster. The promotion gate itself had also merged.
4. Outcome: the prepared worktree fixes were superseded and discarded. The pre-push boundary
   check prevented a duplicate PR. It could not prevent the two issues and the tracker edit,
   which were already filed on the decayed premise and needed close-out instead.

### Diagnosis

Premise checks ran at analysis time and at the push boundary, but not at the issue-filing
boundary. The artifact that is cheap to discard (the local branch) received the fresh check;
the artifacts that a human must triage (tracker records) did not. On a fast shared train, an
inventory is valid only at capture time; every outward mutation needs its own re-anchor.

### Boundary-check commands that caught the decay

```bash
git fetch origin <default> --quiet
git log --oneline <analysis-base>..origin/<default> | wc -l      # ~30 while the session ran
git log --oneline <analysis-base>..origin/<default> -- <touched paths>
gh pr checks <gate-PR>                                           # gate state moved meanwhile
git log --oneline <analysis-base>..origin/<default> | grep -iE "<failing node names>"
```

## 2026-10-31 — Stale conflict premise on an open PR head already rebased by sibling sessions

### Session Context

- **Repository**: internal CI-gate repository (unnamed), fast-moving default branch with
  parallel worker sessions
- **Trigger**: a rebase-only task brief stated that an open pull request was conflicting and
  dirty against the default branch and could not merge

### What Happened

1. The worker fetched the default branch and the PR head and measured the premise before
   rebasing. The merge base equaled the current default tip; the head was zero commits
   behind, a local merge test reported clean, and the provider's mergeability status agreed.
2. The PR timeline explained the state: the head had been force-pushed several times after
   the durable approval label was applied, and sibling worker sessions had posted rebase
   completion reports at each new head. The last report covered the task's full reporting
   step (old head, new head, conflict files, behavior change, check status, and the note
   that a head-bound approval does not cover a rewritten head) at the current head.
3. The required checks were green at that head.
4. Outcome: zero writes. No rebase, no push, no duplicate completion comment. The worker
   reported the task-complete disposition with the measured evidence.

### Diagnosis

The task brief's premise was a snapshot. Delivery had happened on the same open PR's head,
not on the default branch, so a merged-PR search and a main-tree site check could not see
it. The PR's own timeline (force-push events plus sibling completion comments) and head
ancestry were the decisive evidence.

### Hazard avoided

Re-running the rebase and re-signing the commits would have produced a new head SHA at
identical content. That would have broken the head-bound approval record and restarted the
review gate for no content change.

### Diagnostics that caught the stale premise

```bash
git fetch origin <default> <pr-branch>
git merge-base origin/<default> origin/<pr-branch>        # equal to the default tip
git rev-list --count origin/<pr-branch>..origin/<default> # 0
git merge-tree --write-tree origin/<default> origin/<pr-branch>  # clean
gh pr view <pr> --json mergeable,mergeStateStatus         # MERGEABLE / CLEAN
gh api repos/<org>/<repo>/issues/<pr>/events \
  --jq '[.[] | select(.event == "head_ref_force_pushed") | .created_at]'
```
