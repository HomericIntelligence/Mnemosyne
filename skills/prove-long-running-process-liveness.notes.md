# Notes: prove-long-running-process-liveness

## Evidence

The source session investigated a shared inference service deployment that runs one
reconciler inside a long-lived allocation. The investigation produced two false
conclusions before the liveness question was settled.

### False claim 1: a control interface had no capability

An early read of the available administrative verbs suggested that no activation path
existed. A later search of the deployment scripts found a purpose-built release driver
that had already been used successfully. The earlier claim was wrong, and acting on it
would have stalled the work.

Lesson: confirm a capability claim against the operator tooling and the recorded history
of its use, not against one listing.

### False claim 2: a healthy process was stalled

The reconciler log stopped advancing. That was read as a long outage with no failover.
Two probes contradicted it:

1. The component writes only on error or state change. A quiet log is the healthy case.
2. Its state file, which the process rewrites on every pass, had a current modification
   time and advanced during a 40-second observation window.

The process was completing a pass roughly every 30 seconds. The outage claim was
withdrawn before any disruptive action.

## Evidence that separated the two cases

| Signal | Reading | Conclusion it supported |
| ------ | ------- | ----------------------- |
| Log modification time | Unchanged for many hours | None. Error-only output is quiet when healthy. |
| State file modification time | Advanced within a 40-second window | Process alive and completing passes |
| Reported status content | Healthy counts, stable | Consistent with a live reconciler, but does not identify the writer |

The modification time of a rewritten artifact gave the decision. The log gave no signal.

## Environment constraints observed

- An allocation may give each job a private temporary directory. A batch job can write
  its own output where an operator cannot read it. Confirm where a job's output lands
  before reading it.
- A control process may hold an environment that a later operator process cannot
  reproduce from the files on disk. Compare a resolved identity from the operator side
  with the identity a job reports, and treat a mismatch as a finding rather than a
  reason to edit a rendered artifact.
- A rendered launch artifact copied from a long-running instance can carry an identity
  that no longer validates. Render fresh when the producer can render, and check the
  identity fields rather than only the resource flags.

## Related entries and boundaries

- `swarm-agent-status-misread-as-premature-exit` covers the same invariant for
  delegated agent work, where notification wording and timing stand in for liveness.
  That entry is about a harness lifecycle. This entry is about a service process and a
  filesystem signal. Use each for its own trigger.
- `debugging-diagnose-before-fixing-stale-blocker-claims` covers inherited claims that
  are stale against active code. That entry is about a recorded claim. This entry is
  about a live observation.

## Validation performed

- Schema check of the required frontmatter fields.
- Structure check against the repository skill template.
- Corpus search by name and by content for an existing entry with the same intent. None
  was found. The two nearest entries have different triggers, as recorded above.
- Open pull request inspection for a competing or duplicate entry. None targets this
  intent.