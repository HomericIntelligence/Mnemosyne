---
name: patch-port-identity-not-correctness
description: "Verify a patch-series port or rebase onto a new upstream base when a reference (oracle) tree exists: tree identity is not runtime correctness. Use when replaying a vendor or format-patch stack onto a new release, when a byte-identical comparison to a reference tree passes, or when clean apply plus compile checks are the only validation for dynamic-language targets."
category: testing
date: 2026-10-24
version: "1.0.0"
user-invocable: false
tags: [port, patch-stack, rebase, upstream, verification, oracle-tree, symbol-completeness, name-resolution, absorbing-upstream]
---

# Patch-Port Identity Is Not Correctness

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-24 |
| **Objective** | Catch latent port defects in a patch series rebased onto a new upstream base before review shuttles or runtime finds them. |
| **Outcome** | successful: two runtime defects that survived a byte-identical oracle comparison, a clean replay, compile checks, CI, and an architecture review were found and fixed by the symbol-completeness and upstream-absorption audits below. |

A clean `git am`, a byte-identical tree comparison against a proven earlier
port, and a compile pass prove structure and identity. They do not prove that
the ported code runs. In dynamic languages, name binding happens at runtime:
a changed call site that references a symbol the port never added, or a
fragment that keeps lines that use a local the port deleted, compiles without
error and fails on the first execution. CI test suites do not help when no
test covers the patched path.

## When to Use

- You replay a maintained patch series (format-patch stack, quilt series, or
  a vendored patch directory) onto a new upstream base.
- A reference tree from an earlier port (an "oracle") exists and part of the
  sign-off is a tree-diff or byte-identical comparison against it.
- The target is a dynamic language where parse/compile checks cannot resolve
  names (for example `py_compile` on Python).
- Upstream may have absorbed some of the patched mechanisms between the old
  and the new base.
- Patch hygiene checks (clean apply, no conflict markers, no secrets) passed
  and the port feels done.

## Verified Workflow

### Quick Reference

```bash
# 1. Replay onto the pristine base; treat identity as provenance only.
git am ../patches/*.patch && python3 -m py_compile <each patched file>

# 2. Symbol completeness: every diff-added reference must be defined.
grep -o 'self\._[a-z_]*(' <file> | sort -u     # + module-level added names
grep -n 'def _name\|_name =' <tree>            # prove each definition exists

# 3. Absorption audit: diff every touched function against pristine upstream.
git diff <base> HEAD -- <file>                 # read the full per-function delta

# 4. Live callers: enumerate upstream's own callers/tests per patched function.
git grep -n '<function_name>(' -- '*.py' | grep -v '^test' ; git grep -l '<function_name>' -- 'test*'
```

### Suggested Approach

1. **Record tree identity as provenance, never as the criterion.** A
   byte-identical comparison to an earlier port tree proves only that the
   states agree. If the reference tree predates a repair, both trees share the
   same latent defects.
2. **Replay onto the pristine base and compile every patched file.** Clean
   apply plus compile is necessary, not sufficient.
3. **Run a symbol-completeness sweep.** For every name that the diff adds as a
   reference (new call sites such as `self._helper()`, new imports, new module
   globals), prove that the defining line exists in the final tree. Automated
   extraction plus grep works. Every miss is a latent `NameError` or
   `AttributeError` that type-less CI cannot see.
4. **Run an upstream-absorption audit on every touched region.** For each
   patched function, compare with the new base's version: did upstream absorb
   the mechanism (a `*_streaming` sibling, a delegate to a helper module, an
   idiom change)? A fragment ported onto an absorbed mechanism is the second
   classic defect: the port deletes a removed line but keeps lines that use
   it. Example shape that compiles and crashes when iterated:

   ```python
   def f(weights):
       # port deleted: weights_dict = dict(weights)
       # upstream's own test still calls list(f(weights))
       yield from weights_dict.items()     # NameError at runtime
   ```

5. **Verify upstream's live callers, not only your own.** Grep the pristine
   base for every caller of each patched function, including upstream's own
   tests and compatibility shims. A function your code no longer calls can
   still be called by upstream's test suite; execute those tests or step
   through the path.
6. **Decide per delta: complete, drop, or keep.** Incomplete port (references
   outnumber definitions) → complete it or revert that hunk. Absorbed
   mechanism → drop the fragment and its unused imports entirely; keep the
   byte-identical upstream version. Still-needed delta → keep. Record each
   decision and its evidence.
7. **Bound the final comparison.** After fixes, the final tree-diff against
   the oracle must be limited to an enumerated, documented set of files. A
   silent third file is a new defect.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Oracle byte-identity as sign-off | Compared the rebased tree byte-for-byte against an earlier "proven" port tree | Proved identity to a pre-repair state; two runtime defects passed review | Identity is provenance; correctness needs name-level and caller-level checks |
| Clean apply + compile as verification | `git am` succeeded and every file passed compile checks | Compile does not resolve names; both defects were syntactically valid | Add a symbol-completeness sweep for every added reference |
| Review-only audit of patches | Human architecture review of patch content, markers, and scope | Review read the fragments as small deltas and missed the dangling names | Pair the review with replay, symbol sweep, and absorption audit |
| Porting a fragment because it applies | Kept a hunk that still applied textually onto the new base | Upstream had absorbed the mechanism; the fragment left a dangling local identifier plus unused imports | Diff each touched function against upstream and choose complete/drop/keep with evidence |

## Results & Parameters

### Configuration

- `<base>`: pristine upstream commit (tag-resolved object ID, not the tag name).
- `<patches>`: the full series, applied in order with `git am`.
- Sweep target: identifiers introduced by `+` lines that the diff uses as
  callables, attributes, imports, or globals.
- Caller target: every `git grep` hit for each patched function in the
  pristine base, including `test/` trees.

### Expected Output

- All patches replay cleanly onto `<base>`; patched files compile.
- Symbol sweep: zero added references without a definition in the final tree.
- Absorption audit: a recorded complete/drop/keep decision for every delta,
  with upstream's absorbing mechanism named when dropped.
- Live callers: upstream callers/tests of each patched function enumerated and
  exercised or hand-verified.
- Final tree-diff vs the oracle: limited to a documented file set; each file
  has a recorded reason.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Engine patch-stack rebase onto a newer upstream release | ~25-patch series onto a newer base of a public open-source inference engine (2026-10-24) | Two latent defects (a referenced-but-never-defined method; a dangling local after upstream absorption) caught by the sweep and audit after identity check, CI, and human review had passed. See [notes](./patch-port-identity-not-correctness.notes.md). |

## References

- [PR rebase and conflict resolution patterns](./pr-rebase-conflict-resolution-patterns.md) — audit beyond conflict markers after combining two sides.
- [Targeted port audit with parallel reviewers](./targeted-port-audit-parallel-reviewers.md) — parity audit of a rewrite against its prior implementation.
