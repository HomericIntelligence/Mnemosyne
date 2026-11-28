---
name: registry-load-isolate-faults-skip-warn
license: BSD-3-Clause
description: "Isolate per-record faults in a multi-record authority registry load: skip and warn for records a request does not need, refuse concisely for the record it does, and surface every skipped record. Use when one corrupt registry entry, inventory file, or profile blocks every command or consumer, when a loader validates all records in one loop, or when a raw validation dump reaches end users."
category: architecture
date: 2026-11-23
version: "1.1.0"
user-invocable: false
tags:
  - registry
  - fail-closed
  - degraded-state
  - skip-and-warn
  - error-isolation
  - loader
  - health-surface
  - authority-data
  - validation-dump
---

# Registry Load: Isolate Faults, Skip and Warn, Keep Refusals Scoped

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-23 |
| **Objective** | Keep a set of authority records usable when one record is invalid, without weakening any trust boundary. |
| **Outcome** | Operational. A defect review reproduced the whole-set block twice at the reviewed revision of a multi-binary CLI service: one record with one wrong field, and one malformed file, each blocked every command for every user. The isolation repair is designed and tracked; the rule below generalizes three verified instances in that codebase. |
| **Verification** | verified-local. The defect is reproduced and the repair design is reviewed. The repair itself is not merged yet; treat implementation details as design until the tracked change lands. |

## When to Use

- A loader validates every record of a set (registry entries, inventory files, profiles) inside one loop, and the first invalid record raises out of the load.
- One malformed or mis-edited record blocks every command, job, or consumer, including the ones that need none of that record's authority.
- End users see a raw library validation dump: multi-line parser output, a truncated record repr, or a link to the library's error documentation.
- You must decide where fail-closed ends and degraded service starts for a set of records.
- You are reviewing a loader change and must keep the recovery path observable.

## Verified Workflow

### Quick Reference

```text
1. Classify the fault before you choose the failure mode:
   per-record fault  -> isolate, skip, warn, continue
   set ambiguity     -> refuse the load (two valid records conflict)
   all records bad   -> refuse, with one bounded cause per record
2. Load each record independently. A fault skips that record, not the set.
3. Print one bounded warning per skipped record. No library dumps.
4. Run every request that needs no skipped record normally.
5. Refuse only the request that selects the skipped record, with one
   concise line: file, field, expected vs observed, remedy.
6. List skipped records in the health or status surface.
7. A skipped record grants no authority. Never use a partial record.
8. A skipped record is not an absent record. Never use a packaged,
   cached, or default fallback for a selected record that was skipped.
```

### Suggested Approach

1. Reproduce with the smallest bad record: change one field value in one
   registered file, then register a syntactically broken file. Record what
   every command prints and which consumers stop. A whole-set block with a
   library dump is the defect shape this rule repairs.
2. Split the load loop. Give each record its own validation step and catch
   the per-record fault there. Collect skipped records with their causes
   instead of raising out of the load. See
   [coded-rejection-boundary-catch-completeness](coded-rejection-boundary-catch-completeness.md)
   for how to split one exception family by cause at the boundary.
3. Bound every client-facing message. One line per skipped record: the file
   name, the one-line cause, and a statement that the other records stay
   usable. Do not render library exception objects, record reprs, or
   documentation links for end users.
4. Scope the refusal to the authority the request uses. A request that
   selects the skipped record, explicitly or through auto-resolution, gets
   the bounded one-line refusal and a nonzero exit. Every other request
   runs. Fail-closed protects the authority a request consumes; it does not
   stop unrelated work.
5. Surface the degradation. Add the skipped records and their causes to the
   status or health output that operators already read. A degradation that
   the health surface cannot see persists until a user reports it.
6. Keep the guards that make skipping safe. A skipped record provides no
   authority: no partially valid spec, no defaults filled from it, no
   silent repair. Ambiguity between two valid records still refuses the
   load, because a conflict between two authorities is not a simple
   per-file error. When every record fails, refuse with the bounded
   per-record causes; there is nothing left to select.
7. Keep the trust boundaries unchanged: canonical-path and no-follow
   checks, ownership and ancestor checks, and environment prohibitions stay
   strict. Do not widen a tolerant-read mode to cover this rule: tolerant
   read answers version skew between releases, not corruption. The two
   mechanisms stay separate.
8. Test each branch: skip-and-continue, the bounded warning, the scoped
   refusal, the all-invalid refusal, the valid-conflict refusal, and the
   status surface listing. When no status surface exists yet, the stderr
   warning is the minimum, and the surface item becomes the follow-up.

### Skip Is Not Absence

A consumer that falls back to a packaged, cached, or default copy must know
why the selected record is missing. Return the skipped identities with the
valid set. If the requested identity is in the skipped set, refuse the
request before the fallback. Use the fallback only when the identity is
absent. A fallback after a skip is a silent authority change, not a recovery.

Test both branches together:

- selected identity skipped -> bounded refusal, fallback is not called;
- selected identity absent -> fallback is used, and the result says so.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Whole-set fail-closed as a safety stance | Kept the one-loop load that refuses all records when one is invalid, on the grounds that authority data must be exact | The refusal stopped every consumer of every record, including requests that needed none of the bad record's authority | Fail-closed belongs to the authority a request actually uses. Unrelated sibling records degrade, warn, and recover when fixed. |
| Widen tolerant-read to absorb the bad record | Considered passing the tolerant flag to skip validation failures | Tolerant read ignores fields that a newer release wrote; it does not isolate a corrupt file, and it would hide real damage | Version skew and corruption are different failure modes with different mechanisms. Isolation is structural; tolerance is field-level. |
| Ship the library dump to users | Let the validation library render its own multi-line error with a truncated record repr and a documentation link | Users cannot act on it, it leaks the full record structure on every command, and it repeats for every consumer | Render one bounded line yourself: file, cause, remedy. Keep the detail in a log or diagnostic surface, not the user path. |
| Skip records silently | Considered dropping bad records without a warning or a status entry | The damage became invisible: consumers worked against fewer records and nobody knew which authority was missing | A skip is a state change. Warn once per run and list the skips where operators look. |
| Fall back after a skip | The tolerant loader dropped a malformed selected record, so the consumer found no record and used a packaged fallback copy | The command appeared to succeed with different authority, and the skip warning was easy to miss | A skipped selected record must refuse before the fallback. Return skipped identities so the consumer can tell skip from absence. |

## Results & Parameters

### Configuration

Shape of the isolated load loop:

```python
entries, skipped = [], []
for name in manifest.records:
    try:
        entries.append(load_record(directory / name))
    except RecordError as error:
        skipped.append((name, bounded_cause(error)))  # one line, no reprs
warn_once_per_run(skipped)   # stderr: file, one-line cause, set stays usable
validate_set(entries)        # ambiguity between valid records still refuses
```

### Expected Output

- One stderr line per skipped record: `warning: skipped <file>: <one-line cause>; the other registered records stay usable`
- Every command that needs no skipped record: normal output, normal exit code
- A command that selects the skipped record: one refusal line naming file, field, expected vs observed, and remedy; nonzero exit
- The status or health surface: a list of skipped records with their causes
- No library exception text, no record reprs, no documentation URLs in any user-facing message

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A multi-binary CLI service (private deployment) | Registry-load defect review at the reviewed revision, 2026-11 | Reproduced the block with one wrong field and one malformed file; the same shape appeared in the client registry, an administrator inventory, and a launch preflight. Repair designed and tracked; see [notes](registry-load-isolate-faults-skip-warn.notes.md). |

## References

- [Coded Rejection Boundary: Catch Every Type the Call Raises](coded-rejection-boundary-catch-completeness.md) — split one exception family by cause at the boundary
- [Explicit Config Path Must Fail Closed; Auto-Discovery May Fall Through](config-explicit-path-fail-closed.md) — the single explicit path keeps fail-closed; this rule adds the multi-record dimension
- [Registry Map: Total Lookup, Empty Writer, Silent Fallback](registry-map-total-lookup-silent-empty-fallback.md) — the publication-completeness counterpart for per-key entries
