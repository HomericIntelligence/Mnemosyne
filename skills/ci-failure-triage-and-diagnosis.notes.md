# CI Failure Triage and Diagnosis — Notes

Supporting case evidence for the canonical
[`ci-failure-triage-and-diagnosis`](ci-failure-triage-and-diagnosis.md) skill. The exact
30,593-byte v1.1.0 main is archived once in
[`ci-failure-triage-and-diagnosis.history`](ci-failure-triage-and-diagnosis.history), with
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

## Verification Checklist

- Preserve the run ID, job ID, failing step, exact signature, action versions, and head SHA.
- Mark reruns as transient or reproducible only after comparing the same signature.
- For cores, record host/container paths, signal, debugger version, inferior exit, and artifact.
- For CPU surveys, pin image digest and reproducer and report all iterations, including successes.
- Keep proposals labeled unverified until their own implementation and CI evidence exist.
