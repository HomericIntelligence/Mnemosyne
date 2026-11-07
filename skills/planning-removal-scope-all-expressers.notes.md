# Notes: Planning a Removal by Every Expresser

Supporting evidence for `planning-removal-scope-all-expressers.md`. Host paths, repository and
project names, issue identifiers, and the names of the audited functions are omitted. Substitute
site values.

## The source case

A read-only requirements audit of one issue. The issue decided that the caller requests replicas
and the scheduler decides placement. The issue asked to remove a grant-versus-pool refusal and a
node-count derivation from the deployment start path. The repository was at a clean detached head.
No change was in flight.

## What the audit found

| Issue claim | Evidence at the checkout |
| --- | --- |
| Exactly one validator refuses the start on the grant. | Two validators refuse. One compares the mandatory footprint against an internal node budget. The other compares the desired pool set against the recorded external grant. Both run from the same start hook, before any scheduler work. |
| The issue cited two functions by line number. | Both functions existed, but each line cite had moved. The finding held; the coordinates did not. |
| "No code path derives a node count from a replica target." | The slot cost of a replica is computed once and read by rendering, placement, and both validators. The node bound is only one conversion of that slot cost. |
| A scheduler refusal must report a job identifier, a placement target, a policy name, and a message. | The repository already had a rejection-persistence path and an error-enrichment path for one scheduler message. These are the candidate surfaces for the new diagnostic. |

## The decision branches the entry keeps

1. Enumerate every start-path gate. The issue named one; two existed. A removal of the named gate
   alone leaves the start refused, and the acceptance test stays red.
2. Split by change kind. The issue held four kinds in one scope: remove the refusal, keep the record
   as report-only, report the scheduler refusal, and set the requested values. Each kind needs its
   own step and its own evidence.
3. Keep the shared arithmetic. The slot cost stays because other consumers read it. The node bound
   that gates a start goes. The plan must say which readers remain.
4. Keep the diagnostic fields. The removed refusal gave a start-time explanation. The replacement
   gives a later explanation with more detail. The named fields are the acceptance criteria.
5. Test behaviour. A start above the old record must reach submission. A test for a missing symbol
   proves deletion only.

## Limits

- This was a read-only audit. No removal was implemented, run, or reviewed.
- The audit could not re-derive the count of pools that the linked record described. Only the
  refusal mechanism was verifiable.

## Related entries

- `verify-issue-premise-against-code-before-planning` covers the cite drift and the wrong-operator
  branch. This entry covers the removal-scope branch that remained after the premise was verified.
- `audit-remediation-verify-evidence-before-planning` covers per-target classification of audit
  findings. This entry extends it to a removal scope with several change kinds.