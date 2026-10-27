---
name: github-commit-sha-readback-pr-scoped-routes
description: "Read commit evidence for a pull-request head through PR-scoped routes when a direct commit lookup is rejected. Use when: (1) `gh api repos/<owner>/<repo>/commits/<sha>` returns 422 for an object identifier that the pull request plainly contains, (2) the identifier is reachable only through a pull-request ref or another repository in the fork network, (3) push verification must read the hosted signature state of an exact head, or (4) a script must resolve commit evidence identically for same-repository and fork pull requests."
category: tooling
date: 2026-10-27
version: "1.0.0"
user-invocable: false
license: BSD-3-Clause
verification: verified-live
tags:
  - gh-api
  - github
  - commit-verification
  - pull-requests
  - fork-network
  - readback
  - evidence
  - signature-verification
---

# GitHub Commit SHA Readback Through PR-Scoped Routes

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-27 |
| **Objective** | Read hosted commit evidence (signature state, existence, parentage) for an exact pull-request head without depending on one endpoint's reachability rules. |
| **Outcome** | Successful. A 422 from the generic commit lookup was replaced by the PR-scoped commit listing, which returned the complete evidence set for the same head, including the hosted verification state. |
| **Verification** | verified-live during a multi-repository review sweep: the rejection and both working routes were observed on the same object identifiers. |

## When to Use

- `GET /repos/<owner>/<repo>/commits/<sha>` answers 422 for an identifier that the pull request references.
- The identifier sits behind `refs/pull/<n>/head` rather than a branch ref, or belongs to a fork in the same network.
- A push-verification step must read `.commit.verification.verified` for every introduced commit.
- A script must behave the same for same-repository and fork pull requests.

## Verified Workflow

### Quick Reference

```bash
# Preferred: one call returns every PR commit with hosted verification state.
gh api repos/<OWNER>/<REPO>/pulls/<N>/commits \
  --jq '[.[] | {sha:.sha,verified:.commit.verification.verified,reason:.commit.verification.reason}]'

# Alternative: materialize the head locally, then use any local git read.
git fetch origin refs/pull/<N>/head
```

### Suggested Approach

1. **Treat a 422 as a reachability signal, not as a missing commit.** The
   generic commit lookup resolves objects reachable from the named
   repository's refs. An identifier that only a pull-request ref names can be
   rejected even though the pull request displays it.
2. **Switch to the PR-scoped listing.** `GET /repos/<o>/<r>/pulls/<n>/commits`
   returns the introduced commits with their verification state in one call.
   It works for same-repository and fork pull requests.
3. **Or materialize the head locally.** Fetch `refs/pull/<n>/head` into a
   clone and answer existence, parentage, and diff questions with local git
   reads. This also completes an anchor source for later verification.
4. **Normalize byte-exact readbacks.** When a digest binds a read-back body,
   remember that `gh api --jq .body` appends one trailing LF; strip exactly one
   final LF before comparison. See the record-repair skill in References.
5. **Keep one evidence path per assertion.** Record which route produced each
   piece of evidence, so a later reader can reproduce it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Verify the pushed head through the generic commit endpoint | Called `GET /repos/<o>/<r>/commits/<sha>` immediately after push | 422 for an identifier reachable only through the pull-request ref | Use the PR-scoped routes for pull-request evidence |
| Retry the same endpoint | Repeated the lookup to rule out a transient fault | The rejection was deterministic reachability, not rate or state | Change the route, not the retry count |
| Conclude the commit was absent | Read the 422 as non-existence | The commit existed and the pull request listed it | A 422 on this endpoint is a routing result; confirm existence through the PR listing |

## Results & Parameters

### Configuration

```yaml
evidence_routes:
  pr_scoped_listing: GET /repos/{owner}/{repo}/pulls/{n}/commits   # verification state included
  local_materialization: git fetch origin refs/pull/{n}/head       # then local git reads
  generic_lookup: GET /repos/{owner}/{repo}/commits/{sha}          # branch-reachable identifiers only
byte_readback:
  trailing_lf: gh api --jq appends one LF; strip exactly one before byte compares
failure_semantics:
  http_422: reachability, not non-existence; switch route
```

### Expected Output

- The PR-scoped listing returns every introduced commit with `verified` and
  `reason` fields.
- A 422 from the generic endpoint no longer appears in the evidence path.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A multi-repository review sweep | Push verification of signed heads across same-repository and fork pull requests; the PR-scoped listing replaced the rejected generic lookup | Route details in this skill; byte-readback normalization in the referenced record-repair skill |

## References

- [GitHub REST API: pull request commits](https://docs.github.com/en/rest/pulls/commits)
- [github-pr-review-record-void-repair.md](github-pr-review-record-void-repair.md) — canonical record of the trailing-LF readback behavior
- [git-commit-signing-failures-and-setup.md](git-commit-signing-failures-and-setup.md) — hosted signature verification workflow
