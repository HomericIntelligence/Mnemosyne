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
git log --format=%B origin/main..$CUR  > /tmp/new.txt
git log --format=%B origin/main..HEAD > /tmp/old.txt
diff /tmp/old.txt /tmp/new.txt        # empty: messages preserved exactly
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

## Foreign-signer incident reconstruction (v1.7.0 source material)

One verified session on a public shared repository with a merge queue. An
earlier automation lane had produced pull-request commits signed with its own
SSH key under the author's identity. The author-side signing config pointed to
a different key.

Observed diagnostics:

- `git log --format='%h %G? %GK'` reported `U` on the foreign commit and `G`
  on the sibling commits; `%GK` printed a fingerprint that differed from
  `ssh-keygen -lf "$(git config user.signingkey).pub"`.
- `git verify-commit <commit>` printed `Good "git" signature with ED25519 key
  SHA256:…` followed by `No principal matched.` A good object-level signature
  from an unbound key.
- The same foreign fingerprint appeared on a commit in a sibling automation
  branch, so the identity was lane-wide, not a one-off.

Verified repair (explicit authorship authority granted first):

1. `git rebase --force-rebase --exec 'git commit --amend --no-edit -S' <base>`
   on a scratch branch in a separate worktree.
2. Post-rewrite checks: all 3 commits `%G?` `G` with `%GK` equal to the
   configured key; `git rev-parse HEAD^{tree}` equal to the pre-rewrite tip
   tree; per-commit tree hashes identical across the stack; `git diff
   <old-tip> HEAD` empty; `git log --format='%b'` still contained all 3
   `Signed-off-by` trailers; author and committer identity unchanged.
3. `git push --force-with-lease=<branch>:<old-head-oid> origin
   <local>:<branch>` — the push would refuse on any concurrent remote move.
4. Consequence accepted and recorded: review records bound to the old heads
   became void; the pull request later merged through the repository merge
   queue.

## Label-gated provenance session (v1.8.0 source material)

One verified drive-to-merge session on a public shared repository. The PR carried three
successive heads and four provenance runs.

Observed sequence:

1. The reviewed head was unsigned. Two commits reported `%G?` `N` from a rebase that ran
   without signing. The base commits reported `G`.
2. A repair replay produced one signed commit whose `%G?` was `G`, and the forge reported
   `signature.isValid: true` with the configured signer. The tree was unchanged.
3. A run at that head failed at the step `Require the implementation label`. The step's `env`
   showed `LABELS: ["state:implementation-no-go"]` and the step exited 1. The signature step
   never ran.
4. The workflow declared `on.pull_request_target.types: [labeled, synchronize]`. The label
   flip to the state label started a new run at the unchanged head. That run passed with
   `LABELS: ["state:implementation-go"]`.
5. An empty signed commit had already been pushed to start a run. Its run also passed. The
   push was not necessary and its message was false; one PR comment recorded the correction.

Observations that shaped the rules:

- The failure text from a label-gated provenance job looks identical for a missing label and
  for an unsigned commit. Only the failing step separates them.
- The forge's commit API returned `verification: null` for a fresh commit while the GraphQL
  `signature.isValid` field returned `true`. Use the GraphQL field for a fresh head.
- Documented delivery guidance said a push is required after a label change because a run
  replays its own label payload. That is true for `synchronize`-only workflows. It is false
  when the workflow also lists `labeled`.

## Related entries

- [git-commit-signing-failures-and-setup](git-commit-signing-failures-and-setup.md):
  initial key registration and setup failures.
- [git-dco-signoff-distinct-from-gpg-sign](git-dco-signoff-distinct-from-gpg-sign.md):
  trailer vs cryptographic signature — this incident confirmed the gate wanted
  the latter; trailers survived the rebase and did not help.
