---
name: central-version-manifest-drift-from-automation-bypass
description: "When a repo declares `versions.yml`/`versions.json`/`versions.toml` as single source of truth for pinned versions, automated bumps (Dependabot, weekly cron, hand-edits) often update only the consumer files (Dockerfiles, workflows) and bypass the manifest. Result: drift + automation silently breaks. Use when: (1) reviewing a base-image / pinned-tool bump PR, (2) auditing why a digest-refresh cron has stopped producing PRs, (3) onboarding a repo that has a centralized versions manifest, (4) writing or modernizing an update workflow that touches Dockerfiles or pinned-tool scripts."
category: ci-cd
date: 2026-05-31
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - manifests
  - dependabot
  - drift
  - base-images
  - supply-chain
  - single-source-of-truth
  - dockerfile
  - github-actions
---

# Central Version Manifest Drift From Automation Bypass

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-31 |
| **Objective** | Catch a class of PRs that quietly desync a "single source of truth" versions manifest from the files it claims to govern |
| **Outcome** | Caught 3/11 Dependabot PRs (#681, #682, #683 on HomericIntelligence/AchaeanFleet) in one review session — each landed only the Dockerfile change and left `versions.yml` lying |
| **Verification** | verified-local (manifest-vs-Dockerfile mismatch reproduced; `digest-bump.yml` silently skipping confirmed by reading the workflow's hardcoded grep pattern) |

## When to Use

- Reviewing a Dependabot or contributor PR that bumps a base image, language toolchain, or pinned binary in a Dockerfile
- The repo has any of: `versions.yml`, `versions.json`, `versions.toml`, `versions/`, `pins.yaml`, `tool-versions.yaml`, `.versions/`
- The repo has a scheduled workflow (cron) that refreshes digests or pinned hashes by editing source files in place (grep/sed style)
- A weekly "digest-bump" / "update-pins" cron has gone quiet (no PRs opened for several cycles)
- Onboarding a new repo and you see a manifest header that claims to be "the single source of truth" — verify before trusting it
- Writing or refactoring an update workflow that touches Dockerfiles, install scripts, or `FROM` lines

## Verified Workflow

### Quick Reference

```bash
# === Pre-approval checklist for any base-image / pinned-tool bump PR ===

OWNER_REPO="HomericIntelligence/AchaeanFleet"
PR="682"

# 1. Does the repo claim a central versions manifest?
ls versions.yml versions.json versions.toml .versions/ pins.yaml tool-versions.yaml 2>/dev/null

# 2. If yes, does the PR diff include it?
gh pr diff "$PR" --repo "$OWNER_REPO" --name-only | grep -E '^(versions\.(yml|json|toml)|pins\.yaml|tool-versions\.yaml)$'
# Empty output + step 1 hit  =>  manifest update missing => REQUEST_CHANGES

# 3. Does any workflow hardcode the OLD version/digest in grep/sed?
OLD_VERSION="25-slim"          # extract from the PR's "before" side
OLD_DIGEST="sha256:67134eb"    # extract from the PR's "before" side
grep -rn -E "$OLD_VERSION|$OLD_DIGEST" .github/workflows/
# Matches  =>  bump-automation will silently skip after merge => flag as follow-up

# 4. Is `used_by:` (if present) actually accurate?
yq '.base_images.*.used_by[]' versions.yml | sort -u
git ls-files 'bases/Dockerfile.*' 'vessels/**/Dockerfile' | sort -u
# Diff the two => any Dockerfile not in used_by is hidden drift
```

### Detailed Steps

#### Step 1 — Detect that a central manifest exists

A versions manifest is any file at the repo root (or `.versions/`, `versions/`) named with a `versions.*` / `pins.*` / `tool-versions.*` pattern. The give-away is a header comment like:

```yaml
# Single source of truth for all pinned tool versions and checksums across
# base images and vessel Dockerfiles.  When upgrading a tool, update this
# file and mirror the change into the relevant Dockerfile(s).
base_images:
  node:
    tag: "25-slim"
    digest: "sha256:67134eb…"
    used_by: [bases/Dockerfile.node, bases/Dockerfile.minimal]
```

If you see that header, the repo has staked a contract. Every base-image / pinned-tool change MUST update this file or the contract is broken.

#### Step 2 — Verify the PR honours the contract

For Dependabot-class PRs the title usually looks like `chore(deps): bump node from 25-slim to 26-slim in /bases`. These almost always touch only the Dockerfile. Confirm:

```bash
gh pr diff "$PR" --repo "$OWNER_REPO" --name-only
```

If the changed-files list does NOT contain the manifest file, the PR is incomplete. Verdict: **REQUEST_CHANGES** with a comment like:

> This PR bumps `bases/Dockerfile.node` to `node:26-slim` but leaves `versions.yml` declaring `tag: "25-slim"`. The repo's `versions.yml` header pins it as the single source of truth — please update `.base_images.node.tag`, `.base_images.node.digest`, and any matching `used_by:` entries in the same commit so they cannot diverge.

#### Step 3 — Detect upstream automation that will silently break

The deeper problem: the bump-automation itself often hardcodes the old version in a grep/sed pattern. Once the Dockerfile moves to `node:26-slim`, the workflow's grep matches zero lines and exits 0 with no error.

```bash
# Example real-world breakage in .github/workflows/digest-bump.yml:
#   line 70: grep -l 'node:25-slim' bases/
#   line 73: sed -i "s|node:25-slim@sha256:[a-f0-9]*|node:25-slim@$NEW_DIGEST|" "$f"
# After PR #682 merges with node:26-slim, both lines do nothing.

grep -rn -E "${OLD_VERSION}|${OLD_DIGEST}" .github/workflows/ scripts/
```

If you find matches, the PR will land **and** the weekly digest refresh will stop. File a follow-up issue or block the PR until both are updated together.

#### Step 4 — Audit `used_by:` accuracy

If the manifest tracks consumers (`used_by: [paths]`), compare against the actual filesystem:

```bash
yq '.base_images.*.used_by[]' versions.yml | sort -u  > /tmp/manifest_consumers.txt
git ls-files 'bases/Dockerfile.*' 'vessels/**/Dockerfile' 'images/**/Dockerfile' \
  | sort -u > /tmp/actual_dockerfiles.txt
diff /tmp/manifest_consumers.txt /tmp/actual_dockerfiles.txt
```

Any Dockerfile in `/tmp/actual_dockerfiles.txt` but not in `/tmp/manifest_consumers.txt` is a hidden consumer — the next bump for that base will silently miss it.

#### Step 5 — Recommend the root-cause fix in the review

Replace the grep/sed worker in the bump workflow with a parser that reads the manifest and writes both. Pseudo-code (yq):

```bash
# Update manifest first
yq eval ".base_images.node.tag = \"$NEW_TAG\"" -i versions.yml
yq eval ".base_images.node.digest = \"$NEW_DIGEST\"" -i versions.yml

# Then derive Dockerfile content from manifest
for f in $(yq '.base_images.node.used_by[]' versions.yml); do
  new_from="FROM node:$(yq '.base_images.node.tag' versions.yml)@$(yq '.base_images.node.digest' versions.yml)"
  sed -i "s|^FROM node:.*|$new_from|" "$f"
done
```

This inverts the data flow: the manifest is the source, Dockerfiles are derived. Drift becomes structurally impossible.

#### Step 6 — Audit historical drift

Before approving any new manifest change, look back:

```bash
# Every base-image / pinned-tool bump commit SHOULD have touched the manifest.
git log --format="%h %s" --since="6 months ago" -- bases/Dockerfile.* \
  | while read sha msg; do
      if ! git show --name-only --format= "$sha" | grep -q '^versions\.yml$'; then
        echo "DRIFT: $sha $msg (manifest not touched)"
      fi
    done
```

Output lines are historical drift incidents. Each one is a bug fix candidate.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Approve PR #682 because the new `node:26-slim` digest itself was correct | Spot-check the digest value, confirm it pins a real published image, click APPROVE | Lands the bump but leaves `versions.yml` declaring `tag: "25-slim"` — manifest now lies about the file it claims to govern | A bump PR is judged not only on the value being set but on every file the value SHOULD be set in |
| Patch the drift by editing only the Dockerfile after merge | Hand-edit `bases/Dockerfile.node` back to a consistent state, ignore the manifest | The weekly `digest-bump.yml` cron grep-greps the OLD version string and will silently skip on the next run; the leak gets bigger every cycle | Manifest drift and workflow grep-fragility are the same bug — fix both or fix neither |
| Trust the `used_by:` field at face value | Read `versions.yml.base_images.python.used_by` and assume it lists every consumer | `Dockerfile.python` was missing even though it consumes the python base; bumps based on `used_by` skipped it for months | Treat `used_by:` as a hint, not a contract — verify with `git ls-files` until a CI gate proves equivalence |
| Re-run the bump workflow manually after the bump PR merges, hoping it will "catch up" | `gh workflow run digest-bump.yml` after merging the version bump | The workflow's hardcoded `node:25-slim` grep returns zero matches; the job exits 0 successfully with nothing to do; nobody notices for weeks | A workflow that succeeds with zero work is indistinguishable from a workflow that succeeds with real work — add a guard that fails when expected substitutions return 0 hits |

## Results & Parameters

```yaml
# Symptoms / triggers
trigger:
  - "Dependabot opens PRs that bump base-image FROM lines"
  - "Weekly digest-bump cron has stopped producing PRs"
  - "versions.yml claims SoT in its header"

# Repo signatures
manifest_files:
  - versions.yml
  - versions.json
  - versions.toml
  - pins.yaml
  - tool-versions.yaml
  - .versions/

fragile_workflow_patterns:
  - "grep -l '<tool>:<exact-version>' bases/"
  - "sed -i 's|<tool>:<exact-version>@sha256:[a-f0-9]*|...|' \"$f\""
  - "grep -rn 'FROM <tool>:<exact-version>' ."

# Review verdicts
verdict_table:
  manifest_exists_and_in_diff: APPROVE
  manifest_exists_and_NOT_in_diff: REQUEST_CHANGES
  no_manifest_but_workflow_has_hardcoded_old_version: APPROVE + follow-up issue
  manifest_exists_AND_workflow_hardcodes_old_version: REQUEST_CHANGES + follow-up issue

# Tools used
shell_tools:
  - "gh pr diff <N> --repo <owner/repo> --name-only"
  - "yq eval '.base_images.<tool>.used_by[]'"
  - "git ls-files 'bases/Dockerfile.*'"
  - "grep -rn '<old-version>' .github/workflows/"

# Real-world hit rate
session_hit_rate: "3 of 11 Dependabot PRs (27%) — #681 python, #682 node, #683 debian on HomericIntelligence/AchaeanFleet"
```

### Detection Heuristic (one-liner)

```bash
# Returns true if repo claims a versions manifest AND has at least one workflow
# that hardcodes a version string in grep/sed (the high-risk combo).
test -f versions.yml && \
  grep -rqlE 'grep .*(:|@sha256:)[a-zA-Z0-9._-]+|sed .*(:|@sha256:)[a-zA-Z0-9._-]+' .github/workflows/ && \
  echo "AT_RISK: manifest + hardcoded-version workflow combo"
```

### Comment Template (REQUEST_CHANGES)

```text
This PR bumps `<dockerfile-path>` to `<tool>:<new-tag>` but `versions.yml`
still declares `.base_images.<tool>.tag: "<old-tag>"`. Per the manifest's
header ("Single source of truth for all pinned tool versions … When
upgrading a tool, update this file and mirror the change into the
relevant Dockerfile(s)"), please:

1. Update `.base_images.<tool>.tag` and `.base_images.<tool>.digest`
   in `versions.yml` in this same PR.
2. Confirm `.base_images.<tool>.used_by[]` lists every Dockerfile that
   actually consumes this base.
3. Note that `.github/workflows/<bump-workflow>.yml` hardcodes the OLD
   version in its grep/sed pattern — once this PR merges, that workflow
   will silently no-op until the pattern is parameterised from
   `versions.yml`. Opening a follow-up issue is acceptable; do not let
   it slip.
```

## Related Skills

- `dependabot-pr-scope-contamination-check-the-diff` — the contamination angle on the same class of PRs; always run both checks on a Dependabot bump.
- `verify-audit-findings-before-acting` — don't trust the PR label or title; read the actual diff with `gh pr diff <N> --name-only`.
- `python-version-drift-detection` — a narrower instance of the same pattern (pyproject.toml classifier vs Dockerfile FROM); generalise into manifest discipline.
- `doc-config-drift-check` — the docs/config sibling; both are manifest discipline at different layers.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| HomericIntelligence/AchaeanFleet | Dependabot session 2026-05-31 review of 11 PRs | PR #681 (python), #682 (node), #683 (debian) all bumped the Dockerfile only; `versions.yml` left at the prior tag; `digest-bump.yml` lines 33, 70-73 grep/sed against the OLD version, would silently no-op after merge |
