# Ruff-Specific Rule Fixes — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| S101 production assertions replaced with runtime errors | [immutable source with PR #1142/#1211 evidence](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/ruff-specific-rule-fixes.md) | `verified-ci` | Retained as explicit-exception rule |
| C901 helper extraction | [ProjectHephaestus PR #1050](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1050) | `verified-ci` | Retained as cohesive extraction workflow |
| Repeated documentation defects exposed missing lint enforcement | [immutable source with PR #863–#867 evidence](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/ruff-specific-rule-fixes.md) | `verified-ci` | Generalized into the recurrence/root-cause decision rule |
| RUF022 and I001 autofix | [ProjectHephaestus issue #1189](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1189) | Verified in the recorded issue workflow | Retained; manual sorting rejected |
| RUF100 and script `--help` smoke contract | [ProjectHephaestus PR #1250](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1250) | `verified-precommit` | Retained with the narrower status |
| Ruff/mypy floor-bump regressions | [ProjectHephaestus issue #1313](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1313) | `verified-local` | Condensed into upgrade discovery and exact-byte rules |
| E501 and formatter failures in added tests | [ProjectHephaestus PR #1035](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1035) | `verified-ci` | Retained as all-changed-files gate |
| D413 after final docstring section | [ProjectHephaestus issue #1434](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1434) | `verified-local` | Retained with local-only boundary |

## Rule-specific details

- S101 repairs should preserve the intended exception contract and cover the failure path. An
  assertion is suitable for a test assertion, not a production precondition.
- C901 extraction is useful when branches map to distinct responsibilities. Purely redistributing
  complexity or adding a suppression does not improve maintainability.
- Ruff/isort owns `__all__` and import order. Alias-aware ordering is a material reason to prefer
  `ruff check --fix` over manual edits.
- D413 is checked by `ruff check`, not `ruff format`. The blank line belongs between the last
  section body and the closing triple quote.
- A tool-floor bump can change formatting, line-length results, inference, and ignore usage across
  untouched files. Run repository-wide discovery when the dependency changes.
- An executable script can pass Ruff but fail repository CLI conventions. Auto-discovered help and
  version tests remain part of the relevant gate.

## Verification boundary

The skill-level `verified-ci` status reflects the aggregate corpus. It must not be used to upgrade
the D413 and floor-bump cases beyond their recorded local evidence, or the script smoke case beyond
pre-commit evidence.
