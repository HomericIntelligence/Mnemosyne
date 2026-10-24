# patch-port-identity-not-correctness — supporting notes

Provenance: one worked session on 2026-10-24, delivered through durable
`learn`. Source identifiers are generalized; the failure classes and the
verification shape are the evidence.

## Session evidence (generalized)

Context: a maintained patch series (~25 stacked format-patch commits) on a
vendored engine was rebased from an old fork pin to a much newer upstream
release tag. Verification before the defect discovery:

- The final patched tree compared **byte-identical** to a tagged "oracle" tree
  from the earlier port pipeline.
- The series applied cleanly with `git am` onto the pristine base.
- Every patched file passed `py_compile`.
- Repository CI (build, lint, full test matrix, policy checks) was green.
- An architecture review of the whole delta returned GO with no blockers.

Two defects survived all of that:

1. **Referenced-but-never-defined port.** One patch changed a call site from a
   locally nested (decorator-wrapped) function to a cached getter method,
   `self._get_impl()`. The getter and its backing method were never added to
   the class; `py_compile` passed because the reference is just an attribute
   read until runtime. The patch's own test parametrized the names of the
   missing getter, its implementation, and its cache attribute — reading the
   patch's test rows against the class surface exposed the incompleteness
   immediately. At the new upstream base, half of the old two-part
   optimization was obsolete (upstream's method now delegates to a helper
   module), so the fix completed the still-needed half and removed the
   obsolete half from the patch's test.
2. **Vestigial fragment over an absorbed mechanism.** A second patch rewrote
   the body of a function whose mechanism upstream had absorbed into a
   `*_streaming` sibling. The ported fragment deleted the line that defined a
   local mapping but kept the trailing `yield from mapping.items()` — a
   diameter of one line, syntactically valid, referenced by nobody in the
   product code path. Upstream's own loader unit test was a live caller:
   `list(_legacy_fn(weights))` would raise `NameError` the first time that
   test ran in an environment with the patch applied. Correct fix: drop the
   entire per-file section from the patch (also removed a now-unused import),
   restore the function to byte-identity with upstream, and update the
   patch's stat header.

## Why the usual gates did not catch it

- Tree identity proved the replayed tree matched the earlier machine of
  record — which itself was pre-repair. Identity is transitive; correctness
  is not.
- `py_compile` parses and byte-compiles; it never resolves attribute or free
  names.
- CI tests did not cover the patched paths (the product's own patched-model
  integration tests run only in the build environment), and upstream's caller
  is in the vendored engine's test tree, outside the product's CI.
- The architecture review assessed the delta structurally (paths, markers,
  scope, decisions) and its content-level spot checks verified claims about
  the base, not the ported bodies.

## The working verification loop

1. `git am` the full series onto a scratch checkout pinned to the pristine
   base object ID.
2. `py_compile` each patched file (cheap gate, not the answer).
3. For every patched file, print the per-function delta against the base and
   read each touched function's final body in full — this is where both
   defects were visible in seconds once someone looked.
4. Symbol sweep: extract added references (`self._name(`, new imports, new
   module names) and grep the final tree for matching definitions; zero
   misses required.
5. For dropped/kept decisions, grep the pristine base for callers —
   including `test/` — of every patched function, and map each to a run or a
   hand-verified path.
6. Re-diff the final tree against the oracle tree; require the difference
   file set to equal the documented decision list.

Each fix in the session was validated by replaying all patches onto the
pristine base again (clean apply), compiling, re-running the sweep, and
enumerating the final tree-diff. Only then were the fixes committed.
