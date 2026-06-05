# readme-badges-live-sources-verification — Session Notes

## Issue #779 Implementation Context

**PR**: Added CI/PyPI/Python/license badge row to ProjectHephaestus README.md

**Key Discovery**: The broader principle underlying issue #779 is **semantic anchors** (live data sources vs. hardcoded values) — the same principle documented in issue #749 platform asymmetry docs.

## Session Learnings

### 1. Badge URLs Must Point to Live Sources

**Principle**: Badges are documentation assertions about current project state. They MUST query live data, not encode static values.

**Shields.io endpoints**:
- PyPI version: `https://img.shields.io/pypi/v/<package-name>` — queries latest release via PyPI JSON API
- GitHub topics: `https://img.shields.io/badge/<label>-<value>-<color>` — can reflect GitHub metadata
- Custom endpoints: shields.io supports nearly any metric queryable via REST

**GitHub Actions badges**:
- Format: `https://github.com/<org>/<repo>/actions/workflows/<workflow>.yml/badge.svg?branch=<branch>`
- Always points to live workflow status
- Branch pinning (`?branch=main`) ensures main-branch state

**Invalid patterns** (DO NOT USE):
- Hardcoded version numbers: `https://img.shields.io/badge/version-1.0.0-blue`
- Static text: `https://img.shields.io/badge/ci-passing-brightgreen`
- These go stale immediately and require manual updates

### 2. PyPI Package Names Must Be Verified

**Discovery**: Package normalization is real. The PyPI JSON API resolves package names but returns the canonical form.

**Example**:
- Assumption: `Hephaestus-HomericIntelligence`
- Actual on PyPI: `HomericIntelligence-Hephaestus`
- Result: Badge URL with wrong name = 404

**Verification workflow**:
```bash
curl -s https://pypi.org/pypi/HomericIntelligence-Hephaestus/json | jq '.info.name'
```

This returns the normalized package name and confirms the package exists before committing.

### 3. Pre-Commit Markdown Validation is Comprehensive

**Hooks that validate badges**:
- **MD041**: First line is top-level heading (`# Title`)
- **MD013**: Line length limits (shields.io badges are very long URLs — table format helps)
- **MD034**: Bare URLs (all URLs must be in markdown link syntax `[text](url)`)
- **Trailing whitespace**: No spaces at end of lines
- **End-of-file newlines**: All files must end with exactly one newline

**Command**:
```bash
pixi run pre-commit run --files README.md
```

This validates all quality gates automatically. **Do not skip pre-commit with `--no-verify`.**

### 4. Documentation Changes Still Require Full PR Policy Compliance

**Common misconception**: "It's just a README edit, does it really need GPG signatures?"

**Answer**: YES. Project policies enforce:
1. **Signed commits**: `git commit -S` (GPG-signed)
2. **PR body**: `Closes #<issue-number>` (literal string, capital C, no colon)
3. **Auto-merge**: `gh pr merge --auto --squash` (mandatory; rebase disabled)

These apply **even to documentation-only PRs** because:
- The `pr-policy` CI gate is enforced on all PRs
- It validates commit signatures via `gh api repos/<org>/<repo>/commits/<sha>` (which checks GitHub's verification status, not local `git log --show-signature`)
- Architecture is audited for commit policy compliance regardless of change type

**GPG signature verification subtlety**:
- `git log --show-signature -1` shows local signature status (can lie about verification)
- `gh api repos/<org>/<repo>/commits/<sha> --jq '.commit.verification'` shows GitHub's verification (the truth)
- If committer email doesn't match GPG key email, GitHub will show `"verified": false` even if local signature is valid

### 5. Semantic Anchors Principle (Issue #749 Connection)

**Related learning**: Issue #749 established that documentation should use semantic anchors (live data) rather than hardcoded values.

**Examples**:
- ✅ Badge querying shields.io (live PyPI query)
- ✅ Documentation referencing git tags (resolved at read time)
- ❌ README documenting "Version 1.0.0" (hardcoded, goes stale)
- ❌ Badge with hardcoded status text

This skill implements the semantic-anchor principle for badges specifically.

## Code Snippets from Implementation

### PyPI Verification (curl command)

```bash
#!/bin/bash
set -euo pipefail

PACKAGE_NAME="HomericIntelligence-Hephaestus"

# Verify package exists and extract metadata
response=$(curl -s "https://pypi.org/pypi/${PACKAGE_NAME}/json")

if echo "$response" | jq empty 2>/dev/null; then
  name=$(echo "$response" | jq -r '.info.name')
  version=$(echo "$response" | jq -r '.info.version')
  echo "✓ Package found: ${name} (v${version})"
else
  echo "✗ Package not found or JSON error"
  exit 1
fi
```

### Badge Row Markdown

```markdown
| CI | Python | PyPI | License |
|----|--------|------|---------|
| [![CI](https://github.com/HomericIntelligence/ProjectHephaestus/actions/workflows/comprehensive-tests.yml/badge.svg?branch=main)](https://github.com/HomericIntelligence/ProjectHephaestus/actions/workflows/comprehensive-tests.yml) | [![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/) | [![PyPI](https://img.shields.io/pypi/v/HomericIntelligence-Hephaestus)](https://pypi.org/project/HomericIntelligence-Hephaestus/) | [![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE) |
```

This table format:
- Keeps long URLs readable (table cells support longer content than bare markdown)
- Organizes related badges logically
- Pre-commit markdown linting handles table syntax validation

## Related Skills & Issues

- **Issue #779**: Add badge row to README (this skill's origin)
- **Issue #749**: Platform asymmetry documentation — established semantic-anchor principle
- **Skill: add-ci-badge-to-readme**: Specific workflow for adding a single CI badge (complementary)
- **Skill: badge-count-drift-prevention**: Automate count badge validation (different use case)

## Cross-Project Application

This skill applies to all HomericIntelligence projects that publish to PyPI and use GitHub Actions. Standard badge row:

```markdown
| CI | Python | PyPI | License |
|----|--------|------|---------|
| [![CI](https://github.com/HomericIntelligence/<REPO>/actions/workflows/comprehensive-tests.yml/badge.svg?branch=main)](https://github.com/HomericIntelligence/<REPO>/actions/workflows/comprehensive-tests.yml) | [![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/) | [![PyPI](https://img.shields.io/pypi/v/HomericIntelligence-<Package>)](https://pypi.org/project/HomericIntelligence-<Package>/) | [![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE) |
```

Replace `<REPO>` and `<Package>` appropriately and verify PyPI package names match.
