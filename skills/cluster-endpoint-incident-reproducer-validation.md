---
name: cluster-endpoint-incident-reproducer-validation
description: "Build and harden cluster endpoint incident reproducer PRs after strict review. Use when: (1) a model-serving/HPC incident needs a checkout-to-validation reproducer, (2) a shell reproducer allocates Slurm or similar cluster resources, (3) artifacts may contain private prompts, responses, tokens, endpoint metadata, profiler traces, or control-plane evidence, (4) a strict PR review produced blockers around security, cleanup, reproducibility, shell quoting, tests, operator docs, or CI."
category: debugging
date: 2026-07-02
version: "1.1.0"
user-invocable: false
verification: verified-ci
history: cluster-endpoint-incident-reproducer-validation.history
tags:
  - incident-reproducer
  - cluster
  - hpc
  - slurm
  - endpoint
  - artifact-security
  - cleanup
  - dry-run
  - strict-review
  - validation
  - profiler
  - shell-quoting
  - operator-contract
---

# Cluster Endpoint Incident Reproducer Validation

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-02 |
| **Objective** | Turn a strict PR review of a cluster endpoint incident reproducer into a concrete fix list and a reusable validation contract. |
| **Outcome** | Checkout-to-validation reproducers and issue-local profiler helpers were hardened for private artifacts, non-launching testability, allocation-safe cleanup, shell-safe command construction, reproducibility evidence, operator docs, tests, and CI. |
| **Verification** | verified-ci |
| **History** | [changelog](./cluster-endpoint-incident-reproducer-validation.history) |

## When to Use

- A PR adds or changes a reproducer for a model-serving, endpoint, parser, corruption, or semantic-behavior incident on an HPC or Slurm-style cluster.
- The reproducer can allocate nodes, register/start an endpoint, query HTTP APIs, or write prompts/responses/control metadata to artifacts.
- A strict review reports blockers across security/privacy, cleanup safety, reproducibility metadata, test coverage, typing, docs, or CI, and you need to convert them into implementation work.
- You need a testable prepare/dry-run path that proves manifests, configs, command logs, and artifact metadata without allocating GPUs or binding a live control socket.
- Cleanup correctness depends on allocated node IDs, Slurm job IDs, or endpoint registration state, and failures may occur between allocation and startup.
- The incident helper launches a profiler such as Nsight Systems or Nsight Compute inside an H200 Slurm container and builds a second-stage `bash -lc` command.
- A review flags env-only helper contracts, unvalidated enum/numeric inputs, missing operator docs, or missing shell syntax tests for a cluster script.

## Verified Workflow

### Quick Reference

```bash
# Static shell validation for reproducer scripts.
bash -n scripts/<incident-reproducer>.sh
bash -n docs/runbooks/<incident>/profile_<incident>_kernels.sh

# Focused tests before full validation.
pytest tests/<focused-reproducer-tests>.py -q
pytest tests/<focused-http-or-parser-tests>.py -q
pytest tests/<focused-profiler-helper-tests>.py -q

# Python tooling only on Python files; shell files need shell-specific checks.
ruff format scripts/<helper>.py tests/<focused-python-tests>.py
ruff check scripts/<helper>.py tests/<focused-python-tests>.py
mypy scripts/<helper>.py scripts/<incident-helper>.py

# Repo-level gates after focused checks.
git diff --check
pre-commit run --files <staged-files>
scripts/validate.sh

# GitHub final state.
gh pr checks <pr-number> --repo <owner>/<repo>
gh pr view <pr-number> --repo <owner>/<repo> --json mergeStateStatus,mergeable,statusCheckRollup
```

### Detailed Steps

1. **Translate strict review into a fix list.** Treat the review as concrete work, not commentary. Use the review categories as implementation buckets: security/privacy, cleanup safety, reproducibility metadata, test coverage, typing, docs, and CI.
2. **Add a non-launching prepare/dry-run mode.** The reproducer should be able to generate manifests, configs, replay metadata, and artifact README files without allocating GPUs, registering endpoints, starting services, binding control sockets, or sending live HTTP requests. This makes the shell contract testable in restricted sandboxes and CI.
3. **Make private artifact handling explicit.** Set `umask 077`, create shared log/artifact directories with mode `700`, and write token-bearing or prompt/response-bearing files with mode `600`. Add an artifact README warning that full prompts, responses, endpoint metadata, and control-plane evidence are private incident evidence.
4. **Keep live tokens out of replay logs.** Do not print control tokens or token-bearing environment values into command logs. Write replay metadata using shell-safe quoting (`printf '%q'`) or a structured serialization format. Validate required environment variables and ports before interpolating them into shell commands, YAML, manifests, HTTP URLs, or profiler command lines.
5. **Capture allocation metadata immediately.** Record allocated node IDs and Slurm job IDs immediately after allocation, before endpoint registration or startup. Failures can occur after allocation but before the endpoint has a started node ID, so cleanup cannot rely only on "started endpoint" metadata.
6. **Make cleanup release allocated resources, not just started endpoints.** Cleanup should release based on the allocation metadata captured in step 5. Do not clear allocated node IDs unless release succeeds; failed release attempts are evidence and must remain visible for follow-up cleanup.
7. **Preserve reproducibility and evidence.** Keep endpoint metadata, launch command, parser/serving flags when relevant, control registry path, allocated node IDs, Slurm job IDs, and best-effort `squeue`/`sacct` snapshots before and after cleanup. Treat these as audit evidence, not optional logs.
8. **Expose a non-launching command preview for profiler helpers.** If the helper allocates Slurm resources or starts a profiler, add `--print` or `--dry-run` so tests and reviewers can inspect the exact `srun` command without needing GPUs. Prefer CLI flags with environment fallbacks over env-only contracts.
9. **Validate script inputs before Slurm launch.** Reject invalid profiler enum values (`nsys`/`ncu`), nonnumeric ports/counts/seeds, missing required paths, and unknown options before constructing `srun`. A bad local option should fail with exit 2 before any cluster command is printed or executed.
10. **Quote nested shell command boundaries explicitly.** For scripts that build an inner `bash -lc` body, shell-quote host-provided values before interpolating them into the inner script, and keep arrays for outer `srun` arguments. Add tests that use paths with spaces to prove the quoted command survives preview mode.
11. **Register operator-facing contracts.** Add the helper to shell syntax tests and operator-script contract docs. Document required CLI flags, env fallbacks, private artifact expectations, and any intentionally dangerous serving flags such as `--trust-remote-code`.
12. **Separate replay controls from production fixes.** For determinism investigations, document that slower global batch-invariant or deterministic kernels are replay/verification controls unless the serving engine owns a production path with measured performance. Do not present them as the default incident fix when the bug is local to cache shape or scheduler contracts.
13. **Test the shell reproducer contract directly.** Add tests for bash syntax, private file modes, shell-safe replay logs, allocation cleanup behavior, Slurm evidence capture, prepare-only artifact generation, profiler `--print` output, enum/numeric validation, and operator docs coverage. Use fake control commands or temp fixtures so tests do not need a live cluster.
14. **Add focused coverage for nearby Python behavior.** If review identified HTTP error logging gaps, parser edge cases, or profiler extractors, add targeted tests for those paths rather than relying on the reproducer integration path to exercise them indirectly.
15. **Verify in layers.** Run focused pytest first, then `bash -n`, `git diff --check`, Ruff format/check only on touched Python files, direct mypy for touched Python scripts, pre-commit on staged files, full repo validation, and finally GitHub PR checks plus mergeability.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Formatting shell with Python tooling | Ran Ruff over a Bash reproducer script | Ruff cannot parse shell, so the check fails before validating anything useful | Use `bash -n` and shell-specific tests for shell scripts; limit Ruff to Python files |
| Dry-run tests used an ephemeral local socket | Prepare-mode tests still tried to bind or probe a local control port | Restricted sandboxes can reject socket binding or networking, making non-network tests flaky | Make the control port overrideable and provide a prepare-only mode that does not bind sockets |
| Cleanup keyed only off started endpoint node ID | Release logic looked for node IDs only after endpoint startup | A failure after allocation but before startup leaves allocated nodes unreleased | Capture allocated node IDs immediately and use them as the cleanup source of truth |
| Clearing allocation metadata too early | Cleanup erased allocated node IDs even when release failed | The evidence needed for manual cleanup disappeared | Clear allocation metadata only after release succeeds |
| Raw environment interpolation in generated commands | Shell/YAML snippets interpolated raw env values directly | Tokens can leak, quoting can break, and replay artifacts become malformed or unreproducible | Validate inputs first; quote with `printf '%q'` or serialize structurally |
| Treating command logs as safe by default | Replay logs included live control-token context | Command logs persist and are often shared during incident review | Keep tokens out of logs; store private control metadata in mode-600 evidence files |
| Env-only profiler helper contract | Required `MODEL_PATH`, `CONTAINER_IMAGE`, and `OUTPUT_DIR` only through environment variables | Reviewers and tests could not see the contract at the call site, and missing values failed late | Add explicit CLI flags with env fallbacks and keep `--print` output copy-pasteable |
| Unvalidated profiler mode | Let arbitrary `PROFILER` values flow into branch logic | Typos can silently select the wrong path or fail after allocation | Validate enum-like inputs before printing or executing `srun` |
| Unquoted second-stage `bash -lc` values | Built the inner script from host paths and flags without shell quoting | Paths with spaces or shell metacharacters can break commands or become injection surfaces | Shell-quote each host-provided value before interpolation; test with paths containing spaces |
| Shell helper omitted from quality gates | Added a new cluster shell helper without including it in syntax tests or operator docs | The PR can pass Python tests while the operator script remains unreviewed and syntactically unguarded | Add shell syntax coverage plus operator-script contract docs in the same PR |
| Treat deterministic kernels as the production answer | Proposed global batch-invariant or deterministic kernels for a local cache-shape bug | They can be useful for replay but may carry performance cost and solve a broader problem than needed | Keep production guidance shape-stable and engine-owned; use deterministic kernels as controls unless measured otherwise |

## Results & Parameters

### Reproducer Contract Checklist

| Area | Required Contract |
|------|-------------------|
| Prepare mode | Generates manifests/configs/replay metadata/artifact README without GPU allocation, endpoint startup, network calls, or socket binding |
| Artifact permissions | `umask 077`; directories mode `700`; prompt/response/token/control files mode `600` |
| Replay metadata | Shell-safe or structured; no live tokens in command logs; validated env vars and ports before interpolation |
| Profiler preview | `--print`/dry-run mode prints exact `srun` commands without allocating GPUs; tests assert good and bad cases both appear |
| Profiler inputs | CLI flags with env fallbacks; `nsys`/`ncu` enum validation; integer validation for ports, launch counts, token counts, and seeds |
| Nested shell quoting | Host-provided paths and flags are shell-quoted before inner `bash -lc` interpolation; outer command remains an argv array |
| Allocation metadata | Captured immediately after allocation; includes node IDs and job IDs before register/start |
| Cleanup | Releases allocated node IDs; preserves node IDs if release fails; records before/after `squeue` and `sacct` snapshots best-effort |
| Evidence files | Endpoint metadata, launch command, parser/serving flags when relevant, profiler reports/exports/summaries, control registry path, node IDs, job IDs, cleanup snapshots |
| Static tests | Bash syntax, file modes, command-log quoting, allocation cleanup contract, Slurm evidence contract, profiler preview contract, prepare-only generation |
| Focused Python tests | HTTP error logging, parser edge cases, and profiler extractor edge cases when touched by the incident reproducer PR |
| Validation | Focused pytest, `bash -n`, `git diff --check`, Ruff on Python files only, mypy on touched Python scripts, pre-commit on staged files, full validation, GitHub checks and mergeability |

### Verification Evidence

Verified in example-org/inference-service PR #262 on 2026-06-25 at commit `48c2e1f` with sanitized context only:

- Local validation passed with the repo's explicit virtualenv command: `PYTHON=.venv/bin/python INFERENCE_SERVICE=.venv/bin/inference_service scripts/validate.sh`.
- Test result: 791 passed, 8 skipped, coverage 82.22%.
- Pre-commit on staged files passed.
- Direct mypy passed for the touched endpoint/status and incident-trial Python helpers.
- GitHub PR checks were green; `mergeStateStatus` was `CLEAN`; `mergeable` was `MERGEABLE`.

Do not copy raw prompts, responses, model/checkpoint names, internal hostnames, tokens, or corrupted output snippets into a durable skill or shared PR body. Keep this skill generic; cite the PR only as the verified workflow context.

Verified again in example-org/inference-service PR #327 on 2026-07-02 with sanitized context only:

- Strict review findings on an issue-local H200 Slurm profiler helper were fixed with CLI flags, `--print`, early enum/numeric validation, shell quoting for nested `bash -lc`, operator contract docs, and shell syntax coverage.
- Local focused tests passed: `tests/test_issue257_profile_prefix_cache_kernels.py`, `tests/test_issue257_nsys_kernel_extractor.py`, and `tests/test_quality_gate_scripts.py` reported 75 passed.
- Local full validation passed with `just validate`: 1051 passed, 9 skipped.
- The pre-push hook passed: 1059 passed, 1 skipped.
- GitHub checks passed, including `validate`, `pre-commit`, `sast`, `secrets`, `python-sca`, CodeQL, and action/python analysis.
