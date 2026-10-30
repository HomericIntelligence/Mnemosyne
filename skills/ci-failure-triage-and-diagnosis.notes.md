# CI Failure Triage and Diagnosis — Notes

Supporting case evidence for the canonical
[`ci-failure-triage-and-diagnosis`](ci-failure-triage-and-diagnosis.md) skill. The exact
30,593-byte v1.1.0 main is archived once in
[`ci-failure-triage-and-diagnosis.history`](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/ci-failure-triage-and-diagnosis.history), with
SHA-256 `dbfeed396bb4cb23d547fc0d9077a6e5756b9f71b820cda2b4e2ee6acd83e592`.

## Case Index

| Case | Source | Verification status | Reusable result |
| --- | --- | --- | --- |
| Read the actual failing log before planning | [ProjectOdyssey issue #252](https://github.com/HomericIntelligence/ProjectOdyssey/issues/252) | verified-local | `--log-failed` exposed exit 127 before the recipe body |
| Confirm an already-landed workflow fix | [ProjectOdyssey PR #254](https://github.com/HomericIntelligence/ProjectOdyssey/pull/254) | verified-local against later main runs | Search the fix string and inspect current-main runs before replanning |
| Container/JIT core capture and symbolication | [ProjectOdyssey PR #5380](https://github.com/HomericIntelligence/ProjectOdyssey/pull/5380) | verified-ci | Use a container-visible core path and symbolicate beside the binary |
| Separate OOM from the libKGEN crash | [modular issue #6413](https://github.com/modular/modular/issues/6413) and [ProjectOdyssey PR #5381](https://github.com/HomericIntelligence/ProjectOdyssey/pull/5381) | verified-ci | Log signature outranks exit code 137 |
| Opt-in gdb capture and required-context triage | [ProjectOdyssey PR #5411](https://github.com/HomericIntelligence/ProjectOdyssey/pull/5411) | verified-ci | Dispatch-only diagnostics avoid taxing every PR while keeping the gate visible |
| Interruptible E2E subprocess runner | [ProjectScylla PR #1515](https://github.com/HomericIntelligence/ProjectScylla/pull/1515) | verified-ci | Poll futures/processes every two seconds and isolate stdin/process groups |
| Cross-CPU survey | [Immutable v1.1.0 source](https://github.com/HomericIntelligence/Mnemosyne/blob/10e28497993009cc221cb991e1ee183e6117eda8/skills/ci-failure-triage-and-diagnosis.md) | verified-local survey; causal interpretation not proved | Hold image/reproducer constant and record CPU model, flags, iterations, and exits |
| Proposed pixi/yamllint hardening | [ProjectOdyssey issue #252](https://github.com/HomericIntelligence/ProjectOdyssey/issues/252) | unverified proposal | Do not upgrade a planning suggestion to verified behavior |
| Failed-job rerun rejected by attempt-bound producer output | CI drive-green session, 2026-10 (public project; identifiers withheld) | verified-ci | A startup identity error after a `--failed` rerun means the producer output pins the old attempt; only a full rerun realigns it |
| Confirmed merge-conflict suppression of PR runs | CI drive-green session, 2026-10 (public project; identifiers withheld) | verified-ci | Empty per-head run list plus the conflict state at the same head plus `git merge-tree` isolation plus an immediate post-resolution wave establishes the cause; the conflict-resolving push is the supported trigger |

## Detailed Case Notes

### ProjectOdyssey issue #252

The issue described configuration validation as failing in CI while passing locally and suggested
that detailed output was unavailable. Direct job-log retrieval showed `just: command not found`, so
the recipe never ran. The workflow version in the old run and a `git log -S "Install just"` search
then identified PR #254; subsequent main runs were green. The general lesson is evidence ordering,
not the project-specific command name.

### Containerized libKGEN failures

The investigation separated three boundaries that can otherwise be conflated:

- the host controls `core_pattern`, but its path is resolved in the crashing process namespace;
- an in-process signal handler can suppress kernel dumping, requiring ptrace interception;
- the executable and core must be symbolicated in a namespace where both paths exist.

The CI cases validated SIGILL handling, an exit-code side channel from gdb event callbacks, and
container-side symbolication. Exact scripts and workflow fragments remain available in the archived
v1.1.0 snapshot.

### CPU survey boundary

Six surveyed non-AVX-512 Intel hosts ran clean while the hosted environment remained flaky. That
observation rejected the simple “no AVX-512 always crashes” hypothesis; it did not prove the
virtualization/CPU-name mechanism. Treat the latter as a focused hypothesis requiring additional
compiler/runtime evidence.

### Attempt-bound producer output rejects failed-job reruns

A workflow that shards tests behind one gate job re-ran only the failed shard after a single
timing-sensitive test read an empty status payload from a worker process (verified flake; test
file untouched by the change under review). The rerun failed in under a minute: a policy job's
scope record embedded `run_id` and `run_attempt` from attempt 1, and the re-run shard validated
that record against its own attempt 2 environment before it ran any test. The aggregate gate job
then reported the required test job as failed. A full rerun regenerated the scope record for the
new attempt, every shard passed, the gate check succeeded, and the pull request merged on the
green result.

Name this branch early: an identity or configuration error at job startup that the original
attempt did not show is not a test regression. Repeating `--failed` reruns only bumps the
consumer attempt again, so the mismatch is permanent until a full rerun regenerates the producer
output. Verification: `verified-ci` (full rerun green; required gate success observed on the
same head).

### Confirmed merge-conflict suppression

A drive-green session pushed a rebased feature head and observed zero `pull_request` runs for
it: the per-head `actions/runs` listing was empty and the PR rollup showed no pending entries.
`gh pr view --json mergeable,mergeStateStatus` reported the conflict state at that head, and
`git merge-tree --write-tree <base> <head>` reproduced the conflict in one file. After a
base-updating push that preserved the PR delta, the full workflow wave started for the new head
within seconds, which converts the merge-conflict hypothesis into an established cause for this
evidence bundle. Review verdicts bound to the pre-rebase tree carried to the post-rebase head
because the tree hash was unchanged; the single conflict-resolved file received fresh review.

This case complements the unresolved missing-run case in the verification checklist: the
observation shape is identical (an empty per-head run list), but here the evidence bundle
confirms the cause and the recovery. Verification: `verified-ci` (run wave at the post-update
head succeeded on every applicable check; the pre-update head never carried any run).

## Verification Checklist

### Missing-run evidence boundary

A session observed an absent aggregate on a new PR head while documentation and provenance checks passed.
The previous head had a completed CI run. The current workflow declared a PR trigger without a path filter.
Legacy protection reported no protected branch, but the applicable ruleset required the aggregate.
An authorized administrator merge attempt was rejected for that missing check.
The available evidence did not establish why the new PR workflow had not started.

These observations support the missing-run and ruleset diagnostic branches.
They do not verify a recovery trigger or prove an event-delivery defect.
The source case identifiers and operational details are intentionally omitted.
The amendment has no claim of new end-to-end CI verification.

### Retained checks

- Preserve the run ID, job ID, failing step, exact signature, action versions, and head SHA.
- Mark reruns as transient or reproducible only after comparing the same signature.
- For cores, record host/container paths, signal, debugger version, inferior exit, and artifact.
- For CPU surveys, pin image digest and reproducer and report all iterations, including successes.
- Keep proposals labeled unverified until their own implementation and CI evidence exist.

## Amended 2026-10-30 — ghost-match evidence (v2.5.0)

A coordination-lane shard diagnosis quoted a compile error line that a filtered or
decorated log view appeared to show, and attributed it to a CI job. The bare job log,
fetched through the authenticated jobs API (about 60 KB), contained zero occurrences of
the quoted token. The job's only true failure was an unrelated assertion that mirrors an
import rule. The quoted hypothesis was withdrawn, and the report and the fix dispatch
were corrected to the verified failure.

Recovery used four steps: fetch the bare log into a file; count token occurrences
(zero); identify the true failed assertion in the bare log; correct the record. The
source case identifiers and operational details are intentionally omitted. The amendment
has no claim of new end-to-end CI verification.
