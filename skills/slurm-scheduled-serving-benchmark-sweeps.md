---
name: slurm-scheduled-serving-benchmark-sweeps
description: "Submit and run resumable LLM serving benchmark sweeps on shared preemptible Slurm queues. Use when: (1) a benchmark job fails before its payload because the submission environment never arrived, (2) an engine refuses to start when a reasoning parser is configured and engine warmup stays enabled, (3) a low-priority preemptible queue can interrupt a multi-concurrency sweep, or (4) automation must describe the state of a scheduled job."
category: tooling
date: 2026-10-27
version: "1.0.0"
user-invocable: false
tags:
  - slurm
  - sbatch
  - benchmarking
  - serving
  - preemption
  - environment-contract
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
| **Outcome** | Operational. Two complete job batches were lost to the export syntax failure below; each remaining constraint was recorded at the failure it prevents. Sweeps that used these constraints completed across queue preemptions with every completed level retained. |

## When to Use

- A sweep job is submitted with `sbatch --export` lists, and some variable names contain underscores.
- A benchmark engine is launched with a reasoning or structured-output parser while the engine's warmup request is enabled.
- A sweep is scheduled on a low-priority preemptible partition that runs behind production work.
- A lost measurement would force a full variant to run again because several levels write one file.
- You are about to say that a job is queued, running, or complete without reading scheduler state or a result file.

## The Submission Contract

Some clusters drop underscore variable names from the comma form of
`--export`. The failure is silent: the job starts, the payload runs without
its configuration, and the resulting error looks like an application defect.
Use the space form and prove the environment inside the job:

```bash
sbatch --export="ALL $cfg" --export=OTHER_VAR=value sweep.sbatch
# First statements of the job: echo the contract, then stop on absence.
echo "CFG=${CFG:?submission environment missing}"
```

The echo check turns a silent environment loss into an immediate, legible
failure at the start of the job instead of two lost batches.

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
sbatch --export="ALL $cfg" sweep.sbatch             # space form, never comma lists
grep -m1 "^CFG=" results/<id>.out                   # submission environment echoed in job
grep -c "Serving Benchmark Result" results/<lvl>.out  # one trailing block per level file
sacct -j <id> --format=JobID,State,ExitCode        # before any state claim
```

### Suggested Approach

1. Submit with the space form of `--export` and an in-job echo gate for every
   contract variable. Stop the job on absence.
2. Disable engine warmup whenever a reasoning or structured-output parser is
   configured. Record the skip flag in the run record.
3. Give each concurrency level a distinct seed and clear engine caches, per
   the warmup-regime entry.
4. Emit one result file per level with the level in the filename. Parse the
   trailing result block; never infer the level from inside the file.
5. Budget for preemption: one active job behind production work, long load
   time, and resumes that re-run only the levels with no artifact.
6. State each job's position only from `sacct` and artifact reads. Apply the
   payload-verification rule after completion.
7. Before publication, pass the retained artifacts through the triage rules in
   [benchmark-artifact-triage-pr-splitting](benchmark-artifact-triage-pr-splitting.md).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Comma-form `--export` lists | Submitted sweep batches with a comma-separated export list | The scheduler silently dropped every underscore-named variable, and two complete batches ran without their configuration | Use the space form and make the job echo and require each contract variable |
| Engine warmup with a reasoning parser | Left engine warmup enabled after configuring a reasoning parser | The warmup prompt was empty, the parser rejected it, and the engine failed during startup | Pass the engine warmup-skip flag whenever a reasoning parser is set |
| One seed for every concurrency level | Reused the level-1 seed and cache state for levels 2, 4, and 8 | The later levels were served from the first level's prefix cache, so their TTFT values measured cache hits, not cold prefill | Distinct seed plus cache flush per level; the rule and its measurement cases live in the warmup-regime entry |
| One result file per variant | Wrote all levels of a variant to one file | A preemption discarded every level completed in that run, not one level | One file per level; a preemption costs one level and resumes skip completed levels |
| State claims from memory | Described jobs as queued or complete without reading them | The claim disagreed with the scheduler and the artifacts | Read `sacct` and one output file before any state claim |

## Results & Parameters

### Configuration

```yaml
export_form: space                    # comma lists can drop underscore names
environment_gate: echo-and-require    # first job statements echo each contract variable
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
| Internal inference-serving benchmark campaign on a shared preemptible Slurm cluster | Multi-concurrency serving sweep behind production replicas | Two job batches were lost to the comma-form export; the warmup/parser conflict blocked engine startup until the skip flag; per-level files retained every completed level across a preemption. Project, model, host, queue, job, and issue identifiers are withheld under the privacy rules. See [notes.md](../skills/slurm-scheduled-serving-benchmark-sweeps.notes.md). |

## References

- [Inference Benchmark Warmup Regime](inference-benchmark-warmup-regime.md)
- [Slurm Batch Job Result Verification](slurm-batch-job-result-verification.md)
- [Benchmark Artifact Triage and PR Splitting](benchmark-artifact-triage-pr-splitting.md)
