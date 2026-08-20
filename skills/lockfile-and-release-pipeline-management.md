---
name: lockfile-and-release-pipeline-management
description: "Recover generated lockfiles, resync locks after manifest edits, repair no-op release recipes, enforce one version source, configure multi-ecosystem dependency automation, recover garbage-collected nightly pins, and stabilize Dependabot contract tests without deleting coverage. Use when lock/release CI disagrees with manifests or bot updates must move exact peers together."
category: ci-cd
date: 2026-06-17
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
history: lockfile-and-release-pipeline-management.history
tags: [lockfile, release, pixi, npm, cargo, versioning, renovate, dependabot]
---

# Lockfile and Release Pipeline Management

## Overview

Lockfiles are generated evidence of a manifest and resolver state. Restore them verbatim only when
the source manifest is identical to a known-green base; otherwise regenerate with the correct tool
and inspect semantic deltas. Releases likewise need one version authority and idempotent behavior
when files already contain the target version.

Detailed incidents are indexed in
[`lockfile-and-release-pipeline-management.notes.md`](lockfile-and-release-pipeline-management.notes.md).
The complete prior source is in
[`lockfile-and-release-pipeline-management.history`](lockfile-and-release-pipeline-management.history).

## When to Use

- CI rejects a generated lock while its source manifest is unchanged from main.
- `package.json` changed without `package-lock.json` and `npm ci` reports EUSAGE.
- A release recipe fails on “nothing to commit” although versions already equal the target.
- Version literals exist in multiple source/config files.
- Renovate must cover Conan, FetchContent, pixi, Actions, and containers.
- A pinned nightly/dev artifact disappeared from its channel.
- Dependabot PRs fail because tests pin current versions or exact-peer packages split across PRs.

## Verified Workflow

### 1. Classify drift before touching the lock

Identify each lock’s source manifests and compare them with the trusted base:

```bash
git diff origin/main -- <manifest-paths>
git diff origin/main -- <lock-path>
```

If manifests are byte-identical and current main passed the same lock validation at that SHA, restore
the lock verbatim from main and verify zero diff. Do not run the installer afterward; it may rewrite
the recovered artifact with a different local resolver version.

If any source changed, regenerate instead. Record tool/version/platform/channels/registries and audit
why packages changed rather than treating a large generated diff as opaque.

### 2. Regenerate npm locks with the manifest

After `package.json` edits, run the repository-approved locked npm command (commonly
`npm install --package-lock-only` with the supported npm version), inspect root dependency entries,
then prove `npm ci` from a clean install. Commit manifest and lock together. Never hand-edit integrity
or resolved fields.

### 3. Make release version bumps idempotent

Diagnose a failed release before retrying:

```bash
git status --short
rg -n 'version\s*=|__version__' <version-surfaces>
git tag --list 'v<target>'
```

If files already hold the target, the bump step should report unchanged and continue to validation,
commit-if-needed, tag, and publish; it must not require a version-file commit. Tag directly only after
the tree is clean, current HEAD is the intended release commit, artifacts/checks are green, the tag
does not exist locally/remotely, and repository policy authorizes that recovery.

### 4. Establish one version source

Prefer installed metadata or VCS-derived version as canonical. Runtime modules read
`importlib.metadata.version(<distribution-name>)` with a documented source-tree fallback. Parse
pyproject with `tomllib` in consistency checks; avoid regex/string comparisons. Register the semantic
invariant in pre-commit/CI rather than duplicating a literal into many files.

### 5. Configure dependency automation per ecosystem

Inventory every manager and generated file. Configure Renovate managers for manifests actually
consumed by the build: Conan, CMake/FetchContent, pixi, GitHub Actions, Dockerfiles, npm/Cargo, and
custom regex only where no native manager exists. Pin action digests according to policy, group exact
peer families, define schedules/labels, and require lock maintenance through the real resolver.

Install/authorize the App separately from committing config. Validate discovery output so a valid
config that finds zero dependencies is not called success.

### 6. Recover garbage-collected nightly pins

When the solver reports no candidate for an exact dev/nightly build, query the configured channel and
prove the pin is absent. Select the newest compatible available build according to project policy,
update the manifest, then run the correct install/lock-producing command. Do not invent a `pixi lock`
subcommand on versions where lock generation is an `install` side effect.

Audit transitive changes and run the package’s import/test smoke. A lockfile copied from main cannot
repair a manifest whose exact artifact no longer resolves.

### 7. Stabilize lock-backed Dependabot contracts

Group failing bot PRs by signature. Replace tests that assert today’s exact version with structural
properties:

- policy-required dependencies remain exactly pinned where necessary;
- lock root/package entries equal the manifest;
- related package-family entries are internally compatible;
- required features/sources remain present.

Do not delete the contract test. When packages have exact peer coupling, update them in one grouped
PR and regenerate one coherent lock. After the stabilization change lands, refresh/rebase open bot
branches so they run against the new structural contract.

### 8. Verify release and dependency outcomes

Run lock/install checks from a clean environment, the full required suite, version invariant,
artifact version inspection, and tag/release dry run. Verify the remote tag points to the intended
signed commit and published artifact metadata matches it. For automation, confirm managers discover
the expected dependencies and sample PRs update manifest plus lock coherently.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Blind lock restore | Copied main lock after manifest changed | Lock no longer represented source | Restore only on identical manifest |
| Regenerate known-good drift | Ran local resolver on unchanged manifest | Produced unrelated solver churn | Restore verbatim and stop |
| Manifest-only npm edit | Changed package.json alone | `npm ci` rejected lock mismatch | Regenerate/commit pair |
| No-op release failure | Required version edit to create commit | Target already present | Make bump and commit conditional |
| Duplicate literals | Updated versions in several files | Surfaces drifted | One metadata/VCS source plus invariant |
| Valid config, zero discovery | Assumed Renovate config was enough | Managers found nothing | Verify actual dependency discovery |
| Copy lock for missing nightly | Restored generated file only | Manifest pin was unavailable | Repin available artifact then resolve |
| Exact-version contract test | Asserted current dependency literal | Every bot update failed by design | Assert structural consistency |
| Split peer updates | Opened separate exact-peer PRs | Solver could not satisfy intermediate state | Group family and regenerate once |

## Results & Parameters

```text
lockfile and authoritative manifest set
base SHA/main check evidence and manifest-equality result
resolver/tool version, platform, channels/registries
old/new direct and notable transitive dependencies
release target, version authority, HEAD, local/remote tag state
artifact versions and publish environment
Renovate managers, grouping, schedule, discovery counts
nightly pin availability query and replacement rationale
Dependabot failure groups and structural contract assertions
clean install, required suite, invariant, and remote release evidence
```

## Verified On

- Pixi/Cargo/npm lock recovery, release no-op repair, version invariants, Renovate setup, nightly pin
  recovery, and Dependabot contract stabilization through 2026-06-17.
- Verification remains `verified-ci`; case-specific local observations are identified in notes.
