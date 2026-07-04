---
name: release-auto-tag-token-trigger-and-doc-guard-traps
description: "Two traps in a GitHub Actions auto-tag → tag-triggered release pipeline (hatch-vcs, tag-driven versioning, ProjectHephaestus auto-tag.yml → release.yml): (1) a tag pushed by an Actions job using GITHUB_TOKEN NEVER triggers the on:push release workflow — GitHub suppresses workflow triggers for GITHUB_TOKEN-created events (anti-recursion), so the release silently does not run with no error anywhere; (2) a doc version-currency guard evaluated against the TAG's checked-out tree permanently strands any tag cut before the doc bump — the tag tree is immutable, so bumping main cannot fix it, only superseding with the next version can. Use when: (1) a tag-triggered release workflow never fires after an Actions-pushed tag, (2) a release test job fails a doc-version drift guard against an immutable tag, (3) authoring an auto-tag→release pipeline, (4) deciding recovery for a stranded release tag."
category: ci-cd
date: 2026-07-03
version: "1.0.0"
user-invocable: false
verification: verified-local
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
---

# Release Pipeline Traps: GITHUB_TOKEN Tag Push Cannot Trigger release.yml; Doc Guard Strands Immutable Tags

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-03 |
| **Objective** | Cut v0.9.8 of HomericIntelligence/ProjectHephaestus via the documented "One-Click Release" path (`auto-tag.yml` → tag push → `release.yml`), diagnose why nothing published, and establish a release order that cannot re-strand a tag. |
| **Outcome** | Two independent traps found and root-caused live. Trap 1: `auto-tag.yml` pushes the tag with `GITHUB_TOKEN`, and GitHub deliberately suppresses `on: push` workflow triggers for GITHUB_TOKEN-created events — release.yml never fired, silently. Trap 2: the release test job's doc version guard evaluates against the TAG's immutable tree; v0.9.8 was tagged before the `docs/MIGRATION.md` bump, so v0.9.8 can never pass and is permanently stranded. Recovery: bump the doc to the NEXT version on main (Hephaestus PR #1803 / issue #1802), auto-tag v0.9.9, and dispatch release.yml explicitly. Durable fix for Trap 1 filed as Hephaestus issue #1801. |
| **Verification** | verified-local — both root causes were verified live (taggeremail comparison, absent runs on the tag ref, guard test semantics read from source), and the manual `gh workflow run release.yml` escape hatch was confirmed to start the workflow. The final v0.9.9 release run outcome was still in flight at capture time, so end-to-end publish is not yet confirmed-CI. |

Related skill: `release-tag-drift-recut-on-fixed-commit` covers the same doc drift guard from a different surface (tag exists, PyPI empty, decide whether to re-cut). This skill is the "cutting a Hephaestus release failed" surface and adds the GITHUB_TOKEN trigger-suppression trap, which that skill does not cover. Recovery also differs: here the stranded tag was left as a ghost and superseded by the next patch version — do NOT delete or re-point a pushed tag without explicit owner approval.

## When to Use

- You ran an auto-tag workflow (or any Actions job that does `git push origin "${TAG}"` with `token: secrets.GITHUB_TOKEN`) and the tag exists on the remote, but the tag-triggered Release workflow never started — `gh run list --branch vX.Y.Z` is empty 30+ minutes later, with no error anywhere.
- Prior releases "just worked" and this one didn't: check WHO pushed each tag. Human-pushed tags fire `on: push` triggers; `github-actions[bot]`-pushed tags do not.
- The Release workflow's test job fails a doc version-currency guard (e.g. `tests/unit/docs/test_version_currency.py::test_migration_md_version_does_not_trail_latest_git_tag`) when run against a `vX.Y.Z` tag checkout, and bumping the doc on main does not help — the tag's tree is immutable.
- You are authoring or reviewing an auto-tag → release pipeline and need to pick a tag-push credential (GITHUB_TOKEN vs PAT/App token) or wire an explicit dispatch.
- You must decide what to do with a stranded release tag: supersede with the next version, never mutate the pushed tag.

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

Recovery (verified): the guard is `documented >= tag`, so the doc may LEAD the tag. Bump `docs/MIGRATION.md` to the NEXT version and merge via the normal PR gate (ProjectHephaestus PR #1803 / issue #1802, which also added this step to RELEASING.md's checklist), then auto-tag the next patch (v0.9.9) and dispatch release for it. The stranded tag stays as a ghost — unpublished and harmless. Do NOT delete or re-point a pushed tag without explicit owner approval.

### Quick Reference

```bash
# Correct Hephaestus release order (hatch-vcs, tag-driven):

# 1. Bump docs/MIGRATION.md "latest released version" line to the version about
#    to be tagged (or the next version — guard is documented >= tag), merge via
#    the normal PR gate FIRST.

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

### Key references

- ProjectHephaestus issue #1801 — durable fix for Trap 1 (auto-tag self-dispatches release.yml, or PAT tag push).
- ProjectHephaestus PR #1803 / issue #1802 — MIGRATION.md bump + RELEASING.md checklist step (Trap 2 recovery + prevention).
- ProjectHephaestus PR #1542 — the first v0.9.7 release attempt broken by the same doc guard.
- Verification level is `verified-local` because the v0.9.9 release run outcome was still in flight when this skill was captured; the diagnoses and the dispatch escape hatch were verified live.
