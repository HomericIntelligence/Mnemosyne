---
name: testing-env-gated-marker-misfire-deselection
description: "Reproduce a project's CI-equivalent test result on a development host where an environment-gated test marker cannot fire. Use when: (1) a full-suite run on a development host reports a large error population concentrated in one marked suite instead of skips, (2) the host carries the gated environment's production tooling but not the suite's dedicated test fixture, so a presence-keyed auto-skip cannot fire, (3) a merge or review gate needs a local result that matches CI semantics, or (4) an env-gated suite may already have contacted the shared production system during a failed run."
category: testing
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - pytest
  - env-gated
  - markers
  - deselection
  - auto-skip
  - presence-predicate
  - production-tooling
  - shared-infrastructure
  - ci-parity
  - harness-override
  - pollution-audit
---

# Environment-Gated Marker Misfire and CI-Equivalent Deselection

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Produce a CI-equivalent test result on a heterogeneous development host whose suites carry environment-gated markers, without multi-hour error storms or production-system side effects. |
| **Outcome** | Operational rule derived from one live suite forensic. A presence-keyed auto-skip passed on a host that carried the production tooling but not the dedicated test fixture; the gated suite errored for two hours against shared infrastructure. Deselecting the marker reproduced CI semantics exactly: every erroring test mapped one-to-one onto the deselected population, the rest stayed green, and a queue and accounting audit confirmed no production pollution. |
| **Verification** | verified-live in one full-suite forensic (2026-10-30): error-to-marker mapping, deselection run, and pollution audit each observed. Single-case evidence; the invariant follows from marker-gate semantics, not frequency. |

## When to Use

- A test suite declares environment-gated markers (cluster, GPU, live broker, network) whose support files auto-skip when the environment is absent, and CI relies on that skip on clean runners.
- A full-suite run on a development host reports a large error population instead of skips, with abnormal duration or side effects.
- The host has the gated environment's production tooling on `PATH` (login nodes, shared build hosts) but not the suite's dedicated test fixture.
- A gate decision needs a local result that matches CI semantics, and harness overrides or ignore lists would silently change which tests run relative to the project gate.
- An environment-gated suite may already have contacted the shared production system during the failed run.

## Verified Workflow

### Quick Reference

```text
Errors concentrate in one environment-marked population
  -> attribute them to the gate before any regression claim.
Production tooling on PATH is not the suite's fixture:
  the auto-skip path does not exist on such hosts.
CI-equivalent local run = the project's gate selection
  with the environment marker DESELECTED (-m "not <marker>"),
  with the project's own addopts and gate flags intact.
After any misfire, audit the shared production system
  (queue, accounting, data) before trusting the green re-run.
```

### Suggested Approach

1. Read the marker contract before running anything. The marker registration states what the gate requires, how the fixture comes up, and what CI does with the marker: a clean CI runner auto-skips the population, and the job that owns the suite may enforce an execution floor so a skip cannot pass as its result. This defines CI-equivalent for a local run: everything CI's gate job runs, minus the population that skips there.
2. Attribute the error population to the gate, not to the change under test. Collect the marker population directly (for example `pytest -m "<marker>" --collect-only`) and match it against the erroring tests. A one-to-one mapping with the rest of the suite green is environmental evidence. Record the mapping and counts; a raw "N errors" line is not a regression claim.
3. Diagnose the skip predicate before rerunning. Presence-keyed predicates (binary on `PATH`, environment variable set, port open) pass on hosts that carry production tooling without the dedicated fixture. There the suite's fixtures run against the production system: they error, run long, and can submit or mutate real work. On such hosts the auto-skip path is unavailable; do not rerun the unchanged selection hoping the skip fires.
4. Reproduce CI semantics by deselecting the marker: run the project's normal gate selection with `-m "not <marker>"`, keeping the project's addopts and gate flags intact. Do not neutralize harness configuration (for example an addopts override) to make a constrained environment pass: an override can silently drop the project's opt-in flags, so the "full" run skips populations the project gate includes, and it can also re-expose the gated suite. Record the deselected count in the reported result so downstream readers can reconstruct what the run covered.
5. Audit the shared system after a misfire, before trusting the green re-run. Check the production queue, accounting, and data stores the gated suite could have touched during the erroring run; attribute, report, and clean any suite-produced artifacts. A clean audit is part of the run evidence.
6. Tighten the predicate when you own the suite. A gate that checks the dedicated fixture (health check, sentinel configuration, explicit opt-in variable) cannot misfire on tooling hosts. Marker deselection stays the operator-side recovery; the tighter predicate removes the hazard for the next host.

### If a step is unavailable

- No marker declared for the failing population: this rule does not apply; treat the errors as real failures.
- The harness cannot deselect by marker: deselect by explicit path exclusion and record both sides of the split; do not leave the equivalence implicit in a green summary alone.
- No access to the shared system's audit surface: state that limit in the report; the green re-run alone does not clear pollution risk.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Report the raw erroring run as evidence against the change | A full-suite run on a production-tooling host reported over a hundred errors against a reviewed head | Every erroring test mapped one-to-one onto the environment-marked population; the rest of the suite was green | Attribute the error population to the gate before any regression claim |
| Neutralize harness configuration to fit a constrained environment | Overrode the harness's configured options to make an isolated environment viable | The override silently dropped the project's opt-in gate flags (a whole marked population skipped), re-exposed the gated suite the defaults hold back, and the "full" run no longer matched the project gate | A run under neutralized configuration is not the project gate; keep the project's own options and deselect only the environment marker |
| Rerun unchanged and expect the auto-skip | Repeated the full selection on the host with production tooling | The presence predicate passed, so fixtures ran against the shared system and errored for hours | On tooling hosts the auto-skip path does not exist; deselect explicitly |

## Results & Parameters

### Configuration

```text
errors concentrate in one marked population -> attribute to the gate; verify the
                                               one-to-one mapping; report as
                                               environmental
host has production tooling, no fixture     -> auto-skip unavailable; deselect the
                                               marker; audit the shared system
CI-equivalent local run                     -> project gate selection minus the
                                               environment marker; project addopts
                                               intact; deselected count recorded
after any misfire                           -> queue/accounting/data audit before
                                               trusting the green re-run
you own the suite                           -> tighten the predicate to the fixture
                                               (health check, sentinel, opt-in)
```

### Expected Output

- A forensic result that states the error-to-marker mapping explicitly, with the deselection-run counts (including the deselected population size) recorded, and no green claim resting on neutralized harness configuration.
- A misfire report that includes the production-system audit result (clean, or artifacts found and handled), not only the green re-run.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Scheduler-integration repository on a shared-compute login host | Full-suite forensic: the erroring population mapped exactly onto the environment-marked suite; the deselection run matched CI semantics with the same green counts in minutes instead of hours; the production queue and accounting audit found no suite-attributed jobs | [notes](testing-env-gated-marker-misfire-deselection.notes.md) |

## References

- [pytest-configuration-discovery-and-ci-pitfalls](pytest-configuration-discovery-and-ci-pitfalls.md) — plugin and addopts hazards; its rule that a neutralized-harness run is not the full gate binds this entry's override warning.
- [testing-env-gated-skip-fail-installed-cli-lane](testing-env-gated-skip-fail-installed-cli-lane.md) — the inverse direction: absence-keyed skips that silently lose coverage. Here, presence passes and the suite gains dangerous runs.
- [testing-env-gated-live-broker-gtest-suite](testing-env-gated-live-broker-gtest-suite.md) — designing the environment gate itself; this entry covers operating safely where the gate cannot fire.
- [verify-delegated-agent-claims-run-full-suite](verify-delegated-agent-claims-run-full-suite.md) — the full-suite discipline this entry refines on CI-divergent hosts, where the full selection is not CI's selection.
