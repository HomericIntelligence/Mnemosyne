---
name: debugging-bash-cwd-edit-tool-divergence
description: "Diagnose and prevent silent file-edit divergence when a Claude Code session has multiple git worktrees checked out and Bash tool cwd drifts away from the absolute paths used by Read/Edit/Write. Use when: (1) Read shows expected content but grep from Bash cannot find it, (2) Edit appears to succeed but subsequent Bash commands (sed/grep/python rewrites) operate on a stale file, (3) a commit lands on an unexpected branch in a sibling worktree, (4) you ran `cd <worktree>` in a Bash call earlier in the session and downstream tool results disagree."
category: debugging
date: 2026-05-17
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - bash
  - cwd
  - worktree
  - edit-tool
  - tool-divergence
  - claude-code
---

# Bash CWD vs Edit Tool Divergence in Multi-Worktree Sessions

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-17 |
| **Objective** | Detect, root-cause, and prevent silent divergence between Bash-tool cwd and the absolute paths used by Read/Edit/Write/Grep/Glob when multiple git worktrees coexist. |
| **Outcome** | Verified live: a stray commit (`cf710fb4`) on a stray branch (`ci-pipe-handler-cores-gate`) was traced to a Bash `cd worktrees/coredump-pipe-handler` earlier in the session. Edit operated on the main worktree's `.github/workflows/comprehensive-tests.yml`; Bash grep/sed/python rewrites ran against the sibling worktree's copy. Resolved by `cd /home/mvillmow/Projects/ProjectOdyssey` to re-anchor. |
| **Context** | Claude Code's Bash tool persists shell cwd across invocations, but Read/Edit/Write/Grep/Glob always use absolute paths. When a user has multiple worktrees and an earlier Bash call did `cd <other-worktree>`, the two tool families silently operate on different copies of the "same" file. |

## When to Use

Use this skill when:

1. You have multiple git worktrees checked out simultaneously.
2. You (or a prior turn) ran `cd <worktree>` inside a Bash tool call earlier in the session.
3. `Read` shows content (an edit you just made) that a subsequent `grep` from Bash cannot find.
4. An `Edit` appears to succeed, but a follow-up Bash rewrite (sed/awk/python heredoc) reports the file already lacks the change, or vice versa.
5. A commit unexpectedly lands on a branch that belongs to a different worktree than the one you thought you were editing.
6. `git status` and `git log` results from Bash disagree with the file contents you see via Read.

Do NOT use this skill if:

- Only one worktree is checked out for the repo (the divergence cannot happen).
- The discrepancy is due to file-modification race between two tools modifying the same file (different problem).
- The mismatch is between staged and working-tree content (use a `git diff` skill instead).

## Verified Workflow

### Quick Reference

```bash
# 1) Anchor cwd at the start of every session
cd /abs/path/to/main/worktree && pwd

# 2) Operate on other worktrees WITHOUT persisting cwd
git -C /abs/path/to/other/worktree status
(cd /abs/path/to/other/worktree && some_command)   # subshell — cwd does not leak

# 3) If you must persist a cd, re-anchor before any Edit-then-Bash sequence
cd /abs/path/to/main/worktree && pwd

# 4) Detection: when Read shows new content but grep cannot find it
pwd                           # are we where we think we are?
realpath .github/workflows/comprehensive-tests.yml   # which copy is this?
git rev-parse --show-toplevel  # which worktree root am I in?
```

### Step-by-step

1. **Anchor cwd explicitly at session start.** First Bash call should be
   `cd /abs/path/to/main/worktree && pwd` — never rely on the inherited cwd.

2. **Treat `cd` as session-global state.** Every `cd` in a Bash call persists for
   ALL subsequent Bash invocations until the session ends. Edit/Read/Write/Grep/Glob
   do NOT see this cd — they use absolute paths verbatim.

3. **Prefer cwd-free patterns over `cd`:**
   - `git -C <path> <cmd>` instead of `cd <path> && git <cmd>`
   - `make -C <path>` instead of `cd <path> && make`
   - `(cd <path> && cmd)` subshell when a tool truly needs cwd — the parens
     prevent leak.

4. **After ANY `cd`, re-anchor before mixing with Edit:** If a turn does
   `cd <other-worktree>` and then later wants to use Edit on a file in the
   main worktree, run `cd /abs/path/to/main/worktree` FIRST so any follow-up
   Bash verification (`grep`, `git status`, `cat`) sees the same file Edit
   touched.

5. **When results disagree, suspect cwd divergence FIRST:** Symptoms:
   - `Read /abs/path/file` shows line X present.
   - `Bash: grep X /abs/path/file` (absolute path!) — still might fail if a
     Python heredoc or sed used a relative path resolved against the wrong cwd.
   - `Bash: grep X file` (relative) — definitely cwd-dependent.

   Diagnostic sequence:

   ```bash
   pwd
   git rev-parse --show-toplevel
   realpath <file>
   git log -1 --oneline -- <file>
   ```

   If `git rev-parse --show-toplevel` is not the worktree you expected, that's
   the bug.

6. **Recovery when a stray commit landed in the wrong worktree:**

   ```bash
   # Find the stray commit
   cd /abs/path/to/wrong/worktree
   git log --oneline -5
   # Cherry-pick into the correct worktree, then reset the wrong one
   cd /abs/path/to/correct/worktree
   git cherry-pick <stray-sha>
   cd /abs/path/to/wrong/worktree
   git reset --hard HEAD~1     # or origin/<branch> as appropriate
   ```

7. **Use absolute paths in EVERY Bash command.** Even if cwd is correct, a
   relative path is fragile across turns. Absolute paths neutralize cwd entirely.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust Edit succeeded | Assumed `Edit` on an absolute path edited the file that Bash subsequently `grep`'d | Edit operated on the main worktree path; Bash `grep` ran in a different cwd against the sibling worktree's copy of the same relative path | Edit and Bash can target different copies of the same logical file when multiple worktrees exist |
| Re-Read to verify | Re-read the file via `Read` (absolute path) to confirm the edit landed | Read showed the correct content (main worktree), so Edit "looked successful" — but Bash kept grepping the wrong copy via relative path | A successful Read does not prove subsequent Bash commands see the same file |
| Python heredoc rewrite | Switched to `python3 <<EOF` rewrite after Edit refused (file modified between reads) | The Python interpreter inherits Bash cwd, opened a relative path that resolved into the wrong worktree | Heredoc/subprocess tools inherit Bash cwd — same root cause, different surface |
| Grep with relative path | Used `grep PATTERN .github/workflows/comprehensive-tests.yml` to confirm the change | Relative path resolved against stale cwd; returned no match even though the file in the main worktree clearly contained the pattern | Always use absolute paths in Bash when cross-checking Edit results |
| Blame the Edit tool | Suspected Edit was silently no-oping or operating on a cached buffer | Edit had worked correctly the whole time — the divergence was in the verifier, not the editor | When two tools disagree, suspect cwd before suspecting tool bugs |

## Results & Parameters

**Tool cwd behavior matrix (Claude Code):**

| Tool | CWD-dependent? | Notes |
| ---- | -------------- | ----- |
| Bash | YES — persists across calls | Every `cd` leaks into the next Bash turn |
| Read | NO | Requires absolute path |
| Edit | NO | Requires absolute path |
| Write | NO | Requires absolute path |
| Grep | NO | Uses absolute or workspace-relative path arg |
| Glob | NO | Uses absolute or workspace-relative path arg |

**Detection signal:** `grep` returns no match for content that a fresh `Read` of
the same absolute path clearly shows. The fastest discriminator is
`git rev-parse --show-toplevel` — if it does not match the worktree root that
contains the Edit's target path, the session has diverged.

**Prevention checklist (run at session start when worktrees exist):**

```bash
cd /abs/path/to/main/worktree
pwd
git worktree list           # know which siblings exist
git rev-parse --show-toplevel
```

**Commit message format for fixes that resulted from this debugging:**

```text
fix(<scope>): restore intended <file> change in <main-worktree>

Previous edits were applied via Edit (absolute path, main worktree) but
Bash-tool follow-ups ran in a sibling worktree's cwd, producing a stray
commit on <stray-branch>. Re-anchored cwd and reapplied.
```

**Related skills:**

- `git-worktree-management-patterns` — general worktree hygiene
- `parallel-pr-worktree-workflow` — multi-worktree parallel PR work
- `audit-skip-cwd-resolution` — cwd-relative path semantics in scripts
