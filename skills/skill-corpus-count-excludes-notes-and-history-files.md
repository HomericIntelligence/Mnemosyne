---
name: skill-corpus-count-excludes-notes-and-history-files
license: BSD-3-Clause
description: "Use when: (1) counting the number of skills in the tracked corpus, (2) auditing per-category skill counts, (3) any script or agent step that measures corpus size with ls/find/git ls-tree on the skills/ directory. Naive *.md globs silently include .notes.md companion files and inflate counts by ~57%."
category: tooling
date: 2026-05-19
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: ["skill-corpus", "counting"]
---

# Skill Corpus Count Excludes Notes and History Files

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-19 |
| **Objective** | Count the real number of skills in `skills/` without inflating by `.notes.md` or `.history` companion files |
| **Outcome** | Successful — canonical one-liner identified and verified against ground-truth corpus of 693 skills |

## When to Use

Apply this skill whenever you need an accurate count of skills in the corpus:

- Before and after consolidation sessions to verify corpus size changed as expected
- In orchestrator scripts that compute per-category breakdowns
- In CI validation steps that check corpus size thresholds
- When an agent reports a suspiciously large corpus count (naive glob inflates by ~57%)
- When writing or reviewing any script that enumerates `skills/*.md`

## Verified Workflow

### Quick Reference

```bash
# Canonical: count only real skill files, not companion files
ls skills/*.md | grep -v -E "\.notes.*\.md$|\.history.*$" | wc -l

# Alternative using find (safer with spaces in filenames)
find skills/ -maxdepth 1 -name "*.md" ! -name "*.notes*.md" ! -name "*.history*" | wc -l

# Alternative using git (counts only committed files)
git ls-tree -r HEAD -- skills/ | awk '{print $NF}' | grep "\.md$" | grep -v -E "\.notes.*\.md$|\.history.*$" | wc -l

# Per-category count (exclude every notes/history companion before grepping)
for f in skills/*.md; do [[ "$f" == *.notes*.md || "$f" == *.history* ]] && continue; grep "^category:" "$f"; done | sort | uniq -c | sort -rn
```

### Detailed Steps

1. Understand the three file types that coexist in `skills/`:
   - `<name>.md` — the actual skill document (counts toward corpus size)
   - `<name>.notes*.md` — raw session notes companion files (do NOT count)
   - `<name>.history*` — changelog snapshots (do NOT count)

2. Always exclude `*.notes*.md` and `*.history*` (with `grep -v` or `find ! -name`) from any enumeration of `skills/*.md`.

3. When doing per-category audits, filter out notes and history files before piping to `grep "^category:"` — companions can inherit a `category:` frontmatter line from their sibling and will double-count skills.

4. If using `git ls-tree`, apply the same notes/history filters after selecting `.md` files.

5. Cross-check: `find skills/ -maxdepth 1 -name "*.notes*.md" | wc -l` should be close to the number of skills (every skill may have a companion); `find skills/ -maxdepth 1 -name "*.history*" | wc -l` is typically smaller.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | `ls skills/*.md \| wc -l` | Returned 1,089 — silently included all `.notes.md` companion files; inflated by ~57% | Always exclude `.notes*.md` (and `.history*`) with companion filters |
| 2 | `find skills/ -name "*.md" \| wc -l` | Same problem — `*.md` glob matches `.notes.md` too | The `.notes.md` extension is a double-extension; standard `*.md` globs catch it |
| 3 | `git ls-tree -r HEAD -- skills/ \| grep "\.md$"` | Still includes `.notes.md` because they end in `.md` | Tree-level enumeration has the same trap |
| 4 | Per-category audit without companion filters | Inflated category counts by ~57% — companions can inherit a `category:` frontmatter line from their sibling | Per-category counts must also exclude notes and history companions |

## Results & Parameters

### Configuration

No configuration required — this is a one-liner shell pattern.

```bash
# Correct corpus count
CORPUS_SIZE=$(ls skills/*.md | grep -v -E "\.notes.*\.md$|\.history.*$" | wc -l)
echo "Real skill count: $CORPUS_SIZE"

# Breakdown by category (correct)
for f in skills/*.md; do
  [[ "$f" == *.notes*.md || "$f" == *.history* ]] && continue
  grep "^category:" "$f"
done | sort | uniq -c | sort -rn
```

### Expected Output

- `CORPUS_SIZE` reflects only actual skill files
- The companion filters remove notes and history files from the count
- Naive `ls skills/*.md | wc -l` will be approximately 1.57x the real count when every skill has a `.notes.md` companion
- A mismatch between naive count and filtered count is a reliable signal that `.notes.md` files are present

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Mnemosyne | 2026-05-19 second-pass consolidation session (epic #1823) | Real corpus = 693 skills vs naive count of 1,089; .notes.md = 396, .history = 96 |

## References

- [Epic #1823 — second-pass consolidation](https://github.com/HomericIntelligence/Mnemosyne/issues/1823)
- [AGENTS.md — Skill Standards](../AGENTS.md)
