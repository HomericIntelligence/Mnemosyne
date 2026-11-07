# Notes: timing oracle equalization probe review

## Source

One plan-review session. A plan proposed a dummy verifier and a count test for
a credential lookup that returned early for an unknown identifier. The review
rejected the plan before implementation. No fix, test, or mutation check ran.

## Verification limits

- The rule is a review checklist, not an executed fix.
- Compiler elimination of an unused call (step 4) is stated as a risk. The
  session did not measure it.
- Step 6 comes from standard practice for anonymous comparison probes. The
  session did not test a nonce attack.

## Supporting observations

- A digest produced by a hash function cannot equal all zeros. A fixed
  all-zero digest is therefore a marker, not a verifier that a write path
  produces.
- Human credential writes in the reviewed service wrote one class and role
  pair only. A dummy with another class and role pair did not match any stored
  entry.
- The decision path of the reviewed service had these non-secret answers:
  unknown identifier, authority unavailable, revoked, expired, and malformed.
  The plan covered the first two on one path and none on the exception path.
- The retained-snapshot decision path called the same inner function. One edit
  covered it, but the plan did not say so.

## Related entries

- `testing-non-vacuous-regression-guards-behavior-unchanged`: mutation table and
  non-vacuity for regression tests.
- `plan-verification-commands-are-dry-run-before-approval`: checks that a
  listed command can fail.