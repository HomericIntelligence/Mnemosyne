# Notes: Give a Session-Launched Refresher One Claim Owner

These notes give the generalized evidence behind
[duplicate-refresher-single-owner-claim](duplicate-refresher-single-owner-claim.md).
Product, project, host, path, and session identifiers are intentionally omitted.

## The case

An agent tool installs a small helper that keeps a model list in a client
configuration file in step with a published service record. Each interactive
session can start the helper as a watch loop. The helper reads the service
record, queries the served model list, and writes only the model-picker entry of
the client configuration file. The owner refreshes every 60 seconds.

The helper enforces one owner with a claim file. A second launcher starts,
fails the exclusive create, sees a live owner, and sleeps 5 seconds before it
tries again. Nothing in that design is wrong, but nothing bounds the number of
standbys either.

## Observed state

- Eight helper processes were live at the same time: one claim owner and seven
  standbys. The standbys came from earlier sessions that started the watch loop
  and never stopped it.
- The claim file named the owner pid. The state directory held one numeric pid
  file per process.
- The served model list and the client list agreed: 23 entries in the same
  order. The duplicate work was invisible in the output and visible only in the
  process set.
- Earlier in the same day the claim named a pid that no longer existed. A later
  launcher reclaimed the claim and refreshed. No manual step was necessary.

## Behavior tests

An isolated copy of the installed helper ran with its own configuration,
settings copy, cache, log, and state directory. The live configuration was not
touched.

| Case | Setup | Result |
| --- | --- | --- |
| Free claim | No claim file | Claim created, refresh ran, claim released |
| Live owner deferral | Owner running, one-shot command | Reported the cached state, exit 0, no second refresh |
| Stale claim | Owner killed with SIGKILL, claim left | Next launcher reclaimed the claim, refreshed, released |
| Standby handover | Standby waiting, owner sent SIGTERM | Standby became the owner in about 2 seconds |
| Graceful stop | Owner sent SIGTERM | Claim and own pid file removed |

## The residue after SIGKILL

A SIGKILL cannot run the release step. The claim file stays, and the numeric pid
file for that process stays. The two need different treatment:

- The claim is the authority for ownership, so the next launcher must recover
  it. Recovery is safe because the owner check fails and the content compare
  confirms that the claim did not change.
- The numeric pid file is only an input to the stop and cleanup path. Claim
  logic must not read it as ownership. The stop path reaps a file whose pid is
  dead, is a zombie, or does not have the helper command line.

A stop path that signals only the claim owner leaves the standby loops in place.
A stop path that signals only the pid files misses an owner whose file was
already reaped.

## Measurements that matter

- Standby claim retry interval: 5 seconds. This bounds takeover delay after an
  owner stop.
- Refresh interval: 60 seconds. The record age stayed under the interval with
  one owner.
- Stop wait before SIGKILL: 10 seconds. Each test owner exited well inside this
  bound.

## Boundaries

- These tests ran on one host with a local runtime state directory. A network
  file system needs the same exclusive create and the same liveness test; the
  content compare and delete in step 5 of the main entry are the protection
  against a slow reader, not a lease timeout.
- The helper refreshes an idempotent record. A refresher that mutates state
  without idempotency needs a stronger ownership rule than this entry gives.