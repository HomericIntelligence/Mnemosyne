---
name: agent-chat-approval-question-vs-tool-permission
description: "Diagnose repeated approval requests from a coding agent before you change its permission config. Use when a user says agents keep asking for permission to run routine mutations such as commit, push, or open a pull request."
category: tooling
date: 2026-11-24
version: "1.1.0"
user-invocable: false
verification: unverified
tags:
  - agent
  - permissions
  - approval
  - instructions
  - allowlist
---

# Chat Approval Questions Versus Tool Permission Prompts

Follow the [agent authority and host permissions policy](https://github.com/HomericIntelligence/Athena/blob/main/docs/policies/agent-authority.md)
for authority, host permissions, security invariants, and stop conditions. This skill classifies
approval requests; it does not grant authority.

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | Stop routine approval requests with the correct mechanism. |
| **Outcome** | Operational. The fix was applied. Its effect in a live session was not measured. |

## When to Use

- A user reports that agents ask for approval before routine mutations such as commit, push, or PR creation.
- The user pastes the request text, and you must find its source.
- A permission config already allows the tool, and requests continue.

## Verified Workflow

### Quick Reference

Classify the request first. Two different sources produce an approval request:

| Source | How it looks | Where the fix is |
| --- | --- | --- |
| Tool permission layer | A harness dialog for a tool call, a path, or a command pattern | The agent permission config |
| Model chat question | Agent prose such as "May I commit and push?" with a numbered option list | Instruction files that the agent reads |

### Suggested Approach

1. Read the pasted text. A question with a numbered option list from the agent is a chat
   question. No permission setting can stop it. Do not edit the permission config for it.
2. For a chat question, write a global instruction file that the agent loads in every session.
   State that the user request and the canonical authority policy already cover commit, push of
   the agent's own branch, and PR work. State the narrow set of actions that still need a
   question: those that destroy work the agent did not create. Check that the project
   instructions do not already state this. A project rule that exists and is ignored means that a
   global rule can still help.
3. For a tool permission dialog, read the effective config. Check the global file, then the
   project file, then per-agent overrides. Check path rules too: a worktree outside the project
   directory can trigger an external-directory prompt even when the command pattern is allowed.
4. If the user wants an allowlist, set the host default for the command tool to ask, then list
   only the specific commands the task needs. Read the host's own matching order and precedence.
   Do not assume that one order applies to every host.
5. Tell the user what a pattern allowlist cannot do. If the host matches command prefixes, an
   allowed `git push origin *` also allows a force push because the pattern cannot exclude a
   flag from an allowed prefix. Closing that gap needs a narrow deny rule. Apply that rule only
   after you confirm the host's policy and matching syntax.
6. Back up the config before the edit. Validate it with the tool's own parser. A strict JSON
   parser can reject comments and trailing commas that the tool accepts.

If the harness log does not record permission events, do not claim a cause. State the
classification evidence you have and the limit.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Blacklist | Allow all, ask on a list of destructive commands | The pasted request was a chat question, so the config could not affect it | Classify the request source before you edit config |
| Log search | Search the harness log for permission asks | The log recorded only HTTP polling of the permission endpoint | Do not rely on logs to name the prompt; ask for the exact text |

## Results & Parameters

### Configuration

Use the host's own configuration schema and parser. The safe shape is:

- default ask for command execution;
- allow only the command patterns the task needs;
- add a narrow deny for dangerous flags that a broad allow would include.

Do not copy this shape as a portable file. Host configuration owns the exact keys and matching
rules. Follow the canonical authority policy for the action, not the pattern.

### Expected Output

- Chat questions for routine work stop, or become rare. The effect depends on the model.
- Commands outside the allowlist request approval according to host policy.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private | One local session | Config and instruction file changed. Live effect not measured. |

## References

- [Agent authority and host permissions](https://github.com/HomericIntelligence/Athena/blob/main/docs/policies/agent-authority.md)
- [Least-privilege tool scopes](automation-agent-tool-scopes-least-privilege.md)
