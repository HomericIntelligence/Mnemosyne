---
name: hephaestus-interrupted-implementation-lane-recovery
license: BSD-3-Clause
description: "Recover a Hephaestus automation-loop item whose implementation agent job stopped before first publication (job timeout, external signal, operator stop). Use when: (1) the summary says RESUMABLE at implementation but the issue has no PR, (2) a relaunch dies at intake with `repository-intake requires a clean tracked tree`, (3) a relaunch dies with `BLOCKED:first_publication_discovery_failed`, (4) the implementation lane keeps changing after the loop exits, or (5) an implementer job reached its timeout with forward progress."
category: tooling
date: 2026-10-12
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - hephaestus-automation
  - automation-loop
  - implementation-lane
  - first-publication
  - run-nonce
  - zombie-session
  - intake-recovery
  - worktree
  - recovery
  - opencode
---

# Hephaestus Interrupted Implementation-Lane Recovery

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-12 |
| **Objective** | Recover an issue item that the automation loop interrupted during implementation, before any PR existed, so a fresh run converges instead of dying in intake or discovery. |
| **Outcome** | Operational. With the lane work preserved, the zombie agent session interrupted, and the durable records disposed in the correct order, each fresh run re-entered implementation and ran to its next budget decision. |
| **Verification** | verified-live: five interrupted implementer jobs on one issue recovered across ~10 loop runs; every signature below reproduced against the live intake. See [notes](hephaestus-interrupted-implementation-lane-recovery.notes.md). |

## When to Use

- The automation loop stopped an issue during implementation (job timeout, external signal,
  operator stop) and the issue has no PR yet.
- The summary says `RESUMABLE at implementation` and you must decide what the next run can reuse.
- A relaunch dies at intake with `repository-intake requires a clean tracked tree`
  (`FAIL:clone exhausted`), or with `BLOCKED:first_publication_discovery_failed` after a clean intake.
- Lane files keep changing, or a lane session stays in the agent-runtime active list, after the
  loop process exited — an implementer zombie session is writing between your recovery steps.
- An implementer job reached its timeout with verified forward progress and you must size the
  relaunch budget.
- A first-publication discovery failure shows `pending rebase directory permissions are unsafe`
  or a lane self-poisons on its own agent state files.

## Core rule: a pre-PR implementation lane cannot resume across runs

Each `hephaestus-automation-loop` run generates a fresh `run_nonce = uuid.uuid4().hex`
(`coordinator_sources.py`). For a direct item with no existing PR, the coordinator derives the
item branch as `<issue>-auto-impl-direct-<run_nonce>` and durable records bind to it. The
first-publication pre-intent check compares that bound branch and fails closed with
`ValueError("The first-publication source branch changed.")`; the summary shows
`BLOCKED:first_publication_discovery_failed`.

Consequences:

- The summary disposition `RESUMABLE at implementation` is nominal for a pre-PR item. The loop
  preserves the lane and records, but no future run can bind to them.
- A clean lane with `HEAD` equal to the receipt revision is NOT enough; a new run always has a
  new nonce. Do not spend a run attempt to discover this.
- Renaming a branch or editing records to mimic the old nonce is out of bounds; the pre-intent
  path also checks start-identity and revision records.
- Once a PR exists for the issue, this rule does not apply: discovery binds by PR instead of by
  nonce branch. Use the branch-sync guidance in
  [hephaestus-automation-loop-branch-sync-drive-green](hephaestus-automation-loop-branch-sync-drive-green.md)
  for that case.

## Signature table: identify the block first

| # | Signature | Cause | Action |
| - | --------- | ----- | ------ |
| 1 | Lane files change after the run summary prints; `<agent-api>/session/active` lists a session whose directory ends with the lane name | The implementer agent session outlives its job (timeout and external signal both reproduce) and keeps writing into the lane | Interrupt that session with `POST /api/session/<id>/interrupt`; confirm it leaves the active list. Never kill the shared agent serve daemon; other runs share it. Filter sessions by lane directory, never by recency alone |
| 2 | Relaunch dies fast at intake: `FAIL:clone exhausted ... repository-intake requires a clean tracked tree; preserve the tracked changes in <lane>, then commit or stash them` | Intake scans every registered worktree fail-closed; one dirty lane aborts the run before issue processing | Clean the lane (step P3) and relaunch |
| 3 | Relaunch dies with `BLOCKED:first_publication_discovery_failed` after a clean intake | Stale durable records from the interrupted run bind the old nonce; the new run's nonce differs | Full record disposition (step P4), then relaunch |
| 4 | Discovery fails with `pending rebase directory permissions are unsafe` | The clone common dir (`.git`) or the source-workspaces state dir is group-writable; ownership checks require owner-only write | `chmod 755` the clone common dir and the source-workspaces dir |
| 5 | Discovery fails after lane creation because a `git status` inside the lane shows its own state files | The run's state dir (`DEFAULT_STATE_DIR`, for example `build/`) can be created inside the lane and self-poison the cleanliness check | Add the state path (for example `/build/`) to the clone common dir `info/exclude` |

## Verified Workflow

### Quick reference: disposition sequence

```bash
# P1. Interrupt the surviving implementer session (signature 1), then verify:
POST /api/session/<lane-session-id>/interrupt
GET  /api/session/active            # confirm the lane session is gone

# P2. Preserve the interrupted work. Preferred: a signed WIP commit on the lane's
#     nonce branch; the retained branch keeps the commit reachable after lane removal.
git -C <lane> add -A && git -C <lane> commit -s -m "wip: interrupted implementer round"
#    Fallback for small remnants: a stash survives worktree removal (refs/stash lives
#    in the common dir).
git -C <lane> stash push -u -m "interrupted implementer round"

# P3. Leave the lane pristine for intake:
git -C <lane> status --porcelain    # must print nothing

# P4. Archive, then remove the durable records in
#     <clone-common-dir>/hephaestus-source-workspaces/ :
#       <issue>-impl.json                      (receipt)
#       <issue>-implementation-start.json
#       <issue>-implementation-start.pending.json
#       <issue>-implementation-start.reservation.json
#       pending-rebases/<issue>*
#       <issue>-impl-terminal.json             (only if present)
#     Move them to an archive directory; never delete them.

# P5. Remove the lane worktree:
git -C <clone> worktree remove --force <lane>

# P6. Probe GitHub GraphQL budget with a real call before relaunch:
gh label list --limit 1 --json name --jq '.[0].name' -R <owner>/<repo>
#     (the REST rate_limit endpoint reports a GraphQL remainder that the enforcement
#      counters do not honor; only a real query is authoritative)

# P7. Relaunch the loop for the issue. Expect this sequence:
#     intake OK -> lane created -> discovery OK -> rebase writer -> implement job claimed
```

### Suggested approach

1. Classify the item first: does a PR exist for the issue? If yes, follow the PR-bound branch-sync
   guidance instead; the nonce rule applies only to the pre-publication window.
2. Handle the zombie session BEFORE any stash, commit, or disposal step. A live implementer keeps
   writing between your steps and re-poisons the lane.
3. Size the relaunch budget from evidence, not from the failure alone. When the interrupted
   implementer made verified forward progress at its deadline (transcript activity plus changed
   files), the constraint is budget, not correctness: raise `-implementer-timeout` and retry.
   The ~1200 s default is far too small for a thinking model on a large issue; doubling per
   observed timeout with progress is a workable rule.
4. Keep every interrupted round's preservation commit on its nonce branch. The stale branches are
   harmless, and each round's work stays reachable for review or cherry-pick.
5. Never patch the automation source to "fix" resumability. The nonce binding is an intentional
   fail-closed identity guard; the operator-side disposition exists because resume is not offered.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Immediate relaunch after an operator stop | New run while the lane still held zombie-written paths | Intake died with `FAIL:clone` (signature 2) before any issue work | Clean every registered worktree before relaunch |
| Clean-lane resume attempt | Lane stashed, `HEAD` equal to the receipt revision, records retained | Died at `BLOCKED:first_publication_discovery_failed` (signature 3) | The nonce binding defeats resume even in the cleanest lane state; dispose the records |
| WIP commit without record disposal | Lane content committed, lane and records retained | Next run died again in first-publication pre-intent | Preservation is not enough; the durable records must move out of the state dir |
| Waiting out a zombie session | Expected the implementer session to end after the loop exited | The session stayed active and kept writing; it only stopped on an explicit interrupt call | An agent job timeout does not stop the underlying model session; interrupt it by API |
| Trusting the REST budget probe | `gh api rate_limit` reported large GraphQL remainder during a contention window | Enforcement-side GraphQL calls were rejected; probes that matter failed | Probe the budget with a real GraphQL call (signature in P6); REST remainder is stale under multi-run contention |

## Results & Parameters

### Configuration

- Budget escalation on observed timeout-with-progress: `--implementer-timeout 5400 -> 7200 -> 14400`;
  plumb the same reasoning through `--planner-timeout 5400` / `--reviewer-timeout 3600` for thinking models.

### Expected Output

- A disposed item's next run prints, in order: intake preparation, worktree creation,
  `discover_pending_rebase`, rebase writer, advise job, implement job — with no intake or
  discovery failure.
- The implementer now has a full fresh budget; an item that made progress before should reach
  commit+push or a verdict before the raised timeout.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Hephaestus automation loop + one target repository | One issue recovered through five interrupted implementer rounds (two job timeouts, two external signals, one operator stop) | [notes.md](hephaestus-interrupted-implementation-lane-recovery.notes.md) |

## References

- [hephaestus-loop-unconfigured-host-operation](hephaestus-loop-unconfigured-host-operation.md) —
  layered host repair and intake-cleanliness recovery after crashes; this skill adds the
  implementation-stage nonce binding, the zombie-session interrupt, and the record disposition.
- [hephaestus-automation-loop-branch-sync-drive-green](hephaestus-automation-loop-branch-sync-drive-green.md) —
  branch/worktree inspection and PR-bound recovery once publication has occurred.
- [automation-loop-log-driven-layered-debug](automation-loop-log-driven-layered-debug.md) — the
  log-signature-at-stage-boundary methodology used to isolate each signature above.
