---
name: documentation-github-issue-final-report-live-body
license: BSD-3-Clause
description: "Rewrite GitHub issues, PR bodies, comments, and evidence mirrors into coherent public reports without overwriting live edits or leaking local operator details. Use when: (1) an issue has accumulated investigation notes, follow-up phrasing, or stale detours, (2) the user asks for a final report-style issue body, (3) sensitive or model-specific details must be removed before publishing, (4) automation evidence may contain local filesystem paths or usernames."
category: documentation
date: 2026-07-06
version: "1.1.0"
user-invocable: false
verification: verified-ci
history: documentation-github-issue-final-report-live-body.history
tags: [github, issues, pull-requests, comments, evidence-mirrors, final-report, live-body, redaction, documentation, public-artifact-hygiene, local-path-sanitization]
---

# GitHub Issue Final Report Live Body

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-06 |
| **Objective** | Convert GitHub issue/PR public artifacts from incremental investigation transcripts into coherent final reports while preserving user edits and removing stale, sensitive, or local-operator details. |
| **Outcome** | Successful. The safe workflow reads the current live issue/PR body and comments, checks for concurrent edits, sanitizes public evidence including older comments and mirrors, publishes once, then verifies required content and forbidden local identifiers are absent. |
| **Verification** | verified-ci - public artifact hygiene for ProjectHephaestus PR #1854 / issue #1818 passed the PR gate; local full automation tests 3237 passed and affected slice 190 passed. |
| **History** | [changelog](./documentation-github-issue-final-report-live-body.history) |

## When to Use

- A GitHub issue body contains chronological debugging notes, follow-up language, or obsolete side investigations.
- The user asks for the issue to read as a final report rather than an activity log.
- You need to avoid overwriting edits that may have happened since your last local draft.
- The issue should preserve technical evidence while removing user-error detours, stale checklists, or unnecessary operational specifics.
- The report must protect model-specific, endpoint-specific, host-specific, path-specific, or other internal identifiers.
- A PR body, issue comment, automation evidence mirror, or final run report may have copied local paths, home-directory fragments, or operator usernames into a public artifact.
- You need to clean older comments as well as the latest body because durable public evidence is spread across the issue/PR timeline.

## Verified Workflow

### Quick Reference

```bash
# 1. Fetch the current live body. Treat this as source of truth.
gh issue view <issue-number> --repo <owner>/<repo> \
  --json body --jq '.body' > /tmp/issue-live.md

# 2. Capture metadata for a concurrent-edit guard.
gh issue view <issue-number> --repo <owner>/<repo> \
  --json number,title,state,url,updatedAt --jq '.'

# 3. Draft the replacement body locally.
$EDITOR /tmp/issue-final.md

# 4. Re-check updatedAt immediately before editing.
gh issue view <issue-number> --repo <owner>/<repo> \
  --json updatedAt --jq '.updatedAt'

# 5. Publish only if updatedAt is unchanged or the newer body has been merged.
gh issue edit <issue-number> --repo <owner>/<repo> \
  --body-file /tmp/issue-final.md

# 6. Fetch and verify the live final body.
gh issue view <issue-number> --repo <owner>/<repo> \
  --json body --jq '.body' > /tmp/issue-live-final.md

rg -n "## Summary|## Final Finding|## Evidence|## Acceptance Criteria" /tmp/issue-live-final.md
rg -n "follow-up|previously unchecked|remaining|still untested|intermediate detour" /tmp/issue-live-final.md
rg -n "/mnt|/home|home/|/Users|Users/|<operator-username>" /tmp/issue-live-final.md
```

### Detailed Steps

1. **Read the live issue body first.** Do not reuse an older local draft as the source of truth after the user says they edited or wants to avoid overwrites.
2. **Capture `updatedAt`.** Use it as a simple guard against concurrent edits between read and write.
3. **Identify the final report structure.** Prefer sections like Summary, Final Finding, Environment, Evidence, Reproduction Matrix, Controls, Logs, Bad Behavior, Expected Behavior, Reproduction Steps, Acceptance Criteria, and Validation.
4. **Convert chronology into conclusions.** Replace "follow-up testing" and "still unchecked" phrasing with final-state statements such as "tested", "observed", "not observed", or "inconclusive".
5. **Remove stale detours.** If an intermediate problem was unrelated to the final diagnosis, omit it unless it materially changes the conclusion.
6. **Protect sensitive details.** Replace model IDs, endpoint addresses, hostnames, job IDs, absolute paths, internal repo names, usernames, and proprietary payloads with placeholders or generic descriptions unless the user explicitly asks to retain them.
7. **Keep enough evidence to reproduce.** Preserve response shape, request shape, relevant flags, logs, control results, and acceptance criteria, but sanitize identifiers.
8. **Re-check `updatedAt` before publishing.** If the timestamp changed, fetch the body again and merge the user edits before editing.
9. **Sanitize every public surface, not only the latest body.** Search the PR body, issue body, issue comments, PR comments, review comments, and any evidence mirror that automation posts or links. Edit older comments too; leaving an old leaked path in the timeline defeats the cleanup.
10. **Scan for local operator details before posting or updating.** Treat these as forbidden in public artifacts unless explicitly approved: `/mnt`, `/home`, `home/`, `/Users`, `Users/`, absolute checkout paths, local cache paths, usernames, hostnames, job scratch paths, and raw evidence paths.
11. **Verify the live result, not the local file.** Fetch the GitHub body/comments after editing and check both required sections and forbidden stale phrasing plus forbidden local-identifier patterns.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Editing from an old local draft | Reused a body file after additional live edits may have occurred | Risked overwriting user changes or resurrecting stale language | Always re-read the live issue body before a rewrite |
| Leaving chronological investigation language | Kept phrases like "follow-up", "previously unchecked", or intermediate detours | The issue read like a work log instead of a final bug report | Rewrite in final-state language once the investigation is complete |
| Over-preserving raw evidence | Included raw identifiers and detailed operational paths | Durable issue bodies can leak unnecessary internal information | Keep response shapes and conclusions; redact identifiers and proprietary payloads |
| Cleaning only the latest artifact | Updated the current PR body or latest issue comment but left older automation comments and evidence mirrors untouched | Public timeline still exposed local filesystem paths or operator usernames even though the newest artifact looked clean | Scan and edit every durable public surface: PR body, issue body, comments, review comments, and evidence mirrors |
| Publishing without absence checks | Verified only that new sections existed | Old misleading phrases or leaked local identifiers can remain and undermine the final report | Check both presence of required sections and absence of stale wording plus `/mnt`, `/home`, `home/`, `/Users`, `Users/`, and username patterns |

## Results & Parameters

### Final Report Section Order

```text
## Summary
## Final Finding
## Date And Environment
## Runtime Context
## Template Or Parser Evidence
## Request Shape
## Response Evidence
## Reproduction Matrix
## Control Results
## Endpoint Checks
## Log Evidence
## Bad Behavior
## Expected Behavior
## Reproduction Steps
## Acceptance Criteria
## Validation
```

### Concurrent Edit Guard

```text
1. Fetch live body.
2. Record updatedAt.
3. Draft local replacement.
4. Re-fetch updatedAt immediately before `gh issue edit`.
5. If changed, stop and merge live edits before publishing.
```

### Public Artifact Hygiene Scan

```bash
# Fetch durable public artifacts into a temp directory, then scan them before posting/updating.
rg -n "/mnt|/home|home/|/Users|Users/|<operator-username>|<local-hostname>" /tmp/public-artifacts
# Expected: no output. If matches appear, redact and re-fetch live artifacts after editing.
```

Surfaces to check:

- PR body and issue body.
- Issue comments and PR comments, including older automation comments.
- Review comments and resolved-thread summaries.
- Evidence mirrors, status reports, and final-run comments produced by automation.
- Any linked public gist, artifact summary, or markdown file copied from local run evidence.

### Redaction Checklist

- No model IDs or model-family names unless explicitly approved.
- No endpoint IPs, hostnames, ports, or internal URLs unless explicitly approved.
- No job IDs, process IDs, usernames, cluster names, or allocation identifiers.
- No absolute paths, checkpoint paths, local cache paths, or evidence mirror paths.
- No home-directory fragments such as `/mnt`, `/home`, `home/`, `/Users`, or `Users/`.
- No full raw reasoning output unless explicitly approved and clearly truncated.
- No obsolete auth/user-error detours unless they are part of the final diagnosis.

### Live Verification Checklist

```bash
# Required content should exist.
rg -n "## Summary|## Final Finding|## Acceptance Criteria|## Validation" /tmp/issue-live-final.md

# Stale wording should be absent.
rg -n "follow-up|previously unchecked|remaining|still untested|intermediate detour" /tmp/issue-live-final.md
rg -n "/mnt|/home|home/|/Users|Users/|<operator-username>" /tmp/issue-live-final.md
# Expected: no output, exit code 1.
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| GitHub issue tracker | Final report rewrite after operational debugging | Sanitized workflow only; no issue number, model IDs, endpoints, paths, jobs, or raw proprietary payloads retained |
| ProjectHephaestus | PR #1854 / issue #1818 public automation evidence cleanup | Scanned and removed absolute local filesystem paths and operator usernames from public PR/issue evidence, including older comments rather than only the latest artifact. Final head `30287af`; Required Checks `28771968071`, Test `28771968016`, and HOL Plugin Scanner `28771968083` succeeded; local full automation suite 3237 passed and affected slice 190 passed. |
