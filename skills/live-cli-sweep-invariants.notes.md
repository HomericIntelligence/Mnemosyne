# Notes: live-cli-sweep-invariants

Privacy-safe supporting evidence for the main entry. Identifiers that could name
the product, the deployment, the repository, or the issues are generalized away.

## Source engagement

A 46-case live acceptance sweep over a public CLI, run against a production
deployment with an ordinary-user credential, across three days (2026-11-11 to
2026-11-13). Two independent review rounds reviewed the sweep; round 1 returned
NO-GO with two blocking findings, round 2 returned GO after one code fix.

## Evidence for each invariant

### Closed inventory

- Round 1 of review found a case body that was absent from the case listing, so
  the run executed 47 bodies while the listing showed 46.
- The same round found a group name that matched zero case ids; selecting it
  exited zero with an empty summary — a false green selector.
- The repair renamed groups to case-id prefixes, added the missing id, and
  compared the listing to the bodies mechanically; round 2 verified 46 ids and
  46 bodies, one each.
- A related selector defect: selecting a single case that depends on state
  gathered by an earlier case (a batch identifier from a list case) always
  reports SKIP, because the dependency case did not run in that selection.

### One verdict per hang

- Round 1 reproduced a double report with a hanging fake client and a 2-second
  timeout on a mutate-gated case: the runner printed the `[timeout]` FAIL, then
  the case body read exit code 124 and printed a second FAIL.
- After the one-line guard, the same repro printed exactly one FAIL line
  (`pass=1 fail=1 skip=0`).
- The repaired sweep had 23 raw case bodies; all 23 start with the guard. Three
  shared helpers start with the guard as their first statement.

### Mutation gate

- Round 1 found five unguarded mutating invocations: two retry calls that
  re-submit failed requests, one quota reconcile that changes counters, one
  submit that creates a batch, and two donation verbs that change an active
  donation.
- Each was gated behind the explicit flag with a skip reason that names the
  consequence, and the listing marks the gated cases.
- The read-only default run then reported 9 skips out of 46 cases; the 3
  failures were exactly the 3 non-gated known-defect cases.

### Negative control

- The vacuous helper: the pattern-argument position in a `grep -qF` wrapper was
  wrong, so every pattern matched every file. Symptom: a model-name case
  reported the 401-credential branch while its exit code was 0.
- The negative control (a model alias that cannot appear in the served list)
  reported `FAIL missing expected text` after the fix, and PASS before it.
- A full run against a do-nothing fake client produced failures on every case
  that asserts content — a second proof that the assertions are live.

## Recorded results of the repaired sweep

- Read-only run against the published client: 34 pass, 3 fail, 9 skip, exit 1.
  The 3 failures were the 3 open known-defect cases, each reported with its
  issue number in the detail.
- One service-side change mid-session (a served model removed from the list)
  made the model cases fail on the missing expected alias. That is correct
  behaviour, not a sweep defect; pick served models at run time.
- Exit codes verified: 0 clean, 1 failure, 2 usage (unknown selector,
  non-executable client, invalid model characters).

## Delivery notes

- The sweep lives in the product repository; this entry is the generalized
  rule. The product artifacts are not linked here on purpose.
- The lint gate on the delivery of the product PR flagged a missing trailing
  newline; the same fix was recorded in a commit so the check passed on review.
- Review flow that worked: fresh independent context per round; the author
  session publishes the review text and applies the verdict label.
