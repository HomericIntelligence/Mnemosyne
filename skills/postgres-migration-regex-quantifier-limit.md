---
name: postgres-migration-regex-quantifier-limit
description: "Rewrite PostgreSQL regex check patterns whose repetition quantifier exceeds the engine limit of 255 (RE_DUP_MAX) as a character-class test plus a separate length test, and repair a migration that fails on fresh-database apply in place rather than with a follow-up migration. Use when a SQL migration, CHECK constraint, or trigger guard fails with 'invalid regular expression: invalid repetition count(s)', when writing bounded-length text patterns in PostgreSQL, or when a sealed/append-only migration policy conflicts with a fresh-apply failure."
category: debugging
date: 2026-10-28
version: "1.0.0"
user-invocable: false
tags: [postgres, sql-migration, regex, re-dup-max, invalid-regular-expression, check-constraint, char-length, sealed-migration, fresh-apply, ci-failure]
---

# PostgreSQL Migration Regex Quantifier Limit

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-28 |
| **Objective** | Diagnose and repair PostgreSQL regex patterns that exceed the engine repetition limit, and select the correct repair mode for a defective migration under an append-only policy. |
| **Outcome** | successful |

## When to Use

- A migration apply, CHECK constraint, trigger guard, or validation function fails on
  a fresh database with `invalid regular expression: invalid repetition count(s)`
  (for example `InvalidRegularExpressionError` from a PostgreSQL driver).
- You author a PostgreSQL pattern with a repetition quantifier such as `{1,512}` or
  `{1,1024}` to bound text length.
- A merged migration is defective under a sealed or append-only migration policy and
  you must decide between an in-place correction and a follow-up migration.

## Verified Workflow

### Quick Reference

PostgreSQL limits regex repetition counts to 255 (`RE_DUP_MAX`). Split any larger
bound into a character-class test plus a separate length test:

```sql
-- Before: rejected by the engine at apply time.
CHECK (value ~ '^[ -~]{1,512}$')
-- After: identical acceptance set, valid at apply time.
CHECK (value ~ '^[ -~]+$' AND char_length(value) <= 512)
```

Repair mode rule: a migration that fails on fresh-database apply cannot be repaired
by a later migration, because every fresh apply runs the broken file first and
stops. Correct that file in place when no durable artifact (a published template
database, a released dump, or a deployed schema) already contains its applied
result. Databases that CI builds per run are not durable artifacts. To find
offending quantifiers before apply:

```bash
# Upper bound above 255 in an explicit quantifier.
grep -nE '\{[0-9]+,(25[6-9]|2[6-9][0-9]|[3-9][0-9]{2}|[0-9]{4,})\}' migrations/
```

### Suggested Approach

1. Confirm the limit before deeper diagnosis: the apply error names
   `invalid repetition count(s)`; repetition counts above 255 are invalid in the
   PostgreSQL regex engine for both `{n,m}` forms.
2. Decide the repair mode with the durability test above. A failed apply records
   no version row, so the corrected file applies cleanly on fresh databases. If a
   durable artifact already applied the defective file, use a follow-up migration
   for those and correct the in-place file as well when policy permits.
3. Preserve the exact acceptance set in the rewrite:
   - `{1,N}` has a minimum of one character, so use `+`, not `*`.
   - Keep the anchors (`^`, `$`) only on the class test so the length test cannot
     bypass them.
   - Keep collations (for example `COLLATE "C"`), negation polarity (`~` versus
     `!~`), and wrapper semantics (for example a JSON-type guard that returns false
     for non-string values) unchanged.
   - Apply the length test to the same extracted value the pattern sees.
4. Validate on a fresh-database apply lane, plus focused tests for the guard
   behavior (empty, overlong by one, non-ASCII, control characters, and non-string
   JSON values). When no database engine is available locally, parse-check the SQL
   and scan every migration file for remaining over-limit quantifiers.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Append-only correction | Added a follow-up migration to replace the defective objects. | Fresh-database apply runs the broken file first and stops before any later file. | A fresh-apply failure requires an in-place correction of the broken file. |
| Bounded quantifier pattern | Wrote `^[ -~]{1,512}$` and `^[ -~]{1,1024}$` in guard checks. | Repetition counts above 255 exceed `RE_DUP_MAX`; the engine rejects the pattern at apply time. | Express length ceilings with `char_length() <= N` and keep the quantifier for character-set shape only. |

## Results & Parameters

### Configuration

```sql
-- JSON wrapper site (pattern runs on extracted text; length test on the same value).
(value -> 'path') #>> '{}' ~ '^[ -~]+$'
AND char_length((value -> 'path') #>> '{}') <= 1024
-- Column site with negation preserved.
column_name COLLATE "C" !~ '^[ -~]+$' OR char_length(column_name) > 512
```

### Expected Output

- The migration applies without `invalid repetition count(s)` on a fresh database.
- Empty strings, non-ASCII and control characters, and values one character above
  the ceiling are still rejected; non-string JSON values are still rejected by the
  type guard.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Service with numbered append-only SQL migrations and fresh-database CI apply lanes | Repaired a nine-site guard migration in place; later push CI green on all apply lanes | Same engine limit produced a same-class defect in an earlier migration of the same repository; a corpus-wide quantifier scan found no other sites. |

## References

- [PostgreSQL pattern matching](https://www.postgresql.org/docs/current/functions-matching.html)
- [ci-failure-triage-and-diagnosis](ci-failure-triage-and-diagnosis.md)
