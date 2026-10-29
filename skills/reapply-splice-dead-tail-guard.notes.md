# Notes: reapply-splice-dead-tail-guard

Supporting evidence for [reapply-splice-dead-tail-guard](./reapply-splice-dead-tail-guard.md).
Identifiers are generalized; the pattern, measurements, and repair are complete.

## Case

During a conflict-free re-application of a test hunk into a long pytest
module (~3800 lines, 138 test functions), a new deferral test was spliced in
by replacing the `def` line of the existing test that followed it. The
existing test's body (settings construction and policy assertions) became
dead tail code of the new test.

Evidence measurements in the affected environment:

- Definition count before the re-apply: 138. After the re-apply: 138.
  Expected with one added test: 139.
- A name search for the existing test found no `def` anywhere in the tree.
- The full behavior suite over the module passed green (hundreds of tests),
  because the absorbed assertions still executed inside the new function.
- Restoration was two lines: one blank line and the absorbed `def` line.
  After restoration the module counted 139 and stayed green.

A reviewer then rewrote the same branch externally (same author account,
different session) without the unpublished review's finding. The rewrite
repeated the same splice, and the shipped merge removed the test from the
target branch. The absorbed assertions still execute there under the wrong
name, which confirms the failure mode end-to-end: no green gate saw the loss
at any stage.

## Decision branches the case adds

1. **Constant count with one intended addition.** The count staying constant
   when one definition was added distinguishes absorption from a correct
   edit. This is the primary signal in this lesson.
2. **Green suite as counter-evidence.** Pass/fail and coverage both stay
   green across the splice, because the absorbed statements still execute.
   Any verification plan that treats execution as sufficient proof of
   structural integrity is blind here.
3. **Cheap repair.** When caught, restoration is the absorbed `def` line
   plus separating blank lines. Delay makes later edits build on the wrong
   attribution and raises repair cost.

## Boundaries

- The guard counts top-level definitions that match the module's naming
   convention. Parametrization, fixtures, and class-based suites need a
   pattern that matches that suite's definition shape (for example
   `^class Test` or `^    def test_`).
- The guard does not replace execution. It supplements execution with a
   structural fact that execution cannot see.
- The related whole-file failure mode — replacing a destination file with
   another ref's content and reverting unrelated work — is covered by
   `checkout-other-ref-silent-file-clobber`. This lesson covers the
   intra-file boundary, not whole-file replacement.

## Provenance

- Source session: an implementation-review cycle on an internal pull request,
  2026-10-26/27. The splice was found by a testing-dimension review through
  the module definition count, repaired before publication of the review,
  repeated by an external rewrite of the same branch, and observed shipped.
- Privacy review: all repository, path, pull-request, and issue identifiers
  are omitted. The measurements (138/139, two-line repair, ~3800-line module)
  are kept because they carry the decision value.
