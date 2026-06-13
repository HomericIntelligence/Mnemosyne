---
name: ci-matrix-yaml-multiformat-regex-fallback
description: "Regex fallback pattern for parsing CI matrix Python version lists that appear in either inline bracket format (python-version: [\"3.10\", \"3.11\"]) or multiline YAML sequence format. Use when: (1) extending a function that parses CI workflow YAML for Python version lists, (2) a regex-based parser only handles one of the two common GHA matrix formats, (3) reviewing a plan to add multiline sequence support alongside existing inline bracket support."
category: ci-cd
date: 2026-06-13
version: "1.1.0"
user-invocable: false
verification: unverified
history: ci-matrix-yaml-multiformat-regex-fallback.history
tags: [yaml, regex, python-version, ci-matrix, github-actions, multiformat]
---

# CI Matrix YAML Multiformat Regex Fallback

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Extend `extract_ci_matrix_python_versions` to handle both inline bracket and multiline YAML sequence formats |
| **Outcome** | Plan reviewed (R1); corrected regex and verified assumptions; not yet implemented |
| **Verification** | unverified |
| **History** | [changelog](./ci-matrix-yaml-multiformat-regex-fallback.history) |

GitHub Actions CI matrix workflows express `python-version` lists in two common formats:

**Inline bracket** (most common):
```yaml
python-version: ["3.10", "3.11", "3.12"]
```

**Multiline YAML sequence**:
```yaml
python-version:
  - "3.10"
  - "3.11"
  - "3.12"
```

A regex-based parser that only handles the inline bracket format silently returns no versions when encountering the sequence format, causing coverage checks to pass vacuously via an early-return in the internal consumer (`check_ci_matrix_coverage:200-202`). The fix is a two-regex fallback: try the bracket pattern first; if it yields no results, try the sequence pattern.

## When to Use

- Extending a function that parses CI YAML workflow files for Python version lists
- A `check_python_version_consistency` script reports no CI matrix versions but the workflow file exists
- Reviewing an implementation plan for adding multiline sequence support to `extract_ci_matrix_python_versions`
- Writing tests for a parser that must handle both YAML matrix formats

## Verified Workflow

> **Warning:** This workflow has **not** been validated end-to-end. The implementation is a proposed plan derived from code inspection only — no tests were run. Treat as a hypothesis until CI confirms.

### Quick Reference

```python
import re

# Inline bracket format: python-version: ["3.10", "3.11"]
_CI_MATRIX_BRACKET_RE = re.compile(r"python-version:\s*\[([^\]]+)\]")

# Multiline sequence format:
#   python-version:
#     - "3.10"
#     - "3.11"
# NOTE: use (?=\n|$) lookahead (zero-width) — NOT (?:\n|$) consuming alternation.
# The consuming form drops the final element when the file has no trailing newline.
# re.MULTILINE is NOT needed (pattern uses literal \n, not ^/$ anchors).
_CI_MATRIX_SEQUENCE_RE = re.compile(
    r"python-version:\s*\n((?:[ \t]+-\s*[\"']?\d+\.\d+[\"']?(?=\n|$)\n?)+)"
)

# Individual version extractor (shared by both paths)
_CI_VERSION_RE = re.compile(r'["\']?(\d+\.\d+)["\']?')


def extract_ci_matrix_python_versions(content: str) -> list[str]:
    """Extract Python versions from a CI matrix, supporting bracket and sequence formats."""
    bracket_match = _CI_MATRIX_BRACKET_RE.search(content)
    if bracket_match:
        versions = _CI_VERSION_RE.findall(bracket_match.group(1))
        return sorted(set(versions))

    seq_match = _CI_MATRIX_SEQUENCE_RE.search(content)
    if seq_match:
        versions = _CI_VERSION_RE.findall(seq_match.group(1))
        return sorted(set(versions))

    return []
```

### Detailed Steps

1. **Locate the existing function** in `hephaestus/scripts_lib/check_python_version_consistency.py:146`. The current regex is inlined inside the function body at `:161` — there is **no** module-level constant named `_CI_MATRIX_PYTHON_RE`. Add the three new constants after `import re` at `:11`.

2. **Replace `extract_ci_matrix_python_versions`** with the bracket-first/sequence-fallback implementation above.

3. **Add tests** covering:
   - Inline bracket format (existing behavior preserved)
   - Multiline sequence format: double-quoted, single-quoted, unquoted
   - 4-space indented sequence (tab/space-agnostic `[ \t]+`)
   - Deduplicated + sorted output
   - Mixed file where both formats appear (bracket wins by precedence)
   - **No-trailing-newline**: `'python-version:\n  - "3.10"\n  - "3.11"'` must return `["3.10", "3.11"]` — this is the critical test for the `(?=\n|$)` lookahead fix
   - Empty / no version key (returns `[]`)

4. **Do not repeat the public-API export claim**: `extract_ci_matrix_python_versions` is **not** in `hephaestus/validation/__init__.py` `__all__`. The bug's real impact is the silent-skip at `check_ci_matrix_coverage:200-202`, not a broken public API.

5. **Run the test suite**: `pixi run pytest tests/unit/scripts_lib/test_check_python_version_consistency.py -v`

### Bracket-Format Precedence

`_CI_MATRIX_BRACKET_RE` is tried first unconditionally. If it matches anywhere in the file, the sequence RE is never tried. A file with both formats returns the bracket version list regardless of string position.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Single regex covering both formats | `r'python-version:\s*(?:\[([^\]]+)\]\|((?:\n\s+-\s+.+)+))'` | Alternation with backreference groups makes extraction ambiguous; harder to read and test | Two separate named patterns with explicit fallback logic are clearer and independently testable |
| PyYAML `yaml.safe_load` for full parsing | Parse the entire workflow YAML with PyYAML | PyYAML is likely dev-only; adding a runtime dependency for one field extraction is disproportionate | Regex is the right tool here |
| `(?:\n\|$)` consuming alternation for sequence end-anchor | Used `(?:\n\|$)` to handle files with/without trailing newline | Consuming alternation drops the final sequence element when no `\n` follows — the `$` branch is effectively dead | Use `(?=\n\|$)` lookahead (zero-width); verified: input `'...\n  - "3.11"'` (no trailing newline) returns only `["3.10"]` with consuming form |
| `re.MULTILINE` flag on sequence RE | Added `re.MULTILINE` "for safety" | Flag is irrelevant — pattern uses literal `\n`, not `^`/`$` line anchors; misleads readers | Only add `re.MULTILINE` when the pattern actually uses `^` or `$` as line anchors |
| Citing `validation/__init__.py:105` as public-API export | Plan stated function is "exported via `validation/__init__.py:105`" as the bug's justification | Function is not in `__all__` at all; claim was inferred from issue body without grepping | Always `grep __all__` before citing a public-API export as rationale; the real justification is the silent-skip early-return in the internal consumer |

## Results & Parameters

### Verified Assumptions (R1 review)

| Assumption | Status | Evidence |
|------------|--------|----------|
| `extract_ci_matrix_python_versions` exported from `validation/__init__.py` | **FALSE** | `grep __all__ hephaestus/validation/__init__.py` — not present |
| `_CI_MATRIX_PYTHON_RE` is a module-level constant | **FALSE** | Current code inlines regex at `:161`; no such constant exists |
| Real impact of bug | Confirmed: `check_ci_matrix_coverage:200-202` early-return silently skips matrix check when `[]` returned | Code inspection |

### Reviewer Risk Flags (post-R1)

1. **No-trailing-newline test is the critical regression check**: `test_sequence_format_no_trailing_newline` is the only test that exercises the `(?=\n|$)` lookahead. If the implementer accidentally reverts to `(?:\n|$)`, this test catches it.

2. **`_CI_VERSION_RE` permissiveness**: Within the captured segment, `[ \t]+-\s*` anchors each line to a list item, so stray decimals in inline comments inside the block are unlikely — acceptable risk.

3. **`check_ci_matrix_coverage` hardcodes `test.yml`**: Intentionally out of scope for #1284 but worth noting in the PR description.

### Reference

- Source file: `hephaestus/scripts_lib/check_python_version_consistency.py`
- Issue: HomericIntelligence/ProjectHephaestus #1284
