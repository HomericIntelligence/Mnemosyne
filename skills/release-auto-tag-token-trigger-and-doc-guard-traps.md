---
name: release-auto-tag-token-trigger-and-doc-guard-traps
description: "Three traps in tag-driven release preparation: GITHUB_TOKEN tag pushes do not trigger push workflows, immutable tags strand stale documentation guards, and pre-tag documentation must name the pending version without falsely claiming it is released while keeping regex-owned phrases physically contiguous. Use when: (1) a tag-triggered release workflow never fires, (2) a release test fails a doc-version drift guard, (3) preparing release-status prose before a signed tag exists, (4) Markdown blockquote wrapping breaks a release-gate regex, (5) recovering a stranded release tag."
category: ci-cd
date: 2026-08-07
version: "1.1.0"
user-invocable: false
verification: verified-local
history: release-auto-tag-token-trigger-and-doc-guard-traps.history
tags:
  - release
  - auto-tag
  - github-actions
  - github-token
  - workflow-trigger-suppression
  - tag-triggered-release
  - version-drift
  - drift-guard
  - immutable-tag
  - stranded-tag
  - migration-md
  - hatch-vcs
  - workflow-dispatch
  - pypi-publish
  - pending-release
  - release-status
  - markdown-blockquote
  - regex-owned-prose
---

# Release Pipeline and Pre-Tag Documentation Guard Traps

**History:** [changelog](./release-auto-tag-token-trigger-and-doc-guard-traps.history)

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-07 |
| **Objective** | Preserve the original v0.9.8 release-pipeline diagnoses and add a chronology-safe way to prepare release-status documentation before the next signed tag exists. |
| **Outcome** | Three related traps are now covered. Trap 1: `GITHUB_TOKEN` tag pushes do not trigger the release workflow. Trap 2: a stale doc guard in an immutable tag permanently strands that tag. Trap 3: pre-tag prose must declare the version pending, preserve the current-main chronology, and keep the parser-owned `latest released version is **X.Y.Z**` phrase on one physical line. |
| **Verification** | verified-local — the original trigger and immutable-tag diagnoses were verified live. The pending-release pattern was tested in a disposable ProjectHephaestus clone: the blockquote-aware content assertion, focused release-gate test, chronology assertion, and Markdown lint passed. CI and final publication remain pending. |

Related skill: `release-tag-drift-recut-on-fixed-commit` covers the same doc drift guard from a different surface (tag exists, PyPI empty, decide whether to re-cut). This skill is the "cutting a Hephaestus release failed" surface and adds the GITHUB_TOKEN trigger-suppression trap, which that skill does not cover. Recovery also differs: here the stranded tag was left as a ghost and superseded by the next patch version — do NOT delete or re-point a pushed tag without explicit owner approval.

Related skill: `testing-doc-guard-markdown-linewrap-substring` is the canonical source for
ordinary whitespace normalization and focused `pytest --no-cov` iteration. This release
skill adds the narrower blockquote case: collapsing whitespace alone is insufficient when
each continuation line contributes a literal `>` marker.

## When to Use

- You ran an auto-tag workflow (or any Actions job that does `git push origin "${TAG}"` with `token: secrets.GITHUB_TOKEN`) and the tag exists on the remote, but the tag-triggered Release workflow never started — `gh run list --branch vX.Y.Z` is empty 30+ minutes later, with no error anywhere.
- Prior releases "just worked" and this one didn't: check WHO pushed each tag. Human-pushed tags fire `on: push` triggers; `github-actions[bot]`-pushed tags do not.
- The Release workflow's test job fails a doc version-currency guard (e.g. `tests/unit/docs/test_version_currency.py::test_migration_md_version_does_not_trail_latest_git_tag`) when run against a `vX.Y.Z` tag checkout, and bumping the doc on main does not help — the tag's tree is immutable.
- You are authoring or reviewing an auto-tag → release pipeline and need to pick a tag-push credential (GITHUB_TOKEN vs PAT/App token) or wire an explicit dispatch.
- You must decide what to do with a stranded release tag: supersede with the next version, never mutate the pushed tag.
- You must update a migration or release guide before the signed tag exists, but an unconditional “latest released version” claim would be temporally false.
- A regex-backed documentation guard cannot find a phrase that looks continuous when rendered because a Markdown blockquote marker splits it across physical lines.

## Verified Workflow

### Trap 1 — GITHUB_TOKEN tag push cannot trigger release.yml

`auto-tag.yml` checks out with `token: secrets.GITHUB_TOKEN` and runs `git push origin "${TAG}"`. GitHub **deliberately suppresses** `on: push` (and other) workflow triggers for events created with `GITHUB_TOKEN` (anti-recursion protection). The tag lands on the remote, but the tag-triggered Release workflow NEVER fires — no failure, no log, it just silently doesn't run.

Why prior releases looked automatic: their tags were pushed by a human.

```text
v0.9.7 taggeremail = 4211002+mvillmow@users.noreply.github.com        → push event fires
v0.9.8 taggeremail = github-actions[bot]@users.noreply.github.com     → nothing fires
```

Remediation used (verified live): the release workflow's documented escape hatch —

```bash
gh workflow run release.yml -f tag=vX.Y.Z
```

Durable fix (filed as ProjectHephaestus issue #1801): have `auto-tag.yml` dispatch `release.yml` explicitly at the end of its run — `workflow_dispatch` via `GITHUB_TOKEN` IS allowed when the job has `actions: write` permission — or push the tag with a PAT/App token so the push event fires natively.

### Trap 2 — doc version guard strands immutable tags

The Release workflow's test job runs `test_migration_md_version_does_not_trail_latest_git_tag`, which requires `docs/MIGRATION.md`'s "latest released version is **X.Y.Z**" line to be `>=` the latest git tag — **evaluated against the TAG's checked-out tree**. If you tag before bumping the doc, that tag's tree is immutable, so that version can NEVER be released. Bumping main does not help. v0.9.8 was stranded exactly this way (its tree documents 0.9.7); the same trap broke the first v0.9.7 release attempt (fixed then by doc-bump PR #1542). RELEASING.md even claimed "The version itself does not need to be edited in any file" — wrong for MIGRATION.md.

Recovery (verified): the guard is `documented >= tag`, so the doc may LEAD the tag. Declare the NEXT version pending in `docs/MIGRATION.md` and merge via the normal PR gate before tagging. After the signed tag exists, the same sentence truthfully describes it as the latest release. Then auto-tag the next patch and dispatch release for it. The stranded tag stays as a ghost — unpublished and harmless. Do NOT delete or re-point a pushed tag without explicit owner approval.

### Trap 3 — pre-tag prose must separate pending from released state

A release guide can satisfy a future-version parser without claiming that an unpublished
version already exists. State that `X.Y.Z` is the pending release and is not released until
the signed `vX.Y.Z` tag is published. Put the parser-owned phrase
`latest released version is **X.Y.Z**` in the post-tag clause.

Keep that exact phrase on one physical Markdown line. In a blockquote, this visual wrapping
does **not** match a regex that expects a plain space:

```markdown
> the latest
> released version is **X.Y.Z**
```

The file contains `latest\n> released`, not `latest released`. Wrap before `latest` so
the complete parser-owned phrase stays contiguous:

```markdown
> After that tag is published, the
> latest released version is **X.Y.Z** (tag-driven via hatch-vcs).
```

Do not advance a `Current main (unreleased; post-vOLD)` heading to `post-vNEW` until the
new signed tag exists. Historical behavior attributed to `vOLD` also remains historical
fact; do not rewrite it merely because `vNEW` is being prepared. Hatch-vcs still derives
the package version from the tag, so this documentation edit does not justify a package
version field.

### Quick Reference

```bash
# Correct Hephaestus release order (hatch-vcs, tag-driven):

# 1. Before tagging, declare vX.Y.Z pending and explicitly not released until
#    its signed tag is published. Keep the future-facing parser phrase
#    "latest released version is **X.Y.Z**" contiguous on one physical line.
#    Preserve current-main as post-vOLD until the tag exists. Merge this first.

# 2. Cut the tag from the merged main:
gh workflow run auto-tag.yml -f bump_kind=patch

# 3. Confirm the new tag exists:
git fetch --tags && git tag --sort=-v:refname | head -3

# 4. Dispatch the release EXPLICITLY — do NOT wait for the tag-push trigger,
#    it will never fire for a GITHUB_TOKEN-pushed tag:
gh workflow run release.yml -f tag=vX.Y.Z

# 5. Watch and verify:
gh run watch <run-id> --exit-status
gh release view vX.Y.Z
# ...and confirm the new version is live on PyPI.
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Waited 30 minutes for release.yml to fire from the auto-tag-pushed tag | GitHub suppresses `on: push` workflow triggers for events created with `GITHUB_TOKEN` (anti-recursion) — the bot-pushed tag can never trigger release.yml, and there is no error or log anywhere indicating this | Always dispatch the release workflow explicitly (`gh workflow run release.yml -f tag=vX.Y.Z`) after an Actions-pushed tag, or fix the pipeline to push with a PAT/App token / self-dispatch with `actions: write` |
| 2 | Tagged v0.9.8 before bumping docs/MIGRATION.md's latest-version line | The version-currency guard runs against the TAG's checked-out tree, which is immutable — v0.9.8's tree documents 0.9.7, so the guard fails forever; bumping main cannot repair it | Bump the doc BEFORE tagging (doc may lead the tag since the guard is `documented >= tag`); a stranded tag cannot be fixed, only superseded by the next version — never delete/re-point a pushed tag without owner approval |
| 3 | Claimed “the latest released version is X.Y.Z” before the signed tag existed | The release guide became factually false during the preparation window | Declare X.Y.Z pending and explicitly unreleased until its signed tag is published; place the parser phrase in a conditional post-tag clause |
| 4 | Wrapped `the latest released version is **X.Y.Z**` as `the latest\n> released version` inside a blockquote | The literal `>` continuation marker interrupts the regex-owned phrase even though rendered prose looks continuous | Keep the complete parser-owned phrase on one physical line; wrap before it |
| 5 | Normalized the whole blockquote with `' '.join(text.split())` for an exact-content assertion | Whitespace normalization retains `>` markers, so expected prose without markers still does not match | Normalize line-by-line with `line.removeprefix('> ')` before joining |
| 6 | Ran one focused pytest file under a repository-wide `fail_under` coverage policy | The assertion can pass while pytest still exits nonzero because a single test cannot meet global coverage | Use `pytest --no-cov <focused-test>` for local assertion diagnosis; retain the exact full-suite/CI coverage gate for release evidence |

## Results & Parameters

### Diagnosis signatures

**Trap 1 — release never fired.** No runs exist for the tag ref well after the tag was pushed:

```bash
gh run list --branch vX.Y.Z
# → empty 30+ minutes after the tag landed = trigger suppression, not slowness
```

Confirm the tagger identity — bot-tagged means suppressed:

```bash
git for-each-ref refs/tags/vX.Y.Z --format='%(taggeremail)'
# github-actions[bot]@users.noreply.github.com  → on:push will NEVER fire
# <human>@users.noreply.github.com              → on:push fires normally
```

**Trap 2 — stranded tag.** The Release run's test job fails `test_migration_md_version_does_not_trail_latest_git_tag`, and the tag's own tree contains the stale doc line:

```bash
git show vX.Y.Z:docs/MIGRATION.md | grep -i "latest released version"
# documents an older version than the tag → this tag is permanently stranded
```

### Escape hatch / recovery commands

```bash
# Manually dispatch the release for a tag whose push event never fired:
gh workflow run release.yml -f tag=vX.Y.Z

# Recovery for a stranded tag: doc-bump PR on main (doc may LEAD the tag),
# then supersede with the next patch version:
gh workflow run auto-tag.yml -f bump_kind=patch
gh workflow run release.yml -f tag=vX.Y.(Z+1)
```

### Chronology-safe pre-tag declaration

```markdown
> **Release status:** **X.Y.Z is the pending release; it is not released until
> the signed `vX.Y.Z` tag is published.** After that tag is published, the
> latest released version is **X.Y.Z** (tag-driven via hatch-vcs).
> **1.0 has not been released yet** — forthcoming guidance remains unreleased.
```

The exact nouns vary by repository, but the state model does not:

1. Before the signed tag: `X.Y.Z` is pending, and current main is post-`vOLD`.
2. After the signed tag: the conditional clause makes `X.Y.Z` the latest release.
3. Package metadata remains tag-derived; no static version field is added.

### Focused local verification

```bash
# Blockquote-aware exact-content check.
python -c "from pathlib import Path; raw = Path('docs/MIGRATION.md').read_text(); \
text = ' '.join(line.removeprefix('> ').strip() for line in raw.splitlines()); \
expected = '**X.Y.Z is the pending release; it is not released until the signed \`vX.Y.Z\` tag is published.** After that tag is published, the latest released version is **X.Y.Z**'; \
assert expected in text"

# Preserve pre-tag chronology.
python -c "from pathlib import Path; text = Path('docs/MIGRATION.md').read_text(); \
assert 'Current main (unreleased; post-vOLD)' in text; \
assert 'Current main (unreleased; post-vX.Y.Z)' not in text"

# Diagnose the focused parser without a repository-wide coverage threshold.
pytest --no-cov tests/unit/docs/test_version_currency.py

# Use the repository's real Markdown hook.
pre-commit run markdownlint-cli2 --files docs/MIGRATION.md
```

### Key references

- ProjectHephaestus issue #1801 — durable fix for Trap 1 (auto-tag self-dispatches release.yml, or PAT tag push).
- ProjectHephaestus PR #1803 / issue #1802 — MIGRATION.md bump + RELEASING.md checklist step (Trap 2 recovery + prevention).
- ProjectHephaestus PR #1542 — the first v0.9.7 release attempt broken by the same doc guard.
- Pre-v0.10.3 disposable-clone validation — confirmed the chronology-safe declaration only passes the existing regex gate when `latest released version is **0.10.3**` stays on one physical line.
- Verification level is `verified-local`: the diagnoses, dispatch escape hatch, corrected parser layout, focused gate, chronology assertion, and Markdown lint were verified locally; CI and final publication were not.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | v0.9.8/v0.9.9 release recovery | Live trigger and immutable-tag diagnoses |
| ProjectHephaestus | Pre-v0.10.3 release preparation | Disposable-clone exact-content, parser, chronology, and Markdown validation |
