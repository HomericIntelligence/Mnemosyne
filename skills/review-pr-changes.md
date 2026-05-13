---
name: review-pr-changes
description: "Review PR changes with a structured checklist, strict GitHub review posting, inline comments, per-file grading, and GO/NO-GO release readiness summary. Use when: (1) reviewing PRs before approval, (2) asked for a strict review, (3) asked to add review comments, (4) needing REQUEST_CHANGES with actionable inline findings."
category: tooling
date: 2026-05-13
version: "1.1.0"
user-invocable: false
verification: verified-local
history: review-pr-changes.history
tags: [github, pr-review, strict-review, request-changes, inline-comments, per-file-grading]
---

# Review PR Changes with Checklist

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-13 |
| **Objective** | Perform structured PR review, attach actionable GitHub review comments, and publish a strict per-file GO/NO-GO summary |
| **Outcome** | Operational; PR288 review was submitted as `CHANGES_REQUESTED` with five inline comments and API readback verification |
| **Verification** | verified-local - live GitHub review workflow executed on `LLM360/RL360#288`; ProjectMnemosyne validation pending |
| **History** | [changelog](./review-pr-changes.history) |

## When to Use

- Reviewing a PR before approving or merging
- Performing a strict review with release-readiness grading
- Adding GitHub review comments directly to changed lines
- Requesting changes with an overall `GO`, `Conditional Go`, or `NO-GO` verdict
- Producing a per-file grade table for reviewers or maintainers
- Checking standards compliance, test coverage, security exposure, or architectural impact
- Verifying that comments attach to the intended PR head SHA and diff lines

## Verified Workflow

### Quick Reference

```bash
# Fetch current PR metadata
gh pr view <pr> --repo OWNER/REPO \
  --json url,title,state,isDraft,mergeStateStatus,reviewDecision,headRefOid,baseRefOid

# List changed files
gh api repos/OWNER/REPO/pulls/<pr>/files --paginate \
  --jq '.[] | [.filename, .status, .additions, .deletions] | @tsv'

# Check CI status
gh pr checks <pr> --repo OWNER/REPO

# Read existing reviews and comments to avoid duplicates
gh api repos/OWNER/REPO/pulls/<pr>/reviews --jq '.[] | [.id, .user.login, .state] | @tsv'
gh api repos/OWNER/REPO/pulls/<pr>/comments --paginate \
  --jq '.[] | [.id, .user.login, .path, .line, .body] | @tsv'

# Submit a review with inline comments
gh api --method POST repos/OWNER/REPO/pulls/<pr>/reviews --input review.json

# Verify comments landed on intended lines
gh api repos/OWNER/REPO/pulls/<pr>/comments --paginate \
  --jq '.[] | select(.pull_request_review_id==REVIEW_ID) | [.id, .path, .line, .side] | @tsv'
```

### Strict Review Posting Workflow

1. **Fetch PR truth first**

   Capture PR URL, title, draft state, merge state, base SHA, head SHA, changed files,
   existing reviews, existing comments, and checks. Do not review from stale browser state.

2. **Review the actual diff and run targeted verification**

   Read the changed files at the PR head and run checks suited to the patch:
   shell syntax for shell scripts, Python compile/tests for Python changes, `git diff --check`
   for whitespace, workflow validation where available, and CI status via `gh pr checks`.

3. **Draft findings as actionable inline comments**

   Prefer inline comments for defects that have a specific file and line. Use blocker-level
   language for correctness, security, reproducibility, or launch failures. Keep optional
   suggestions out of `REQUEST_CHANGES` unless they affect release readiness.

4. **Build a per-file grade table**

   Grade each changed file independently and assign a verdict:

   - `Go`: no blocking or major issue in the file
   - `Conditional Go`: acceptable only after specific validation or minor cleanup
   - `No-Go`: file contains a blocker or unvalidated high-risk behavior

5. **Re-fetch the PR head SHA before posting**

   Confirm the head SHA has not changed since drafting. Verify every target path and line
   still exists in the current diff. If the SHA moved, re-review the affected diff before
   posting.

6. **Submit one GitHub review**

   Use one `REQUEST_CHANGES` review when there are blockers. Put the per-file grading and
   final GO/NO-GO verdict in the review body. Put each actionable defect in the `comments`
   array so maintainers can resolve threads line by line.

7. **Read the review back**

   Fetch the submitted review and comments. Confirm the review state, commit SHA, file paths,
   lines, and comment count. If any comment became file-level or attached to the wrong line,
   follow up immediately.

## Review Checklist

**Code Quality**:

- [ ] Code is readable and well-structured
- [ ] Functions/classes have clear purposes
- [ ] Variable names are descriptive
- [ ] Complex logic is commented
- [ ] No code duplication (DRY principle)
- [ ] Follows project naming conventions

**Testing**:

- [ ] Tests present for new functionality
- [ ] Tests are passing or CI status is explicitly called out
- [ ] Edge cases covered in tests
- [ ] Test names describe what they test
- [ ] No skipped or xfail tests without justification
- [ ] Adequate coverage for changed behavior

**Documentation**:

- [ ] Docstrings for public APIs
- [ ] README or operational docs updated if needed
- [ ] Comments explain non-obvious code only
- [ ] Examples provided for complex features
- [ ] Type hints or schema changes are documented

**Security & Safety**:

- [ ] No hardcoded secrets/tokens
- [ ] No secrets exposed through generated scripts, logs, argv, or CI summaries
- [ ] Inputs validated before use
- [ ] Error handling is explicit and observable
- [ ] No unsafe or surprising side effects

**GitHub Review Mechanics**:

- [ ] Current PR head SHA verified immediately before posting
- [ ] Existing comments checked to avoid duplicate review noise
- [ ] Inline comments target changed lines in the current diff
- [ ] Review summary includes per-file grades and final GO/NO-GO
- [ ] Submitted review read back via API

## Error Handling

| Problem | Solution |
| --------- | ---------- |
| Cannot access PR | Check `gh auth status` and repository name |
| No checks reported | Mention explicitly in summary; do not infer validation passed |
| Head SHA changed | Re-review the changed diff before posting |
| Inline line is invalid | Recompute against current diff and retry before submitting |
| Multiple blockers | Submit one `REQUEST_CHANGES` review with multiple inline comments |
| Only minor suggestions | Use `COMMENT`, not `REQUEST_CHANGES` |

## Review Standards

Approve when:

- No critical or major issues remain
- Tests/checks passed for the relevant behavior
- Documentation and operational paths are accurate
- No security or reproducibility concerns remain

Request changes when:

- Correctness, launchability, security, or reproducibility blockers are present
- Tests/checks are missing for high-risk behavior
- The PR claims safety/equivalence that the code does not prove
- A file-level `No-Go` verdict is warranted

Comment when:

- Only minor suggestions remain
- The review is informational or asks clarifying questions
- The PR needs human confirmation but no direct code change yet

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Stale line/head review | Drafted comments from an earlier diff snapshot | GitHub comments can attach to wrong lines or fail if the PR head moved | Re-fetch head SHA and verify target lines immediately before posting |
| PR-level-only feedback | Put all findings in the review body | Maintainers lose line-level resolution threads and actionable context | Use inline comments for defects with a concrete file and line |
| Summary without per-file grading | Gave only an overall verdict | Release readiness was hidden when one file was safe and another was a blocker | Include per-file grades plus an overall GO/NO-GO |

## Results & Parameters

PR288 evidence from `LLM360/RL360`:

- Review ID: `4284402017`
- Review state: `CHANGES_REQUESTED`
- Head SHA: `825525d73b24be56a444ffab90de5fc3164261ed`
- Inline comments:
  - `3236617139`: `scripts/train/run-xllm-375B-bbq-r3-32k.sh:9`
  - `3236617145`: `scripts/train/run-xllm-375B-bbq-r3-32k.sh:667`
  - `3236617149`: `scripts/train/run-xllm-375B-bbq-r3-128k.sh:703`
  - `3236617153`: `scripts/train/run-xllm-375B-bbq-r3-32k.sh:381`
  - `3236617156`: `scripts/train/run-xllm-375B-bbq-r3-128k.sh:399`

Recommended review body shape:

```markdown
## Strict review summary

Overall verdict: **NO-GO / CHANGES_REQUESTED**.

| File | Grade | Verdict | Notes |
| --- | --- | --- | --- |
| path/to/file | D | No-Go | Blocking issue summary |

Required before merge:
1. Fix blocker A.
2. Add or attach validation B.
```

## References

- See `gh-review-pr` for a lighter PR review workflow
- See `gh-get-review-comments` for collecting existing review threads
- See `training-rl360-xllm-launcher-review-pitfalls` for PR288 domain-specific findings
