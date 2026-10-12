# Notes: interrupted-automation-loop-relaunch-salvage

Supporting evidence from a three-day supervision engagement on a private automation host.
Identifiers are generalized; commands and sequences are verbatim where they are safe.

## Scenario

A per-issue automation loop processed 35 open child items of one epic. Each work
item got an isolated Git worktree on an item-scoped branch below one intake
checkout. A wrapper supervisor ran attempts, detected deaths, and relaunched with
the same intake state. The driver routed agent work as sessions on a shared
agent-service daemon that also served unrelated work on the host.

## Observed failure chain, in order

1. Rate-limit deaths. Three attempts died on an account-level API throttle
   (see the sibling skill `github-shared-token-lockout-rate-limit-diagnosis`):
   instant `API rate limit already exceeded` on every GraphQL call while the
   hourly budget read as mostly unused. Attempts that survived long enough
   between throttles completed useful work (session claims, worktree creation,
   resume detection) before the next burst.

2. Preflight over-approximation. The first supervisor predicate ran plain
   `git status --porcelain` over each intake worktree. Untracked `build/`
   journal directories counted as dirt, so five consecutive attempts
   self-aborted within seconds of launch. The tool's actual acceptance check
   (found by reading the intake module) was:

   ```bash
   git status --porcelain --untracked-files=no
   ```

   Tracked modifications block; untracked `build/` and virtual-environment
   content never blocks; the operator checkout is not part of the check at all.
   Rewriting the predicate to the exact source gate ended the self-aborts: the
   next attempt ran 26 productive minutes before its death cause (another
   throttle burst).

3. Stash-invisibility loss. An early rescue pass had preserved worker output as
   six `git stash` entries across the worker worktrees. On resume, one
   implementer regenerated work that already existed, because the resume logic
   plans from branches and working trees, not stashes. Total at-risk content:
   27 unique file changes that existed only as stash entries. Recovery:

   ```bash
   git -C <worktree> stash list
   git -C <worktree> stash show -p 'stash@{N}' > /archive/<item>.patch   # archive
   git -C <worktree> stash apply --index 'stash@{N}' || \
       git -C <worktree> stash apply 'stash@{N}'
   # stage tracked edits + explicitly named new source files; never add -A
   git -C <worktree> commit -m "salvage: restore in-flight worker output"
   # verify: compare blob ids of committed files against the stash diff blobs
   git -C <worktree> ls-tree -r --long HEAD | awk '{print $3}'
   git -C <worktree> stash drop 'stash@{N}'        # only after verification
   ```

   Result: five salvage commits over five worker branches (21, 2, 1, 2, 1 file
   changes each), blob-verified; archives kept outside the repository.

4. Orphan writers. After loop death, some worker sessions on the shared daemon
   kept writing into worktrees. They could not be killed: the daemon is shared
   infrastructure. Liveness was read from a companion signal pair:

   - newest file mtime inside each worktree; and
   - the session store's `time_updated`-style field per worker session
     (a sqlite journal in this deployment; the general shape is the daemon's
     own durable session table).

   Both idle below a 10-minute floor = safe to salvage. Salvage then used
   commits, which the resumed workers could see on their next run.

5. Supervisor suicide by pattern. Terminating the supervisor with
   `pkill -f '<absolute script path>'` also matched the probing shell's own
   command (the path occurred in the probe's command string). The supervisor
   died — so did the probe. Fix: record the supervisor PID at launch, kill by
   PID, verify with `kill -0 <pid>`.

## Branch publication naming

Local worker branch names carried a per-run nonce suffix. Remote publication
used shorter stable names. The mapping was taken from the tool's source (a
one-line helper), then applied as:

```bash
git push origin <local-branch>:refs/heads/<publication-name>
```

All pushed tips were verified with one remote API call per branch afterward.
Guessing the publication name would have produced silently divergent refs.

## Parameters that mattered

| Parameter | Value | Why |
| --------- | ----- | --- |
| Liveness idle floor | 10 min | Both signals below = treat worker as dead |
| Stale-writer alert | 90 min | A live writer older than this blocks relaunch until an operator looks |
| Attempt quiet floor | 600–1800 s | Spaces attempt starts under throttle pressure; 1800 s chosen after recurrences |
| Salvage staging | `add -u` + explicit new files | Keeps `build/` journals and virtual environments out of commits |
| Stash disposition | archive, then drop after blob verification | Prevents silent double preservation and future confusion |

## Limits

- The session-store liveness source is deployment-specific; substitute the
  daemon's own durable session table on other hosts.
- The quiet floor paces attempt starts, not in-attempt request bursts; a burst
  inside an attempt can still trip the throttle. Request-rate guards inside
  the tool are the prevention layer.
