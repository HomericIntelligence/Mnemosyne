# Notes: Git Rebase Signing for CI

Companion evidence for [git-rebase-signing-ci](git-rebase-signing-ci.md).
Long commands, measurements, and verification detail live here; every rule the
skill needs for operation lives in the main file. All values come from one
verified repair session on a fast-moving shared repository (dozens of merges
per day) that gates merges on forge-verified per-commit signatures.

## Incident reconstruction (v1.5.0 source material)

An operator-side rebase of two automation-produced PR branches was done with a
privately built git that had no signing configuration in its injected
environment. The rebase replayed the commits and force-pushed new heads:

- every rewritten commit carried no signature;
- the forge's commit-provenance check failed on both PRs with
  `invalid_signature`, per commit;
- all other checks (build, tests, lint) were green or re-running.

Observed details that shaped the rules:

1. **Forge-side verified-signature checks are per commit.** The check enumerates
   the PR's commit range and requires each commit's `verified` flag with a
   `valid` reason. One unsigned commit fails the whole PR. It is not a DCO or
   `Signed-off-by` trailer check — trailers were preserved by the rebase and
   made no difference.
2. **The exec-based repair did nothing.** First repair attempt was the main
   file's Quick Reference: `git rebase --exec 'git commit --amend -S --no-edit'`
   onto the current base, repeated with explicit `--onto` and full signing
   config. The log line "apply all changes, even those already present
   upstream" appeared, the command exited in seconds, and `%G?` stayed `N` on
   all commits. The rewritten branch already had the current base as a direct
   ancestor, so git skipped every pick; skipped picks never fire the exec hook.
3. **The bundled git broke the signer.** Running the fallback `commit-tree`
   loop under the privately built git died with `OpenSSL version mismatch`
   (built-against and loaded libcrypto versions differed). The same
   `/usr/bin/ssh-keygen -Y sign -f <key> -n git` succeeded on the first try
   when invoked from the shell. Root cause: the bundled git's launcher injects
   its own library search path, which the exec'd signer inherits.
4. **The system git is sufficient for object writes.** `commit-tree`, `log`,
   `rev-parse` need no network. The loop was rebuilt with the system git; only
   `fetch` and `push` used the bundled git (needed for its credential helpers
   and CA bundle in that environment).
5. **GPG vs SSH signature appearance on the same repo.** Merge commits created
   by the forge show classic GPG verification (`gpg:` lines from
   `verify-commit`); author commits signed with an SSH key registered on the
   account verify on the forge as well but show `%G?` `U` locally because the
   `allowedSigners` file carries only the public key, not a full trust record.
   `U` did not block the gate.
6. **Armed auto-merge completed on its own.** After the re-signed pushes, the
   queued checks re-ran; both PRs merged within about an hour with zero further
   intervention. A parallel automation log reported the intermediate state as
   `BLOCKED:auto_merge_already_armed` — informational, not a failure.

## Exact command patterns used

Rebuilt stack (run once per branch, in a detached worktree):

```bash
CUR=$(git rev-parse origin/main)
for H in $(git log --format=%H --reverse origin/main..HEAD); do
  TREE=$(git log -1 --format=%T $H)
  export GIT_AUTHOR_NAME=$(git log -1 --format=%an $H) \
         GIT_AUTHOR_EMAIL=$(git log -1 --format=%ae $H) \
         GIT_AUTHOR_DATE=$(git log -1 --format=%ai $H) \
         GIT_COMMITTER_NAME=$(git log -1 --format=%cn $H) \
         GIT_COMMITTER_EMAIL=$(git log -1 --format=%ce $H) \
         GIT_COMMITTER_DATE=$(git log -1 --format=%ci $H)
  NEW=$(git log -1 --format=%B $H | git -c gpg.format=ssh \
        -c user.signingkey=$HOME/.ssh/<registered-key> \
        -c commit.gpgsign=true commit-tree -S $TREE -p $CUR)
  CUR=$NEW
done
git log --format='%G?' origin/main..$CUR | tr '\n' ' '   # expect: U U ... (SSH)
```

Push (bundled git for network), one per branch:

```bash
git push origin $CUR:refs/heads/<branch> --force-with-lease
```

Verification after push:

- forge check suite re-queued automatically; the provenance job reported
  `SUCCESS` on the next run for both PRs;
- `gh pr view <N> --json state,mergedAt,autoMergeRequest` showed
  `autoMerge` armed through the repair and `state=MERGED` afterwards.

## Decision checklist distilled from the session

1. `%G?` unchanged after an exec-based repair → replay was a no-op →
   `commit-tree` loop.
2. Signer dies only when a specific git binary invokes it → environment, not
   key: test `ssh-keygen -Y sign` standalone first.
3. `U` for SSH keys is object-level success; the forge decides validity.
4. Never fix a signature gate via a server-side Update branch (v1.2.0 rule) or
   by disarming auto-merge; both destroy state you want to keep.
5. Sign with the same registered key that produced the branch's previously
   green commits — a different key may still pass content checks but changes
   what the forge verifies against.

## Related entries

- [git-commit-signing-failures-and-setup](git-commit-signing-failures-and-setup.md):
  initial key registration and setup failures.
- [git-dco-signoff-distinct-from-gpg-sign](git-dco-signoff-distinct-from-gpg-sign.md):
  trailer vs cryptographic signature — this incident confirmed the gate wanted
  the latter; trailers survived the rebase and did not help.
