---
name: stale-documentation-audit-and-broken-reference-repair
description: >-
  Audit and repair stale documentation using live authoritative sources. Use for counts,
  versions, directory trees, phantom paths, links/anchors, command tables, placeholders,
  file-line citations, and recursive living-document policies where drift must stay blocked.
category: documentation
date: 2026-07-20
version: "2.0.0"
user-invocable: false
verification: verified-ci
license: BSD-3-Clause
history: stale-documentation-audit-and-broken-reference-repair.history
tags: [doc-drift, broken-references, phantom-path, anchor-validation, count-disambiguation, source-of-truth, living-documentation, markdownlint]
---

# Stale Documentation Audit and Broken Reference Repair

**Supporting cases:** [notes](./stale-documentation-audit-and-broken-reference-repair.notes.md)

**Superseded content:** [history](./stale-documentation-audit-and-broken-reference-repair.history)

## Overview

Documentation repairs begin by rediscovering the current truth, not by copying an issue's count,
line number, command, or version. Determine what set a number describes, choose the authoritative
source for each claim, locate references by content, and repair every in-scope duplicate without
blind replacement. Add a drift guard only when a stable semantic contract exists.

The canonical repair workflow is `verified-ci`. The recursive living-documentation policy is
proposed/unverified and remains labeled that way in the notes/history.

## When to Use

- Counts, metrics, versions, role descriptions, or future-work claims disagree across docs/code.
- A directory, recipe, command, link, heading anchor, or `file:line` reference no longer resolves.
- A getting-started page contains placeholders, invented APIs, or commands that do not run in the
  repository's declared environment.
- A curated tree/table/list has a caption count that may describe the enumeration rather than the
  entire filesystem.
- A version claim should follow a manifest, package metadata, or git tag.
- Markdown lint appears skipped because the changed path is outside the hook's file pattern.
- Nested normative docs need owners, semantic sources, freshness triggers, and deterministic checks.

## Verified Workflow

1. **Bind the tree and re-read the issue.** Record the commit, then search for the described
   content rather than trusting cited line numbers.
2. **Identify the claim and authority.** Examples: manifest membership, `pyproject.toml` version,
   latest reachable tag, `git ls-files`, `just --list`, package directories containing
   `__init__.py`, or an existing executable guard.
3. **Disambiguate the counted set.** Compare the prose number to the adjacent curated enumeration
   and to the live population. If a caption describes the list, either complete the list or clarify
   “documented”; do not replace it with an unrelated filesystem total.
4. **Find every in-scope copy semantically.** Search a phrase or surrounding label, not the bare
   number. Classify matches so unrelated metrics are not changed.
5. **Choose remove, redirect, or rewrite.** Remove a phantom reference if no supported replacement
   exists; redirect only to a real equivalent; rewrite a stub from repository-owned commands and
   source headers. Preserve accepted historical records unless policy says otherwise.
6. **Run replacement commands.** A feature name is not necessarily an environment name. In a
   Pixi-only repository, invoke environment tools through `pixi run` and prove the exact command.
7. **Repair links by content.** Prefer a stable symbol/section/path reference over another volatile
   line number. Compute relative links from the containing document, including nested docs.
8. **Add the smallest durable guard.** Reuse an existing semantic test when the claim has a stable
   source. Avoid wording/line-count tests and skip a new guard if the invariant is already enforced.
9. **Validate the changed surface.** Run link/anchor checks, the exact repository docs gate,
   Markdown lint on every changed Markdown path, and a negative grep proving stale variants are gone.
   Confirm the hook actually processed the file rather than printing `Skipped`.
10. **Report provenance.** State the source, old/new values, commands run, scope exclusions, and
    any unverifiable or proposed claim.

### Audit commands

```bash
git rev-parse HEAD
git ls-files -- '*.md'
rg -n '<claim phrase|heading|path|recipe>' README.md CONTRIBUTING.md docs tests
just --list
find <package> -mindepth 1 -maxdepth 1 -type d -exec test -f '{}/__init__.py' ';' -print
npx markdownlint-cli2 '<changed-path>.md'
```

Use repository-specific equivalents. Quote globs so the linter, not the shell, expands them.
When a pre-commit hook says Markdown lint was skipped, lint the file directly or fix the hook scope;
do not treat skip as a pass.

### Count and inventory rules

- Count the enforced artifact, not either side of conflicting prose.
- A curated list's number normally annotates that list. Reconcile number-to-list first.
- Count Python subpackages by tracked/package markers such as `__init__.py`, not raw directories
  that include caches and dotfiles.
- For a tracked-file catalog, use `git ls-files`; filesystem globs include scratch files.
- After deriving a value, search with the surrounding phrase and review each hit manually.
- Avoid global replacement of bare digits or version fragments.

### Placeholder and command repair

Classify a stub before editing: delete if it has no consumer, keep a clearly marked deferred
placeholder if policy requires it, or rewrite from current code/recipes. Do not invent behavior.
Cross-check every documented recipe against the task file because mixed verb-first/prefix-first
naming can hide additional phantom entries. Verify environment selection from the manifest and
run the exact command on a clean-equivalent path.

### Recursive living-document policy (proposed)

For normative Markdown, define recursive inclusion and narrow exclusions for fixtures, generated
or scratch content, accepted ADR bodies, and point-in-time release notes. For each volatile claim,
record an owner, authoritative source, review trigger, and semantic check. Ignore fenced examples
when scanning prose claims, resolve links relative to their containing document, inject dates into
roadmap checks for deterministic testing, and wire hooks only after the existing corpus is clean.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Trust the issue's count or line number | Trust the issue's count or line number | Both drift as files evolve | Re-derive from the live authority and search by content |
| Replace every matching number | Replace every matching number | Unrelated metrics share digits | Search with the claim phrase and classify hits |
| Count raw directories | Count raw directories | Caches, dot-directories, and nonpackages inflate totals | Count tracked/package-marked members |
| Redirect a phantom path to a guessed sibling | Redirect a phantom path to a guessed sibling | The replacement may not provide the same workflow | Verify equivalence or remove the reference |
| Ship an unrun replacement command | Ship an unrun replacement command | Feature/environment names and PATH differ | Resolve the environment and execute it |
| Use bare `pytest`, `ruff`, or `pre-commit` in a Pixi-only repo | Use bare `pytest`, `ruff`, or `pre-commit` in a Pixi-only repo | Clean machines may not expose the tool | Use the repository's `pixi run` contract |
| Add a fresh `file:line` citation | Add a fresh `file:line` citation | It immediately starts rotting again | Cite stable content, symbol, or section |
| Treat a skipped lint hook as green | Treat a skipped lint hook as green | The changed file was never checked | Run lint directly or repair hook scope |
| Add wording tests for prose | Add wording tests for prose | They pin presentation rather than semantics | Guard a stable source-to-doc invariant only |

## Results & Parameters

| Parameter | Rule |
| --- | --- |
| Evidence base | Current immutable commit |
| Claim location | Content/heading search, not cited coordinates |
| Count authority | Adjacent enumeration or enforced live artifact, explicitly named |
| Replacement | Verified existing path/command; no invention |
| Search scope | Phrase-scoped and manually classified |
| Links | Resolved relative to the containing document |
| Drift guard | Semantic, deterministic, and sourced from one authority |
| Markdown lint | Direct evidence that each changed file was processed |
| Historical docs | Preserve unless their policy permits supersession/removal |
| Verification label | Keep proposed work distinct from executed local/CI evidence |

The result is a coherent documentation surface whose claims cite current sources, whose commands
run in the declared environment, and whose durable invariants have appropriately scoped guards.
Project-specific repairs, PRs, and validation outcomes are indexed in the notes.
