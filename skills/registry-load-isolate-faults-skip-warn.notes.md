# Notes: registry-load-isolate-faults-skip-warn

Supporting evidence for the main entry. Generalized: no repository names,
issue identifiers, hostnames, internal paths, or product names.

## Source defects (one codebase, one review session, 2026-11)

Three instances of the same decision rule were verified in one multi-binary
CLI service at one reviewed revision:

1. **Client deployment registry.** A registry of YAML authority records is
   loaded strictly inside one loop before every public command. One record
   with a single wrong field (a scope value that did not match its own
   deployment identifier) raised out of the load. Every command — status,
   identity, model list, batch list — printed the same three-line library
   validation dump, including a truncated record repr and a documentation
   URL, and exited nonzero. A syntactically broken file in the same
   registry produced eight lines of parser output on every command. Every
   ordinary user on the installation was blocked until an operator edited
   the file. The client load path did not use the loader's tolerant mode,
   and the tolerant mode only ignores fields that a newer release wrote —
   it cannot isolate a broken file.

2. **Administrator paths inventory.** A long inventory record gated a
   session handshake, so one slow or large inventory blocked every
   administrator command. Same shape: one record's fault refused consumers
   that needed other records.

3. **Launch preflight (precedent for the direction).** An advisory
   preflight drift signal was changed to permit well-formed launches
   instead of refusing them. The project owner then asked for the same
   recovery stance for the registry: robust and recovering instead of
   failing closed for simple per-record errors.

## Observed defect shape

- Loader structure: one loop over a manifest of record file names; each
  record validated eagerly; the first failure raised out of the load, so
  the failure mode was all-or-nothing by construction.
- User-visible result: a multi-line library validation dump per command,
  identical for every command, with no per-command difference.
- Recovery available to users: none. The registry files are
  operator-owned; an ordinary user could only report the dump.

## Repair design (reviewed, tracked, not yet merged)

- Split the load loop; catch the per-record fault at the record boundary.
- Collect skipped records with one bounded cause each; warn once per run.
- Continue the load with valid records; set-level validation (uniqueness,
  identity conflicts) runs over the valid set and still refuses on
  ambiguity.
- A request that selects a skipped record refuses with one bounded line.
- Skipped records appear in the status surface operators already read.
- Trust boundaries unchanged: canonical-path and no-follow checks,
  ownership checks, environment prohibitions.
- Tolerant-read semantics stay as-is: they answer release skew, not
  corruption.

## Verification boundary

- verified-local: both defect shapes were reproduced by command-line
  probes at the reviewed revision; the transcript shapes are in the main
  entry's Expected Output.
- The repair is designed and tracked in the project tracker; it was not
  implemented at the time of this entry. Treat loop-structure details as
  design guidance until the tracked change merges.
