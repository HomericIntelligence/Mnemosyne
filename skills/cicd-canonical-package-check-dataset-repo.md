---
name: cicd-canonical-package-check-dataset-repo
description: "How to fill a canonical `package` CI check-run for a GitOps/manifest dataset repo (no sdist/wheel/container): build the dataset itself as a reproducible tar.gz + SHA256SUMS, round-trip-verify it, and upload as artifact. Use when: (1) an ecosystem CI-status board tracks canonical check-run names (build/test/lint/security/package/...) and a manifest-only repo shows a `package` gap, (2) you must choose between adding a real package job vs documenting N/A — check whether the board is GENERATED from live check-runs (then N/A has no marker mechanism and only a real job fills the cell), (3) you need a deterministic/reproducible tar of dataset dirs (--sort=name --owner=0 --group=0 --numeric-owner --mtime pinned), (4) a repo has forbid-suppression guards (no `|| true`, no `continue-on-error: true`, no `::warning::`) and the new job must pass them, (5) you must verify a CI job's run blocks locally before pushing (byte-identical simulation), including when the actionlint system binary is absent locally or a safety net blocks `rm -rf` on mktemp dirs, (6) registering the new job as a required branch-protection context post-merge with an idempotent jq snippet."
category: ci-cd
date: 2026-07-03
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - canonical-check-run
  - ecosystem-ci-board
  - package-job
  - dataset-repo
  - manifest-repo
  - reproducible-tar
  - sha256sums
  - round-trip-verify
  - upload-artifact
  - branch-protection
  - required-status-checks
  - actionlint
  - forbid-suppressions
  - doc-sync
---

# CI/CD: Canonical `package` Check for a Dataset/Manifest Repo

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-03 |
| **Objective** | Fill the missing canonical `package` check-run cell on an ecosystem CI-status board for Myrmidons, a GitOps dataset repo (agent YAML manifests) with no sdist/wheel/container to build |
| **Outcome** | Success — `package` job added to `_required.yml` (`needs: build`, reproducible tar + SHA256SUMS + round-trip verify + SHA-pinned upload-artifact); docs synced in 3 homes; all local gates green |
| **Verification** | verified-local — pre-commit --all-files green (actionlint run via downloaded pinned binary), byte-identical local simulation of both run blocks passed (54 YAMLs round-tripped, checksum OK); CI on PR #755 pending at capture time |

## When to Use

- An ecosystem CI-status board (e.g. Odysseus) tracks canonical check-run names per repo and a manifest/dataset repo shows a gap for `package` (or another category that "doesn't obviously apply").
- The issue offers "add the job OR document N/A" — decide by checking how the board is produced: if it is **generated from live check-runs on `main`**, there is no N/A marker mechanism, so only a real check-run fills the cell.
- You need a **reproducible release archive** of data directories as the repo's distributable.
- The repo enforces **forbid-suppression guards** (`|| true`, `continue-on-error: true`, `::warning::` all blocked) and any new job must be fail-fast to pass them.
- You want to **verify the job's run blocks locally** before pushing, in an environment where the actionlint system binary is missing or a safety net blocks `rm -rf` outside cwd.

## Verified Workflow

### Quick Reference

```yaml
# .github/workflows/_required.yml — job runs on both pull_request and push to main
package:
  name: package            # check-run name must EXACTLY match the canonical name
  runs-on: ubuntu-latest
  timeout-minutes: 10
  needs: build             # only package a schema-valid dataset (build = schema gate)
  steps:
    - uses: actions/checkout@<pinned-sha>  # match the repo's existing pin
    - name: Build dataset release archive
      run: |
        set -euo pipefail
        mkdir -p dist
        sha="$(git rev-parse --short HEAD)"
        tar --sort=name --owner=0 --group=0 --numeric-owner \
          --mtime='UTC 2020-01-01' \
          -czf "dist/<repo>-dataset-${sha}.tar.gz" agents/ fleets/ schemas/
        (cd dist && sha256sum -- *.tar.gz > SHA256SUMS)
    - name: Verify archive integrity (round-trip)
      run: |
        set -euo pipefail
        workdir="$(mktemp -d)"
        tar -xzf dist/<repo>-dataset-*.tar.gz -C "${workdir}"
        for dir in agents fleets schemas; do diff -r "${dir}" "${workdir}/${dir}"; done
        yaml_count="$(find "${workdir}/agents" -name '*.yaml' | wc -l)"
        [ "${yaml_count}" -gt 0 ] || { echo '::error::archive contains no agent YAMLs'; exit 1; }
        (cd dist && sha256sum --check SHA256SUMS)
    - name: Upload dataset artifact
      uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a  # v7.0.1
      with:
        name: <repo>-dataset
        path: dist/
        if-no-files-found: error
        retention-days: 14
```

```bash
# Post-merge (admin): register as required context — idempotent
gh api repos/<owner>/<repo>/branches/main/protection/required_status_checks \
  | jq '.contexts += ["package"] | .contexts |= unique' \
  | gh api --method PATCH \
    repos/<owner>/<repo>/branches/main/protection/required_status_checks --input -
```

### Detailed Steps

1. **Decide option 1 (real job) vs option 2 (document N/A) from ground truth, not the issue's framing.** Fetch the actual naming-convention doc: if it defines `package` as "sdist/wheel, container image, **or release archive**", a dataset repo has a genuine distributable — the dataset archive its consumers read. If the status board is generated from live check-runs (a `gen-*-table.sh` script + shields.io `nameFilter=` badges), an N/A note in a README cannot mark the cell — only a real check-run can. A tar + checksum + round-trip-verify + artifact upload is a real artifact build, not a fabricated pass (naming docs typically say "do not fabricate a passing job").
2. **Put the job in the workflow that already triggers on both `pull_request` and `push: branches: [main]`** — the board reads check-runs on `main`, and PRs need the gate too. Emit the canonical name via `name: package` (GitHub's required-check string is the job's `name:` field, not its YAML key).
3. **Gate on the schema/build job** (`needs: build`) so only a validated dataset is packaged.
4. **Make the tar reproducible**: `--sort=name --owner=0 --group=0 --numeric-owner --mtime='UTC 2020-01-01'` (GNU tar). Name it with `git rev-parse --short HEAD`. Write `SHA256SUMS` beside it.
5. **Verify the artifact in the same job**: extract to `mktemp -d`, `diff -r` every packaged dir against the source tree, guard against an empty archive with a file-count check, then `sha256sum --check SHA256SUMS`. Every step `set -euo pipefail`; use `::error::` (permitted) never `::warning::`/`|| true`/`continue-on-error` (blocked by forbid-suppression guards).
6. **SHA-pin the upload action** to match the repo's pinned-action convention; `if-no-files-found: error` so a silent empty upload fails.
7. **Sync the contract in ALL documented homes** (doc-drift discipline): branch-protection required-checks table, the full-restore `contexts` JSON list, an incremental-add jq snippet, and the CI job list in CLAUDE.md/README. Give any one-time migration snippet a **lead-in sentence** ("To register the new `package` check post-merge (one-time migration):") — a near-verbatim duplicate snippet floating without a lead-in draws a PR-review comment (this happened; PR #755 review).
8. **Verify locally before pushing** with a byte-identical simulation of the job's run blocks (same tar flags, same diff/checksum sequence). Run the full pre-commit suite; see Failed Attempts for the actionlint-binary and safety-net workarounds.
9. **Post-merge admin step**: register the new required context with the idempotent `jq '.contexts += [...] | .contexts |= unique'` PATCH, then confirm the check-run exists on `main` so the board picks it up.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Run repo's `actionlint-system` pre-commit hook locally | `pixi run --environment lint pre-commit run --all-files` | Hook requires a system-installed actionlint binary (repo policy for Go <1.16 compat); binary absent in the sandbox → hook fails with "Executable `actionlint` not found" while every other hook passes | Download the pinned release binary (`v1.7.7` linux_amd64 tarball from rhysd/actionlint releases) to /tmp and run it directly on the workflow file; treat the hook failure as an environment limitation, not a lint finding — but say so explicitly in the report |
| Clean up local simulation with `rm -rf dist "${workdir}"` (mktemp dir) | Copy-pasting the CI verify block verbatim including cleanup | CC Safety Net blocks `rm -rf` on paths outside cwd (mktemp under /tmp), and also blocks `find <dir> -delete` | Scope ALL scratch dirs inside the cwd (e.g. `.package-sim/`) when simulating CI steps locally, and clean up with explicit `rm <files>` + `rm -r <known-subdirs>` + `rmdir` — the CI job itself can keep `mktemp -d` since runners are ephemeral |
| Duplicate the generic incremental-add snippet with only the context name changed | Added a second near-verbatim `gh api ... jq '.contexts += ["package"]'` block right after the generic example, with no lead-in text | PR reviewer flagged it: near-verbatim duplicate floating without a lead-in sentence reads as accidental duplication | One-time migration commands need a one-line lead-in stating their purpose ("To register the new X check post-merge (one-time migration):"); alternatively fold the new context into the existing example's array |

## Results & Parameters

- Reproducible tar flags (GNU tar): `--sort=name --owner=0 --group=0 --numeric-owner --mtime='UTC 2020-01-01'`
- Upload action pin: `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` (= v7.0.1 tag commit, verified against upstream)
- actionlint pinned binary: `https://github.com/rhysd/actionlint/releases/download/v1.7.7/actionlint_1.7.7_linux_amd64.tar.gz`
- Local simulation output: `myrmidons-dataset-<sha>.tar.gz: OK` / `OK: archive round-trips (54 agent YAMLs packaged)`
- Local gates: pre-commit --all-files all green except env-missing actionlint (run directly instead: clean); `pixi run test-doc-drift`: 7 files, 0 errors
- Board badge check (post-merge): `curl -sI "https://img.shields.io/github/check-runs/<owner>/<repo>/main?nameFilter=package&label=package"`

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Myrmidons | Issue #749 / PR #755 — canonical `package` check for the Odysseus Ecosystem CI Status board | verified-local; CI pending at capture time |
