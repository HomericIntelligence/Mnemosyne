---
name: cli-format-output-pola-silent-fallback
license: BSD-3-Clause
description: "Choose and test a deliberate contract for CLI output-format dispatch instead of silently accepting invalid format names. Use when: (1) an audit flags POLA fallback in format_output(), (2) deciding whether caller compatibility requires fallback or permits ValueError, (3) preserving table-on-non-sequence behavior while rejecting unknown, empty, or case-mismatched names."
category: debugging
date: 2026-08-06
version: "1.1.0"
user-invocable: false
verification: unverified
history: cli-format-output-pola-silent-fallback.history
tags: [cli, output-format, pola, validation, compatibility]
---

# CLI format_output POLA: Silent Fallback vs ValueError

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 (v1.1.0; originally 2026-06-27) |
| **Objective** | Choose an explicit invalid-format contract for `format_output()` after auditing callers, without changing supported rendering or the separate table/non-sequence fallback. |
| **Outcome** | The earlier fallback-documentation workflow was CI-verified. The v1.1.0 strict-validation successor is an implementation plan only; ProjectHephaestus code and tests were not changed in this session. |
| **Verification** | unverified for v1.1.0; the v1.0.0 fallback workflow remains archived as verified-ci |
| **History** | [changelog](./cli-format-output-pola-silent-fallback.history) |

## When to Use

- When an audit flags a function for silently ignoring invalid input (POLA violation)
- When deciding between raising `ValueError` vs documenting silent fallback in a CLI utility
- When writing tests to pin CLI `format_type` fallback behavior in `hephaestus/cli/utils.py`
- When a PR title says "raise ValueError" but the implementation keeps silent fallback — commit message must match actual behavior
- When unknown, empty, or case-mismatched format names should fail while exact `"text"`, `"json"`, and `"table"` remain compatible
- When strict name validation must not accidentally remove the existing `"table"` request behavior for non-sequence data

## Verified Workflow

> **Warning:** The v1.1.0 strict-validation branch below has not been validated
> end-to-end. Treat it as a hypothesis until its focused tests and CI pass. The
> v1.0.0 document-and-test fallback branch was previously `verified-ci`.

### Quick Reference

```python
# Option A — Document + test (preferred if callers depend on fallback)
# In docstring, explicitly state the fallback:
# "Any unrecognized format_type falls back to 'text' format rather than raising."

# Option B — Raise ValueError (preferred after caller audit proves compatibility)
_SUPPORTED_OUTPUT_FORMATS = ("json", "table", "text")
if format_type not in _SUPPORTED_OUTPUT_FORMATS:
    supported = ", ".join(_SUPPORTED_OUTPUT_FORMATS)
    raise ValueError(
        f"Unsupported output format {format_type!r}; expected one of: {supported}"
    )
```

```python
# Test pinning silent-fallback behavior (for Option A):
def test_invalid_format_falls_back_to_text():
    # hephaestus/cli/utils.py: format_output() — else branch falls through to text
    result = format_output({"key": "value"}, format_type="invalid")
    assert "key" in result  # text representation, not an exception

def test_table_format_on_dict_falls_back_to_text():
    # hephaestus/cli/utils.py: 'table' branch requires list/tuple; dict falls to else (text)
    result = format_output({"key": "value"}, format_type="table")
    assert "key" in result  # text fallback, not an exception
```

### Detailed Steps

1. Identify if callers depend on the silent fallback behavior (grep call sites for `format_type=`)
2. If callers pass arbitrary strings or rely on "text" as a safe default: **use Option A** (document + test)
3. If `format_type` only comes from validated sources (CLI argparse choices): **use Option B** (raise ValueError)
4. For `hephaestus/cli/utils.py` specifically: the actual branching logic is `if format_type == 'json': ... elif format_type == 'table' and isinstance(data, (list, tuple)): ... else: # text`
5. Update the docstring to describe exact fallback behavior including case-sensitivity (`"JSON"` != `"json"`)
6. Add non-vacuous test comments citing the specific code path and line numbers exercised
7. Before moving an established helper from fallback to rejection, search every production call site. If all callers use supported literals, a strict public boundary does not require a permissive compatibility API solely for hypothetical callers.
8. Validate the format name before rendering, then leave supported dispatch unchanged. In particular, `format_type="table"` with a dict or scalar is a supported format request with incompatible data shape; preserve its existing text rendering unless the issue explicitly changes that separate contract.
9. Test invalid names (`"bogus"`, `"yaml"`, `""`, `"JSON"`) and supported behavior (`"text"`, `"json"`, sequence `"table"`, default text, and table/non-sequence compatibility) independently.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Attempt 1 | Titled PR "raise ValueError" but implementation kept silent fallback | Misleading mismatch between PR title/body and actual code change; commit message must describe what actually changed | PR title and commit message MUST describe the actual behavior change, not the originally intended one |
| Treat invalid format names and unsupported table data as one case | Put both checks behind one broad rejection path | `"table"` is a recognized format even when the input is not a sequence; rejecting it would expand scope beyond strict name validation and break compatibility | Validate the case-sensitive format identifier first, then preserve the existing rendering rules for each supported identifier |
| Keep permissive fallback without auditing callers | Assumed unknown third-party strings might exist and retained silent text fallback | A repository-wide ProjectHephaestus search found production calls use the supported literal `"json"`; hypothetical compatibility did not justify hiding typos | Search actual call sites and choose the narrowest explicit contract supported by evidence |

## Results & Parameters

**hephaestus/cli/utils.py — format_output() branching logic (as of PR #1663)**:

```python
# Effective branching (simplified):
if format_type == 'json':
    # JSON output
elif format_type == 'table' and isinstance(data, (list, tuple)):
    # Table output
else:
    # Text fallback — reached for: unrecognized format_type, case mismatch ("JSON"),
    # or 'table' on non-sequence data (dict, str, etc.)
```

**Docstring pattern for documenting fallback behavior**:
```
Args:
    format_type: Output format. One of "text", "json", "table".
        Matching is case-sensitive ("JSON" != "json"). Unrecognized
        values and "table" applied to non-list/tuple data both fall
        back silently to text format.
```

**Test comment pattern** (explains which code path is exercised):
```python
# hephaestus/cli/utils.py: format_output() — else branch falls through to text
# when format_type is not 'json' and not ('table' on a sequence).
```

**Proposed ProjectHephaestus v1.1.0 boundary tests**:

```python
@pytest.mark.parametrize("format_type", ["bogus", "yaml", "", "JSON"])
def test_unknown_format_is_rejected(format_type: str) -> None:
    with pytest.raises(ValueError, match="Unsupported output format"):
        format_output({"name": "hephaestus"}, format_type=format_type)

def test_supported_formats_remain_case_sensitive_and_compatible() -> None:
    assert format_output(["a", "b"], "text") == "a\nb"
    assert json.loads(format_output({"ok": True}, "json")) == {"ok": True}
    assert "name" in format_output([{"name": "hephaestus"}], "table")
```

The current plan reported 22 production calls and all explicit format arguments
used the supported literal `"json"`. Re-run the search at implementation time;
counts and line numbers are point-in-time evidence, not a permanent invariant.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1509, PR #1663 — fix(cli): raise ValueError on invalid format_type in format_output | CI green 2026-06-27 |
| ProjectHephaestus | CLI boundary-hardening plan — strict case-sensitive format-name validation while preserving supported rendering | unverified plan, 2026-08-06 |
