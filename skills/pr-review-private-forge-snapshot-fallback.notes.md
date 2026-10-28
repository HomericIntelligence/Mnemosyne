# Notes — PR Review Private-Forge Snapshot Fallback

Supporting evidence for `pr-review-private-forge-snapshot-fallback.md`. Source: one
live review session on a private automation monorepo, 2026-10. Identifiers are
generalized. All commands and error strings are public tooling output.

## Diagnostic chain that identified the root cause

1. The target resolver bound the pull request (state `OPEN`, exact base and head
   object identifiers).
2. Strict evidence collection from the local clone failed closed:

   ```text
   The immutable review evidence needs a non-shallow repository. Use a complete source snapshot.
   ```

3. The bounded materialization helper failed with only its generic message:

   ```text
   The helper cannot materialize the immutable pull-request snapshot.
   ```

4. The helper parent drops the bounded child's stderr, so the child error was
   invisible. Disk quota, temporary-directory location, and user-namespace
   creation were each verified as available on the host.
5. A manual replay of the bounded steps (mount, init, fetch) with the normal
   shell environment passed. This ruled out the sandbox itself but, by dropping
   the child's environment, selected the wrong cause at first.
6. The helper wraps every child git call in an isolated environment. The
   relevant values:

   ```text
   GIT_CONFIG_GLOBAL=/dev/null
   GIT_CONFIG_SYSTEM=/dev/null
   GIT_CONFIG_NOSYSTEM=1
   GIT_TERMINAL_PROMPT=0
   GIT_NO_LAZY_FETCH=1
   GIT_NO_REPLACE_OBJECTS=1
   ```

   It also removes every inherited `GIT_*` setting and passes read-only
   arguments such as `--no-replace-objects`.
7. A replay of only the fetch with that exact environment reproduced the true
   failure (public git diagnostic):

   ```text
   fatal: could not read Username for 'https://<host>': terminal prompts disabled
   ```

   With the global and system configuration forced to `/dev/null`, no
   credential helper remains. The forge rejects anonymous reads of private
   repositories. The helper then has no interactive prompt to recover.

## Why the fallback keeps the same trust level

The fallback replaces only the object-acquisition step. It keeps every check
the helper or the strict collector performs:

- complete history: `git rev-parse --is-shallow-repository` must print `false`;
- exact identity: the fetched scratch refs must resolve to the captured base and
  head object identifiers;
- unambiguous ancestry: `git merge-base --all` must print exactly one merge base;
- immutable worktree: a detached checkout at the reviewed head;
- strict binding: the collector runs with every `--expected-*` value from the
  target resolver, so any drift between the forge record and the local objects
  fails collection.

The fallback was used to bind the changed-path manifests in both diff lenses
(author-intent and current-target). The round state then reduced to a terminal
GO, and the delivery helper's exact-head checks passed.

## Session execution facts

| Step | Result |
| --------- | --------- |
| Target resolution | Bound; state `OPEN`; exact base and head captured. |
| Evidence collection from shallow local clone | Failed closed (non-shallow required). |
| Bounded materialization helper | Failed with the generic message; child stderr discarded. |
| Sanitized-environment fetch replay | Reproduced the public authentication diagnostic. |
| Authenticated complete fetch to scratch refs | Passed; shallow check `false`. |
| Invariant verification | Base, head, and single merge base all matched the captured values. |
| Strict collection from snapshot directory | Exit 0; two identical changed-path manifests of five paths. |
| Terminal delivery | Passed; carrier readback byte-identical to the rendered body. |

## Adjacent failure classes that this lesson does not cover

- Missing objects where the forge can still serve them: fetch by object
  identifier, see the prematerialize lesson linked from the main entry.
- Readback mismatches after publication: usually a newline added on output or
  input. Compare parsed fields, not captured string output; see the exact-byte
  publication lesson linked from the main entry.
- A graph query that rejects a field or an argument: the readback query used a
  field argument that the type does not accept and a field name that the type
  does not have. The forge error names the type; remove the argument or use the
  documented field before any retry of the surrounding workflow.
