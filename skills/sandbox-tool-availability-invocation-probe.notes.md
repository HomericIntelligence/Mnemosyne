# Notes: Probe Tool Availability by Invocation, Not by Inspection

Supporting evidence for `sandbox-tool-availability-invocation-probe.md`. Generalized from a
verified-local session; identifiers are intentionally omitted.

## Session context

- Environment: a hosted agent platform that offers (a) a sandboxed code runtime whose tool
  catalog is fixed for each turn and (b) direct native tool calls at the harness level.
- Work: a multi-step delivery task in a shared repository that required shell execution, Git
  signing, and pull-request operations.
- Constraint: the sandboxed runtime rejected every shell invocation with an unknown-tool error
  for several turns.

## Timeline evidence

1. Sandbox invocation failure. A zero-side-effect shell call through the sandbox API returned
   the unknown-tool error. This was repeated on each of three consecutive turns with the same
   result.
2. False positive from inspection. An introspection pass over the runtime's proxy object
   reported several plausible executor names (the primary name and five guessed aliases) as
   present and callable. Every invocation through each of these names still failed with the
   same unknown-tool error. Conclusion: the proxy resolves names that are not registered in
   the per-turn catalog.
3. Read-only delivery. While execution remained unavailable, the session completed every
   deliverable that did not need execution: test-result evaluation, a disposition table, the
   exact remaining commands for an unblocked turn, and the values that the later verification
   had to confirm.
4. Recovery. After the turn reported the blocker, a new turn began with a relaunched harness.
   A single native direct shell call succeeded immediately. All shelled work ran normally in
   the same turn.

## Commands

The zero-side-effect probes used:

```bash
# Through the sandbox API of the runtime: returned the unknown-tool error on every alias.
# As a native direct harness call:
echo <marker> && <auth-status-command>
# Result: marker printed, authentication listing succeeded.
```

## Decision rules that the evidence supports

- Invocation is the only authoritative probe. Name and property inspection of a sandbox proxy
  can report unregistered names as callable.
- A sandbox catalog is per-turn and per-confinement. It can omit tools that the host harness
  exposes natively. After a relaunch, probe again once instead of carrying over a stale
  conclusion.
- Repeated probing of a fixed catalog yields no new information. One invocation per interface
  per turn is enough; further retries only consume turns.
- Read-only work first keeps an execution outage low-cost: the unblock was one probe and one
  continuation, not a re-plan.

## Privacy notes

Internal paths, organization and repository identifiers, issue and pull-request numbers, and
personal identifiers are intentionally omitted from the main entry and from these notes. The
generalized interface terms ("sandboxed code runtime", "native direct call") describe the
public capability model of hosted agent platforms and are sufficient for the decision rule.
