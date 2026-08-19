# Benchmark Artifact Triage and PR Splitting — Notes

## Verification evidence for v1.3.0

- A local publication candidate contained one new valid record but had been built from a strict subset of the destination PR's current snapshot.
- Replacing the destination with that candidate would have removed destination-only stable identities even though the candidate itself passed local checks.
- The safe integration started from the bound destination head, inserted exactly the verified new identity, recomputed aggregate counts from the merged set, and regenerated every direct and transitive consumer.
- Stable-identity comparison proved that all destination records remained and only the expected addition appeared. Deterministic render checks and targeted tests passed.
- An added-line privacy scan found a private absolute path in a rewritten aggregate row. The value was corrected at the generation boundary, covered by a regression check, regenerated, and rescanned successfully.

## Evidence boundaries

- Raw profiler captures, operational logs, endpoints, internal paths, model or customer identifiers, repository names, issue numbers, and exact campaign measurements are intentionally excluded.
- The evidence supports snapshot integration, provenance, regeneration, and privacy-audit rules. It does not establish profiler-capture completeness or kernel-level performance conclusions.
- Existing-PR publication remains conditional on rebinding the destination identity and head immediately before push; a moved head requires stopping and repeating the merge proof.
