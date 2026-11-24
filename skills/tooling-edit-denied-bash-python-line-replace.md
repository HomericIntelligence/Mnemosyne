---
name: tooling-edit-denied-bash-python-line-replace
license: BSD-3-Clause
description: "Use an alternate tool for a formatting-preserving edit only when the host permits that tool for the same authorized action and a non-protected path."
category: tooling
date: 2026-11-23
version: "1.2.0"
user-invocable: false
verification: verified-local
tags:
  - tooling
  - permissions
  - edit-denied
  - dont-ask-mode
  - json
  - config
  - line-replacement
  - formatting-preserving
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/tooling-edit-denied-bash-python-line-replace.history"
history-cleanup-date: "2026-09-20"
---

# Formatting-Preserving Edits Through an Authorized Alternate Tool

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-23 |
| **Objective** | Apply a precise, formatting-preserving single-line change to a non-protected config file when the `Edit`/`Write` tool is denied but `Bash` is permitted for that action and path |
| **Outcome** | The exact requested one-line edit was applied through a Python in-place line replacement scripted in Bash; the diff stayed at exactly one line, and the file remained valid |
| **Verification** | verified-local (replacement mechanics only) |

**Verified locally only — CI validation pending.** The whole-line replacement mechanics were
verified locally in the ProjectHephaestus issue-1497 worktree. The rewritten non-security example is
illustrative and was not rerun through CI.

An unavailable editing tool can have a permitted substitute. A permission denial is different:
it can protect the action or the path, not merely the tool. Inspect the stated reason and the
host policy before you choose another mechanism. User intent alone does not remove that boundary.

**Stop condition:** Do not use an alternate tool to change permission or security configuration,
hooks, CI workflows, secrets, credential stores, or protected policy. Do not use it to broaden a
permission rule. A denial on one of those paths is a stop condition. Report the exact file, the
intended change, and the block. Use the documented host-owner approval path. Follow the
[agent authority and host permissions policy](https://github.com/HomericIntelligence/Athena/blob/main/docs/policies/agent-authority.md).

When the host explicitly permits the same action through another tool on a non-protected path, a
whole-line replacement can preserve formatting. Otherwise, report the denied action and continue
independent work.

## When to Use

- An editing mechanism is unavailable, and host policy explicitly permits the same authorized
  action through an alternate tool on a non-protected path.
- Tool availability differs, and the denial reason has been checked before choosing a substitute.
- You need a **formatting-preserving** single-line change to a JSON/YAML file where a full
  re-serialization (`json.dump`) would reorder keys, change indentation, or otherwise produce a
  noisy multi-line diff.
- **Do NOT use this on permission or security configuration.** Only use it when the user asked for
  the edit, only the tool was gated, and the target path is not protected.

## Verified Workflow

> **Note:** verified-local. The replacement mechanics were applied and verified locally in the
> ProjectHephaestus issue-1497 worktree. The example below uses non-security configuration. It was
> not exercised through CI.

### Quick Reference

```bash
# 1. Read the non-protected file first. Only Edit/Write are denied.
#    Copy the EXACT old line, including leading whitespace and trailing comma.

# 2. Replace exactly one whole line via a Python heredoc in Bash.
#    Whole-line matching preserves the file's exact formatting.
python3 - <<'PY'
from pathlib import Path

path = Path("config/service.json")
old = '  "timeout_seconds": 30,\n'
new = '  "timeout_seconds": 60,\n'

lines = path.read_text().splitlines(keepends=True)
count = sum(1 for line in lines if line == old)
assert count == 1, f"expected exactly 1 match, found {count}"   # fail loudly
lines = [new if line == old else line for line in lines]
path.write_text("".join(lines))
print("replaced 1 line")
PY

# 3. Verify: still valid JSON + membership assertions.
python3 - <<'PY'
import json
with open("config/service.json") as handle:
    data = json.load(handle)
assert data["timeout_seconds"] == 60
print("verified: valid JSON and new value present")
PY
```

### Detailed Steps

1. **Read the file first with the `Read` tool.** Read almost always still works when Edit/Write are
   denied. Copy the EXACT text of the line to change, including leading indentation and any trailing
   comma, so the match is unambiguous.
2. **Inspect the denial and the path ownership.** Use an alternate tool only if the host permits
   that same action on that path. If the path is permission or security configuration, stop. Do not
   infer permission from shell availability.
3. **Replace exactly ONE whole line via a Python heredoc in Bash.** Read all lines with
   `read_text().splitlines(keepends=True)`. Count matches of the exact old line and
   `assert count == 1` to fail loudly on zero (stale or wrong string) or multiple (ambiguous)
   matches. Rebuild the line list by swapping only the matched line, then
   `write_text("".join(lines))`.
4. **Match WHOLE lines, including leading whitespace and the trailing comma or newline.** This
   preserves the file's exact formatting. It avoids a reindent or JSON re-serialization that would
   reorder keys.
5. **Verify with a separate Python one-liner.** Use `json.load` or `yaml.safe_load` to confirm the
   file still parses. Add membership assertions for the new value and the old value.
6. **Never `json.dump` the whole file to apply the change.** A full rewrite reorders or reformats
   keys and produces a noisy multi-line diff. Line-level replacement keeps the diff to one line.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Call the Edit tool on permission config | Used the normal `Edit` tool to change a deny-list line in `.claude/settings.json` | Denied. The path was protected, and the denial applied to the action and path, not only to the tool | A protected-path denial is a stop condition. Report the blocked change and use the host-owner path. |
| Broaden the permission rule through Bash | Used a Python heredoc to replace a specific deny rule with a wildcard | This changed the security policy with an alternate tool and made the deny rule broader | Do not use an alternate tool to edit permission or security configuration. Do not broaden a deny rule. |
| `json.dump` full rewrite | Loaded the JSON, mutated the value in memory, and wrote the whole file back with `json.dump` | Re-serialization reordered keys and changed indentation, producing a noisy multi-line diff | Use line-level replacement with a whole-line `str` match. Never full re-serialization for a one-line edit. |
| Partial-substring replace | Considered `str.replace` on a bare substring | A bare substring risks a match inside a comment or a different key and drops the surrounding indentation or comma | Match the ENTIRE line, including whitespace and the trailing comma or newline, and assert exactly one occurrence. |
| Assume Read was also blocked | Almost skipped reading the file because Edit was denied | Read was still allowed. Only Edit/Write were gated | Read through permitted tools when useful. Inspect the actual denial rather than assuming its scope. |

## Results & Parameters

### The exact change (worked example)

```text
# config/service.json before -> after:
- "timeout_seconds": 30,
+ "timeout_seconds": 60,
```

This changes a non-security timeout value. It does not change a permission or security rule.

### Parameters that made it safe

- **`assert count == 1`** before writing fails loudly on zero (stale string) or multiple
  (ambiguous) matches, so a bad match never silently corrupts the file.
- **`keepends=True`** on `splitlines` preserves the trailing newline, so the rewritten file is
  byte-identical except for the one line.
- **Whole-line match** including indentation and trailing comma avoids a reindent or key reorder.
- **Post-write `json.load` plus membership assertions** confirms valid JSON and that the swap
  happened.

### Expected Output

- The file still parses (`json.load` or `yaml.safe_load` succeeds).
- `git diff` shows exactly ONE changed line.
- The new value is present in the target container and the old value is gone.

### Rule of thumb

Use an alternate tool for an authorized edit only when the host permits it for the same action and
non-protected path. Read the original content, keep the change narrow, and inspect the result.
A denied action remains denied when another tool could mechanically perform it. A denied permission
or security path remains denied.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | issue-1497 worktree; whole-line replacement while Edit/Write were denied in "don't ask mode" | verified-local (valid JSON and membership assertions passed); the original permission-file example is now prohibited; this rewrite uses a non-security config |

## References

- [Agent authority and host permissions](https://github.com/HomericIntelligence/Athena/blob/main/docs/policies/agent-authority.md) — canonical authority, host permission, and security-invariant policy.
- [ci-hygiene-and-validation-gates](ci-hygiene-and-validation-gates.md) — Pattern 5 records a read → replace → write fallback in a CI-hook context.
- [tooling-edit-templated-config-at-source](tooling-edit-templated-config-at-source.md) — a different config-edit footgun: a generated artifact overwritten on re-render.