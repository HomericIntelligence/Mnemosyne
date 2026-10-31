---
name: tooling-forge-content-revision-recovery
description: "Recover a forge-hosted text artifact after an external overwrite or a loss from the forge edit-revision history. Use when: (1) a pull-request body, issue body, or comment that coordination depends on is found empty or replaced, (2) an author-facing claim about artifact content disagrees with the live readback, (3) an earlier revision must be restored with provenance recorded."
category: tooling
date: 2026-10-30
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags: [forge, github, pull-request-body, issue-comment, revision-history, userContentEdits, recovery, overwrite-incident, readback, provenance]
---

# Forge Content Revision Recovery

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Restore a destroyed or replaced forge text artifact from revision history, with attribution, byte-level proof, and an incident record. |
| **Outcome** | Operational — a pull-request body of about 14.5 KB destroyed by an external overwrite was recovered from revision history, restored byte-verified, and the incident recorded. |

## When to Use

- A pull-request body, issue body, or comment that coordination depends on is found empty or replaced, and the responsible edit was external.
- An author-facing claim such as "the body is updated" disagrees with the live readback.
- An earlier revision of a forge artifact must be restored, and the agent is not the original author.
- A review or a plan binding names content that no longer exists at the bound location.

Do not use this skill to author new content. If revision history has no revision that restores the artifact, a rewrite is new authorship and must identify itself as such.

## Verified Workflow

### Quick Reference

```bash
# 1. Read the edit-revision history of the artifact.
gh api graphql -f query='query { repository(owner:"<org>",name:"<repo>") {
  pullRequest(number:<PR>) { userContentEdits(first:20) {
    nodes { editedAt editor { login } diff } } } } }'

# 2. Save the pre-destruction revision to a file; record bytes and checksum.
sha256sum recovery-source.md

# 3. Restore from the file, never through standard input:
#    issue comments - PATCH through the REST API with the body from a file;
#    pull-request bodies - the CLI edit command with a body-file flag.

# 4. Read back and compare byte content, markers, and references.
```

### Suggested Approach

> Proposed workflow; executed end-to-end once with a verified result. The forge objects
> that expose `userContentEdits` include issues, issue comments, and pull requests.

1. **Establish the loss.** Record the live body length and the current text head. Compare with the claims that actors made. Fetch the revision history (`userContentEdits` nodes carry `editedAt`, `editor`, and `diff`). The edit with an empty or content-replacing `diff` gives the destruction timestamp and the editing actor.
2. **Select the recovery source.** Use the last revision before the destructive edit. Save the full content of that revision to a file. Record the byte size and a checksum of the file: this is the recovery source.
3. **Restore from a file.** Write the artifact through a file body: `PATCH` a comment through the REST API with the body read from the file, or use the CLI pull-request edit command with a body-file flag. Do not pass a body through standard input: at least one CLI release accepts the standard-input flag form but writes an empty body.
4. **Verify the readback.** Fetch the live body again. Compare the byte content with the recovery source, apart from trailing-newline differences that the API applies. Check each protocol marker and reference string that the artifact must carry. Record the comparison result.
5. **Record the incident.** Add a note, in the artifact itself or in the coordination record, that states: the destructive edit timestamp, that the artifact was restored from revision history, and the revision that was used as the source. Treat restored text as recovered provenance, not fresh authorship. Do not change labels, review state, or other forge state during a recovery unless the owning protocol assigns that change.
6. **Escalate true loss.** If the revision history cannot restore the artifact, stop and report. A reconstruction is new authorship.

### Boundaries

- The `userContentEdits` connection is paged; request more pages for artifacts with many edits.
- REST discussion endpoints answer 404 for repositories that host discussions only under the GraphQL API.
- A restored body cannot recover comments that were deleted rather than edited.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Write through standard input | Sent a comment body through a CLI standard-input body flag | The flag was accepted but the written body was empty | Write forge bodies from files |
| Trust the actor claim | Accepted an author-facing "content updated" claim against a zero-length readback | The live artifact was empty; the claim described intent, not outcome | Compare claims with the live readback and the revision history |
| Treat an empty artifact as current intent | Read the empty body as the author's latest revision | The revision history showed a destructive external edit minutes after the last full-body edit; the emptiness was loss, not intent | Check the revision history before treating an empty artifact as current intent |

## Results & Parameters

### Configuration

```yaml
recovery:
  revision_source: "last edit before the destructive edit"
  restore_channel: "file body, never standard input"
  verify:
    - "byte comparison, modulo API trailing-newline"
    - "required marker and reference strings, count matches"
  incident_record:
    - "destructive edit timestamp"
    - "restoration source revision timestamp"
```

### Expected Output

- The live body matches the recovery source byte-for-byte, apart from trailing-newline differences.
- The marker and reference string counts match the pre-destruction artifact.
- An incident note exists that states the destruction and restoration timestamps.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Cross-org coordination lane | Recovery of a pull-request body destroyed by an external overwrite | [notes](./tooling-forge-content-revision-recovery.notes.md) |

## References

- [GitHub GraphQL API reference](https://docs.github.com/en/graphql/reference/objects)
- [Exact-byte comment publication](forge-exact-byte-comment-publication.md)
- [Plan-artifact delivery failure](tooling-plan-artifact-delivery-nogo.md)
