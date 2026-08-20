---
name: gha-security-scanning-supply-chain
description: "Use when GitHub Actions needs CodeQL, Semgrep, Gitleaks, Bandit, zizmor, dependency scanning, immutable action pins, verified installers, or SARIF publication; when a scan is absent from pull requests, masked, falsely failing, or stuck before job start; or when a reviewed baseline must fail closed. Preserve least privilege, scan the same roots in local and CI gates, resolve tags to immutable SHAs, parse structured output structurally, and distinguish verified procedures from proposed baseline and composite-Action extensions."
category: ci-cd
date: 2026-08-07
version: "2.0.0"
user-invocable: false
license: BSD-3-Clause
history: gha-security-scanning-supply-chain.history
verification: verified-local
tags: [github-actions, codeql, semgrep, gitleaks, bandit, zizmor, sarif, sast, supply-chain, sha-pinning, least-privilege, fail-closed]
---

# GitHub Actions Security Scanning and Supply-Chain Hardening

## Overview

Build security checks as ordinary, deterministic quality gates: run them on pull requests, give
write permissions only to the job that needs them, pin every action and downloaded tool, and parse
machine formats with a machine parser. This compact reference retains the reusable decisions and
copy-ready commands. Detailed case evidence is in
[the notes](./gha-security-scanning-supply-chain.notes.md); the exact superseded content is in
[history](./gha-security-scanning-supply-chain.history).

Verification remains `verified-local`. Established scanning, pinning, SARIF, and triage procedures
were exercised locally or in their cited cases. The fail-closed Bandit LOW-baseline design and the
extension of zizmor to composite Actions remain proposals and must not be represented as shipped.

## When to Use

- A repository needs CodeQL, Semgrep, Gitleaks, Bandit, dependency audit, or zizmor coverage.
- A scan runs only on `push`, is hidden by `continue-on-error`, or a summary gate always fails.
- `uses:` contains mutable tags, or an installer downloads executable bytes without verification.
- A job fails during “Set up job” because a transitive action reference cannot resolve.
- A scanner produced SARIF that must be uploaded to Code Scanning without granting broad workflow
  permissions or suppressing the scanner's failure.
- A CodeQL item shown by `gh pr checks` is a check-run ID, not a workflow-run ID.
- A reviewed finding-count baseline must detect increases, reductions, malformed JSON, duplicate
  keys, and updates without an issue or PR reference.
- Composite Actions were added under `.github/actions/`, but local/required/scheduled zizmor roots
  no longer agree.

## Verified Workflow

### Quick Reference

```bash
# Inventory mutable action references across workflows and composite Actions.
grep -rnE 'uses:.*@(v[0-9]|main|master)([^0-9a-f]|$)' .github/

# Required/local parity: offline and deterministic. Scheduled scans may use online audits.
uv run zizmor --no-online-audits --min-severity medium \
  .github/workflows/ .github/actions/
uv run zizmor --min-severity medium .github/workflows/ .github/actions/

# Parse SARIF structurally; zero results is success.
jq -e '[.runs[].results[]] | length == 0' results.sarif

# Inspect a CodeQL check-run and its annotations.
gh api 'repos/<owner>/<repo>/check-runs/<check-run-id>' \
  --jq '{name,conclusion,details_url,html_url}'
gh api 'repos/<owner>/<repo>/check-runs/<check-run-id>/annotations' --paginate
gh api 'repos/<owner>/<repo>/code-scanning/alerts?pr=<pr>&tool_name=CodeQL' --paginate

# Produce LOW findings without letting Bandit's own exit status skip policy comparison.
uv run bandit -c pyproject.toml -r <targets> \
  --severity-level low --exit-zero -f json -o build/bandit_low.json
uv run python <baseline-checker>.py build/bandit_low.json <baseline>.json
```

### 1. Establish trigger and permission boundaries

Every pre-merge gate needs `pull_request` as well as any `push` or `schedule` trigger. Do not put
`security-events: write` at workflow scope. Give ordinary scanners `contents: read`; grant the write
permission only to a SARIF-upload job. Keep untrusted fork behavior explicit: uploads may be skipped
when GitHub withholds the permission, but the scan and its enforcement must still run.

```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  upload-sarif:
    permissions:
      contents: read
      security-events: write
```

Do not use `continue-on-error: true` on an enforcing scan. If an upload must happen even when the
scanner finds an issue, separate production from enforcement: capture the scanner status, upload
with `if: always()`, then fail the job from the captured status.

### 2. Pin every trust boundary

Pin third-party actions to a full commit SHA and retain the release tag as a review comment. Resolve
both lightweight and annotated tags:

```bash
ref=$(gh api repos/<owner>/<action>/git/ref/tags/<tag>)
type=$(jq -r '.object.type' <<<"$ref")
sha=$(jq -r '.object.sha' <<<"$ref")
if [ "$type" = tag ]; then
  sha=$(gh api repos/<owner>/<action>/git/tags/"$sha" --jq '.object.sha')
fi
printf '%s\n' "$sha"
```

For downloaded executables, pin the version and expected digest, use a fail-fast transfer, verify
before extraction or execution, and select the digest by operating system and architecture. Prefer
the publisher's signed checksum metadata where available. A package-manager install is acceptable
only when its lock/integrity metadata is part of the reviewed trust chain.

```bash
curl -fsSLo tool.tar.gz "https://example.invalid/tool-${VERSION}-${TARGET}.tar.gz"
printf '%s  %s\n' "$EXPECTED_SHA256" tool.tar.gz | sha256sum -c -
tar -xzf tool.tar.gz
```

When “Set up job” reports an unresolved action you do not reference, search the called action's
metadata at the pinned commit. The missing reference is commonly in `action.yml` or an embedded
composite step. Upgrade or replace the parent action; adding a direct dependency to your workflow
does not repair its transitive metadata.

### 3. Enforce scanners by their structured contracts

- CodeQL: use the language matrix appropriate to the repository and keep generated/vendor paths
  excluded. Triage via check-run and Code Scanning APIs, then add a focused regression test for a
  real code fix.
- Gitleaks/Semgrep/Trivy: publish SARIF when useful, but use `jq -e` against the JSON/SARIF schema
  for pass/fail. POSIX `grep` does not implement `\s` and cannot safely interpret nested JSON.
- Bandit: enforce the agreed severity/confidence gate. `# nosec` needs a narrow rule ID and a reason.
  Weak hashes require `usedforsecurity=False` only when the use is genuinely non-security-related.
- Dependency audit: run the ecosystem-native command (`npm audit`, `pip-audit`, lockfile audit) and
  enable Dependabot/Renovate for ongoing updates. For pixi, put PyPI-only tools under
  `pypi-dependencies`, not conda dependencies.
- zizmor: derive roots from both `.github/workflows/` and tracked `.github/actions/**/action.yml`.
  Required CI and pre-commit must use identical offline arguments; scheduled runs may add online
  audits. Tests should inventory tracked Actions rather than pinning a hand-maintained list.

For Gitleaks, fetch full history (`fetch-depth: 0`) and retain default git-history scanning; `--no-git`
or a single-commit range misses earlier branch commits. When repository policy makes main advisory
and pull requests enforcing, set exit behavior by event rather than weakening all runs. For npm
production risk, the cited gate used `npm audit --omit=dev --audit-level=high`; choose scope
explicitly instead of letting dev-only transitive findings redefine the production gate.

When Bandit is invoked through a pixi task that already embeds targets, do not append arguments that
duplicate the target. Use a bare task or call `python -m bandit` with the complete argv. Upload JSON
with `if: always() && hashFiles('<report>') != ''` so a finding does not suppress its own evidence.

### 4. Maintain a fail-closed reviewed baseline

This subsection is proposed, not verified. A baseline checker should deserialize with duplicate-key
rejection, validate the schema and nonnegative integer counts, and compare exact rule IDs. An
increase is a regression; a reduction means the baseline is stale; a missing or malformed report is
an error, never “zero findings.” Updating the baseline is a distinct command that requires a
reviewable issue/PR reference, writes atomically, and re-runs comparison afterward.

The report-generation command must use `--exit-zero` only to ensure the checker always receives the
complete JSON. The checker, not Bandit's ordinary finding exit, becomes the policy gate.

### 5. Verify the complete gate

1. Parse workflow YAML and inspect effective triggers and permissions.
2. Search all `.github/` action references; assert full-SHA pins.
3. Run each scanner with the exact required-CI command.
4. Inject or use a fixture finding to prove the job fails; use an empty fixture to prove it passes.
5. For SARIF, prove upload executes after both clean and finding-producing scans.
6. Compare local, pre-commit, required-CI, and scheduled scan roots and arguments.
7. Confirm the required-check name is stable before changing branch protection.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Mask the scanner | `continue-on-error: true` on the enforcing step | Findings become green CI | Separate artifact upload from final enforcement |
| Parse SARIF as text | `grep` for an empty `results` array or for summary glyphs | `\s` is not portable and nested JSON defeats line matching | Use `jq -e` on the schema |
| Pin only direct actions | Updated workflow `uses:` entries | A transitive action still failed during setup | Inspect the pinned action's metadata and upgrade the parent |
| Trust a mutable release | Used `@v4`, latest URLs, or `curl | bash` | The reviewed bytes can change without a diff | Pin immutable SHA/digest before execution |
| Treat missing baseline input as clean | Parser returned an empty result on invalid JSON | Broken evidence silently passed | Validate strictly and fail closed |
| Scan workflows only | zizmor ignored `.github/actions/` | Composite Actions escaped pin and permission audits | Inventory all tracked action roots and keep command parity |

## Results & Parameters

| Parameter | Recommended value or invariant |
| --- | --- |
| Action reference | Full 40-character commit SHA, tag retained as comment |
| Required zizmor mode | `--no-online-audits --min-severity medium` |
| Scan roots | `.github/workflows/` and `.github/actions/` when present |
| SARIF clean predicate | `jq -e '[.runs[].results[]] | length == 0'` |
| Upload permission | Job-local `security-events: write` |
| Installer | Pinned version + platform-specific SHA-256, verified before execution |
| Bandit baseline | Exact reviewed rule counts; increase, decrease, missing, or malformed = fail |
| Baseline update | Explicit reference, atomic write, immediate re-check |

## Verified On

- 2026-08-07: established workflows and local command contracts (`verified-local`).
- Proposed Bandit LOW-baseline and composite-Action extensions remain unverified.
- Source cases and their individual evidence boundaries are indexed in
  [the notes](./gha-security-scanning-supply-chain.notes.md).

## Companions

- [Case notes](./gha-security-scanning-supply-chain.notes.md)
- [Version history and exact superseded snapshot](./gha-security-scanning-supply-chain.history)
