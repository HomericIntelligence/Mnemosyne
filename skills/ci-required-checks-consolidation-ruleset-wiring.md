---
name: ci-required-checks-consolidation-ruleset-wiring
description: "Use when: (1) consolidating 5+ separate GitHub Actions workflow files into a single _required.yml that maps 1:1 to org-wide branch ruleset required checks, (2) wiring GitHub branch ruleset required_status_checks to specific job names, (3) a PR is blocked because required checks no longer exist after workflow restructuring, (4) classifying CI jobs into canonical job taxonomy (lint/unit-tests/integration-tests/build/benchmarks/coverage/schema-validation/deps-version-sync/security-dependency-scan/security-secrets-scan)."
category: ci-cd
date: 2026-04-25
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - github-actions
  - required-status-checks
  - branch-ruleset
  - workflow-consolidation
  - _required.yml
  - ci-cd
  - job-classification
---

# CI Required-Checks Consolidation and Ruleset Wiring

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-04-25 |
| **Objective** | Consolidate 5+ separate GitHub Actions workflow files into a single `_required.yml` whose job names map 1:1 to the org-wide branch ruleset required status checks |
| **Outcome** | Successfully consolidated; PR #451 on HomericIntelligence/ProjectKeystone unblocked |
| **Verification** | verified-local (CI run triggered, consolidation structure confirmed correct) |

## When to Use

- A repo has 5+ workflow files with overlapping concerns (ci.yml, security-scan.yml, codeql-analysis.yml, dependency-audit.yml, build-and-test.yml)
- A PR is blocked by the GitHub branch ruleset because required check contexts no longer match workflow job names
- You need to add or remove a required status check from the org-wide branch ruleset
- A new workflow restructuring leaves stale required-check contexts (e.g. old `typecheck` context after merging clang-tidy into lint)
- CI job naming is inconsistent and doesn't match the `"Required Checks / <job-name>"` context format

## Verified Workflow

### Quick Reference

```bash
# Identify existing workflow files to consolidate
ls .github/workflows/*.yml

# Verify current ruleset required checks
RULESET_ID=$(gh api repos/<owner>/<repo>/rulesets --jq '.[] | select(.name=="homeric-main-baseline") | .id')
gh api repos/<owner>/<repo>/rulesets/$RULESET_ID | jq '.rules[].parameters.required_status_checks'

# After creating _required.yml, update ruleset
gh api repos/<owner>/<repo>/rulesets/$RULESET_ID \
  --method PUT \
  --input - <<'EOF'
{ ... see Results & Parameters section ... }
EOF

# Files to delete after consolidation
git rm .github/workflows/ci.yml \
       .github/workflows/security-scan.yml \
       .github/workflows/codeql-analysis.yml \
       .github/workflows/dependency-audit.yml \
       .github/workflows/build-and-test.yml
```

### Detailed Steps

#### Step 1 — Create `_required.yml` with canonical job names

The workflow `name:` MUST be exactly `"Required Checks"`. The ruleset contexts take the form `"Required Checks / <job-id>"`.

```yaml
name: Required Checks

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: lint
    # clang-format, ruff, pre-commit, CMake cycle detection, cppcheck, clang-tidy, mypy
    ...

  unit-tests:
    name: unit-tests
    # C++ unit tests (ctest -L unit) + Python pytest
    ...

  integration-tests:
    name: integration-tests
    strategy:
      matrix:
        sanitizer: [asan, ubsan, tsan, lsan]
    # All sanitizer builds as a matrix + C++ integration/sample/example/application tests
    ...

  build:
    name: build
    # Release build artifact only (no tests)
    ...

  benchmarks:
    name: benchmarks
    needs: build
    # Release benchmarks
    ...

  coverage:
    name: coverage
    needs: build
    # Coverage build + Codecov upload
    ...

  schema-validation:
    name: schema-validation
    # Workflow YAML validation via check-jsonschema
    ...

  deps-version-sync:
    name: deps/version-sync
    # Cross-file version consistency checks
    ...

  security-dependency-scan:
    name: security/dependency-scan
    # pip-audit + Trivy FS scan + supply-chain dependency-review-action + Docker image scan (Trivy)
    ...

  security-secrets-scan:
    name: security/secrets-scan
    # gitleaks + Semgrep SAST + CodeQL (c-cpp + python) + secret findings gate
    ...
```

#### Step 2 — Classify every existing CI job into the canonical taxonomy

Use the classification table in Results & Parameters. Key rules:
- All 4 sanitizers (asan/ubsan/tsan/lsan) → **matrix** inside `integration-tests`
- `typecheck` (clang-tidy + mypy) → merges INTO `lint`
- cppcheck → merges INTO `lint`
- supply-chain-scanning → merges INTO `security/dependency-scan`
- Docker image scanning → `security/dependency-scan` (supply-chain, not a secret)
- CodeQL → `security/secrets-scan` (SAST analysis, not a dependency)

#### Step 3 — Update the GitHub branch ruleset

Retrieve the ruleset ID, then PUT the full updated ruleset. The `context` strings must exactly match `"Required Checks / <job-name>"` where `<job-name>` is the value of the job's `name:` field (not the YAML key).

```bash
RULESET_ID=$(gh api repos/<owner>/<repo>/rulesets --jq '.[] | select(.name=="homeric-main-baseline") | .id')
gh api repos/<owner>/<repo>/rulesets/$RULESET_ID \
  --method PUT \
  --input - <<'EOF'
{
  "name": "homeric-main-baseline",
  "target": "branch",
  "enforcement": "active",
  "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
  "rules": [{
    "type": "required_status_checks",
    "parameters": {
      "strict_required_status_checks_policy": false,
      "do_not_enforce_on_create": false,
      "required_status_checks": [
        {"context": "Required Checks / lint"},
        {"context": "Required Checks / unit-tests"},
        {"context": "Required Checks / integration-tests"},
        {"context": "Required Checks / build"},
        {"context": "Required Checks / benchmarks"},
        {"context": "Required Checks / coverage"},
        {"context": "Required Checks / schema-validation"},
        {"context": "Required Checks / deps/version-sync"},
        {"context": "Required Checks / security/dependency-scan"},
        {"context": "Required Checks / security/secrets-scan"}
      ]
    }
  }]
}
EOF
```

#### Step 4 — Delete absorbed workflow files

```bash
git rm .github/workflows/ci.yml \
       .github/workflows/security-scan.yml \
       .github/workflows/codeql-analysis.yml \
       .github/workflows/dependency-audit.yml \
       .github/workflows/build-and-test.yml
```

Keep standalone workflows:
- `_required.yml` (new consolidated file)
- `profiling-weekly.yml` (scheduled, heavy resource use)
- `release-please.yml` (tag/release triggered)

#### Step 5 — Validate YAML

```bash
for f in .github/workflows/*.yml; do
  python3 -c "import yaml; yaml.safe_load(open('$f'))" && echo "OK: $f" || echo "FAIL: $f"
done
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 22-job structure | Background agent created separate jobs for each sanitizer, separate typecheck, separate supply-chain-scanning, separate docker-image-scanning, separate sast-scanning | Too granular — didn't match the org ruleset's 10 canonical context strings; PRs stayed blocked | Always classify first against the canonical job taxonomy before generating the workflow |
| Stale `typecheck` context | After merging clang-tidy into lint, the ruleset still referenced `"Required Checks / typecheck"` | Old context string no longer had a matching job; PR status checks showed it as missing | After any job rename or merge, immediately update the ruleset via PUT to remove stale contexts |
| Job IDs with slashes in YAML keys | Used `security/dependency-scan:` as the YAML job key | GitHub Actions does not allow slashes in job IDs (YAML keys); workflow failed to parse | Use underscore-based job IDs (e.g. `security-dependency-scan:`) but set `name: security/dependency-scan` — the ruleset context matches the `name:` field, not the YAML key |
| Separate jobs for each sanitizer | Created asan-tests, ubsan-tests, tsan-tests, lsan-tests as 4 separate jobs | Requires 4 separate ruleset contexts; harder to manage; doesn't reflect that all sanitizers test the same code | Use a single `integration-tests` job with `strategy.matrix.sanitizer: [asan, ubsan, tsan, lsan]` |
| CodeQL in dependency-scan | Placed CodeQL analysis inside `security/dependency-scan` | CodeQL is SAST (static application security testing), not a dependency vulnerability scanner | CodeQL belongs in `security/secrets-scan` alongside gitleaks and Semgrep |

## Results & Parameters

### Canonical Job Classification Table

| Job name | What belongs in it |
|----------|-------------------|
| `lint` | clang-format, ruff, pre-commit, CMake cycle detection, cppcheck, clang-tidy, mypy — ALL static analysis |
| `unit-tests` | C++ unit tests (ctest -L unit) + Python pytest |
| `integration-tests` | C++ integration/sample/example/application tests + ALL sanitizer builds (asan/ubsan/tsan/lsan) as a matrix |
| `build` | Release build artifact only (no tests) |
| `benchmarks` | Release benchmarks (needs: build) |
| `coverage` | Coverage build + Codecov upload (needs: build) |
| `schema-validation` | Workflow YAML validation via check-jsonschema |
| `deps/version-sync` | Cross-file version consistency (CMakeLists.txt, conanfile.py, pyproject.toml, pixi.toml) |
| `security/dependency-scan` | pip-audit + Trivy FS scan + supply-chain dependency-review-action + Docker image scan (Trivy container) |
| `security/secrets-scan` | gitleaks + Semgrep SAST + CodeQL (c-cpp + python) + secret findings gate |

### Classification Decision Rules

| Tool / step | Goes into |
|------------|-----------|
| clang-format | `lint` |
| clang-tidy | `lint` |
| mypy | `lint` |
| cppcheck | `lint` |
| ruff | `lint` |
| pre-commit | `lint` |
| pytest | `unit-tests` |
| ctest -L unit | `unit-tests` |
| ctest -L integration | `integration-tests` |
| AddressSanitizer (asan) | `integration-tests` (matrix) |
| UndefinedBehaviorSanitizer (ubsan) | `integration-tests` (matrix) |
| ThreadSanitizer (tsan) | `integration-tests` (matrix) |
| LeakSanitizer (lsan) | `integration-tests` (matrix) |
| Release build | `build` |
| Codecov upload | `coverage` |
| Trivy filesystem scan | `security/dependency-scan` |
| Trivy container/image scan | `security/dependency-scan` |
| pip-audit | `security/dependency-scan` |
| dependency-review-action | `security/dependency-scan` |
| CodeQL | `security/secrets-scan` |
| gitleaks | `security/secrets-scan` |
| Semgrep | `security/secrets-scan` |

### Ruleset Context Format

```
"Required Checks / <job name field value>"
```

The YAML job `id` (key) and `name:` field can differ. The ruleset context matches the `name:` field.

```yaml
jobs:
  security-dependency-scan:   # ← YAML key (job id) — no slashes allowed
    name: security/dependency-scan  # ← this is what appears in the ruleset context
```

Ruleset context: `"Required Checks / security/dependency-scan"`

### Workflow Files: Keep vs Delete

| File | Action | Reason |
|------|--------|--------|
| `_required.yml` | Keep (create) | New consolidated required-checks workflow |
| `profiling-weekly.yml` | Keep | Scheduled/heavy, different concern |
| `release-please.yml` | Keep | Release triggered, different concern |
| `ci.yml` | Delete | Absorbed into `_required.yml` |
| `security-scan.yml` | Delete | Absorbed into `_required.yml` |
| `codeql-analysis.yml` | Delete | Absorbed into `_required.yml` |
| `dependency-audit.yml` | Delete | Absorbed into `_required.yml` |
| `build-and-test.yml` | Delete | Absorbed into `_required.yml` |

### Ruleset Update Command Template

```bash
# Look up ruleset ID
RULESET_ID=$(gh api repos/<owner>/<repo>/rulesets \
  --jq '.[] | select(.name=="homeric-main-baseline") | .id')

# Verify current state
gh api repos/<owner>/<repo>/rulesets/$RULESET_ID \
  | jq '.rules[].parameters.required_status_checks[].context'

# Full PUT to update required checks
gh api repos/<owner>/<repo>/rulesets/$RULESET_ID \
  --method PUT \
  --input - <<'EOF'
{
  "name": "homeric-main-baseline",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [{
    "type": "required_status_checks",
    "parameters": {
      "strict_required_status_checks_policy": false,
      "do_not_enforce_on_create": false,
      "required_status_checks": [
        {"context": "Required Checks / lint"},
        {"context": "Required Checks / unit-tests"},
        {"context": "Required Checks / integration-tests"},
        {"context": "Required Checks / build"},
        {"context": "Required Checks / benchmarks"},
        {"context": "Required Checks / coverage"},
        {"context": "Required Checks / schema-validation"},
        {"context": "Required Checks / deps/version-sync"},
        {"context": "Required Checks / security/dependency-scan"},
        {"context": "Required Checks / security/secrets-scan"}
      ]
    }
  }]
}
EOF
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectKeystone | PR #451 consolidation | 5 workflow files → single `_required.yml`; PR unblocked after ruleset update |
