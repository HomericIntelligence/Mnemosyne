---
name: owner-only-live-repair-command-handoff
description: "Hand a live repair that only the owner may run to the owner as exact commands with a read-only check and a rollback line, and verify the result without changing anything. Use when an agent finds drift on live shared storage or needs a live action that the rules reserve for the owner (a mode change, a group change, a reload, a publish)."
category: tooling
date: 2026-11-25
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
tags: [owner-only, live-repair, handoff, shared-storage, permissions, read-only-verification, rollback, agents]
---

# Hand an Owner-Only Live Repair to the Owner

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-25 |
| **Objective** | Get a live repair done without an agent touching live state, and without a vague request. |
| **Outcome** | Operational. The owner ran the commands in one step each; the agent verified the result read-only and closed the issue. |

## When to Use

- An agent finds drift between a manifest and live files or directories (mode bits, group, setgid bit).
- A live action is reserved for the owner by the rules of the project: a reload, a publish, a restart, a mode or group change on shared storage.
- The code that creates the paths is already correct, so only live state differs and no code change can fix it.
- The owner asks "why do we need this?" or "give me the commands".

## Verified Workflow

### Quick Reference

Before you write the commands, read the live state and prove that the code is not the cause. Then give the owner four things:

1. The reason, in two lines: what the manifest says, what the live state is, and what risk was not established.
2. Exact commands, each scoped to named paths. Do not use a recursive option unless the drift is in a tree.
3. A read-only check that the owner can run before and after, with the expected result (for example a count of zero).
4. A rollback line, and a statement of what the rollback cannot undo (a changed group has no rollback without the old value).

```bash
# repair (owner runs)
chmod g-s <dir-a> <dir-b>
find <dir> -maxdepth 1 -name '*.yaml' -type f ! -perm 0444 -exec chmod 0444 {} +
# check (read-only; expect 0)
find <dir> -maxdepth 1 -name '*.yaml' -type f \( ! -perm 0444 -o ! -group <group> \) | wc -l
# rollback
chmod g+s <dir-a> <dir-b>
```

### Suggested Approach

1. Look at the live paths first, read-only. Use the real path names, not a placeholder. A placeholder in a command is a request for the owner to guess.
2. Read the direction of each rule from the source line before you describe it. A manifest that forbids a bit means the repair removes the bit.
3. Say plainly if the drift is minor and no outage is tied to it. Offer the owner the option to accept the drift.
4. Do not run the command yourself, even when the permission check would allow it. Ask the owner, and continue other work.
5. After the owner runs the commands, run the same read-only check yourself and report the result. Then close the item only on the owner's word.
6. If a command needs a group membership that the owner may lack, say so and give the one-line alternative.

If the owner declines, record the accepted drift on the tracking item and stop. Do not repeat the request.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Placeholder paths | Gave a command with a `<root>` placeholder in it | The owner had to find the real path | Resolve paths read-only first and print them |
| Wrong direction | Briefed an agent to add a bit that the manifest forbids | The summary line hid the direction | Quote the rule from its source line |
| Repair without a check | Gave only the repair commands | The owner could not tell that the repair worked | Give a read-only check with the expected result |
| Rollback without limits | Offered `chmod` back as the rollback for a group change | The old group was not recorded | State what the rollback cannot undo |

## Results & Parameters

| Item | Value |
| ------- | ------- |
| Commands per repair | One per path set; no recursion by default |
| Check | Read-only; states the expected result |
| Rollback | One line; names what it cannot undo |
| Close | Only after the owner confirms; the agent verifies read-only first |
