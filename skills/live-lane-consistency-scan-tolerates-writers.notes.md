# Live-Lane Consistency Scan Tolerates Writers — Source Notes

Supporting evidence for the main skill. It is not retrieved with the skill.

## Source incident

A production promotion of a release through an ordered sequence of numbered
steps failed in one run because the control daemon could not produce a
consistency record. The lane was serving: one supervisor process and several
serving replicas, each rewriting per-pool state files on a fixed interval.

## Failure 1 — the scan aborted on a moving file

Two operation records, same verb, ~90 s each:

```text
Operation <id-a> failed: [Errno 2] No such file or directory:
  'scale-out-retry.json.tmp.<pid>.<uuid>'
Operation <id-b> failed: service path validation failed:
  check=file-identity, expected=opened and visible identity,
  observed=<root>/pools/<model>/gpu-metrics/<job>-<index>.json
```

Diagnosis:

- The first name is the writer's own temporary name, removed before the scan
  reached it. The writer pattern is write-temporary-then-rename.
- The second is a different declared path, in a different directory family,
  failing the identity check. A file replaced between the directory scan and
  the identity read shows exactly this.
- The pool retry-state files were rewritten for every pool within the scan
  window (mtimes inside the scan interval).
- The supervisor that writes them was the process named in the temporary file
  name (`<pid>`), confirmed in the process table.

Rule: a different victim each attempt is a writer race. Do not retry the full
scan.

## Failure 2 — one failed scan wedged the control lane

The control daemon serves one request at a time. During and after each failed
scan every other verb returned:

```text
The operator service is busy with an earlier request and did not start
action <name> for request <id>: the dispatch queue wait exceeded 5.0 s
after 5.0 s. No operator action was started.
```

Three different verbs failed this way inside the same window. After a daemon
restart (clean start, empty queue) a verb still answered busy for the first
tries while the previous work drained.

Rule: the failing scan must not hold the dispatch critical section.

Useful observation: the daemon restart itself was clean and cheap (~6 min
including two liveness checks), and it disturbed no serving component. The
restart clears the queue, but it does not fix the race.

## Failure 3 — the consuming step ran before any step produced its record

The step that validates the promotion compared the prior manifest with the
candidate and final manifests and refused:

```text
promotion requires a recorded path attestation for the active deployment;
run <cli> paths attest first.
```

No step in the ordered sequence produced that attestation. The consuming step
had already authored pool records, built both manifests, and validated the
release interface before it failed. It was not resumable without redoing the
work.

Rule: for each step, name the step that writes each consumed record. Guard
before the first write.

## Start model used when the node had no user service manager

The node had no user service manager (`systemctl --user` failed to connect to a
bus) and no alternate route to the node. The daemon was started as a detached
scheduler step inside the allocation it manages:

```text
<interpreter> -u <VAR>_JOB_ID -u <VAR>_JOBID setsid nohup \
  <scheduler> --jobid=<gateway job> --overlap -N1 -n1 --cpu-bind=none \
  --job-name=<daemon unit name> bash <launcher> > <client log> 2>&1 </dev/null &
```

Properties that matter:

- The step ends only with the managed allocation, so it survives the calling
  shell, the agent session, and logout.
- The launcher reads the connection secret inside itself and never on a
  command line.
- The step re-execs itself onto the node that owns the socket:
  `<VAR>_ON_HOST=1 <scheduler> --jobid=<job> --overlap ... bash <step>`.
- The unit name is kept as the scheduler step name so identity stays visible
  in the queue listing.

## Cross-release helper state

A supervision helper from the previous release was still running on the node.
It restarts the previous daemon when the heartbeat is stale and its claim file
is free. The stop-to-start window therefore held that claim:

- take the claim with an exclusive create before the stop;
- refresh it before any long wait (its staleness rule frees it after a fixed
  age);
- release it on failure so the prior daemon returns without a hand-run
  command;
- release it after the new daemon passes its liveness checks.

Leaving this dependency unnamed in a shipped step is the defect; bind the claim
and the launcher to the release that owns the daemon.

## Verification limits

- The three failures are verified live from operation records and the process
  table.
- The corrected scans are not yet deployed; the tolerance rule is the required
  correction, not an observed result.
- The start model was verified live twice (initial transition and a restart),
  each with the 30 s and 5 min liveness checks.