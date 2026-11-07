# Notes: OpenCode Goal-Lane Revival

Supporting detail for [opencode-goal-lane-revival](./opencode-goal-lane-revival.md).
Nothing here is required to apply the skill; it records the measured sweep that
produced the rule. All host, user, repository, and session identifiers are omitted.

## Sweep inventory

| Goal store state | Count | Disposition taken |
| ------- | ------- | ------- |
| `active`, session moving and tokens growing | 2 | busy: no action, passive polling |
| `active`, session idle about twenty minutes, wait condition not yet true | 1 (became the idle-watch case below) | one bounded wait, then one nudge with current facts |
| `active`, session dead 12 days, era still relevant | 1 | one revive nudge; lane completed |
| `active`, session dead 5 days, era superseded but goal open | 1 | one revive nudge with audit-only instruction; lane closed with an audit |
| `paused` (plan mode), session dead | 1 | one nudge; lane reported the mode block; escalated to owner |
| `complete` | 10 at sweep start (14 at end) | ceremony only |
| `usageLimited` / `unmet` from a superseded era | 5 | no nudge: eras ahead of them already shipped |

## Timing record (coordinator local time)

- 21:14 — revive nudge to the dead twelve-day lane. Failure ladder seen in fewer
  than thirty seconds per attempt: stored entry refused as `Model unavailable: <entry>`;
  fleet-standard entry refused as `no worker available for model <entry>; retry when a
  replica is ready`; own-session entry attached in ten seconds.
- ~21:35 — the revived lane closed its goal record `complete` with a full audit:
  the asked-for merge had already landed during the dead period, checks green, issue
  closed, local worktree and branch cleaned per repo policy. Redo cost avoided: one
  duplicated implementation wave.
- ~21:19 — one nudge to the five-day-dead lane with an audit-only instruction.
- ~21:37 — closure `complete`: the lane re-verified every success criterion against
  live state, recorded one historical deviation, delivered its own outstanding
  durable-learning pull request, and renamed its session `Done:`-prefixed.
- 21:27 — nudge to the idle lane after all checks were green and no auto-merge was
  armed; session had been static about thirty minutes with a self-resume watcher that
  did not fire.
- 21:31 — merge recorded on the exact head, landmark artifacts reviewed, lifecycle
  record closed, redundant watcher stopped. Total steering cost: one message.
- The plan-mode lane answered with its goal identifier, status, blocker text, and
  remaining phase/task; it did not close. No further nudges were sent.

## Verbatim failure strings seen on the delivery path

These strings classify the retry decision. They are stable across the observed runs:

- `Model unavailable: <provider>/<entry>` — static. The stored entry has no service
  on this host. Retry once on a proven entry; do not retry on the same entry.
- `no worker available for model <entry>; retry when a replica is ready` — transient
  capacity. Treat as unserved for delivery; switching entries is cheaper than waiting,
  and a wait loop here burns coordinator turns without changing the decision.
- Successful attach: process alive beyond ten seconds and the owned log shows the
  banner line plus tool or text output growth.

## Closure evidence classes observed for later audits

| Lane | Class of closure evidence |
| ------- | ------- |
| Dead twelve days | Forge audit: merged pull request, green checks, closed issue, local cleanup |
| Dead five days | Success-criteria re-verification plus recorded deviation and outstanding work delivered |
| Idle watcher | Merge at the checked head, landmark artifact review, watcher released |
| Plan mode | Refusal with blocker; no closure (correct) |

## Cross-checks that made the sweep safe

- Busy classification used two store snapshots twenty seconds apart plus a 120 s
  freshness window; both live lanes moved between snapshots, so no steer went to a
  busy lane.
- Log-probe rule respected: every owned log was tested with an empty redirect
  before launch.
- Self-exclusion: the coordinator's own session matched the fleet's title filter
  and was removed from every batch target list by identifier.
- Terminal lanes from a superseded era were left untouched on purpose: two later
  release waves had already shipped their scope.
