# TDD Workflow and Test-Coverage Expansion — Case Notes

These notes retain project-specific outcomes and detailed case distinctions moved out of the
retrievable main. The complete superseded main is archived only in the history companion.

## Case Index

| Case | Source | Verification |
| --- | --- | --- |
| ProjectScylla script expansion: 29% to 65%, then 100% | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/tdd-workflow-and-test-coverage-expansion.md) | verified-ci |
| ProjectScylla quoted-filename parser regression | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/tdd-workflow-and-test-coverage-expansion.md) | verified-ci |
| ProjectHephaestus subprocess-heavy validation module | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/tdd-workflow-and-test-coverage-expansion.md) | verified-ci |
| ProjectHephaestus circular-import guard | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/tdd-workflow-and-test-coverage-expansion.md) | verified-ci |
| Extracted post-merge session drivers | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/tdd-workflow-and-test-coverage-expansion.md) | verified-ci |
| ProjectOdyssey all-covered hash audit | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/tdd-workflow-and-test-coverage-expansion.md) | verified-ci |
| EvaluationService seven-PR coverage swarm | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/tdd-workflow-and-test-coverage-expansion.md) | verified-local |

## Script-Coverage Campaigns

ProjectScylla issue #1162 / PR #1343 expanded covered scripts from 10/34 (29%) to 22/34
(65%) with 453 tests across 13 files. Issue #1358 / PR #1383 completed the remaining 12 scripts,
reaching 34/34 with 130 more tests. The useful method was not the raw count: targets were grouped
by purity, subprocess cost, and operational impact, and existing tests were searched first.

Other recorded outcomes include 106 tests across five source modules (74.93%), five command-handler
tests appended to an existing file, and 65 fully mocked tests reaching 99% in a subprocess-heavy
module. These numbers describe those repositories and are not universal thresholds.

## Parser Bug Discovery

ProjectScylla PR #1467 / issue #1447 exposed a bug in quoted `git status --porcelain` parsing.
`stdout.strip().split("\n")` removed the meaningful first status-column space for a single line;
existing multi-line fixtures passed because trimming occurred only at the ends. `splitlines()` plus
positive and negative argv assertions made the regression non-vacuous.

## Import-Layer Guard

After the `hephaestus.github` to `hephaestus.automation` cycle was removed, the retained guard used
fresh subprocesses for both import orders and an AST walk across every Python file in the lower
layer. This catches cached-import false greens and function-local forbidden imports.

## Extracted Session Drivers

ProjectHephaestus issue #1362 / PR #1363 added 11 tests to the existing helper file rather than the
new filename sketched in the issue. Key interface facts were:

- the Claude session helper returned `(stdout, metadata)`;
- the Codex helper returned an object with `.stdout`;
- the compact helper returned a direct boolean;
- `cwd` was keyword-passed;
- a dry-run or agent-mode guard had to prove the downstream call was absent;
- a named raising helper was clearer than a generator-throw lambda.

## All-Covered and Swarm Cases

ProjectOdyssey issue #4051 / PR #4859 found all requested hash behaviors already covered. The right
output was a requirement-to-test mapping and zero duplicate tests. By contrast, the
EvaluationService campaign genuinely needed seven isolated PRs and 518+ tests. Its CI workflow
manually enumerated test files, so each worker had to update the appropriate shard and audit new
test docstrings before delivery.

## Compaction Disposition

- Kept in main: decision rules, audit-first workflow, exact mocking contracts, parser and import
  guard mechanics, discovery rules, copy-ready commands, and named failures.
- Moved here: project counts, issue/PR narratives, and detailed case outcomes.
- Archived only: repeated templates, long transcripts, and the complete prior main.
