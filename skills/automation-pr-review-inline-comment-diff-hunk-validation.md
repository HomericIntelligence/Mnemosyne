---
name: automation-pr-review-inline-comment-diff-hunk-validation
description: >-
  Validate LLM/agent-generated inline PR-review comments against the PR diff
  hunks before POSTing the review, so GitHub does not reject the entire review
  with HTTP 422. Use when: (1) writing/editing code that POSTs a PR review with
  inline comments via `gh api -X POST .../pulls/{n}/reviews`, (2) a runtime log
  shows `gh: Unprocessable Entity (HTTP 422)` on a review POST, (3) an LLM/agent
  generates inline review comments (path/line/side) that may not lie on a
  changed line, (4) an automation loop records a spurious NOGO/Grade=F because
  the in-loop review POST failed, (5) the diff shown to a review model is
  truncated so it can cite real-but-out-of-hunk lines.
category: tooling
date: 2026-06-06
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - github-api
  - pull-request-review
  - 422
  - unprocessable-entity
  - diff-hunk
  - inline-comments
  - llm-generated-comments
  - fail-open
  - automation-pipeline
---

## Overview

| Field | Value |
|-------|-------|
| Date | 2026-06-06 |
| Objective | Stop GitHub from 422'ing an entire PR review because one LLM-generated inline comment points at a line that is not in the diff hunk. |
| Outcome | `gh_pr_review_post` now parses the unified diff into accepted (line, side) positions, drops + logs out-of-hunk comments, and still posts the summary review with whatever survives. Spurious NOGO/Grade=F from a 422'd in-loop review is eliminated. |
| Verification | verified-ci — fix merged to ProjectHephaestus `main` (PR #1043, closes #1039) with new unit/integration tests covering the 422 path and the pure hunk parser. |

## When to Use

- You are writing or editing code that POSTs a PR review carrying inline
  comments via `gh api -X POST /repos/{owner}/{repo}/pulls/{n}/reviews`.
- A runtime log shows `gh: Unprocessable Entity (HTTP 422)` on a review POST.
- An LLM or agent generates inline review comments (`path`/`line`/`side`) and
  those positions may not land on a changed line of the PR.
- An automation loop records a spurious `Verdict=NOGO` / `Grade=F` because the
  in-loop review POST failed (not because the code was actually bad).
- The diff handed to a review model is truncated (e.g. to 8000 chars), so the
  model can cite real lines that are nonetheless outside the visible hunk.

## Verified Workflow

1. **Fetch the FULL diff, not the truncated review context.** The reviewer
   model may only see a truncated diff (8000 chars), but validation must run
   against the complete PR diff. Use `gh pr diff <n>` (or
   `GET /repos/{owner}/{repo}/pulls/{n}` with `Accept: application/vnd.github.v3.diff`).
   Validating against the truncated context would wrongly drop valid comments on
   large diffs.

2. **Parse the unified diff once into a set of accepted (line, side) positions
   per file.** Walk hunk headers and track new-file and old-file line counters:
   - `RIGHT` side = added (`+`) lines and context (` `) lines, numbered in the
     NEW file.
   - `LEFT` side = removed (`-`) lines and context (` `) lines, numbered in the
     OLD file.
   - Hunk header form: `@@ -oldStart,oldLen +newStart,newLen @@` — the `,len`
     part is optional (e.g. `@@ -1 +1 @@`), so parse defensively.

3. **Filter the LLM comments.** Keep each comment whose `(path, line, side)`
   tuple is in the accepted set. DROP the rest, and LOG each dropped comment at
   `WARNING` (with path/line/side) so the loss is visible.

4. **Still POST the summary review with whatever remains.** The summary-only
   path (empty `comments` array) works fine against the reviews endpoint, so an
   all-dropped review still delivers the body/event verdict.

5. **FAIL OPEN.** If the diff is empty or could not be fetched, return the
   comments UNCHANGED. Dropping feedback because the diff fetch hiccuped is worse
   than a possible 422.

6. **Add the missing tests.** The post-reviews path had NO test exercising a 422
   / out-of-hunk comment (existing tests mocked `gh_pr_review_post` or returned
   success). Add: (a) out-of-hunk comment filtered while in-hunk survives,
   (b) all-out-of-hunk → summary-only POST, (c) empty diff → fail open, and
   (d) pure unit tests of the hunk parser for RIGHT/LEFT/context numbering.

### Quick Reference

```text
Hunk header parse rule:
  @@ -oldStart[,oldLen] +newStart[,newLen] @@
        ^old counter         ^new counter      (",len" is OPTIONAL)

Side mapping (which (line, side) GitHub accepts):
  RIGHT : added '+' lines AND context ' ' lines, numbered in the NEW file
  LEFT  : removed '-' lines AND context ' ' lines, numbered in the OLD file

Pipeline:
  full_diff = gh pr diff <n>            # NOT the 8000-char model context
  accepted  = parse(full_diff)          # {path -> {(line, side)}}
  kept      = [c for c in comments if (c.line, c.side) in accepted[c.path]]
  # log+drop the rest at WARNING
  if not full_diff: return comments     # FAIL OPEN
  POST review(body, event, comments=kept)   # summary-only is OK if kept == []
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Post comments unvalidated | `gh_pr_review_post` in `hephaestus/automation/github_api.py` mapped LLM comment dicts (`path`, `line`, `side`, `body`) straight into the `POST .../pulls/{n}/reviews` payload with no diff check. | GitHub rejects the ENTIRE review with HTTP 422 if ANY single comment is out-of-hunk; the in-loop implementer then logged a spurious `Verdict=NOGO Grade=F`. | One bad comment poisons the whole review — validate every `(path, line, side)` against the diff before POST. |
| Validate against the truncated context diff | Reuse the 8000-char diff already shown to the reviewer model as the source of accepted positions. | On large PRs the truncation omits real hunks, so valid in-hunk comments would be wrongly dropped. | Validation needs the FULL `gh pr diff`, not the model's truncated context. |
| Fail closed on empty diff | If the diff was empty/unavailable, drop all comments to be "safe". | A transient diff-fetch hiccup would silently discard all reviewer feedback. | FAIL OPEN: when the diff is unavailable, return comments unchanged — a possible 422 beats guaranteed silent feedback loss. |

## Results & Parameters

- **Root cause**: `gh_pr_review_post` mapped LLM-produced comment dicts straight
  into the reviews payload with NO validation that each `(path, line, side)`
  lies on a line present in the PR diff. GitHub 422s the whole review on any
  out-of-hunk comment; the loop recorded it as a spurious `Verdict=NOGO
  Grade=F`. Amplified because the diff shown to the reviewer model was truncated
  to 8000 chars (the model cites real-but-out-of-hunk lines).
- **Fix**: parse the unified diff once into accepted `(line, side)` positions per
  file, filter comments to that set, drop + log the rest at WARNING, and still
  POST the summary review with whatever remains. Fail open on empty/unavailable
  diff.
- **Endpoint**: `POST /repos/{owner}/{repo}/pulls/{n}/reviews` (via
  `gh api -X POST`). Failure mode: `gh: Unprocessable Entity (HTTP 422)`.
- **Side semantics**: `RIGHT` = `+`/context lines numbered in the new file;
  `LEFT` = `-`/context lines numbered in the old file.
- **Hunk header**: `@@ -oldStart,oldLen +newStart,newLen @@`; the `,len` is
  optional — parse defensively.
- **Design invariant**: fail OPEN — never drop comments because the diff could
  not be fetched.
- **Source**: `hephaestus/automation/github_api.py` (`gh_pr_review_post`).
- **Verification**: verified-ci — merged to ProjectHephaestus `main` via PR
  #1043 (closes #1039) with new tests for the 422/out-of-hunk path and the pure
  hunk parser.
