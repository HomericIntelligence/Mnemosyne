---
name: communication-deliverable-before-decision-questions
license: BSD-3-Clause
description: "Deliver the artifact a collaborator asked for before you list the open decisions around it, and read a short request that implies a summary as an order for that summary. Use when: (1) a request names an artifact such as a release note, a report, a list, or a statement, (2) the evidence holds unreleased or pending state, (3) investigation found open decisions or blockers that would change what the answer says, (4) a short request such as give me the notes must be read as a full deliverable, (5) a revision asks for less talk and more output."
category: documentation
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - communication
  - deliverable
  - release-notes
  - pending-state
  - open-decisions
  - request-interpretation
  - output-style
  - agent-behavior
---

# Deliver the Requested Artifact Before the Decision List

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Give the collaborator the artifact they requested, in its usable form, and keep open decisions out of the position of the deliverable. |
| **Outcome** | Operational. The rule is applied and observed in one session. It has not been validated by a merged delivery. |
| **Verification** | unverified. The lesson comes from collaborator feedback in one session. |

## When to Use

- A request names a deliverable: release notes, a report, a statement, a summary, a list, a table.
- The evidence holds pending state, for example an unreleased version, an open promotion, or a
  failing check.
- Investigation found open decisions, blockers, or unanswered questions that change the content.
- A short request such as "give me the notes" or "just the statement" arrives after a longer answer.
- A collaborator says the reply contains questions or commentary instead of the requested output.

## Verified Workflow

### Quick Reference

> Write the requested artifact first, in the form the collaborator can use. Put open decisions,
> blockers, and status caveats after it, or in one short section at the end. A question is not a
> deliverable.

### Suggested Approach

1. **Name the deliverable from the request.** "Release notes for X", "a statement of what is in
   X", and "a summary of X" ask for the content itself. They do not ask for a status report about
   the content.
2. **Write the artifact first.** Use the headings and order the artifact family uses. For release
   notes, use highlights, breaking changes, upgrade notes, and fixes. Do not open with the state of
   the release when the collaborator asked for the notes.
3. **Keep pending state as one short caveat.** Put the unreleased status, the open promotion, or
   the failing check in a short line or a short final section. Do not let it replace the content.
4. **Do not end with questions that the artifact can answer.** If a decision is open, state the
   open decision and the options in the artifact. Offer to apply one option, but do not stop and
   wait for an answer to a deliverable request. Ask only when the answer changes materially which
   artifact to write.
5. **Read a short request as a full deliverable.** When a collaborator says the previous answer was
   wrong because it asked questions, the next reply is the artifact, not a shorter status note.
   Silence on a detail is not permission to omit a large part of the content.
6. **Cap the caveats.** Keep the status caveat shorter than the content it describes. If the caveat
   is longer, the reply is a status report, not the requested artifact.

### Keep the evidence honest

State a release as unreleased when no tag or published release exists. Name the open change that
will create it. Do not present pending work as shipped. Put the observation in the caveat, not in
place of the deliverable.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Answer the status question instead of the artifact | Replied with the state of the cut, the blocking checks, and the open owner decisions. | The collaborator asked for release notes and received a status report with no notes. | Write the artifact first, then add a short status caveat. |
| End with the open decisions | Closed the reply with the decisions that still needed an answer. | The reply looked like a request for direction, not the requested content. | State an open decision inside the artifact as an option, and continue. |
| Treat the follow-up as a request for less text | Made the second reply shorter without the content. | The collaborator rejected the follow-up too: less exactness was not fewer words, it was the wrong content. | A correction asks for the right content, not for brevity. |
| Assume pending state makes the request premature | Waited for the merge before writing the notes. | The notes were useful and mostly complete while the change was pending. | Write the deliverable from current evidence and mark the pending part. |

## Results & Parameters

| Parameter | Value |
| --- | --- |
| Order of a reply | Artifact first, status caveat last |
| Status caveat limit | Shorter than the artifact content it describes |
| Default to a named artifact | Write the artifact; do not ask which form |
| Ask the collaborator | Only when the answer selects a materially different artifact |
| Pending state | State it as one short caveat; do not withhold the artifact |