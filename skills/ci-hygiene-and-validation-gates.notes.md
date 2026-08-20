# Notes: CI Hygiene and Validation Gates

Supporting evidence for
[`ci-hygiene-and-validation-gates`](./ci-hygiene-and-validation-gates.md). The complete prior main is
in [history](./ci-hygiene-and-validation-gates.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Deprecated identifier guard | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained scoped grep, dialect/exclusion, ASCII, and injected-failure rules |
| Standalone schema validation | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained complete inventory and existing-job placement |
| Stale-script detector | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained heuristic exit-zero versus invariant distinction |
| Dead required version-sync gate | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained exact-environment and clean/fail/restore verification |
| Tracked file under ignored build directory | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained whole-repo hard invariant and nondestructive handling |
| Already-wired CI issue | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/ci-hygiene-and-validation-gates.md) | verified-ci | Retained search-first and local discoverability comment fix |

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

## Compaction Disposition

- Kept in main: six triggers, exit policies, exact-environment rule, ruleset safety, two-sided tests,
  and nondestructive scratch handling.
- Moved here: repository names, prior PR sequence, and observed outputs.
- Archived only: long command listings and deprecated-name examples.
