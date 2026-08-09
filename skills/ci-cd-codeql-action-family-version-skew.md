---
name: ci-cd-codeql-action-family-version-skew
description: "The github/codeql-action family (init / analyze / upload-sarif) enforces internal version consistency — mixing sub-action versions in one workflow hard-fails the CodeQL job with a configuration error. Dependabot files SEPARATE PRs per sub-action, so merging any one alone breaks scanning; the CodeQL check is often non-required, so branch protection lets the broken merge through and scanning silently stops. Use when: (1) a dependabot PR bumps any github/codeql-action sub-action (init, analyze, upload-sarif), (2) a CodeQL job fails with 'Loaded a configuration file for version X, but running version Y' or 'CodeQL job status was configuration error', (3) you see multiple sibling dependabot PRs each bumping one codeql-action sub-action, (4) you need to verify a codeql-action SHA pin matches its release tag (annotated-tag double-deref)."
category: ci-cd
date: 2026-07-16
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - codeql
  - codeql-action
  - dependabot
  - version-skew
  - action-pinning
  - sha-pin
  - annotated-tag
  - upload-sarif
  - github-actions
  - non-required-check
  - family-alignment
---

# CI/CD: Align the github/codeql-action Family in One PR (Version Skew Breaks Scanning)

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-16 |
| **Objective** | Merge dependabot bumps of `github/codeql-action` sub-actions (init / analyze / upload-sarif) without breaking CodeQL scanning |
| **Outcome** | Verified: bumping analyze to v4.36.3 while init stayed v4.36.2 hard-failed the CodeQL job (`Loaded a configuration file for version '4.36.2', but running version '4.36.3'` → `CodeQL job status was configuration error`). Fix: align ALL family pins to one SHA in one PR; the sibling dependabot PR collapses to an empty diff. Observed across HomericIntelligence Charybdis #269/#270 and Proteus #204/#200 |
| **Verification** | verified-local — config-error failure and green aligned run observed on live PR CI in the source repos; this skill file validated locally |
| **Related skill** | [ci-cd-codeql-default-to-advanced-canonical-names](./ci-cd-codeql-default-to-advanced-canonical-names.md) — different topic (default-setup → advanced migration + canonical check names), but shares the codeql-action SHA-pinning gotchas |

## When to Use

- A dependabot PR bumps **any** `github/codeql-action` sub-action (`init`, `analyze`, or `upload-sarif`) — never merge it in isolation without checking the rest of the family
- A CodeQL job fails with `Loaded a configuration file for version 'X', but running version 'Y'` or the run summary says `CodeQL job status was configuration error`
- Multiple sibling dependabot PRs are open, each bumping ONE codeql-action sub-action to the same new version
- The CodeQL check is not in the branch's required status checks, so a broken bump could merge silently and stop C++/JS scanning without anyone noticing
- You need to verify that a codeql-action commit-SHA pin actually corresponds to the release tag (annotated tags need a double dereference)

## Verified Workflow

### Quick Reference

```bash
# 1. When any codeql-action bump PR appears, locate ALL family pins across workflows:
grep -rn "github/codeql-action" .github/workflows/
# Expect init / analyze / upload-sarif — they must ALL move to the same SHA.

# 2. Verify the target SHA == the release tag (annotated-tag DOUBLE deref):
gh api repos/github/codeql-action/git/ref/tags/v4.36.3 --jq '{type: .object.type, sha: .object.sha}'
# If type == "tag" (annotated), dereference the tag object to get the COMMIT sha:
gh api repos/github/codeql-action/git/tags/<tag-object-sha> --jq '.object.sha'
# Pin uses: <commit-sha>  # v4.36.3   (never the tag-object sha)

# 3. Push a family-alignment commit to the CHOSEN dependabot PR branch:
#    edit every init/analyze/upload-sarif pin to the one verified commit SHA, then:
git commit -S -s -m "ci: align codeql-action family (init/analyze/upload-sarif) to v4.36.3

The codeql-action sub-actions enforce internal version consistency; a partial
bump fails the CodeQL job with a configuration error. Aligning all pins to
<commit-sha> (v4.36.3) in one PR."

# 4. PROOF before merge: the CodeQL job must run GREEN on the aligned head.
gh pr checks <PR> --repo <owner>/<repo>   # name the CodeQL check run explicitly

# 5. Sibling dependabot PR now has an identical/empty diff — first merge wins;
#    the other auto-closes on rebase-push, or close it manually with a
#    supersession comment to avoid a race.
```

### Detailed Steps

1. **Treat any codeql-action bump as a family event.** The `github/codeql-action` sub-actions (`init`, `analyze`, `upload-sarif`) enforce internal version consistency: `analyze` reads the configuration file written by `init` and hard-fails if the versions differ (`Loaded a configuration file for version '4.36.2', but running version '4.36.3'`). Grep **all** workflow files for `github/codeql-action` — pins can live in more than one workflow.
2. **Understand why dependabot makes this worse.** Dependabot files a SEPARATE PR per sub-action. Merging any one of them alone introduces skew. Worse, the CodeQL check is often **not** in the required status checks, so branch protection will happily merge the broken bump and scanning silently stops for every language (C++/JS in the observed case).
3. **Pick one dependabot PR as the carrier** and push a family-alignment commit to its branch that moves every family pin to ONE commit SHA.
4. **Verify the SHA against the release tag with a double deref.** `gh api repos/github/codeql-action/git/ref/tags/vX.Y.Z` returns an object; if `object.type == "tag"` it is an **annotated tag object**, not the commit — dereference again via `gh api repos/github/codeql-action/git/tags/<sha> --jq '.object.sha'` to get the commit SHA that belongs in `uses:`. (Alternative: the `/tags` list endpoint's `.commit.sha`.)
5. **Require proof before merge:** the CodeQL job must run **green on the aligned head**, and you must be able to name the specific check run. Do not rely on the overall PR state — the CodeQL check may be non-required and easy to overlook.
6. **Resolve the sibling PR deterministically.** After alignment, the other dependabot PR's diff is identical/empty. First merge wins; the sibling auto-closes when dependabot rebase-pushes it, or close it manually with a supersession comment referencing the merged PR to avoid a race.
7. **Do not rely on partial-bump tolerance.** `upload-sarif` tolerated being newer than `init` in at least one observed combination (a lone upload-sarif bump passed) — but this is undocumented behavior; always move the family together.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Merging the analyze-only dependabot bump (v4.36.3) while init stayed at v4.36.2 | Its own PR CI proved the failure: `Loaded a configuration file for version '4.36.2', but running version '4.36.3'` → `CodeQL job status was configuration error` (NO-GO caught pre-merge) | The family enforces internal version consistency; a partial bump is a guaranteed CodeQL failure, not a risk |
| 2 | Relying on branch protection to catch the broken bump | The CodeQL check was not in the required status contexts, so the red check would not have blocked the merge — scanning would have silently stopped post-merge | Non-required checks provide zero merge protection; verify the CodeQL run yourself and name the check run before merging any family bump |
| 3 | Searching for a matching init-bump dependabot PR to pair with the analyze bump | Dependabot had not filed one — nothing covers `init` unless you add the alignment commit yourself | Do not wait for dependabot to complete the family; push the family-alignment commit to the chosen PR yourself |

## Results & Parameters

### Observed failure signature (Charybdis #269, 2026-07-16)

```text
Loaded a configuration file for version '4.36.2', but running version '4.36.3'
CodeQL job status was configuration error
```

### Family grep

```bash
grep -rn "github/codeql-action" .github/workflows/
# Every hit (init / analyze / upload-sarif, across ALL workflow files) must pin the same commit SHA.
```

### Tag-deref verification snippet

```bash
TAG=v4.36.3
REF=$(gh api "repos/github/codeql-action/git/ref/tags/$TAG" --jq '{type: .object.type, sha: .object.sha}')
TYPE=$(echo "$REF" | jq -r .type); SHA=$(echo "$REF" | jq -r .sha)
if [ "$TYPE" = "tag" ]; then
  SHA=$(gh api "repos/github/codeql-action/git/tags/$SHA" --jq '.object.sha')
fi
echo "pin uses: github/codeql-action/<sub-action>@$SHA  # $TAG"
```

### Alignment-commit message template

```text
ci: align codeql-action family (init/analyze/upload-sarif) to <vX.Y.Z>

The codeql-action sub-actions enforce internal version consistency; a partial
bump fails the CodeQL job with "Loaded a configuration file for version 'A',
but running version 'B'" (configuration error). Aligning all family pins to
<commit-sha> (<vX.Y.Z>) in one PR. Sibling dependabot PR #<N> is superseded.
```

### Known partial-bump tolerance (do not rely on it)

- A lone `upload-sarif` bump (newer than `init`) passed in at least one observed combination (Proteus #200) — undocumented; still move the family together.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectCharybdis (HomericIntelligence) | Dependabot PRs #269/#270 — analyze-only bump failed with config error; family alignment went green | 2026-07-16 |
| ProjectProteus (HomericIntelligence) | Dependabot PRs #204/#200 — sibling-PR collapse after alignment; lone upload-sarif bump tolerated (not relied upon) | 2026-07-16 |
