# Notes: pr-base-contract-pin-binding

Supporting evidence for the main skill. Identifiers are omitted under the
privacy rules.

## Incident chronology (2026-10-31)

1. An automation program delivered a small cross-repository change: 15 files
   with about +1323/-98 lines. The change belongs on the producer
   repository's integration branch. The consuming repository's contract pins
   that branch to an exact commit.
2. The delivery lane opened the pull request on the producer's default
   branch. The lane had no base gate, and the default branch is the usual
   base in one-repository work.
3. The default branch had run far ahead of the pinned integration branch.
   The pull request presented the whole divergence: about 880 files and
   +157k lines. The presented change set did not equal the intended change
   set.
4. The retarget to the pinned integration branch returned the pull request
   to the intended 15 files and +1323/-98. The review then proceeded on the
   intended change.

## Why the default-branch signal misleads

Repository defaults answer "which branch integrates most often here". A
contract pin answers "which branch state does the consumer bind". They agree
for one-repository work and diverge for a two-repository delivery where the
consumer freezes the producer at an exact commit. The lane must read the pin
before the push, because the producer's own settings never show the pin.

## Why the preview gauge works

The wrong-base failure shows as size, not as an error. The pull-request
preview against the pinned base gives the exact same numbers the review will
present. A preview far above the intended change set can only mean a wrong
base or a contaminated branch. Both stop the open.

## The retarget correction

A retarget after the open is recoverable: the file set returns to the
intended change set. It still costs a review binding round, CI runs against
the wrong base, and a correction record in the pull request. The two checks
before the open cost one fetch and one preview each.

## Limits

- Evidence comes from one two-repository delivery with one retarget. The
  numbers are the measured values of that case.
- The pin source in the case was a consumer-side contract record. A delivery
  under a different contract shape (a manifest, a promotion pin, or a
  submodule pin) uses the same rule with its own pin source.
