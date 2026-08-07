---
name: codeql-action-family-version-alignment
description: "Keep every github/codeql-action sub-action in a workflow on one release and immutable commit. Use when: (1) Dependabot updates init, analyze, or upload-sarif independently, (2) CodeQL reports a configuration-version mismatch, or (3) a non-required scanning check could fail without blocking a merge."
category: ci-cd
date: 2026-08-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [codeql, github-actions, dependabot, action-pinning, security-scanning, ci]
---

# CodeQL Action Family Version Alignment

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-08-07 |
| Objective | Prevent partial updates of the CodeQL action family from disabling security scanning. |
| Outcome | Treat `init`, `analyze`, and `upload-sarif` as one atomic dependency and verify both the workflow pins and the resulting check. |

## When to Use

- An update changes only one `github/codeql-action/*` reference.
- A run says its loaded configuration and running action have different versions.
- Separate dependency-update PRs target sibling CodeQL sub-actions.
- CodeQL is informative rather than required, so a red scan may not block merging.
- A full commit pin must be checked against an annotated release tag.

## Verified Workflow

### Quick Reference

```bash
rg -n 'github/codeql-action/(init|analyze|upload-sarif)@' .github/
```

Every result participating in one scan must resolve to the same release and commit. If an automated update changes one member, add an alignment commit to that PR or replace the sibling PRs with one atomic update.

1. Inventory the entire `.github/` tree, not only the file named by the update.
2. Group references by scan pipeline. Align `init`, `analyze`, and any `upload-sarif` steps that consume the same analysis artifacts.
3. Resolve the release tag to its commit. Annotated tags require dereferencing the tag object before comparing the workflow pin.
4. Preserve least-privilege permissions and all existing scan languages, triggers, query suites, and build modes; this is a dependency alignment, not a workflow redesign.
5. Run the workflow and inspect the CodeQL job itself. A green required-check summary is insufficient when CodeQL is not required.
6. Close or supersede sibling dependency PRs only after their intended version is represented by the aligned change.

The invariant is:

```text
one scan pipeline -> one CodeQL action release -> one immutable commit
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Merge one generated update | Updated `analyze` while `init` remained on the prior release | CodeQL rejected the mixed configuration before analysis | Treat the sub-actions as one atomic dependency family |
| Rely on branch protection | Assumed any broken scan would block merging | CodeQL was not a required context, so the repository could merge with scanning disabled | Inspect the scan result explicitly or make the intended check required |
| Compare an annotated tag object directly | Compared the workflow commit with the tag object's SHA | Annotated tag SHA and peeled commit SHA are different objects | Dereference annotated tags before validating immutable pins |

## Results & Parameters

| Check | Expected result |
|-------|-----------------|
| Family inventory | All participating sub-actions use one commit |
| Tag verification | Peeled release-tag commit equals the workflow pin |
| Workflow behavior | CodeQL job completes without a configuration-version error |
| Scope | No unrelated query, language, permission, or trigger changes |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| C++ continuous-integration pipeline | Partial automated action update | Mixed family versions reproduced the configuration error; aligning the family restored the scan locally. |
