---
name: validation-cli-tier-docs-duplicate-section-detection
description: "Fix load_documented_tiers to detect duplicate H2 section headers in COMPATIBILITY.md. Use when: (1) the cli-tier-docs validator silently accepts a file with two identical H2 sections, (2) a break-on-H2 parser exits early and misses a second occurrence of the target section, (3) adding duplicate-section detection to a state-machine markdown parser."
category: debugging
date: 2026-06-13
version: "2.0.0"
user-invocable: false
verification: verified-ci
tags: [validation, markdown-parser, state-machine, cli-tier-docs, duplicate-section]
---

# Validation: CLI Tier Docs Duplicate Section Detection

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Fix `load_documented_tiers` in `hephaestus/validation/cli_tier_docs.py` to detect and report duplicate `## Console-Script Stability Tiers` H2 sections in COMPATIBILITY.md |
| **Outcome** | Implemented and verified — 22 tests pass including `TestRealRepo::test_repo_has_no_tier_doc_violations` on live COMPATIBILITY.md |
| **Verification** | verified-ci — PR #1301 merged, all CI gates green |
| **Issue** | ProjectHephaestus #1255 |

## When to Use

- The `hephaestus-check-cli-tier-docs` validator reports OK but COMPATIBILITY.md has two `## Console-Script Stability Tiers` sections
- A markdown state-machine parser uses `break` on encountering a non-matching H2, causing it to stop scanning before finding a second occurrence of the target section
- Adding `duplicate-section` error detection parallel to an existing `duplicate-tiers` detection pattern
- Changing a function's return from a 2-tuple to a 3-tuple and needing to audit all unpack sites
- Reviewing a state-machine parser that has `in_section`, `in_table`, and related flags to ensure all flags are reset correctly when exiting a section

## Verified Workflow

> **Status**: Verified — implemented in PR #1301, 22 tests pass, CI green.

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
   Run `grep -rn "load_documented_tiers" hephaestus/ tests/ scripts/` and confirm every unpack site. Only two callers existed: `main()` and the test file — safe to change atomically in one PR.

2. **Replace `break` with a section-exit reset** in `load_documented_tiers`:
   ```python
   # OLD — stops scanning the file on first non-matching H2
   break
   # NEW — exits this section but continues scanning for a second occurrence
   in_section = False
   in_table = False
   continue
   ```
   Reset order matters: set `in_section = False` before `in_table = False`.

3. **Add `section_count` tracking** — increment on every `_SECTION_HEADER_RE` match inside `load_documented_tiers`, not just on the first one. Initialize to `0` before the loop.
   ```python
   if _SECTION_HEADER_RE.match(line):
       in_section = True
       in_table = False
       section_count += 1
       continue
   ```

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
           return [
               TierDocFinding(
                   cli="<section>",
                   kind="duplicate-section",
                   detail=(
                       f"COMPATIBILITY.md contains {section_count} "
                       "'## Console-Script Stability Tiers' sections; "
                       "merge them into one to prevent cross-section contradictions"
                   ),
               )
           ]
       return []
   ```
   The sentinel CLI value `"<section>"` is parallel to the existing `"<table>"` sentinel.

6. **Update `main()`** to unpack the 3-tuple and call both new and existing helpers:
   ```python
   tiers, occurrences, section_count = load_documented_tiers(path)
   findings = (
       find_duplicate_sections(section_count)
       + find_duplicate_tiers(occurrences)
       + find_violations(tiers, registered)
   )
   ```

7. **Update all test unpack sites** — every line in `test_cli_tier_docs.py` that unpacks `load_documented_tiers()` must change from 2-tuple to 3-tuple. Sites changed: lines 84, 98, 103, 132-133.

8. **Add test class `TestDuplicateSectionDetection`** with six tests:
   - `test_no_finding_when_single_section` — boundary case: section_count=1 produces no finding
   - `test_no_finding_when_zero_sections` — boundary case: section_count=0 produces no finding
   - `test_duplicate_section_flagged` — unit test for find_duplicate_sections in isolation
   - `test_parser_counts_two_sections` — integration test: write a tmp_path COMPATIBILITY.md with two target sections separated by an unrelated H2; assert `section_count == 2`, `occ` contains both tiers, `tiers` has last-write-wins
   - `test_cross_section_conflict_surfaces_both_findings` — assert both `duplicate-section` AND `conflicting-tier` are emitted
   - `test_two_sections_same_tier_no_conflict_but_duplicate_section_flagged` — same tier in both sections still emits `duplicate-section` + `duplicate-tier`

9. **Run tests**:
   ```bash
   pixi run pytest tests/unit/validation/test_cli_tier_docs.py -v
   ```
   Expected: 22 tests pass.

10. **Rename misleading test**: `test_load_tiers_stops_at_next_section` to `test_load_tiers_excludes_content_under_other_sections` — the new behavior is a soft state reset, not a hard stop.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Using `break` on first non-matching H2 | Parser exits the loop entirely when it hits any H2 that is not the target section | A second occurrence of the target section later in the file is never reached; validator reports false OK | Replace `break` with `in_section = False; in_table = False; continue` to keep scanning |
| Assuming 2-tuple return is safe to change without audit | Changed return to 3-tuple based only on reading the two known call sites | Did not grep full codebase for additional callers; any external consumer would break silently | Always run `grep -rn load_documented_tiers` across the entire repo before changing a return type |
| Trusting test name `test_load_tiers_stops_at_next_section` | Test name implies hard stop (break) as correct behavior | After fix, the behavior is a soft reset not a stop; test still passes but name is semantically wrong | Rename tests when the behavior they describe changes, even if the assertion still holds |

## Results & Parameters

```
Files modified:
  hephaestus/validation/cli_tier_docs.py
    - load_documented_tiers: break -> continue + section_count tracking
    - find_duplicate_sections: new helper (parallel to find_duplicate_tiers)
    - main: unpack 3-tuple, call find_duplicate_sections

  tests/unit/validation/test_cli_tier_docs.py
    - 2-tuple -> 3-tuple unpack at lines 84, 98, 103, 132-133
    - TestDuplicateSectionDetection: 6 new tests
    - test_load_tiers_stops_at_next_section renamed to
      test_load_tiers_excludes_content_under_other_sections

State-machine variables in load_documented_tiers (all reset on section exit):
  in_section: bool   -- True while inside the target H2 block
  in_table: bool     -- True while inside the markdown table
  header_seen: bool  -- True after the | Tier | ... | header row is parsed
  section_count: int -- NEW: counts occurrences of the target H2

New TierDocFinding kind:
  kind="duplicate-section", cli="<section>"

New TierDocFinding kind for existing detection:
  kind="conflicting-tier" -- emitted by find_duplicate_tiers when same CLI
  appears in both sections with different tiers

Cross-section scenario: two sections with same CLI but different tiers
  -> both duplicate-section AND conflicting-tier emitted (verified in test)

Verified (2026-06-13):
  22 tests pass including TestRealRepo::test_repo_has_no_tier_doc_violations
  grep -c "^## Console-Script Stability Tiers" COMPATIBILITY.md -> 1 (healthy)
  PR #1301 merged, all CI gates green
  find_duplicate_sections correctness verified
  3-tuple return annotation mypy compliant
  No external callers beyond main() and test file (grep confirmed)
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1255, PR #1301 | 22 tests pass, CI green, verified-ci |
