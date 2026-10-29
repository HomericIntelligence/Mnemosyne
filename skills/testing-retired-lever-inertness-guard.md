---
name: testing-retired-lever-inertness-guard
description: "Ship executable proof that a retired runtime lever is inert and stays retired. Use when an issue asks to remove an environment variable, flag, or configuration hatch and its branches are already absent from source: deliver a set-the-lever rejection test with a non-vacuity control, a resurrection source scan, and acceptance criteria bound to step-qualified CI evidence instead of fabricated deletions."
category: testing
date: 2026-10-27
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - lever-retirement
  - feature-flag-removal
  - env-var-hatch
  - inertness-guard
  - non-vacuity-control
  - resurrection-scan
  - acceptance-criteria-evidence
  - ci-step-qualification
  - overtaken-by-events
  - regression-guard
---

# Retired Runtime-Lever Inertness Guard

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-27 |
| **Objective** | Close a lever-removal issue whose code was already removed by earlier history, with CI artifacts that prove the retired lever has no effect and cannot return silently. |
| **Outcome** | Successful — the removal issue closed on guards only: one behavioral inertness test family with a non-vacuity control, one resurrection source scan, and each acceptance criterion bound to concrete evidence. Zero source edits. |

A removal issue can be valid at filing and discharged later by a merged change
before a worker arrives. The lever branches are gone, so there is nothing to
delete. Closing with no artifact leaves two gaps: nothing proves the retired
lever is inert, and nothing stops a future change from resurrecting the
identifier. The residual deliverable is executable proof, not fabricated
deletions.

## When to Use

- An issue or plan asks to remove a runtime lever (environment variable, flag,
  or configuration hatch) after stated acceptance criteria.
- `rg` on the current tree and `git log --all -S '<LEVER>' -- src/` both return
  zero hits: the branches are already absent, and the removal predates your
  branch. This is the overtaken-by-events disposition from
  [planning-verify-issue-premise-before-implementing](planning-verify-issue-premise-before-implementing.md),
  not a false premise.
- The gates the lever used to relax still exist and still reject (mode checks,
  capability checks, policy checks), so an inertness assertion has a concrete
  target.
- Do not use this skill for a false-premise issue that names code which never
  existed; that intent belongs to
  [automation-moot-issue-regression-guard-pattern](automation-moot-issue-regression-guard-pattern.md).

## Verified Workflow

### Quick Reference

```bash
# 1. Prove the lever is historically gone, not merely absent on this branch.
git log --all -S '<RETIRED_LEVER>' -- src/     # zero hits: identifier inert
rg -n '<RETIRED_LEVER>' src/                    # zero hits on current tree

# 2. Qualify acceptance evidence per criterion.
gh run view <run-id> --json jobs,conclusion
#   The required gate step must be "success" on that run.
#   A run where the required step was "skipped" does not qualify.
git merge-base --is-ancestor <removal-commit> <ci-head-sha>

# 3. Baseline before editing: same pinned environment, detached at the base
#    commit. Pre-existing failures that reproduce there are not yours.

# 4. Guards: inertness test + non-vacuity control + resurrection scan
#    (examples below).
```

### Suggested Approach

1. Date the removal and keep the overtaken-by-events disposition. Implement
   only the residual asks. Never re-create branches or machinery that a merged
   change deliberately deleted.
2. Bind each documented acceptance criterion to one verifiable artifact, and
   record the command and the observed fact in the PR body:
   - a closed prerequisite issue that satisfied an earlier criterion;
   - a documented runbook step, cited by file and line, present on the current
     default branch;
   - a CI run where the required step succeeded on a head that descends from
     the removal commit. Qualify runs at step granularity, not by overall
     conclusion: a green run whose required step was `skipped` never exercised
     the unset configuration. An earlier candidate run can fail this test; name
     why it does not qualify.
3. Ship the inertness guard with a non-vacuity control. For each retired
   lever: set the lever, then require the gate to still reject a violating
   fixture. Pair every rejection with an acceptance on a clean fixture under
   the same lever, so the rejection is attributable to the intended mechanism
   and the guard cannot be vacuous.

```python
import pytest

RETIRED_LEVERS = ("EXAMPLE_RELAXED_GATE_CHECKS", "EXAMPLE_ALLOW_UNSUPPORTED_ACL")


@pytest.mark.parametrize("lever", RETIRED_LEVERS)
def test_retired_lever_does_not_relax_mode_gate(monkeypatch, lever, dir_factory):
    """With a retired lever set, the gate must still reject a dirty mode."""
    monkeypatch.setenv(lever, "1")
    dirty = dir_factory(mode=0o2775)  # setgid and group-writable
    with pytest.raises(GateError):
        mode_gate.check_service_dir(dirty)


@pytest.mark.parametrize("lever", RETIRED_LEVERS)
def test_gate_accepts_clean_dir_with_retired_lever_set(monkeypatch, lever, dir_factory):
    """Non-vacuity control: a clean 0o755 fixture passes with the lever set,
    so the rejection above is attributable to the permission bits and not to
    the environment."""
    monkeypatch.setenv(lever, "1")
    mode_gate.check_service_dir(dir_factory(mode=0o755))  # must not raise
```

   Fixture discipline decides whether the guard means anything: pass the
   observed device, owner, and group through unchanged and force the value
   under test (mode) so that only the branch under test can reject. A fixture
   that lets a second branch reject hides a lever that still works.

4. Ship the resurrection scan, so a reintroduced identifier fails the suite.

```python
def test_retired_levers_are_absent_from_source():
    src = Path(__file__).parents[1] / "src"
    offenders = [
        path
        for path in src.rglob("*.py")
        if any(lever in path.read_text(encoding="utf-8") for lever in RETIRED_LEVERS)
    ]
    assert not offenders, f"resurrected lever identifiers: {offenders}"
```

5. Leave failures you did not cause untouched. Baseline the touched modules at
   the base commit first; a failure family that reproduces identically there
   belongs to its own tracker. Your delta is `+N passed`, zero new failures.
   Do not widen a tier or profile to absorb the new tests without checking the
   tier inventory test.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Accept the first green CI run as the acceptance proof | The candidate run had a green conclusion, but its required provenance step was `skipped`. | A run that skips the gating step never exercised the unset configuration, so the criterion stayed unmet. | Qualify acceptance runs at step granularity; a later run with the step `success` on a descendant head qualified instead. |
| Rejection-only guard | Assert only that a dirty fixture raises with the lever set. | A suite-wide environment fault (or a lever that still relaxes a different branch) passes the same assertion; the guard is vacuous. | Pair each rejection with a clean-fixture acceptance under the same lever; the contrast attributes the rejection to the intended branch. |
| Delete source that is already gone | Prepare a source diff for the removal the issue asked for. | Zero hits in `src/`; the deletion landed in earlier history, so the diff is empty and the issue would close with no resurrection barrier. | Convert the residual ask into executable guards; the guards, not a diff, close the issue. |

## Results & Parameters

Parameters to capture in the PR body:

- `retired_levers`: the exact retired identifiers the guards set and scan for.
- `removal_evidence`: the zero-hit `git log --all -S` and `rg` results, and
  the change that removed the branches.
- `criterion_evidence`: one row per documented criterion — artifact type
  (closed issue, runbook line, CI run), command, and observed fact; for CI,
  the required step's conclusion and the head's ancestry from the removal
  commit.
- `baseline_delta`: pinned-environment test counts at the base commit versus
  the branch on the touched modules; expected shape `+N passed`, zero new
  failures.
- `preexisting_failures`: failures reproduced at the base commit and left for
  their tracker, with the tracker reference.

Expected output of a correct delivery:

- Every acceptance criterion row names a verifiable artifact; no row rests on
  an overall run conclusion alone.
- Inertness guards fail if any retired lever regains an effect, and the
  clean-fixture controls fail if the rejection becomes environment-attributable.
- The resurrection scan fails on any reintroduced identifier in source.
- The issue closes on test-only changes when the branches are already absent.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Python deployment-gate package (privacy-screened) | Lever-removal issue closed by a test-only PR; guards merged and CI green on the default branch. | Delivery record in [notes](testing-retired-lever-inertness-guard.notes.md). |

## References

- [planning-verify-issue-premise-before-implementing](planning-verify-issue-premise-before-implementing.md) — overtaken-by-events disposition and per-ask triage that select this endgame.
- [automation-moot-issue-regression-guard-pattern](automation-moot-issue-regression-guard-pattern.md) — sibling for false-premise issues; AST guards for structural invariants.
