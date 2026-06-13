---
name: automation-planner-learn-record-writing-robustness
description: "Robustness patterns for planner learn record writing in hephaestus/automation/planner_review_loop.py. Use when: (1) auditing or refactoring _write_planner_learn_record, (2) adding companion file writes (json + log), (3) changing persisted JSON schema fields, (4) designing multi-part prompt directives in build_learn_prompt."
category: architecture
date: 2026-06-13
version: "2.0.0"
user-invocable: false
verification: verified-ci
history: automation-planner-learn-record-writing-robustness.history
tags: ["planner", "learn-record", "write-order", "json", "schema", "prompt-design", "build_learn_prompt"]
---

# Automation Planner Learn Record Writing Robustness

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Identify and address robustness gaps in `_write_planner_learn_record` in `hephaestus/automation/planner_review_loop.py` |
| **Outcome** | Implementation complete and CI-verified (PR #1279, 4049 tests passed, 0 failed) |
| **Verification** | verified-ci |
| **Source Issue** | ProjectHephaestus #1138 |

## When to Use

- Auditing or refactoring `_write_planner_learn_record` in `planner_review_loop.py`
- Adding or changing any pair of companion files (authoritative `.json` + human-readable `.log`)
- Dropping or renaming a field in any persisted `.json` schema (e.g., `learn_succeeded_at`)
- Designing multi-part prompt strings where output format directives might be misplaced in `build_learn_prompt`
- Comparing `_write_planner_learn_record` against `_write_learn_record` in `learn.py` for symmetry

## Verified Workflow

### Quick Reference

```bash
# Audit consumers of a persisted JSON field before removing it
grep -r "learn_succeeded_at" hephaestus/ tests/ scripts/

# Verify write order in _write_planner_learn_record: json must come before log
grep -n "_write_planner_learn_record\|\.json\|\.log" hephaestus/automation/planner_review_loop.py | head -40

# Compare with learn.py reference implementation
grep -n "_write_learn_record\|\.json\|\.log" hephaestus/automation/learn.py | head -20

# Verify OSError patch path for test coverage
grep -n "from pathlib import Path" hephaestus/automation/planner_review_loop.py
# Expected at line 20 — confirms patch("hephaestus.automation.planner_review_loop.Path.write_text", ...)

# Verify prompt directive ordering in build_learn_prompt
grep -n "Do NOT return a plan\|plan text\|build_learn_prompt" hephaestus/automation/learn.py | head -20
```

### Detailed Steps

#### Pattern 1 — Write Order Atomicity (json before log)

1. Locate the two companion file writes in `_write_planner_learn_record` (around line 599–666 of `planner_review_loop.py` at planning time — line numbers may shift).
2. Confirm the current order: if `.log` is written before `.json`, swap them.
3. The authoritative `.json` file must always be written first so that a mid-write crash leaves the authoritative record present (even if incomplete) rather than only the human-readable log.
4. Reference: `learn.py:_write_learn_record` writes `.json` only — mirror that discipline in the planner variant.

#### Pattern 2 — Schema Field Removal Audit

1. Before removing any field from a persisted `.json` schema, run a consumer audit:
   ```bash
   grep -r "<field_name>" hephaestus/ tests/ scripts/
   ```
2. For the specific case of `learn_succeeded_at → learn_duration_s`:
   - Confirm all readers of the old field name are updated or that the field is truly unused.
   - `learn_duration_s` is computed from `time.monotonic()` start/end; the `start: float = 0.0` sentinel is safe in practice (monotonic is always > 0 at normal process start) but document the assumption.
3. **Audit scope caveat (R1):** The grep-based consumer audit is NOT exhaustive — it covers the local repo but does not traverse the full dependency graph across sibling projects. Flag this as a risk in the PR body so downstream consumers of the JSON records are warned.
4. Add a migration note in the PR body so downstream consumers of the JSON records are warned.

#### Pattern 3 — Prompt Directive Placement (CORRECTED in v2.0.0 — directives go FIRST)

> **v2.0.0 Correction:** v1.1.0 described this pattern backwards. The actual implementation moves
> directives to appear IMMEDIATELY AFTER `/learn` and BEFORE the context suffix — not at the end.
> The v1.1.0 test assertion was also inverted and must not be used.

1. In `build_learn_prompt` (in `learn.py`), output format directives must appear IMMEDIATELY AFTER `/learn` and BEFORE the context/background suffix.
2. Actual prompt structure: `/learn [EXECUTE directives] [context/background suffix]`
3. Pattern: `"/learn " + execute_directives + context_suffix` — NOT `context_suffix + execute_directives`.
4. Do NOT make this change in `capture_planner_learnings` — that function provides context strings, not the final prompt assembly.
5. Review the full prompt string in `build_learn_prompt` after any refactor to verify directive ordering is preserved.

**Correct test assertion (verified in CI):**
```python
# Verify directives appear BEFORE context content in build_learn_prompt output
prompt = build_learn_prompt(plan_text="plan text", ...)
assert prompt.index("Do NOT return a plan") < prompt.index("plan text")
# WARNING: Do NOT write the assertion the other way around:
# assert prompt.index("plan text") < prompt.index("Do NOT return a plan")  # WRONG — v1.1.0 error
```

**Existing test that must also be updated when changing directive placement:**

`test_build_learn_prompt_uses_user_facing_command` in `tests/unit/automation/test_learn.py` previously
asserted `prompt.startswith("/learn Capture what happened.")`. After moving directives to the front,
update to:
```python
assert prompt.startswith("/learn EXECUTE")
assert prompt.index("Do NOT return a plan") < prompt.index("Capture what happened.")
```

#### Pattern 4 — Sentinel Value Safety

1. The `start: float = 0.0` sentinel in `_write_planner_learn_record` uses `if start else None` to detect "not set".
2. This is theoretically unsafe: `0.0` is a valid `time.monotonic()` return value at process start (though extremely rare in practice).
3. **Implementation decision (v2.0.0 verified):** The sentinel risk was accepted as theoretical only. The implementation kept `start: float = 0.0` with `if start else None`. No change made.
4. Safer alternative (not implemented): `start: float | None = None` with `if start is not None`.
5. If a reviewer flags the sentinel check, document the assumption with an inline comment rather than changing the sentinel type.

#### Pattern 5 — OSError Handling is Non-Fatal (verified)

1. `_write_planner_learn_record` wraps all file writes in `try/except OSError` — failures log a warning but do not raise.
2. This is intentional: the learn record is auxiliary; a write failure must not abort the main pipeline.
3. The correct patch path to activate this branch in tests:
   ```python
   patch("hephaestus.automation.planner_review_loop.Path.write_text", side_effect=OSError("permission denied"))
   ```
4. Test name: `test_oswrite_failure_is_nonfatal` — confirmed passing in CI (PR #1279).
5. `from pathlib import Path` at line 20 of `planner_review_loop.py` (between `import json/logging` and `from datetime import datetime`) is what makes the patch path above work.

#### Pattern 6 — learn_duration_s Implementation (verified)

1. `import time` must be present at module level in `planner_review_loop.py` (confirmed at line 20).
2. Declare `_learn_start: float = 0.0` sentinel BEFORE calling `_call_claude` (or equivalent learn invocation).
3. After the call (in BOTH success and failure paths), compute:
   ```python
   duration = round(time.monotonic() - _learn_start, 3) if _learn_start else None
   ```
4. Pass `start=_learn_start` to `_write_planner_learn_record`.
5. Both success and failure paths must supply `start` — do not guard the assignment with an `if success` check.
6. Test assertions:
   ```python
   assert record["learn_duration_s"] is not None
   assert record["learn_duration_s"] >= 0.0
   ```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Log-before-json write order | `_write_planner_learn_record` wrote `.log` then `.json` | A crash mid-sequence leaves only the human-readable log with no authoritative record | Always write authoritative file first; human-readable is secondary |
| Dropping `learn_succeeded_at` without audit | Field removal planned without grep-checking consumers | Silent breakage in downstream readers that parse the JSON | Grep all consumers before any schema field removal |
| Mid-prompt directive placement (wrong function) | R0 plan — added `Do NOT return a plan` directive to `_capture_planner_learnings` context string | Issue #1138 explicitly named `build_learn_prompt` in `learn.py` as the target; editing the adjacent function violates POLA and doesn't fix the actual prompt structure | When the issue spec names a specific function, that is the target — read the function signature before editing neighbors |
| Backwards directive ordering in skill (v1.1.0) | v1.1.0 described directives appearing AFTER content (standard "context → directives" pattern) | Actual implementation moved directives BEFORE context suffix; the v1.1.0 test assertion was also inverted | Always verify against the actual implementation, not the planning-phase hypothesis |

## Results & Parameters

### Write Order Rule (copy-paste pattern)

```python
# CORRECT — authoritative first, human-readable second
_write_json_record(path_json, record)   # authoritative
_write_log_record(path_log, record)     # human-readable

# INCORRECT — do not write log before json
_write_log_record(path_log, record)     # human-readable (wrong order)
_write_json_record(path_json, record)   # authoritative too late
```

### Schema Change Audit Command

```bash
# Run before removing any persisted JSON field
FIELD="learn_succeeded_at"
grep -rn "$FIELD" hephaestus/ tests/ scripts/ docs/
# NOTE: This audits the local repo only. Cross-project consumers are NOT covered.
```

### Prompt Structure Template (build_learn_prompt) — VERIFIED FORM

```python
# In build_learn_prompt (learn.py) — directives FIRST, context AFTER
# WRONG (v1.1.0): context_background → content → directives
# CORRECT (v2.0.0 verified): /learn + directives → context_suffix
prompt = (
    "/learn "
    f"{execute_directives}\n\n"   # FIRST: "Do NOT return a plan. Do NOT ask for approval."
    f"{context_suffix}"           # SECOND: background/context string
)
```

### Sentinel Value Note

`start: float = 0.0` in `_write_planner_learn_record` uses `if start else None`. This is safe in practice because `time.monotonic()` always returns a value > 0 after normal process initialization. However:

- **Theoretical risk:** `0.0` is a valid monotonic value at process start — the sentinel check would incorrectly treat it as "not set"
- **Implementation decision (verified):** sentinel risk accepted as theoretical; `0.0` sentinel kept as-is
- **Safer alternative (not implemented):** `start: float | None = None` with `if start is not None`
- Document the assumption with an inline comment to prevent future reviewer flags

### OSError Test Patch Path

When testing OSError handling in `_write_planner_learn_record`, the correct patch path is:
```python
patch("hephaestus.automation.planner_review_loop.Path.write_text", side_effect=OSError(...))
```
This is valid because `from pathlib import Path` is at line 20 of `planner_review_loop.py`. Test name: `test_oswrite_failure_is_nonfatal`.

### learn_duration_s Pattern

```python
import time  # must be present at module level

# Before _call_claude / learn invocation:
_learn_start: float = 0.0
_learn_start = time.monotonic()

# After call (in both success and failure paths):
learn_duration_s = round(time.monotonic() - _learn_start, 3) if _learn_start else None
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1138 planning session (R0) | Patterns identified via code review; implementation not yet executed |
| ProjectHephaestus | Issue #1138 planning session (R1) | R0 POLA violation corrected; sentinel gotcha documented; OSError patch path confirmed |
| ProjectHephaestus | Issue #1138 implementation (PR #1279) | Full unit suite 4049 passed, 0 failed; CI verified; directive ordering correction confirmed |
