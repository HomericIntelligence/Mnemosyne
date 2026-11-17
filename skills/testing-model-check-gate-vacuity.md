---
name: testing-model-check-gate-vacuity
license: BSD-3-Clause
description: "Prove that a model-checking gate can fail before you trust a green run. Use when: (1) a CI job or wrapper runs TLC or another model checker and the result gates a merge, (2) the gate passes but no one has seen it report a violation, (3) a parser reads a clean marker or a state count from tool output, (4) a safe configuration has no state-count floor, or (5) a mutation configuration decides whether the invariants are meaningful."
category: testing
date: 2026-11-17
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [testing, model-checking, tla-plus, tlc, ci-gate, vacuity, mutation-testing, false-pass, log-parsing, invariant, state-space]
---

# Model-Checking Gate: Prove It Can Fail

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-11-17 |
| Objective | Make a model-checking job evidence that the invariants hold, not evidence that the model was too small or that the parser did not read the result |
| Outcome | A gate with four parts: a safe configuration that passes, at least one mutation configuration that must fail with a named invariant, a distinct-state floor for each safe configuration, and a result parser that reads only summary lines and the tool exit code |
| Verification | verified-local — two gates were added and one was refined in one repository; the negative checks and the guard matrix ran locally, and the gate ran green in CI |

## When to Use

- A CI job runs a model checker and the result gates a merge or a release.
- The gate checks only that the tool printed a clean marker.
- A wrapper parses state counts, counterexample names, or a success string from tool output.
- A safe configuration is new and has no state-count floor.
- A mutation configuration exists, but its expected violation is a broad list.
- A reviewer asks whether the formal check is meaningful, or the model may have become vacuous after an edit.

## Verified Workflow

### Quick Reference

```text
PASS = exit code is the expected code
   AND the summary line reports the expected result
   AND (safe: no violation, distinct states >= floor)
   AND (mutant: a named invariant in the expected set is violated)
```

### Suggested Approach

1. Keep one safe configuration per model. It must report that no error was found.
2. Add one mutation configuration for each invariant that the gate claims to protect. A mutation
   removes one guard or adds one fault. The mutant must report a name from its expected set. An
   unexpected invariant name, or a clean mutant, fails the run.
3. Set a distinct-state floor for each safe configuration. Use about 50 to 65 percent of the current
   count. A model that collapses after an edit still prints the clean marker, so the marker alone
   cannot show that the interesting behavior is reachable.
4. Read the result from the tool exit code and the summary lines. Do not accept a printed marker as
   success. A specification can print the marker and then fail.
5. Parse only summary lines. A long run prints progress lines, and their counts can be smaller than
   the final count. A parser that reads the first count can report a fraction of the real state
   space.
6. Keep each mutation inside the domain of the real system. A value that the implementation cannot
   produce can violate the type invariant instead of the target invariant, and the run then depends
   on search order.
7. Reject a safe configuration with a zero or missing floor when you select the runs, so a new
   configuration cannot lose the guard silently.
8. Prove the gate with a negative check. Remove the guard from the **safe** model, run the gate, and
   confirm that the safe run fails. Restore the model. The mutant configurations prove detection of
   known faults. This check proves that the runner reads the model and not a fixture.

### Guard matrix

Test the runner with a fake subprocess when the tool is slow or unavailable. Each row must produce
the stated result:

| Input | Required result |
|-------|-----------------|
| Clean marker printed, tool exits non-zero | fail |
| Clean marker printed, an `Error:` line is present | fail |
| Safe run below the distinct-state floor | fail |
| Mutant reports no error | fail |
| Mutant reports an invariant outside the expected set | fail |
| Mutant reports an expected invariant, non-zero exit | pass |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|-----------------|---------------|----------------|
| 1 | Accepted any output that contained the clean marker. | A specification that printed the marker and then failed still passed. The tool exit code and an `Error:` line were ignored. | Require the expected exit code, and reject an error line before the marker counts. |
| 2 | Read the first `N distinct states found` match from the full output. | A run longer than the progress interval matched a `Progress(...)` line. Progress counts omit the thousands separator below 1000, so a safe run that reached tens of thousands of states reported 46. | Filter progress lines, and parse only the summary. |
| 3 | Allowed each mutant to report any of several invariants. | The first violating invariant hid the others, so one protected property was never exercised. | Add a run per invariant when the claim names several, and record which run covers each one. |
| 4 | Mutated a guard with a value that the implementation cannot produce. | The type invariant failed first, and the reported name depended on search order. | Keep fault values inside the real domain. |
| 5 | Relied on the safe run alone to show the invariants are meaningful. | A name guard makes some invariants unreachable in the safe configuration by construction, so the safe pass carries no weight for them. | State which invariants only the mutants exercise. |

## Results & Parameters

### Configuration

```yaml
safe_run:
  exit_code: 0
  summary: "No error has been found"
  reject_when: "an Error: line is present"
  floor: "0.5 to 0.65 of the observed distinct states"
mutant_run:
  exit_code: "non-zero"
  expected: "one invariant name from the configured set"
  reject_when: "no violation, or a name outside the set"
parse:
  source: "summary lines only"
  drop_prefix: "Progress("
```

### Expected Output

- One line for each configuration: model, configuration, kind, result, distinct states, generated
  states, depth, and elapsed time.
- A mutant line that names the violated invariant.
- A final line with the number of configurations that matched the expected result.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| An isolated service repository | Two gates added, then one refined after review | [notes](testing-model-check-gate-vacuity.notes.md) |

## References

- [TLA+ home page](https://lamport.azurewebsites.net/tla/tla.html)
- [TLA+ tools releases](https://github.com/tlaplus/tlaplus/releases)
- [Related skill: verification gate zero-test false pass](testing-verification-gate-zero-test-false-pass.md)
- [Related skill: derived-artifact gate non-vacuity](derived-artifact-gate-non-vacuity.md)
- [Related skill: union-containment vacuous pass](union-containment-vacuous-pass.md)