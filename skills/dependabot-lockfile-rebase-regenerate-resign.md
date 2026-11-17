---
name: dependabot-lockfile-rebase-regenerate-resign
license: BSD-3-Clause
description: "Resolve dependency-bot manifest and lock conflicts by preserving intended constraints, regenerating locks, and following repository signing policy."
category: ci-cd
date: 2026-06-11
version: "1.2.0"
user-invocable: false
verification: verified-ci
tags:
  - dependabot
  - pixi-lock
  - lockfile
  - pixi
  - pyproject
  - dependency-bump
  - rebase
  - semantic-merge
  - regenerate
  - locked
  - re-sign
  - gpg-signing
  - bot-pr
  - fleet-sync
  - conflict-resolution
  - constraint
  - mypy
  - force-with-lease
  - stale-info
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/dependabot-lockfile-rebase-regenerate-resign.history"
history-cleanup-date: "2026-09-20"
---

# Dependabot Lockfile Rebase: Semantic-Merge, Regenerate, Re-Sign

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-11 |
| **Objective** | Resolve a reported Dependabot dependency-bump conflict, or an active security task that needs main content, without hand-merging the generated lock; preserve main's refactored manifest layout and re-sign every commit so pr-policy accepts it |
| **Outcome** | PR #1032 (HomericIntelligence/ProjectHephaestus, author `app/dependabot`) rebased and MERGED this session; CI (including the `--locked` gate) passed green |
| **Verification** | verified-ci |

## When to Use

- A Dependabot (or other bot) dependency-bump PR shows `CONFLICTING`/`DIRTY` and the conflict is on `pixi.lock` plus `pyproject.toml`/`pixi.toml`.
- `hephaestus-fleet-sync` (or any `--author @me`-scoped rebase tool) ran but did NOT touch the bot PR — its discovery deliberately skips PRs you didn't author, so bot PRs are invisible to it and need a MANUAL pass.
- main has REFACTORED the dependency layout since the bot opened the PR (e.g. moved a dep out of separate `[feature.dev.dependencies]`/`[feature.lint.dependencies]` blocks into a consolidated `[feature.shared.dependencies]` block), so the PR's stale edit targets a location that no longer exists.
- You hit a `pixi.lock` merge conflict and are tempted to `--ours`/`--theirs`/hand-edit it — don't; regenerate.
- pr-policy requires every commit cryptographically signed with the committer email matching a UID on your GPG key (NOT the bot's noreply email), and the bot's commits are signed by the bot.
- Your rebased bot branch fails to push with `stale info` although the lease was fresh when you fetched — the bot force-updated its own remote branch while you worked.

Do not rebase a bot PR merely because it is old. After task completion, rebase
only to resolve a reported merge conflict; repository CI/CD owns other main
integration.

## Verified Workflow

### Quick Reference

```bash
# 0. Isolated worktree (never rebase a bot PR in the shared checkout)
REPO=HomericIntelligence/ProjectHephaestus
BRANCH=dependabot/pip/python-dependencies-6615f4149c
KEY_EMAIL='<signing-email>'
git fetch origin
git worktree add /tmp/pr-1032 -b rebase/dependabot-1032 "origin/$BRANCH"
cd /tmp/pr-1032

# 1. Only if a host-reported conflict or an active security task requires main
#    content, rebase onto main AND re-sign every commit (bot signed them; pr-policy wants YOUR key + committer email)
git rebase origin/main \
  --exec "git -c user.email=$KEY_EMAIL commit --amend --no-edit -S --reset-author"

# 2. On a pyproject.toml / pixi.toml conflict: SEMANTIC merge.
#    Keep main's layout; apply ONLY the bump's real constraint change to main's CURRENT location.
#    Here: mypy "<2,>=1.8.0" -> ">=1.8.0,<3", re-applied to main's consolidated
#    [feature.shared.dependencies] block; drop the PR's obsolete reintroduced [feature.dev]/[feature.lint] block.
git add pyproject.toml pixi.toml
git -c user.email=$KEY_EMAIL rebase --continue   # (--exec re-signs the amended commit)

# 3. On a pixi.lock conflict: do NOT hand-merge a generated file. Take main's lock, then REGENERATE.
git show origin/main:pixi.lock > pixi.lock   # or: git checkout --theirs pixi.lock
pixi lock                                    # often: "Lock-file was already up-to-date" if resolved ver already satisfies the widened constraint
git add pixi.lock

# 4. MANDATORY local validation BEFORE pushing — proves lock matches manifest (mirrors CI's --locked gate)
pixi install --locked

# 5. Force-push (lease-safe); PR keeps state:implementation-go + auto-merge and lands when CI re-runs green
git push --force-with-lease origin HEAD:"$BRANCH"
```

### Detailed Steps

1. **Use an isolated worktree.** Never rebase a bot PR in your main checkout — bot branches force-push under you and the shared clone's state matters for concurrent work. First confirm the host-reported conflict or active-task main-content need.
2. **Re-sign during the rebase.** The bot's commits carry the bot's signature. pr-policy requires each commit signed with a key whose UID email matches the committer email — use `--exec 'git -c user.email=<key-email> commit --amend --no-edit -S --reset-author'`. Do NOT use the bot's noreply email and do NOT trust `git log --show-signature` alone (it can show "Good signature" while GitHub still reports the commit unverified — check `gh api .../commits/<sha> --jq .commit.verification`).
3. **Manifest conflicts are CONSTRAINT EDITS, not 3-way text merges.** Read what real change the bump makes (one constraint string), then apply ONLY that to main's CURRENT layout. If main moved/renamed/consolidated the dependency block, re-apply the bump to the NEW location and DELETE the PR's stale reintroduced block. Blindly keeping the PR's old structure reintroduces a layout main deliberately removed.
4. **Update BOTH manifests.** `pyproject.toml` and `pixi.toml` must agree — a consistency test (`test_dependency_floor_consistency.py`) asserts they match. Editing only one fails CI.
5. **Never hand-merge `pixi.lock`.** It encodes resolved versions + hashes; any manual/`--ours`/`--theirs` merged result is invalid. Take main's lock and REGENERATE with `pixi lock` (or `pixi install`). If the already-resolved version satisfies the widened constraint (e.g. mypy 1.20.2 satisfies `<3`), `pixi lock` reports "Lock-file was already up-to-date" and the lock is unchanged — that's correct, not a failure.
6. **Validate `--locked` before pushing.** Run `pixi install --locked`; it must succeed. This proves the lock matches the manifest and mirrors CI's `--locked` gate — a mismatched lock fails CI.
7. **Force-push lease-safe and let auto-merge finish.** `git push --force-with-lease`. The PR retains its `state:implementation-go` label and armed auto-merge, so it lands once CI re-runs green.
8. **If the push reports `stale info`, compare before you retry — never force a stale copy over the bot's newer branch.** The bot can regenerate its branch while you rebase (a scheduled re-run, a new dependency group resolution, or a manual re-create). Re-fetch and compare:

   ```bash
   git fetch origin "$BRANCH"
   git log --oneline -3 "origin/$BRANCH"
   git merge-base --is-ancestor origin/main "origin/$BRANCH" && echo "bot head is based on the current trunk tip"
   ```

   - If the bot's new head is **already based on the current trunk tip**, its regenerated bump is newer evidence of the same intent and supersedes your rebase. Discard your local copy (`git reset --hard "origin/$BRANCH"` in the worktree) and push nothing. The bot's own commit signature shows `%G?` `E` locally because your trust ring cannot check the bot's key; the forge verifies it, so do not "fix" it.
   - If the bot's new head is **not** based on the current trunk tip, redo the rebase from its new head (steps 1–7).
   - A blind retry after a re-fetch can overwrite the bot's newer bump with your older resolution. Compare first; push only when your rebased head is the content that must land.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Rely on fleet-sync | Expected `hephaestus-fleet-sync` to rebase the DIRTY Dependabot PR with the rest of the queue | Its PR discovery is scoped to `--author @me` (by design, #1070/#1071), so bot-authored PRs are invisible and silently skipped | For a policy-permitted rebase, handle the bot dependency PR manually; @me-scoped fleet tooling will never pick it up |
| Keep the PR's manifest block | Resolved the `pyproject.toml`/`pixi.toml` conflict by keeping the bot's side of the block | main had refactored mypy into a consolidated `[feature.shared.dependencies]` block; keeping the PR side reintroduced the obsolete `[feature.dev.dependencies]`/`[feature.lint.dependencies]` blocks main had removed | Manifest conflicts are constraint edits onto main's CURRENT layout — re-apply only the bump to the new location, drop stale structure |
| Hand-merge the lockfile | Tried to resolve `pixi.lock` conflict markers / use `--ours`/`--theirs` | A merged generated lock encodes inconsistent resolved versions + hashes → invalid → CI `--locked` gate fails | Never hand-merge `pixi.lock`; take main's lock and regenerate with `pixi lock` |
| Keep the bot's signature | Left Dependabot's commits as-is after rebase | pr-policy requires every commit signed with a key UID email matching the committer; the bot's signature/email don't match your key | Re-sign every commit during rebase via `--exec` with `-S --reset-author` and `user.email=<your key email>` |
| Edit only one manifest | Updated the mypy constraint in `pyproject.toml` only | `test_dependency_floor_consistency.py` asserts `pyproject.toml` and `pixi.toml` agree | Update BOTH manifests in lockstep for any cross-referenced constraint |
| Push past a moved bot branch | Rebasing a batch of PRs, pushed the rebased bot branch with `git push --force-with-lease` | The push rejected with `stale info`: the bot had force-updated its own remote branch between the initial fetch and the push, regenerating the bump on the current trunk tip | Re-fetch, compare the bot's head against the trunk tip, and discard the local rebase when the bot's head supersedes it; the bot's regenerated bump is the newer intent, and a retry would clobber it |

## Results & Parameters

Verified instance (HomericIntelligence/ProjectHephaestus, PR #1032, MERGED, verified-ci):

```text
PR:            #1032
Author:        app/dependabot
Branch:        dependabot/pip/python-dependencies-6615f4149c
Manifest edit: mypy "<2,>=1.8.0"  ->  ">=1.8.0,<3"   (in BOTH pyproject.toml AND pixi.toml)
Layout note:   main consolidated mypy into [feature.shared.dependencies];
               re-applied the bump there, dropped the PR's reintroduced
               [feature.dev.dependencies]/[feature.lint.dependencies] block
Lockfile:      "Lock-file was already up-to-date" — mypy 1.20.2 already satisfied <3, no lock change
Re-sign email: <signing-email>
Validation:    pixi install --locked  (must succeed before push)
Push:          git push --force-with-lease
Result:        auto-merge retained (state:implementation-go); CI green; MERGED
```

Second verified instance (v1.2.0, verified-local; batch rebase of five open PRs
in one session, one of them a dependency-bot branch):

```text
Trigger:       git push --force-with-lease rejected with "stale info"
Cause:         the bot force-updated its remote branch during the batch;
               its regenerated bump was already based on the trunk tip
Action:        re-fetch, compare bases, reset the worktree branch to the
               bot's head, push nothing
Signature:     the bot's own head shows %G? E locally; the forge verifies it
Outcome:       PR stayed mergeable with the bot's own head; the other four
               rewritten branches re-signed clean during their rebases
```

Core lesson: a dependency-bump conflict is a **constraint edit + lock regeneration**, NOT a 3-way merge of the lockfile — and bot PRs are invisible to `@me`-scoped fleet tooling, so they need a hand pass. When the bot's own branch moves under you, its regenerated head supersedes your local rebase; compare bases before any retry push.

**Related skills:** `pr-rebase-conflict-resolution-patterns` (general rebase/conflict playbook) and `dependency-update-automation-bot-prs` (Renovate config + bot-PR scope/drift review). This skill is the Dependabot-lockfile-specific rebase case.
