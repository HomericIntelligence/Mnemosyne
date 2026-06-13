---
name: ci-gitignore-claude-coordinator-files
description: "Claude automation coordinator files (.claude-address-review-*.md, .claude-prompt-*.md, .claude-followup-*.md) must be gitignored to prevent markdownlint CI gate failures. Use when: (1) CI fails with 100+ markdownlint violations on a .claude-*.md file, (2) adding a new Claude coordinator file pattern to the automation loop, (3) diagnosing mysterious lint failures on a PR branch caused by an accidentally-tracked automation scratch file."
category: ci-cd
date: 2026-06-13
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [gitignore, markdownlint, claude-code, coordinator-files, address-review, lint-gate, pre-commit, automation-loop, ci-failure]
---

# CI: Gitignore Claude Automation Coordinator Files

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Prevent Claude automation coordinator files from being committed and breaking the markdownlint CI gate |
| **Outcome** | Successful — adding `/.claude-address-review-*.md` to `.gitignore` and removing the tracked file resolved 142+ markdownlint violations on ProjectHephaestus PR #1292 |
| **Verification** | verified-ci |

## When to Use

- When CI fails with markdownlint violations on a `.claude-address-review-*.md`, `.claude-prompt-*.md`, or `.claude-followup-*.md` file
- When adding a new type of Claude automation coordinator file pattern that will be created at runtime by the automation loop
- When diagnosing unexplained lint failures on a feature branch (check `git ls-files | grep '\.claude-'`)
- When the automation loop creates new scratch file types that get accidentally tracked by git

## Verified Workflow

### Quick Reference

```bash
# 1. Confirm a coordinator file is tracked
git ls-files | grep '\.claude-'

# 2. Add missing pattern to .gitignore (two-fold fix required)
echo "/.claude-address-review-*.md" >> .gitignore

# 3. Remove already-committed file from git index (without deleting local file)
git rm --cached .claude-address-review-*.md 2>/dev/null || true

# 4. Verify git now ignores the file
git check-ignore -v .claude-address-review-1179.md
# Expected: .gitignore:N:/.claude-address-review-*.md  .claude-address-review-1179.md

# 5. Commit and push
git add .gitignore
git commit -S -m "fix(ci): gitignore claude address-review coordinator files"
git push
```

### Detailed Steps

1. **Diagnose the failure** — CI lint job shows a cascade of markdownlint violations on a `.claude-*.md` file:

   ```text
   .claude-address-review-1179.md:12 MD033/no-inline-html Inline HTML [element: NONCE]
   .claude-address-review-1179.md:45 MD034/no-bare-urls Bare URL used
   .claude-address-review-1179.md:67 MD031/blanks-around-fences Fences should be surrounded by blank lines
   ... (142+ violations total)
   ```

   A 100+ violation count on a single file is a strong signal that the file is a machine-generated scratch file, not a human-authored document.

2. **Confirm the file is tracked** — check whether git is tracking it:

   ```bash
   git ls-files | grep '\.claude-'
   # OR
   git status | grep '\.claude-'
   ```

   If tracked (no `??` prefix in `git status`), both steps are required: `git rm --cached` AND `.gitignore`.

3. **Identify which coordinator file patterns are already in `.gitignore`**:

   ```bash
   grep 'claude' .gitignore
   # May show: /.claude-prompt-*.md, /.claude-followup-*.md
   # If /.claude-address-review-*.md is missing, add it
   ```

4. **Add the missing pattern** to `.gitignore`:

   ```bash
   echo "/.claude-address-review-*.md" >> .gitignore
   ```

   Use a leading `/` to anchor to the repo root (these files are only ever created at the root by the automation loop).

5. **Untrack the already-committed file** from the git index:

   ```bash
   git rm --cached .claude-address-review-*.md 2>/dev/null || true
   # This removes the file from tracking without deleting it from disk
   ```

6. **Verify the ignore took effect before committing**:

   ```bash
   git check-ignore -v .claude-address-review-1179.md
   # Expected: .gitignore:N:/.claude-address-review-*.md  .claude-address-review-1179.md

   git status | grep '\.claude-address-review'
   # Expected: (nothing — file should now be ignored)
   ```

7. **Commit and push** both changes together:

   ```bash
   git add .gitignore
   git commit -S -m "fix(ci): gitignore claude address-review coordinator files"
   git push
   ```

8. **Verify CI passes** — the lint gate should no longer report markdownlint violations on coordinator files.

## Why Coordinator Files Break Markdownlint

Claude automation coordinator files (e.g. `.claude-address-review-*.md`) are machine-generated scratch files consumed by the automation loop. They contain:

- **NONCE tags**: `<!-- NONCE: abc123 -->` — HTML comments in specific contexts trigger MD033 (no-inline-html)
- **Reference-link bracket placeholders**: `[FINDING_ID]`, `[THREAD_URL]` — trigger MD052 (reference-links-images) when not resolved
- **Bare URLs**: unformatted issue/PR links trigger MD034 (no-bare-urls)
- **Unspaced fences**: code blocks without surrounding blank lines trigger MD031/MD032
- **Raw HTML elements**: template anchor tags trigger MD033 (no-inline-html)

These files are consumed by the automation loop and are NEVER intended for git history or human readers. The correct fix is always gitignore, not adding markdownlint exceptions.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Adding markdownlint per-file exceptions | Tried to suppress specific rules for coordinator files in `.markdownlint.yaml` | Files have too many violation types (142+); exception list would need to enumerate a dozen rule IDs | Gitignore is the correct fix — these files should never be committed in the first place |
| Deleting the file without gitignoring | Removed `.claude-address-review-1179.md` from the branch | Next automation run re-created the file and it got staged and tracked again on the next commit | Both steps required: `git rm --cached` to untrack AND `.gitignore` to prevent re-tracking |

## Results & Parameters

The complete set of Claude coordinator file patterns that should be in `.gitignore` for any repo running the HomericIntelligence automation loop:

```gitignore
# Claude Code automation coordinator files — machine-generated scratch, never commit
/.claude-address-review-*.md
/.claude-prompt-*.md
/.claude-followup-*.md
```

**Pattern anchoring**: Use a leading `/` (e.g. `/.claude-address-review-*.md`) to anchor to the repo root. The automation loop creates these files at the repo root only. Anchoring prevents accidentally ignoring legitimate files in subdirectories.

**Relationship to `.claude-prompt-*.md` and `.claude-followup-*.md`**: Those two patterns were already fixed in ProjectHephaestus before this issue arose. The `address-review` pattern was missed. Any new coordinator file type added to the automation loop should be added to `.gitignore` at the same time it is introduced to the codebase.

**Detection heuristic**: If CI reports 50+ markdownlint violations on a single `.claude-*.md` file, it is almost certainly a coordinator scratch file that slipped into the index. The violation count is diagnostic — human-authored Markdown rarely exceeds 10 violations.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PR #1292 (issue #1179) — 142+ markdownlint violations from accidentally-tracked `.claude-address-review-1179.md`; CI lint gate blocked merge | Adding `/.claude-address-review-*.md` to `.gitignore` and running `git rm --cached` resolved all violations; CI lint gate passed |
