---
name: pr-state-label-retroactive-audit
description: "Backfill missing mutually-exclusive state:* implementation labels on closed pull requests from hosted review-verdict records. Use when: (1) merged or closed PRs lack the pipeline GO/NO-GO state label, (2) review verdicts must be recovered from several hosted carrier formats at scale, (3) a delegated GO classification must be verified against the exact merged head before any label write, or (4) a bulk label repair must keep the exclusive-vocabulary invariant."
category: ci-cd
date: 2026-10-16
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags:
  - github-labels
  - retroactive-audit
  - review-verdict-recovery
  - exact-head-binding
  - mutually-exclusive-labels
  - delegated-classification
  - evidence-digests
---

# Retroactive State-Label Audit of Closed Pull Requests

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-16 |
| **Objective** | Restore the mutually-exclusive `state:implementation-go` / `state:implementation-no-go` vocabulary on a large set of merged pull requests that lack it, using hosted review records as the only evidence. |
| **Outcome** | Operational. Executed end-to-end on a live repository: several hundred closed PRs inventoried, every merged candidate digested and classified, labels written in bulk, and the exclusive-state invariant verified by a final repo-wide read. |

Audit means evidence recovery and classification, not a fresh review. Do not re-grade the
change; bind the verdict that the review records already carry. Complements
`architecture-github-labels-as-state-vocabulary` (the forward state-machine contract) and
`automation-review-comment-validation-host-receipts` (the forward review-to-label path):
this entry covers the repair path when merged history bypassed that path.

Supporting commands and parser details are in
[pr-state-label-retroactive-audit.notes.md](pr-state-label-retroactive-audit.notes.md).

## When to Use

- A repository uses exclusive `state:implementation-*` labels, and some closed or merged
  PRs carry neither.
- You must determine which unlabeled merged PRs were authorized (review verdict exists,
  label missing) versus merged without a hosted verdict.
- Verdicts were recorded over several mechanism generations, so one scan cannot assume one
  carrier format.
- Delegated agents classify evidence at scale, and their positive votes need an
  independent binding check before any write.

Do not use this audit as a substitute for the review itself. If no hosted verdict record
exists for a PR, the honest outcome is the negative state, not a new review.

## Verified Workflow

### Quick Reference

```text
inventory (label-filtered PR list, JSON to file)
  -> dual-source verdict scan (PR review objects AND issue comments, ALL known formats)
  -> per-PR evidence digests via script (reviews + comments + timeline + head SHAs -> JSONL)
  -> delegate classification with written verdict rules (parallel, one output line per PR)
  -> verify every GO vote against the exact merged head before any write
  -> apply labels with add-target + remove-siblings semantics at bulk scale
  -> final repo-wide read: exactly one state per audited PR, zero conflicts
```

### Suggested Approach

1. **Inventory to file, not to context.** List the closed PR set once with labels as JSON
   and select the unlabeled set locally. Keep PR metadata (state, merged flag, dates) for
   the join. Work from files; large result sets must not flow through the conversation.
2. **Scan both verdict carriers and every recorded format.** Query the PR's review
   objects and its issue comments. Accept each format the review machinery has emitted:
   terminal-exchange bodies with an explicit `Verdict:` line and machine-readable state
   JSON; legacy round comments such as `## Implementation review — GO at <sha>`;
   multi-round exchanges in which a later `NO-GO` supersedes an earlier GO unless a still
   later round re-authorizes; and report-only reviews, which count as review evidence but
   need an authority decision before a positive backfill.
3. **Digest per PR through a script.** For each candidate, collect reviews, comments,
   timeline event counts, final head SHA, and merge-commit SHA into one JSONL record with
   only verdict-relevant lines. Digests make the classification step cheap and keep raw
   bodies out of context.
4. **Delegate classification against written rules.** Split digests into batches and give
   each agent the same explicit verdict-rule document: GO formats, supersede ordering,
   the exact-head rule, and the required output shape. Validate completeness (every input
   PR appears exactly once) before acting on results.
5. **Re-verify every positive vote against content.** A GO is backfill evidence only when
   the verdict binds the artifact that actually merged. Check for each positive: the
   reviewed head equals the merged head, or the reviewed content is provably identical
   (tree or per-file blob equality, respecting rebase tree change); no material commit
   landed after the terminal verdict; and no later record disclaims authorization
   (merge-fidelity NO-GO, observer disclaimer). Downgrade failures to ambiguous.
6. **Write labels as one exclusive transition per PR.** Add the target state and remove the
   sibling in the same operation (or in immediate sequence at bulk scale), then verify.
   Adding a positive label to a PR that already carries the negative sibling without
   removing it contradicts the vocabulary.
7. **Close with a repo-wide invariant read.** Re-list the audited population and require:
   exactly one implementation-state label per PR, no PR holding both, and zero label-free
   outliers. Report the classification buckets with their lists.

Classify, do not infer: a timeline `labeled` then `unlabeled` pair on the GO label is a
withdrawn authorization, not an error to repair silently; an empty-duplicate artifact's
review record (byte-identical tree to main) is superseded only when the record says so.
When the repository owner records a tombstone superseding a NO-GO, honor it as the
authority record it is and apply the state it declares.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Scanned only issue comments for verdict headers | Found zero GOs in a set that contained several; terminal verdicts live in PR review objects | Scan both endpoints and every format the machinery has emitted before concluding "no review record" |
| 2 | Trusted delegated GO votes directly | Several positive votes failed content binding: reviewed head superseded with changed file blobs, a material commit after the final GO, and a final record disclaiming merge authorization | Re-verify each positive classification against the exact head and later records before any label write |
| 3 | Added the GO label without removing the existing NO-GO sibling | Affected PRs held both exclusive states at once | Apply each transition as add-target plus remove-siblings, then re-read; the vocabulary tolerates no overlap |
| 4 | Parsed `gh api --paginate --jq` output as one JSON value | Pagination emits one JSON document per page; a strict single-value parse fails on multi-page results | Decode concatenated documents (incremental decoder or slurp) before merging |
| 5 | Treated a checks-green status comment as review evidence | A CI status line names the head but carries no verdict | A verdict requires the review carrier; status comments are operational noise for this audit |

## Results & Parameters

- Population handled in one live audit: about 800 closed PRs by one author windowed by
  creation date; about 240 lacked the state label; every merged candidate (about 160) was
  digested and classified in four parallel batches.
- Outcome distribution: a small positive set (verified GO records), a large bare-merge set
  (no hosted review records at all), a small final-NO-GO set (merged against an unreversed
  terminal NO-GO), and an ambiguous set returned for authority decision.
- The delegated pass voted GO on several ambiguous items; coordinator content-binding
  checks confirmed only the honestly bound subset before any write.
- Final invariant read: every audited merged PR holds exactly one state label; zero
  conflicts; zero unlabeled.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal service monorepo | Retroactive audit across two creation-date windows | End-to-end execution: inventory, dual-source verdict recovery, delegated classification, coordinator binding checks, bulk exclusive label writes, and the closing invariant read. Evidence is operational, not CI. |
