---
name: git-submodule-cd-persists-wrong-repo
license: BSD-3-Clause
description: "Diagnose Git or verification commands acting on the wrong checkout when the shell working directory persists or silently changes between tool calls; bind the repository explicitly."
category: tooling
date: 2026-07-18
version: "1.1.0"
user-invocable: false
verification: verified-local
tags:
  - git
  - submodule
  - superproject
  - cwd
  - working-directory-persists
  - working-directory-reverts
  - bash-tool
  - git-c
  - git-worktree
  - false-green-evidence
  - odysseus
  - meta-repo
  - subshell
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/git-submodule-cd-persists-wrong-repo.history"
history-cleanup-date: "2026-09-20"
---

# A `cd` Into a Submodule Persists Across Bash Calls and Redirects Git to the Wrong Repo

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-18 |
| **Objective** | Bump all submodule pins in the Odysseus meta-repo and commit them in the PARENT superproject. Also: run verification against the intended tree when two sibling worktrees of one repository are in play. |
| **Outcome** | Recovered — the bumps were never lost; a persisted `cd` into a submodule had redirected `git add`/`status`/`log` to the submodule. Re-scoping with `git -C <superproject>` staged all 14 pins correctly. Later, the reverse drift (ambient cwd reverting to a sibling worktree between calls) produced false-green verification; an in-command identity record exposed the binding. |
| **Verification** | verified-local — the `git -C <superproject> add -A` recovery was executed and observed to stage all 14 submodule pins in-session; this skill PR's own CI gate not yet observed green. |
| **History** | (none yet) |

## When to Use

- `git add -A` stages nothing in a meta-repo/superproject and `git status --short` comes back empty even though you know you changed submodule pins.
- `git log --oneline -1` shows a commit that belongs to a SUBMODULE (e.g. an Agamemnon commit) when you expected the superproject's HEAD.
- Submodule pin bumps appear to have "vanished" right after you inspected a submodule with `cd sub && git rev-parse HEAD`.
- You ran something like `cd control/Agamemnon && git fetch && git rev-parse HEAD` in one Bash call, and later git commands — issued WITHOUT re-cd'ing — silently operated on the submodule.
- `git rev-parse --show-toplevel` resolves to a submodule path instead of the meta-repo root.
- `git log --oneline -1`, grep hit counts, or test summaries match the tree you did NOT edit — the sibling worktree's HEAD or the pre-edit file — while relative paths made every command look normal.
- Two or more worktrees of one repository exist (`git worktree list`), and commands that used relative paths were separated by at least one tool call.
- A background-task notification or other harness event arrived between two shell calls that you expected to share a working directory.
- A test or lint PASS that you want to record as verification evidence came from a command whose working directory you did not pin.

## Root Cause

The Bash tool's working directory **persists between separate tool invocations**. A `cd` into a
submodule made in an earlier call is never undone, so every later git command runs inside the
submodule's `.git`, not the superproject's. Git commands are cwd-relative: `git add`,
`git status`, `git commit`, and `git log` all act on whatever repository owns the current
directory. Inside a submodule that is the submodule repo — a completely different `.git` — so:

- `git add -A` stages nothing in the parent (there is nothing to stage in the submodule).
- `git status --short` is empty (the submodule tree is clean).
- `git log --oneline -1` shows the submodule's HEAD, which looks like "my commits are gone".

Nothing errors. The symptoms read like "the submodule bumps disappeared" when in fact the
commands were pointed at the wrong repo the whole time.

The reverse drift also happens: between two calls, the ambient directory can silently
CHANGE BACK to an earlier location — for example around a background-task completion
notification or other harness working-directory management. Commands then run in the tree
an EARLIER `cd` selected, not the one a later `cd` selected. Nothing errors in this
direction either: sibling worktrees of one repository carry identical relative paths, so a
test or lint run against the sibling can PASS and print a plausible summary. The result is
false-green evidence — a PASS recorded for a tree that does not contain the change.

So "the cwd persists between calls" is only half of the rule. The safe statement is: **the
ambient directory between calls is not under your control** — it can persist, or it can
change without an explicit `cd`. Do not trust it in either direction.

## Verified Workflow

### Quick Reference

```bash
# PREFERRED: never rely on the shell's cwd — target the superproject explicitly.
SUPER=/abs/path/to/Odysseus            # the meta-repo / superproject root
git -C "$SUPER" add -A
git -C "$SUPER" status --short
git -C "$SUPER" commit -S -m "chore(submodules): bump pins"
git -C "$SUPER" log --oneline -1

# Inspect a submodule WITHOUT leaking the cwd — scope the cd in a subshell:
( cd "$SUPER/control/Agamemnon" && git fetch && git rev-parse HEAD )
# cwd is unchanged outside the parentheses.

# RECOVERY when you notice commands hitting the wrong repo:
cd "$SUPER"                            # or just switch to git -C
pwd                                    # confirm you are at the meta-repo root
git rev-parse --show-toplevel          # MUST print $SUPER, not a submodule path
git add -A && git status --short       # re-run staging; the pins reappear

# EVIDENCE-YIELDING commands (tests, lint, diffs you will record): pin the
# directory per command — the tool's explicit workdir setting, or an absolute
# cd in the SAME command text — and print the source identity in that command:
cd /abs/worktree && uv run pytest tests/test_x.py -q
pwd; git rev-parse --show-toplevel; git rev-parse HEAD
# If the printed identity names a tree that lacks the change under test,
# the output is not evidence: discard it and re-run with the pin fixed.
```

### Detailed Steps

1. **Diagnose before concluding "changes are lost."** If `git add -A` stages nothing or
   `git log` shows an unexpected commit, do NOT assume the bumps vanished. Run
   `git rev-parse --show-toplevel` — if it prints a submodule path, the cwd is wrong, not the data.
2. **Bind before you believe a PASS.** Verification output that plausibly matches the wrong
   tree is a signature of its own: `git log -1` shows the other branch's head, grep hits
   line up with the unedited file, or a test count equals the pre-edit run although the
   change alters tests. Print the identity triple (`pwd`, `rev-parse --show-toplevel`,
   `rev-parse HEAD`) in the same command; when any field names a tree that lacks the
   change, discard the output. Absolute-path file EDITS do not rescue relative-path
   verification — the edit lands in the right tree while pytest still runs in the wrong one.
3. **Recover by re-scoping.** `cd` back to the superproject root (verify with `pwd` +
   `git rev-parse --show-toplevel`), or switch every command to `git -C /abs/superproject`.
   Re-run `git add -A`; the submodule pin changes stage correctly.
4. **Prevent it going forward — three equally good options:**
   - Use `git -C /abs/path/to/superproject <cmd>` for every git command that must act on the
     parent. This is immune to a stray persisted `cd`.
   - If you must `cd` into a submodule to inspect it, scope the change in a subshell
     `( cd sub && git ... )`, or explicitly `cd` back to the superproject root afterward.
   - For verification commands whose output becomes recorded evidence, pin the directory
     (the tool's workdir setting, or an absolute `cd` in the same command text) and append
     `; pwd; git rev-parse --show-toplevel; git rev-parse HEAD` so the log carries its own
     source identity. This survives cwd drifting in either direction.
5. **Verify the commit landed in the parent.** After committing, `git -C "$SUPER" show --stat HEAD`
   should list the submodule paths (e.g. `control/Agamemnon`) as changed entries.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| `git add -A` after an un-scoped `cd` into a submodule | Ran `cd control/Agamemnon && git fetch && git rev-parse HEAD` in one Bash call, then later (without re-cd'ing) `git add -A` in a separate call | The Bash cwd persisted, so `git add -A` ran INSIDE control/Agamemnon (a clean submodule tree) — it staged nothing in the parent | Always scope a submodule `cd` with a subshell `( cd sub && git ... )`, or use `git -C /abs/superproject` so the parent is targeted regardless of cwd |
| Trusted `git log` / `git status` output showing a submodule's commit | Read `git log --oneline -1` (which showed an Agamemnon commit) and an empty `git status --short` as evidence the pin bumps were lost | The commands were operating on the submodule repo because of the persisted cwd — the parent's changes were intact all along | Before diagnosing "changes lost," run `git rev-parse --show-toplevel`; if it points at a submodule, the cwd is wrong, not the data |
| Trusted cwd persistence between calls | Ran an absolute `cd` to worktree B in one Bash call, then several relative-path pytest/ruff invocations without re-pinning | The ambient cwd reverted to worktree A around a background-task notification, so every verification ran against the sibling tree that lacked the change | Ambient cwd between calls is harness state that can persist OR change; pin the directory in every evidence-yielding command (workdir setting or absolute `cd` in the same command text) |
| Recorded a PASS summary as evidence with no identity | Treated "60 passed" from a relative-path pytest call as proof for the edited tree | Both worktrees carried identical relative paths, so the sibling run printed the same plausible count; only an in-command `git log -1` exposed the mismatch | Print `pwd`, `git rev-parse --show-toplevel`, and `git rev-parse HEAD` in the same command as the check; evidence without source identity is not evidence |

## Results & Parameters

Recovery that worked in-session (staged all 14 Odysseus submodule pins correctly):

```bash
SUPER=/abs/path/to/Odysseus
git -C "$SUPER" rev-parse --show-toplevel   # -> $SUPER (confirms correct repo)
git -C "$SUPER" add -A
git -C "$SUPER" status --short               # -> 14 submodule paths staged
```

Key facts:

- The Bash tool's cwd between separate calls is harness-managed state: it is often NOT
  reset per invocation (a `cd` persists), but it can also revert to an earlier directory
  without an explicit `cd` — for example around background-task notifications. Both
  directions redirect later commands silently.
- Git is cwd-relative: inside a submodule, `add`/`status`/`commit`/`log` act on the submodule's
  `.git`, not the superproject's — silently, with no error.
- Sibling worktrees of one repository share identical relative paths, so a wrong-tree
  verification run can end in a plausible PASS: the false-green signature. Confirm the
  identity triple before you record the output.
- `git -C <path>` runs as if git had started in `<path>`, ignoring the ambient cwd — the robust fix.
- A subshell `( cd sub && ... )` confines the cwd change to the parentheses.
- Companion skill for the broader Odysseus pin workflow (selective `--remote`, `git add .`
  foot-gun, rebase/justfile collisions): [[odysseus-multi-branch-submodule-pin-management]].
- Related: [[session-cwd-path-alias-repo-binding]] — re-derive the repository binding from
  canonicalized paths and git facts after a session move or path aliasing; the same identity
  triple protects in-session cwd drift.
- Related: [[test-worktree-parents-path-resolves-wrong-tree]] — repo-scanning tests that
  anchor to `parents[N]` resolve the wrong tree when invoked from another checkout's root.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Odysseus | Bumping all submodule pins in the meta-repo; a persisted `cd control/Agamemnon` from an inspection call redirected later `git add`/`status`/`log` to the submodule | Recovery via `git -C <superproject> add -A` staged all 14 pins; verified-local (skill PR CI gate not yet observed green) |
| A multi-worktree PR delivery session | 2026-10 — driving verification across two sibling worktrees after absolute-path edits; the ambient cwd reverted between calls around a background-task notification | Relative-path pytest/ruff ran against the unmodified sibling tree and printed plausible PASS counts; an in-command `git log -1`/`rev-parse` identity check exposed the binding, and re-pinned runs produced valid evidence; verified-local |
