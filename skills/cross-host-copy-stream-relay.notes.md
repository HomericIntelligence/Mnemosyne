# Notes: cross-host-copy-stream-relay

Supporting evidence for `cross-host-copy-stream-relay.md`. The
session-level identifiers are deliberately generalized.

## Context

A pending release command copies runtime images from the cookbook pins of one
cluster into the administrative image store of another cluster. The two
administrative roots live on different clusters with different networks and
different filesystems, so the bytes transit the invoking host. Remote access
uses short-lived SSH sessions with per-host logins.

## The failed design that supplied the rules

The implementation built one rsync argv with a remote source and a remote
destination. The production dry run recorded "The source and destination
cannot both be remote." No bytes moved. The same change required GNU-only
flags, so a presence check was not enough: the invocation host carried
openrsync, which rejects `--append-verify`. After a manual relay got one image
across, the timeout defect surfaced: the transfer process ran with a fixed
one-hour bound, a 36 GB image exceeded it, and the run stopped with a
complete but unpublished stage.

## What worked

- The replacement streams two one-sided remote commands through the invoking
  host: `tail -c +<offset>` on the source and `cat >>` on the target.
- The resume offset is the existing stage size, so the next run appends
  instead of restarting.
- The byte stream has no timeout; only the read-only probes and the target
  hashing keep a bounded timeout.
- The target digest is the trust check. The resumed prefix is trusted until
  the hash confirms the whole file.
- The same-node pair check moved from the removed shim into the plan entry
  point, so the invalid configuration fails before any probe.

## Verification record

- RED: the transport-behavior tests failed before the change (missing
  stream-path support, obsolete flag and shim expectations).
- GREEN: the focused image-sync and command-matrix suites passed after the
  change (85 tests).
- Lint clean, formatter clean, and type check clean on the changed files.
- Command-matrix drift check matched the derived surface.
- The full CI matrix passed, including the test shards first and the
  aggregate gate.
- A signer-verified squash merge delivered the change; the tracking issue
  auto-closed from the PR body.

## Failure modes the rules prevent

- A copy that uses one command with two remote endpoints and moves no bytes.
- A production run that requires a tool variant the operator host does not
  have.
- A multihour transfer that dies at a fixed bound with an unpublished stage.
- A retry loop that restarts large copies from byte zero after each
  interruption.
