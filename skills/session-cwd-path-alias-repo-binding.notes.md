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

## Companion evidence: harness context reset (2026-11)

A second case confirmed the same rule from a different direction. Times are UTC, generalized.

### Timeline

| Time | Event |
| --- | --- |
| T+0h | A milestone-sweep session finished work in a hand-built worktree and pushed its branch. The pending merge still ran on the forge. |
| T+1h | The harness compressed the conversation and restarted. An external cleanup removed the worktree during the same window. |
| T+1h | The first shell call of the new turn began with `cd <worktree>` followed by a relative-path file write. The `cd` failed with `No such file or directory`. The shell kept running, so the write created one stray file under the fallback working directory, which was the knowledge-checkout root. |
| T+1h | A `pwd` probe reported the fallback directory, not the recorded worktree. `git status` in the fallback repository listed exactly one untracked path. |
| T+1h | The session removed the stray file and re-verified: the knowledge checkout returned `git status --porcelain` empty, and the pushed branch still carried the intended feature commit on the forge. |

### Commands used for detection and remediation

```bash
# Detection: show the directory the shell is actually in
pwd

# Scope the damage in the fallback repository
git status --porcelain

# Remove only the stray path, then prove the tree is clean
rm "<stray-file>"
git status --porcelain
```

### Measurement and blast radius

- Cost: `pwd`, `git status`, and one `rm` — seconds, all reversible except the verified stray file remove.
- Blast radius avoided: the stray file looked like a legitimate title match for a feature in flight; if it had been
  committed and pushed, the knowledge repository would have needed a reversion plus a provenance audit against the
  milestone-sweep branch on the forge.
- Companion condition observed in the same session: the condense step and the external worktree cleanup both happened
  between turns, outside the agent's control. Neither produced a warning in the next turn. The only detectable signal
  was the failed leading `cd`, which did not stop the remaining lines of the same shell call.
