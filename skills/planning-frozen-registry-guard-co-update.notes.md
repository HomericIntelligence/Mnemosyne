# Notes: planning-frozen-registry-guard-co-update

Supporting evidence for the 2026-10-31 "new consumer" instance. Generalized; no
source-project identifiers.

## Guard shape observed

- The guard is a pytest module that walks the package source tree.
- Two tables: a routed-module table (each entry a module path plus a purpose phrase) and an
  exclusion table (module path plus a short rationale).
- For routed modules, every guarded call site must show the resolution seam inside a joined
  7-line window (the load line plus six preceding lines): either the seam wraps the call, or
  a `path =`/`cb_path =` assignment from the seam appears in that window.
- The tree-wide scan skips tabled modules and lines that start a definition, comment, import,
  or docstring; it fails on any other line that matches the guarded call patterns.
- Module keys in the exclusion table can carry a `#function` suffix; the scan's covered set
  splits on `#`, so the suffix documents the reason while the whole module is covered.

## Decision evidence

- The failing scan message named the new consumer module and the matched line, which made the
  classification mechanical: the module was absent from both tables.
- The consumer's deployment-facing entry point resolved the resource through the shared seam;
  only an internal cache helper read the caller-resolved path.
- Re-resolving inside the reading helper would break a cache test that injects arbitrary
  paths (tmp-directory files) and monkeypatches only the loader — the approved design's
  contract. This is the concrete reason exclusion beat restructuring.
- The fix was a five-line table registration with an at-site comment; no production code
  changed.

## Verification record

- Guard suite after the registration: 19 passed locally in under a second.
- Focused consumer suites after the registration: 124 passed, and 3 passed (cache and route
  tests).
- Project CI at the fixed head: all required checks green; the change merged the same day.
- The registration commit was the only delta between the failing head and the merged head,
  so the guard suite is the decisive evidence.
