---
name: ci-cd-canonical-release-check-manifest-repo
description: "How to plan the canonical `release` CI check (Odysseus ecosystem CI-naming board) for a GitOps/manifest/dataset repo where a release step looks N/A — the board is GENERATED from live check-runs on main (scripts/gen-ecosystem-table.sh), so documenting 'N/A' in the repo can never fill the board cell; the only real options are (a) a genuine release job emitting check-run name `release` on main or (b) leaving the issue-linked gap. For a dataset repo the honest release artifact is a versioned dataset snapshot (tar of the manifest dirs + RELEASE_INFO manifest with commit SHA/date/counts) uploaded as a workflow artifact on every main push and published via `gh release create` on v* tags — the convention explicitly sanctions 'a release-tag-gated job that still emits release on main' and forbids fabricating a passing no-op. Use when: (1) an ecosystem CI-naming issue asks to add a canonical check (release/package/install) to a repo where the category seems inapplicable, (2) you are choosing between 'add real job' vs 'document N/A' for a generated status board, (3) you plan a release job in a repo with strict no-silent-failure guards (forbid-continue-on-error, forbid-or-true, forbid-advisory-warnings) and pinned-SHA action policy, (4) the job needs `gh release create` with GITHUB_TOKEN and you have not verified org settings allow workflow-created releases, (5) you pin a third-party action SHA from memory instead of the release page, (6) versioning on shallow checkouts — git describe sees no tags, so tag names must come from GITHUB_REF_NAME."
category: ci-cd
date: 2026-07-03
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - ci-naming-convention
  - canonical-check-run
  - ecosystem-status-board
  - release-check
  - manifest-repo
  - dataset-repo
  - gitops
  - myrmidons
  - odysseus
  - publish-artifacts
  - gh-release-create
  - github-token-permissions
  - pinned-action-sha
  - upload-artifact
  - shallow-checkout-tags
  - no-silent-failures
  - planning-methodology
  - unverified-assumptions
---

# Canonical `release` CI Check for a Manifest/Dataset Repo

> ⚠️ **UNVERIFIED — PLAN ONLY.** This skill captures a *planning* pattern produced for
> Myrmidons issue #751 (add canonical `release` check for the Odysseus ecosystem CI board).
> No workflow was committed, no CI run executed, no release published. Tool-behavior and
> API-permission claims below are assumptions to re-verify at implementation time.

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-03 |
| **Objective** | Plan the canonical `release` CI check for Myrmidons (GitOps agent-dataset repo) per the Odysseus ecosystem CI-naming convention |
| **Outcome** | Plan produced (real dataset-snapshot release job, not an N/A doc) — NOT implemented; no workflow committed, no CI run |
| **Verification** | unverified |
| **History** | initial version |

## When to Use

- An ecosystem CI-naming issue asks a repo to emit a canonical check (`release`, `package`, `install`) that seems N/A for the repo type (manifest/dataset/docs repo).
- You must choose between "add a real job" and "document N/A" for a status board that is **generated from live check-runs** — prose in the target repo cannot fill a generated cell.
- The repo enforces no-silent-failure guards (`forbid-continue-on-error`, `forbid-or-true`, `forbid-advisory-warnings`) and pinned-SHA actions, constraining how the new workflow may be written.
- The release job must call `gh release create` with `GITHUB_TOKEN` and you have not confirmed org/repo settings permit it.
- You need a version string on a shallow checkout (`fetch-depth: 1` has no tags — `git describe` fails; use `GITHUB_REF_NAME` on tag events).

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

```bash
# Read the convention doc read-only before deciding N/A vs real job:
gh api repos/<org>/Odysseus/contents/docs/ci-naming-convention.md --jq .content | base64 -d

# Decision rule: board generated from live check-runs => documenting N/A never fills the cell.
# Real-but-honest release job for a dataset repo:
#   package: tar dataset dirs + RELEASE_INFO(commit, %cI date, counts) -> dist/
#   every main push: upload-artifact; v* tag: gh release create
# Version on shallow checkout: tag events use $GITHUB_REF_NAME, else snapshot-$(git rev-parse --short HEAD)

# Post-merge proof (the ONLY command that proves the board criterion):
gh api repos/<org>/<repo>/commits/main/check-runs --jq '.check_runs[].name' | grep -x release
```

### Detailed Steps

1. **Fetch the naming convention doc read-only first.** It defines the canonical check-run name, sanctions "a release-tag-gated job that still emits `release` on `main`", and forbids fabricating a passing no-op job. It also reveals the board is generated from live check-runs — which kills the "document N/A" option for filling the cell.
2. **Find the repo's honest release artifact.** For a dataset/manifest repo: a versioned snapshot archive of the canonical dirs plus a RELEASE_INFO manifest (commit SHA, `git log -1 --format=%cI` commit date so re-runs are deterministic, file counts). Consumers that reconcile against the dataset can pin it.
3. **Put packaging logic in a script under the repo's validator dir, not inline YAML** — gets existing shellcheck coverage and CI↔local parity (`just package` and CI call the same script). Guard against packaging an empty tree (refuse when counts are 0).
4. **Job emits the canonical name exactly** (`jobs.release.name: release`); triggers on PR (dry-run), main push (board signal + artifact upload), and `v*` tags (publish step gated by `if: startsWith(github.ref, 'refs/tags/v')`).
5. **Respect the repo's guard suite**: no `continue-on-error`, no `|| true`, no `::warning::`; `set -euo pipefail`; checkout pinned to the same SHA every other workflow uses; rely on the existing actionlint/yamllint/workflow-schema gates rather than adding new lint wiring.
6. **Label verification by what it proves**: local packaging + pre-commit prove lint/packaging only; the board criterion is proved ONLY post-merge by querying check-runs on main (`gh api .../commits/main/check-runs`), and the shields `nameFilter` badge resolving.
7. **Keep required-checks unchanged and document why** — publishing is post-merge; record the deliberate omission in the branch-protection doc so it is not mistaken for drift.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Document `release` as N/A | Issue option 2: write "N/A for a manifest repo" in the repo docs | The board is generated from live check-runs on main; no prose in the target repo can fill a generated cell — the gap would persist as an issue-linked hole | For generated status boards, only an emitted check-run changes the cell; docs-only "N/A" is a non-fix |
| Hollow green `release` job | A no-op job that just exits 0 to satisfy the name filter | Convention explicitly forbids fabricating a passing job ("Do not fabricate a passing job") | Attach the canonical name to real work — for a dataset repo, package+verify+upload the snapshot every run |
| `git describe` for versioning in CI | Derive the version from tags inside the job | Default `actions/checkout` is shallow with no tags; `git describe --tags` fails or lies | On tag events take the version from `GITHUB_REF_NAME`; otherwise `snapshot-<shortsha>` |
| Pin action SHA from memory | Wrote `actions/upload-artifact@ea165f8d…  # v4.6.2` from recall | SHA↔tag mapping was never checked against the release page — a wrong pin either breaks the job or silently pins a different version | Always re-verify third-party action SHAs against the tag on github.com before committing; let Renovate track them afterward |
| Assume `gh release create` just works with `GITHUB_TOKEN` | Publish step uses `GH_TOKEN: ${{ github.token }}` + job `contents: write` | Org/repo Actions settings can restrict the default token (read-only default, or release creation blocked); never executed | Verify Actions token permissions policy before relying on workflow-created releases; the first tag push is the real test |
| `contents: write` on a job that also runs on pull_request | One job-level permission block for all three triggers | Grants a write-scoped token to PR-triggered runs that only need read (forks get read regardless, but same-repo PRs would carry write) — broader than needed | Scope write to the publish path: either split the publish into a tag-only job, or accept and document the trade-off explicitly |

## Results & Parameters

- Plan target: Myrmidons `.github/workflows/release.yml` + `scripts/package-dataset.sh` + `just package` recipe + README badge + CLAUDE.md CI/CD bullet + branch-protection design note.
- Dataset measured at planning time: 51 agent YAMLs (excluding `_templates/`), 6 fleet YAMLs.
- Canonical check-run name: `release` (job key AND `name:` field).
- Badge: `https://img.shields.io/github/check-runs/<org>/<repo>/main?nameFilter=release&label=release`.

### Unverified assumptions a reviewer MUST check (verbatim)

- `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` really is v4.6.2 (recalled from memory, never checked against the release page).
- Repo/org Actions settings allow `gh release create` with the default `GITHUB_TOKEN` under job-level `permissions: contents: write` (never executed; only proven by the first `v*` tag push).
- The shields per-check-run endpoint (`nameFilter=release`) resolves once the check-run exists on main (taken from the convention doc, not exercised).
- GNU tar accepts `-C dist RELEASE_INFO` mid-argument-list as planned (standard on ubuntu runners, not re-tested).
- Emitting a `release` check-run on pull_request events does not confuse the board (board reads main check-runs only, per the convention doc's badge mechanism).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Myrmidons | Issue #751 planning session (2026-07-03) — plan only, not implemented | Odysseus ecosystem CI-naming rollout |
