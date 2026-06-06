---
name: automation-github-graphql-field-validation-live-schema
description: "A GitHub GraphQL mutation/query that selects a non-existent output field — OR names a mutation whose Input type lacks the argument you pass — fails on EVERY call (`Field 'X' doesn't exist on type 'Y'` for a bad output selection; `InputObject '<Input>' doesn't accept argument '<arg>'` + `Variable $X is declared by <Mutation> but not used` for a wrong mutation name), and a code path with no direct unit test can ship such a broken query indefinitely. Validate every field selection AND every input argument against the LIVE schema via introspection before shipping. Use when: (1) writing or editing a raw `gh api graphql` query/mutation string (especially `addPullRequestReview`, `addPullRequestReviewThreadReply`, `reviewThreads`, or any PR-review traversal), (2) a runtime log shows `gh: Field '<field>' doesn't exist on type '<Type>'`, `gh: InputObject '<Input>' doesn't accept argument '<arg>'`, `Variable $X is declared by <Mutation> but not used`, or repeated identical mutation failures, (3) you need to read a parent object off a child node (e.g. a comment's thread or review) and are assuming a reverse edge exists, (4) a function that builds a GraphQL query has no direct unit test and is only mocked out by higher-level callers, (5) an automation loop treats a PR as NOGO/re-runs forever because an in-loop review/comment/reply never posts."
category: tooling
date: 2026-06-05
version: "1.1.0"
user-invocable: false
verification: verified-ci
history: automation-github-graphql-field-validation-live-schema.history
tags:
  - graphql
  - github-api
  - schema-introspection
  - field-validation
  - input-argument-validation
  - wrong-mutation-name
  - addPullRequestReview
  - addPullRequestReviewThreadReply
  - resolveReviewThread
  - reviewThreads
  - pull-request-review
  - silent-broken-query
  - missing-unit-test
  - child-to-parent-edge
  - gh-api-graphql
  - automation-pipeline
---

# Automation: Validate GitHub GraphQL Field Selections Against the Live Schema

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-05 |
| **Objective** | Stop a GitHub GraphQL mutation/query from selecting a non-existent output field OR naming a mutation whose Input type lacks the argument you pass (both fail on EVERY call), by validating every field selection AND every input argument against the live schema via introspection before shipping, and by giving every raw-query function a direct unit test. |
| **Outcome** | SUCCESS (two confirmed instances). **v1.0.0:** `gh_pr_review_post` selected `pullRequestReviewThread { id isResolved }` on a `PullRequestReviewComment` node; that output field does not exist, so the `addPullRequestReview` mutation failed on every call and NO in-loop PR review ever posted. Fixed by returning only `pullRequestReview { id }` and resolving threads via a separate `pullRequest.reviewThreads` query. Shipped in PR #906 (closes #905). **v1.1.0 (new variant — wrong mutation NAME):** `gh_pr_resolve_thread` replied with `addPullRequestReviewComment(input: {pullRequestReviewThreadId: $threadId, body: $body})`, but `AddPullRequestReviewCommentInput` has NO `pullRequestReviewThreadId` field, so every reply failed with `gh: InputObject 'AddPullRequestReviewCommentInput' doesn't accept argument 'pullRequestReviewThreadId'` + `Variable $threadId is declared by AddReply but not used`; PR review threads were never replied-to or resolved. Fixed by switching the reply mutation to `addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $threadId, body: $body}) { comment { id } }` (the correct Input type). Shipped in PR #1006 (closes #999). |
| **Verification** | verified-ci — both fixes merged/auto-merging this session; every field selection AND input argument validated against the live GitHub schema via `gh api graphql` introspection. v1.1.0: mypy clean tree-wide (315 files), ruff clean, 112 automation tests pass (incl. 3 new). |
| **History** | [changelog](./automation-github-graphql-field-validation-live-schema.history) |

## When to Use

- You are writing or editing a raw `gh api graphql` query/mutation string, especially `addPullRequestReview`, `addPullRequestReviewThreadReply`, `resolveReviewThread`, `reviewThreads`, or any pull-request-review traversal.
- A runtime log shows `gh: Field '<field>' doesn't exist on type '<Type>'`, or you see many identical mutation failures in one automation run (the v1.0.0 case produced 219 identical failures).
- **A runtime log shows `gh: InputObject '<Input>' doesn't accept argument '<arg>'` and/or `Variable $X is declared by <Mutation> but not used`.** This signature means the mutation NAME is wrong (or the arg is): the Input type you named lacks that argument, and the variable you declared never binds. The v1.1.0 case logged `InputObject 'AddPullRequestReviewCommentInput' doesn't accept argument 'pullRequestReviewThreadId'` + `Variable $threadId is declared by AddReply but not used`, then 3 retry-exhaustion failures. Fix: introspect the Input type's `inputFields` (NOT just the output type's `fields`) and pick the mutation whose Input actually accepts your argument (here `addPullRequestReviewThreadReply` / `AddPullRequestReviewThreadReplyInput`).
- You need to read a parent object from a child node (e.g. a comment's thread, or a comment's review) and are assuming a reverse edge exists on the child.
- A function that builds a GraphQL query/mutation has NO direct unit test and is only mocked out by higher-level callers.
- An automation loop treats a PR as NOGO and re-runs forever because an in-loop review, comment, or thread reply never actually posts.

## Verified Workflow

### Quick Reference

Validate any field selection against the LIVE schema BEFORE shipping. There is no
compile-time check — an invalid selection ships silently and fails at runtime:

```bash
# List every OUTPUT field that actually exists on a type:
gh api graphql -f query='{ __type(name: "PullRequestReviewComment") { fields { name } } }'

# Inspect a connection's node fields (e.g. what a reviewThread exposes):
gh api graphql -f query='{ __type(name: "PullRequestReviewThread") { fields { name } } }'
gh api graphql -f query='{ __type(name: "PullRequestReview") { fields { name } } }'

# List the INPUT arguments a mutation's Input type accepts (validates the args you pass):
gh api graphql -f query='{ __type(name: "AddPullRequestReviewCommentInput") { inputFields { name } } }'
gh api graphql -f query='{ __type(name: "AddPullRequestReviewThreadReplyInput") { inputFields { name } } }'
# ...and confirm the payload's leaf fields for the response selection set:
gh api graphql -f query='{ __type(name: "AddPullRequestReviewThreadReplyPayload") { fields { name } } }'
```

Correct PR-review-thread reply (the v1.1.0 fix — right mutation NAME + right Input):

```graphql
# WRONG: AddPullRequestReviewCommentInput has no pullRequestReviewThreadId field.
# addPullRequestReviewComment(input: { pullRequestReviewThreadId: $threadId, body: $body }) { ... }

# CORRECT: addPullRequestReviewThreadReply takes pullRequestReviewThreadId + body.
mutation AddReply($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {
    pullRequestReviewThreadId: $threadId,
    body: $body
  }) {
    comment { id }   # AddPullRequestReviewThreadReplyPayload exposes `comment`
  }
}
# Step 2 resolveReviewThread(input: { threadId: $threadId }) was already correct.
```

Correct PR-review post + foreign-thread-safe resolve (fields that ACTUALLY exist):

```graphql
# 1. Mutation: select ONLY pullRequestReview { id } (NOT a comment's thread).
mutation {
  addPullRequestReview(input: {
    pullRequestId: "<PR_NODE_ID>",
    event: COMMENT,
    body: "<review body>",
    comments: [{ path: "<file>", line: <n>, body: "<comment>" }]
  }) {
    pullRequestReview { id }   # PullRequestReview has `id`, NOT `databaseId`
  }
}

# 2. Follow-up query: read threads off the PARENT (pullRequest.reviewThreads),
#    and read each thread's first comment's parent review id (child -> parent).
query {
  repository(owner: "<owner>", name: "<name>") {
    pullRequest(number: <pr>) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes { pullRequestReview { id } }   # comment -> its parent review
          }
        }
      }
    }
  }
}
```

```python
# 3. Keep only unresolved threads created by THE review we just posted
#    ("foreign thread" guarantee — excludes pre-existing human-reviewer threads):
own_thread_ids = [
    t["id"]
    for t in review_threads
    if not t["isResolved"]
    and (t["comments"]["nodes"] or [{}])[0]
        .get("pullRequestReview", {})
        .get("id") == created_review_id
]
```

### Detailed Steps

1. **Before writing the selection set, introspect the type — outputs AND inputs.** For
   every object whose fields you select, run
   `gh api graphql -f query='{ __type(name: "TYPE") { fields { name } } }'` and confirm
   each selected field name is in the returned list. Do this for the mutation payload
   type AND every nested node type. **Equally important: introspect the mutation's Input
   type's `inputFields`** with
   `gh api graphql -f query='{ __type(name: "<Mutation>Input") { inputFields { name } } }'`
   and confirm every argument you pass exists. A wrong mutation name passes a valid-looking
   argument to the WRONG Input type and fails with
   `InputObject '<Input>' doesn't accept argument '<arg>'` + `Variable $X is declared ... but not used`.

2. **Never assume a reverse (child→parent) edge.** A GraphQL connection edge often
   exists in only ONE direction. Here, a `PullRequestReviewComment` has NO thread
   field, and a `PullRequestReviewThread` has NO direct `review` field. The available
   edges are: `PullRequestReview.comments` (parent→child), `PullRequest.reviewThreads`
   (parent→child), and a thread comment's `pullRequestReview { id }` (child→parent).
   If `Child.parent` doesn't exist, fetch via `Parent.children` and filter.

3. **Treat HTTP 200 with an `errors` array as a FAILURE.** `gh api graphql` can return
   exit code 0 with a top-level `errors` array. A bare exit-code check misses it.
   Parse the JSON and surface `data.errors` (or the `errors` key) explicitly.

4. **Give every raw-query function a direct unit test.** Mock `_gh_call` / the
   subprocess, assert the exact query string AND the parsing of a sample response.
   A cheap durable guard: assert the sent query string does NOT contain the
   known-bad field name (e.g. `assert "pullRequestReviewThread" not in sent_query`).
   Mocking the whole function out in higher-level tests is what let the broken
   query ship for a long time.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---|---|---|---|
| 1 | `addPullRequestReview` mutation selected `pullRequestReviewThread { id isResolved }` on each `PullRequestReviewComment` node | That field does NOT exist on `PullRequestReviewComment` — `gh: Field 'pullRequestReviewThread' doesn't exist on type 'PullRequestReviewComment'`; the mutation failed on EVERY call so NO in-loop review ever posted (219 identical failures in one run) | A field selection has no compile-time check; introspect every type with `__type { fields { name } }` against the LIVE schema before shipping |
| 2 | `gh_pr_review_post` had no direct unit test — coverage only mocked it out via `pr_reviewer` tests | The structurally-broken query passed CI indefinitely because nothing exercised the real query string | Any function that builds a raw GraphQL query/mutation MUST have a direct unit test asserting the query string and the parsing; add a guard asserting the known-bad field name is absent |
| 3 | Assumed a comment could report its own thread (read thread off the comment / child) | The reverse edge does not exist; you cannot read a comment's thread off the comment | Child→parent edges often don't exist; fetch threads via `pullRequest.reviewThreads` (parent→child) and filter |
| 4 | Tried selecting `databaseId` on `PullRequestReview` to correlate threads to the review | `PullRequestReview` exposes `id`, not `databaseId`, in the path needed here; correlation must use the node `id` | Confirm the exact identifier field name via introspection; don't assume `databaseId` exists everywhere |
| 5 | (Risk) relied on `gh api graphql` exit code alone to detect success | `gh api graphql` can return HTTP 200 with a top-level `errors` array and still have FAILED | Surface the `errors` array from the JSON response; a bare exit-code check can miss a failed operation |
| 6 | `gh_pr_resolve_thread` Step-1 reply used `addPullRequestReviewComment(input: {pullRequestReviewThreadId: $threadId, body: $body})` | `AddPullRequestReviewCommentInput` has NO `pullRequestReviewThreadId` field (it takes `pullRequestId`/`pullRequestReviewId`/`inReplyTo`/...), so every call failed with `gh: InputObject 'AddPullRequestReviewCommentInput' doesn't accept argument 'pullRequestReviewThreadId'` + `Variable $threadId is declared by AddReply but not used`, then retry-exhaustion — threads were never replied-to or resolved | Introspect the Input type's `inputFields` (NOT just the output type's `fields`) before shipping. The correct mutation for thread replies is `addPullRequestReviewThreadReply` (`AddPullRequestReviewThreadReplyInput` accepts `pullRequestReviewThreadId` + `body`); a wrong mutation NAME yields a DIFFERENT error signature than a wrong output field — `InputObject doesn't accept argument` + `Variable declared but not used`, not `Field doesn't exist on type` |
| 7 | `gh_pr_resolve_thread` had no direct unit test — callers (`address_review`) mock it at the boundary | The broken reply mutation shipped silently for the same reason as v1.0.0 Attempt 2: nothing exercised the real query string | Added a direct unit test (`TestGhPrResolveThread`) pinning the mutation name + call args + `dry_run` no-op; every raw-query function needs a direct test, not just boundary mocks |

## Results & Parameters

**Schema relationships (verified via live introspection, 2026-06-03):**

- `PullRequestReviewComment` has **no** thread field at all (verified:
  `gh api graphql -f query='{ __type(name: "PullRequestReviewComment") { fields { name } } }'`).
- `PullRequestReview` exposes `id` and `comments` (NOT `databaseId` in this path).
- `PullRequestReviewThread` exposes `comments` (no direct `review` field).
- A thread's comment exposes `pullRequestReview { id }` (child→parent), which is how
  you correlate a thread back to the review that created it.

**Mutation Input types (verified via live introspection, 2026-06-05):**

- `AddPullRequestReviewCommentInput.inputFields` = `clientMutationId, pullRequestId,
  pullRequestReviewId, commitOID, body, path, position, inReplyTo` — there is **NO**
  `pullRequestReviewThreadId`. Passing it yields
  `InputObject 'AddPullRequestReviewCommentInput' doesn't accept argument 'pullRequestReviewThreadId'`.
- `AddPullRequestReviewThreadReplyInput.inputFields` = `clientMutationId,
  pullRequestReviewId, pullRequestReviewThreadId, body` — this is the CORRECT Input for
  replying to a review thread by thread id.
- `AddPullRequestReviewThreadReplyPayload.fields` = `clientMutationId, comment` — so
  `{ comment { id } }` is a valid response selection.
- `resolveReviewThread(input: { threadId: ... })` (Step 2) was already correct and unchanged.

**Corrected thread-reply mutation (v1.1.0 — right NAME + right Input + valid leaf):**

```graphql
mutation AddReply($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {
    pullRequestReviewThreadId: $threadId, body: $body
  }) {
    comment { id }
  }
}
```

**Corrected mutation (returns only an existing field):**

```graphql
mutation {
  addPullRequestReview(input: {
    pullRequestId: $prId, event: COMMENT, body: $body, comments: $comments
  }) {
    pullRequestReview { id }
  }
}
```

**Corrected follow-up resolve query + foreign-thread filter:**

```graphql
query {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 1) { nodes { pullRequestReview { id } } }
        }
      }
    }
  }
}
```

Keep unresolved threads whose first comment's `pullRequestReview.id` equals the
review id you just created — this excludes pre-existing human-reviewer threads
(the "foreign thread" guarantee) using fields that actually exist.

**Generalizable lessons (the heart of this skill):**

1. Validate every GraphQL field selection against the LIVE schema via introspection
   BEFORE shipping: `gh api graphql -f query='{ __type(name: "TYPE") { fields { name } } }'`.
   There is no compile-time check; an invalid selection ships silently and the
   `gh` CLI prints `Field 'X' doesn't exist on type 'Y'` only at runtime.
2. `gh api graphql` returning HTTP 200 with an `errors` array still means the
   operation FAILED — surface the `errors` array, don't trust the exit code alone.
3. Any function that builds a raw GraphQL query/mutation MUST have a direct unit
   test (mock `_gh_call`/subprocess, assert the query string and the parsing). A
   cheap durable guard is a unit test asserting the sent query string does NOT
   contain the known-bad field name.
4. Child→parent vs parent→child: a connection edge often exists in only ONE
   direction. If `Child.parent` doesn't exist, fetch via `Parent.children` and filter.
5. **Two distinct error signatures, one discipline.** A wrong OUTPUT field selection
   fails with `Field '<f>' doesn't exist on type '<T>'`. A wrong mutation NAME (so the
   Input type lacks your argument) fails DIFFERENTLY: `InputObject '<Input>' doesn't
   accept argument '<arg>'` + `Variable $X is declared by <Mutation> but not used`.
   Both are caught by the same pre-ship habit — introspect the Input type's
   `inputFields`, not just the output type's `fields`, before shipping.

## Verified On

| Project | File / Issue | Notes |
|---|---|---|
| ProjectHephaestus | `hephaestus/automation/github_api.py` (`gh_pr_review_post`) | v1.0.0: removed non-existent `pullRequestReviewThread` output selection; mutation now returns `pullRequestReview { id }` |
| ProjectHephaestus | Issue #905 / PR #906 | v1.0.0 fix merged 2026-06-03; thread resolution moved to `pullRequest.reviewThreads` follow-up query |
| ProjectHephaestus | `hephaestus/automation/github_api.py` (`gh_pr_resolve_thread`) | v1.1.0: Step-1 reply switched from `addPullRequestReviewComment` (wrong Input — no `pullRequestReviewThreadId`) to `addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId, body}) { comment { id } }`; Step-2 `resolveReviewThread` unchanged |
| ProjectHephaestus | Issue #999 / PR #1006 | v1.1.0 fix merged/auto-merging 2026-06-05; verified-ci — mypy clean (315 files), ruff clean, 112 automation tests pass incl. 3 new (`TestGhPrResolveThread`) |
| GitHub GraphQL API | live schema introspection | v1.0.0: `__type(name: "PullRequestReviewComment" / "PullRequestReviewThread" / "PullRequestReview") { fields }`; v1.1.0: `__type(name: "AddPullRequestReviewCommentInput" / "AddPullRequestReviewThreadReplyInput") { inputFields }` + `AddPullRequestReviewThreadReplyPayload { fields }` confirmed the correct Input type and leaf |
