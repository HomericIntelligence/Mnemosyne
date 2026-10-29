---
name: git-helper-ambient-context-preflight
description: "Run repository-aware helper scripts from the intended checkout and pre-fetch expected objects into its ambient Git store before an isolated-environment collection. Use when a review-evidence, worktree-preparation, or snapshot helper fails closed with a generic message such as 'cannot materialize' or 'Needed a single revision', when the helper hides the inner command output, when the target repository requires authenticated access, or when the helper resolves its primary project from the working directory."
category: tooling
date: 2026-10-26
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags:
  - git
  - helper-scripts
  - isolated-environment
  - evidence-collection
  - snapshot-materialization
  - repository-auth
  - worktree-preparation
  - preflight
---

# Git Helper Ambient-Context Preflight

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Make a repository-aware helper read the intended repository state before it needs forge access at all. |
| **Outcome** | Successful: a generic closed failure became one recorded first cause, and a small ambient preflight let the helper complete from local immutable objects. |

Repository-aware helpers read three kinds of ambient context in a fixed
order: the working directory, the local object store, and the forge. A
failure report often hides the inner command error. Diagnose the ambient
context in the same order before any deeper repair.

## When to Use

- A review-evidence, snapshot, or collection helper fails closed with a
  generic message, and its log does not show the inner command error.
- A worktree-preparation or branch helper reports that a revision is
  unavailable even though the object exists in the intended repository.
- The target repository requires authenticated access, and the helper runs
  Git in an isolated environment.
- The helper documentation says that it resolves a primary project, a base,
  or a root from the current working directory.

## Verified Workflow

### Quick Reference

Run the preflight in this dependency order:

```bash
# 1. Working directory: run the helper from the intended checkout.
cd <primary-checkout>
# 2. Local object store: fetch the expected revisions and probe them.
git fetch <remote>
git cat-file -e <base-oid>^{commit} && git cat-file -e <head-oid>^{commit}
# 3. Forge: only when the helper must authenticate, replicate its isolated
#    read to expose the hidden inner error.
env GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0 \
  git ls-remote https://<host>/<owner>/<repo>.git HEAD
# 4. Re-run the helper only after you record the first cause.
```

### Suggested Approach

Helpers that prove immutable reads run Git with its configuration, credential
helpers, and terminal prompts disabled. This isolation is intentional. On a
repository that allows anonymous access, the helper can still materialize an
isolated snapshot from the forge. On a repository that requires credentials,
that materialization fails closed by design, and the generic error hides the
authentication cause. The designed alternative reads local immutable objects:
the helper probes the expected revisions with `cat-file -e` in the current
checkout and skips materialization when every probe succeeds.

Use this order:

1. Confirm the working directory first. Some preparation helpers resolve the
   primary project from the current working directory. From the wrong
   checkout, a valid start revision of another repository reports a generic
   revision-resolution failure.
2. Fetch the expected base and head into the ambient store of the intended
   checkout, and probe both objects. An authenticated ambient fetch is a
   read-only operation and keeps the helper reads local.
3. Expose a hidden forge cause only with a manual isolated read. A reply such
   as `could not read Username for 'https://host': terminal prompts disabled`
   confirms authentication as the first cause. Report the first cause, then
   return to step 2: the local probes then short-circuit the materialization.
4. Record each first cause before you re-run the helper. Do not weaken the
   isolation. Do not write credentials into it, patch the helper, or keep
   ambient configuration, because the isolation protects revision integrity.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Create a worktree through the helper from a different repository's tree | The shell working directory was a worktree of another repository. | The helper resolves the primary project from the working directory, so it looked for the start revision in the wrong object store and reported `Needed a single revision`. | Check the working directory before the revision. The revision existed all along in the intended repository. |
| Re-run the evidence collector after the generic materialization error | The collector was started again with no environment change. | Its isolated Git environment cannot authenticate to a repository that requires credentials, and the generic message does not show the hidden authentication error. | Reproduce the isolated read manually to prove the first cause. The manual read printed the authentication cause directly. |
| Repair the collector for private repositories | Considered giving the isolated environment credentials or ambient configuration. | This weakens an intentional immutability boundary for a problem that has a designed local path. | Fetch the expected revisions into the ambient store instead. The local probes then make materialization unnecessary. |

## Results & Parameters

### Configuration

```yaml
preflight:
  working_directory: "<primary-checkout>                    # step 1"
  fetch: "git fetch <remote>                                # step 2, read-only"
  probes: ["git cat-file -e <base-oid>^{commit}", "git cat-file -e <head-oid>^{commit}"]
  isolated_forge_reproduction: "env GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0 git ls-remote <url> HEAD  # step 3, diagnostic only"
```

### Expected Output

- Both object probes exit 0, so the helper derives its lenses from local
  immutable objects and reports no materialized snapshot.
- The manual isolated read prints the inner error that the helper hides, so
  the first cause is on record before the next attempt.
- The helper completes on the re-run without any change to its environment
  contract.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A pull-request review coordination session | Evidence collection for one reviewed change on a repository that requires authentication; worktree preparation for a knowledge checkout. | See [notes.md](../skills/git-helper-ambient-context-preflight.notes.md). |

## References

- [Related credential-helper failure in a headless container pull](tooling-docker-headless-build-credential-helper.md) — a
  different trigger (missing desktop keyring during an image pull) and a
  different repair.
- [Git environment variables](https://git-scm.com/book/en/v2/Git-Internals-Environment-Variables)
  — the configuration and prompt variables that an isolated read disables.
