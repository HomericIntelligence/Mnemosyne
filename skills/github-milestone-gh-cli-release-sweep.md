---
name: github-milestone-gh-cli-release-sweep
license: BSD-3-Clause
description: "Manage GitHub milestones and release-board sweeps with the gh CLI. The gh CLI has no milestone subcommand, so creation and due-date repair go through the REST API; set due_on at noon UTC, not midnight UTC, or the UI renders the date one day early. Use when creating milestones from a script, assigning a large mixed issue and pull-request backlog to milestones, or verifying that a release board has zero unassigned items."
category: tooling
date: 2026-10-24
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [github-cli, gh-api, milestone, release-train, release-board, due-on-timezone, batch-assignment, issue-sweep, pr-sweep, tracker-epic]
---

# GitHub Milestones with the gh CLI and Release-Board Sweeps

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-24 |
| **Objective** | Create a full release train of GitHub milestones from automation, sweep every open issue and pull request into the correct milestone, and verify a zero-unassigned end state. |
| **Outcome** | Successful. Thirteen milestones created and date-corrected, approximately 700 open issues and all open pull requests assigned with zero failures, verified by zero-count unassigned queries. |

Two API facts drive every decision in this skill:

1. The `gh` CLI has **no** `milestone` subcommand. Milestones are managed only
   through the REST API path `repos/{owner}/{repo}/milestones`.
2. GitHub renders a milestone `due_on` timestamp as a calendar date in the
   viewing account timezone. A `due_on` of `...T00:00:00Z` renders one day
   early for any account whose timezone is behind UTC.

## When to Use

Use this skill when one or more of these conditions apply:

- A script or agent must create or update GitHub milestones, and
  `gh milestone create ...` returns an "unknown command" usage error.
- A milestone created with `due_on` at midnight UTC displays a due date one
  day earlier than intended in the GitHub web UI.
- You must assign a large backlog of issues **and** pull requests to
  milestones, and you must prove completeness (zero unassigned).
- You run a release train: one tracker epic per milestone, plus periodic
  re-sweeps as new issues and pull requests arrive between sweeps.

For audit-remediation epic coordination (wave sequencing, verify-and-close of
already-fixed findings), see
[audit-epic-sequencing-milestone-attachment](audit-epic-sequencing-milestone-attachment.md).
That skill shares the milestone API primitives but does not cover the
due-date trap, pull-request assignment, or sweep verification described here.

## Verified Workflow

### Quick Reference

```bash
# 1. Create a milestone. There is NO `gh milestone` subcommand; use the API.
#    Always pass due_on at noon UTC (T12:00:00Z), never midnight UTC.
gh api repos/{owner}/{repo}/milestones \
  -f title="v1.2.3" \
  -f due_on="2026-11-15T12:00:00Z" \
  -f description="Release plan: issue #epic."

# 2. List milestones with numbers, dates, and live progress counts.
gh api repos/{owner}/{repo}/milestones --paginate \
  --jq '.[] | "\(.number)\t\(.title)\tdue \(.due_on[0:10])\topen=\(.open_issues)\tclosed=\(.closed_issues)"'

# 3. Repair a shifted due date in place (PATCH accepts the same fields).
gh api -X PATCH repos/{owner}/{repo}/milestones/{number} \
  -f due_on="2026-11-15T12:00:00Z"

# 4. Assign matters: milestones apply to issues AND pull requests.
gh issue edit {n} --milestone "{title}"
gh pr edit {n} --milestone "{title}"

# 5. Batch sweep with an explicit failure log (tolerate individual errors,
#    never trust the loop's final exit code).
: > sweep-fail.log
assign() {
  local ms="$1"; shift
  for e in "$@"; do
    local kind="${e%%:*}" n="${e##*:}"
    if [ "$kind" = pr ]; then
      gh pr edit "$n" --milestone "$ms" >/dev/null 2>&1
    else
      gh issue edit "$n" --milestone "$ms" >/dev/null 2>&1
    fi || echo "$kind#$n -> $ms" >> sweep-fail.log
  done
}
assign "v1.2.3" issue:101 issue:102 pr:103 pr:104

# 6. Verify the end state. Both counts must be exactly zero.
gh issue list --state open --limit 1000 --json milestone \
  --jq '[.[] | select(.milestone == null)] | length'
gh pr list --state open --limit 500 --json milestone \
  --jq '[.[] | select(.milestone == null)] | length'
```

### Suggested Approach

1. **Snapshot the inventory to disk before mutating anything.** Export every
   open issue with `--json number,title,labels,milestone` and every open pull
   request to local JSON files. Classify offline; apply mutations from the
   snapshot. This keeps a multi-hundred-item sweep resumable across agent
   restarts and gives you diff-able before/after evidence. Pass an explicit
   high `--limit`; the default page size silently truncates large backlogs.
2. **Classify by decision rule, then assign.** Order of evidence: linked
   parent issue or epic (a pull request inherits the milestone of the issue it
   closes), then labels, then title theme. Record the rule for each ambiguous
   item next to its assignment so a later re-sweep can be audited.
3. **One tracker epic per milestone.** Create a tracker issue that carries the
   full membership list, deferral notes, and the due date; label it and give
   it the milestone itself. When the board is re-partitioned (a milestone
   split, a rebalance), append a transfer note to the tracker body of every
   affected milestone instead of rewriting history.
4. **Midnight-UTC `due_on` is a display bug.** GitHub stores a timestamp but
   presents the date in the viewer's account timezone, so
   `2026-10-30T00:00:00Z` presents as 2026-10-29 for accounts behind UTC.
   Noon UTC keeps the rendered calendar date identical in all time zones from
   UTC-12 to UTC+11. If a milestone already displays early, PATCH it with the
   noon-UTC value; no recreation is needed.
5. **Do not chain `gh milestone ... || gh api ...` as a fallback.** The usage
   error and the fallback's success output interleave, so the log cannot show
   which path ran. Select the REST path directly; it is the only supported
   path for milestone mutation.
6. **Re-sweeps are normal operation.** New issues and pull requests arrive
   between sweeps with no milestone. Run the two unassigned queries first,
   classify only the unassigned set, assign, and re-verify. A sweep is done
   only when both queries return zero and the failure log is empty.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Milestone creation via CLI | `gh milestone create --title ... --due-date ...` | The `gh` CLI has no milestone subcommand; it prints a usage error and creates nothing. | Milestone create, update, and list exist only under `gh api repos/{owner}/{repo}/milestones`. |
| Midnight-UTC due dates | `due_on="2026-10-30T00:00:00Z"` on all new milestones | Every milestone rendered one day early in the web UI (viewing account behind UTC). | Use `T12:00:00Z` for date-only intents; repair existing milestones with a PATCH. |
| Fallback-chained creation | `gh milestone create ... || gh api ...` | The usage error and fallback output interleaved, making the creation log ambiguous. | Call the supported command directly; a `||` chain hides which branch executed. |
| Issue-only sweep | Assigned all open issues and verified zero unassigned issues | The release board still showed unassigned pull requests; milestone state spans both kinds. | Sweep and verify `gh pr list` separately from `gh issue list`; both counts must be zero. |

## Results & Parameters

### Configuration

| Parameter | Value | Notes |
| --------- | ------- | ------- |
| `due_on` | `YYYY-MM-DDT12:00:00Z` | Noon UTC for every date-only milestone due date. |
| `gh issue list --limit` | 1000 | Default page size truncates large backlogs silently. |
| `gh pr list --limit` | 500 | Same reason as above. |
| Failure log | one `kind#number -> milestone` line per failed edit | Inspect before any verification claim. |

### Expected Output

- `gh api repos/{owner}/{repo}/milestones` lists each milestone with the
  intended `due_on` calendar date and live `open_issues`/`closed_issues`
  counts.
- Both unassigned queries return `0`.
- The failure log is empty.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private multi-service monorepo | 2026-10 release-train setup: 13 milestones, approximately 700 open issues, all open pull requests | Full mechanics and the midnight-UTC observation are in [github-milestone-gh-cli-release-sweep.notes.md](../skills/github-milestone-gh-cli-release-sweep.notes.md). |

## References

- [GitHub REST API: milestones](https://docs.github.com/en/rest/issues/milestones)
- [gh CLI manual: issue edit / pr edit](https://cli.github.com/manual/)
- [Related skill: audit-epic-sequencing-milestone-attachment](audit-epic-sequencing-milestone-attachment.md)
