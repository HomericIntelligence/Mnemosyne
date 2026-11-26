# GitHub Auto-Merge and CI Gating — Case Notes

These notes retain project-specific evidence moved during
[Mnemosyne #3335](https://github.com/HomericIntelligence/Mnemosyne/issues/3335).

## Case index

| Case | Source | Status | Disposition |
| --- | --- | --- | --- |
| Merge-queue REST 405 | [ProjectHephaestus #2311](https://github.com/HomericIntelligence/ProjectHephaestus/issues/2311) / [PR #2312](https://github.com/HomericIntelligence/ProjectHephaestus/pull/2312) | verified-ci | Repository helper fell back to native queue path without method flag |
| Queue-only gh admission | [Mnemosyne PR #3454](https://github.com/HomericIntelligence/Mnemosyne/pull/3454) | verified | Direct REST merge returned 405 under the merge-queue rule; `gh pr merge` enqueued (CLI output is informational), `already queued` confirmed state, and the `merged_at` poll confirmed the queue merge |
| Required-thread blocker | [ProjectHephaestus PR #1282](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1282) | verified-ci | Two unresolved threads, not stale lint, blocked merge |
| Current-head completion | [Issue #1645](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1645) / [PR #1646](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1646) | verified-ci | DCO/signature, PR label, squash auto-merge, current checks |
| Six-PR completion sweep | [ProjectHephaestus epic #1809](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1809) | verified-ci | Exposed PR-vs-issue label, stale check, merge-result drift, truncated review, leaked checkout edits |
| Shared-queue ownership | [Issues #2419](https://github.com/HomericIntelligence/ProjectHephaestus/issues/2419), [#2423](https://github.com/HomericIntelligence/ProjectHephaestus/issues/2423) | verified-local | No conditional disable/ownership nonce; fail-closed interlock |
| Direct review handoff | [Athena PR #60](https://github.com/HomericIntelligence/Athena/pull/60) | verified-local | Exact GO plus architecture evidence and reviewed-head revalidation |
| Queue readback and batch arming | Mnemosyne bulk queue sweep, 16 PRs | verified-ci | `autoMergeRequest` stayed null for every queue-owned PR; `mergeQueueEntry` proved admission; a piped wrong flag hid eleven failed calls |
| Armed-merge ceremony race and label semantics | Multi-repository review sweep, terminal GO delivery | verified-live | The armed merge fired on the last gate clearing ahead of the remaining ceremony; deliver records before the final gate or disarm first, and decorative state labels did not gate the merge |
| Cancelled-leg blocker on an armed merge | Internal repository delivery flow, 2026-10 | verified-ci | A matrix leg hung to a six-hour workflow timeout and was cancelled; the required aggregate failed with a message naming the leg; the leg owned tests outside the change surface and completed in minutes on comparator runs at nearby heads; `gh run rerun <run-id> --failed` returned the head green and the armed squash merge fired |
| Label-gate re-run replays the old payload | Internal repository delivery flow, 2026-10 | verified-local | A required aggregate workflow gated on `toJSON(github.event.pull_request.labels.*.name)`. After the gate label replaced a hold label, a failed-only re-run started 80 s later still failed, and its step `env` listed the hold label. A fresh `pull_request` `labeled` run on the same head passed the gate, auto-merge armed, and the squash merge landed. Branch-protection readback showed both the stale re-run failure and the fresh success on the same head. |
| Live-label gate recovery on a rerun | Agent delivery session, 2026-11 | verified-ci | A required gate failed before authorization while a newer run on the same head was green. The gate used `gh pr view <PR> --json labels` to query current labels during execution. After confirming the current label and unchanged head, a targeted rerun of the old run passed without a source, branch, or label change. Exact-head check and required-check queries then passed. |
| Queue rejects an explicit method without `--auto` | Internal repository delivery flow, 2026-11 | verified-local | `gh pr merge <N> --squash` on a queue-protected base printed `The merge strategy for <BASE> is set by the merge queue` and returned a non-zero status; `gh pr view` still reported `OPEN` with a null merge commit; the same command with `--auto` printed `already queued to merge`; the queue merged the PR about ten minutes later |
| Unattributable-signature blocker | Mnemosyne PR #4046 | verified-ci | The signature verified against a registered key but the committer email was a personal address, so the commit API read `no_user`. An identity reset plus re-sign in one amend repaired it; a plain re-sign would have preserved the blocker |
| Conflicting head suppressed all `pull_request` workflows | Internal repository delivery flow, 2026-11 | verified-ci | Only the label-gate and provenance `pull_request_target` checks posted while the PR was `CONFLICTING`; the nine-shard test workflow never started, so its absence was a missing event, not a result. After a rebase the PR turned `MERGEABLE` and the full workflow started on the new head |

## Additional observed patterns

- AchaeanFleet had clean, armed PRs with zero CI because path filters excluded them.
- ProjectCharybdis exposed a self-required workflow bootstrap deadlock and squash-only settings.
- ProjectNestor moved from blocked to merged immediately after unresolved CodeQL threads were
  answered and resolved.
- A Homeric organization audit confirmed rulesets and classic protection apply as a union; a
  relaxed ruleset does not cancel a classic approval count.
- Duplicate required-check entries after reruns required selecting the latest run on the current
  head, not treating any historical red conclusion as current.
- A review sweep armed auto-merge while a terminal review record and one foreign thread
  resolution still pended. The merge fired within minutes of the last gate clearing, ahead of
  the remaining ceremony, and the ceremony had to be completed post-merge. On other pull
  requests in the same sweep, a non-mergeable state label did not hold an armed merge: the
  label was decorative, and only reviews, threads, checks, and policy-required inputs gated.
  Order ceremonies before the final gate, or disarm and re-arm.
- A `CONFLICTING` head suppresses every `pull_request` workflow. Pull-request-target checks
  still report, so a partial green rollup can look like success while no test has run.
- An armed auto-merge waited for hours while one matrix leg hung to the workflow timeout and was
  cancelled. The required aggregate check failed with a message that named the cancelled leg.
  The leg owned only tests outside the change surface, and the same leg completed in minutes on
  comparator runs at nearby heads. A failed-only rerun turned the head green, and the armed
  merge fired with no content change. A rebase or push would have discarded the reviewed head
  without repairing the leg.
- Two pull requests showed no failing check at all: 24 and 23 contexts, every conclusion
  `SUCCESS`, `mergeable: MERGEABLE`, and no unresolved threads. Both stayed `BLOCKED` and
  `gh pr merge --auto` refused with no message. The cause was the checkless
  `required_signatures` rule on one unverified commit per branch. The rule's `parameters` were
  `null`, no check name matched a signature pattern, and the commit API reported
  `verified: false, reason: unsigned`. A rebase onto the current base and a signed re-creation
  of the commit changed only the signature; both then read `CLEAN` and entered the queue. A
  byproduct: after the force-push, mergeability read `UNKNOWN` for about one minute before
  GitHub recomputed it, which is a calculation window, not a second blocker.
- The same sweep found a third signature reason. One head was signed with a key whose
  fingerprint the account had registered, but the committer email was a personal address, so
  the commit API read `verified: false, reason: no_user` although the signature was sound.
  A plain amend with the signing key preserves the committer identity, so the repair reset
  the author and committer to the account's verified noreply identity and re-signed in one
  amend. The remote head then read `reason: valid`, the PR read `CLEAN`, and the queue
  admitted it. Before pushing a repair, re-read the remote branch head: a concurrent lane
  can push the same repair first, and the lease then correctly rejects the redundant push.

## Durable case details

The shared-queue review inspected the GraphQL contract: enable accepts an expected head OID, but
disable has no corresponding ownership token and the request exposes no client nonce. A later read
cannot prove the request is still yours. A queue encountering any existing request therefore stands
down rather than adopting or disabling it.

The six-PR sweep also showed that CI may lint the synthetic merge ref. Main drift can fail that job
even when branch-only checks pass. Reproduce the merge-result command, include required formatting,
and do not mistake an automation run that ended before its completion marker for a clean review.

The queue sweep armed sixteen PRs on a queue-protected base. Every PR returned a null
`autoMergeRequest` after a successful arm, because the queue owns the request. Reading that field as
proof of failure caused a false "not armed" conclusion and a redundant re-arm. `mergeQueueEntry`
state and position were the only reliable readback. The same sweep showed that a batched loop can
report success while every call fails: the loop used `--auto-merge`, which is not a flag, and the
piped output hid the error. Confirm each PR reached the queue instead of trusting the loop status.
The sweep also found that one list response reported `BLOCKED` for PRs that a single-PR read
reported as `CLEAN`. Read merge state per PR.

## Claim before check on a two-lane review

Two reviewer sessions received the same request to review one pull request at the
same head in one checkout. The second session waited for the first to go quiet,
rebased the branch, pushed a fix, and posted a GO verdict. Its comment reported
the required check as `success`.

The check run did not exist at that moment. It started after the comment and
concluded `failure`. The same workflow posted `lint` and `typecheck` failures on
two source files. Those files were byte-identical to the default branch, and both
failures reproduced on a clean extraction of the default branch, so they were
pre-existing. The test shards were still pending at the verdict time.

The label was already set when the second reviewer read it. Recovery used the
same evidence path for both problems:

1. Read the check results for the exact head with the check-runs API, and read
   the job conclusion per name.
2. Read `lint` and `typecheck` job logs. Confirm the failing file and line.
3. Extract the default branch and run the same type check and format check
   there, without a worktree. Both failed the same way, so the red belonged to
   the default branch, not to the change.
4. Post a follow-up verdict comment that states the real check result, the
   pre-existing attribution, and the unmet label conditions as corrections to
   the earlier comment. Leave the label in place, because the task rules forbid
   removing a foreign label, and record that the owner decides the label.

This case is `verified-local` for the two-lane timeline and `verified-ci` for the
check conclusions and the pre-existing attribution.

## Trigger label absent: zero check runs

An automation campaign opened a pull request and armed auto-merge in the same turn. The
repository gates CI with a state label: the workflows start only when that label is on the
pull request. The campaign assigned no label. The request stayed open for more than a day.

Readback at review time:

- `state: OPEN`, auto-merge request armed with the squash method.
- `mergeStateStatus: UNKNOWN`.
- `gh pr checks <N>` answered "no checks reported on the branch" - not failures, not skipped
  jobs, no runs at all.

Applying the trigger label started the full check matrix within seconds, and the armed
request stayed valid. A sibling pull request from the same campaign carried the label from
creation and had check runs immediately, so the difference was the label, not the workflow
definition. A third pull request carried a verdict label instead; its checks were skipped by
the workflow gate.

Decision rule captured from the trio: classify each label as policy-required, decorative, or
trigger. An absent trigger label is a "no result exists" state. Waiting cannot change it, and
no failing run exists to debug. Apply the label only within explicit authority, then verify a
run starts on the current head.

## Verification boundaries

Rows marked `verified-ci` observed merged PRs and remote checks. Shared-queue and Athena direct-review
designs passed local gates only at capture. Historical administrator bypasses are case evidence, not
a recommendation; current workflows must preserve repository policy and explicit authority.
