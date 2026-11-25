---
name: installer-permission-default-preserve-existing
description: "Set an agent harness auto-approval mode only after explicit user opt-in and only when the user has no existing approval or permission setting. Use when a setup script offers approve-for-me, auto mode, or automatic review and must preserve an existing policy."
category: tooling
date: 2026-11-25
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [installer, permissions, approval, auto-review, preserve-existing, idempotence, codex, claude]
---

# Installer Permission Default Must Preserve Existing Policy

Follow the [agent authority and host permissions policy](https://github.com/HomericIntelligence/Athena/blob/main/docs/policies/agent-authority.md)
for authority, host permissions, security invariants, and stop conditions.
Automatic approval is an explicit user choice. It is not an installer default.

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-25 |
| **Objective** | Enable a harness automatic-approval mode only after explicit user opt-in, without overriding an existing approval or permission policy. |
| **Outcome** | Successful. The installers wrote the opt-in approval setting only when the user opted in and the setting was absent. Existing settings and restore behavior were verified with stub harness settings. |
| **Verification** | verified-local |

## When to Use

Use this skill when all or some of these conditions apply:

- The user explicitly opted in to automatic approval, auto mode, or automatic review for a coding-agent harness.
- A setup or install script offers that mode and must not enable it by default.
- The harness settings may already contain an approval policy, a sandbox mode, or a permission mode.
- The installer must be idempotent and must not downgrade or replace a user's security policy.
- The installer needs a rollback path that restores the pre-install settings.

## Verified Workflow

### Quick Reference

Write a harness automatic-approval setting only when the user explicitly opts
in and the related setting is absent. Host documentation owns the exact key
names, values, and supported modes.

```text
Approval group:
  if the user did not explicitly opt in:
      write nothing
  elif any key in the approval group exists:
      keep the whole group
  else:
      write the host-documented approval setting
```

Treat all keys that affect one approval decision as one group. If any key
exists, keep the whole approval configuration. Keep every related setting that
already exists.

### Suggested Approach

1. Get explicit user opt-in for automatic approval. A setup script must not
   enable it by default.
2. Read the host documentation. Identify the approval setting and every key
   that affects the same decision. Do not assume that one key name or value is
   portable across harness versions.
3. Read the user settings before the first write.
4. Apply the group rule:
   - If the user did not opt in, write no approval key.
   - If any key in the approval group exists, do not change any of them.
5. Write the host-documented setting only when the user opted in and the group
   is absent.
6. Record the result in the install manifest and output. Use `written` or
   `existing:<value>`.
7. Use the installer snapshot and restore path for rollback. Do not delete
   individual keys to undo.
8. Validate with the harness parser when it is available. The parser rejects
   an invalid enum value.
9. Test three cases: explicit opt-in with fresh settings, existing approval
   settings, and restore.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Always write the approval keys | Enabled approve-for-me on every install | It overwrote an existing sandbox mode or permission mode and silently changed the user's security policy | Write the approval setting only when the user explicitly opts in and the related setting is absent |
| Enable automatic approval without an opt-in | Treated a setup script as authority to change the approval policy | The installer changed a security decision that the user did not request | Automatic approval is an explicit user choice. The installer must not enable it by default. |
| Fill only the missing keys in the approval group | Added one approval key when another key in the same decision already existed | It created a mixed policy: the existing sandbox stayed, but a new reviewer changed the approval behavior | Treat all keys that belong to one approval decision as a group and keep all of them when any exists |
| Use `bypassPermissions` for Claude Code | Treated auto mode as a full bypass | It skips all permission checks, which is broader than automatic review | Use the host-documented automatic-review mode only after explicit opt-in. Do not use a full bypass. |
| Check only the primary key | Looked only for the primary approval key or only for the permissions object | It missed related keys that change the decision | Inspect every key that belongs to the same approval decision |

## Results & Parameters

### Configuration

The exact key names, values, and supported modes belong to the host
documentation. This skill does not define them.

```text
Approval decision:
  if the user did not explicitly opt in:
      write nothing
  elif any key in the approval group exists:
      keep the existing approval configuration and every related key
  else:
      write the host-documented approval setting
```

### Expected Output

- An install with explicit user opt-in writes only the host-documented
  approval setting.
- An install without explicit opt-in writes no approval setting.
- An existing approval or permission policy stays unchanged.
- The manifest records `written` or `existing:<value>`.
- The restore action returns the pre-install settings.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private | Installer smoke tests with stub gateway and harness settings | Explicit opt-in, existing, and restore cases passed. The harness parser accepted the documented values and rejected an invalid enum value. See [notes](installer-permission-default-preserve-existing.notes.md). |

## References

- [Agent authority and host permissions policy](https://github.com/HomericIntelligence/Athena/blob/main/docs/policies/agent-authority.md)
- [Classify approval requests before changing permissions](agent-chat-approval-question-vs-tool-permission.md)
- [Run an interactive upstream installer non-interactively](bash-noninteractive-installer-wrapper.md)
- [Plan removal of blanket permission bypasses](architecture-claude-permission-bypass-removal-planning.md)
