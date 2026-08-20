# GitHub Auto-Merge and CI Gating — Case Notes

These notes retain project-specific evidence moved during
[Mnemosyne #3335](https://github.com/HomericIntelligence/Mnemosyne/issues/3335).

## Case index

| Case | Source | Status | Disposition |
| --- | --- | --- | --- |
| Merge-queue REST 405 | [ProjectHephaestus #2311](https://github.com/HomericIntelligence/ProjectHephaestus/issues/2311) / [PR #2312](https://github.com/HomericIntelligence/ProjectHephaestus/pull/2312) | verified-ci | Repository helper fell back to native queue path without method flag |
| Required-thread blocker | [ProjectHephaestus PR #1282](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1282) | verified-ci | Two unresolved threads, not stale lint, blocked merge |
| Current-head completion | [Issue #1645](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1645) / [PR #1646](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1646) | verified-ci | DCO/signature, PR label, squash auto-merge, current checks |
| Six-PR completion sweep | [ProjectHephaestus epic #1809](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1809) | verified-ci | Exposed PR-vs-issue label, stale check, merge-result drift, truncated review, leaked checkout edits |
| Shared-queue ownership | [Issues #2419](https://github.com/HomericIntelligence/ProjectHephaestus/issues/2419), [#2423](https://github.com/HomericIntelligence/ProjectHephaestus/issues/2423) | verified-local | No conditional disable/ownership nonce; fail-closed interlock |
| Direct review handoff | [Athena PR #60](https://github.com/HomericIntelligence/Athena/pull/60) | verified-local | Exact GO plus architecture evidence and reviewed-head revalidation |

## Additional observed patterns

- AchaeanFleet had clean, armed PRs with zero CI because path filters excluded them.
- ProjectCharybdis exposed a self-required workflow bootstrap deadlock and squash-only settings.
- ProjectNestor moved from blocked to merged immediately after unresolved CodeQL threads were
  answered and resolved.
- A Homeric organization audit confirmed rulesets and classic protection apply as a union; a
  relaxed ruleset does not cancel a classic approval count.
- Duplicate required-check entries after reruns required selecting the latest run on the current
  head, not treating any historical red conclusion as current.

## Durable case details

The shared-queue review inspected the GraphQL contract: enable accepts an expected head OID, but
disable has no corresponding ownership token and the request exposes no client nonce. A later read
cannot prove the request is still yours. A queue encountering any existing request therefore stands
down rather than adopting or disabling it.

The six-PR sweep also showed that CI may lint the synthetic merge ref. Main drift can fail that job
even when branch-only checks pass. Reproduce the merge-result command, include required formatting,
and do not mistake an automation run that ended before its completion marker for a clean review.

## Verification boundaries

Rows marked `verified-ci` observed merged PRs and remote checks. Shared-queue and Athena direct-review
designs passed local gates only at capture. Historical administrator bypasses are case evidence, not
a recommendation; current workflows must preserve repository policy and explicit authority.
