---
name: generated-child-job-bounded-by-parent-duration
description: "Bound every generated scheduler job by the duration of the record or grant it serves. Use when: (1) a controller job and its child jobs are generated from one duration, (2) a child job runs with no time limit or the scheduler default, (3) a short registration can hold a node for days, or (4) a duration change does not update the baked job limits."
category: architecture
date: 2026-11-25
version: "1.0.0"
user-invocable: false
tags: [scheduler, walltime, generated-job, child-job, duration, sbatch, compatibility]
---

# Generated Child Jobs Share the Parent Duration Bound

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-25 |
| **Objective** | Make every scheduler job that a duration-bearing record generates end no later than that duration. |
| **Outcome** | Successful. The controller job already had a time limit. The child job now receives the same duration as an explicit scheduler argument. Focused tests and CI passed. |

A service can generate more than one scheduler job for one record. One job runs the controller or daemon. Another job runs the work. If only one job gets a time limit, the other can hold its allocation after the record ends. Check every generated job, not only the long-lived one.

## When to Use

- A registration, lease, reservation, or grant has a duration, and the service generates a controller job and one or more child jobs.
- A child job renders placement and resources but no time limit.
- A short request holds an allocation for the scheduler default or for an unbounded period.
- The duration can change after the job starts.
- A test checks the controller limit but not the child limit.

## Verified Workflow

### Quick Reference

Apply one duration to every generated job:

```bash
# Controller job
#SBATCH --time=02:00:00

# Child job: pass the same bound on the scheduler command.
sbatch --time=02:00:00 ... child.sbatch
```

```python
duration = parse_duration(user_value)
controller_walltime = slurm_walltime(duration)
child_walltime = slurm_walltime(duration)
```

### Suggested Approach

1. **List every generated job.** Find each `sbatch`, `srun`, or scheduler submission that the record creates. A controller job and a child job usually come from different functions. Include optional jobs such as donors, replicas, or cleanup work.
2. **Name the duration owner.** Use one parsed duration value. Do not parse the user text again in another layer. Convert once to the scheduler walltime shape.
3. **Put the bound in the child job.** Add the time value to the child scheduler arguments or its script header. A child job with no `--time` can inherit a long site default.
4. **Do not rely on the controller to stop the child.** A controller can be killed before it runs its cleanup. A separate scheduler limit keeps the child bounded even when the controller does not clean up.
5. **Validate the walltime once.** Accept the scheduler's supported shapes and reject free text. Use the same validator for controller and child values.
6. **Test each job kind.** Assert the controller limit and the child limit from one short duration. A test of the controller alone misses the reported defect.
7. **State the modify boundary.** If a later duration change does not re-render the jobs, the baked limits can disagree with the record. Either update the live limits or refuse the change with a clear reason. Keep that work separate when it needs a scheduler mutation.
8. **Preserve older jobs.** A job that is already queued or running keeps its submitted script or arguments. The fix applies to a new submission. Do not rewrite a running job to force the new bound.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Bound only the controller job | Added a time limit to the long-lived daemon job | The child work job used the site default and held its node after the record ended | Enumerate every generated job and give each one the duration |
| Rely on controller cleanup | Expected the controller to cancel the child at its end | The controller can be killed first, so it never runs the cancel path | Put an independent scheduler limit on the child |
| Use the scheduler default | Omitted `--time` because the site default looked short | The default can be days or unbounded and can exceed the record duration | Make the bound explicit and derived from the record |
| Change the record only | Updated the stored duration without re-rendering the jobs | The baked scheduler values stayed at the old duration | Update the live limits, or refuse the change and name the stale limit |
| Test only the controller | Asserted one script had the expected time | The child had no time value, so the defect passed the test | Test each generated job kind from one duration |
| Rewrite a running job | Tried to change the limit of an in-flight job | A running job keeps its submitted text or arguments | Apply the fix to new submissions; leave older jobs to their own lifetime |

## Results & Parameters

### Configuration

```yaml
duration_source: parsed_user_duration_seconds
walltime_shape: "[[D-]HH:]MM:SS"
controller_job: explicit --time from duration_source
child_job: explicit --time from duration_source
validation: one validator for both values
test: one short duration, assert controller and child limits
```

### Expected Output

- The controller job and every child job have a time limit no longer than the record duration.
- A short request cannot hold a node after the record ends.
- The child job is bounded even when the controller does not run cleanup.
- Older running jobs keep their submitted behavior.
- The focused tests and the scheduler-limit assertions pass.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-backed capacity-sharing service | A short registration generated a controller job and a child work job | The child job received the registration duration as an explicit scheduler limit. Focused tests and required checks passed. |

## References

- [Slurm walltime expiry outage diagnosis](slurm-walltime-expiry-outage-diagnosis.md): classify a job that already ended at its limit.
- [Slurm step lifetime server ownership](slurm-step-lifetime-server-ownership.md): keep a server alive across client steps.
- [Generated child commands take explicit arguments, not environment](generated-child-explicit-args-not-environment.md): pass per-run values without ambient state.
