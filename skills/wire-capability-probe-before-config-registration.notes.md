# Notes: wire-capability-probe-before-config-registration

Privacy-safe session evidence. Hostnames, record paths, issue numbers, and
product names are generalized.

## Session source

- A client-installer session, 2026-11. The session wrote installer changes
  that registered a provider-qualified reference form (`<provider>/<model>`)
  for every declared model across three client harnesses.
- The deployed gateway answered a not-found error for every request in the
  new form, on all three public inference routes, while the same requests in
  the plain form answered success.
- Two independent verification passes (fresh contexts) reproduced the probe
  matrix: 12 of 12 live probes consistent — plain form success, prefixed
  form a not-found-class error on each route.
- The deployed error text did not exist anywhere in the current source tree.
  The current tree's equivalents name a retry hint and a serving-set hint;
  the deployed text named neither.
- Source cross-check: the canonicalization that accepts the new form entered
  the source line weeks before the session, and the release tags that
  contain it are newer than the deployed record's version field (0.1.x).
- The record's source digest named a same-day change on the default branch.
  The digest therefore described the record producer's revision, not the
  serving binary's revision.

## Remediation that worked

1. Restore the live client configuration to the last known-good form first.
2. File an upgrade request against the deployment owner, with the probe
   matrix as evidence.
3. Ship an adaptive probe in both installers: one minimal request per form
   against a target with live replicas; decision table as in the main
   skill; inconclusive selects the old form plus a warning.
4. Bake the decided mode into the background monitor and the refresher, so
   neither rewrites the form between user runs.
5. Re-probe on every refresh and on an endpoint move; the mode flips to the
   new form automatically after the deployment upgrades.
6. Contract tests cover both modes, both flip directions, the restore
   round-trip, and the baked-mode honor; a mock endpoint with a
   reject-prefixed knob simulates the old binary.

## Verification evidence

- Full contract test run for the installer suite passed (85 tests), plus the
  neighboring suites (63 tests).
- Isolated end-to-end runs against a local mock endpoint covered: old-binary
  rejection, acceptance, refresh flips in both directions, background
  components honoring the baked mode, and restore round-trips.
- The live machine held the old-form mode until the deployment upgrade; a
  later read-only check confirmed the deployment had not upgraded yet.
