---
name: session-cwd-path-alias-repo-binding
description: "Bind repository work to canonicalized paths and git identity, not to remembered session paths. Use when a session working directory moves, a remembered path goes stale, or one checkout is visible under several absolute prefixes."
category: tooling
date: 2026-10-09
version: "1.0.0"
user-invocable: false
tags: [session-cwd, working-directory, path-alias, symlink, bind-mount, realpath, canonicalize, repo-binding, identity-verification, hosted-writes]
---

# Bind repository identity to canonicalized paths and git facts, not to remembered session paths

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-10-09 |
| **Objective** | Keep repository binding correct when an agent session's working directory moves, or when one checkout is reachable through more than one absolute path (symlinked or bind-mounted prefixes). |
| **Outcome** | During a full-repository review, a remembered pre-move path no longer existed and the target checkout was visible under two prefixes. Re-deriving the binding from canonicalized paths and git facts kept every verification and hosted write on the intended repository. |
| **Verification** | verified-local — the aliasing and the re-binding protocol were both observed and executed in-session. |

## When to Use

- The session started in one directory and continued in another — a session move, a harness restart with a different working directory, or a manually relocated checkout.
- A previously used absolute path now fails an existence check, or resolves to content that differs from what you recorded.
- One repository is reachable through two absolute prefixes: a symlinked home directory, a bind mount, or a local plus network mount of the same tree.
- You compare the current path with a recorded path to decide "same repository or different repository".
- You are about to run identity-sensitive hosted writes (`gh issue create`, `gh pr create`, label or sub-issue edits) that resolve the target repository from the ambient working directory.

## The two failure mechanisms

1. **Stale path.** A session move leaves the remembered absolute path pointing at a location that no longer exists, or — worse — at a same-named path that later holds a different tree. Commands then fail with confusing errors, or act on the wrong tree.
2. **Path alias.** Two different strings, for example a direct home path and a storage-mounted home path, resolve to the same directory. A raw string comparison reports a false repository mismatch and sends tooling down a wrong-repository recovery path.

Both mechanisms break binding that is based on remembered path strings. Binding based on canonicalized paths and git facts survives both.

## Verified Workflow

### Quick Reference

```bash
# 1. Canonicalize BEFORE comparing — never compare raw path strings:
realpath "$PATH_A"; realpath "$PATH_B"     # equal outputs => same directory

# 2. Derive identity from git facts at the canonical path:
git -C "$DIR" rev-parse --show-toplevel    # physical repository root
git -C "$DIR" rev-parse HEAD               # exact source identity
git -C "$DIR" remote get-url origin        # hosting identity

# 3. After any session move, treat remembered paths as stale:
[ -d "$REMEMBERED" ] || echo "STALE — resolve again from the current session directory"

# 4. Before a hosted write, confirm the ambient resolution or bypass it:
gh repo view --json nameWithOwner          # what gh WOULD target from this cwd
gh issue create -R OWNER/REPO ...          # explicit target wins over ambient cwd
```

### Detailed Steps

1. **Canonicalize every path before comparison.** Use `realpath` or `Path.resolve()`. Two prefixes of one mount compare equal only after resolution; unresolved strings compare unequal and trigger false wrong-repository handling.
2. **Derive repository identity from git facts.** Record top-level, `HEAD`, and `origin` from the canonical path. A path string is an address, not an identity — addresses change when sessions move, identity does not.
3. **Re-validate after any session move.** Existence-check, canonicalize, and re-derive git identity before you reuse a path that was recorded before the move. Do not trust a path only because it existed earlier in the session.
4. **Re-resolve before identity-sensitive hosted writes.** `gh` resolves the target repository from the current working directory unless you pass `-R OWNER/REPO`. After any move or aliasing doubt, either confirm the ambient resolution with `gh repo view` or pass the explicit target to every write.
5. **Stop on identity disagreement.** If one path string now resolves to a different git directory, stop and re-bind. Do not merge evidence that was collected under two different bindings.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Reused a remembered pre-move path | Referenced an absolute path recorded before the session moved | The path no longer existed; every command on it failed, and a same-named path could later hold a different tree | After a session move, treat every remembered path as stale: existence-check, canonicalize, and re-derive git identity before use |
| Compared path strings for same-repository | Checked `current_path == recorded_path` to confirm the binding | The same checkout was visible under two prefixes, so equal repositories compared unequal — a false mismatch that triggered wrong-repository handling | Canonicalize both paths with `realpath` (or `Path.resolve()`) before any comparison, then confirm identity with git facts |

## Results & Parameters

- Canonicalization: `realpath <path>` or Python `Path(<path>).resolve()`; compare only the resolved values.
- Identity triple: `git -C <dir> rev-parse --show-toplevel`, `rev-parse HEAD`, `remote get-url origin`. All three must agree with the recorded binding.
- Generalized alias example: a home directory directly at `/home/<user>` that is also bind-mounted at `/mnt/<storage>/home/<user>` — one tree, two strings.
- Cost: the full re-binding protocol is a handful of read-only commands — seconds. A wrong-repository write needs an incident cleanup.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| A full-repository review session | 2026-10 — the session continued in a different directory than it started in, and the reviewed checkout was visible under two path prefixes | remembered-path reuse failed an existence check; canonicalized comparison plus git-fact binding kept all verification and hosted writes on the intended repository |

## References

- Related skill: [automation-ambient-cwd-repo-resolution-breaker-cascade](./automation-ambient-cwd-repo-resolution-breaker-cascade.md) — ambient-CWD repo resolution in multi-repo automation loops and its cascade failure mode
- Related skill: [git-submodule-cd-persists-wrong-repo](./git-submodule-cd-persists-wrong-repo.md) — a persisted `cd` redirects git to a submodule; re-scope with `git -C`
- Related skill: [test-worktree-parents-path-resolves-wrong-tree](./test-worktree-parents-path-resolves-wrong-tree.md) — path-relative tests resolve against the wrong checkout when the cwd is wrong
- Related skill: [repo-audit-triage-fix-and-issue-workflow](./repo-audit-triage-fix-and-issue-workflow.md) — re-resolve the repository binding before each hosted write during issue publication
