# Notes: CI Hygiene and Validation Gates

Supporting evidence for
[`ci-hygiene-and-validation-gates`](./ci-hygiene-and-validation-gates.md). The complete prior main is
in [history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/ci-hygiene-and-validation-gates.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Deprecated identifier guard | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained scoped grep, dialect/exclusion, ASCII, and injected-failure rules |
| Standalone schema validation | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained complete inventory and existing-job placement |
| Stale-script detector | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained heuristic exit-zero versus invariant distinction |
| Dead required version-sync gate | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained exact-environment and clean/fail/restore verification |
| Tracked file under ignored build directory | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained whole-repo hard invariant and nondestructive handling |
| Already-wired CI issue | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained search-first and local discoverability comment fix |
| Required gate moved to warning | Planning review of an open change, delivery base revision `d33ae7500bbfe9fe029b606420bcdd1708692fb3` | planned, not executed | Added Pattern 7; adds the verdict-class table, the anti-suppression step, and the gate-owner rule |

## Case Details

The dead-gate case showed why clean success is insufficient: the original required context computed a
result that did not enforce its named contract. Testing under a rich pixi environment masked a
missing dependency in the actual editable-install invocation. The corrected check used dependencies,
the pinned pixi command, and synthetic violations for both version and lockfile legs.

The build-directory case separated ignored runtime state from tracked package content. A live loop
regenerated logs, so deleting them was futile and outside the invariant. `git ls-files build/` became
the hard gate with whole-repository hook semantics.

The already-wired case found a prior CI job before editing. Repeating the step would create drift;
doing nothing would preserve the discoverability gap. A local task-runner comment linked the recipe
to the existing CI context.

## Warning-Downgrade Case

This case came from a planning review. No downgrade merged at the delivery base, so
the pattern is guidance from repository evidence, not a verified outcome.

Observations from the repository:

- A required workflow rejected `continue-on-error: true` in workflow files. The test
  suite also asserted that this key is absent from selected steps. A soft-fail step
  was therefore not available, and the decision had to move inside the script.
- One target script was a library that a different required check imported. The
  library had no workflow step of its own. Reading the file list alone gave the
  wrong required context.
- Parts of the scope already printed a `WARNING` line and recorded a list of
  warnings in an evidence summary. That summary was the documented input for the
  acceptance step, so only the remaining non-zero exits needed to change.
- A test counted the exact number of warning call sites in one verifier. The count
  pinned the contract, so the test changed with the source.

Resulting rule: classify each verdict, not each file. Give every warning a reader,
and keep fail-closed behavior for evidence that cannot be parsed and for the
objective invariant that the gate also protects.

## Compaction Disposition

- Kept in main: seven triggers, exit policies, exact-environment rule, ruleset safety, two-sided
  tests, nondestructive scratch handling, and the warning-downgrade verdict classes.
- Moved here: repository names, prior PR sequence, and observed outputs.
- Archived only: long command listings and deprecated-name examples.
