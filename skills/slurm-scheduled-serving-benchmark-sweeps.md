---
name: slurm-scheduled-serving-benchmark-sweeps
description: "Submit and run resumable LLM serving benchmark sweeps on shared preemptible Slurm queues. Use when: (1) a benchmark job fails before its payload because the submission environment never arrived, (2) the container payload does not inherit the batch shell's variables, (3) an engine refuses to start when a reasoning parser is configured and engine warmup stays enabled, (4) a low-priority preemptible queue can interrupt a multi-concurrency sweep, or (5) automation must describe the state of a scheduled job."
category: tooling
date: 2026-11-01
version: "1.1.0"
user-invocable: false
tags:
  - slurm
  - sbatch
  - benchmarking
  - serving
  - preemption
  - environment-contract
  - container-boundary
  - warmup
  - result-artifacts
  - scheduler-evidence
---

# Slurm-Scheduled Serving Benchmark Sweeps

<!-- Use [ASD-STE100](../docs/asd-ste100.md) for prose. Keep the headings and table
columns below so that the entry stays compatible with corpus retrieval. -->

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-27 |
| **Objective** | Make every job in a serving-benchmark sweep start with its full environment, keep results resumable per concurrency level, and let state claims come only from scheduler and artifact evidence. |
| **Outcome** | Operational. Two complete job batches were lost to the export syntax failure below; each remaining constraint was recorded at the failure it prevents. Sweeps that used these constraints completed across queue preemptions with every completed level retained. Re-verified on a second cluster: inline `--export` propagated nothing there, `--export-file` set only the first file line, and only inlined assignments plus positional arguments across the container boundary gave the payload its full contract. |

## When to Use

- A sweep job's environment is transferred with `sbatch --export` or
  `--export-file`, or inlined in a generated job script.
- A container step launched with Slurm's container plugin must receive the
  contract, or an import in the container breaks against a shadowing
  user-site package under `$HOME`.
- A benchmark engine is launched with a reasoning or structured-output parser while the engine's warmup request is enabled.
- A sweep is scheduled on a low-priority preemptible partition that runs behind production work.
- A lost measurement would force a full variant to run again because several levels write one file.
- You are about to say that a job is queued, running, or complete without reading scheduler state or a result file.

## The Submission Contract

`sbatch` environment transfer is site-specific. Measured behavior on two
clusters:

| Form | Measured result |
| ------ | ------ |
| Comma list `--export=A=1,B=2` | Silently dropped every underscore-named variable. |
| Inline space form `--export="ALL A=1 B=2"` | Propagated nothing; `/proc/self/environ` was empty. |
| `--export-file=FILE` | Set only the first line of the file. The remaining lines leaked into the step's stdout as literal text, which mimics a correct echo log. |
| `--export=ALL`, variables exported in the submitting shell | Propagated correctly. |
| Assignments inlined in a generated job script | Always reliable. |

Do not select a form from documentation. Generate a derived job script per
variant with the assignments inlined in the script body, and keep an
echo-and-require gate as the first statements of the job:

```bash
# submit.sh: derive a per-variant script, then submit it.
sed -n '1,/^set -uo pipefail$/p' sweep.sbatch >  "$tmp"
printf 'VARIANT_ID=%q\nGPUS=%q\n' "$id" "$gpus"   >> "$tmp"
sed -n '/^set -uo pipefail$/,$p' sweep.sbatch | tail -n +2 >> "$tmp"
sbatch "$tmp"

# Immediately after the strict-mode line in every job:
echo "VARIANT_ID=${VARIANT_ID:?submission contract missing}"
echo "GPUS=${GPUS:?submission contract missing}"
```

The gate turns silent environment loss into an immediate, legible failure at
the start of the job instead of a lost batch. The stdout leak of
`--export-file` makes the gate mandatory: a log that shows the values is not
proof that they became variables.

## The Container Boundary

A container step launched with Slurm's container plugin (for example Pyxis or
enroot) does not inherit the batch shell's variables. Pass the contract to
the in-container payload as positional arguments, then export them inside:

```bash
srun --container-image=... bash payload.sh "$VARIANT_ID" "$GPUS"
# payload.sh: VARIANT_ID="${1:?submission arguments missing}"; export VARIANT_ID
```

Treat `$HOME` differently from the container image: the home directory is
usually mounted, so a stale user-site package there can shadow a package in
the image and break engine imports with attribute errors on symbols that the
image's packages do not reference. Harden the payload with
`PYTHONNOUSERSITE=1` and prepend a controlled overlay directory to
`PYTHONPATH` when an import in the payload must be pinned.

## Warmup And Parsers

An engine warmup sends one empty or generic prompt before the server accepts
traffic. A configured reasoning parser can reject that prompt and stop the
engine at startup. When a reasoning parser is set, disable the engine warmup
with its skip flag, for example `--skip-server-warmup`. This is engine
operability, not the measurement-hygiene cause in
[inference-benchmark-warmup-regime](inference-benchmark-warmup-regime.md):
that entry covers warmup state that contaminates measurements; this case is
an engine that never reaches the measurement.

Cache-state hygiene applies with the same decision rule per sweep level:
give each concurrency level a distinct prompt seed and clear the prefix cache
(for example `--flush-cache`), or higher levels measure cache hits on the
first level's prompt and the TTFT values are fiction. Use the canonical
warmup-regime entry for the full rule; do not copy it here.

## Preemption-Tolerant Result Layout

Write one result file per concurrency level. Encode the level in the file
identity, because the per-level output of common harnesses carries no
in-file level marker: parse the trailing result block of each file (for
example the block that follows a `Serving Benchmark Result` header) and take
the level from the filename or submission record.

A preemptible low-priority queue typically runs one job at a time behind
production replicas, with a minutes-class model load on each launch.
Preemption mid-sweep then costs exactly one level, not the whole variant.
Do not buffer the whole sweep in one file.

## State Claims Only From Evidence

Before you describe a job's state, run `sacct` and read one output file. An
assertion like "queued" without either is a guess, and automation that
consumes the guess inherits it. For completed jobs, treat scheduler
State/ExitCode as an availability signal only and verify the payload exit
record and required artifacts per
[slurm-batch-job-result-verification](slurm-batch-job-result-verification.md).

## Verified Workflow

### Quick Reference

```bash
# submit host: derive one script per variant, then submit (no env plumbing)
printf 'VARIANT_ID=%q\nGPUS=%q\n' "$id" "$gpus" >> "$tmp"   # after strict-mode line
grep -m1 "^VARIANT_ID=" logs/<id>.out                      # batch-shell contract echoed
srun --container-image=... bash payload.sh "$VARIANT_ID" "$GPUS"  # container boundary
grep -m1 "== contract ==" logs/<id>.out                    # in-container contract echoed
grep -c "Serving Benchmark Result" results/<lvl>.out       # one trailing block per level file
sacct -j <id> --format=JobID,State,ExitCode                # before any state claim
```

### Suggested Approach

1. Generate a derived job script per variant with the contract assignments
   inlined after the strict-mode line. Keep an echo-and-require gate as the
   first statements; stop the job on absence. Do not rely on any
   `sbatch --export` form or on `--export-file` without measuring the
   transfer in a real job first.
2. Cross the container boundary with positional arguments to the in-container
   payload; re-export inside. Set `PYTHONNOUSERSITE=1` and, when an import
   must be pinned, prepend a controlled overlay directory to `PYTHONPATH`.
3. Disable engine warmup whenever a reasoning or structured-output parser is
   configured. Record the skip flag in the run record.
4. Give each concurrency level a distinct seed and clear engine caches, per
   the warmup-regime entry.
5. Emit one result file per level with the level in the filename. Parse the
   trailing result block; never infer the level from inside the file.
6. Budget for preemption: one active job behind production work, long load
   time, and resumes that re-run only the levels with no artifact.
7. State each job's position only from `sacct` and artifact reads. Apply the
   payload-verification rule after completion.
8. Before publication, pass the retained artifacts through the triage rules in
   [benchmark-artifact-triage-pr-splitting](benchmark-artifact-triage-pr-splitting.md).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Comma-form `--export` lists | Submitted sweep batches with a comma-separated export list | The scheduler silently dropped every underscore-named variable, and two complete batches ran without their configuration | Inline the assignments in a generated script and make the job echo and require each contract variable |
| Inline space-form `--export` | Submitted with `--export="ALL A=1 B=2"` after the comma failure | The form propagated nothing; `/proc/self/environ` inside the job was empty | Inline export forms are not trustworthy on every site; measure the transfer with the gate |
| `--export-file` with one line per variable | Put the six contract variables in a file, one per line | Only the first line became a variable; the other five lines leaked into the step's stdout and looked like a correct echo log | A log that shows the values is not proof they became variables; require the gate to pass, not the values to appear |
| Variables passed to a container step | Exported the contract in the batch shell, then `srun --container-image` | The container payload did not inherit the batch shell's variables; the payload gate failed inside the container | Pass positional arguments through the container boundary and export them inside the payload |
| Container imports with a mounted home directory | Launched the engine in a container with `$HOME` mounted | A stale user-site package under `$HOME` shadowed the image's package; the engine failed on a symbol that the image's own packages do not use | Set `PYTHONNOUSERSITE=1` in the payload; pin imports with a controlled `PYTHONPATH` overlay |
| Engine warmup with a reasoning parser | Left engine warmup enabled after configuring a reasoning parser | The warmup prompt was empty, the parser rejected it, and the engine failed during startup | Pass the engine warmup-skip flag whenever a reasoning parser is set |
| One seed for every concurrency level | Reused the level-1 seed and cache state for levels 2, 4, and 8 | The later levels were served from the first level's prefix cache, so their TTFT values measured cache hits, not cold prefill | Distinct seed plus cache flush per level; the rule and its measurement cases live in the warmup-regime entry |
| One result file per variant | Wrote all levels of a variant to one file | A preemption discarded every level completed in that run, not one level | One file per level; a preemption costs one level and resumes skip completed levels |
| State claims from memory | Described jobs as queued or complete without reading them | The claim disagreed with the scheduler and the artifacts | Read `sacct` and one output file before any state claim |

## Results & Parameters

### Configuration

```yaml
export_form: inline_assignments       # measured: export forms are site-specific; a generated script always works
environment_gate: echo-and-require    # first job statements echo and require each contract variable
container_boundary: positional_args   # container steps do not inherit the batch shell; re-export inside
python_env: PYTHONNOUSERSITE=1        # a mounted $HOME can shadow container packages; pin with PYTHONPATH overlay
warmup_skip_when_reasoning_parser: true
flush_cache: true
distinct_seed_per_concurrency_level: true
result_artifact: one_file_per_level
level_identity: filename_or_submission_record   # files carry no in-file marker
parse: trailing result block          # e.g. after a serving-result header
preemption_budget:
  active_jobs: one behind production work
  model_load: minutes class
  loss_per_preemption: one level
state_evidence: [sacct, one_output_file_per_claim]
```

### Expected Output

- One parseable result file per completed level, each with a trailing result
  block and the level in its identity.
- A sweep resume that re-runs only levels without an artifact.
- A state record where every claim cites a `sacct` line or a named artifact.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal inference-serving benchmark campaign on a shared preemptible Slurm cluster | Multi-concurrency serving sweep behind production replicas | Two job batches were lost to the comma-form export; the warmup/parser conflict blocked engine startup until the skip flag; per-level files retained every completed level across a preemption. |
| Second internal serving sweep on a different shared Slurm cluster, 2026-10-31..11-01 | 14-variant sweep launched through container steps | Inline `--export` propagated nothing (`/proc/self/environ` empty); `--export-file` set only the first line and leaked the rest to stdout; a container step dropped the batch shell's variables; a stale user-site package under `$HOME` shadowed the image's package. The pilot variant then ran to completion under the derived-script, positional-argument, and python-env constraints above. Project, model, host, queue, job, and issue identifiers are withheld under the privacy rules. See [notes.md](../skills/slurm-scheduled-serving-benchmark-sweeps.notes.md). |

## References

- [Inference Benchmark Warmup Regime](inference-benchmark-warmup-regime.md)
- [Slurm Batch Job Result Verification](slurm-batch-job-result-verification.md)
- [Benchmark Artifact Triage and PR Splitting](benchmark-artifact-triage-pr-splitting.md)
