---
name: agent-chat-approval-question-vs-tool-permission
description: "Diagnose repeated approval requests from a coding agent before you change its permission config. Use when a user says agents keep asking for permission to run routine mutations such as commit, push, or open a pull request."
category: tooling
date: 2026-11-23
version: "1.0.0"
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

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-23 |
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
   State that the user request already gives the authority for commit, push of the agent's own
   branch, and PR work. State the narrow set of actions that still need a question: those that
   destroy work the agent did not create. Check that the project instructions do not already
   state this. A project rule that exists and is ignored means that a global rule can still help.
3. For a tool permission dialog, read the effective config. Check the global file, then the
   project file, then per-agent overrides. Check path rules too: a worktree outside the project
   directory can trigger an external-directory prompt even when the command pattern is allowed.
4. If the user wants an allowlist, set the default for the command tool to ask, then list the
   allowed patterns. Rules are usually evaluated in order and the last match wins, so put the
   catch-all first.
5. Tell the user what a pattern allowlist cannot do. It cannot exclude a flag from an allowed
   prefix. An allowed `git push origin *` also allows a force push. Closing that gap needs one
   deny rule, which is a blacklist entry.
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

```jsonc
{
  "permission": {
    "*": "allow",
    "bash": { "*": "ask", "git commit*": "allow", "git push --force-with-lease*": "allow" }
  }
}
```

### Expected Output

- Chat questions for routine work stop, or become rare. The effect depends on the model.
- Commands outside the allowlist ask once each. Add the common ones after the first prompts.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private | One local session | Config and instruction file changed. Live effect not measured. |

## References

- [Least-privilege tool scopes](automation-agent-tool-scopes-least-privilege.md)
