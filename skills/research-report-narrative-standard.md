---
name: research-report-narrative-standard
description: "Write one narrative research report per research line. Use when drafting or revising experiment documentation: quarantine operational metadata in a reproducible-environment appendix, replace superseded content, and ban absence narration."
category: documentation
date: 2026-11-04
version: "1.0.0"
user-invocable: false
tags: [research-report, technical-writing, narrative, reproducibility, report-structure]
---

# Research Report Narrative Standard

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-04 |
| **Objective** | Keep research reports readable: prose carries the argument, artifacts carry the evidence |
| **Outcome** | Operational — authored for a long-running segmented research campaign after hash-dense, per-run operational detail made the reports unreadable |

## When to Use

- Writing or revising a report that documents an experimental research line.
- A report cites hashes, timestamps, token counts, runtimes, or completion counts inside its prose.
- A research line continues in sequential segments and each new segment becomes a new document instead of extending one report.
- A report keeps superseded numbers or explains why material is absent.

## Verified Workflow

### Quick Reference

One line of research: one report, one story, segments in sequence. Before delivery, run a mechanical sweep for forbidden token classes outside the appendix and remove every match.

### Suggested Approach

1. **One report per research line.** A research line has one living report. Segments extend it in execution order, so the reader follows the linear history: what was tried, what the evidence showed, what is now believed. Do not create a parallel document for each segment or assume that named campaign boundaries are scientifically special.
2. **Quarantine operational metadata.** Prose carries findings, decisions, and result tables. Hashes, timestamps, runtimes, counts, paths, and job identifiers go to exactly one reproducible-environment appendix, or stay in machine-readable artifacts that the appendix references. If removing a metadata item from a paragraph does not change what the reader concludes, it belongs in the appendix.
3. **Replace superseded content in full.** State what is true now. Delete superseded numbers and claims instead of annotating them with earlier values. Keep history only when the history itself is the finding, and state it once.
4. **Never narrate absence.** Do not tell the reader what is not in the report or why. Keep constraining negative results: they are findings. Drop organizational absence: unfilled scope is silently out of scope.
5. **State each fact once.** A later segment references earlier results by their position in the sequence, not by restating their numbers.
6. **Enforce mechanically.** After drafting, search for the forbidden classes outside the appendix: literal digests, timestamps, counts of runs or steps, and superseded headline values. Target zero matches. Intent alone is not sufficient; stale content survives narrative-only review.

Example decision branches:

| Case | Decision | Reason |
| --- | --- | --- |
| A donor-disabled control regresses to the baseline | Keep in prose | Constraining negative results are findings; removing them changes the conclusion |
| Another task family was not evaluated in a segment | Remove in full | Organizational absence narration; silence marks the scope |
| Evidence policy requires sealed receipts for every result | Put every receipt in the appendix; prose references the appendix once | Provenance stays intact without competing with the story |
| A result table holds per-task scores | Keep in prose | The table is the finding |
| A section lists per-run token counts and step counts | Move to the appendix | Operational counts are metadata, not findings |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Inline provenance | Kept hashes and run identifiers in result paragraphs for traceability | The report became unreadable; the argument disappeared behind operations detail | Traceability lives in the appendix and artifacts; prose points at it |
| Annotate superseded values | Marked old numbers as earlier results next to the new numbers | The report claims two different results at once; the reader cannot tell what is true now | Replace superseded content in full; use Git for prior versions |
| Delete stale narrative by intent | Instructed authors to update numbers after results changed | Superseded framing survived next to the new claims in later sections | Run a mechanical sweep with an explicit list of stale claims; treat remaining matches as defects |

## Results & Parameters

### Placement rule

| Class | Destination |
| --- | --- |
| Findings, decisions, result tables | Prose, stated once |
| Constraining negative results | Prose, as findings |
| Hashes, timestamps, runtimes, counts, paths, job identifiers | One reproducible-environment appendix, or referenced artifacts |
| Superseded numbers and claims | Deleted; prior versions live in version control |
| Unfilled scope | Absent without comment |

### Sweep token classes

Search for these classes outside the appendix before delivery: long hexadecimal digests, date-time stamps, occurrence counts of runs and steps, and each superseded headline value. Expected matches: zero.

### Expected Output

- One report document per research line, extended by each segment.
- Prose that reads as a continuous argument with findings and tables only.
- One appendix that carries all provenance; prose references it once.
- Zero sweep matches outside the appendix.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal research-campaign documentation | Standard authored from a review of a 140-segment report program whose prose buried findings in operational metadata | Applied to follow-on segment documents from initial drafting |

## References

- [academic-paper-accuracy-and-citation-audit](academic-paper-accuracy-and-citation-audit.md) — mechanical residual-narrative audit used as the sweep model
- [evaluation-paper-rewrite-after-data-fix](evaluation-paper-rewrite-after-data-fix.md) — verified failure mode for stale-narrative deletion by intent
- [evaluation-analysis-pipeline-reporting](evaluation-analysis-pipeline-reporting.md) — evidence in generated artifacts, prose generated from data
