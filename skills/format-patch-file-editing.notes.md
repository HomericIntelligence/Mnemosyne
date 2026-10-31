# format-patch-file-editing — supporting notes

Provenance: one worked session on 2026-10-24/30, delivered through durable
`learn`. Source identifiers are generalized; the failure shapes and commands
are the evidence.

## Session evidence (generalized)

Task: repair two port defects by editing stored `format-patch` files of a
vendored 25-patch series. The surgery had two parts:

1. **Insert two hunks** into one patch's file diff (an init line; two class
   methods), keep its existing nested-def removal hunk, correct the new-side
   start of the two hunks that follow, and drop obsolete rows from the same
   patch's test-file hunk with a header recount.
2. **Drop a whole file section** from another patch (stat row, its
   `diff --git` span, and the `N files changed / insertions / deletions`
   totals).

The script went through three attempts:

- **Attempt 1** — assertion failure, no edit. The exact-match block for the
  nested-def removal hunk went straight from the header into the removed
  lines, but the real hunk had three context lines (a docstring and a blank)
  in between. The block also used a guessed `+count` of 20 where the correct
  value computed from the insertion was 18.
- **Attempt 1b** — `SyntaxError`. The repair mixed implicit string
  concatenation with `+ EXPR` joins inside a parenthesized literal chain.
  Python parses `"a" "b"` but not `"a" EXPR`; the error pointed at the block
  start, which resembled a patch problem but was a script bug.
- **Attempt 3** — success. Anchors re-read with `cat -A` from the current
  file; multi-line blocks built with explicit joins and `" \n"` for blank
  context lines; hunk headers computed from the inserted lines and the
  cumulative delta (init +1, methods +15 ⇒ following hunks' new-side starts
  shifted by +15); stat row located by regex from the real file instead of a
  copied string (column padding differs per row); totals recomputed from the
  dropped section's actual `+`/`-` line counts (measured 5/11, giving
  `2 files changed, 366 insertions(+), 26 deletions(-)` from
  `3 files changed, 371 insertions(+), 37 deletions(-)`).

Validation was the replay, not the asserts:

```bash
git reset --hard <pristine-base>
git am <series>        # all 25 clean
python3 -m py_compile <each patched target>
diff -q <worktree copy> <scratch mirror copy>   # proof mirrors stayed equal
```

Two mirrors of the series existed (a worktree vendor directory and a scratch
directory); both were edited by the same script invocation and then compared
byte-for-byte.

## Header arithmetic that held

For the same file's hunks in one patch, with an import-side hunk already at
delta -1:

- init insertion `@@ -L,4 +L,5 @@`: cumulative delta becomes 0;
- methods insertion `@@ -M,3 +M,18 @@`: cumulative delta becomes +15;
- pre-existing removal hunk `@@ -N,15 +Q,6 @@`: Q must become N + 15;
- pre-existing call-site hunk after the removal (delta -9) shifts its
  new-side start by the cumulative +6.

Old-side positions never change for hunks later in the stream; only the
new-side start moves with the cumulative delta.
