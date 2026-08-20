# GitHub Actions Required Checks and Branch Protection — Notes

These notes retain project-specific incidents, identifiers, and verification records moved out of
the retrievable [skill](./gha-required-checks-branch-protection.md). The complete v1.14.0 main is
stored once in [history](./gha-required-checks-branch-protection.history), not duplicated here.

## Case Index

| Case | Source | Verification at capture | Disposition |
| --- | --- | --- | --- |
| Summary aggregator | [ProjectOdyssey PR #5406](https://github.com/HomericIntelligence/ProjectOdyssey/pull/5406) | verified-ci | Keep stable-context and event-aware skip pattern |
| Branch-protection read-back | [ProjectNestor issue #54](https://github.com/HomericIntelligence/ProjectNestor/issues/54), [PR #108](https://github.com/HomericIntelligence/ProjectNestor/pull/108) | verified-ci | Keep synthetic positive/negative API fixtures |
| Workflow smoke expansion | [ProjectOdyssey PR #4838](https://github.com/HomericIntelligence/ProjectOdyssey/pull/4838) | verified-local/precommit evidence in source | Keep multi-workflow structural coverage principle |
| Guard negative path | [ProjectHephaestus PR #1343](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1343) | verified-local, CI pending | Keep `_unwired_jobs` and mutation-style negative test |
| Required-context placement | [Mnemosyne issue #309](https://github.com/HomericIntelligence/Mnemosyne/issues/309) | enumeration verified-local; placement unverified | Keep exact pinned-context membership rule |
| Prerequisite and destructive write review | [Mnemosyne issue #284](https://github.com/HomericIntelligence/Mnemosyne/issues/284) | premise checks/NOGO verified-local; proposed PUT unverified | Keep merged-main precondition, rollback, and dynamic foreign key |
| Advisory job promotion | [ProjectHephaestus issue #1514](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1514) | verified-local, seven tests | Keep five-step promotion pattern |
| Merge-queue readiness policy | [Telemachy issue #308](https://github.com/HomericIntelligence/Telemachy/issues/308), [PR #310](https://github.com/HomericIntelligence/Telemachy/pull/310) | verified-local; CI pending | Keep artifact-derived staged activation contract |
| Live merge-queue activation | [Athena PR #45](https://github.com/HomericIntelligence/Athena/pull/45) | verified-ci | Keep auto-merge prerequisite and synthetic-run proof |
| Silent queue ejection | [Agamemnon PR #457](https://github.com/HomericIntelligence/Agamemnon/pull/457), [Nestor PR #133](https://github.com/HomericIntelligence/Nestor/pull/133) | verified-ci | Keep whole-gate-workflow diagnosis |
| Coupled contexts and fleet rollback | [Mnemosyne PR #3189](https://github.com/HomericIntelligence/Mnemosyne/pull/3189) | verified-ci | Keep identical-name and narrow rollback rules |
| Fail-closed test report | [Odyssey issue #5731](https://github.com/HomericIntelligence/Odyssey/issues/5731), [PR #5738](https://github.com/HomericIntelligence/Odyssey/pull/5738) | verified-ci; artifact trust controls not deployed | Keep dual contract, diagnostics-first order, and trust boundary |

## Required Context and Aggregator Cases

ProjectOdyssey PR #5406 replaced individually required container-pipeline jobs with one summary
context. The aggregate used `if: always()` and inspected dependency outcomes. Required jobs had to
succeed; only jobs explicitly optional on that event accepted `skipped`. This avoided the failure
where a whole job gated by `if: github.event_name != 'pull_request'` posted `skipped` and could
never satisfy branch protection.

The reusable-workflow split placed shared job definitions in `_checks.yml` with `workflow_call` and
kept `_required.yml` as a thin event caller. That layout was verified precommit in Mnemosyne, not
with the same hosted evidence as the ProjectOdyssey aggregate.

ProjectNestor PR #108 used a read-back after a branch-protection write and synthetic fixtures for a
Bash verifier. The essential test pair used one fixture with the required approval count and one
with a lower count, requiring exit 0 and non-zero respectively. A passing API response was not
treated as proof that GitHub retained the requested value.

## Wiring and Placement Cases

The initial `RESULTS`-loop and guard work for ProjectHephaestus issue #1315 remained planning-only.
PR #1343 later extracted `_unwired_jobs`; six local tests passed, but CI was pending. The durable
negative-path method is to mutate a valid workflow fixture by removing one `needs` member and then
assert that the helper names the missing job. Merely testing the unchanged good fixture can conceal
an inverted condition.

Mnemosyne issue #309 locally enumerated eight repository-rule contexts:

- `lint`
- `unit-tests`
- `integration-tests`
- `security/dependency-scan`
- `security/secrets-scan`
- `build`
- `schema-validation`
- `deps/version-sync`

The proposed guard originally lived in a `validate` job that was not pinned. Moving it into the
displayed `schema-validation` job would make it blocking, but that placement and CI wiring were not
executed. A later review noted that org policy could use `Required Checks / schema-validation`
while repository policy used bare `schema-validation`; only the repo leg was locally enumerated.
The org-prefix parity was documentation-derived and remained unverified.

ProjectHephaestus issue #1514 showed the full advisory-to-required promotion locally:

1. Add the job to `_required.yml` with the same change/event guard and required environment.
2. Add its key to `required-checks-gate.needs`.
3. Prevent duplicate PR execution in the advisory workflow while retaining scheduled/manual use.
4. Add a named structural test for the job and its gate dependency.
5. Run focused tests and YAML validation.

Seven gate tests and yamllint passed. No branch-protection PUT was needed because the repository
already pinned the aggregate gate, not each child job.

## Prerequisite and Ruleset-Write Case

For Mnemosyne issue #284, the issue claimed PR #264 had introduced a SAST context. Local checks
showed the PR was open with `mergedAt: null`, and the default-branch workflow grep found no posting
job. Requiring that context at that point would have blocked all PRs.

The first ruleset plan also had two review failures:

- It described a read-back but no recovery operation. A full-replacement PUT needs an explicit
  re-PUT of a validated pre-edit snapshot on any invariant mismatch.
- It pasted `integration_id: 15368` from another source. The value should be selected from a live
  sibling required-check object in the target ruleset and used in the appended entry.

Those corrections were planning decisions. The actual ruleset PUT and rollback were not executed,
so they remain unverified even though the failed-review origin and prerequisite checks were real.

## Merge-Queue Cases

### Readiness policy

Telemachy PR #310 committed `configs/github/merge-queue-policy.json` with twelve exact contexts and
the exact merge-queue rule. Tests asserted `push.main`, `pull_request.main`, and
`merge_group.checks_requested` triggers and preserved a tag-only release workflow. Local evidence:

- TDD red: 3 failed, 4 passed before the artifact.
- Focused green: 7 passed.
- Full suite: 290 passed, 3 skipped, 88.86% coverage.
- Commit `65c97ec2920ba89c9440edf00ea32a2b697ab608` had a verified signature and DCO.
- Required PR CI was still queued/in progress, so this was not `verified-ci`.

The readiness PR used `Refs #308`, because live activation and a representative queued run were
post-merge work.

### Live activation

For the live HomericIntelligence fleet rollout, each ruleset was snapshotted, an existing queue
rule was rejected, the exact approved object was appended, and unrelated fields/rules were read
back. Repository `allow_auto_merge` was also required; Athena was the one repository where it had
to be enabled.

Athena PR #45 entered the queue, produced merge-group run `29609074296` at synthetic SHA
`93a2e7fd5915f16492c6fc108bf083ef20e1c68a`, and merged at that SHA. That is hosted operational
proof rather than merely a workflow trigger test.

### Silent ejection

Agamemnon PR #457 had all 18 required contexts green at its PR head but was ejected because a
non-required `markdownlint` job inside the Required Checks workflow failed MD024 on the synthetic
merge result. Fixing the changelog allowed re-entry and merge. Nestor PR #133 reproduced the class
with MD013. The important diagnostic unit is the entire gate workflow on the queue SHA, not only the
contexts individually named in the ruleset.

### Coupled context names and rollback

Mnemosyne PR #3189 used a fast `merge-queue-smoke` context after removing the full required
workflow's `merge_group` trigger, but policy still required the original full check names. The
synthetic SHA never posted them, so GitHub removed the PR three times with `checks_timed_out` even
though the smoke was green.

The fleet rollback removed only `merge_queue` from 15 active baseline rulesets across 17 accessible
repositories. It preserved deletion, non-fast-forward, linear-history, pull-request,
required-check, and signature protections. The final org query found no active queue rule. This was
verified-CI/live-policy evidence.

## Fail-Closed Test Report Case

Odyssey PR #5738 replaced a report that could declare “0 groups / all tests passed” after setup
failures. Its two independent contracts were:

1. The complete `needs` object is authoritative for execution. Success is required by default;
   cancellation, failure, and dependency-induced skip are red. The sole ordinary SIMD skip was an
   explicit event-aware exception.
2. Every expected producer or matrix shard supplies exactly one schema-valid outcome manifest that
   agrees with its authoritative job result. Missing, duplicate, unknown, malformed, empty, or
   contradictory manifests are red.

Diagnostics were generated and written before verdict enforcement, then uploaded in an always-run
step. This ensured a red gate still produced useful evidence.

Hosted evidence recorded in the source:

| Evidence | Result |
| --- | --- |
| Negative run `30499502544` | Test Report job `90741695665` failed and artifact `8743636017` still uploaded |
| Ordinary exact-main run `30566396623` | 37 successes plus one allowed SIMD skip; 19 upstream rows and 12 manifests |
| Extended exact-main run `30566477564` | 38/38 successes including SIMD; 19 upstream rows and 12 manifests |
| Ordinary artifact | `8770150630`, SHA-256 `24b6c991e03a4ab233b2e261799fbefb468e006860102ca15581d1a6f124058c` |
| Extended artifact | `8771296615`, SHA-256 `156b7168bf6101a805122f633ebf06237948270213ca47f0f95ee3869abe478e` |
| Accepted main | `760aed20a2cacf84e1e83256e1de169ccee9f433` |

The verdict, exact-run/head binding, and red fallback were verified. The stronger artifact trust
controls—closed bounded schema, safe extraction, escaped rendering, mention neutralization, and
bot-identity-bound comment updates—were security-derived but not deployed in that workflow. Do not
upgrade them to verified-CI.

Regression coverage should test behavior, not pin prose. Include setup failure, zero artifacts,
direct-root extraction, every malformed/missing/duplicate producer case, unallowlisted skip,
event-specific allowed skip, failed matrix shard, complete green state, unwired/duplicate `needs`,
unsafe expression interpolation, missing `always()`/strict upload, oversized/schema-invalid comment
artifact, and markup/mention neutralization.

## Compaction Audit

- Retained in main: all distinct triggers; skip semantics; exact context identity; guard placement
  and negative tests; default-branch prerequisite; GET/read-back/rollback and dynamic foreign key;
  org/repo forms; job promotion; policy-as-code queue activation; auto-merge; silent ejection;
  coupled context names; fleet rollback; authoritative `needs`; complete manifests;
  diagnostics-before-verdict; and the artifact trust boundary.
- Moved here: repository-specific context lists, run/job/artifact IDs, detailed PR histories, test
  counts, and per-case status records.
- Archived only in history: the complete v1.14.0 retrievable document and redundant worked prose.
