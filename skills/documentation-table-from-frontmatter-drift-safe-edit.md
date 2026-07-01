---
name: documentation-table-from-frontmatter-drift-safe-edit
description: "How to safely add/edit a markdown documentation TABLE whose cell values are derived VERBATIM from another file's YAML frontmatter (e.g. a CLAUDE.md skill-catalog table whose new Arguments column mirrors each skill's argument-hint: field), and how to drift-check the result without false failures. Use when: (1) adding a column to a doc table where each row value must equal a per-file frontmatter field (argument-hint, name, description) extracted verbatim; (2) executing an approved plan that cites specific doc line ranges for the table location — the numbers WILL have drifted, re-grep the section heading anchor instead; (3) a grep -qF drift check reports a spurious MISS on a value containing markdown table metacharacters (a raw pipe | that must be escaped as \\| inside a table cell, so the raw form is intentionally absent from the rendered file); (4) invoking the markdownlint pre-commit hook and needing its REAL hook id (markdownlint-cli2, not markdownlint) before claiming the gate is green; (5) representing no-value rows with an em dash — as the sentinel."
category: documentation
date: 2026-07-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - documentation
  - markdown-table
  - frontmatter-derivation
  - doc-table-drift
  - line-number-drift
  - content-anchoring
  - escaped-pipe
  - grep-false-miss
  - markdownlint
  - precommit-hook-id
  - argument-hint
  - claude-md-catalog
  - hephaestus
---

# Adding a Frontmatter-Derived Column to a Markdown Doc Table (Drift-Safe)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-01 |
| **Objective** | Capture the three sharp, reusable gotchas hit while adding an **Arguments** column to the CLAUDE.md skill-catalog markdown table, where each cell is derived VERBATIM from that skill's `argument-hint:` frontmatter field (skills lacking the field shown as `—`), plus argument-bearing invocation examples in `docs/plugin-installation.md`. Pure documentation change; no code, no tests. |
| **Outcome** | Success — table column added, all 13 skill values verified against their frontmatter source, `markdownlint-cli2` passed locally. No CI run for this doc change yet. |
| **Verification** | verified-local — markdownlint (the only relevant gate) passed locally via the correct hook id; CI not yet run for this change. |
| **Category** | documentation |
| **Related Issues** | ProjectHephaestus #1496 (MINOR/POLA audit finding) |

The win is not "add a table column." It is: **derive each cell verbatim from its
frontmatter source, anchor the edit on CONTENT not the plan's line numbers, and
drift-check against the ESCAPED form so a correct edit doesn't read as a failure —
then run the REAL markdownlint hook id before claiming green.**

## When to Use

Use this skill when:

1. You are **adding or editing a doc table whose cell values must equal a per-file
   frontmatter field** — e.g. a CLAUDE.md skill-catalog table gaining an **Arguments**
   column that mirrors each skill's `argument-hint:` field verbatim, or any doc whose
   rows are a projection of `name:` / `description:` / other frontmatter across a set of
   sibling files.
2. You are **executing an approved plan that cites doc line ranges** for the table
   location. The numbers are a snapshot and WILL have drifted — re-grep the section
   heading anchor instead of trusting them.
3. Your **drift check reports a spurious MISS** on a value that contains markdown table
   metacharacters (a literal pipe), because that value must be escaped inside the cell
   and so its raw form is intentionally absent from the rendered file.
4. You need to **run the markdownlint pre-commit hook** and must use its real id.
5. You are **representing no-value rows** and want the conventional sentinel (`—`).

Do NOT use this for tables whose values are authored freehand (not derived from a
machine-readable source) — the derivation + drift-check discipline is the whole point.

## Verified Workflow

> Verification level: **verified-local**. `markdownlint-cli2` (the only relevant gate for
> this doc-only change) passed locally via `pixi run pre-commit run markdownlint-cli2
> --files CLAUDE.md docs/plugin-installation.md`. No CI run has confirmed this change yet,
> so do NOT claim `verified-ci`.

### Quick Reference

```bash
# 1. Ground-truth: extract EVERY frontmatter value in one pass.
for d in skills/*/; do
  s=$(basename "$d")
  h=$(grep -m1 'argument-hint:' "$d/SKILL.md" | sed 's/.*argument-hint: *//')
  echo "$s :: ${h:-(none)}"
done

# 2. Anchor the edit on the section HEADING, not the plan's line numbers.
grep -n '### Skill Catalog' CLAUDE.md   # plan said 225-251; real table was 243-269

# 3. Render each cell: no-value -> em dash; escape inner pipes for the table.
#    raw  "--dry-run | --no-swarm | --trunk BRANCH"
#    cell "--dry-run \| --no-swarm \| --trunk BRANCH"

# 4. Drift-check against the ESCAPED form (or normalize metachars before grep -F).
#    Comparing the RAW value with pipes -> spurious MISS (see gotcha #2).

# 5. Confirm the REAL markdownlint hook id, THEN run it.
grep -iE 'id:.*(markdown|md)' .pre-commit-config.yaml   # -> markdownlint-cli2
pixi run pre-commit run markdownlint-cli2 --files CLAUDE.md docs/plugin-installation.md
```

### Detailed Steps

1. **Extract the source of truth in one pass, before editing anything.** Loop the sibling
   files and pull each frontmatter value verbatim so you edit against ground truth, not
   memory:

   ```bash
   for d in skills/*/; do s=$(basename "$d"); \
     h=$(grep -m1 'argument-hint:' "$d/SKILL.md" | sed 's/.*argument-hint: *//'); \
     echo "$s :: ${h:-(none)}"; done
   ```

2. **Anchor the table edit on a CONTENT string, never the plan's cited line numbers.**
   The approved plan cited `CLAUDE.md:225-251` for the catalog table; the table was
   actually at `243-269` — an ~18-line offset. `grep -n '### Skill Catalog' CLAUDE.md`
   to find the real location. Plan line ranges are a snapshot and drift as the file
   changes; re-anchor on the heading (or the header row of the table) every time.

3. **Render cells: em dash for no-value, escaped pipe for values with pipes.** Skills
   lacking the field become `—` (em dash) — the conventional "no argument" sentinel.
   A value containing a literal `|` (e.g. `--dry-run | --no-swarm | --trunk BRANCH`) MUST
   have each inner pipe escaped as `\|` or it will break the markdown table structure and
   trip markdownlint's table rule (and mis-render).

4. **Drift-check against the ESCAPED form, not the raw frontmatter value.** A loop that
   does `grep -qF "$raw_value" CLAUDE.md` will report a spurious **MISS** for any value
   containing pipes, because the raw (unescaped) form was intentionally escaped in the
   cell and so is absent from the rendered file. Compare against the escaped form
   (transform `|` -> `\|` first), or strip/normalize table metacharacters before
   `grep -F`. A correct edit otherwise reads as a failure. (In this case 12/13 skills
   matched raw; only `tidy` — whose value has literal pipes — reported a false MISS.)

5. **Confirm the real markdownlint hook id, THEN actually run it.** The hook id is
   `markdownlint-cli2`, NOT `markdownlint`. `pre-commit run markdownlint --files ...`
   fails with "No hook with id `markdownlint` in stage `pre-commit`". Discover the real
   id first — `grep -iE 'id:.*(markdown|md)' .pre-commit-config.yaml` — then run it:
   `pixi run pre-commit run markdownlint-cli2 --files CLAUDE.md docs/plugin-installation.md`.
   Never claim the lint gate is green without running the correct id.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Trusting the plan's cited line range | Editing the catalog table at `CLAUDE.md:225-251` as the approved plan stated | The real table had shifted to lines `243-269` (~18-line drift); the cited range pointed at unrelated content | Re-grep the section heading anchor (`### Skill Catalog`) — plan line numbers are a snapshot and drift; anchor edits on CONTENT, not line numbers |
| Raw-value drift check with `grep -qF` | Verifying each documented value with `grep -qF "$argument_hint" CLAUDE.md`, expecting all 13 to match | Reported `MISS tidy` — `tidy`'s raw value has literal pipes (`--dry-run \| --no-swarm \| ...`) that MUST be escaped as `\|` in a table cell, so the RAW form is intentionally absent from the rendered file | Drift-check documented table values against the ESCAPED form (`\|`), or normalize/strip table metacharacters before `grep -F`, or a correct edit reads as a failure |
| Guessing the markdownlint hook id | Running `pre-commit run markdownlint --files CLAUDE.md docs/plugin-installation.md` | Failed with "No hook with id `markdownlint` in stage `pre-commit`" — the real id is `markdownlint-cli2` | Never guess a pre-commit hook id: `grep -iE 'id:.*(markdown|md)' .pre-commit-config.yaml` first, then invoke the real id (here `markdownlint-cli2`) and actually RUN it before claiming green |

## Results & Parameters

The change added an **Arguments** column to the CLAUDE.md skill-catalog table with each
cell derived verbatim from its skill's frontmatter, plus argument-bearing invocation
examples in `docs/plugin-installation.md`.

| Element | Value / rule |
| ------- | ------------ |
| Source of truth per row | `argument-hint:` field in `skills/<name>/SKILL.md`, extracted verbatim |
| No-value sentinel | `—` (em dash) for skills lacking the field |
| Pipe-bearing value rendering | inner `\|` escaped inside the table cell |
| Correct plan-cited table location | drifted (~18 lines); re-anchored on `### Skill Catalog` |
| Drift-check caveat | compare vs ESCAPED form — raw `grep -qF` false-MISSes pipe values |
| Real markdownlint hook id | `markdownlint-cli2` (not `markdownlint`) |
| Verification command | `pixi run pre-commit run markdownlint-cli2 --files CLAUDE.md docs/plugin-installation.md` → Passed |

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Issue #1496 — add an **Arguments** column to the CLAUDE.md skill-catalog table (derived from each skill's `argument-hint:` frontmatter) + argument-bearing examples in `docs/plugin-installation.md` | **verified-local** — `markdownlint-cli2` (the only relevant gate for this doc-only change) passed locally via the correct hook id; CI not yet run for this change. All 13 skill values verified against their frontmatter source (12 matched raw; `tidy` matched only after accounting for escaped pipes). |
