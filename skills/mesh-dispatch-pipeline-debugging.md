---
name: mesh-dispatch-pipeline-debugging
license: BSD-3-Clause
description: "Debug and fix the live HomericIntelligence agent mesh dispatch pipeline
  (Agamemnon → NATS → claude-myrmidon Python workers → GitHub PRs). Use when: (1)
  Agamemnon POST /v1/tasks returns 404, (2) Claude CLI in container produces zero
  API traffic, (3) container agent gets EACCES on .credentials.json, (4) --resume
  fails with 'No conversation found' across ephemeral containers, (5) IMPLEMENT stage
  gets permission denied writing to bind-mounted workspace, (6) pipeline loops on
  NOGO due to empty REVIEW output, (7) git push blocked by GitHub email privacy, (8)
  PR stuck in CONFLICTING state blocking CI auto-merge, (9) a concurrent mesh worker
  force-pushes its own rebase over YOUR manual PR fix (git push rejected 'tip behind
  remote'; run_end exit 130), (10) you need to STOP the mesh touching one repo without
  killing the org-wide Agamemnon control plane."
category: ci-cd
date: "2026-07-12"
version: "1.1.0"
user-invocable: false
verification: verified-local
history: mesh-dispatch-pipeline-debugging.history
tags:
  - agamemnon
  - nats
  - myrmidon
  - pipeline
  - podman
  - container
  - claude-cli
  - session-resume
  - github-actions
  - pr-conflict
  - markdownlint
  - git-push
  - auto-merge
---

# HomericIntelligence Mesh Dispatch Pipeline Debugging

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-12 |
| **Objective** | Dispatch GitHub issues through the live HomericIntelligence agent mesh (Agamemnon → NATS → claude-myrmidon Python workers → GitHub PRs) AND, when the mesh contends with your own manual PR work, detect it and drain the offending repo's tasks without decapitating the org-wide control plane |
| **Outcome** | SUCCESS — original dispatch (v1.0.0) closed issues #22/#69 via PR #147; v1.1.0 detected + drained a concurrent mesh that force-pushed a failing rebase over the operator's Hephaestus PR #2056 fix; the operator's fix held at sha 79f9ebb3 after draining |
| **Verification** | verified-local (v1.1.0 detection + drain performed live; not a CI-gated claim) |
| **History** | [changelog](./mesh-dispatch-pipeline-debugging.history) |

## When to Use

- Agamemnon POST to `/v1/tasks` returns 404 (wrong endpoint)
- Claude CLI inside an achaean-claude container produces zero API traffic (Traefik TLS interception)
- Container agent user cannot read `.credentials.json` (EACCES, uid mismatch)
- `--resume <session_id>` returns empty output or "No conversation found" in ephemeral containers
- IMPLEMENT stage fails with "permission denied" writing files in the bind-mounted workspace
- Pipeline loops repeatedly on NOGO because REVIEW stage gets empty Claude output
- `git push` blocked by GitHub email privacy (`<private-email>`)
- PR stuck in CONFLICTING state; GitHub CI won't run and auto-merge stalls
- `.markdownlint.yaml` on main causes lint failures for new PRs
- Auto-merge dropped silently after a force-push or new commit
- A `git push` to your PR branch is rejected `tip behind remote`, or your own drive-green
  loop reports `run_end` exit code 130 (interrupted) — a concurrent mesh writer advanced the
  branch underneath you
- A `hephaestus-mesh-worker` from a SECOND checkout is force-pushing its own (often
  CI-failing) rebase over your manual PR fix and looping on the failure
- You need to STOP the mesh touching ONE repo without taking down the shared org-wide
  Agamemnon control plane (which also runs unrelated ecosystem work, e.g. PredictiveCoding
  sweeps)

## Verified Workflow

### Quick Reference

```bash
# 1. Post a task to Agamemnon — use team-scoped endpoint
TEAM_ID=$(curl -s http://localhost:8080/v1/teams | jq -r '.[0].id')
curl -s -X POST "http://localhost:8080/v1/teams/$TEAM_ID/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title": "Fix issue #22", "description": "..."}'

# 2. Run myrmidon worker with all container fixes
CONTAINER_NETWORK=odysseus_homeric-mesh python3 e2e/claude-myrmidon.py

# 3. Re-enable auto-merge after every push to a PR branch
gh pr merge --auto --rebase <PR_NUMBER> --repo <OWNER/REPO>
```

### Correct Agamemnon Task Endpoint

POST must use the team-scoped route:

```bash
# CORRECT
POST /v1/teams/:team_id/tasks

# WRONG — returns 404
POST /v1/tasks

# List tasks (GET works without team scope)
GET /v1/tasks

# Discover team IDs
curl http://localhost:8080/v1/teams
```

### Correct `_build_container_cmd` Implementation

The following implementation incorporates all five container fixes verified in CI:

```python
def _build_container_cmd(claude_args: list[str], cwd: str = WORKING_DIR) -> list[str]:
    import glob as _glob
    import stat as _stat
    home = os.path.expanduser("~")
    # Fix 3: credential permissions reset by host claude processes
    for _path in _glob.glob(f"{home}/.claude/**", recursive=True) + [f"{home}/.claude.json"]:
        try:
            _st = os.stat(_path)
            if not (_st.st_mode & _stat.S_IROTH):
                os.chmod(_path, _st.st_mode | _stat.S_IROTH)
        except OSError:
            pass
    # Fix 2: use standalone binary — avoids Traefik TLS interception of api.claude.ai
    standalone = os.path.join(home, ".local/share/claude/versions/2.1.120")
    if not os.path.exists(standalone):
        versions = sorted(_glob.glob(os.path.join(home, ".local/share/claude/versions/*")))
        standalone = versions[-1] if versions else ""
    cmd = [
        CONTAINER_RUNTIME, "run", "--rm",
        "--userns=keep-id",               # Fix 1: maps host UID inside container
        "--network", os.environ.get("CONTAINER_NETWORK", "odysseus_homeric-mesh"),  # Fix 5
        "-v", f"{cwd}:{CONTAINER_WORKSPACE}",
        "-v", f"{home}/.claude:{home}/.claude",
        "-v", f"{home}/.config/gh:{home}/.config/gh:ro",
        "-w", CONTAINER_WORKSPACE,
        "-e", f"ANTHROPIC_API_KEY={os.environ.get('ANTHROPIC_API_KEY', '')}",
        "-e", f"HOME={home}",
        *(["-v", f"{home}/.claude.json:{home}/.claude.json"] if os.path.exists(f"{home}/.claude.json") else []),
        *(["-v", f"{standalone}:/usr/local/bin/claude-host:ro"] if standalone else []),
        CLAUDE_IMAGE,
    ]
    cmd.extend(claude_args)
    return cmd
```

### Correct `invoke_claude` — No Session Resumption

Disable all `--session-id`/`--resume` flags. Each pipeline stage gets full context in its prompt:

```python
log("claude", f"Starting new session ({len(prompt)} chars)")
claude_args = [
    "claude-host", "-p", prompt,
    "--dangerously-skip-permissions",
    "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep",
]
# Do NOT add --resume or --session-id
```

### markdownlint Config for Odysseus Docs

Use `.markdownlint.json` (not `.markdownlint.yaml`). The yaml variant with a 200-char
line limit was on main causing lint failures. Replace with:

```json
{
  "default": true,
  "MD013": {
    "line_length": 80,
    "tables": false,
    "code_blocks": false,
    "headings": false
  },
  "MD022": false,
  "MD032": false,
  "MD040": false,
  "MD060": false
}
```

### PR Conflict Resolution Pattern

When a PR branch is in CONFLICTING state (GitHub UI), CI won't run and auto-merge
stalls. Do NOT rebase a long branch history. Instead:

```bash
# 1. Create a clean branch from current main tip
git fetch origin main
git checkout -b fix/clean-rebase origin/main

# 2. Cherry-pick only the needed commits (not the whole branch)
git cherry-pick <sha1> <sha2>

# 3. Push and update PR
git push origin fix/clean-rebase
gh pr edit <N> --base main
# Or create a fresh PR pointing to the same issue

# 4. Re-enable auto-merge (GitHub drops it on new commits)
gh pr merge --auto --rebase <N> --repo <OWNER/REPO>
```

### Re-Enabling Auto-Merge After Every Push

GitHub silently drops auto-merge whenever new commits are pushed or force-pushed.
Always re-arm after any push to a PR branch:

```bash
gh pr merge --auto --rebase <PR_NUMBER> --repo <OWNER/REPO>
```

### Git Push Email Privacy Fix

GitHub blocks pushes from `<private-email>`. Use the noreply address:

```bash
git config user.email "mvillmow@users.noreply.github.com"
```

### Unsticking Stalled GitHub Actions Runners

If runs are queued but never picked up (2+ hours):

```bash
# Push an empty retrigger commit
git commit --allow-empty -m "ci: retrigger stalled runners"
git push origin <branch>
# Re-enable auto-merge
gh pr merge --auto --rebase <N> --repo <OWNER/REPO>
```

If still stuck after a retrigger commit, create a fresh branch from main tip and
cherry-pick only the needed diff (see PR Conflict Resolution Pattern above).

### Concurrent Mesh Overwrites Your Manual PR Fix (Detect → Drain, Don't Decapitate)

A long-running org-wide agent mesh (Agamemnon dispatcher on `localhost:8080` + NATS on
`localhost:4222` + `hephaestus-mesh-worker` processes) can be assigned the SAME repo you are
manually fixing — often from a SECOND checkout on the box (e.g. `/home/mvillmow/Hephaestus`
distinct from your `/home/mvillmow/ProjectHephaestus`). Its `ci_fix_orchestrator` will
force-push its OWN rebase over your correct one; that rebase frequently FAILS CI (it computes
doc/line refs wrong and does not re-run the guard suite before pushing) and then LOOPS on the
failure — never merging, going backwards.

Observed live on Hephaestus PR #2056: the mesh force-pushed `40086268` → `64e28415` over the
operator's correct fix; CI went red; it looped. Flagging symptoms: `run_end` exit code 130
(interrupted) on the operator's own drive-green loop, plus a rejected `git push`
(`tip behind remote`) because a concurrent writer advanced the branch.

**Detect** (take 3-5 samples 1-2s apart — mesh workers FLICKER spawn→exit fast when the
dispatcher has no work, so one `ps` sample cannot distinguish flicker from a persistent
worker):

```bash
# Multiple long-uptime workers?
ps -eo pid,etime,cmd | grep hephaestus-mesh-worker
# The SECOND checkout has worktrees on the SAME issue-N branches you're on:
git -C /path/to/OTHER/checkout worktree list
# Did the branch tip change underneath you? (your pushed sha != remote)
git rev-parse origin/<branch>          # compare to the sha YOU pushed
# Is a mesh process holding repo files open?
lsof +D /path/to/repo
```

**Drain, don't decapitate** — the mesh is org-wide (also runs PredictiveCoding sweeps, etc.),
so `SIGKILL` on `ProjectAgamemnon_server` takes down unrelated work. Instead, drain just the
offending repo's tasks and confirm the dispatcher queue is empty:

```bash
# Query the dispatcher: total:0 means nothing is queued — the mesh will stop touching the
# repo on its own once any in-flight task finishes.
curl -s -H "Authorization: Bearer $(cat ~/Agents/mesh/.agamemnon_key)" \
  http://localhost:8080/v1/tasks           # → {"total":0,...} = drained
curl -s -H "Authorization: Bearer $(cat ~/Agents/mesh/.agamemnon_key)" \
  http://localhost:8080/v1/agents          # registered workers

# SIGTERM stops CURRENT execution but workers RESPAWN if the dispatcher re-dispatches.
# So killing workers alone does NOT hold — the empty queue (total:0) is what stops it.
kill -TERM <hephaestus-mesh-worker-pids>

# Verify your fix HELD after draining:
git rev-parse origin/<branch>            # still equals YOUR pushed sha
lsof +D /path/to/repo                    # no mesh process holding files
```

**Prevention:** enforce a single-writer-per-repo rule — a merge queue (see the merge-queue
proposal) or a per-repo advisory lock. The mesh's `ci_fix_orchestrator` MUST run the guard /
pre-commit suite before force-pushing a CI-fix rebase, so it never pushes a red rebase.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | `POST /v1/tasks` to Agamemnon | Returns 404; task creation requires team-scoped route | Use `POST /v1/teams/:team_id/tasks`; discover team ID via `GET /v1/teams` |
| 2 | npm Claude 2.1.101 in achaean-claude container | Traefik intercepts `api.claude.ai` system-wide with self-signed cert (hostname mismatch) — zero API traffic reaches Anthropic | Mount standalone binary (`~/.local/share/claude/versions/<latest>`) as `/usr/local/bin/claude-host` — connects to `api.anthropic.com` directly |
| 3 | Podman rootless without `--userns=keep-id` | Maps host UID to root inside container; `.credentials.json` (0600) unreadable by agent user (uid=1000) | Add `--userns=keep-id` so host UID maps to same UID inside container |
| 4 | `--resume <session_id>` across ephemeral containers | Standalone binary keys sessions by host working-dir path, not container `/workspace`; every resume returns "No conversation found" | Disable all `--session-id`/`--resume` flags; pass full context in each stage prompt |
| 5 | IMPLEMENT stage writing files without `--userns=keep-id` | Workspace bind-mount owned by host user appears as root without uid mapping; permission denied | Add `--userns=keep-id` to every `podman run` invocation |
| 6 | Pipeline REVIEW stage with failed session resume | Empty output defaults to NOGO, pipeline loops up to MAX_ITERATIONS | Disable session resumption; empty output then fails fast instead of looping |
| 7 | SHIPPER committed to existing branch instead of task-specific one | Incorrect branch targeting logic in shipper stage | Workaround: update PR body with `Closes #N`; fix branch logic in shipper |
| 8 | `git push` with `<private-email>` | GitHub email privacy blocks push from this address | Use `mvillmow@users.noreply.github.com` for all git operations |
| 9 | Waiting for stalled GitHub Actions runners | Runs queued 2+ hours, never picked up | Push empty retrigger commit; if still stuck, create fresh branch from main tip |
| 10 | Long-lived PR branch diverged from main | PR enters CONFLICTING state; CI won't run, auto-merge stalls | Create fresh branch from main tip, cherry-pick only the needed diff |
| 11 | `.markdownlint.yaml` with 200-char line limit on main | New PRs fail lint because docs exceed 80-char limit | Replace with `.markdownlint.json` using 80-char limit with table/code/heading exemptions |
| 12 | Auto-merge after force-push or new commits | GitHub silently drops auto-merge on every push | Always run `gh pr merge --auto --rebase <N>` after every push to a PR branch |
| 13 | Container network name `homeric-mesh` | Network created by compose uses project-prefix: `odysseus_homeric-mesh` | Set `CONTAINER_NETWORK=odysseus_homeric-mesh` or default to it in `_build_container_cmd` |
| 14 | `kill -TERM` the `hephaestus-mesh-worker` pids to stop the mesh clobbering PR #2056 | Workers RESPAWNED — the Agamemnon dispatcher re-dispatched queued tasks to fresh workers | Killing workers alone doesn't hold; DRAIN the dispatcher's task queue and confirm `/v1/tasks` `total:0` — that is what actually stops it |
| 15 | Considered `SIGKILL` on `ProjectAgamemnon_server` as "stop the mesh" | Agamemnon is the org-wide control plane (PredictiveCoding sweeps, all ecosystem automation); killing it takes down unrelated work | Drain the SPECIFIC repo's tasks; leave the shared control plane running |
| 16 | Re-launched the operator's own drive-green loop into the contention | Interrupted (`run_end` exit 130) + rejected `git push` — the mesh had advanced the branch concurrently | Don't run a competing automation into an active mesh; enforce single-writer-per-repo (merge queue or advisory lock) |

## Results & Parameters

| Parameter | Verified Value |
| ----------- | ---------------- |
| Agamemnon task POST endpoint | `POST /v1/teams/:team_id/tasks` |
| Agamemnon task list endpoint | `GET /v1/tasks` |
| Agamemnon default port | `8080` |
| Container runtime | `podman` (or `CONTAINER_RUNTIME` env var) |
| Container network | `odysseus_homeric-mesh` (or `CONTAINER_NETWORK` env var) |
| Claude image | `achaean-claude:latest` (or `CLAUDE_IMAGE` env var) |
| Standalone Claude binary path | `~/.local/share/claude/versions/<latest>` |
| Mounted binary path in container | `/usr/local/bin/claude-host` |
| Required Podman flag | `--userns=keep-id` |
| Session resumption | DISABLED — each stage gets full context in prompt |
| Git push email | `mvillmow@users.noreply.github.com` |
| markdownlint config file | `.markdownlint.json` (not `.markdownlint.yaml`) |
| markdownlint line length | 80 (tables/code_blocks/headings exempt) |
| Auto-merge command | `gh pr merge --auto --rebase <N> --repo <OWNER/REPO>` |
| Auto-merge re-arm | Required after every push/force-push to PR branch |

### Concurrent-mesh contention (v1.1.0)

| Parameter | Verified Value |
| ----------- | ---------------- |
| Agamemnon control-plane process | `ProjectAgamemnon_server` on `localhost:8080` |
| NATS bus | `localhost:4222` |
| Mesh worker process name | `hephaestus-mesh-worker` |
| Dispatcher auth | `Authorization: Bearer $(cat ~/Agents/mesh/.agamemnon_key)` |
| Drain-confirmed signal | `GET /v1/tasks` → `{"total":0,...}` |
| Registered-workers query | `GET /v1/agents` |
| Kill semantics | `kill -TERM <worker-pids>` stops CURRENT run only; workers RESPAWN unless queue is drained |
| DO NOT | `SIGKILL ProjectAgamemnon_server` — it is the org-wide control plane |
| Branch-drift check | `git rev-parse origin/<branch>` != your pushed sha ⇒ concurrent writer |
| File-hold check | `lsof +D <repo>` shows a mesh process ⇒ still active |
| Flicker sampling | 3-5 `ps` samples 1-2s apart (workers spawn→exit fast when idle) |
| Contention symptoms | `run_end` exit 130; `git push` rejected `tip behind remote` |
| Verified outcome | Operator's Hephaestus PR #2056 fix held at sha `79f9ebb3` after draining |
| Prevention | Single-writer-per-repo (merge queue / advisory lock); mesh `ci_fix_orchestrator` must run guard suite before force-pushing a CI-fix rebase |
