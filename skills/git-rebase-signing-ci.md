---
name: git-rebase-signing-ci
license: BSD-3-Clause
description: "Diagnose signature failures, resume a justified rebase after conflicts, re-sign rewritten commits when the rebase replay is a silent no-op, compare signing repair with current branch-update or merge-queue requirements, and tell a label short-circuit apart from a signature failure when a provenance gate fails inside review-to-merge drive work."
category: tooling
date: 2026-07-17
version: "1.8.0"
user-invocable: false
verification: verified-ci
tags: [git, signing, rebase, ci, gpg, exec, conflict-resolution, update-branch, force-with-lease, stale-info, branch-protection, up-to-date, stacked-pr, squash-merge, merge-queue, ssh-signing, commit-tree, provenance-gate, label-gate]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/git-rebase-signing-ci.history"
history-cleanup-date: "2026-09-20"
---

# Git Rebase Signing for CI

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-16 |
| **Objective** | Sign all PR commits to pass CI pr-policy checks that require GPG signatures, avoid commit corruption when a `--exec` rebase stops on a real conflict, and avoid the server-side branch updater that silently strips signatures |
| **Outcome** | All commits show 'G' after rebase; corruption recovery, server-side stripping, and the label short-circuit have verified steps |
| **Verification** | verified-ci |
| **History** | [changelog](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/git-rebase-signing-ci.history) |

## When to Use

- CI `pr-policy` check fails with "every commit is signed" requirement
- Commits were created without `-S` flag and need to be retroactively signed
- After rebasing, need to verify all commits are signed
- A `git rebase --exec ...` run stops with a real content conflict and you
  need to resume it without corrupting the in-progress commit
- `git reflog` shows an amend landed directly on a `rebase (start): checkout`
  entry with no intervening pick — signals the corruption described below
- `pr-policy` fails with `commit signature is missing or invalid` right after the PR branch was
  updated via GitHub's **Update branch** button or `gh pr update-branch --rebase`
- `git push --force-with-lease` is rejected with `stale info` after a server-side branch update
- The repository requires strictly up-to-date branches AND signed commits, no merge queue is
  enabled, and several PRs must merge in sequence
- The same repository has NO integration mechanism at all (no merge queue, no branch-update bot)
  and an armed auto-merge never fires because the head goes stale before checks pass
- A GitHub merge queue IS enabled — before preparing any re-signed rebase, confirm the PR is not
  simply queueable (the queue makes the local rebase unnecessary)
- A stacked PR's base branch was squash-merged and the branch now shows CONFLICTING
- A forge commit-provenance check fails with `invalid_signature` (or a per-commit "signature is missing
  or invalid" report) after PR commits were rewritten locally — a rebase, cherry-pick, or other object
  rewrite dropped the signatures the forge verifies against the account's registered signing keys
- `git rebase --exec 'git commit --amend ... -S' <base>` finished instantly, created no new objects, and
  `%G?` still shows `N` — the replay skipped every pick, so the exec hook never ran
- The signing helper (`ssh-keygen` for `gpg.format=ssh`) fails with a library version error such as
  `OpenSSL version mismatch` only when a privately built or bundled git invokes it
- A commit reports `%G?` `U` and `%GK` shows a fingerprint that is NOT the configured
  `user.signingkey` fingerprint — a foreign key (for example, a shared automation identity's own
  key) signed the commit, and the forge cannot bind it to the author's registered keys
- You must re-sign a stack whose tree content must stay byte-identical and whose commits already
  sit on their base, so a plain `--exec` replay would no-op
- A provenance gate failed inside review-to-merge drive work, and you must order the label fix
  and the signature fix

## Verified Workflow

### Current applicability

Use [verify-pr-ready](verify-pr-ready.md) for live policy, affected validation, and evidence
reuse. A branch behind main is not itself blocked. Rebase only for a blocker, required main
content, or a host-reported merge conflict; otherwise CI/CD or the merge queue integrates
main. Keep required CI and exact-head review before merge.

### Signing repair boundary

Signing repair is separate from target integration. Re-sign without changing source content
or ancestry unless integration is also necessary. The `origin/main` examples below apply only
when integration is justified. Do not repeat a full local suite solely because main moved.

### Quick Reference

```bash
# Only for an active-task blocker or required main content, or a host-reported conflict
# after completion: replay with signing.
git rebase --exec 'git commit --amend --no-edit -S' origin/main

# Verify all commits are signed (G = good)
git log --format='%h %G? %s' origin/main..HEAD

# Force push to update PR
git push --force-with-lease origin <branch>
```

> **Critical — if the `--exec` rebase stops on a real conflict, do NOT
> hand-invoke the exec command.** After resolving the conflict
> (`git add <file>`), always run `git rebase --continue` — never run
> `git commit --amend ...` yourself to "help it along," even though the
> rebase reports "Next command to do: exec ...". At that pause point the
> conflicted commit has **not yet been created** as a commit object; `git
> rebase` is still mid-`pick`. Manually running `git commit --amend` amends
> whatever HEAD currently is — the rebase's "onto" checkout (the base branch
> tip) — instead of finalizing the pick. `git rebase --continue` correctly
> sequences "finalize the pick as a real commit" BEFORE "run the queued exec
> command against it." This applies to any `--exec` script, not just
> amend/sign (e.g. `--exec "pytest"` has the same risk).

### Detailed Steps

1. **Identify unsigned commits**: `git log --format='%h %G? %s' origin/main..HEAD` — look for `N` (no signature) or `U` (unknown validity).
2. **Rebase with signing only when permitted**: for an active-task blocker or required main content, or a host-reported conflict after completion, run `git rebase --exec 'git commit --amend --no-edit -S' origin/main`. This replays each commit and re-signs it with your GPG key.
3. **If it stops on a conflict**: resolve the conflict per-hunk, `git add <file>`, then run `git rebase --continue` (NOT `git commit --amend` by hand — see warning above). `--continue` finalizes the pick as a commit and then automatically fires the queued `--exec` command against that new commit.
4. **Verify**: Re-run `git log --format='%h %G? %s' origin/main..HEAD` — all should show `G`.
5. **Force push**: `git push --force-with-lease origin <branch>` — the `--force-with-lease` is safer than `--force` as it rejects if the remote has changes you haven't fetched.

### Recovery if you already hand-invoked the exec command mid-conflict

If `git commit --amend` was run by hand while paused on a conflict and the
result looks wrong (see Failed Attempts below for the corruption symptoms):

1. Verify the working tree is clean/matches your target state:
   `git status` + `git diff <target-sha> HEAD`.
2. If `git rebase --abort` is unavailable (e.g. blocked by a safety-net
   policy) and deleting `.git/**/rebase-merge` directly is also blocked as an
   unsafe path deletion, use the non-destructive combo instead:
   `git reset --keep <pre-rebase-sha>` followed by `git rebase --quit`.
   `--quit` clears only the rebase bookkeeping directory — unlike `--abort`,
   it does **not** touch HEAD or the working tree — so it is safe once HEAD
   is already back at the pre-rebase commit via `reset --keep`.
3. Redo the rebase in two explicit, separate passes instead of `--exec`:
   (a) plain `git rebase origin/main`, resolve conflicts by hand per-hunk
   (verify with `git ls-files --stage <file>` that stage `:2:` = ours/base and
   `:3:` = theirs/your-branch — rebase inverts the usual merge meaning),
   `git add <file>`, `git rebase --continue` through to completion (git
   prints "Successfully rebased..."); (b) only then run
   `git commit --amend --no-edit -s -S` once, standalone, over the final HEAD
   to add signing/DCO. This decouples conflict-resolution-continuation from
   the signing amend and avoids the whole bug class.

See also `pr-rebase-conflict-resolution-patterns.md` § re-signing replayed
commits for the general `--exec` signing pattern on conflict-heavy rebase
chains — this skill's warning applies there too whenever a pick in that
chain conflicts.

### Server-side branch updates strip signatures (v1.2.0)

GitHub's **Update branch** button and `gh pr update-branch --rebase` perform the rebase
server-side: every commit is re-created by GitHub **without your GPG signature**, so a
signed-commits `pr-policy` gate that was green goes red on the next run with
`<sha>: commit signature is missing or invalid`. On a repo that requires signed commits,
NEVER update a PR branch server-side. If a rebase is otherwise permitted, instead:

```bash
# Local re-signed rebase (commit.gpgsign re-signs each replayed commit)
git fetch origin main <branch>          # refresh BOTH refs; stale tracking ref => lease 'stale info'
git -c commit.gpgsign=true rebase origin/main
git log --show-signature -2             # expect 'Good signature' on every replayed commit
git push --force-with-lease --force-if-includes origin <branch>
```

- **Lease rejection `stale info`:** after any server-side update the remote-tracking ref no
  longer matches the remote, and `--force-with-lease` (correctly) refuses. Fetch the branch,
  confirm the remote head is exactly the known server-side rewrite (not someone else's work),
  then push again.
- **Strict up-to-date + signed commits:** a behind status alone does not permit an agent rebase,
  whether or not the repository has a merge queue. Hand ordinary integration to repository CI/CD.
  If CI/CD reports an actual merge conflict, resolve that conflict with the permitted signed rebase
  above. Do not use a local serial re-sign-and-force-push cycle merely after a sibling merges.
- **End-game exception, no integration mechanism:** when the repository has NO way to integrate
  a behind head (no merge queue, no branch-update bot) and CI time meets or exceeds the base-move
  cadence, a completed, reviewed, checks-green PR can merge only inside a manufactured window.
  Rule: the policy above still forbids treadmill rebases during work; in the end-game, repeat
  minimal signed rebases onto each base move, lease-push, fix any real blocker first (unresolved
  review threads, draft state), and merge the exact head the moment merge state reads CLEAN —
  the window can last seconds; restart on the next base move. Never use the server-side
  "Update branch" here: it strips signatures and turns the provenance gate red.
- **A real GitHub merge queue makes the local re-signed rebase UNNECESSARY:** when the repo has a
  merge queue enabled (branch protection "Require merge queue" / a `merge_group`-triggered required
  workflow), a green PR does NOT need to be brought up-to-date by hand. Queue it and the queue
  rebuilds the branch on the current base and merges it **server-side**, signing the resulting merge
  with GitHub's key — the PR lands MERGED with no author force-push. So before starting the
  serial re-sign-rebase cycle above, check `gh pr view <N> --json state,mergeStateStatus`: if the
  PR is already MERGED or is queueable, skip the rebase entirely. Note the queue's transient head
  can appear unsigned (`N`) and carry extra queue-machinery commits while it processes — that is
  ephemeral queue state, not the final signed merge commit, and it is not a signature failure to fix.
- **Stacked PR whose base was squash-merged:** the branch still carries the base's original
  commits (now absent from `main`'s history), so it shows CONFLICTING. Shed them with
  `git rebase --onto origin/main <old-base-head> <branch>`, then re-verify signatures and push.

### Verified-signature provenance gates and no-op replays (v1.5.0)

Some repositories gate merges on each PR commit carrying a signature the forge itself
can verify — a signature made by a key registered on the author's account, checked by API
and reported per commit, for example with the reason `invalid_signature`. Any local object
rewrite (an unsigned rebase, cherry-pick, or amend) creates commits without such signatures
and trips the gate even when the content and every other check are green. Repair is always
local; a server-side branch update has the same signature-stripping effect as above.

1. **Why `git rebase --exec 'git commit --amend --no-edit -S'` can silently do nothing:**
   a rebase replays only the picks it considers necessary. When the branch commits already
   sit on top of the current base (their trees match what a replay would produce), git
   skips or fast-forwards every pick — and a skipped pick never fires the `--exec` hook.
   The command exits instantly, no new objects exist, and `%G?` stays `N`. Re-check
   `git log --format='%G?' <base>..HEAD` after any exec-based repair; an unchanged result
   means the replay was a no-op, not a signing failure.
2. **Reliable fallback — rebuild the exact stack with `commit-tree`:** replay each commit
   into a new signed object, preserving author, committer, both dates, tree, and message.
   The loop is in [notes](git-rebase-signing-ci.notes.md). Verify every `%G?` entry and
   `diff` the old and new message lists (empty). Then `git push --force-with-lease` the
   rebuilt head.

   Every rebuilt commit is a new object, so the forge's per-commit check re-runs from
   scratch on the pushed head. Build in a detached worktree; leave the local branch alone.
3. **Signer-exec environment trap:** with `gpg.format=ssh`, git shells out to the
   configured `gpg.ssh.program` (usually `ssh-keygen`). A privately built or bundled git
   can inject its own library search path into the child process, and the helper then fails
   with a version error such as `OpenSSL version mismatch` — even though the same
   `ssh-keygen -Y sign` test succeeds standalone. Drive the `commit-tree` loop above with
   the **system git** (object writes need no network), and reserve the bundled git for the
   network operations it was built for (fetch/push with its credential helpers or CA
   bundle). Test the helper standalone before attributing a signing failure to the key.
4. **SSH-signature verification semantics:** `%G?` reports `U` for a *good* SSH signature
   whose key has no local trust record. That is an object-level success; the forge verifies
   the signature against the account's registered signing keys, so `U` does not block the
   gate. But `U` alone does not prove the signer is yours — it also appears for a foreign
   key. Discriminate with `%GK` before you trust any `U` (see the v1.7.0 section below).
   The repair needs `gpg.format=ssh`, `user.signingkey=<private-key-path>`, and
   `commit.gpgsign=true`; sign with the same key that produced the branch's previously
   green commits.
5. **An armed auto-merge absorbs the repair:** if auto-merge was enabled before the gate
   failed, leave it armed. The re-signed push re-triggers the checks, and the armed
   auto-merge merges on its own once they pass. An automation-log disposition like
   `BLOCKED:auto_merge_already_armed` reports exactly that state — it is a reason to wait
   and watch, not an error to fix.

### Foreign-signer discrimination and byte-identical stack re-sign (v1.7.0)

`%G?` `U` is ambiguous: it can be your own SSH key with no local trust record (benign,
v1.5.0 rule 4), or a *foreign* key — another identity signed the commit, and git reports a
good signature that no local principal matches. Discriminate before you act:

```bash
git log --format='%h %G? %GK' -n 5        # %GK = the signer's key fingerprint
ssh-keygen -lf "$(git config user.signingkey).pub"   # your key's fingerprint
```

A fingerprint mismatch means a foreign signer. Confirm the key is not in any configured
allowed-signers file and is not another registered key of the author. A foreign-key
signature means another identity signed content under your author identity: get explicit
authority to take authorship of that content BEFORE you rewrite it, and record the decision.

Repair (run in a scratch branch or detached worktree, never the shared checkout):

```bash
git rebase --force-rebase --exec 'git commit --amend --no-edit -S' <unambiguous-base>
```

`--force-rebase` replays every pick even when the trees already match, so the exec hook
cannot be swallowed by the v1.5.0 skipped-pick no-op. Then verify, in order:

1. every commit is `%G?` `G` with `%GK` equal to your fingerprint;
2. each new commit's tree hash equals its pre-rewrite tree hash (byte-identical content);
3. `git diff <old-head> HEAD` is empty;
4. author/committer identities and DCO trailers are preserved
   (`git log --format='%b'` still contains every `Signed-off-by`).

Push with the lease pinned to the exact verified old head, not to a moving ref:

```bash
git push --force-with-lease=<branch>:<verified-old-head-oid> origin <local>:<branch>
```

Rewrite consequences: every review record, assessment, or chain carrier bound to an old
head becomes void. Re-run any head-bound review or delivery against the new head; do not
treat pre-rewrite evidence as covering the new objects.

### Label short-circuit versus signature failure in drive-to-merge work (v1.8.0)

A provenance workflow often gates on a state label *and* on a verifiable signature. Read its
trigger list and step order before you repair anything. A common shape runs the label check
first and exits non-zero, so a run that lacks the label never reads a signature.

1. **Read the trigger list.** Find the workflow and list its `on.pull_request_target.types`.
   A `labeled` trigger fires when the state label is applied, with the new label set in the
   payload, so that run can pass at the current head with no push. A workflow that lists only
   `synchronize` replays the label state in the run's payload, and then a push is required.
2. **Read the failing step, not the check name.** When the failing step is the label check,
   the gate stopped before the signature step. Inspect the commits separately, through the
   forge API or `git log --format='%h %G?'`. A signature defect still needs repair, but it is
   not the cause of that run's failure.
3. **Fix the signature first, then the label.** Re-sign or rebuild the head per the sections
   above. A review bound to a head that the provenance gate would reject is stale as soon as
   the head moves.
4. **Bind the review, then set the label, then wait.** Review the exact new head and apply the
   state label. A `labeled`-triggered run starts at that head. Watch it to a terminal
   conclusion instead of pushing a placeholder commit.
5. **Record one correction if a push was not necessary.** Name the run that already passed in
   one comment. Do not rewrite published history to fix a no-op commit message.

A rebase in drive work can re-create signed commits as unsigned ones, including the commit
that the rebase was meant to repair. Check `%G?` on every commit *after* the rebase.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| `git commit --amend -S` per commit | Manual signing of each commit | Tedious and error-prone with multiple commits | Use `--exec` flag to sign all commits in one rebase |
| `git push --force` | Force push without lease check | Could overwrite remote changes from other collaborators | Use `--force-with-lease` for safety |
| `gh pr update-branch --rebase` to satisfy a strict up-to-date branch-protection rule | Server-side rebase to bring two green PRs current with main | GitHub re-created every commit unsigned; the previously-green signed-commits `pr-policy` gate failed on both PRs with `commit signature is missing or invalid` | Never update a signed-commits PR server-side; do a local `git -c commit.gpgsign=true rebase origin/main` and force-push with lease |
| `git push --force-with-lease` immediately after a server-side branch update | Pushing the locally re-signed rebase over the server-side rewrite | Rejected with `stale info` — the local remote-tracking ref predated the server-side rewrite, so the lease check failed | Fetch the branch first, verify the remote head is the expected rewrite, then push; the rejection is the lease working as designed |
| Preparing a local re-signed rebase + user force-push cycle for a green PR on a repo with a merge queue enabled | Rebased the branch onto the new `main`, re-signed, ran full local gates, and waited on a user force-push to satisfy the strict up-to-date rule before merging | Unnecessary work: the merge queue rebuilt and merged the PR server-side (GitHub-signed merge commit) and it landed MERGED while the re-signed branch was still waiting to be pushed — the whole rebase cycle was moot | On a merge-queue repo, check `gh pr view <N> --json state,mergeStateStatus` first; if queueable, just let the queue merge it — do NOT prepare a serial re-sign-rebase cycle. The queue absorbs the up-to-date requirement itself |
| Armed auto-merge on a squash+signed+strict repo with no merge queue and no update bot | Waited across hours of main drift for the armed auto-merge to fire on a reviewed, checks-green head | Each base move made the head stale again before the ~30-minute checks finished; merge state never reached a fireable state, and the real last blockers (draft state, then one unresolved review thread) surfaced only under direct layered diagnosis | Auto-merge never fires on a stale head; manufacture the current+green+unblocked window with minimal signed rebases, clear real blockers first, and merge the exact head as soon as the state flips CLEAN |
| Hand-invoking the queued `--exec` command (`git add <file>` then `git commit --amend --no-edit -s -S`) after resolving a conflict, instead of `git rebase --continue` | Rebase paused mid-conflict showing "Next command to do: exec ..."; resolved the conflict then manually replicated the exec command to "help it along" | The conflicted commit had not yet been finalized as a commit object — `git rebase` was still mid-`pick`. `git commit --amend` amended the rebase's "onto" checkout (base branch tip, which was HEAD at that moment) instead of the picked change, producing a corrupted commit whose diff was the union of an unrelated upstream commit's changes plus the PR's own changes, under the wrong commit message/title. Diagnosed via `git reflog` showing `rebase (start): checkout <base>` immediately followed by `commit (amend): <wrong title>` with no intervening pick entry, plus `git diff <merge-base> <bad-commit> --stat` showing far more files than the original commit's own `git show <sha> --stat` | Always run `git rebase --continue` after resolving a conflict, even when the rebase reports a queued `exec` line next — never hand-invoke the exec command yourself. If already corrupted: recover via `git reset --keep <pre-rebase-sha>` + `git rebase --quit` (when `--abort` is blocked), then redo as a plain rebase followed by one standalone amend pass |
| Re-signing a rewritten branch with `git rebase --exec 'git commit --amend -S --no-edit' origin/main` | Standard exec-based re-sign after a forge commit-provenance gate failed with `invalid_signature` on every rewritten commit | The replay absorbed the picks — the rewritten commits already sat on top of the current base, so git skipped every pick and the exec hook never ran; the command exited instantly, no new objects were created, and `%G?` stayed `N` on the whole stack | Check `%G?` after any exec-based repair; when it does not change, the replay was a no-op — rebuild the stack per-commit with `commit-tree -S` (preserving author, committer, and both dates) and force-push the rebuilt head; every rebuilt commit is a new object and re-triggers the forge check |
| Signing through a privately built/bundled git with `gpg.format=ssh` | Running the `commit-tree` re-sign loop with a bundled git binary whose launcher sets its own library search path | The signed object write died with `OpenSSL version mismatch` — the bundled environment broke the exec'd `ssh-keygen` at load time, even though the same `ssh-keygen -Y sign` succeeded standalone | Use the system git for local object operations (`commit-tree` needs no network); keep the bundled git for network operations only; verify a standalone `ssh-keygen -Y sign` test succeeds before attributing a signing failure to the key or config |
| Treating every `%G?` `U` as benign and accepting a foreign-signed stack | Almost re-delivered PR branches whose older commits an earlier automation identity had signed with its own key under the same author name; `git verify-commit` printed a good signature with `No principal matched` | `%GK` showed a fingerprint that is not the configured `user.signingkey`'s; without discrimination the foreign signature would have been rewritten or shipped unquestioned | Discriminate `%GK` against your key fingerprint first; a mismatch means foreign — get explicit authorship authority, re-sign with `--force-rebase --exec`, verify tree hashes byte-identical, and push with a lease pinned to the verified old head |
| Pushing an empty signed commit to start a gated provenance run after the state label changed | The delivery instructions said to push because a run from before the label would replay the old payload; an empty commit was pushed before the workflow triggers were read | The workflow triggered on `labeled` as well as `synchronize`, so the label flip had already started a run at the same head, and that run passed. The empty commit added history noise and its message was false | Read `on.pull_request_target.types` before any push. A `labeled` trigger starts the run with the new label set; push only when the trigger list lacks `labeled` |

## Results & Parameters

- **Signing key**: GPG key configured in git (`git config user.signingkey`); for SSH signing also `gpg.format=ssh` and `gpg.ssh.program=<ssh-keygen-path>`
- **Base branch**: `origin/main` (or `origin/master` depending on repo)
- **Verification output**: `G` = good signature, `N` = no signature, `U` = unknown validity; for SSH keys without a local allowed-signers record, `U` on a *good* signature is expected and still passes a forge-side verified-signature gate
- **No-op replay diagnostic**: exec-based re-signing that changes no `%G?` entry means git skipped every pick; rebuild via the `commit-tree` loop in the v1.5.0 section
- **Provenance-gate recovery loop**: re-signed push → the forge re-runs per-commit verification → an already-armed auto-merge completes without further action
- **Corruption diagnostic signals**: `git reflog` missing an intervening pick entry between `rebase (start): checkout` and `commit (amend)`; `git diff <merge-base> <bad-commit> --stat` showing more files than `git show <original-sha> --stat`; commit message inherited from an unrelated pre-existing commit rather than the picked change
- **Safe cancel-and-quit sequence** (when `--abort` is policy-blocked): `git reset --keep <pre-rebase-sha>` then `git rebase --quit` — verify clean state with `git status` first
- **Verified case**: Hephaestus PR #2099 (branch `2053-auto-impl`), 1 commit rebased onto ~38 new commits of `origin/main`, one real conflict in `docs/AUTOMATION_LOOP_ARCHITECTURE.md`; recovery + redo verified via `git diff origin/main --stat` matching the original commit's stat exactly, 892/892 tests passing in `tests/unit/automation/pipeline/`, pre-commit hooks green, correct signature and DCO trailer present
- **Gate step order**: the label check runs before the signature check, so a label failure masks any signature state; confirm signatures from the commit API, not from the failed run
- **Label-trigger signature**: a `labeled` trigger starts a passing gated run at the unchanged head; push only when the trigger list omits `labeled`

## Verified On

| Project | Context | Details |
|---------|---------|-------|
| HomericIntelligence/ProjectHephaestus | PR #1171 — show-prompt CLI | 4 commits rebased and signed, pr-policy passes |
| example-org/inference-service | PR #82 — Move inference_service module | Commits signed for pr-policy compliance |
| HomericIntelligence/ProjectHephaestus | PR #2099 — rebase with one real conflict; `--exec` hand-invocation corrupted a commit | verified-local; recovery detail in Failed Attempts |
| HomericIntelligence/Athena | PRs #35/#36 — `gh pr update-branch --rebase` stripped signatures | verified-ci: red on the server-side rewrite, green on the re-signed heads |
| HomericIntelligence/Athena | PR #45 — re-signed rebase prepared, merge queue merged server-side first | verified-ci: MERGED via the queue, no author force-push |
| example-org/backend-service | Verified-signature gate after local rebases rewrote two unsigned stacks | verified-ci: `commit-tree -S` rebuild, provenance green, auto-merge completed — see [notes](git-rebase-signing-ci.notes.md) |
| HomericIntelligence/Athena | PR #361 — one commit signed by a foreign automation key | verified-live: re-signed with `--force-rebase --exec`, trees byte-identical |
| public shared repository | Drive-to-merge: unsigned rebased head, then a label-gated provenance failure | verified-ci: handoff paths in notes; label flip started the passing run at the unchanged signed head |
