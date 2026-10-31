---
name: stale-base-upstream-landing-recheck
description: "Re-verify upstream before implementation and again before push when work starts from aged CI-failure evidence. Use when a fix lane runs for hours against an active trunk, or several agents repair the same failure set: upstream can land the same scope during the work, and the local diff becomes a duplicate. Fetch, audit upstream commits that touch the same files, and stand down on coverage."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags: [upstream-landing, stale-evidence, dedupe, trunk-freshness, multi-agent, stand-down]
---

# Stale Base Upstream Landing Recheck

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Prevent duplicate implementation when upstream lands the same scope while a long-running fix lane works from aged evidence. |
| **Outcome** | Operational: the lane completes its own work only when upstream coverage is absent, and stands down early when coverage exists. |

## When to Use

Use this skill when:

- a fix or feature lane starts from CI-run evidence or an issue comment that
  is hours old, and the trunk receives other merges on the same day;
- several agents or lanes repair the same failure set or issue in parallel;
- the worktree or branch base stayed unchanged since the lane started, and
  the implementation lasted longer than the typical merge interval of the
  repository;
- a bisect identified the breaking commit, the repair is ready, and the next
  step is to push a branch and open a pull request.

## Verified Workflow

### Quick Reference

Before implementation starts, and again before any push:

```bash
git fetch origin main
git log --oneline <lane-base-sha>..origin/main -- <files the lane touches>
```

For each listed commit, read the commit message and, when the message names
the same scope, read the diff. Coverage in upstream ends the lane: archive
the local diff, record the stand-down, and stop.

### Suggested Approach

1. Record the lane base: the exact trunk commit and CI run the evidence
   comes from, at claim time. This base is the comparison anchor for every
   later freshness check.
2. Claim-time dedupe comes first (search open and closed issues and pull
   requests by signature). This skill covers the interval that dedupe cannot
   see: landings that happen after the claim, during the work.
3. At implementation start, fetch and list upstream commits that touch the
   lane's files since the base. A non-empty list means the evidence snapshot
   is aged: audit each commit before writing code.
4. Before push, repeat the same check. Gate the branch push and the pull
   request on its result, not only on local test status.
5. On upstream coverage, compare semantics, not only commit titles. An
   upstream commit that repairs the same tests with a different technique
   still ends the lane unless its change leaves an independently useful gap.
6. On stand-down, keep the discarded diff as an archive, post the reason in
   the coordination channel, and remove the worktree. Do not force a
   duplicate pull request just to preserve the work.

Do not relax the check because the lane is nearly done. A completed local
fix does not reduce the cost of a duplicate merge; it increases it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Implemented a full multi-group fix from CI-run evidence one day old, and checked upstream activity only after the local tests were green. | Four upstream pull requests had landed the same failure groups during the lane; the local diff (thousands of lines) was functionally duplicate and was discarded at push time. | Fetch-and-audit belongs at implementation start and again at push, not at push alone. The green local run did not change the duplication. |
| Attempt 2 | Treated claim-time issue and pull request search as sufficient freshness control for a long lane. | The search was correct at claim time; landings during the following day were invisible to it. | Claim-time dedupe and mid-work freshness are separate checks. Both are necessary; neither replaces the other. |

## Results & Parameters

### Configuration

| Parameter | Value | Meaning |
| --------- | ----- | ------- |
| lane base | exact trunk SHA and CI run id recorded at claim time | anchor for every freshness comparison |
| audit scope | every file the lane modifies or plans to modify | upstream commits outside this set cannot duplicate the lane |
| check points | implementation start and before push | the two moments where duplicate work is still avoidable |
| coverage rule | semantic overlap with the lane scope ends the lane | applies even when the upstream technique differs |

### Verification

- The `git log` command at each check point names every upstream commit in
  the audit scope since the lane base, so coverage is evidence, not
  assumption.
- A lane that passes both checks opens its pull request against a current
  upstream picture; a lane that finds coverage stands down with the
  superseding commits named in its records.

## Provenance

A multi-group test-failure repair ran for about a day from CI-run evidence.
Four upstream pull requests landed the same scope during the lane. The full
local diff was discarded at push time after a late `git fetch` exposed the
landings. The two checks above would have ended the lane about a day
earlier, and the stand-down record preserves the superseding commit set as
evidence.
