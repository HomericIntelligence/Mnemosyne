# Git Helper Ambient-Context Preflight — Notes

Supporting evidence for `git-helper-ambient-context-preflight`. All
identifiers are generalized; the repository and review identities stay out of
the durable record.

## Source session evidence

Two closed failures occurred in one coordination session, each with a generic
surface message and a hidden concrete cause.

1. **Isolated snapshot materialization.** A review-evidence collector invoked
   its snapshot helper and returned only `The helper cannot materialize the
   immutable pull-request snapshot.` The helper suppresses the inner command
   error stream. The collection had already bound an exact base and head of a
   repository that requires authenticated access.
2. **Revision-resolution failure from the wrong tree.** A worktree-preparation
   helper, started while the shell sat in a worktree of another repository,
   answered `fatal: Needed a single revision` for a start commit that existed
   and was current in the intended repository.

## Isolated-read environment

The evidence helpers build the Git read environment as follows:

- every inherited `GIT_*` variable is removed;
- global and system configuration files are replaced with the null device;
- terminal prompts are disabled;
- graft files, replace objects, lazy fetches, and the commit graph are turned
  off;
- each read has a short bounded time budget and the error stream goes to the
  null device.

Consequences recorded by the session:

- An HTTPS read against a repository that requires credentials cannot prompt
  and cannot find a credential helper, so it fails immediately and
  anonymously.
- The helper surfaces only its own generic message. The concrete cause is
  visible only when an operator repeats the read manually with the same
  isolation variables. The repeated read printed
  `fatal: could not read Username for 'https://host': terminal prompts
  disabled`.
- A repository-metadata query confirmed that the repository is private, which
  made authentication the first cause rather than network failure or rate
  limits.

## Local short-circuit mechanics

Before any snapshot materialization, the collector tries to derive strict
changed-path lenses from the current checkout. It probes the expected base
and head with `git cat-file -e <oid>^{commit}`. Only when any probe fails
does the collector materialize a forge-owned snapshot.

Recovery sequence, each step verified in the session:

1. `git fetch <remote>` in the reviewed worktree with the ambient
   configuration. This is read-only and authenticated.
2. `git cat-file -e` for both expected revisions returned success.
3. The collector re-run completed with no snapshot in its output: the
   reviewed-scope digest, the linked-requirements digest, and both changed
   path manifests were derived locally.
4. The same helper had failed moments earlier before the fetch, so the fetch
   alone separated failure from success.

## Wrong-tree revision mechanics

The worktree-preparation helper resolves the primary project from the current
working directory. From inside a feature worktree of repository A, a start
revision of repository B produces the generic revision-resolution error even
while `git rev-parse <revision>` succeeds inside repository B. Re-running the
same helper invocation with repository B as the working directory passed the
dry-run and the creation on the first attempt.

## Decision record

- Preflight order equals ambient-dependency order: working directory, local
  object store, forge auth.
- A generic closed message from these helpers means "inspect the ambient
  context," not "repair the helper."
- Credentials belong in the ambient store through the normal authenticated
  fetch, never inside the isolated read environment.
- The related headless container credential-helper lesson stays separate: its
  trigger is a missing desktop keyring during an image pull, and its repair
  changes the container credential store, neither of which applies to an
  intentionally isolated Git read.

## Verification record

- Manual isolated read: authentication cause printed, first cause recorded.
- Object probes after one read-only fetch: success for the exact base and
  head.
- Collector re-run: success from local objects, no materialized snapshot.
- Helper dry-run from the intended checkout: success; creation: success.
