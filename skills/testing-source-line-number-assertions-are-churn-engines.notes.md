# Supporting evidence

A test-maintenance change required numeric source citations to move after an
unrelated source edit. Two tests used source positions or citation bounds
instead of observable product behavior.

The maintainer requested their removal. The removal retained functional
safety tests, passed repository checks, and merged. A separate request
asked the review system to reject this class of test. That request is not
evidence that automated enforcement has been implemented.

The prior knowledge entry recommended symbol-presence replacements and
treated an empty test selection as a pass. Those instructions do not
preserve a behavior contract or prove that validation ran.

The amendment keeps the verified removal rule and adds the missing
decision boundaries. A parser diagnostic can legitimately report a line.
An implementation file does not acquire a fixed-line contract merely
because a test records its location.

This record omits project identifiers, private paths, source code, raw
logs, and operational measurements. It records no synthetic test result.
