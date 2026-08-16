---
name: automation-prefix-match-plan-detection
license: BSD-3-Clause
description: "Recognize mutable automation-owned GitHub comments only by an exact opaque marker at byte zero, with headings and malformed lookalikes left inert. Use when: (1) fixing substring or permissive-prefix comment detection, (2) an owned-comment upsert can fall back to a display heading, (3) caller-side trimming can broaden identity, or (4) a durable plan/review journal must reconstruct safely after crashes."
category: architecture
date: 2026-08-06
version: "2.0.0"
user-invocable: false
verification: unverified
history: automation-prefix-match-plan-detection.history
tags:
  - automation
  - github-comments
  - plan-detection
  - canonical-marker
  - exact-match
  - actor-ownership
  - durable-journal
  - crash-recovery
  - fail-closed
  - migration-safety
---

# Automation Plan Detection: Exact Leading Marker Boundary

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Make an actor-owned mutable comment identifiable only when its raw body begins at byte zero with an exact opaque marker line, while preserving display headings and inert historical comments. |
| **Outcome** | v1's verified substring-to-prefix correction is retained as history. v2 generalizes the boundary across plan/review recognition, mutation, admission, and recovery, and replaces display-heading identity with an opaque canonical marker. The v2 implementation was not executed in this session. |
| **Verification** | unverified — the v2 workflow is based on an implementation-ready ProjectHephaestus plan, but its production changes and acceptance suites have not run. |
| **History** | [changelog](./automation-prefix-match-plan-detection.history) |

## When to Use

- Automation edits or replaces a GitHub issue comment that acts as the current pointer to a plan, review, report, lease, or other durable record.
- A substring or broad prefix check can confuse quoted text, a display heading, or a marker extension with a canonical record.
- Human-readable headings were historically used as identity and must become display-only without rewriting old comments.
- A shared predicate is called from queries, mutations, cached state, admission checks, and restart reconstruction.
- Leading whitespace or caller-side `.strip()` / `.lstrip()` could accidentally grant mutation authority to malformed or historical text.
- Archive-first publication must recover after a crash only when the canonical current artifacts form a valid pair.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the implementation and focused crash-recovery tests pass, preferably in CI.

### Quick Reference

```python
def has_exact_leading_marker(body: str, marker: str) -> bool:
    """Return whether marker is the exact first raw line of body."""
    return bool(marker) and (
        body == marker or body.startswith(f"{marker}\n")
    )
```

```text
Recognized:
  <marker>
  <marker>\n<display heading>\n<payload>

Inert:
  <display heading>\n<payload>
   <marker>\n<payload>
  \n<marker>\n<payload>
  <marker> suffix\n<payload>
```

### Detailed Steps

1. **Define one public raw-body identity primitive.** Accept only `body == marker` or `body.startswith(f"{marker}\n")`; reject an empty marker. The primitive must not trim, normalize, decode, or otherwise transform the raw stored body.

2. **Separate identity from presentation and ownership.** The opaque marker grants record identity only when it occupies the exact first raw line. A display heading may remain on the second line for people, but it must never select a mutable record. Separately require authenticated-actor ownership before editing or deduplicating a matching comment.

3. **Route every identity decision through the primitive.** Use the shared helper in comment queries, cached plan/review presence checks, standalone and coordinator upserts, post-create reconciliation, immutable append deduplication, admission, reviewer lookup, and journal reconstruction. Pass raw bodies to these predicates; remove caller-side `.strip()` and `.lstrip()`.

4. **Validate outgoing bodies before any write.** An upsert or immutable append should raise before calling GitHub unless its outgoing body satisfies the same exact-leading-marker rule. This keeps read and write identity symmetric and prevents creating records that the next run cannot reconstruct.

5. **Anchor immutable history records at byte zero too.** Match the whole first marker line and require either newline or end-of-body after it. For example:

   ```python
   HISTORY_RE = re.compile(
       r"^<!-- journal-history:revision=(?P<revision>\d+):"
       r"kind=(?P<kind>plan|review) -->(?:\n|$)"
   )
   ```

6. **Remove legacy identity parameters end to end.** Delete `legacy_marker` from production implementations, protocols, stage interfaces, call sites, and test fakes. A heading-only or whitespace-prefixed comment is audit text, not a migration source and not a fallback mutation target.

7. **Preserve visible canonical rendering.** Render current records as `opaque marker -> display heading -> revision metadata -> payload`. Tightening identity should not remove the heading humans use to scan an issue timeline.

8. **Leave residual legacy data untouched.** When only inert historical comments exist, create a separate canonical pointer beside them. Do not patch, delete, or migrate those records. This preserves audit history and supports rollback when an older implementation already prioritizes a canonical match before any legacy fallback.

9. **Keep recovery archive-first and fail closed.** Reconstruct from unmodified stored bodies. Ignore noncanonical current pointers and refuse to advance an interrupted publication unless the required canonical paired artifact is present. A heading-only or whitespace-prefixed review must never satisfy the paired-review recovery gate.

10. **Test every boundary across layers.** Cover marker-only validity, marker-plus-newline validity, same-line suffix rejection, heading-only rejection, space/tab/newline prefixes, raw-start history matching, canonical rendering headings, create-beside-inert upserts, no PATCH/DELETE of inert comments, admission rejection, and idempotent crash recovery with a valid canonical pair.

## Verified Workflow

> **Warning:** The marketplace validator currently requires this heading. No v2 workflow is verified yet; use the proposed workflow above until implementation tests and CI confirm it. The archived v1 workflow remains verified only for its older substring-to-heading-prefix bug fix.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Substring-match plan text | Used `marker in body` or searched for the word "plan" anywhere in a comment. | Reviews that quoted a plan were misclassified as active plans. | Identity must be anchored at the beginning of the record, never inferred from content. |
| Treat a display-heading prefix as canonical | Used `body.startswith(PLAN_COMMENT_MARKER)` where the marker was a human-readable heading. | Historical heading-only audit text remained mutable and reconstructable. | Use a separate opaque marker for identity and keep the heading on the second line for display only. |
| Trim before classification | Called `.lstrip()` or `.strip()` before testing a canonical marker. | Leading spaces, tabs, or newlines became invisible, so malformed text acquired canonical identity and mutation authority. | Identity checks must receive the raw stored body and preserve byte-zero significance. |
| Use unrestricted `startswith(marker)` | Accepted any body beginning with the marker bytes. | Same-line extensions such as `<marker> appendix` collided with the canonical namespace. | Require the marker to be the entire first line: exact body or marker followed by `\n`. |
| Duplicate first-line parsing in each caller | Queries, mutation helpers, state managers, and reviewers each interpreted markers independently. | Semantics drifted: some callers trimmed, some recognized headings, and some used raw bodies, breaking retry consistency. | Centralize one public predicate and route all identity decisions through it. |
| Tighten reads but keep legacy mutation parameters | Recognition became strict while upsert protocols still accepted `legacy_marker`. | A supposedly inert comment could still be selected by a write path, so the safety boundary was incomplete. | Remove legacy identity from implementations, protocols, call sites, and fakes together. |
| Recover from a noncanonical paired artifact | Archive-first recovery treated a heading-only or whitespace-prefixed review as the current paired review. | The state machine could advance from ambiguous durable evidence after a crash. | Recovery must reconstruct raw canonical records and stop when the canonical pair is incomplete. |

## Results & Parameters

### Identity Truth Table

| Raw body | Result | Reason |
|----------|--------|--------|
| `marker` | canonical | Marker-only records are valid. |
| `marker + "\n" + payload` | canonical | Marker is the exact first raw line. |
| `" " + marker + "\n" + payload` | inert | Marker does not begin at byte zero. |
| `"\t" + marker + "\n" + payload` | inert | Marker does not begin at byte zero. |
| `"\n" + marker + "\n" + payload` | inert | Marker does not begin at byte zero. |
| `marker + " appendix\n" + payload` | inert | Marker has a same-line suffix. |
| `display_heading + "\n" + payload` | inert | A display heading does not establish identity. |

### Required Mutation Invariants

```text
editable = exact-leading-marker(raw_body, marker) AND owned-by-current-actor
outgoing-valid = exact-leading-marker(outgoing_body, marker)
legacy-lookalike = never edit, never delete, never migrate
no canonical match = create canonical record
multiple canonical matches = reconcile only canonical actor-owned records
```

### Acceptance Matrix

| Surface | Required evidence |
|---------|-------------------|
| Shared journal | Direct helper tests plus raw reconstruction tests for current and history records. |
| Queries and cache | Heading-only and whitespace-prefixed bodies do not count as an existing current pointer. |
| Coordinator and standalone upserts | Inert actor-owned records receive no PATCH or DELETE; a canonical record is created and returned. |
| Immutable append | Deduplication recognizes only an exact first marker line. |
| Admission and reviewer lookup | Noncanonical plan bodies are ignored even when authored by the automation actor. |
| Rendering | Canonical marker remains first and the display heading remains second. |
| Crash recovery | Noncanonical paired artifacts cannot advance recovery; valid canonical crash matrices converge idempotently. |

### ProjectHephaestus Acceptance Commands

```bash
uv run pytest \
  tests/unit/automation/test_review_journal.py \
  tests/unit/automation/test_pipeline_github.py \
  tests/unit/automation/test_github_api.py \
  tests/unit/automation/state/test_planner.py \
  tests/unit/automation/state/test_review.py \
  tests/unit/automation/test_plan_reviewer.py -v

uv run pytest \
  tests/unit/automation/pipeline/test_admission.py \
  tests/unit/automation/pipeline/test_plan_journal.py \
  tests/unit/automation/pipeline/stages/test_stage_planning.py \
  tests/unit/automation/pipeline/stages/test_stage_plan_review.py -v

uv run pytest tests/unit/automation -v
uv run ruff check hephaestus/automation tests/unit/automation
uv run mypy hephaestus/automation tests/unit/automation
```

### Related Skills

- `automation-plan-review-journal-bounded-liveness` — bounded agent context and no-progress termination for the same durable journal domain.
- `testing-pipeline-crash-matrix-real-stage-durability` — reconstructing pipeline state from durable stage-owned evidence after restart.
- `github-graphql-pagination-fail-closed-complete-reads` — complete comment inventory before making authoritative GitHub decisions.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #715 / PR #1085 | v1's narrower substring-to-heading-prefix correction was verified in CI with 1,085 tests. It is retained in history, not presented as evidence for the v2 opaque-marker boundary. |
| ProjectHephaestus | Exact raw marker identity across plan/review journal queries, mutations, admission, and recovery | Unverified. The plan named the affected production and test surfaces and supplied acceptance commands, but no Hephaestus implementation or test run occurred in this session. |

## Architecture Notes

- Identity answers which raw record automation is authorized to treat as canonical.
- Ownership answers whether the current actor may mutate that canonical record.
- Presentation answers what humans see after the opaque marker.
- Recovery answers whether durable canonical evidence is complete enough to advance.

Keeping these concerns separate prevents a convenience normalization or display-heading change from silently widening mutation authority.
