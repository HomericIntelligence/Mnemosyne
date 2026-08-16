---
name: docs-readme-subpackage-drift-regression
license: BSD-3-Clause
description: "Replace documentation tests that pin prose, headings, package inventories, dates, or manually maintained counts with observable navigation and source contracts. Use when: (1) a README tree test requires every package or tracked path to appear in prose, (2) privacy or architecture tests assert literal wording, (3) documentation should prove local links resolve, public indexes reach an artifact, or executable source contracts remain valid."
category: documentation
date: 2026-08-05
version: "2.0.0"
user-invocable: false
verification: unverified
history: docs-readme-subpackage-drift-regression.history
tags:
  - documentation-tests
  - behavior-contracts
  - markdown-links
  - source-contracts
  - readme-navigation
  - published-artifacts
  - count-drift
  - prose-pinning
---

# Documentation Drift Tests Should Validate Navigation Contracts

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-05 |
| **Objective** | Prevent documentation regressions without turning README inventories, headings, editorial phrases, dates, emails, source comments, or docstrings into frozen APIs. |
| **Outcome** | Proposed replacement: discover links from the documents, validate that local targets resolve, prove public artifacts are reachable from actual indexes, and bind normative documentation to executable source contracts. The implementation plan was not executed in this session. |
| **Verification** | `unverified` — source and test targets were identified, but no Hephaestus implementation, focused test run, pre-commit run, or CI result was produced. |
| **History** | [changelog](./docs-readme-subpackage-drift-regression.history) |

The original version correctly fixed a missing README entry, but it recommended an exact
subpackage inventory and manually synchronized counts. That creates editorial coupling:
adding an internal package forces prose edits even when navigation and user-facing behavior
remain valid. Preserve the real contract instead of every current sentence or tree row.

## When to Use

- A test parses a README directory tree and requires every importable subpackage or tracked
  path to appear in prose.
- Documentation tests assert exact headings, section numbers, dates, email addresses,
  historical wording, source comments, or a function's docstring.
- A public policy or guide must exist and be reachable from one or more public indexes.
- Architecture documentation names an executable table, registry, schema, or routing symbol
  and the repository already has a source-contract validator.
- A repository change updates only an internal inventory, yet unrelated documentation tests
  fail because they mirror the current tree or a hand-maintained count.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until CI confirms.

### Quick Reference

```python
from pathlib import Path
from urllib.parse import unquote, urlparse

from project.validation.markdown import extract_markdown_links, validate_file_links


def resolved_local_targets(source: Path) -> set[Path]:
    return {
        (source.parent / unquote(urlparse(target).path)).resolve()
        for target, _line in extract_markdown_links(source.read_text(encoding="utf-8"))
        if not urlparse(target).scheme and urlparse(target).path
    }


def test_document_navigation_resolves(repo_root: Path, document: Path) -> None:
    assert extract_markdown_links(document.read_text(encoding="utf-8"))
    assert validate_file_links(document, repo_root)["broken_links"] == []
```

For a published artifact, test existence, link validity, and reachability from the real
public indexes:

```python
def test_policy_is_published_and_reachable(policy: Path, indexes: list[Path]) -> None:
    assert policy.is_file()
    assert all(policy.resolve() in resolved_local_targets(index) for index in indexes)
```

For normative architecture content, select the production-owned source contract rather
than comparing copied route rows or prose:

```python
contract = next(
    item
    for item in SOURCE_CONTRACTS
    if item.document == "docs/architecture.md" and item.selector == "ROUTES"
)
assert validate_source_contracts(repo_root, contracts=(contract,)) == []
```

### Detailed Steps

1. **Name the observable obligation.** Classify the requirement as navigation, artifact
   publication, reachability, link resolution, or parity with an executable source symbol.
   If deleting or rewording a sentence would not change that obligation, do not test the
   sentence.
2. **Reuse repository validators.** Prefer the project's Markdown link checker and
   doc-to-source contract checker over bespoke regexes. They encode path resolution,
   anchors, exclusions, and source selectors once.
3. **Discover links from the document.** Parse the Markdown being tested and validate every
   discovered local target. Do not maintain a second list of expected links solely for the
   test.
4. **Test reachability when discoverability matters.** For privacy, security, licensing, or
   contribution artifacts, assert the target is linked from the actual public indexes. Mere
   file existence does not prove users can find it.
5. **Bind normative docs to executable authorities.** If a document promises to mirror a
   route table or registry, invoke the existing source-contract validator for that selector.
   Do not inspect source comments, docstrings, or copied row counts.
6. **Keep prose editorial.** Remove exact section numbers, headings, phrases, dates, emails,
   historical PR wording, package counts, and directory-tree membership from regression
   assertions unless they are a documented public machine-readable API.
7. **Run the focused documentation tests and the repository's link/lint gate.** A formatter
   or editorial rewrite should remain free to change prose while broken navigation and
   source drift still fail.

## Verified Workflow

No verified workflow exists for the v2 recommendation yet. This heading is retained for
the current Mnemosyne validator; use **Proposed Workflow** above and do not treat it as
CI-confirmed guidance.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Exact README package inventory | Required every importable subpackage and tracked root path to appear in a directory-tree code block | Internal layout changes forced editorial updates even when README navigation stayed valid | Validate links the README actually exposes; do not require prose to mirror the full tree |
| Manually maintained counts | Pinned package totals, section totals, heading counts, or example counts | Counts drift whenever content is reorganized and can be updated in lockstep without proving useful behavior | Discover the current set from its executable registry or document and test its contract |
| Literal policy wording | Asserted dates, email addresses, required section names, and exact phrases in a policy | Editorial improvements fail tests while a broken or unreachable artifact can still satisfy the strings | Test that the artifact exists, its links resolve, and public indexes reach it |
| Source-string and docstring pinning | Compared architecture prose with comments, source fragments, or internal docstrings | Formatting and refactors become breaking changes; matching text does not prove runtime routing parity | Reuse a source-contract validator tied to an executable selector |
| File existence alone | Checked that a public document was committed | A valid file can still be orphaned and undiscoverable | Pair existence with parsed-link reachability from the intended public indexes |

## Results & Parameters

### Contract selection matrix

| Documentation obligation | Durable assertion | Avoid |
| ------------------------ | ----------------- | ----- |
| README navigation | At least one discovered link; all discovered local links resolve | Complete package/tree inventory |
| Published policy | File exists; its own local links resolve; public indexes link to it | Literal date, email, or heading text |
| Architecture-to-code parity | Repository source-contract validator passes for the named executable selector | Copied route tables, source comments, docstrings |
| General Markdown quality | Link parser plus repository Markdown lint/build | Phrase counts and editorial wording snapshots |

### Proposed ProjectHephaestus checks

```bash
uv run pytest \
  tests/unit/docs/test_automation_loop_architecture.py \
  tests/unit/docs/test_privacy_policy.py \
  tests/unit/validation/test_readme_subpackage_tree.py -v
uv run pre-commit run --all-files
```

The Hephaestus-specific reusable seams named by the plan are:

- `hephaestus.validation.markdown.extract_markdown_links`
- `hephaestus.validation.markdown.validate_file_links`
- `hephaestus.validation.doc_maintenance.SOURCE_CONTRACTS`
- `hephaestus.validation.doc_maintenance.validate_source_contracts`

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Issue #1188 / PR #1272, original v1 behavior | The original exact-inventory guard was verified in CI; that version is archived in history. |
| ProjectHephaestus | Issue #1950 behavior-first test refactor plan | The v2 navigation/source-contract replacement is proposed only; implementation and CI validation are pending. |
