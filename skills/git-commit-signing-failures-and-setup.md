---
name: git-commit-signing-failures-and-setup
description: "Use when required-signature policy blocks a conflict-free PR; GitHub reports unsigned, no_user, unknown_key, or bad signatures; local cryptographic checks disagree with GitHub; noninteractive workers silently fail to sign; a fresh headless host needs SSH signing; email privacy rejects a push; or amend produced a signed sibling that the PR did not adopt. Diagnose with REST, align identity and registered key, re-sign every introduced commit without changing content, and verify the exact remote PR head before merge."
category: tooling
date: 2026-07-13
version: "2.0.0"
user-invocable: false
license: BSD-3-Clause
verification: mixed
history: git-commit-signing-failures-and-setup.history
tags: [git, commit-signing, gpg, ssh-signing, required-signatures, github, identity, headless, force-with-lease, pr-head]
---

# Git Commit Signing: Failures and Setup

## Overview

A green, conflict-free PR can remain blocked because every introduced commit must satisfy GitHub
signature policy. Local `%G?` proves cryptography against the local keyring; GitHub REST proves
registered-key and identity attribution. Treat those as separate gates, and treat email-privacy push
acceptance as a third gate.

Verification is `mixed`: the core GPG/SSH remediation is CI-backed, while the in-place patch-replay
recovery for a PR head pinned to an unsigned sibling was reconstructed and partially exercised but
not completed through a green merge. Case evidence is in
[the notes](./git-commit-signing-failures-and-setup.notes.md); the exact prior skill is in
[history](./git-commit-signing-failures-and-setup.history).

## When to Use

- `mergeStateStatus` is BLOCKED although `mergeable` is MERGEABLE and checks are green.
- REST reports `unsigned`, `no_user`, `unknown_key`, or another non-valid reason.
- `git log --show-signature` is good but GitHub still marks the commit unverified.
- An agent inherits `commit.gpgsign=true` yet emits unsigned commits in a noninteractive shell.
- A fresh remote/headless host needs GitHub-valid SSH signing.
- Git rejects a signed commit for exposing a private email.
- GraphQL says UNSIGNED shortly after push while REST may already say valid.
- A tip-only amend leaves older commits unsigned.
- A signed amend creates a sibling SHA and the open PR remains pinned to the old head.
- Fleet tooling might rewrite a bot or another owners PR.

## Verified Workflow

### Quick Reference

```bash
gh pr view <N> --repo <O>/<R> \
  --json mergeStateStatus,mergeable,statusCheckRollup,headRefOid
gh api repos/<O>/<R>/pulls/<N>/commits \
  --jq '[.[] | {sha:.sha,verified:.commit.verification.verified,reason:.commit.verification.reason}]'

# Local tripwire after the first commit; G is required.
git log -1 --pretty=format:'%G?'

# GitHub is authoritative for hosted policy attribution.
gh api repos/<O>/<R>/commits/<sha> \
  --jq '.commit.verification | {verified,reason,signature,payload}'
```

### 1. Classify the blocker

`mergeable` reports conflicts, not policy. Query `mergeStateStatus`, required checks, rulesets, and
every PR commit through REST. Use REST immediately after push; GraphQL signature fields can lag.

| REST reason | Interpretation | Next action |
| --- | --- | --- |
| `unsigned` | Commit has no signature | Configure/prime signing and rewrite every affected commit |
| `no_user` | Signed identity is not attributable to the GitHub user | Use a verified email or canonical noreply identity and re-sign |
| `unknown_key` | Signing key is not registered for signing | Register the correct GPG/SSH signing key |
| `valid` | Signature policy is not the blocker | Inspect missing contexts, reviews, conversations, and issue-link policy |

Record the base SHA, PR head SHA, branch ref SHA, and commit range before rewriting. Do not mutate a
PR you do not own.

### 2. Align author, committer, and key

For GPG, the author/committer email must be a UID attributable to the registered key and GitHub
account. The canonical private-email-safe identity is
`<numeric-id>+<login>@users.noreply.github.com`; derive both components from `gh api user`. A custom
`+bot` suffix is not equivalent.

Pin the signing subkey when multiple secret keys exist. In a noninteractive shell, export a valid
`GPG_TTY` when available and perform a harmless signing/agent-availability preflight before rewriting
history. Fail immediately if `%G?` is not `G`.

For SSH signing on a headless host:

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_signing_ed25519.pub
git config --global commit.gpgsign true
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
git config --global user.email '<numeric-id>+<login>@users.noreply.github.com'
gh ssh-key add ~/.ssh/id_signing_ed25519.pub --type signing --title '<host>-signing'
```

The allowed-signers row contains the email, key type, and public-key body. Registering the key as an
authentication key is insufficient. Adding a signing key may require the interactive
`admin:ssh_signing_key` scope; do not try to bypass that authorization step.

### 3. Re-sign the complete introduced range

Fetch the base, set the correct identity/key, preserve the old head, then rewrite every introduced
commit rather than only the tip:

```bash
git fetch origin
old_head=$(git rev-parse HEAD)
git rebase origin/main --exec 'git commit --amend --no-edit --reset-author -S'
git diff "$old_head" HEAD                 # must be empty: content unchanged
git log origin/main..HEAD --format='%H %G? %ae'
```

Every row must be `G` and use an attributable email. A failed hook can leave HEAD unchanged; inspect
the command exit and before/after SHAs rather than assuming amend occurred. Push rewritten history
only with `--force-with-lease` after fetching and confirming no unexpected remote owner update.

### 4. Recover a PR-head sibling safely

This pattern remains only `verified-local`. `git commit --amend -S` creates a sibling of the old
commit, not its descendant. A branch ref can move while an open PR remains associated with a stale
or tangled lineage. Close/reopen and update-branch do not sign the unsigned ancestor.

Reconstruct content commits on the correct base:

```bash
base=$(git merge-base origin/main <old-pr-head>)
git format-patch --stdout "$base"..<old-pr-head> > /tmp/pr.patch
git switch <owned-pr-branch>
git rebase origin/main
git am --gpg-sign=<signing-key> /tmp/pr.patch
git log origin/main..HEAD --format='%H %G?'
git push --force-with-lease origin HEAD:<owned-pr-branch>
```

Use a recoverable temporary patch and verify its SHA/content before replay. The equivalent rebase
workflow is acceptable when it produces a clean signed lineage. Confirm GitHub `headRefOid` equals
the remote branch tip and re-query REST verification for every commit. A fresh PR is a last-resort
escape because it abandons reviews and discussion.

### 5. Verify hosted acceptance

After push, poll REST on the exact PR commit SHAs until GitHub reports `verified:true, reason:valid`
or a stable failure. Re-read `headRefOid`; do not verify a signed commit that is not the PR head.
Then inspect required checks and merge state. Local signature, hosted verification, and email privacy
must all pass independently.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Trust `mergeable` | MERGEABLE was read as policy-ready | It excludes required-signature policy | Inspect `mergeStateStatus` and commit verification |
| Trust local GPG | `%G?` was good | GitHub could not attribute the email/key | REST verification is authoritative for hosted policy |
| Sign only the tip | Amended the latest commit | Older introduced commits remained unsigned | Rewrite and verify the whole range |
| Omit `--reset-author` | Re-signed with stale bot identity | `no_user` persisted | Reset to an attributable identity during rewrite |
| Rely on default key | Multiple keys existed | A foreign/unregistered key signed the commit | Pin the registered signing key |
| Trust GraphQL immediately | Saw transient UNSIGNED | Signature state lagged REST | Poll REST by SHA |
| Register SSH key as auth-only | Uploaded without signing type | GitHub had no signing key for verification | Use `--type signing` |
| Re-sign another owners PR | Fleet rewrite included bots | Native signatures and ownership were damaged | Scope to owned PRs only |
| Amend into a sibling | Force-pushed a same-parent signed SHA | The PR still introduced unsigned/tangled lineage | Replay patches on the correct base and verify head identity |
| Merge/update over unsigned history | Added a merge commit | Required signatures checks all introduced ancestors | Replace the lineage; do not cover it with a merge |

## Results & Parameters

| Invariant | Required value |
| --- | --- |
| Local signature | `%G? == G` for every introduced commit |
| Hosted signature | REST `verified == true`, `reason == valid` |
| Identity | Verified email or `<id>+<login>@users.noreply.github.com` |
| SSH key registration | Signing key, not authentication-only |
| Content preservation | `git diff <old-head> HEAD` empty after pure re-sign |
| Rewrite push | Owned branch, fetched remote, `--force-with-lease` |
| PR-head proof | `headRefOid` equals verified remote tip |
| Fleet scope | Author/owner allowlist; never rewrite third-party PRs |

## Verified On

- Core GPG/SSH workflows: CI-backed cases across the repositories indexed in notes.
- Sibling/patch-replay recovery: `verified-local`, not demonstrated through a merged green gate.

## Companions

- [Case notes](./git-commit-signing-failures-and-setup.notes.md)
- [Version history and exact superseded snapshot](./git-commit-signing-failures-and-setup.history)
