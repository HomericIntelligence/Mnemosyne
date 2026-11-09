# comet-source-lane-revision-rotation — privacy-safe episode notes

These notes keep the generalized production context of the verified run
behind [comet-source-lane-revision-rotation.md](comet-source-lane-revision-rotation.md).
Hostnames, user names, node names, uids, absolute deployment paths, and job
identifiers are generalized on purpose. Do not add them back.

## Verified episode (November 2026)

One canonical development source lane (comet `m2-development`, a canonical
deployment suffix `dev` over a shared public/administrative root pair) was
rotated end-to-end through the documented playbook:

1. First stage (release-lane revision pinned by the operator as
   `0dc7e7a5…`): `python3 -m comet.source_bootstrap` was used because
   `scripts/install-control-venv.sh` cannot activate a StackRelease on a lane
   whose deployment policy names more models than any release's `pools`
   records. The stage installed `venv/sources/<rev>`, the immutable prefixed
   control environment, and wrote `source-runtime.json` and
   `venv/current -> sources/<rev>`. The machine credential
   (`comet-admin keys bootstrap`) and the one-time common-domain registry
   followed (the lane-bootstrap verb is fenced to governed lanes; the
   tracked issue owns its productization, so the one-time step ran through
   the deployment principal's machine authority).
2. Rotation stage: a second run for a newer pinned revision refused first
   with `the selected source pointer conflicts with this bootstrap`, then,
   after the pointer and record moved aside, completed cleanly (partial
   `venv/sources/<new-rev>` left by one interrupted attempt was re-widened
   and removed once, matching the lesson's rule).
3. The staged `comet-admin status` matched `control_revision` to the new
   revision and the gateway answered `/health` with HTTP 200.
4. The public client selected the new lane's `gateway.json` and
   `status.json`; the administrator enrollment and the user/administrator
   claim flow were unchanged by the rotation.
5. `operator-stop --expected-release <old-sha>` refused with its
   documented manual procedure for the source layout; the operator rolled
   with the watchdog session kill (TERM forwarded; watchdog exited
   cleanly) and an identical watchdog restart, which launched the child
   from `venv/current`.
6. The gateway in-allocation restart refused with
   `deployment_context_drift` (context ID and source SHA mismatches:
   expected the new values, observed the old). The rollback finished and
   the active generation kept serving. `gateway bootstrap-reconcile`
   refused the live job (`the exact scheduler identity proof failed`).
7. The fleet owner cancelled the old allocation (a `RUNNING` job), after
   which the gate changed from `not a meeting` to records-stage
   behavior: `gateway up` refused with `the public gateway does not match
   the selected context`, and the keeper printed one
   `gateway keeper skipped one pass (accounting observation failed:
   ValueError)` line per pass. Moving `gateway-state/current.json`,
   `stack-observed/gateway.json`, the public `gateway.json` and
   `status.json`, and every `*.active-release` receipt into one labeled
   aside directory freed the fresh submission of a new gateway job. One
   blue candidate generation then activated on one fresh node; records
   republished with the new revision; the keeper state returned to
   `consecutive_failures: 0`, `pending_retry: false`.
8. Every moved byte stayed in labeled aside directories
   (`venv/current.aside-<rev>`, `source-runtime.json.aside-<rev>`,
   `keeper-records-pre-<date>/`). Nothing was deleted, and no sibling
   lane, locator record, registered context file, retirement rule, or
   root move was touched.
9. During the same window the lane carried one typed refusal surface for
   `pool-runtime status`, `pool up` (desired accepted with a typed blocked
   check that names `pool-runtime adopt`), `pool scale` (typed ceiling
   refusal at the context capacity bound), `pool restart` (accepted), and
   `pool down` (completed with an unblocked state). The pool-serving
   gates that the surface announces (the release catalog admission gate
   and the embedded-build-record adoption gate) are independent of this
   rotation playbook, so they stay out of it.

## Anchors (kept non-sensitive)

- Skill family: a source runtime via `comet.source_bootstrap` has three
  creation invariants to verify (prefix inventory, immutable modes, verifier
  and record selects), and three rotation invariants to reset (pointer,
  record, observed + public gateway records).
- The lane-bootstrap direction (`domains bootstrap`) is fenced to governed
  lanes; review the tracked productization issue before any lane needs a
  first common-domain registry.
- Typed operator stop documents its source-layout refusal inline; treat its
  output as the trigger for the manual watchdog-kill path, not as a defect.
