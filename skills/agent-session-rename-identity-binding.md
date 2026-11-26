---
name: agent-session-rename-identity-binding
license: BSD-3-Clause
description: "Bind the exact session identifier before any operation that targets a session, such as a rename ceremony or a prompt to a peer session; never select a session by its display name."
category: tooling
date: 2026-10-30
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [session-identity, session-rename, peer-session, cross-session-prompt, mutable-title, fleet, identity-binding]
---

# Agent Session Identity Binding

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Select the correct session for an operation when a host runs many sessions with generated, mutable, and sometimes identical display names. |
| **Outcome** | Successful — the target was bound to an exact identifier before the operation, for a rename ceremony and for a batch of peer prompts. |
| **Verification** | verified-local |

## When to Use

- A protocol requires an operation on the current session, for example a rename that replaces a leading status prefix in its title.
- You must send a prompt to one or more peer sessions, and the user identifies them by a display name or by a task.
- A peer listing shows two or more sessions with the same display name.
- The display names were generated from earlier tasks and can change when a session starts a new task.
- A listing was captured before a wait, and the sessions can rename themselves while you wait.

## Verified Workflow

A display name is not an identity. A host generates a name from the current task, and the name changes when the task changes. Two sessions can also carry the same name. Bind the exact session identifier before every operation that targets a session, and renew the binding immediately before a send or a write.

### Quick Reference

| Rule | Reason |
| ------ | -------- |
| Bind the current session from its environment | The environment is the only exact identity for the session that runs the operation |
| Bind a peer session from its local job-state record | A peer has no readable environment from your session |
| Read the display name as mutable metadata | The name changes when the session starts a new task |
| Rebuild the name-to-identifier map immediately before the send | A listing captured earlier can point at a stale or different session |
| Append the collision reference when a name repeats | A bare name then selects one of several sessions |
| Select the target set from task evidence | A generated name does not prove the task that a session runs |
| Read send success as admission only | Admission does not prove that the peer agent read the prompt |

### Bind the current session

1. Read the session identifier from the environment of the current session. In an OpenCode context the variable is `OPENCODE_SESSION_ID`.
2. Confirm the binding with the session list interface. Match on the identifier, not on the title. Read the exact current title for that identifier.
3. Build the new title from the read title. Change only the required prefix and keep every other character unchanged.
4. Apply the rename to the bound identifier. Report the old title, the new title, and the identifier.
5. If the environment variable is absent, stop and report. Do not guess a session from a partial title match.

### Bind a peer session

1. Enumerate the peers with the host's peer-listing interface. The listing gives each display name and, when the name is not unique, a disambiguating reference.
2. Bind each peer name to its exact identifier from the local job-state records. Each record holds the short identifier, the full session identifier, the display name, the name source, and the run state.
3. Select the target set from task evidence. Read each candidate's last user message, or the intent recorded for its job. A condition of the form "the session did not end with X" applies to the last user message only.
4. List the peers again immediately before the send. Rebuild the mapping. Send to the display name, and add the collision reference when the name repeats.
5. Record the display name, the bound identifier, and the inclusion reason for each target. Record each excluded session and the exclusion reason.
6. After the send, read the peer state again. A successful send shows that the message entered the peer inbox. If the interface reports that the peer holds or refuses the message, report that result. Do not claim that the peer agent read the prompt.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Rename by title substring | Assumed a unique title | A parallel session with a near-identical title receives or loses the rename | Bind the identifier from the environment first |
| Reconstruct the title from memory | Assumed the session summary holds the exact title | Remainder drift: the new title differs from the old in more than the prefix | Read the live title for the bound identifier before the write |
| Best-guess rename without an identifier | The environment variable was not read | Wrong-session write, found only after the fact | No identifier, no rename; stop and report |
| Used the peer listing from the start of the task | Chose recipients from a listing that was several minutes old | The listing showed one name twice and noted that other names had changed; it could not prove which session was which | Rebuild the mapping immediately before the send, and use the collision reference |
| Mapped the user's rule to session names | Read each display name as a description of its task | The names had been regenerated and did not name the task, so the name could not decide inclusion or exclusion | Derive the target set from the last user message or the recorded intent |
| Read the self-name from peer transcripts | Searched each transcript for the line that gives the session its name | Only a session that received a name records that line; other sessions show a generic line | Bind from the job-state record, which holds the identifier and the name for every session |

## Results & Parameters

| Parameter | Rule |
| --------- | ---- |
| Current-session identity | The session environment (`OPENCODE_SESSION_ID` in an OpenCode context) |
| Peer identity | The local job-state record, keyed by the short identifier |
| Target selection | The identifier, bound from a record; never the display name alone |
| Display name | Mutable metadata; regenerate the mapping immediately before use |
| Ambiguous name | Append the host's collision reference |
| Target set | Derived from the last user message or the recorded intent |
| Title construction | Change only the required prefix; keep every other character unchanged |
| Missing identifier | Stop and report; do not guess from a partial name |
| Send success | Admission to the inbox only; verify the peer state after the send |

### Evidence

A protocol required one rename on a host that ran several sessions with the same status prefix and similar wording. A title search could not isolate the target. The identifier from the environment, and the live title for that identifier, gave an exact binding. The rename touched the intended session only.

A later directive required a prompt to every peer session except those that ran one named skill. The peer listing showed two sessions with the same name and a note that other names had changed minutes earlier. The names were mapped to identifiers through the local job-state records, the target set was derived from each session's last user message, and the listing was rebuilt immediately before the send. The excluded sessions received no prompt.

## References

- [Agent Background Task Failure Recovery](agent-background-task-failure-recovery.md)
- [Mid-Drive Peer-Completion Audit](mid-drive-peer-completion-audit.md)
- [Parallel Agent Swarm Dispatch Patterns](parallel-agent-swarm-dispatch-patterns.md)