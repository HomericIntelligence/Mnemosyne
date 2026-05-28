---
name: docs-contributing-md-case-clash-redirect
description: "Resolve CONTRIBUTING.md case-clash and circular cross-reference between root CONTRIBUTING.md and docs/contributing.md. Use when: (1) a repo has both CONTRIBUTING.md (root) and docs/contributing.md with a circular 'See also' mutual reference, (2) docs/contributing.md duplicates content from the root canonical file, (3) docs hygiene audit flags CONTRIBUTING case ambiguity on case-insensitive filesystems."
category: documentation
date: 2026-05-28
version: "1.0.0"
user-invocable: false
verification: verified-precommit
tags:
  - contributing
  - docs
  - case-clash
  - redirect
  - duplication
  - hygiene
---

# Docs CONTRIBUTING Case-Clash Redirect Pattern

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-28 |
| **Objective** | Eliminate circular cross-reference between root CONTRIBUTING.md and docs/contributing.md |
| **Outcome** | Success — docs copy reduced to 5-line redirect, circular reference removed |
| **Verification** | verified-precommit |

## When to Use

- A repo has both `CONTRIBUTING.md` (root, canonical) and `docs/contributing.md` (case variant)
- The two files reference each other circularly ("See also docs/…" ↔ "Canonical source is root/…")
- `docs/contributing.md` duplicates content already covered by the root file
- Case-insensitive filesystem (macOS) ambiguity would make both resolve to the same path

## Verified Workflow

> **Warning:** This workflow has been validated through pre-commit hooks only (verified-precommit) — CI-level link checking not confirmed.

### Quick Reference

```bash
# Step 1: Reduce docs/contributing.md to pure redirect
cat > docs/contributing.md << 'EOF'
# Contributing to <ProjectName>

> **Canonical source:** The root [`CONTRIBUTING.md`](../CONTRIBUTING.md) is the authoritative
> contributing guide. All setup, code style, testing, PR process, and dependency update
> instructions live there. This file is a redirect — please follow the link above.
EOF

# Step 2: Strip the "See also docs/contributing.md" back-reference from root CONTRIBUTING.md
# Remove the admonition block that points to docs/contributing.md
```

### Detailed Steps

1. **Read both files** — identify the circular reference pattern (mutual "See also" ↔ "Canonical source" pointers)
2. **Decide direction**: root `CONTRIBUTING.md` is canonical; `docs/contributing.md` is the redirect
3. **Reduce docs copy**: Replace the full content of `docs/contributing.md` with a 4-5 line redirect block containing only a heading and a blockquote pointing to the canonical root
4. **Strip the back-reference from root**: Remove the `> **See also:** docs/contributing.md` admonition from the top of `CONTRIBUTING.md` — it is now unnecessary since the docs file is a pure redirect
5. **Stage by name**: `git add docs/contributing.md CONTRIBUTING.md`
6. **Verify Markdown lint** passes before committing

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Deleting docs/contributing.md | Removing the file entirely | Breaks any inbound links from docs index | Reduce to redirect instead of deleting |
| Keeping both files with content | Leaving both files with full content | Perpetuates duplication and the circular reference problem | One must become a redirect |
| Moving content to docs copy | Making docs/contributing.md canonical instead | docs/ is secondary navigation; root is the GitHub-visible canonical | Always keep root as canonical |

## Results & Parameters

Resulting `docs/contributing.md` (5 lines):

```markdown
# Contributing to ProjectName

> **Canonical source:** The root [`CONTRIBUTING.md`](../CONTRIBUTING.md) is the authoritative
> contributing guide. All setup, code style, testing, PR process, and dependency update
> instructions live there. This file is a redirect — please follow the link above.
```

Root `CONTRIBUTING.md`: remove the `> **See also:** ...` block from the top — no other changes needed.

Commit message convention: `chore(docs): resolve CONTRIBUTING case clash and add just clean recipe`

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #630 — docs hygiene PR #667 | Pre-commit markdown lint passed |
