---
name: architecture-claude-md-agents-md-single-source-ecosystem-migration
description: "How to consolidate CLAUDE.md into canonical AGENTS.md without leaving policy consumers, templates, guards, tests, workflows, or scanners reading the compatibility pointer. Use when: (1) replacing a substantive CLAUDE.md with an exact AGENTS.md pointer; (2) preserving directives from multiple guidance documents with an executable section-scoped contract; (3) retargeting live repository consumers atomically while keeping narrow compatibility aliases; (4) sweeping an ecosystem where already-migrated repos should be detected before work begins."
category: architecture
date: 2026-07-21
version: "2.0.0"
user-invocable: false
verification: unverified
history: architecture-claude-md-agents-md-single-source-ecosystem-migration.history
tags:
  - claude-md
  - agents-md
  - single-source-of-truth
  - agent-contract
  - policy-consumers
  - semantic-inventory
  - executable-contract
  - pointer-stub
  - compatibility-alias
  - stale-reference-audit
  - atomic-migration
  - ecosystem-migration
---

# Consolidating Repository Agent Guidance into AGENTS.md Without Orphaning Consumers

> **Warning:** The exhaustive policy-consumer workflow added in v2.0.0 is a reviewed
> implementation plan, not an end-to-end result. Treat it as a hypothesis until the
> focused tests, anchor check, static checks, full suite, and CI all pass.

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-21 |
| **Objective** | Make `AGENTS.md` the sole authoritative agent contract, reduce `CLAUDE.md` to an exact compatibility pointer, and migrate every live authority-bearing consumer without losing directives. |
| **Outcome** | The lightweight document migration was previously verified locally across an ecosystem. The stronger policy-consumer workflow is planned for Hephaestus but has not been executed end-to-end. |
| **Verification** | unverified — v2.0.0 changes the core recommendation; the comprehensive workflow and its CI result are pending. |
| **History** | [changelog](./architecture-claude-md-agents-md-single-source-ecosystem-migration.history) |

The dangerous failure mode is not a broken Markdown link. It is successfully replacing
`CLAUDE.md` with a three-line pointer while code, tests, workflows, prompt templates, or
validation scanners still read that file as substantive policy. The visible documentation
looks migrated, but automation now consumes inert compatibility text.

The durable rule is therefore:

> A pointer conversion is an atomic semantic-and-consumer migration. It is docs-only only
> after a repository-wide inventory proves that no executable or authority-bearing consumer
> depends on the old document.

## When to Use

- Consolidating full `CLAUDE.md` and `AGENTS.md` documents into one authoritative contract.
- Replacing `CLAUDE.md` with an exact compatibility pointer while preserving compatibility
  for tools or humans that still look for the filename.
- Migrating a policy-bearing repository where validation code, scanners, templates,
  workflows, tests, runbooks, or README links cite the old authority.
- Reviewing a migration plan that must prove no directive or live consumer was omitted.
- Sweeping an organization where most repositories may already be migrated; probe default
  branches before allocating clones or agents.
- Handling the inverted-pointer state where `AGENTS.md` points back to `CLAUDE.md`.

Use `[[architecture-agents-md-contract-from-codebase]]` when authoring a new contract from
runtime behavior. Use this skill when consolidating or changing authority between existing
guidance documents.

## Verified Workflow

This limited workflow is `verified-local` from the 2026-07-19 ecosystem sweep. Use it only
after the repository-wide inventory proves that the change is genuinely docs-only. It does not
verify the comprehensive policy-consumer migration described in the next section.

### Quick Reference

```bash
# Probe the default branch before cloning.
gh api "repos/<owner>/<repo>/contents/CLAUDE.md" --jq '.size'
gh api "repos/<owner>/<repo>/contents/AGENTS.md" --jq '.size'

# Confirm the old file is already the exact pointer, or classify both substantive files.
gh api "repos/<owner>/<repo>/contents/CLAUDE.md" --jq '.content' | base64 -d

# Only after proving there are no functional consumers: merge the semantic union,
# install the exact pointer, and run the repository's Markdown gate.
npx --yes markdownlint-cli2 --config .markdownlint.yaml CLAUDE.md AGENTS.md
```

The verified lessons are to probe default branches before allocating work, read both files,
handle inverted pointers explicitly, produce one coherent union rather than stapled documents,
work in isolated clones/worktrees, and distinguish mergeable or auto-merge-armed from CI green.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until
> CI confirms it. The earlier lightweight migration evidence is recorded under Verified On.

### Quick Reference

```bash
# Capture every reference, including hidden workflows and templates.
rg -n --hidden --glob '!.git/**' --glob '!build/**' --glob '!.venv/**' \
  'CLAUDE\.md|AGENTS\.md' .

# Run the executable preservation/compatibility contract first.
uv run pytest tests/unit/docs/test_agent_contract.py -v

# Verify only exact compatibility/history references remain.
! rg -n --hidden --glob '!.git/**' --glob '!build/**' --glob '!.venv/**' \
  'CLAUDE\.md' . \
  | rg -v '^\./(CLAUDE\.md|\.github/CODEOWNERS|docs/adr/<history-file>|tests/unit/docs/test_agent_contract\.py):'

# Validate anchors, focused consumer tests, static quality, and the full suite.
uv run hephaestus-validate-anchors --repo-root . --target AGENTS.md --verbose
uv run ruff check hephaestus/ scripts/ tests/
uv run pytest tests/unit -v
```

### Canonical compatibility pointer

When the repository contract requires this exact pointer, compare bytes rather than merely
checking that a link exists:

```markdown
# Claude Code guidance

Follow [`AGENTS.md`](AGENTS.md). It is the sole authoritative agent contract for this repository.
```

### Detailed Steps

1. **Resolve the semantic source before editing.** Use the pre-consolidation parent commit,
   not the current pointer stub, as the inventory source. Record every source heading and
   distinctive high-risk directive: coverage thresholds, security rules, release/version
   authority, commit/PR policy, prohibited flags, temporary-file conventions, skill routing,
   and architecture boundaries.

2. **Classify the repository before choosing a gate.** A lightweight repository may truly
   need only a Markdown union and pointer. A policy-bearing repository has code, tests,
   workflows, scanners, or templates coupled to document names or prose. Only the first class
   is docs-only. For an ecosystem sweep, API-probe `CLAUDE.md` and `AGENTS.md` on default
   branches before cloning; an exact pointer means the visible file conversion is already done,
   although stale consumers may still warrant a separate audit.

3. **Create a source-to-destination map.** For each pre-change section, name the destination
   heading in `AGENTS.md` and at least one distinctive marker that must survive inside that
   section. Preserve ordering explicitly. Deduplicate overlap through same-file anchors rather
   than deleting one side without a traceable mapping.

4. **Inventory every consumer repository-wide.** Search hidden files and all source types.
   Classify each occurrence as:

   - authority-bearing documentation or policy prose;
   - functional consumer or scanner input;
   - prompt/template instruction;
   - workflow or error message;
   - test fixture or contract assertion;
   - deliberate filename/API compatibility;
   - annotated historical statement.

   Compatibility references must be exact and narrow. An old public parameter or function name
   can remain when changing it would break keyword callers, but user-facing documentation and
   internal calls should use the canonical name.

5. **Write regression tests before production edits.** The contract should assert:

   - `CLAUDE.md` equals the exact pointer string;
   - every mapped heading exists in `AGENTS.md` in the expected order;
   - every distinctive directive appears inside its intended section, not merely somewhere in
     the file;
   - only exact path-and-line compatibility/history references to `CLAUDE.md` remain;
   - scanners and validation helpers consume `AGENTS.md`;
   - any renamed public helper retains an explicitly tested delegating alias.

   A heading count is insufficient: it passes even when a directive silently moves to the wrong
   section or disappears during deduplication.

6. **Build one coherent canonical document.** Merge the union of substantive guidance into
   `AGENTS.md`, declare sole authority at the top, preserve the existing topology or specialist
   material under an explicit boundary, and replace cross-document references with same-file
   anchors. Do not staple two documents together or let the pointer become the source for the
   merge.

7. **Retarget all live consumers in the same change.** This includes README links, runbooks,
   ADR statements, workflow diagnostics, CODEOWNERS, validation modules, prompt templates,
   script docstrings, scanner globs, test fixtures, topology inputs, and metadata-safety scans.
   If a public helper is renamed to match the new authority, keep a narrow compatibility alias:

   ```python
   def check_agents_md_threshold(repo_root: Path, expected: int) -> list[str]:
       """Check that AGENTS.md documents the correct coverage threshold."""
       ...


   def check_claude_md_threshold(repo_root: Path, expected: int) -> list[str]:
       """Compatibility alias for :func:`check_agents_md_threshold`."""
       return check_agents_md_threshold(repo_root, expected)
   ```

8. **Replace the pointer only as part of the atomic patch.** The contract, canonical document,
   pointer, consumer retargets, compatibility aliases, and tests move together. Do not leave an
   intermediate or committed state where `CLAUDE.md` is a pointer while any guard still treats
   it as policy.

9. **Verify from narrow to broad.** Run the new contract and focused consumer tests, then the
   repository-wide hidden-file audit, anchor validator, formatter/linter/type checks required by
   the repository, and the complete test suite. CI is required before calling the comprehensive
   workflow verified.

10. **Rollback atomically.** If directive preservation, anchors, or live-consumer checks remain
    red, restore both documents and every retargeted consumer together. A partial rollback is the
    same split-authority failure in reverse.

### Starting-State Decision Table

| Starting state | Required treatment |
| -------------- | ------------------ |
| `AGENTS.md` points to substantive `CLAUDE.md` | Flip authority, merge the body, and rewrite all back-references. |
| Both files are full and cross-reference each other | Preserve the semantic union, deduplicate through anchors, and retarget consumers. |
| Both files are full and independent | Merge both; prove each source section survived. |
| `AGENTS.md` is absent | Seed it from substantive guidance, then audit consumers before stubbing `CLAUDE.md`. |
| `CLAUDE.md` is already the exact pointer | Do not assume completion; audit for code and tests that still consume the pointer. |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Treat every migration as docs-only | Merge Markdown, run markdownlint, and stop | Policy-bearing repositories may have validation code, scanner globs, templates, and tests that read or cite the old authority | Inventory all consumers first; docs-only is a conclusion, not an assumption |
| Stub `CLAUDE.md` before retargeting guards | Make the visible authority change first | Functional consumers now scan three lines of compatibility text and silently lose thresholds, command tables, or topology | Move pointer, consumers, aliases, and contract tests atomically |
| Preserve headings without section-scoped markers | Check only heading presence or count | Distinctive directives can disappear or land in the wrong section while the test stays green | Map source sections to destination headings and assert markers inside each section |
| Search only obvious docs paths | Run scoped `rg` over README and docs | Hidden workflows, templates, Python docstrings, scanner globs, and test fixtures are missed | Use repository-wide `rg --hidden` and exclude only generated environments |
| Allow broad historical exceptions | Ignore an entire ADR or test directory | New stale references can accumulate unnoticed inside the allowlisted area | Allow exact path-and-line text, not directories or free-form occurrences |
| Rename old public APIs outright | Replace a filename-specific helper or parameter everywhere | Keyword callers and external imports can break even though internal tests use the new name | Add the canonical API and retain a tested delegating compatibility alias |
| Use the post-change pointer as the semantic source | Inventory only the current default branch after migration | The original directives are already gone from that file | Read the pre-consolidation parent commit and record a source-to-destination map |
| Fan out across every ecosystem repository | Clone or delegate before checking current main | Most repositories may already have the pointer | Probe default branches through the GitHub API before allocating work |
| Claim completion when a PR is merely mergeable | Treat local tests or armed auto-merge as CI success | Queued checks are not green and auto-merge is not merge | Report the observed verification level honestly |

## Results & Parameters

### Minimum executable contract

The preservation test should encode semantic placement, not just global substring presence:

```python
EXPECTED_POINTER = (
    "# Claude Code guidance\n\n"
    "Follow [`AGENTS.md`](AGENTS.md). It is the sole authoritative "
    "agent contract for this repository.\n"
)


def section(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


def test_directives_are_preserved() -> None:
    text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    positions: list[int] = []
    for heading, markers in REQUIRED_SECTIONS.items():
        positions.append(text.index(heading))
        for marker in markers:
            assert marker in section(text, heading)
    assert positions == sorted(positions)
```

The stale-reference contract should walk the repository, skip generated/cache directories,
and compare each remaining `CLAUDE.md` line against an exact path-specific allowlist. Exclude
the contract test itself so its fixtures do not self-match.

### Consumer categories that must be checked

| Category | Typical migration |
| -------- | ----------------- |
| Policy prose | README, runbook, ADR, workflow error, or script docstring cites `AGENTS.md` |
| Functional scanner | Input glob changes from `CLAUDE.md` to `AGENTS.md` |
| Validation helper | Canonical helper reads `AGENTS.md`; old helper delegates |
| Prompt/template | Agent instruction names the canonical contract |
| Test fixture | Uses `AGENTS.md` unless explicitly testing pointer compatibility |
| Historical record | Keeps one annotated statement naming both old and new authority |
| Ownership | CODEOWNERS may retain both canonical file and compatibility pointer |

### Prior evidence and current parameters

- A 2026-07-19 ecosystem sweep found 12 of 16 non-fork repositories already had the
  pointer; only four required visible document conversion. That validates API probing and the
  lightweight union/pointer mechanics locally, but not the v2.0.0 exhaustive consumer workflow.
- The Hephaestus plan that motivated v2.0.0 identified stale consumers after an earlier pointer
  PR: validation messages, tier mapping docs, prompt templates, security/version scripts,
  scanner globs, discovery fixtures, topology inputs, and metadata-safety tests.
- Verification target for the comprehensive workflow: exact-pointer contract, section-scoped
  directive preservation, focused consumer tests, repository-wide hidden-file audit, anchor
  validation, static quality checks, full unit suite, and CI.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| HomericIntelligence ecosystem | 2026-07-19 lightweight conversion sweep | verified-local — API probing and four document conversions were completed; CI was queued at capture. |
| Hephaestus | #2338 consolidation/consumer-retargeting implementation plan | unverified — reviewed plan only; no implementation, local suite, or CI result was supplied. |
