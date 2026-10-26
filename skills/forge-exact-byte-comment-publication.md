---
name: forge-exact-byte-comment-publication
description: "Publish a machine-verified forge comment byte-exactly. Use when a protocol or exchange helper prepares a comment body and then verifies an exact readback (for example a canonical plan or review carrier), when publication fails with an identity-mismatch diagnostic although the visible text matches, or when a forge CLI or SDK is the write path for such a comment."
category: tooling
date: 2026-10-26
version: "1.0.0"
user-invocable: false
tags: [github, gh-cli, issue-comments, exact-readback, publication, canonical-comment, trailing-newline, byte-exact, recovery]
---

# Forge exact-byte comment publication

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Publish a helper-prepared forge comment so that exact-readback verification passes: the live body must equal the prepared body byte for byte, and the one-comment-per-role invariant must survive a retry. |
| **Outcome** | Successful: the verifier returned a verified receipt after an identity conflict was repaired by an exact-byte update. |

## When to Use

Use this skill when all or some of these conditions apply:

- A helper prepares the exact comment body and the publication does not count until a readback or digest comparison matches it byte for byte.
- The comment is one canonical artifact in a role (for example one plan or one review), so a second create breaks the protocol.
- Publication failed with an identity or conflict diagnostic even though the visible text looks equal.

## Verified Workflow

### Quick Reference

Treat the prepared body as immutable bytes. Write it to the forge in one exact-byte call. Do not re-serialize it through `print`, `echo`, or shell string handling, which can append a newline. With the GitHub CLI:

```bash
# create: file holds the exact prepared bytes, no added terminator
gh api -X POST repos/{owner}/{repo}/issues/<number>/comments -F body=@body.md
# repair an owned comment whose live body drifted
gh api -X PATCH repos/{owner}/{repo}/issues/comments/<id> -F body=@body.md
```

### Suggested Approach

1. Persist the helper's prepared body string by writing the string itself to a file. Do not use `print()` or `echo`, which add a trailing newline. Do not add your own terminator "to be safe": the digest covers every byte.
2. Publish the create or update in one call. Immediately read the comment back and compare it with the prepared body before you run the protocol verifier: compare the lengths, then the tail bytes. A one-byte difference is almost always a trailing newline added between preparation and write.
3. If the identity check reports a conflict but the visible text matches, do not panic-retry the create. The mismatch state is already published; a second create makes a second canonical comment with a different identity.
4. Repair instead: update the owned comment with the exact bytes (PATCH), refresh the snapshot, and run the verifier again. Only exact conflict where you cannot write the comment requires a prepared-operation rebind.
5. Feed the verifier a complete snapshot. For exchange helpers that normalize issue state, exhaust comment pagination, mark the snapshot complete, and give every comment author every field the schema requires (stable id, login, and an authority flag). A missing author field fails schema validation before any body comparison runs.
6. Keep the prepared operation across the retry. Publication verification binds the prepared bytes, not a fresh preparation, so re-preparing against the same unchanged snapshot must produce the same operation; use that equality check as the gate before any write.

If the forge write capability is missing, report the gap and keep the prepared operation as the retry artifact. Do not approximate the body by retyping it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Write the helper-prepared comment body to a file through a script `print()`, then post that file with a forge CLI. | The file gained one trailing newline (6580 bytes live vs 6579 prepared), so exact-readback verification reported an identity conflict although the visible text was identical. | Compare the live body and the prepared body by length and tail bytes before any retry. One extra byte is usually a newline from re-serialization, not a forge-side change. |
| Attempt 2 | Consider re-running the create operation to replace the mismatched comment content. | A second create would add a second canonical comment with a different identity ID and break the one-comment-per-role invariant that the protocol checks. | Update the owned comment in place with the exact bytes, then re-verify. Create exactly one comment per role. |

## Results & Parameters

### Configuration

```bash
# prepared body -> exact bytes on disk (no added terminator)
python3 -c "import json,sys; open('body.md','w').write(json.load(open(sys.argv[1]))['operation']['body'])" prepared.json

# create or repair, then compare readback bytes before verifying
gh api -X POST repos/{owner}/{repo}/issues/<number>/comments -F body=@body.md --jq .id
gh api repos/{owner}/{repo}/issues/comments/<id> --jq .body | diff - body.md && echo EXACT
```

### Expected Output

A successful run shows these properties:

- The readback body equals the prepared body byte for byte (`diff` is empty).
- The protocol verifier returns a verified status with a publication receipt.
- Exactly one comment carries the role marker for the artifact.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private automation monorepo (privacy-generalized) | Canonical issue plan and review comments published through the GitHub CLI under a protocol helper with exact-readback verification; one newline-induced identity conflict repaired by exact-byte PATCH | See [forge-exact-byte-comment-publication.notes.md](forge-exact-byte-comment-publication.notes.md). |

## References

- GitHub REST API: create and update an issue comment (`POST /repos/{owner}/{repo}/issues/{issue_number}/comments`, `PATCH /repos/{owner}/{repo}/issues/comments/{comment_id}`).
- Related mechanism, different intent: [automation-graphql-batch-comment-fetch](automation-graphql-batch-comment-fetch.md) — batched comment read for review inventory. This entry is about the exact-byte write path.
- Related mechanism, different intent: [github-issue-stale-plan-comment-cleanup](github-issue-stale-plan-comment-cleanup.md) — deleting stale plan comments after authorization checks. This entry is about creating and repairing byte-exact canonical comments.
