# Notes: Broad Handler Split, Subclass Classification Order

Supporting evidence for `handler-subclass-classification-order`. The main entry carries the rule.
These notes carry the observed shapes, the review findings, and the verification limits.

## Session evidence (generalized)

A planning round proposed cause-specific messages for one diagnostic CLI operation. The handler
already echoed the exception type and a redacted message, and printed one fixed tail for every
failure. A reviewer rejected the revision with three findings:

1. **Branch order.** The proposed transport branch matched before the "accepted, no reply"
   subclass. The subclass derives from the transport base class, so the plan would have reported a
   request that reached the service as a request that did not reach it. The subclass has its own
   supported outcome, where the caller prints only the subclass diagnostic and no generic tail.
2. **Pinned regression.** One existing test asserts the diagnostic line and the exact generic tail
   for a plain base-class exception. The plan replaced that tail and did not list the test file as
   a file to change or as a test to run. The proposed test command would have passed while the
   tree failed.
3. **Stale source premises.** The plan described two behaviors that earlier merges had already
   fixed. The reviewer cited the commits that removed them. The remaining delta was smaller: one
   dropped machine-readable code and the wording for a small set of short reads.

## Decision shape that survived review

- Keep the diagnostic line for every class.
- Replace only the tail, and only for classes whose tail is wrong.
- Leave the residual base-class branch unchanged to keep the pinned message.
- Leave the "accepted, no reply" class with no tail.
- Add one typed error for the refusal that carries the dropped code, as a subclass of the error that
  the handler already catches.
- Validate the request once, before the retry loop, and raise the usage error from outside the
  runtime handler.

## Verification limits

- Confirmed by source and test reading at one commit. No code was changed and no test was run in
  this lesson.
- The snippet in the main entry is illustrative. It shows the branch order, not a complete handler.
- Test placement, fake client injection, and test ids depend on the target repository. Read the
  existing test module before you add cases.
