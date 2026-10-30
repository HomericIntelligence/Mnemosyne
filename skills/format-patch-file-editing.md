---
name: format-patch-file-editing
description: "Edit git format-patch output or a vendored .patch file programmatically without corrupting the series: anchor on real bytes, keep the space prefix on blank context lines, recompute downstream hunk headers and stat totals after every insertion or deletion, and validate by full git-am replay. Use when you must insert, remove, or drop hunks or whole file sections in stored patch text."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags: [format-patch, patch-editing, hunk-headers, git-am, vendor-patches, string-anchors, replay-validation]
---

# Format-Patch File Editing

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Apply scripted edits to stored `format-patch` text (insert or remove hunks, drop a whole file section) so the series still applies with `git am` and produces the intended tree. |
| **Outcome** | successful: a two-defect patch surgery on a vendored 25-patch series passed full replay after two string-built attempts failed on anchor accuracy; the replay, not the asserts, was the gate. |

A `.patch` file is not free text. Hunk headers, context lines with an exact
space prefix, per-file stat rows, and change totals are interlinked values.
A sed- or string-based edit that addresses one part and not the others
produces a file that reviewers read as sane and `git am` rejects, or worse,
applies at an offset.

## When to Use

- You must restructure stored patch text: insert new hunks into an existing
  file diff, remove lines from a hunk, or drop a whole `diff --git` section.
- You build the edit with string anchors (script, structured editor, or a
  LLM-generated replacement block) rather than an interactive rebase.
- The result must pass `git am` onto a pinned base, byte-for-byte for every
  span not under edit.
- Several in-flight copies of the series exist (a worktree plus a scratch
  mirror) that must receive the same edit.

## Verified Workflow

### Quick Reference

```bash
# 1. Anchor on real bytes, re-read after each earlier edit in the batch.
sed -n 'A,Bp' file.patch | cat -A          # never anchor from remembered line ranges

# 2. Blank context lines are a space, not empty.
grep -n '^$' -m1 file.patch | head -1      # expect zero hits inside diff spans

# 3. Validate by replay, not by string asserts.
git reset --hard <pristine-base> && git am path/to/*.patch

# 4. Mirror the edit to every in-flight copy; prove identity.
diff -q worktree/copy.patch mirror/copy.patch
```

### Suggested Approach

1. **Anchor on real bytes every time.** Read the exact region with `cat -A`
   after any earlier edit in the same script moved line numbers. Anchors
   built from remembered offsets or partially shown diffs miss context lines
   (a hunk header is followed by its context, not by the changed lines) and
   fail as exact-string matches.
2. **Keep the space prefix on blank context lines.** Inside a diff, a blank
   context line is `<space>` + newline. Strings you build with `\n` alone
   break exact matching and produce diffs some consumers tolerate only with
   fuzz. Match git's own output.
3. **Recompute interlinked values after each edit.**
   - An inserted hunk shifts the **new-side start** of every following hunk
     in the same file by the cumulative delta; old-side positions do not
     change. Git treats numbers as hints, but correct values keep
     format-patch tooling, review, and `apply --check` behavior predictable.
   - Removing added (`+`) lines from a hunk reduces that hunk's `+count`;
     removing context changes both counts.
   - Dropping a file section removes its stat row and adjusts the
     `N files changed, X insertions(+), Y deletions(-)` totals.
4. **Mind Python string mechanics for multi-line anchors.** Implicit string
   concatenation (`"a" "b"`) does not combine with `+` expressions inside a
   parenthesized literal chain; build each block by explicit joins. A
   `SyntaxError` here is a script bug, not a patch property.
5. **Validate by replay, never by asserts.** String asserts only prove the
   script saw what it expected. The gate is `git am` of the full series onto
   the pristine base, compile of every affected target file, and the known
   semantic checks for the edit (for example symbol existence when the
   surgery completes an incomplete port — see the linked identity-vs-
   correctness skill).
6. **Mirror the edit to every copy and diff the results.** Duplicate the
   change across the worktree and scratch copies mechanically; then prove
   byte-identity between them. Drifted mirrors re-export into different
   series later.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Anchor from remembered line ranges | Built an exact-match block for a hunk from a partial earlier read | The hunk had context lines between its header and changed lines that were not in the anchor; the assert fired with no edit applied | Read the exact region with `cat -A` immediately before scripting; re-read after earlier edits shift lines |
| `sed -n 'A,Bp'` regions after edits | Displayed regions using pre-edit line numbers | Earlier edits in the same batch moved content, so the shown span was the wrong lines | Re-measure positions in the current file; never reuse stale line numbers |
| Implicit-concat chains with expressions | Mixed `"literal"` runs with `+ EXPR` inside one parenthesized string | Python rejects the mix; the script died before any edit | Build multi-line blocks with explicit joins; treat a syntax error as a script bug to fix before touching patch text |
| Wrong header arithmetic by hand | Guessed an inserted hunk's `+count` and a following hunk's new-side start | Off-by-N headers; replay would apply at offsets or reject | Compute counts from the inserted/removed lines and the cumulative delta; verify with replay |

## Results & Parameters

### Configuration

- `<pristine-base>`: the exact object ID the series applies onto.
- Replay gate: `git reset --hard <pristine-base> && git am <series>` then
  compile each affected file; the replay must be clean and the final tree
  must satisfy the semantic checks of the edit.
- Mirror check: `diff -q` every copy of each edited patch file.

### Expected Output

- Every in-flight copy of the series is byte-identical to its siblings.
- `git am` applies the full series without offsets or failures.
- Stat headers match the actual delta (`git apply --stat` cross-check when
  the totals were edited).

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Vendored patch-series surgery | 25-patch series, 2026-10-30 session evidence | Inserted two hunks, corrected two downstream hunk headers, dropped a file section plus its stat row and totals, removed test rows with a header recount; two string-built attempts failed on anchors, the third passed full replay. See [notes](./format-patch-file-editing.notes.md). |

## References

- [Patch-port identity is not correctness](./patch-port-identity-not-correctness.md) — replay is the gate; pair mechanical correctness with symbol and caller audits when the surgery changes ported code.
- [Cross-repo git history with format-patch replay](./tooling-cross-repo-git-history-format-patch-replay.md) — moving files across repos with provenance.
