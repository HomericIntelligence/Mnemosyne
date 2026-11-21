# Notes: git-bundle-refusal-partial-clone

Session evidence for the main skill. All repository, organization, host, path,
commit, and issue identifiers are generalized.

## Source session (2026-11-20)

A cleanup session removed stale git worktrees from a large working repository.
Two detached-HEAD worktrees held a 41-commit series (the second tip contained
the first as a strict subset) that existed on no remote branch. The approved
disposition was: archive, tag, then remove the worktrees.

## Environment facts observed

- `remote.origin.promisor = true`, `remote.origin.partialclonefilter = blob:none`
  (partial clone).
- git 2.56.0 (packaged build) and system git 2.34.1 both present; both refused.
- Not a shallow clone; no replace refs; `git cat-file -t` resolved the tips.
- A local integration branch contained both tips (garbage-collection safety).

## What failed

Four `git bundle create` variants, all with the identical error
`fatal: Refusing to create empty bundle`:

1. `git bundle create <file> <tip> --not <base>`
2. `git bundle create <file> <base>..<tip>`
3. Same range under system git 2.34.1
4. `git bundle create <file> --filter=blob:none <base>..<tip>`

## Diagnostics that mattered

- `git rev-list --count <tip> --not <base>` returned 40 (and 41 for the second
  tip): the tips were genuinely local-only. This directly contradicted the
  empty-bundle error and proved the error is not reachability evidence in a
  partial clone.
- `git merge-base <tip> <base>` identified the archive start point.
- `git rev-parse --is-shallow-repository` returned false and `git replace -l`
  returned nothing, ruling out the usual history-truncation suspects.

## What worked

- `git format-patch <base>..<tip> -o <archive-dir>/` produced 41 patch files,
  243 KB total. (`format-patch` had already run successfully earlier in the
  same repository during a reuse analysis, so it was a proven mechanism.)
- Lightweight tags `archive/<date>/<worktree-name>` at both tips, created with
  explicit non-interactive config, resolved to the correct tips.
- A README recorded the merge base, the four failed bundle attempts, the
  restore command (`git am 00xx-*.patch`), and the bundle limitation.
- Both worktrees were verified clean and process-free, then removed with
  `git worktree remove` and `git worktree prune`; roughly 70 MB reclaimed.

## Traps encountered

- The empty-bundle error was first misread as "the tip is already on the
  remote," which delayed the task and contradicted later verification. In a
  partial clone, treat the empty-bundle error as a tool failure, not evidence.
- Annotated tag creation opened an interactive editor inside the automation
  session and hung for roughly 45 minutes before being killed. Lightweight
  tags avoid the editor entirely.
