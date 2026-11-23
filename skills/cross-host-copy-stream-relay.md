---
name: cross-host-copy-stream-relay
description: "Stream a file copy whose source and destination are both remote hosts through the invoking host, resume an interrupted copy from the stage size, and never bound a large transfer with a fixed timeout. Use when a copy design would give one command a remote source and a remote destination, or when a tool check proved unreliable in production."
category: tooling
date: 2026-11-23
version: "1.0.0"
user-invocable: false
license: BSD-3-Clause
tags:
  - rsync
  - two-remote
  - stream-relay
  - offset-resume
  - transfer-timeout
  - tool-variant-probe
  - digest-verify
---

# Cross-Host Copy Stream Relay

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-23 |
| **Objective** | Copy bytes from a remote source host to a different remote target host, with the invoking host only connecting the two streams, and without a copy-tool rejection or a mid-transfer timeout. |
| **Outcome** | Operational. A pending production cross-cluster copy failed with the one-command design; the relay design shipped and completed the copy. |

## When to Use

Use this entry when:

- A required copy reads from a remote source host and writes to a remote target host, and the invoking host carries the bytes.
- A copy tool or command in the design has a remote source and a remote destination at the same time.
- A check proves that a tool exists on PATH, but the needed behavior is variant-specific, for example flags that only one implementation provides.
- A large transfer can run longer than any fixed wall-clock bound, or a previous run timed out before the file ended.
- An interrupted copy can resume from a state file instead of restarting from byte zero.

## Verified Workflow

### Quick Reference

Give the source host and the target host one command each, never one command with two remote endpoints:

```text
# Source host: read from the first missing byte.
tail -c +<stage-size + 1> -- /path/to/file
# Target host: append those bytes to the stage.
cat >> /path/to/stage
# Invoking host: connect the two streams with a pipe or a pump.
# The byte stream has no timeout.
```

Verification steps:

1. Probe the target final name and stage with read-only commands; bound these probes with a short timeout.
2. Derive the resume offset from the existing stage size.
3. Stream the source bytes into the stage.
4. Hash the staged file on the target host and compare the digest with the expected digest.
5. Publish only after the digest matches.

### Suggested Approach

1. **Replace the two-remote command with a relay.**
   An `rsync` call with a remote source and a remote destination fails with
   `The source and destination cannot both be remote.` No byte moves. Run a
   read-side command on the source host (for example `tail -c +N`) and an
   append-side command on the target host (for example `cat >>`). The invoking
   host only connects the two standard streams.

2. **Remove the transfer timeout; keep bounded probes.**
   A fixed wall-clock timeout on the transfer fails any file that is larger
   than the bound allows. Probe commands and the target digest use a short
   bound. The byte stream does not.

3. **Resume from the stage size.**
   Derive the stream offset from the size of the existing stage file. An
   interrupted copy then appends, instead of restarting. Refuse a stage that
   is not a regular file or is larger than the source before any byte moves.

4. **Verify the whole file, not the prefix.**
   A resumed prefix comes from an earlier transfer and is only trusted until
   the target hash confirms the whole file. A corrupt or raced stage fails the
   digest and stays on disk for forensics.

5. **Verify tool behavior, not tool presence.**
   A presence check cannot find a tool variant that lacks the needed flags.
   For example, the bundled openrsync on one common desktop OS rejects the
   GNU-only `--append-verify` option. Probe the behavior, or design the copy
   so that it needs only commands that every host already has, such as a shell,
   `tail`, and `cat`.

### Decision Branches

| Condition | Decision |
| --------- | -------- |
| The copy design gives one command a remote source and a remote destination | Replace it with two one-sided commands connected by a stream |
| A tool exists, but the needed option is variant-specific | Probe the behavior, or remove the variant-specific option |
| The transfer can exceed any fixed time bound | No timeout on the stream; bound only probes and the digest |
| An interrupted copy must not restart | Stream from the existing stage size; refuse an oversized stage |
| The staged bytes can be corrupt | Verify the target digest before publish; leave the stage on failure |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| One rsync command across two hosts | Build an rsync call with a remote source and a remote destination; expect bytes to move | rsync rejects the call with "The source and destination cannot both be remote."; no bytes move | Use two one-sided remote commands and connect the streams on the invoking host |
| Presence check for the copy tool | `require_tool("rsync")` verifies the binary exists before a production copy | The desktop OS shipped openrsync, which rejects the GNU-only `--append-verify` flag; presence does not imply the needed variant | Probe the behavior, or use only commands every host already has |
| Fixed timeout on the transfer | A 3600 second timeout bounded the whole transfer process | A 36 GB copy over the relay exceeded one hour; the timeout aborted a copy whose stage was complete but unpublished | No bound on the byte stream; bound only the probes and the target digest |
| Restart an interrupted copy from zero | Each retry re-ran the full copy instead of resuming the stage | Multihour copies restarted after every interruption and never finished | Resume from the stage size; the resumed prefix is verified by the final digest |

## Results & Parameters

### Configuration

```text
stream.source:  tail -c +<stage-size + 1> -- SOURCE   # runs on the source host
stream.target:  cat >> STAGE                          # runs on the target host
stream.relay:   the invoking host connects the two streams; no timeout
resume.offset:  size of the existing stage file; refuse a non-regular or oversized stage
verify.digest:  SHA-256 of the staged file on the target host, compared before publish
probes.timeout: short bounded timeout on reads and hashes only
publish:        hard link after digest match; stage removed after publish
```

### Expected Output

- A two-remote design becomes a two-command relay; the invoking host never runs a copy tool against both ends.
- An interrupted copy resumes from the stage size and finishes.
- The transfer survives files that exceed any probe or hash bound.
- A corrupt stage fails the digest and stays on disk for forensics.
- Publish never overwrites an existing name.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| A cross-cluster administrative image copy on one production deployment | A pending release command failed in production with the two-remote rsync design and a one-hour transfer timeout | The relay design, offset resume, bounded probes, and digest verify shipped with a full TDD record; the merged change passed focused tests, lint, typecheck, and the full CI matrix. Generalized provenance in [notes](cross-host-copy-stream-relay.notes.md) |
