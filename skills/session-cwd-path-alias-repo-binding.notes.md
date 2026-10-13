# Supporting evidence: session CWD, path aliases, and repository binding

Privacy-safe session detail for `session-cwd-path-alias-repo-binding`. Times are UTC, 2026-10-09.
Paths, repositories, and issue identifiers are generalized.

## Session timeline

| Time | Event |
| --- | --- |
| T+0h | A full-repository review session began with its working directory recorded under prefix A (a direct home path). Earlier automation state referenced the same repository under prefix B (a storage-mounted home path). |
| T+1h | Tooling surfaced a remembered absolute path from before an earlier session move. An existence check showed the path no longer existed; the session had since continued in a different directory. |
| T+1h | `realpath` on prefix A and prefix B returned the same resolved path: one checkout, two strings. A raw string comparison would have reported a false repository mismatch. |
| T+2h | The review verified its delegated inventory claims directly, then published one tracking issue and one child issue per selected finding. The repository binding was re-resolved before each hosted write; every write landed in the intended repository. |

## Commands used for re-binding

```bash
# Alias detection: both prefixes returned the same resolved path
realpath "<prefix-a>/<repo>" ; realpath "<prefix-b>/<repo>"

# Identity triple recorded and re-checked before hosted writes
git -C "<repo>" rev-parse --show-toplevel
git -C "<repo>" rev-parse HEAD
git -C "<repo>" remote get-url origin

# Hosted-write targeting confirmed from the target directory
gh repo view --json nameWithOwner
```

## Measured cost and blast radius

- Cost: the re-binding commands complete in seconds and are read-only.
- Blast radius avoided: an entire published artifact set (one tracker plus its child issues) posted to a wrong repository
  would have needed manual deletion and cross-repository reconciliation. A false mismatch would have sent the session
  down a wrong-repository recovery path against the correct repository.
- Companion condition observed in the same session: the harness-facing working directory (`$HOME`-relative) and the
  physical storage path denoted one tree, so tooling that recorded one prefix and tooling that recorded the other
  disagreed only at the string level.
