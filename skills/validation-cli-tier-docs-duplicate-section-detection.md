---
name: validation-cli-tier-docs-duplicate-section-detection
description: "Fix load_documented_tiers to detect duplicate H2 section headers in COMPATIBILITY.md. Use when: (1) the cli-tier-docs validator silently accepts a file with two identical H2 sections, (2) a break-on-H2 parser exits early and misses a second occurrence of the target section, (3) adding duplicate-section detection to a state-machine markdown parser."
category: debugging
date: 2026-06-13
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [validation, markdown-parser, state-machine, cli-tier-docs, duplicate-section]
---

# Validation: CLI Tier Docs Duplicate Section Detection

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Fix `load_documented_tiers` in `hephaestus/validation/cli_tier_docs.py` to detect and report duplicate `## Console-Script Stability Tiers` H2 sections in COMPATIBILITY.md |
| **Outcome** | Plan written; implementation not yet executed |
| **Verification** | unverified — plan only, no CI run |
| **Issue** | ProjectHephaestus #1255 |

## When to Use

- The `hephaestus-check-cli-tier-docs` validator reports OK but COMPATIBILITY.md has two `## Console-Script Stability Tiers` sections
- A markdown state-machine parser uses `break` on encountering a non-matching H2, causing it to stop scanning before finding a second occurrence of the target section
- Adding `duplicate-section` error detection parallel to an existing `duplicate-tiers` detection pattern
- Changing a function's return from a 2-tuple to a 3-tuple and needing to audit all unpack sites
- Reviewing a state-machine parser that has `in_section`, `in_table`, and related flags to ensure all flags are reset correctly when exiting a section

## Verified Workflow

> **Status**: Planning-only — the steps below are planned but not yet executed. Treat as a design reference, not a verified recipe. This workflow has not been validated end-to-end.

### Quick Reference

```bash
# Confirm the bug: parser stops at first non-matching H2
grep -n "break\|in_section\|in_table" hephaestus/validation/cli_tier_docs.py

# Count target sections in COMPATIBILITY.md (should be 1 in a healthy repo)
grep -c "^## Console-Script Stability Tiers" COMPATIBILITY.md

# Find all callers of load_documented_tiers before changing its return type
grep -rn "load_documented_tiers" hephaestus/ tests/ scripts/ 2>/dev/null
```

### Detailed Steps

1. **Audit all callers of `load_documented_tiers`** before touching the return type.
   Run `grep -rn "load_documented_tiers" hephaestus/ tests/ scripts/` and confirm every unpack site. The plan assumed only `main()` and the test file call it — verify this is still true.

2. **Replace `break` with a section-exit reset** in `load_documented_tiers` (around line 89–90 of `cli_tier_docs.py`):
   ```python
   # OLD — stops scanning the file on first non-matching H2
   break
   # NEW — exits this section but continues scanning for a second occurrence
   in_section = False
   in_table = False
   continue
   ```
   Reset order matters: set `in_section = False` before `in_table = False` to avoid state confusion if any mid-table logic reads both flags.

3. **Add `section_count` tracking** — increment on every `_SECTION_HEADER_RE` match inside `load_documented_tiers`, not just on the first one. Initialize to `0` before the loop.

4. **Expand the return from 2-tuple to 3-tuple**:
   ```python
   # OLD
   return tiers, occurrences
   # NEW
   return tiers, occurrences, section_count
   ```
   Update the type annotation accordingly.

5. **Add `find_duplicate_sections` helper** (parallel to `find_duplicate_tiers`):
   ```python
   def find_duplicate_sections(section_count: int) -> list[TierDocFinding]:
       """Return a finding if the target H2 appears more than once."""
       if section_count > 1:
           return [TierDocFinding(cli="<section>", kind="duplicate-section",
                                  message=f"## Console-Script Stability Tiers appears {section_count} times")]
       return []
   ```

6. **Update `main()`** to unpack the 3-tuple and call both new and existing helpers:
   ```python
   tiers, occurrences, section_count = load_documented_tiers(path)
   findings = (find_duplicate_sections(section_count)
               + find_duplicate_tiers(occurrences)
               + find_violations(tiers, registered))
   ```

7. **Update all test unpack sites** — every line in `test_cli_tier_docs.py` that unpacks `load_documented_tiers()` must change from 2-tuple to 3-tuple. Known sites (as of plan date): lines 84, 98, 103, 132–133.

8. **Run tests** to confirm existing tests still pass and add a new test for the duplicate-section path:
   ```bash
   pixi run pytest tests/unit/validation/test_cli_tier_docs.py -v
   ```

9. **Check that the misleading test name is addressed**: `test_load_tiers_stops_at_next_section` (line 87) will still pass under the new code because a non-target H2 resets `in_section`, so content under it is still excluded. The test name implies a `break` but the new behavior is a soft reset — consider renaming to `test_load_tiers_excludes_content_under_other_sections`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Using `break` on first non-matching H2 | Parser exits the loop entirely when it hits any H2 that is not the target section | A second occurrence of the target section later in the file is never reached; validator reports false OK | Replace `break` with `in_section = False; in_table = False; continue` to keep scanning |
| Assuming 2-tuple return is safe to change without audit | Plan changed return to 3-tuple based only on reading the two known call sites | Did not grep full codebase for additional callers; any external consumer would break silently | Always run `grep -rn load_documented_tiers` across the entire repo before changing a return type |
| Trusting test name `test_load_tiers_stops_at_next_section` | Test name implies hard stop (break) as correct behavior | After fix, the behavior is a soft reset not a stop; test still passes but name is semantically wrong | Rename tests when the behavior they describe changes, even if the assertion still holds |

## Results & Parameters

```
Files modified (plan):
  hephaestus/validation/cli_tier_docs.py   — load_documented_tiers, find_duplicate_sections, main
  tests/unit/validation/test_cli_tier_docs.py — 2-tuple → 3-tuple unpack at lines 84, 98, 103, 132–133

State-machine variables in load_documented_tiers (all must be reset on section exit):
  in_section: bool   — True while inside the target H2 block
  in_table: bool     — True while inside the markdown table
  header_seen: bool  — True after the | Tier | … | header row is parsed
  section_count: int — NEW: counts occurrences of the target H2

New TierDocFinding kind:
  kind="duplicate-section", cli="<section>"

Verified today (2026-06-13):
  grep -c "^## Console-Script Stability Tiers" COMPATIBILITY.md  → 1
  break on line 90 of cli_tier_docs.py confirmed by direct read
  Test unpack sites in test_cli_tier_docs.py: lines 84, 98, 103, 132–133

Unverified (needs CI):
  find_duplicate_sections correctness
  3-tuple return annotation mypy compliance
  No external callers exist beyond main() and test file
```
