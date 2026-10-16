# Notes: slurm-foreign-job-artifact-gate

Generalized evidence from the originating session. All identifiers (account,
cluster, job IDs, hostnames, paths, issue numbers) are omitted per the privacy
rules; only the decision-bearing measurements are kept.

## Session evidence

### Phase 1 — monitor a foreign build

- Mission: watch a multi-hour container base-image build owned by another
  service account; poll every 10 minutes; report state and phase; success
  required both scheduler `COMPLETED` and a marker line in the build log.
- Readability boundary, discovered at the first poll: the builder's home
  directory was `drwxr-x---` owned by the builder user and builder group. The
  monitor identity was not in that group; a supplementary-shared-group switch
  did not help. `sacct` and `scontrol show job` remained fully usable.
- The job's `StdOut`/`StdErr` pointed to the same unreadable home, so log
  tails were impossible for every later poll.
- Poll cadence held at 10 minutes with one-line reports that named the
  unreadable channel explicitly.
- Terminal classification attempt: `FAILED`, exit `2:0`, elapsed ~1h52m,
  batch-step `MaxRSS` ≈ 140 GiB against `ReqMem` 320 GiB (≈44%). Classified as
  a script abort, explicitly not the historically known compile-time OOM.
- Step-level states: batch FAILED `2:0`; one step COMPLETED; three short
  steps CANCELLED during teardown.

### Phase 2 — handoff claims the artifact

- A follow-up message said "the checkpoint is now at `<shared-store path>`;
  continue with this as the baseline image," targeting an allowlist insertion
  of the image digest.
- Verification at gate time: the claimed path did not exist; the shared image
  store contained no file matching the new name; the newest attempt had
  FAILED with exit `1:0` at ~42 minutes elapsed.
- Attempt table for the same job name on that day (all from `sacct -X`):
  - two OUT_OF_MEMORY kills at ~4.4h and ~5.6h (the historically known mode);
  - script aborts: exit `2:0` ~1h52m, exit `1:0` ~1h24m, exit `0:0` ~11m,
    exit `1:0` ~23m, exit `1:0` ~42m;
  - a two-second "preflight" COMPLETED trivially.
- Total: seven failed attempts, zero published artifacts. The pin was blocked
  and reported; no digest was invented or estimated.

## Decision branches exercised

1. Readable logs unavailable → metadata-only channel declared up front.
2. Terminal failure vs historical OOM → MaxRSS-vs-request disproved OOM.
3. Claimed artifact path at pin time → stat failed, job failed, pin blocked.

## Commands used (all read-only)

```bash
sacct -j <id> -o JobID,State,ExitCode,Elapsed,NodeList -X
sacct -j <id> -o JobID,State,ExitCode,Elapsed,MaxRSS,ReqMem
sacct -S <date> -u <owner> -o JobID,JobName,State,ExitCode,Elapsed -X
scontrol show job <id>
squeue -u <owner>
ls -ld <parent>; ls -lt <store>; find <store> -name '*<marker>*'
head -c4 <candidate> | od -c      # planned gate step; no artifact existed
sha256sum <candidate>             # planned gate step; no artifact existed
```

## Limits of the evidence

- Log contents were never observable from the monitor identity; the failing
  phase inside each abort could not be identified. The report listed the exact
  commands a group member could run to read them.
- Caches persist between attempts, so "resubmit is cheap" was reported as
  information only; no resubmission was performed or requested by the monitor.
