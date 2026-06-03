# Notes: CI/CD Workflow Deduplication

## Session Context

ProjectTelemachy issue #151: Duplicate lint, test, secrets-scan jobs in `.github/workflows/ci.yml` and `.github/workflows/_required.yml`.

## Analysis

Enumerated jobs in both files:
- `ci.yml` jobs: lint-and-test, secrets-scan
- `_required.yml` jobs: lint, unit-tests, security-secrets-scan, forbid-suppressions, markdownlint, pixi-check, justfile-check, symlink-check, integration-tests, security-dependency-scan, build, schema-validation, deps-version-sync

Every job in ci.yml has a counterpart in _required.yml. The superset includes 9 additional gates not in the inferior workflow.

## Decision Logic

Considered three approaches:
1. **Delete ci.yml** (chosen) — simplest, removes version drift
2. **Extract to reusable workflow** — rejected; adds indirection for one consumer
3. **Keep both with documentation** — rejected; maintains version-drift risk

Chose deletion because:
- Strict containment relationship (no features unique to ci.yml except coverage reporting)
- Single consumer (no other workflows call ci.yml)
- Reusable workflows are worthwhile with 2+ consumers; premature here

## Implementation

1. git rm .github/workflows/ci.yml
2. Added `--cov=telemachy --cov-report=term-missing` to unit-tests pytest command in _required.yml
3. Validated YAML syntax
4. Committed and pushed
5. PR #257 created with auto-merge enabled

## Verification

- ✓ No duplicate jobs (enumerated via YAML parse)
- ✓ YAML syntax valid (yamllint + python parser)
- ✓ Coverage signal preserved (grep for --cov flag)
- ✓ No stale references to deleted workflow
- ✓ PR #257 merged with verified-ci status

## Related Issues

- #92 (Epic: audit remediation) — CI/CD deduplication is Wave 5
- #214, #150, #213, #183, #181 — Bundled in same audit phase but left as separate PRs
