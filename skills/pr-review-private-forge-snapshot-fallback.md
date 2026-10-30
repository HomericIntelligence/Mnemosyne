---
name: pr-review-private-forge-snapshot-fallback
description: "Bind immutable pull-request review evidence when the bounded snapshot materializer cannot authenticate to a private forge. Use when the helper prints only its generic failure text on a private repository, when the local checkout is shallow, when a complete checkout under the caller's control already holds both reviewed revisions, or when a complete authenticated clone can supply the same verification invariants."
category: tooling
date: 2026-10-27
version: "1.1.0"
user-invocable: false
verification: verified-live
tags:
  - pr-review
  - snapshot
  - private-repository
  - authentication
  - credential-helper
  - sanitized-git-environment
  - fallback
  - evidence-binding
---

# PR Review Private-Forge Snapshot Fallback

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-27 |
| **Objective** | Bind the exact reviewed base and head for a pull request on a private forge when the bounded snapshot materializer cannot fetch, with verification invariants equivalent to the helper. |
| **Outcome** | Successful. Strict evidence collection bound the pull request artifact after the helper failed. The terminal review delivery passed its exact-head checks. A later exchange bound the same invariants from an existing complete checkout: the strict collector took its local path, so no fetch and no credentials were necessary. |

## When to Use

Use this skill when all or some of these conditions apply:

- The snapshot materialization helper fails on a private repository and prints only a generic failure message. Its bounded child discards the git stderr, so the true diagnostic stays hidden.
- The forge rejects anonymous HTTPS reads. The helper sanitizes the git environment of its child process: it sets the global and system configuration to `/dev/null`, removes credential helpers, and disables terminal prompts. On a private repository the fetch then fails with an authentication error.
- The local checkout is shallow, so strict evidence collection fails closed with a non-shallow requirement before it can use local objects.
- A normal host-authenticated fetch to the same repository succeeds outside the sanitized environment.
- A non-shallow checkout under the caller's control already holds the base and the head revisions as objects. Run the strict collector from that checkout: it binds the snapshot from the local object database. This path starts no fetch, so it needs no credentials.
- Do not use this skill when git objects are absent but the forge can serve them. For that failure mode, use [prematerialize-git-objects-before-fail-closed-verification](prematerialize-git-objects-before-fail-closed-verification.md). The two recovery branches are different: this skill repairs authentication; the other repairs an incomplete object store.

## Verified Workflow

### Quick Reference

```bash
# 0. Cheapest branch: a non-shallow checkout under your control that
# already holds both revisions. Run the collector from it and stop.
cd <existing-checkout>
git rev-parse --is-shallow-repository          # must print false
git cat-file -e <base-oid>^{commit}            # must resolve
git cat-file -e <head-oid>^{commit}            # must resolve
python3 <skill-scripts>/collect_evidence.py --expected-* ...   # local bind; no fetch

# 1. Confirm the root cause: replay one fetch with the helper's exact
# sanitized environment. An authentication error names the cause.
env -i PATH="$PATH" GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 \
  GIT_TERMINAL_PROMPT=0 \
  git fetch --no-tags https://<private-forge>/<owner>/<repo>.git \
  +refs/heads/<base-branch>:refs/athena/base
# -> fatal: could not read Username ... terminal prompts disabled

# 2. Get a complete source snapshot under normal host permissions.
git init --quiet source && cd source
git fetch --quiet --no-tags --no-write-fetch-head --no-recurse-submodules \
  https://<private-forge>/<owner>/<repo>.git \
  +refs/heads/<base-branch>:refs/athena/base \
  +refs/pull/<N>/head:refs/athena/pr/<N>/head

# 3. Verify the same invariants the helper enforces.
git rev-parse --is-shallow-repository          # must print false
git rev-parse --verify refs/athena/base^{commit}   # must equal the captured base OID
git rev-parse --verify refs/athena/pr/<N>/head^{commit}  # must equal the captured head OID
git merge-base --all <base-oid> <head-oid>     # exactly one result
git checkout --quiet --detach <head-oid>

# 4. Run strict evidence collection from the snapshot working directory.
python3 <skill-scripts>/collect_evidence.py \
  --expected-base-oid <base-oid> --expected-head-oid <head-oid> \
  --expected-host <host> --expected-repository <owner>/<repo> \
  --expected-pr-number <N> --expected-pr-url <url> \
  <N>
```

### Suggested Approach

1. Do not infer the cause from the generic message. Replay the failing fetch outside the bounded sandbox, first with the normal environment and then with the helper's exact git environment. The sanitized-environment run is the discriminating test. If it fails with an authentication prompt-disabled error, the cause is credential removal, not resources, network, or missing objects.
2. Isolation and quota settings are not the cause when the manual bounded steps pass. Recreate them once to rule them out, then stop repairing them.
3. Prefer the no-fetch branch. When a non-shallow checkout under the caller's control already holds the base and the head revisions as objects — the shallow check prints `false` and both object identifiers resolve — run the strict collector from that checkout with every `--expected-*` binding. The collector binds the snapshot from the local object database and never starts its isolated fetch; this path needs no credentials. Skip steps 4 and 5. Do not use this branch for a clone that another process can move.
4. Acquire the snapshot under normal host permissions only after the identity of the review target is bound: captured base OID, captured head OID, host, repository, number, and URL. Fetch named scratch refs. Do not reuse a pre-existing clone that another process can move.
5. Verify the invariants the helper enforces, in the same order: non-shallow store, exact fetched base commit, exact fetched head commit, exactly one merge base, detached checkout at the reviewed head.
6. Run the strict evidence collector from the snapshot directory with every `--expected-*` binding. The collector refuses any drift between the forge record and the local objects.
7. Keep the snapshot until the review output is delivered. Remove it with the other lane artifacts after the merge. Do not inject objects from the snapshot into a shared checkout.
8. If normal host permissions also cannot read the repository, stop. Report the authentication gap. Do not relax the collector to accept a shallow or partial source.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Re-ran the materialization helper after the disk quota and the namespace capability were verified. | The helper failed again with only its generic message. Resource settings were not the cause. | A generic helper message is not a diagnosis. Reproduce the child failure with the exact child environment before you repair anything. |
| Attempt 2 | Replicated the bounded materialization steps by hand, but with the normal shell environment. | Every step passed, so the failure was first attributed to the sandbox itself. | A replication that drops one significant variable selects a false cause. Replicate the full environment of the child, not only its commands. |
| Attempt 3 | Ran strict evidence collection from the local shallow checkout to avoid a new clone. | The collector failed closed: it requires a non-shallow repository. | The shallow-cancellation check runs before the object reads. The fallback must supply complete history, not only the two commits. |
| Attempt 4 | Re-ran the strict collector from outside any checkout of the target repository, although a complete checkout with both revisions existed on the host. | With no local object database in reach, the collector started its isolated fetch; the sanitized environment removed the credential configuration and the private forge rejected the anonymous read. | Try an existing checkout first: when it is non-shallow and holds both revisions, the collector binds the snapshot from local objects and needs no credentials. Re-materialize only when no such checkout exists. |

## Results & Parameters

### Configuration

The verification invariants the fallback must keep, in check order:

```yaml
invariants:
  shallow_repository: false            # rev-parse --is-shallow-repository
  fetched_base_oid: <captured-base>    # refs/athena/base^{commit}
  fetched_head_oid: <captured-head>    # refs/athena/pr/<N>/head^{commit}
  merge_base_count: 1                  # merge-base --all | exactly one line
  worktree_state: detached-at-head     # checkout --detach <head-oid>
collector_bindings:
  - --expected-base-oid                # from the target resolver
  - --expected-head-oid                # from the target resolver
  - --expected-host                    # canonical forge host
  - --expected-repository              # owner/repository
  - --expected-pr-number               # artifact number
  - --expected-pr-url                  # artifact URL
```

### Expected Output

- The sanitized-environment replay prints the public git error about a user name it cannot read and disabled terminal prompts.
- The fallback fetch completes and the store reports `false` for the shallow check.
- The strict collector exits 0 and records the changed-path manifests and the reviewed-scope digest for the exact base and head.
- On the no-fetch branch the strict collector exits 0 from the existing checkout and performs no network operation.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private automation monorepo (privacy-generalized) | Architecture-first review of a lifecycle fix on a private forge; the bounded materializer could not authenticate; evidence bound through this fallback; a terminal GO was delivered on the exact reviewed head. | See [pr-review-private-forge-snapshot-fallback.notes.md](pr-review-private-forge-snapshot-fallback.notes.md). |
| Private automation monorepo (privacy-generalized) | Evidence binding for a chained review round: the strict collector ran from an existing complete checkout, bound the exact base and head with no fetch, and the reviewer carrier published and readback-verified byte-exact. | See [pr-review-private-forge-snapshot-fallback.notes.md](pr-review-private-forge-snapshot-fallback.notes.md). |

## References

- [prematerialize-git-objects-before-fail-closed-verification](prematerialize-git-objects-before-fail-closed-verification.md) — the missing-object branch of source-verification recovery.
- [forge-exact-byte-comment-publication](forge-exact-byte-comment-publication.md) — byte-exact publication and readback for the records this evidence binds.
- [git fetch documentation](https://git-scm.com/docs/git-fetch)
