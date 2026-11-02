# Notes: derived-artifact-gate-non-vacuity

Privacy-safe supporting detail for the main skill. All identifiers from the
source session are generalized; no organization, product, project, issue, host,
or path names appear here.

## Generalized incident

A build pipeline for a container image family carries a dependency-audit gate:

1. A base stage extracts a protected-pin constraint set from a base artifact
   into a pin file.
2. A gate scans that file: forbidden pins must be absent, required pins must
   be present.

On one run, the extraction silently produced an almost-empty file (about one
byte). The input check at the gate verified that the file had been produced —
a byte-level check — and passed. Every scan over the empty set was vacuously
clean. The pipeline continued for about 8.5 minutes and failed at a later
import smoke check, whose error named a toolchain component and not the audit
input. Forensics on the failed run's workdir showed the near-empty pin file.

## Merged repair

- The extraction step now refuses to publish an empty set: it extracts to a
  temporary file, fails on an empty result, and replaces the pin file
  atomically.
- The gate asserts a non-zero entry count and the presence of required
  toolchain markers before it records any verdict; scan errors stop the
  pipeline as INCONCLUSIVE.
- Validation included simulation fixtures for the empty-extraction and
  missing-marker paths, and the repository suite passed green (45 checks)
  at merge.

## Seed-or-stop follow-through

The audit's protected pins come from the base artifact. A pending move to a
new-generation base can legitimately carry none of those pins. The recorded
decision: the recipe seeds the required set when the base lacks it, or the
gate stops early and names the missing input. The gate must not re-vacuate,
and its assertions must not be weakened to admit the empty case. The live
exercise of this branch is pending on that base update, which is tracked
outside this lesson.

## Verification limits

- The hostile paths were proven by simulation fixtures and repository CI, not
  by a hostile full-pipeline run.
- The 8.5-minute cost figure is from one failed run's timestamps; treat it as
  an order-of-magnitude illustration.
