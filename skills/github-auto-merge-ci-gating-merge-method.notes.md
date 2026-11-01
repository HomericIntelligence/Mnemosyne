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
- An armed auto-merge waited for hours while one matrix leg hung to the workflow timeout and was
  cancelled. The required aggregate check failed with a message that named the cancelled leg.
  The leg owned only tests outside the change surface, and the same leg completed in minutes on
  comparator runs at nearby heads. A failed-only rerun turned the head green, and the armed
  merge fired with no content change. A rebase or push would have discarded the reviewed head
  without repairing the leg.

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

## Verification boundaries

Rows marked `verified-ci` observed merged PRs and remote checks. Shared-queue and Athena direct-review
designs passed local gates only at capture. Historical administrator bypasses are case evidence, not
a recommendation; current workflows must preserve repository policy and explicit authority.
