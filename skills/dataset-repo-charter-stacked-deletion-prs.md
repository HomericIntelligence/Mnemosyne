---
name: dataset-repo-charter-stacked-deletion-prs
description: "Enforce a 'dataset-only' repo charter by locking a written charter, bucketing every artifact as in-charter vs out-of-charter, then porting or deleting out-of-charter code via stacked deletion PRs. Use when: (1) a repo has suffered massive scope creep and contains reconcilers/converters/runtime logic that belong elsewhere, (2) you need to reshape a repo to be ONLY schemas + data + validators + docs + CI wrappers, (3) the cleanup will delete 10k+ LOC and you want small reviewable diffs, (4) the receiving repos for ported code are different repos in the same org and you do NOT want to coordinate merge ordering, (5) you need to distinguish 'dataset repo' (just data + schema) from 'consumer repo with reconciler' — the reconciler ALWAYS lives in the consumer, never the dataset, (6) deciding whether to coordinate cross-repo merges or open independent PRs that link back to each other for reconstruction."
category: architecture
date: 2026-05-17
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [charter, scope-creep, dataset-repo, stacked-prs, deletion-pr, multi-repo, repo-boundary, reconciler, port-vs-delete]
---

# Dataset Repo Charter Enforcement via Stacked Deletion PRs

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-17 |
| **Objective** | Cleanly reshape a repo back to its intended charter (dataset-only) after major scope creep, deleting tens of thousands of lines without breaking the receiving consumers. |
| **Outcome** | Successful: -24,632 lines / 159 files deleted from Myrmidons across 4 stacked PRs (#730, #731, #732, #733); reconciler ported to ProjectAgamemnon (#405); hello-world ported to AchaeanFleet (#664); 127 GitHub issues auto-closed as out-of-charter. |
| **Verification** | verified-local — PRs opened, local repo state validates, CI on the PRs themselves was not waited on within the session |

## When to Use

- A repo started as "data + schema" but accumulated reconcilers, runtime logic, integration code, and operational tooling that belongs in consuming repos.
- You want to delete a large amount of out-of-charter code but reviewers will balk at a single 25k-line diff.
- Multiple receiving repos (the "consumers") need to absorb ported code but you do NOT want to block cleanup on cross-repo merge ordering.
- You need a defensible criterion to mass-close GitHub issues that are now out-of-charter (so reviewers see a principled bucket, not arbitrary closures).
- You are about to coordinate "Repo A imports the code, THEN Repo B deletes it" and want to know whether that's necessary (usually it isn't).

## Verified Workflow

### Quick Reference

```bash
# 1. Lock the charter in writing (commit to CLAUDE.md or CHARTER.md first)
#    "This repo is ONLY: <thing 1>, <thing 2>, <thing 3>. Anything else is out-of-charter."

# 2. Bucket every artifact — code, issues, ADRs, lints, workflows — as in-charter or out-of-charter

# 3. For each out-of-charter file/dir, decide PORT or DELETE
#    - Has a consumer that needs it?  -> PORT to that consumer's repo (independent PR)
#    - No consumer / dead code?       -> DELETE in this repo

# 4. Open stacked deletion PRs in this repo (C1 -> C2 -> C3 -> C4), each rebased on the prior
git checkout -b cleanup/c1-<topic> main
# ... delete files for cluster 1 ...
gh pr create --base main --title "cleanup(c1): remove <topic>"

git checkout -b cleanup/c2-<topic> cleanup/c1-<topic>
# ... delete files for cluster 2 ...
gh pr create --base cleanup/c1-<topic> --title "cleanup(c2): remove <topic>"
# repeat for C3, C4

# 5. Mass-close out-of-charter issues with verdict buckets
gh issue list --state open --json number,title,labels --limit 500 > /tmp/issues.json
# Classify each issue into a verdict bucket (e.g., MOVED-TO-AGAMEMNON, MOVED-TO-FLEET, OBSOLETE, DUPLICATE)
# Then close each bucket with a templated comment linking to the migration PR
for n in $(jq -r '.[] | select(.verdict=="MOVED-TO-AGAMEMNON") | .number' /tmp/classified.json); do
  gh issue close "$n" --comment "Out-of-charter per <charter-link>. Migrated to ProjectAgamemnon: <PR-url>"
done
```

### Detailed Steps

1. **Lock the charter FIRST.** Before deleting anything, write the charter into a tracked file
   (e.g., `CLAUDE.md`, `README.md`, `docs/CHARTER.md`) and commit it as its own PR. The charter
   is a single sentence: "This repo is ONLY X, Y, Z." Every subsequent deletion PR references
   this charter as the justification — reviewers can argue with the charter but not with each
   individual deletion.

2. **Bucket every artifact.** Walk the repo (files), issue tracker (open issues), ADR list, lint
   configs, and CI workflows. For each, ask: "Does this serve X, Y, or Z?" If yes → in-charter,
   leave alone. If no → out-of-charter, mark for port-or-delete.

3. **For each out-of-charter artifact, decide PORT vs DELETE:**
   - **Has a clear consumer** (another repo that will actually use this code at runtime) → PORT.
     Open an independent PR on the consumer repo that contains the code. Do NOT block the
     cleanup PR on the port PR merging — see step 5.
   - **No consumer / dead code / superseded** → DELETE in the cleanup PR.

4. **The reconciler-vs-dataset boundary:** If repo A (dataset) supplies data that repo B
   (consumer) reads, any reconciler / converger / "make actual match desired" logic lives in B,
   not A. The dataset repo only emits data; the consumer pulls it. This is the single most
   common scope-creep direction — runtime logic creeping into the dataset repo because "it
   needs the YAML."

5. **Open independent PRs across repos. Do NOT coordinate merge ordering.** Initial instinct is
   to coordinate: "Agamemnon imports reconciler THEN Myrmidons deletes it." This is almost
   always unnecessary. The cleanup PR in the dataset repo can land first; the receiving repo
   reconstructs the code from the PR's commit history and links. Each PR description links to
   its sibling PRs so any reviewer can find the full story. This unblocks the cleanup
   immediately and avoids cross-repo deadlock.

6. **Stack the deletion PRs (C1 → C2 → C3 → C4), each rebased on the prior.** Reviewers see a
   small diff per PR (a few thousand lines, focused on one theme) but the net reduction across
   the stack is large. Use a clear topic per cluster (e.g., "remove reconciler", "remove
   integration tests for reconciler", "remove TLS env-var docs that referenced the
   reconciler", "remove CI workflows for reconciler"). After C1 merges, rebase the stack;
   reviewers approve C2 etc. in sequence.

7. **Mass-close out-of-charter issues by verdict bucket, not individually.** Classify every
   open issue into one of a small number of verdict buckets (e.g., MOVED-TO-AGAMEMNON,
   MOVED-TO-FLEET, OBSOLETE, DUPLICATE-OF-NN). Close each bucket with a templated comment
   linking to the relevant migration PR or charter section. This gives a defensible paper
   trail and lets the issue author understand WHY it was closed.

8. **Trust the actual issue count, not the plan estimate.** Initial estimates (e.g., "~118
   issues") will be wrong. Re-run `gh issue list` after each closure wave; classification
   bucket sums rarely match the upfront estimate. Actual closure was 127, not 118.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Coordinated cross-repo merge ordering | Tried to gate "Agamemnon imports reconciler" BEFORE "Myrmidons deletes it" so consumers were never broken | User vetoed: "Don't block on other repos, just implement here what needs to be implemented and link back to the PRs from the other repos. They can reconstruct the results." Cross-repo merge dependencies introduce deadlock risk and slow every PR to the speed of the slowest reviewer. | PR links + commit history are enough for the receiving repo to reconstruct. Open independent PRs across repos; let each merge on its own schedule. The dataset repo never imports from the consumer, so it CAN delete safely even before the consumer absorbs the code. |
| Single monolithic deletion PR | Considered one big "-24,632 lines / 159 files" PR for the whole cleanup | Reviewer cognitive load is too high. A 25k-line diff cannot be reviewed line-by-line; reviewers either rubber-stamp or stall. | Stack 4 deletion PRs (C1 → C4) each rebased on the prior, each a few thousand lines and one focused theme. Net reduction is the same, but each PR is reviewable. |
| Estimating issue counts up-front | Estimated "~118 issues to close" from a partial scan | Actual count was 127 across 4 verdict buckets. Bucket sums don't equal upfront estimate because the scan undercounts edge cases (stale issues, transferred issues, hidden labels). | Re-run `gh issue list` after every closure wave. Trust the live count, not the plan estimate. |
| Mixing PORT and DELETE in one PR | Considered "delete reconciler in Myrmidons AND copy it to Agamemnon in the same diff" using a meta-PR or coordinated rev | Cross-repo coordinated PRs don't exist as a primitive in `gh`; you can only open one PR per repo. Mixing the two operations also makes review harder because deletion is binary (yes/no) while porting requires code review of the new copy. | Always split: one PORT PR on the consumer repo, one DELETE PR on the dataset repo. Cross-link in each PR body. |
| Treating the reconciler as part of the dataset | Initially Myrmidons contained the reconciler that converged desired-state YAML against ProjectAgamemnon's REST API | The reconciler is consumer logic — it READS Myrmidons YAML and WRITES to Agamemnon. By the dataset/consumer rule, it belongs in Agamemnon (or a dedicated reconciler repo), not in the dataset. | Apply the reconciler-vs-dataset boundary rule: any "make actual match desired" code lives in the consumer that has the actual state, not in the repo that defines desired state. |

## Results & Parameters

**Verdict buckets used (Myrmidons session, 2026-05-17):**

| Bucket | Count | Disposition |
|--------|-------|-------------|
| MOVED-TO-AGAMEMNON | ~52 | Closed with link to ProjectAgamemnon#405 (reconciler import) |
| MOVED-TO-FLEET | ~14 | Closed with link to AchaeanFleet#664 (hello-world port) |
| OBSOLETE (out-of-charter) | ~48 | Closed citing CLAUDE.md charter |
| DUPLICATE | ~13 | Closed with link to canonical issue |
| **TOTAL** | **127** | |

**Stacked deletion PR sizing (Myrmidons #730 → #733):**

```text
PR #730 (C1: remove reconciler core)        ~  8,200 lines deleted, 52 files
PR #731 (C2: remove reconciler tests)        ~  6,400 lines deleted, 38 files
PR #732 (C3: remove TLS/auth docs/scripts)   ~  5,600 lines deleted, 41 files
PR #733 (C4: remove reconciler CI/workflows) ~  4,400 lines deleted, 28 files
-----------------------------------------------------------------------------
TOTAL                                          -24,632 lines, 159 files
```

**Cross-repo PR map:**

```text
Myrmidons (dataset)         Receiving repos
-------------------         ------------------
#730 delete reconciler   →  ProjectAgamemnon#405 (reconciler import)
#732 delete TLS docs     →  (no receiver — docs only described code that moved)
hello-world removal      →  AchaeanFleet#664 (hello-world port)
```

**Post-cleanup repo charter (committed to CLAUDE.md):**

> Myrmidons is the source of truth for *desired* agent state. The repo contains ONLY:
> YAML schemas, agent descriptions, dataset validators, dataset docs, and CI wrappers
> for those validators. Reconcilers, runtime logic, and consumer-side tooling live
> elsewhere (ProjectAgamemnon).

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/Myrmidons | 2026-05-17 cleanup session — repo started as "look at open PRs" but pivoted to charter enforcement when scope creep was discovered | PRs #730, #731, #732, #733 (stacked deletion); 127 issues auto-closed; -24,632 lines |
| HomericIntelligence/ProjectAgamemnon | Receiving repo for reconciler port | #405 |
| HomericIntelligence/AchaeanFleet | Receiving repo for hello-world port | #664 |
