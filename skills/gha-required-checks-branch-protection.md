---
name: gha-required-checks-branch-protection
license: BSD-3-Clause
description: "Design and diagnose GitHub Actions required checks, branch/ruleset protection, merge queues, and fail-closed aggregate reports. Use when skipped jobs block PRs, required contexts drift, a guard is advisory rather than merge-blocking, a full-replacement ruleset update needs rollback, merge-group runs eject green PRs, or reports can pass with missing upstream evidence."
category: ci-cd
date: 2026-07-30
version: "2.0.0"
user-invocable: false
verification: verified-ci
history: gha-required-checks-branch-protection.history
tags:
  - github-actions
  - branch-protection
  - rulesets
  - required-status-checks
  - reusable-workflow
  - aggregator
  - merge-queue
  - merge-group
  - fail-closed
  - outcome-manifest
  - rollback
---

# GitHub Actions Required Checks and Branch Protection

## Overview

Required checks are a three-part contract: the workflow must emit the exact context, repository
policy must require that exact context, and every event GitHub evaluates must be able to complete
it. This skill covers design, safe policy updates, merge-queue behavior, and trustworthy aggregate
reports. Detailed incidents and evidence live in
[notes](./gha-required-checks-branch-protection.notes.md); superseded full content lives in
[history](./gha-required-checks-branch-protection.history).

The core patterns are `verified-ci`, including the summary aggregator, API read-back, live queue
behavior, coupled merge-group contexts, and fail-closed reporting. Some planning patterns were only
verified locally or remain unverified; the [verification table](#verified-on) preserves those
boundaries.

## When to Use

- A required context is skipped on pull requests and therefore never satisfies protection.
- Duplicate workflows run the same jobs, or a stable aggregate context should replace many pinned
  job contexts.
- A new compliance/security guard exists in a workflow but may be advisory rather than required.
- An issue claims a prerequisite job landed, or a job key is being confused with its displayed
  check/context name.
- A branch-protection or ruleset write replaces a complete object and needs snapshot, read-back,
  and rollback protection.
- Org and repository rulesets use different context forms, such as bare `schema-validation` versus
  `Required Checks / schema-validation`.
- A staged or live merge queue needs one policy artifact, an exact `merge_group` contract, or a
  fleet-safe rollback.
- A queued PR has green required contexts but is silently ejected, times out, or fails only on the
  synthetic `gh-readonly-queue/...` SHA.
- An aggregate report can say “all tests passed” despite setup failures, skipped dependencies,
  missing artifacts, zero producers, or an incomplete matrix.

## Verified Workflow

### Decision rules

1. **Discover names from both sides.** Enumerate job keys and displayed names in workflow YAML,
   then enumerate required contexts from every active org/repository ruleset. Match exact emitted
   context strings, not a similar filename or job key.
2. **Prove the posting job exists on default branch.** Before requiring a new context, verify its
   prerequisite PR is merged and grep the default-branch workflow. A never-posted required context
   deadlocks every PR.
3. **Make the gate authoritative.** A job in an advisory/scheduled workflow does not block merges.
   Put it in the required workflow, wire it into the aggregate gate's `needs`, and add a structural
   test that fails when a new non-excluded job is unwired.
4. **Use GET-derived writes.** Snapshot the complete live object, validate the snapshot as a restore
   target, apply the narrow mutation, read back exact invariants, and re-PUT the snapshot
   immediately on mismatch. Derive sibling foreign keys such as `integration_id` from live data.
5. **Treat every queue SHA as a full gate target.** Required names are coupled across
   `pull_request` and `merge_group`. The synthetic SHA must emit every required context, and every
   job in the gate workflow must be green even when that job is not itself pinned.
6. **Require execution and evidence independently.** The full `needs` object decides upstream
   success; complete producer manifests prove evidence coverage. Artifacts alone prove neither.

### Copy-ready pattern 1: one stable required aggregate

```yaml
jobs:
  required-checks-gate:
    needs: [lint, tests, security-scan]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Enforce upstream results
        env:
          LINT_RESULT: ${{ needs.lint.result }}
          TEST_RESULT: ${{ needs.tests.result }}
          SECURITY_RESULT: ${{ needs.security-scan.result }}
        run: |
          failed=0
          [ "$LINT_RESULT" = success ] || failed=1
          [ "$TEST_RESULT" = success ] || failed=1
          case "$SECURITY_RESULT" in
            success) ;;
            skipped) [ "$GITHUB_EVENT_NAME" = pull_request ] || failed=1 ;;
            *) failed=1 ;;
          esac
          exit "$failed"
```

Use `if: always()` on the aggregate so it receives failed/cancelled dependency results. Require
`success` by default. A skipped result is acceptable only for an explicitly named job/event pair;
dependency-induced skips fail. Prefer one stable required context when matrices or optional jobs
would otherwise make repository policy churn.

If duplicated workflows exist, put job definitions in a `workflow_call` workflow and keep the
required workflow as a thin event-specific caller/aggregator. Verify the called workflow's inputs,
secrets, permissions, and displayed job names. A reusable workflow refactor is not complete until
the old duplicate execution path is removed or intentionally retained.

The structural test should compute all top-level jobs except an explicit allowlist and the gate
itself, then require exact equality with `required-checks-gate.needs`; also reject duplicates. Give
the helper a negative-path test by removing one dependency from a parsed fixture and requiring the
helper to report it. A test with an inverted assertion can otherwise pass while checking nothing.

### Copy-ready pattern 2: mutate a ruleset with restoration available

```bash
set -euo pipefail
repo="OWNER/REPO"
ruleset_id="<id>"
snapshot="$(mktemp)"
payload="$(mktemp)"

gh api "repos/$repo/rulesets/$ruleset_id" > "$snapshot"
jq -e '.id and .name and (.rules | type == "array")' "$snapshot" >/dev/null

# Derive a sibling integration_id; do not paste a stale literal.
integration_id="$(jq -er '.rules[]
  | select(.type=="required_status_checks")
  | .parameters.required_status_checks[0].integration_id' "$snapshot")"

# Build the complete update payload from the snapshot, preserving unrelated rules.
jq --arg context '<new-context>' --argjson iid "$integration_id" \
  '<GET-derived transformation producing the API update schema>' \
  "$snapshot" > "$payload"

gh api --method PUT "repos/$repo/rulesets/$ruleset_id" --input "$payload"
if ! gh api "repos/$repo/rulesets/$ruleset_id" \
  | jq -e --arg c '<new-context>' '<exact read-back invariant>' >/dev/null; then
  gh api --method PUT "repos/$repo/rulesets/$ruleset_id" \
    --input '<validated restore payload derived from snapshot>'
  exit 1
fi
```

The API's GET and PUT schemas can differ; construct both update and restore payloads deliberately.
Never call the initial GET a backup until it parses and contains the expected protection/rule
count. For branch-protection endpoints, prefer a narrow subresource update when available. For a
full ruleset PUT, preserve every unrelated rule and field and make rollback part of the executable
failure path, not prose after the command.

Before the write, verify the context producer on the default branch:

- `gh pr view <pr> --json state,mergedAt` must show the prerequisite merged.
- `git grep` or `gh api contents/...` against the default branch must show the posting job and its
  exact `name:`.
- Enumerate all relevant rulesets. Normalize only known org/repo forms; do not use a fuzzy match
  that can accept the wrong check.

### Copy-ready pattern 3: fail-closed report and merge-queue contract

```yaml
on:
  pull_request:
  merge_group:
    types: [checks_requested]

jobs:
  test-report:
    needs: [setup, unit, integration, simd]
    if: always()
    steps:
      - name: Build report before verdict
        env:
          NEEDS_JSON: ${{ toJSON(needs) }}
          EVENT_NAME: ${{ github.event_name }}
        run: python scripts/build_test_report.py
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@<full-commit-sha>
        with:
          name: test-report
          path: test-report.md
          if-no-files-found: error
```

Pass `${{ toJSON(needs) }}` only through step `env`; never interpolate untrusted JSON into shell
source or a heredoc, and do not log the full object. The report job must directly depend on every
authoritative upstream job. Its validator requires success except an explicit job/event skip
allowlist.

Each result producer writes one minimal manifest in an `if: always()` step and uploads it in a
separate always-run step with `if-no-files-found: error`. Use a closed schema containing producer,
job ID, and status. Recursively discover downloads and reject zero, missing, duplicate, unexpected,
empty, malformed, mapping-inconsistent, or result-contradicting manifests. For matrices, validate
every declared shard and independently require the aggregate job in `needs` to succeed.

Generate diagnostics before enforcing the verdict, write the report even on red, then upload it in
an always-run step. Detailed result JSON is diagnostic, not a complete suite census; never derive
“all tests passed” or a global pass count from whatever files happened to download.

For a write-token `workflow_run` commenter, bind to the exact run/head and conclusion, but remember
that freshness is not authenticity. Prefer API-derived authoritative data rendered by trusted
default-branch code. If artifacts are necessary, require one bounded artifact from the bound run,
extract under `runner.temp`, reject unexpected/oversized files, parse a closed versioned schema,
escape Markdown/HTML and mentions, and update only a bot-authored comment with an exact private
marker. Any failure produces a trusted red fallback containing no artifact text.

### Merge-queue activation and diagnosis

Store exact required contexts and the exact `merge_queue` rule in one committed JSON policy
artifact. Tests must derive workflow triggers, activation payload, and smoke assertions from that
artifact. Keep the readiness issue open until live activation and a representative completed
`merge_group` run exist. `allow_auto_merge` must be enabled before `gh pr merge --auto --squash`
can submit to an active queue.

When all PR-head required contexts are green but the PR disappears from the queue, inspect the
Required Checks run on `gh-readonly-queue/...` and drill into every job. A non-pinned job such as
markdownlint can fail inside the gate workflow and eject the PR because the workflow conclusion is
red. Fix that job's content or move a truly advisory job to a separate workflow.

A fast merge-group smoke with a new name cannot replace unchanged required names. If the full gate
stops running on `merge_group`, the synthetic SHA never emits the pinned contexts and GitHub removes
the PR with `checks_timed_out`. During incident rollback, remove only `merge_queue` from complete
GET-derived rulesets, verify all other protections survive, and re-enable only after a synthetic
SHA emits the final required set.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Whole-job PR skip | Omit a required job on pull requests | A skipped required context is not satisfied | Run the context or aggregate explicit optional results |
| Job-key/context confusion | Pin a YAML job key | The emitted display name can differ | Enumerate emitted and required names exactly |
| Green-but-advisory guard | Add a check outside the required gate | It blocks nothing | Promote it and wire it into the aggregate `needs` |
| Unmerged prerequisite | Require a context from an open PR | No default-branch producer posts it | Verify merged state and default-branch content first |
| Read-back without rollback | Detect a bad full-object write | Live policy remains corrupted | Validate a restore payload and roll back on mismatch |
| Hard-coded integration ID | Copy a foreign key from another object | The value can drift across rulesets | Derive it from a live sibling entry |
| Required-only queue diagnosis | Inspect only pinned contexts | Non-pinned jobs can fail the gate workflow | Inspect every job on the synthetic merge-result run |
| Renamed merge smoke | Emit one new fast context | It cannot satisfy old pinned names | Emit the same required names on PR and merge-group SHAs |
| Artifact-means-success | Trust an always-run upload | Uploads survive setup/test failure | Gate on `needs`; use manifests only for completeness |
| Zero-group success | Sum whatever diagnostics downloaded | An empty partial set can still parse | Require the full producer set and hosted negative proof |
| Raw artifact comment | Relay PR-controlled Markdown | It crosses into a write-token consumer | Enforce schema, bounds, escaping, bot identity, and a trusted red fallback |

## Results & Parameters

| Parameter | Required value or rule |
| --- | --- |
| Aggregate execution | `if: always()` with direct `needs` on every authoritative job |
| Default accepted result | `success`; skips only by named job/event allowlist |
| Structural guard | Exact non-excluded jobs equals aggregate `needs`; duplicates rejected |
| Ruleset mutation | GET snapshot, validated restore target, narrow transform, exact read-back, rollback |
| Context identity | Exact emitted display name; account for bare repo and prefixed org forms |
| Queue events | Required contexts emitted for both `pull_request` and `merge_group` |
| Producer evidence | Exactly one closed-schema manifest per expected producer/shard |
| Report ordering | Generate diagnostics, write report, enforce verdict, always upload |
| Comment failure | Trusted red fallback with bound run URL/conclusion and no artifact text |
| Activation evidence | Policy artifact, exact read-back, auto-merge enabled, completed merge-group run |

## Verified On

| Scope | Status | Evidence boundary |
| --- | --- | --- |
| Summary aggregator and branch-protection update | verified-ci | ProjectOdyssey PR #5406 |
| Branch-protection read-back and synthetic fixtures | verified-ci | ProjectNestor PR #108 |
| Guard negative-path helper | verified-local | ProjectHephaestus PR #1343; CI was pending |
| Required-context placement and prerequisite checks | verified-local technique | Proposed ruleset/guard changes remained unverified |
| Advisory-to-required job promotion | verified-local | ProjectHephaestus issue #1514, seven gate tests |
| Merge-queue policy readiness | verified-local | Telemachy PR #310; CI pending at capture |
| Live queue activation and merge-result proof | verified-ci | Athena PR #45 and Required Checks run 29609074296 |
| Queue ejection by non-required job | verified-ci | Agamemnon PR #457 and Nestor PR #133 |
| Coupled-context failure and fleet rollback | verified-ci | Mnemosyne PR #3189 and 17-repository audit |
| Fail-closed test report | verified-ci | Odyssey PR #5738; artifact trust hardening remained security-derived/not deployed |

## References

- [Detailed cases and provenance](./gha-required-checks-branch-protection.notes.md)
- [Version history and superseded full content](./gha-required-checks-branch-protection.history)
- [GitHub: rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [GitHub: merge queues](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)
- [GitHub REST: branch protection](https://docs.github.com/en/rest/branches/branch-protection?apiVersion=2022-11-28#update-branch-protection)
- [GitHub Actions: reusable workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [Zero-test false-pass guard](./testing-verification-gate-zero-test-false-pass.md)
- [Canonical check for non-library repositories](./ci-cd-canonical-check-nonlibrary-repo.md)
