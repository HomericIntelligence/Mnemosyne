---
name: preflight-phase-pinned-job
description: "Give a pre-rendered one-shot job's startup preflight a 'ready' check (the pinned target is valid) separate from a long-lived service's 'active' check (the pinned target is the current one). Use when a batch or stage job rendered by one generation of a long-lived renderer fails its preflight after the renderer's target rotates underneath it, with an error that names a release or revision mismatch."
category: architecture
date: 2026-11-27
version: "1.0.0"
user-invocable: false
tags:
  - preflight
  - pinned-revision
  - one-shot-job
  - hot-swap
  - generation-mismatch
  - batch-job
  - startup-guard
---

# Preflight Phase: "Ready" For A Pinned One-Shot Job, "Active" For A Live Service

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-27 |
| **Objective** | Stop a pre-rendered one-shot job from failing its startup preflight solely because the renderer's current target moved on after the job was rendered. |
| **Outcome** | Operational. One preflight function served both a live service and one-shot jobs with a single check: the pinned target must equal the renderer's current target exactly. After the renderer's target rotated (a routine hot swap), every already-rendered one-shot job failed preflight with a generic "release target" mismatch, even though its own pinned target was still a completely valid, intact build. Adding a second preflight phase that only confirms the pinned target is valid (not that it is current) fixed every affected job class without weakening the live-service check. |

## When to Use

- A long-lived renderer stamps a job script with the identifier of its own current target at render time (a source revision, a release tag, a build ID), and a startup preflight later compares that stamp against "the current target" rather than "a valid target".
- A batch, probe, checkpoint, or other one-shot job fails at startup with a release, revision, or target mismatch message, and the rendering component has since rotated (a hot swap, a redeploy, a promotion) between render time and run time.
- You design or review a preflight/precondition check shared by a long-lived service and short-lived jobs that the same renderer produces.
- The failure is intermittent and timing-dependent: a job rendered and queued just before a rotation fails; one rendered just after does not.

## Verified Workflow

### Quick Reference

```text
Two different questions, two different checks:
  live service  -> "is my pinned target still THE current one?"   (active)
  one-shot job  -> "is my pinned target still A valid one?"       (ready)

A preflight shared by both must branch on which question applies.
Checking "active" for a one-shot job makes every job rendered by an older
generation fail after the very next routine rotation, with no actual defect
in the job or its pinned target.
```

### Suggested Approach

1. **Separate the two questions explicitly.** A live service holding a stale pinned target is a real defect: it is serving the wrong generation and must refuse or roll forward. A one-shot job holding a now-non-current pinned target is normal: it was rendered before the rotation and still names a real, intact, readiness-marked build. Do not let one function answer both questions the same way.
2. **Add a phase (or equivalent discriminator) to the shared preflight**, defaulting to the live-service behavior so existing callers are unaffected. Give one-shot/batch job renderers the other phase explicitly.
3. **Keep the one-shot phase fail-closed on real defects.** It still verifies that the pinned tree exists, carries its readiness marker, and matches its recorded revision. It only drops the requirement that the pinned tree be the renderer's *current* target. Removing the pinned tree (or corrupting its record) must still fail the job.
4. **Find every one-shot caller, not just the one that failed.** The same renderer usually backs more than one job class (a pull/fetch stage, a probe, a checkpoint seal/verify, a generic job submitter). Trace the preflight call site into each class; the generic error text from one failing job is rarely the only affected class.
5. **Expect already-rendered job scripts to keep the old, stricter phase.** A fix to the renderer's default changes only jobs rendered after the fix. A job script rendered before the fix still embeds the old phase text and must be resubmitted (re-rendered) to pick up the new behavior; it is not retroactively repaired.
6. **Verify with a direct preflight-function test, not a rendered-text test.** Build a minimal pinned-target tree where the "current" pointer deliberately differs from the pinned target. Assert the new phase accepts it and the original phase still refuses it. A test that only checks the rendered script's literal flag text does not prove the behavior.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Assume the one-shot job's own target selection was wrong | Suspected the job script picked the wrong backing store or pointer for its pinned target | The job already pinned the correct, intact target; the preflight was comparing it to the renderer's now-different current target, not validating the target itself | Read the actual preflight comparison before changing the job's own target-selection logic |
| Treat the error text as the root cause | The message named a generic "release target" mismatch and was read as a layout or naming defect | The message is generic; the real cause was a phase question (current vs. valid) collapsed into one check | Trace a generic mismatch message to its exact comparison before proposing a layout fix |

## Results & Parameters

### Configuration

```yaml
preflight:
  phase: active   # default; live service: pinned target must equal current target exactly
  # one-shot / batch job renderers pass:
  phase_override: ready  # pinned target must be valid (exists, readiness-marked, record matches); need not be current
```

### Expected Output

- A one-shot job rendered before a routine rotation still starts and runs correctly after the rotation.
- A live service whose pinned target has drifted from current still refuses to start (unchanged, fail-closed).
- A one-shot job whose pinned target was actually removed or corrupted still fails preflight (unchanged, fail-closed).
- Job scripts rendered before the fix keep the old behavior until resubmitted.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A source-build renderer backing a long-lived control service and several one-shot batch jobs (fetch/stage, probe, checkpoint seal/verify, generic submit) | A routine hot swap of the renderer's current target broke every already-rendered one-shot job with a generic release-target mismatch | Fixed by adding a `ready` phase to the shared preflight for one-shot callers, default `active` preserved for the live service. Verified by a direct preflight-function test with a deliberately non-current but valid pinned target. |

## References

- [Release validation describes its own subject](release-validation-running-source-mismatch.md) — a related but distinct question: whether validation evidence describes what a lane currently runs, not whether a job's preflight should require currency
- [Rotate a Comet source lane end to end](comet-source-lane-revision-rotation.md) — the deliberate-rotation playbook this defect surfaces around; that entry covers performing a rotation, this one covers a one-shot job surviving a rotation it did not initiate
- [ASD-STE100 technical English](../docs/asd-ste100.md)
