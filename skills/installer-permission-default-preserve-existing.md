---
name: installer-permission-default-preserve-existing
description: "Set an agent harness auto-approval default only when the user has no existing approval or permission setting. Use when a setup script enables approve-for-me, auto mode, or automatic review and must preserve an existing policy."
category: tooling
date: 2026-11-24
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [installer, permissions, approval, auto-review, preserve-existing, idempotence, codex, claude]
---

# Installer Permission Default Must Preserve Existing Policy

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | Enable a harness automatic-approval mode from an installer without overriding an existing approval or permission policy. |
| **Outcome** | Successful. The installers wrote the default only when the setting was absent. Existing settings and restore behavior were verified with stub harness settings. |
| **Verification** | verified-local |

## When to Use

Use this skill when all or some of these conditions apply:

- A setup or install script will enable automatic approval, auto mode, or automatic review for a coding-agent harness.
- The harness settings may already contain an approval policy, a sandbox mode, or a permission mode.
- The installer must be idempotent and must not downgrade or replace a user's security policy.
- The installer needs a rollback path that restores the pre-install settings.

## Verified Workflow

### Quick Reference

Write the harness default only when the related setting is absent.

```text
Codex approve-for-me: write all three only when none exists:
  approval_policy = "on-request"
  sandbox_mode = "workspace-write"
  approvals_reviewer = "auto_review"

Claude Code auto mode: write only when permissions.defaultMode is absent:
  "permissions": {"defaultMode": "auto"}
```

For Codex, treat the three keys as one approval decision. If any key exists, keep the whole approval configuration. For Claude Code, keep an existing `permissions.defaultMode` and every other `permissions` key.

### Suggested Approach

1. Identify the harness automatic-approval setting and every key that affects the same decision.
   - Codex: `approval_policy`, `sandbox_mode`, and `approvals_reviewer`. The sandbox mode is part of the approval decision.
   - Claude Code: `permissions.defaultMode`. The other keys under `permissions` stay unchanged.
2. Read the user settings before the first write.
3. Apply the group rule:
   - Codex: if any of the three keys exists at the top level, do not write any approval key.
   - Claude Code: if `permissions.defaultMode` exists, do not change it.
4. Write the default only when the group is absent.
5. Record the result in the install manifest and output. Use `written` or `existing:<value>`.
6. Use the installer snapshot and restore path for rollback. Do not delete individual keys to undo.
7. Validate with the harness parser when it is available. For Codex, `codex doctor --json` rejects an invalid enum value.
8. Test three cases: fresh settings, existing approval settings, and restore.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Always write the approval keys | Enabled approve-for-me on every install | It overwrote an existing sandbox mode or permission mode and silently changed the user's security policy | Write the default only when the related setting is absent |
| Fill only the missing keys in the Codex trio | Added `approvals_reviewer` when `sandbox_mode` already existed | It created a mixed policy: the existing sandbox stayed, but a new reviewer changed the approval behavior | Treat the Codex keys as one group and keep all of them when any exists |
| Use `bypassPermissions` for Claude Code | Treated auto mode as a full bypass | It skips all permission checks, which is broader than automatic review | Use `permissions.defaultMode = "auto"` for automatic review |
| Check only the primary key | Looked only for `approval_policy` or only for `permissions` | It missed `sandbox_mode` and other related keys that change the decision | Inspect every key that belongs to the same approval decision |

## Results & Parameters

### Configuration

```toml
# Codex: write all three only when none exists.
approval_policy = "on-request"
sandbox_mode = "workspace-write"
approvals_reviewer = "auto_review"
```

```json
{
  "permissions": {
    "defaultMode": "auto"
  }
}
```

```text
Codex detection:
  if any top-level key in (approval_policy, sandbox_mode, approvals_reviewer):
      keep the whole approval configuration
  else:
      write all three keys

Claude Code detection:
  if "defaultMode" in permissions:
      keep the existing mode and every other permission key
  else:
      set permissions.defaultMode = "auto"
```

### Expected Output

- A fresh install writes the harness automatic-approval default.
- An existing approval or permission policy stays unchanged.
- The manifest records `approval_mode=auto_review|existing` or `permission_mode=auto|existing:<mode>`.
- The restore action returns the pre-install settings.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private | Installer smoke tests with stub gateway and harness settings | Fresh, existing, and restore cases passed. The Codex parser accepted the keys and rejected an invalid enum value. See [notes](installer-permission-default-preserve-existing.notes.md). |

## References

- [Classify approval requests before changing permissions](agent-chat-approval-question-vs-tool-permission.md)
- [Run an interactive upstream installer non-interactively](bash-noninteractive-installer-wrapper.md)
- [Plan removal of blanket permission bypasses](architecture-claude-permission-bypass-removal-planning.md)
