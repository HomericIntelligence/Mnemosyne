---
name: ambient-partial-clone-lazy-fetch-read-hazard
description: "Detect an ambient partial clone (for example blob:none) before read-heavy Git work. Use when a shared ambient checkout can lazy-fetch on demand, when a metadata-looking command silently downloads many objects, when an object probe cannot prove local availability, or when a verification lane forbids object acquisition through the ambient checkout."
category: tooling
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - git
  - partial-clone
  - promisor
  - blob-none
  - lazy-fetch
  - ambient-checkout
  - immutable-reads
  - review-evidence
---

# Ambient Partial-Clone Lazy-Fetch Read Hazard

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Keep read-heavy Git work out of an ambient partial clone, where any object-touching command becomes network I/O of unbounded size. |
| **Outcome** | Successful. The hazard was confirmed in one review session and bounded: the silent fetch was identified, and further verification reads moved into an explicitly acquired immutable source. |

## When to Use

- A shared ambient checkout was cloned with a partial filter (for example
  `blob:none`), and several lanes use it for editing and terminal work.
- A command that looks metadata-only (a one-commit log listing, a tree or
  file listing, a diff) silently starts a large background download.
- An object probe must mean *local availability*: in a partial clone, an
  existence probe can succeed by transparently fetching instead.
- A verification or review lane forbids object acquisition through the
  ambient checkout remote, so lazily completing that store is doubly wrong:
  it moves unbounded bytes and it crosses the lane boundary.

Do not use this skill for helper-side object completeness. That is the
sibling intent of
[git-helper-ambient-context-preflight](git-helper-ambient-context-preflight.md):
prefetch known revisions into the ambient store, or diagnose the helper's
ambient order. This skill covers the ambient checkout's own read behavior.

## Verified Workflow

### Quick Reference

```bash
# 1. Detect a partial checkout before read-heavy work.
git config remote.origin.partialclonefilter     # prints e.g. blob:none
ls .git/objects/pack/*.promisor 2>/dev/null     # promisor pack markers

# 2. Classify commands: treat any blob-touching command in that store as
#    unbounded network I/O. Commit-only probes stay local in blob:none.
git cat-file -e <oid>^{commit}                  # cheap, local existence probe

# 3. Keep large-tree and cross-tree reads inside an explicitly acquired
#    immutable source instead of the ambient checkout.
```

### Suggested Approach

1. **Detect before you read.** Check the remote's `partialclonefilter`
   configuration and the promisor-pack markers. Their presence means blobs
   are not local and any command that needs blob or tree content will fetch
   it on demand, without a report and with an unbounded byte count.
2. **Separate probe classes.** A `blob:none` filter keeps commits and trees
   local. Use commit-typed `^{commit}` probes for existence questions. Do
   not use blob reads as availability probes: they succeed by fetching and
   then misreport the store as complete.
3. **Move bulk reads to an explicit source.** Tree walks, full-file diffs,
   and multi-file audits belong in a source that was acquired for that
   purpose: a complete, non-shallow disposable repository fetched with exact
   revisions and verified invariants, or a snapshot that a verification
   helper already prepared. Read there, never through the ambient store.
4. **Respect the lane's acquisition rule.** Some verification lanes forbid
   fetching through the ambient checkout remote at all. For those, lazy
   completion of the ambient store is not a shortcut: it violates the lane
   boundary and it also violates rule 3 on size.
5. **Report the hazard once observed.** A teammate's terminal in the same
   ambient checkout hits the same boundary. Record which command fetched and
   how much, so the next lane classifies read-heavy work on its first
   attempt.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Run a metadata-looking command in the ambient checkout | Listed one commit and its tree context as part of a review | The command silently lazy-fetched hundreds of blob objects (on the order of tens of MB) in the background | Classify commands before running them: in a partial clone every blob touch is unbounded network I/O |
| Use the ambient store for local review reads after commit probes passed | Assumed a successful `cat-file` probe meant the store was usable for strict verification | The verifier required a complete, non-partial store and rejected it outright; the acquisition boundary of the lane excluded ambient-checkout fetches anyway | A probe result in a promisor store answers a weaker question than the verifier asks; acquire the explicit immutable source instead |

## Results & Parameters

### Configuration

```yaml
detect_partial_clone:
  config_probe: "git config remote.<remote>.partialclonefilter   # blob:none"
  marker_probe: ".git/objects/pack/*.promisor"
pricing_rule:
  partial_clone_read: "unbounded network I/O, silent, background"
  local_by_design_in_blob_none: [commits, trees]
  fetched_on_demand_in_blob_none: [blobs]
lane_rules:
  bulk_reads: "explicitly acquired immutable source only"
  ambient_checkout_remote: "no object acquisition on a verification lane"
```

### Expected Output

- A detected `partialclonefilter` value (or empty result for a full clone)
  before any read-heavy command runs.
- Zero unintended lazy fetches: every blob touch runs inside the selected
  explicit source.
- Existence answers come from commit-typed probes that stay local.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A shared multi-lane repository checkout | Pull-request review evidence collection in an ambient blob:none checkout | Measured detail in [ambient-partial-clone-lazy-fetch-read-hazard.notes.md](ambient-partial-clone-lazy-fetch-read-hazard.notes.md) |

## References

- [Git partial clone](https://git-scm.com/docs/partial-clone) — filter semantics,
  promisor packs, and on-demand fetching.
- [git-helper-ambient-context-preflight](git-helper-ambient-context-preflight.md) —
  helper-side ambient diagnosis by dependency order; this skill covers the
  ambient checkout's own reads.
- [mid-drive-peer-completion-audit](mid-drive-peer-completion-audit.md) —
  audit read-side evidence on immutable sources; the reproduction clause was
  added from the same session evidence.
