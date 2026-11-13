---
name: ci-slow-test-phase-probe-ab-dispatch
description: "Find which phase makes a few CI test cases slow, with pollution-safe probes and a measured A/B dispatch. Use when: (1) one test module or a handful of parametrized cases dominates runner minutes and the cost sits inside an application or CLI invocation whose output the test parses or compares, (2) instrumentation prints inside that invocation corrupt the captured output and fail the instrumented run, (3) a focused dispatch input rejects a boolean keyword expression, (4) a dispatch checkout fails because a hand-typed commit SHA is not a real ref, or (5) a performance hypothesis must be accepted or rejected with a before/after measurement instead of reasoning."
category: ci-cd
date: 2026-11-12
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [ci-cost, slow-tests, phase-probe, file-sink, junit-system-out, ab-dispatch, focused-run, captured-stdout, dispatch-selector, hypothesis-rejection]
---

# Probe Slow CI Test Phases Without Polluting Captured Output

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-12 |
| **Objective** | Name the phase that makes slow CI test cases expensive, without breaking the instrumented run, and accept or reject each optimization hypothesis by measurement. |
| **Outcome** | Successful; probe artifacts reached CI evidence uploads, one hypothesis was rejected by A/B measurement, and the breakdown identified the real cost. |

## When to Use

- A small number of test cases consume most of the runner minutes, and the cost is inside one application or CLI invocation per test round.
- The test parses or compares the captured output of that invocation, so ordinary print probes corrupt the data under test.
- A focused CI dispatch rejects a keyword expression, or a checkout rejects the supplied commit SHA.
- A performance hypothesis (a database or runtime tuning change) needs a measured verdict before it merges.

## Verified Workflow

### Quick Reference

Instrument through a file sink, not stdout, and verify each hypothesis with a paired dispatch:

```python
# Test-side probe helper: file sink when inside the app, stdout otherwise.
_PROBE_SINK = [None]

def _probe(label):
    line = f"PROBE {label} {elapsed():.2f}"
    if _PROBE_SINK[0] is not None:
        with _PROBE_SINK[0].open("a") as handle:
            handle.write(line + "\n")
        return
    print(line, flush=True)
```

```yaml
# Pytest configuration: carry test-level stdout into uploaded JUnit evidence.
[tool.pytest.ini_options]
junit_logging = "system-out"
```

### Suggested Approach

1. **Rank before you probe.** Sum per-test times from an existing JUnit artifact
   or result log. Confirm that a few cases, not a broad tail, hold the cost.
2. **Add a file sink for in-app probes.** Set a per-test sink path at test
   start. Probe helpers write to the sink when it is set and to stdout when it
   is not. Application or CLI invocations capture stdout, so any probe printed
   inside them lands in the data the test asserts on.
3. **Dump the sink at test level.** After each invocation returns, print the
   file contents. Test-process stdout reaches pytest's JUnit `system-out`
   capture, so the lines travel in the uploaded evidence artifact even when the
   case fails later.
4. **Enable `junit_logging = "system-out"`** in the pytest configuration so the
   evidence artifact carries the probe lines for passing cases too.
5. **Dispatch a focused run on a probe branch.** Use one focused job, the same
   selector before and after, and copy the exact full commit SHA into the
   dispatch input. Parse the artifact, not the job log, for per-case numbers.
6. **Read the chronology.** Print elapsed-since-test-start with each probe so
   the lines order themselves into rounds. Name each round (fixture, first
   invocation, retry, resume) at the probe site.
7. **A/B every hypothesis.** Keep the baseline numbers, change one thing, and
   rerun the identical selector. Accept a measured rejection; revert the change.
8. **Clear the cheap suspects first.** Fixture construction, directory walks,
   and setup copies often measure near zero. Delete them from the suspect list
   with data, not judgment.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| 1 | Print probes from inside the application invocation. | The harness captures stdout inside the invocation, so the probes corrupted the JSON receipt the test parses and the instrumented run failed. | Route in-app probes through a per-test file sink; dump the file at test-process level. |
| 2 | Put database tuning flags in the CI service container options. | Service options are container-runtime create arguments, not process command arguments; the flags never reached the database. | Set server settings per connection through client DSN query parameters, which map to startup settings. |
| 3 | Reason that disabling the per-commit flush wait must speed up durable test writes. | The paired dispatch measured every case slower; the wait was not a meaningful share of the cost. | Measure each hypothesis with a before/after focused run and accept measured rejection. |
| 4 | Pass a boolean keyword expression to a dispatch input. | The input validates a single identifier and rejected the expression before any test ran. | Use one substring identifier that selects the target cases, or add a safer selector input. |

## Results & Parameters

- **Sink lifetime:** one file per test case; create it empty at test start so
  the first dump shows the complete round.
- **Probe sites that matter:** fixture build, each invocation round, and the
  per-round phase you suspect. Two elapsed values per line (call elapsed and
  elapsed since test start) order the lines without a timestamp.
- **Expected outputs:** an evidence artifact whose JUnit `system-out` holds one
  probe block per case; per-case totals from the JUnit `time` attribute.
- **Selection:** a single identifier substring that matches the target cases
  (parametrized identifiers included) keeps the focused job short.
- **A/B pairing:** identical selector, identical profile, baseline numbers
  recorded before the change; compare per-case totals, not job wall time.

## References

- Companion evidence and generalized measurements:
  [ci-slow-test-phase-probe-ab-dispatch.notes.md](ci-slow-test-phase-probe-ab-dispatch.notes.md).
- Related corpus entries: `ci-failure-triage-and-diagnosis` (failure, not cost),
  `ci-test-partition-new-modules` (tier inventory, not runtime cost).
