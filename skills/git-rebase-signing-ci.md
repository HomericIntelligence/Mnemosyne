---
name: git-rebase-signing-ci
license: BSD-3-Clause
description: "Diagnose signature failures, resume a justified rebase after conflicts, re-sign rewritten commits when the rebase replay is a silent no-op, rebuild a whole stack parent-first so already-valid commits are not orphaned onto old parents, scan many open pull requests without a shallow-clone range error, compare signing repair with current branch-update or merge-queue requirements, and tell a label short-circuit apart from a signature failure when a provenance gate fails inside review-to-merge drive work."
category: tooling
date: 2026-07-17
version: "1.10.0"
user-invocable: false
verification: verified-ci
tags: [git, signing, rebase, ci, gpg, exec, conflict-resolution, update-branch, force-with-lease, stale-info, branch-protection, up-to-date, stacked-pr, squash-merge, merge-queue, ssh-signing, commit-tree, provenance-gate, label-gate, batch-resign, shallow-clone, parent-first, ld-library-path, signer-env-scrub]
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
- Many open pull requests fail a forge-verified per-commit signature gate, and you must re-sign
  them as a batch without changing content
- A `commit-tree` rebuild left some commits unsatisfied after you skipped them because `%G?` was
  already `G` — their parents changed but the commits still point at the old parents
- A range scan reports far more commits than a branch actually introduces, or the base is not
  detected as an ancestor, because the checkout is shallow or partial
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

> **Critical: never hand-invoke the queued `--exec` command on a conflict pause.** The
> conflicted commit is not created yet; the rebase is still mid-`pick`. A manual `git commit
> --amend` then amends the "onto" checkout (the base tip) instead of finalizing the pick.
> Always run `git rebase --continue`, which finalizes the pick *before* it fires the exec
> hook. This applies to any `--exec` script, such as `--exec "pytest"`.

### Detailed Steps

1. **Identify unsigned commits**: look for `N` (no signature) or `U` (unknown validity) in
   the log above.
2. **Rebase with signing only when permitted**, as stated under Current applicability.
3. **If it stops on a conflict**: resolve per hunk, `git add <file>`, then `git rebase
   --continue` — never `git commit --amend` by hand (see the warning above). `--continue`
   finalizes the pick, then fires the queued `--exec` command against it.
4. **Verify** that every commit shows `G`, then push with `--force-with-lease`.

### Recovery if you already hand-invoked the exec command mid-conflict

1. Verify the working tree matches your target state: `git status` and
   `git diff <target-sha> HEAD`.
2. If `git rebase --abort` is blocked by policy and deleting `.git/**/rebase-merge` is also
   blocked, use `git reset --keep <pre-rebase-sha>` then `git rebase --quit`. `--quit` clears
   only the rebase bookkeeping and does not touch HEAD or the working tree.
3. Redo as two separate passes instead of `--exec`: (a) plain `git rebase origin/main`,
   resolving per hunk — check `git ls-files --stage <file>` because stages `:2:` and `:3:`
   are inverted in a rebase — then `git rebase --continue` to completion; (b) run
   `git commit --amend --no-edit -s -S` once over the final HEAD for signing and DCO.

See also `pr-rebase-conflict-resolution-patterns.md` for the general `--exec` signing pattern
on conflict-heavy chains; the warning applies whenever a pick conflicts.

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
2. **Reliable fallback: rebuild the exact stack with `commit-tree`.** Replay each commit into
   a new signed object, preserving author, committer, both dates, tree, and message. The loop
   is in [notes](git-rebase-signing-ci.notes.md). Verify every `%G?` entry and diff the old and
   new message lists, then `git push --force-with-lease` the rebuilt head. Every rebuilt commit
   is a new object, so the forge check re-runs from scratch. Build in a detached worktree.
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

`--force-rebase` replays every pick even when trees already match, so the exec hook cannot be
swallowed by the v1.5.0 skipped-pick no-op. Then verify that every commit is `%G?` `G` with
`%GK` equal to your fingerprint, that tree hashes are unchanged, and that `git diff <old-head>
HEAD` is empty with every `Signed-off-by` trailer intact. Push with the lease pinned to the
verified old head:

```bash
git push --force-with-lease=<branch>:<verified-old-head-oid> origin <local>:<branch>
```

Every review record or chain carrier bound to an old head becomes void. Re-run head-bound
review and delivery against the new head.

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

### Parent-first batch re-sign without orphaning valid commits (v1.9.0)

A batch re-sign of many open pull requests repeats the v1.5.0 `commit-tree` rebuild per
branch.

1. **Rebuild parent-first; never skip a commit only because `%G?` is `G`.** A rewrite changes
   the ID of every rebuilt commit, so a commit kept unchanged still points at old parents and
   no longer descends from the new stack. Rebuild a commit when its signature fails **or** any
   parent has a rewrite target, resolving parents through a rewrite map to a fixpoint. Then
   require that no commit between base and tip has a target left. The loop is in
   [notes](git-rebase-signing-ci.notes.md).
2. **An unchanged tip is not proof of no change.** Skipping the already-`G` commits above an
   unsigned run returned the same tip, and tip-tree equality hid the fault. Validate the whole
   range by subject and count, and require zero unverified commits in it.
3. **Verify the range in a complete checkout.** A shallow or partial clone makes
   `git merge-base` return a grafted boundary, so `git rev-list --count <base>..<tip>` counts
   all history. Check `git rev-parse --is-shallow-repository` and fetch full history first.
   See [ambient-partial-clone-lazy-fetch-read-hazard](ambient-partial-clone-lazy-fetch-read-hazard.md).
4. **Expect the target set to move.** Re-read each remote tip immediately before its push and
   pin the lease to it. A `stale info` rejection or a vanished ref means the lease worked:
   re-scan and skip that branch. Never fall back to an unconditional force push.
5. **Prove preservation per branch**: equal tip tree, identical subjects, count, author,
   committer, dates, and message, and zero unverified commits in the range and in the forge API.

### Signer-boundary environment scrub when the bundled git must stay (v1.10.0)

The v1.5.0 signer-exec trap rule says to drive object writes with the **system git** when a
privately built git breaks the exec'd ssh helper. That remediation needs a usable system git:
SSH signing support starts at git 2.34, and some hosts lock tooling to the bundled binary.
When the system git is absent, too old, or must not run, keep the bundled git and scrub the
environment at the signer boundary instead.

1. **Diagnose the injected environment before choosing a remediation.** Point
   `gpg.ssh.program` at a dumpenv shim for one probe commit; the shim shows exactly what the
   launcher added (observed: `LD_LIBRARY_PATH` set to the bundled install's own library
   directory, which made the system `ssh-keygen` load a mismatched OpenSSL at start-up):

   ```sh
   printf '#!/bin/sh\nenv > "$HOME/signer-env.txt"\nexit 1\n' > dumpenv.sh && chmod +x dumpenv.sh
   git -c gpg.ssh.program="$PWD/dumpenv.sh" commit -S --allow-empty -m probe 2>&1 | tail -2
   grep '^LD_LIBRARY_PATH=' "$HOME/signer-env.txt"
   ```

2. **Sign with the same bundled git through an env-scrubbing wrapper.** The wrapper clears the
   injected search path for the signer helper only:

   ```sh
   printf '#!/bin/sh\nexec env -u LD_LIBRARY_PATH /usr/bin/ssh-keygen "$@"\n' > ssh-keygen-clean.sh
   chmod +x ssh-keygen-clean.sh
   git -c gpg.ssh.program="$PWD/ssh-keygen-clean.sh" commit -S -s -m "<subject>"
   ```

3. `-c` scopes the signer override to one invocation, so no persistent config changes. Run the
   standalone `ssh-keygen -Y sign` test first (v1.5.0 trap, rule 3): when that test fails, the
   key or config is the problem and no environment scrub will help. Verified on a host where
   the bundled launcher set `LD_LIBRARY_PATH` before every child process: the plain commit died
   with `fatal: failed to write commit object` after `OpenSSL version mismatch`, and the
   scrubbed wrapper produced a valid SSH signature object with the same git and key.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| `git commit --amend -S` per commit | Manual signing of each commit | Tedious and error-prone with multiple commits | Use `--exec` flag to sign all commits in one rebase |
| `git push --force` | Force push without lease check | Could overwrite remote changes from other collaborators | Use `--force-with-lease` for safety |
| `gh pr update-branch --rebase` to satisfy a strict up-to-date branch-protection rule | Server-side rebase to bring two green PRs current with main | GitHub re-created every commit unsigned; the previously-green signed-commits `pr-policy` gate failed on both PRs with `commit signature is missing or invalid` | Never update a signed-commits PR server-side; do a local `git -c commit.gpgsign=true rebase origin/main` and force-push with lease |
| `git push --force-with-lease` immediately after a server-side branch update | Pushing the locally re-signed rebase over the server-side rewrite | Rejected with `stale info` — the local remote-tracking ref predated the server-side rewrite, so the lease check failed | Fetch the branch first, verify the remote head is the expected rewrite, then push; the rejection is the lease working as designed |
| Re-sign-rebase cycle on a merge-queue repo | Rebased, re-signed, and waited on a force-push for a green PR | The queue merged the PR server-side while the re-signed branch waited; the cycle was moot | Check `gh pr view <N> --json state,mergeStateStatus` first; a queueable PR needs no re-sign cycle |
| Waited for armed auto-merge on a strict repo with no queue | Waited hours on a reviewed, green head | Each base move made the head stale before checks finished | Auto-merge never fires on a stale head; clear real blockers, then merge the exact head when state reads CLEAN |
| Hand-invoking the queued `--exec` command instead of `git rebase --continue` | Replicated the exec command after resolving a conflict | The pick was not finalized, so `git commit --amend` corrupted the "onto" checkout. `git reflog` showed `rebase (start): checkout` then `commit (amend)` with no intervening pick | Always run `git rebase --continue`; if corrupted, `git reset --keep <pre-rebase-sha>` then `git rebase --quit` |
| Re-signing a rewritten branch with `git rebase --exec 'git commit --amend -S --no-edit' origin/main` | Standard exec-based re-sign after a forge commit-provenance gate failed with `invalid_signature` on every rewritten commit | The replay absorbed the picks — the rewritten commits already sat on top of the current base, so git skipped every pick and the exec hook never ran; the command exited instantly, no new objects were created, and `%G?` stayed `N` on the whole stack | Check `%G?` after any exec-based repair; when it does not change, the replay was a no-op — rebuild the stack per-commit with `commit-tree -S` (preserving author, committer, and both dates) and force-push the rebuilt head; every rebuilt commit is a new object and re-triggers the forge check |
| Signing through a privately built/bundled git with `gpg.format=ssh` | Running the `commit-tree` re-sign loop with a bundled git binary whose launcher sets its own library search path | The signed object write died with `OpenSSL version mismatch` — the bundled environment broke the exec'd `ssh-keygen` at load time, even though the same `ssh-keygen -Y sign` succeeded standalone | Use the system git for local object operations (`commit-tree` needs no network); keep the bundled git for network operations only; verify a standalone `ssh-keygen -Y sign` test succeeds before attributing a signing failure to the key or config |
| One-shot signed commit through a bundled git when the system git is not usable | `git commit -S -s` with `gpg.format=ssh` on a host whose git launcher injects its library path into every child process | The child `ssh-keygen` aborted with `OpenSSL version mismatch. Built against 30000020, you have 30500070` and `fatal: failed to write commit object` | The fault is the injected library search path, not the key or config; when the system git is absent, too old (< 2.34 for SSH signing), or locked away, pin `gpg.ssh.program` per invocation to an env-scrubbing wrapper (`env -u LD_LIBRARY_PATH`) instead of switching git binaries |
| Treating every `%G?` `U` as benign and accepting a foreign-signed stack | Almost re-delivered PR branches whose older commits an earlier automation identity had signed with its own key under the same author name; `git verify-commit` printed a good signature with `No principal matched` | `%GK` showed a fingerprint that is not the configured `user.signingkey`'s; without discrimination the foreign signature would have been rewritten or shipped unquestioned | Discriminate `%GK` against your key fingerprint first; a mismatch means foreign — get explicit authorship authority, re-sign with `--force-rebase --exec`, verify tree hashes byte-identical, and push with a lease pinned to the verified old head |
| Pushing an empty signed commit to start a gated provenance run after the state label changed | The delivery instructions said to push because a run from before the label would replay the old payload; an empty commit was pushed before the workflow triggers were read | The workflow triggered on `labeled` as well as `synchronize`, so the label flip had already started a run at the same head, and that run passed. The empty commit added history noise and its message was false | Read `on.pull_request_target.types` before any push. A `labeled` trigger starts the run with the new label set; push only when the trigger list lacks `labeled` |
| Batch rebuild that skipped already-`G` commits | Rebuilt only the failing commits | Already-valid commits above the unsigned run kept old parents; the unchanged tip passed the tree check | Rebuild when a parent has a target; validate the whole range |
| Sizing a range with `merge-base` in a shallow clone | Counted `<base>..<tip>` | A grafted boundary returned all history | Check `--is-shallow-repository`; fetch full history first |

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
- **Batch re-sign invariant**: no commit between base and tip keeps a rewrite target, and every commit in the new range verifies

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
| a shared repository with a forge-verified per-commit signature gate | Batch re-sign of many open pull requests with the parent-first `commit-tree` rebuild | verified-live: ten pull requests pushed, forge API reported zero unverified commits on each; detail in [notes](git-rebase-signing-ci.notes.md) |
