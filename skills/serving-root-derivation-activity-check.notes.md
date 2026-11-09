# Notes: Serving-Root Derivation Activity Check

Supporting evidence for `serving-root-derivation-activity-check.md`. Repository names, file
paths, issue and pull-request numbers, account names, and environment-variable names are
generalized. The roles and the failure chain are preserved.

## Source context

A planning round for a feature in a public multi-deployment GPU gateway. The feature changes
the accepted input directory for batch submission. That directory was a container mount
string. The new directory is a path that the gateway derives from the administrative root of
its resolved deployment context and from the identity of the requesting account. The gateway
has three deployments: a production deployment, a main deployment, and a development
deployment. A supervisor renders the context values into each child process of the gateway.

The premise checks confirmed the code anchors, the derived suffix rule, and the recorded
owner decision. The two findings below came from reading the installer and the directory
opening code, not from the tests.

## Evidence chain

| Link | Source-derived fact | Effect on the plan |
| ---- | ------------------- | ------------------ |
| Renderer and reader | The serving entry point reads the deployment context once at start. It copies the administrative root and the deployment suffix into one runtime configuration record | The derived path is correct in source. It stays inactive in an active job until the job runs the new executable. |
| Activation surface | The repository contains general supervision and installer entry points. It has no step that replaces the executable of an active job for this change | The plan must name a restart or re-render operation, or state that the behavior is not active in deployment. |
| Protected parent | The deployment directory below the administrative root has a mode that permits entry only from the service account. The installer opens each path component and does not follow a directory symlink | The installer cannot create a directory below it with a mode that admits writes by ordinary users. |
| Required writable target | Each user must create files below a leaf with that user name | The derived path stays empty for every user until an operation with the correct privileges creates the group-writable level. |

## Corrective plan changes

- Add an explicit activation step with an owner: the code change in the installer, or a
  named operator command. Do not write an acceptance criterion that no named step can
  satisfy.
- State the mode and the owner of each created directory: a group-writable level for the
  account leaves, and a leaf that only the matching account can create below it.
- Keep the code change and the tests. Mark the deployed behavior as unverified until the
  activation step runs.

## Duplicate-analysis record

Corpus inspection at revision `d33ae7500bbfe9fe029b606420bcdd1708692fb3`. The upstream
refresh verified. The listing helper returned the full bounded main-skill list. The
nearest entries and their boundaries:

- `pr-review-deployed-composition-error-contract` — the nearest entry. Its intent is a
  review check that a composition delivers a contracted error status. One of its inputs is
  the spawn-time environment. It has no rule for a path that a new feature adds, no rule for
  the activation surface of a new executable, and no rule for a protected parent that blocks
  directory creation. Its workflow is a raise-inventory and catch-set audit. It cannot
  produce the two plan changes recorded here.
- `deployed-version-runbook-goal-feasibility` — checks that operator directions can reach a
  goal on one deployed version. It has no directory creation, mode, or ownership rule.
- `live-hotfix-content-addressed-identity-rotation` — states that an edit alone never reaches
  a running process, in one line inside a hotfix rotation workflow. It has no planning gate
  and no permission check.
- `supervised-restart-stale-worker-state-guard` — classifies left-over entries in a shared
  state directory during a restart. It has no derivation or permission rule.
- Planning-family entries, including `pre-implementation-plan-review-wave` and
  `implementation-plan-process-helper-risk-capture` — general plan review. None reads an
  installer for directory entry permissions or names an activation surface for a
  start-time value.

Open pull requests that change flat `skills/*.md` artifacts: none at inspection time.

Disposition: `create`. The trigger is a planning round for a start-time value in a
deployment-rendered service. The failure mode is a correct source change that stays inactive
and a target directory that no reachable account can write. Neither the nearest review entry
nor the deploy entries owns that decision.

## Verification limits

The source reading is complete. The change is not implemented, so the activation surface and
the directory mode are planned, not observed. Mark any claim about deployed behavior as
unverified until an activation run supplies evidence.