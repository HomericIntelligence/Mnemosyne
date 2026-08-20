---
name: release-workflow-planning-assumptions-and-risks
description: "Audit first-release plans for assumptions that must be verified: real tag/release lineage, CHANGELOG links, manifest schema, runtime compatibility, signing capability, action pins, and required-check wiring. This is planning guidance, not a release-workflow implementation recipe."
category: ci-cd
date: 2026-07-02
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: unverified
history: release-workflow-planning-assumptions-and-risks.history
tags:
  - planning
  - release-automation
  - first-release
  - version-lineage
  - changelog
  - signed-tags
  - required-checks
  - supply-chain
---

# Release Workflow Planning Assumptions and Risks

## Overview

A first-release plan often presents guesses as decisions: the next version, whether CHANGELOG tags
exist, the manifest's version table, the runner's Python version, signing-key availability, or the
identity of a required check. Convert every such claim into a discovery command and record its
observed result before implementation.

This skill is a reviewer checklist. Implementation mechanics belong in release-workflow and
lockfile skills. All guidance here remains `unverified`: its source cases were planning sessions,
not executed release implementations. Case provenance is in
[release-workflow-planning-assumptions-and-risks.notes.md](release-workflow-planning-assumptions-and-risks.notes.md),
and the complete prior content is in
[release-workflow-planning-assumptions-and-risks.history](release-workflow-planning-assumptions-and-risks.history).

## When to Use

- A plan chooses a version from CHANGELOG headings without checking tags and GitHub Releases.
- An `[Unreleased]` compare URL assumes a tag that may not exist.
- Reused code assumes `[workspace]`, `[project]`, or another manifest table without reading it.
- A script imports `tomllib` while the runner's Python version is unknown.
- A recipe uses `git tag -s` without proving a signing key exists in its execution environment.
- Issue citations disagree with live files or reachable commits.
- A third-party action pin was copied rather than resolved from the current upstream ref.
- A new canonical `release` status check is proposed in a repository with no release contract.

## Verified Workflow

### 1. Establish the real release lineage

```bash
git tag --list --sort=-version:refname
gh release list --repo "$REPO" --limit 100
git log --oneline --decorate -20
```

Read the manifest version and CHANGELOG sections separately. Tags and published releases are
release ground truth; CHANGELOG headings are documentation. If the four sources disagree, record
the disagreement rather than forcing the manifest to match an unshipped heading.

For a never-tagged repository, choose the next version as an explicit product decision. Do not
retroactively declare historical CHANGELOG sections released.

### 2. Make a valid tagless CHANGELOG link

When no release tag exists, use the root commit as the compare base:

```bash
ROOT_SHA=$(git rev-list --max-parents=0 HEAD | tail -1)
printf '[Unreleased]: https://github.com/%s/compare/%s...HEAD\n' \
  "$REPO" "$ROOT_SHA"
```

State the producer string and validator regex together. Execute the validator against the literal
artifact; do not merely assert that they match. The positive check must accept both a root SHA now
and `vX.Y.Z` later, while the negative check rejects a phantom version-tag base.

```bash
printf '%s\n' "$FOOTER" | grep -E '/compare/([0-9a-f]{40}|v[0-9]+\.[0-9]+\.[0-9]+)\.\.\.HEAD$'
```

### 3. Inspect the actual manifest schema

```bash
rg -n '^\[(project|workspace|tool\.[^]]+)\]|^version\s*=' \
  pyproject.toml pixi.toml Cargo.toml package.json 2>/dev/null
```

Parse the table that exists. Do not transplant `pixi["workspace"]["version"]` or
`project["version"]` from another repository. Define what happens when the field is absent,
duplicated, dynamic, or not a string.

### 4. Verify runtime compatibility

Find the Python version from the actual runner setup and project constraints:

```bash
rg -n 'python-version|requires-python|python\s*=' .github pyproject.toml pixi.toml
```

If Python 3.11 is not guaranteed, decide whether to use a `tomli` fallback or a different parser
and declare the dependency. Do not add a silent import fallback that is absent from the lockfile.

### 5. Treat signing as a capability

Probe the environment that creates the tag:

```bash
git config --get user.signingkey
gpg --list-secret-keys --with-colons
```

Choose and document one behavior: require signing and fail clearly, or sign when available and
produce an explicit unsigned artifact otherwise. Pre-commit signing proves nothing about tag-key
availability in CI.

### 6. Revalidate issue evidence and action pins

```bash
git cat-file -e "$CITED_SHA^{commit}"
git show "$CITED_SHA:path/to/file"
git ls-remote https://github.com/OWNER/ACTION.git refs/tags/vX
```

If issue evidence contradicts live state, call out the contradiction with current file/commit
evidence. Resolve action SHAs at planning time from their canonical repository, then preserve the
immutable SHA and human-readable version comment.

### 7. Wire the required check to a real job

Inspect reusable workflow callers, job `name:` values, and live ruleset contexts:

```bash
rg -n 'uses: .*_required\.yml|name:.*release|check_version' .github/workflows
gh api "repos/$REPO/rulesets"
```

A ruleset pins the emitted check-run name, not an aspirational workflow filename. Do not rename an
existing required job casually or add a standalone always-green job that no ruleset requires.

If a repository has no release model but governance requires a canonical `release` check, the same
PR should bootstrap a minimal real contract:

- manifest and CHANGELOG semantics;
- a behavior-based version validator;
- dry-run validation attached to an existing required workflow;
- publish behavior confined to the tag/release workflow.

The required PR check must validate artifacts without publishing. The tag workflow may enforce
tag/manifest/CHANGELOG equality and publish only after that passes.

## Decision Matrix

| Question | Evidence | Planning response |
| --- | --- | --- |
| Has a version shipped? | Git tags and GitHub Releases | Derive lineage from real releases |
| No tags or releases? | Both commands empty | Choose a forward version; use root-SHA compare link |
| Where is version stored? | Parsed live manifest | Implement against that table and failure modes |
| Is `tomllib` available? | Runner and package constraints | Require 3.11 or declare a fallback |
| Can the environment sign? | Secret-key/config probe | Fail clearly or document explicit unsigned mode |
| Is a check actually required? | Workflow callers and ruleset contexts | Attach validation to the emitted required job |
| Does the plan's output pass its test? | Literal artifact executed through validator | Record observed output, not an assertion |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Infer releases from CHANGELOG headings | Documented versions may never have shipped | Reconcile tags, releases, manifest, and CHANGELOG |
| 2 | Link from a nonexistent `v0.1.0` | Compare URL is phantom | Use root SHA until a real tag exists |
| 3 | Use `/commits/main` while tests require `/compare/...HEAD` | Producer and validator contradict each other | Define once and execute parity check |
| 4 | Copy a TOML lookup from another repo | Wrong table raises or reads the wrong version | Inspect and parse the target schema |
| 5 | Assume commit signing means tag signing works | Different environment and key path | Probe the actual tag producer |
| 6 | Trust issue-body SHAs over live Git | Plan solves stale or fictional state | Verify each citation and report contradictions |
| 7 | Copy a marketplace action SHA | Pin may be stale or wrong | Re-resolve from the canonical action repository |
| 8 | Add an always-green `release` job | Fabricates governance without a contract | Bootstrap validator and artifacts in the same PR |

## Results & Parameters

- Release lineage comes from reachable tags and GitHub Releases, not headings alone.
- A never-tagged repository uses its immutable root SHA as the initial compare base.
- The runner version decides whether `tomllib` is available or a dependency is required.
- Signing behavior is selected only after probing the tag-producing environment.
- The producer artifact must be executed through the exact planned validator.
- Required-check wiring is proven from emitted job names, callers, and live rulesets.

## Plan Acceptance Checklist

- The plan records output from tags, releases, manifest, and CHANGELOG discovery.
- Never-released and previously-released paths are explicit.
- The CHANGELOG producer string passes the exact planned validator.
- Manifest table and parser/runtime compatibility are confirmed.
- Signing behavior is explicit and capability-based.
- Every cited SHA and third-party action pin is revalidated.
- The proposed check-run name exists on the intended required workflow path.
- Dry-run PR validation cannot publish; tag publication cannot bypass parity checks.
- Unverified assumptions are labeled as such and assigned to implementation-time verification.

## Evidence Boundary

ProjectOdyssey issue #189 and Mnemosyne issue #2913 supplied planning observations only. No release
implementation or CI result was executed for this skill, so its verification remains `unverified`.
