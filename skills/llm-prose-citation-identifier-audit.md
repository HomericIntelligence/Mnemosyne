---
name: llm-prose-citation-identifier-audit
description: "Audit external identifiers (PRs, issues, tickets, commit SHAs, tags) that LLM-generated prose cites. Use when a model writes reports or summaries from collected data and the prose names tracker references that readers will treat as authoritative."
category: documentation
date: 2026-10-19
version: "1.0.0"
user-invocable: false
tags: [llm, generated-prose, citation-audit, identifier-verification, fabrication-detection, report-generation, dataset-membership, system-of-record, range-expansion, evidence-counts]
---

# LLM Prose Citation Identifier Audit

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-19 |
| **Objective** | Establish that every external identifier cited by LLM-generated prose resolves to a real record before the document ships. |
| **Outcome** | successful |

## When to Use

- An LLM writes prose from a collected dataset, and the prose names external
  identifiers: pull requests, issues, tickets, commit SHAs, or release tags.
- Readers will treat the citations as authoritative (status reports, weekly
  reports, change summaries, release notes).
- The collected dataset is available locally, and a system of record
  (tracker API or CLI) can confirm anything the dataset does not contain.
- A citation error costs more than the audit: one fabricated or mismatched
  reference can invalidate an otherwise correct document.

## Verified Workflow

### Quick Reference

1. Extract every cited identifier from the generated text, including each
   member of closed ranges (a range `#A–#B` expands to its members; bound the
   expansion, for example at 50 items).
2. Check membership against the collected dataset's key sets (merged-PR
   numbers, closed-issue numbers, commit SHAs).
3. Classify each out-of-dataset citation by where it appears:
   factual sections versus forward-looking plans.
4. Verify every outlier against the system of record before you accept it,
   and check its state against the claim the prose makes.
5. Record the audit counts with the artifact. Re-audit after any
   regeneration.

```bash
# Extract and classify (illustration; adapt keys to your dataset):
grep -oE '#[0-9]{3,4}' report.md | sort -u > cited.txt
# Membership test against the collected JSON key sets, then:
system-cli item view <outlier-id> --json state,title   # one call per outlier
```

### Suggested Approach

Treat every cited identifier as an unverified claim, regardless of how
accurate the prose's numbers look. A document whose metrics all match the
data can still cite references the data does not contain.

Membership in the dataset is verification. Absence is not proof of error:
decide by section role. In factual sections ("what happened this window"),
an out-of-dataset identifier is a defect — fix the prompt or data and
regenerate. In derived or forward-looking sections ("next steps"), citations
of records outside the window are legitimate, but each one must still exist
in the system of record, and its recorded state must support how the prose
uses it (an umbrella tracker cited as open must actually be open).

When prose asserts a disposition about an identifier ("closed by", "fixed
in", "blocked on"), check the record's state, not only its existence. When
prose compresses a backlog into a range, expand the range before the
membership test; spot-check the range members' states if the prose claims
the whole range is resolved.

Regeneration after a prompt or style fix invalidates the old audit. Pin the
data window when regenerating so the dataset and citations stay comparable,
then re-run the audit on the new text; citation sets shift between valid
reruns.

Report the result as counts: cited, in-dataset, out-of-dataset and where
each outlier was verified. These counts are the delivery evidence. If the
system of record is unavailable, keep the outliers unverified and say so in
the report instead of accepting them.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust prose whose metrics match | Accepted the document because every aggregate figure matched the dataset, without checking citations. | The audit still found cited identifiers outside the dataset that only a system-of-record lookup could confirm or reject. | Metric accuracy does not imply citation accuracy; audit identifiers separately. |
| Reject all out-of-dataset citations | Treated every out-of-window reference as a fabrication. | Forward-looking sections legitimately cite open trackers outside the window; blanket rejection removes valid plan items. | Classify outliers by section role, then verify each against the system of record instead of deleting. |

## Results & Parameters

### Configuration

```yaml
identifier_pattern: '#(\d{3,4})'   # adapt to tracker reference shapes in the prose
range_expansion_cap: 50            # members; larger spans get manual review
dataset_keys: [merged_prs.number, closed_issues.number, commits.sha]
outlier_action: verify-against-system-of-record  # never accept silently
record_with_artifact: [cited, in_dataset, outliers, outlier_resolutions]
```

### Expected Output

- One count line: cited identifiers, verified in-dataset, out-of-dataset.
- For each outlier: identifier, section role, system-of-record state, and
  the verdict (accept as contextual, or defect to fix).
- The counts stored beside the generated artifact as delivery evidence.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private weekly-report pipeline | Three regenerated revisions of one data-driven report | Audit rounds: 66/67, 55/58, 65/67 cited refs verified in-dataset; all outliers confirmed real via tracker CLI; no fabricated references. See [notes.md](../skills/llm-prose-citation-identifier-audit.notes.md). |

## References

- [Academic paper accuracy and citation audit](academic-paper-accuracy-and-citation-audit.md) — adjacent audit for human-written papers against bibliographic sources; different corpus and failure modes.
