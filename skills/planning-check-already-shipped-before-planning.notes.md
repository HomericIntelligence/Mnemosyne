# Notes: Check If Work Already Shipped Before Planning

Supporting evidence for
[`planning-check-already-shipped-before-planning`](./planning-check-already-shipped-before-planning.md).
The exact prior skill is archived in
[history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/planning-check-already-shipped-before-planning.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Merged fix discovered before replanning (issue #1291 / PR #1308) | [immutable source at the #3335 base](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-ci | Kept merged-PR and main-content verification rule |
| Uncommitted sibling-worktree implementation (issue #1357) | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-local | Kept worktree inventory and subset-versus-full-gate boundary |
| Large extraction already delivered under another ADR | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-local | Kept destination/source/residual/build acceptance mapping; cross-repo CI remained unverified |
| Retrospective plan rejected | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-local | Kept forward-looking closeout requirement |
| Placeholder plan while tests ran | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-local | Kept complete-at-handoff artifact rule |
| False “foreign WIP” provenance claim | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-check-already-shipped-before-planning.md) | verified-local | Kept independent source/wiring provenance commands |

## Case Details

### Merged and worktree-only implementations

The merged-fix case used issue/PR search, main-branch source inspection, and tests to avoid duplicate
implementation. A separate case showed why this is insufficient by itself: the requested behavior
already existed in an uncommitted sibling worktree, so ordinary `git log` on main showed nothing.
The durable sequence is repository sync, worktree/status inventory, symbol search, and then tests.

### Extraction epic already delivered

The case checked target source presence, source-repository directory absence, residual symbol hits,
and build/test labels. The issue's earlier LOC estimate did not match landed counts. Some paths were
feature-guarded and sibling-repository claims rested on a local checkout rather than hosted CI.
Those boundaries are why the canonical skill requires criterion-by-criterion evidence and does not
promote a local sibling build to cross-repository CI proof.

### Plan-review failures

One artifact accurately described shipped work but contained no future actors or gates, so it was a
status report rather than an implementation plan. A subsequent artifact withheld content while a
background process ran, making the delivered plan effectively empty. The correction is to emit the
complete known plan and label a pending command honestly.

In the provenance case, three test failures were called foreign because the `.cpp` files were
untracked. The current worktree's `CMakeLists.txt` was modified to wire them into the build, so the
premise was false even if the final scope decision could still be defensible. Source provenance and
build-wiring provenance must be checked separately.

## Compaction Disposition

- Kept in main: cheap premise checks, immutable-base evidence, worktree discovery, acceptance
  mapping, provenance, closeout planning, cross-repo separation, and count consistency.
- Moved here: case sequence, old counts, review outcomes, and evidence limitations.
- Archived only: full transcripts, path inventories, and superseded wording.

## 2026-10-31: Fixed-elsewhere detection at claim time

- Context: an unassigned bug issue in a release milestone carried report-time evidence (cited
  module, line number, and a timeout traceback) and a plan-issue label. The cited behavior had
  already been repaired: the fix PR merged on the issue's filing day, its subject referenced the
  issue number, but its body carried no closing keyword, so the issue stayed open.
- The issue-number PR search (`--search '<issue> in:body'`) returned nothing for the closing
  keyword check. The pickaxe search (`git log --oneline <default-branch> -S '<cited symbol>' --
  <cited path>`) surfaced the fix commit immediately; its subject carried the issue reference.
- Verification before the disposition: the fix commit's added tests covered each evidence path the
  issue cited (the no-lock rule on the shared-storage path, the failure-site error naming, the
  second cited call site, and node-local behavior preservation). A separate policy test file pins
  the bounded-wait surface.
- Disposition taken: one disposition comment naming the fix commit and the covering tests, close as
  completed, release the claim. No plan cycle started; no duplicate regression guard added, because
  the fix's own tests already pin the invariant.
- Cost of the check: two commands and one file read. Cost of the missed check would have been a
  full plan-publish-review-implement cycle.

## 2026-10-31: Re-dispatched task already completed

- Context: one hosted pull request needed a rebase-only task: rebase onto the default branch, keep
  the review-gate label, and post one completion report. The dispatcher re-issued the same task
  several times in one day while the default branch advanced.
- Observed cost: separate runs each restarted from the snapshot prompt and re-derived all state.
  Their reports accumulated to seven on one thread. Several runs faced a genuinely advanced default
  branch, so re-running the rebase was correct for them; the missed step was binding to the latest
  report before acting.
- Final run's check: the branch sat on the current default-branch tip (merge base equal to the
  branch tip, zero commits behind, no conflicts), all hosted checks passed, the gate label was
  intact, auto-merge was off, and the latest report described exactly that state and named the
  outstanding re-review gate.
- Disposition taken: verify live state, confirm the gate state, and stop without a new report. The
  deliverable was a stop-and-report verdict, not another duplicate report.

## 2026-11-01: Multi-item issue with a recorded remainder

- Context: a plan review for an issue that named four converted checks. Two merged PRs already
  converted three of them. The last merged PR body held a "kept blocking" list with one item marked
  "no log directory; a design is needed first" and one item marked "ambiguous, kept". The authority
  ADR placed both items in the convert class. The plan's first draft converted only the first item
  and left the second item unchanged, because the last merged PR had kept it.
- Confirming evidence for the remainder boundary: the merged PR body, the cited source lines, and
  the authority record. Each closed item was re-read at its cited symbol and showed the new
  behavior. Each remainder item still raised.
- Population check: a directory-wide scan of the same check class found about 40 candidate sites
  across six modules. The plan then named about 18 convert sites by number and kept the rest behind
  one written keep rule. The hand-written list alone would have understated the change.
- Reference-count misses that the named test commands still catch at collection, so the plan stayed
  runnable, but which a reviewer finds first:
  - a deleted error class had three references, not two: one import, one re-raise site, and one more
    `except` clause inside a function that the plan did not list;
  - a callback parameter had five call sites, not three: the plan missed a publisher site and the
    loader's own command-line entry point, which has no log context;
  - two "constructors" in the plan were a static method and an instance method, and the real
    constructor was about 400 lines away.
- Reference case: one usage search per deleted symbol, and one for each changed signature, gives all
  three counts in under a minute.
- Verification limit: the plan review ran read-only. No plan step was implemented in this session.

## 2026-11-07: Re-plan while the implementation is already in an open pull request

- Context: a planning dispatch on a documentation issue. The issue body still described the defect
  and carried an early planning label. The session context held a prior plan, a plan-review GO with
  two conditions, and a completion report that named an open pull request at an exact head.
- Live checks: the cited line at the default-branch tip still held the defect, so the issue premise
  was true; the open pull request diff was exactly the one-line change; the pull request was open,
  non-draft, mergeable, merge-state blocked, and carried the implementation gate label; its head was
  not an ancestor of the default branch.
- Delivered plan: implementation declared complete with zero residual source work, the two retained
  review conditions restated as acceptance criteria with their measured baselines and an explicit
  stop rule for a red result, prior-plan decay corrected, and a check-classification step for the
  failing pull-request checks before any rerun. The prior plan expected pre-existing reds in a gate
  suite; the review measured the suite green, so the revised plan retired that expectation instead
  of repeating it.
- Failed alternative: stopping the plan entirely because the open pull request already held the
  change. That reading would have left the prior review conditions unbound and the stale baseline in
  force. An open pull request delivers its diff only; it does not deliver the planning artifact.
- Reuse limit: the check classification in this case rested on job-name and node-identity evidence
  gathered at the default-branch tip. A merge still depends on the owning repair lanes.
