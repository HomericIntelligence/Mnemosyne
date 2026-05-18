---
name: github-action-transitive-pin-failure-diagnosis
description: "Diagnose 'Unable to resolve action' failures at workflow startup where the named action is NOT one your workflow references directly — it's a transitive dependency pinned inside a wrapper/composite action you do use. Use when: (1) a GHA job fails at the 'Set up job' phase before any of your code runs with `Unable to resolve action <owner>/<other-action>@<ver>` and that <other-action> is not anywhere in your workflow files, (2) version-bumping the wrapper action you DO reference doesn't fix it, (3) you're about to attempt a 3rd version pin on the same wrapper action and should stop."
category: ci-cd
date: 2026-05-18
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [ci, github-actions, trivy, composite-action, transitive-dependency, version-pin, debugging]
---

# GitHub Action Transitive Pin Failure Diagnosis

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-18 |
| **Objective** | Recognize when a `Unable to resolve action` error names an action your workflow does not reference because the broken pin lives INSIDE a wrapper/composite action, and stop wasting CI iterations playing version-pin whack-a-mole. |
| **Outcome** | Verified on ProjectAgamemnon PR #400 across 3 distinct pin attempts on `aquasecurity/trivy-action`. After the 2nd failed pin, the correct play is "drop the step and file a tracking issue," not another pin bump. |
| **Verification** | verified-local |

## When to Use

- A GitHub Actions job fails at the "Set up job" phase (BEFORE any of your steps execute) with `Unable to resolve action '<owner>/<action>@<ver>', unable to find version '<ver>'`.
- The `<owner>/<action>` named in the error does NOT appear anywhere in your `.github/workflows/*.yml` files (i.e., you never `uses:` it directly).
- You DO reference a wrapper/composite action from the same or related publisher (classic: workflow uses `aquasecurity/trivy-action@vX.Y.Z`, error names `aquasecurity/setup-trivy@v0.2.2`).
- You've already tried one or two version pins on the wrapper action and they failed for different reasons (tag doesn't exist, internal SHA still missing, etc.).
- You're tempted to bump-and-retry a 3rd time — STOP and apply the playbook below.

## Verified Workflow

### Quick Reference

```bash
# 1) Identify the wrapper action you ACTUALLY reference (in your workflow YAML).
WRAPPER_OWNER="aquasecurity"
WRAPPER_ACTION="trivy-action"
WRAPPER_VERSION="v0.30.0"   # whatever version your workflow pins

# 2) Read its action.yml to find the transitive pin that the runner is failing on.
curl -fsSL "https://raw.githubusercontent.com/${WRAPPER_OWNER}/${WRAPPER_ACTION}/${WRAPPER_VERSION}/action.yml" \
  | grep -nE 'uses:'

# 3) List recent releases of the wrapper to find a candidate that may pin a valid transitive.
curl -fsSL "https://api.github.com/repos/${WRAPPER_OWNER}/${WRAPPER_ACTION}/releases?per_page=10" \
  | grep '"tag_name"'

# 4) Confirm the transitive ref exists at the version the wrapper expects.
TRANSITIVE_OWNER="aquasecurity"
TRANSITIVE_ACTION="setup-trivy"
TRANSITIVE_VERSION="v0.2.6"
curl -fsSL "https://api.github.com/repos/${TRANSITIVE_OWNER}/${TRANSITIVE_ACTION}/releases/tags/${TRANSITIVE_VERSION}" \
  | grep '"tag_name"'

# 5) Two-strikes-and-drop rule: after 2 failed pin attempts, remove the step from this PR
#    and file a tracking issue with: (a) exact runner error, (b) link to upstream action.yml
#    line that names the broken transitive ref, (c) what versions you tried.
```

### Detailed Steps

1. **Read the error carefully.** Note the owner/action/version of the action that the runner failed to resolve. Compare it to the `uses:` lines in your workflow YAML. If the failing action is NOT in your YAML, it's transitive — proceed.
2. **Locate the wrapper action's `action.yml`.** Fetch it from `raw.githubusercontent.com/<owner>/<action>/<version>/action.yml`. Composite actions have one or more `uses:` lines inside `runs.steps`. One of those lines names the broken transitive (with a SHA pin and a `# vX.Y.Z` comment).
3. **Try the latest non-beta release of the wrapper FIRST.** Newer wrapper releases typically re-pin to a transitive that still exists. List releases via `gh api` or `curl`, pick the latest, retry. Cost: 1 CI iteration.
4. **If the latest wrapper release still fails**, inspect that release's `action.yml`. The wrapper may have been left referencing a SHA that was force-pushed or a tag that was deleted upstream. This is not something you can fix downstream.
5. **Apply the two-strikes rule.** If 2 pin attempts have failed:
   - Drop the failing step from your PR. Keep your PR focused on what you actually changed; don't let unrelated upstream breakage block you.
   - File a tracking issue. Include: the exact runner error, the wrapper version(s) you tried, the link to the line in upstream `action.yml` that names the broken transitive ref, and a TODO to re-enable the step once upstream is fixed.
   - Move on. Do NOT do a third pin attempt.
6. **Do not** add `continue-on-error: true` or `|| true` to mask the failure — this hides the issue and conflicts with `forbid-continue-on-error` / `forbid-suppressions` lint guards.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Keep original pin `aquasecurity/trivy-action@v0.30.0` | Wrapper internally pins `aquasecurity/setup-trivy@v0.2.2`, which does not exist on the marketplace | The wrapper's transitive pin is the actual broken ref; your direct pin existing is irrelevant |
| 2 | Re-pin to `aquasecurity/trivy-action@0.19.0` (no leading `v`) | Tag literally does not exist with that format; `aquasecurity/trivy-action` uses `vX.Y.Z` tags | Always check tag format on the wrapper's Releases page before pinning |
| 3 | Bump to latest: `aquasecurity/trivy-action@v0.36.0` | Action resolved cleanly (transitive setup-trivy@v0.2.6 exists), but downstream Docker build then OOM/timed out for unrelated reasons in this repo | Resolution success doesn't mean the step will pass — separate the action-resolution problem from runtime problems |
| 4 | Drop the trivy step from the PR entirely; file tracking issues | WORKED. PR unblocked. Upstream breakage tracked separately for later fix | After 2 failed pins, drop + track is faster than continuing pin attempts |

## Results & Parameters

**Verified pin outcomes for `aquasecurity/trivy-action` on 2026-05-17/18 (ProjectAgamemnon PR #400):**

| Pinned version | Result |
|----------------|--------|
| `aquasecurity/trivy-action@v0.30.0` | Fails: internal `setup-trivy@v0.2.2` does not exist |
| `aquasecurity/trivy-action@0.19.0` | Fails: tag itself does not exist (wrong format, missing leading `v`) |
| `aquasecurity/trivy-action@v0.36.0` | Resolves; downstream Docker build then fails (OOM/Conan), separate concern |
| Drop the trivy step + open tracking issue | Worked; PR merged |

**Confirmed-existing transitive refs (for reference):**

| Transitive | Confirmed |
|------------|-----------|
| `aquasecurity/setup-trivy@v0.2.6` | Exists |
| `aquasecurity/setup-trivy@v0.2.2` | Does NOT exist (this is the original broken ref) |

**Runner error signature to match:**

```text
Unable to resolve action `aquasecurity/setup-trivy@v0.2.2`, unable to find version `v0.2.2`
```

Where the surrounding workflow only contains:

```yaml
- uses: aquasecurity/trivy-action@v0.30.0
```

— no direct reference to `setup-trivy` anywhere.

**Tracking issue template (when you drop the step):**

```markdown
Title: Re-enable <step name> once <wrapper-owner>/<wrapper-action> ships a working transitive pin

Body:
- Workflow: `<path/to/workflow.yml>` step `<step name>`
- Removed in: PR #<num>
- Upstream wrapper: <owner>/<action>
- Broken transitive: <owner>/<transitive-action>@<ver>
- Upstream action.yml line: https://github.com/<owner>/<action>/blob/<ver>/action.yml#L<n>
- Runner error: `Unable to resolve action <transitive>@<ver>, unable to find version <ver>`
- Re-enable when: upstream releases a wrapper version that pins a valid transitive, OR transitive is republished at the pinned ref.
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectAgamemnon | PR #400 (security workflow Trivy step); tracking issues #411, #416 | 3 failed pin attempts on 2026-05-17/18 before dropping the step |
