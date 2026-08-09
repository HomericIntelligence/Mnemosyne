---
name: automation-session-naming-pr-scoped-not-commit-scoped
description: "Keep deterministic agent session IDs scoped to the durable artifact while resolving Claude transcripts across only the registered worktrees of the caller's exact Git checkout. Use when: (1) repo-root and worktree callers share the same repo/issue/agent/model key but silently create duplicate sessions, (2) call sites cannot safely enforce one identical cwd, (3) same-slug repositories must remain isolated, (4) historical same-family transcripts need deterministic resume behavior without migration."
category: architecture
date: 2026-07-20
version: "2.0.0"
user-invocable: false
verification: unverified
history: automation-session-naming-pr-scoped-not-commit-scoped.history
tags:
  - automation
  - claude-session
  - session-resume
  - session-id
  - deterministic-uuid
  - transcript-resolution
  - checkout-family
  - git-worktree
  - porcelain-z
  - cwd-mismatch
  - fail-closed
  - same-slug-collision
  - provider-isolation
---

# Artifact-Stable Session IDs with Checkout-Scoped Transcript Lookup

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-20 |
| **Objective** | Preserve artifact-stable session UUIDs while allowing repo-root and registered-worktree callers in one Git checkout to find the same Claude transcript without exposing transcripts from unrelated same-slug checkouts. |
| **Outcome** | Proposed v2 design: keep the session key unchanged, discover only `git worktree list` roots for the explicit invocation cwd, select existing same-family transcripts deterministically, and fail closed to the exact cwd path. |
| **Verification** | unverified — implementation and CI validation are pending |
| **History** | [changelog](./automation-session-naming-pr-scoped-not-commit-scoped.history) |

## When to Use

- A deterministic Claude session key such as `(repo, issue, agent, model)` is stable, but turns still start fresh because one caller uses the repository root and another uses a linked worktree.
- The create/resume probe derives Claude's JSONL location from `cwd`, so identical UUIDs map to different on-disk project directories.
- Multiple invocation families cannot reliably carry one canonical cwd through every stage, compatibility wrapper, and post-merge fallback.
- Historical duplicate transcripts already exist under two or more registered worktrees and callers must choose one consistently without deleting or migrating user data.
- Two unrelated checkouts have the same repository slug, issue number, role, model, and therefore deterministic UUID; neither checkout may inspect or resume the other's transcript.
- Session lookup must remain safe when Git is unavailable, the supplied cwd is not a repository, repository discovery times out, or ambient Git repository selectors point elsewhere.
- Claude needs checkout-family transcript resolution while Codex, Pi, or another direct-session provider must keep its existing path.

## Verified Workflow

The following legacy invariants were previously verified and remain valid:

1. Scope a deterministic session ID to the durable artifact, not a live trunk commit. Adding a changing SHA to the key silently abandons earlier transcripts.
2. Keep model identity in the key when different models require isolated context.
3. Audit every session-bearing call path. A stable UUID alone does not guarantee resume because Claude's transcript storage path is also cwd-encoded.
4. Do not retry a failed resume as a fresh create. Agent failures must propagate instead of starting a context-loss cascade.

The older same-cwd mitigation worked for individual call paths, but it was not a durable system-wide invariant: a later repo-root helper and worktree pipeline family diverged again. The v2 resolver below replaces “make every caller use the same cwd” as the primary remediation.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the focused regressions and CI confirm it.

### Quick Reference

```python
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def session_jsonl_path(uuid_str: str, cwd: Path) -> Path:
    """Encode Claude's exact cwd-specific transcript path."""
    encoded_cwd = str(cwd.resolve()).replace("/", "-").replace(".", "-")
    return Path.home() / ".claude" / "projects" / encoded_cwd / f"{uuid_str}.jsonl"


_GIT_REPO_ENV_KEYS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
)


def _repo_scoped_git_env() -> dict[str, str]:
    """Remove ambient repository selectors before explicit git -C discovery."""
    env = os.environ.copy()
    for key in _GIT_REPO_ENV_KEYS:
        env.pop(key, None)
    return env


def _registered_worktree_roots(cwd: Path) -> tuple[Path, ...]:
    """Return roots registered to cwd's exact Git repository."""
    resolved_cwd = cwd.resolve()
    roots = {resolved_cwd}
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(resolved_cwd),
                "worktree",
                "list",
                "--porcelain",
                "-z",
            ],
            check=True,
            capture_output=True,
            env=_repo_scoped_git_env(),
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return (resolved_cwd,)

    for field in result.stdout.split("\0"):
        if field.startswith("worktree "):
            roots.add(Path(field.removeprefix("worktree ")).resolve())

    return tuple(sorted(roots, key=str))


def resolve_session_jsonl_path(uuid_str: str, cwd: Path) -> Path:
    """Resolve an existing transcript only inside cwd's checkout family."""
    expected = session_jsonl_path(uuid_str, cwd)
    candidates = {expected}
    candidates.update(
        session_jsonl_path(uuid_str, root)
        for root in _registered_worktree_roots(cwd)
    )
    existing = sorted(
        (candidate for candidate in candidates if candidate.is_file()),
        key=str,
    )
    return existing[0] if existing else expected
```

Wire the resolver only into Claude's pre-invocation create/resume probe:

```python
sid = session_uuid(repo, issue, agent, model)
transcript = resolve_session_jsonl_path(sid, cwd)
create = not transcript.is_file()

mode_args = (
    ["--session-id", sid, "--name", display_name]
    if create
    else ["--resume", sid]
)
```

### Detailed Steps

1. **Keep the artifact-stable key unchanged.** Do not add cwd, worktree path, branch SHA, or trunk SHA to `session_name` / `session_uuid`. Changing the tuple abandons existing transcript IDs and defeats cross-turn reuse.

2. **Retain the exact cwd encoder.** `session_jsonl_path(uuid, cwd)` remains the single representation of Claude's storage convention. First use still creates under the caller's exact cwd path.

3. **Discover the checkout family from the explicit cwd.**
   - Run `git -C <explicit-cwd> worktree list --porcelain -z`.
   - Parse NUL-delimited fields; consume only fields beginning with `worktree `.
   - Resolve, deduplicate, and sort returned roots.
   - Use a short timeout such as five seconds.
   - Scrub ambient repository selectors such as `GIT_DIR`, `GIT_WORK_TREE`, and `GIT_COMMON_DIR` so `git -C` selects the repository instead of inherited process state. Preserve unrelated Git settings such as transport configuration.

4. **Construct candidates only from registered roots.** Map the same UUID through `session_jsonl_path` for the exact cwd and each registered worktree root. Never glob `~/.claude/projects/*` and never search by UUID across all Claude projects.

5. **Choose duplicates deterministically.** Lexicographically sort existing same-family candidate paths and select the first. Repo-root and worktree callers then choose the same historical transcript even if earlier bugs created duplicates. Do not delete, merge, or migrate transcripts.

6. **Fail closed.** If Git is unavailable, cwd is not a repository, discovery fails, or the subprocess times out, return only the exact cwd candidate. This preserves existing first-create behavior and cannot reveal an unrelated checkout.

7. **Centralize the behavior at the Claude boundary.** Replace only the transcript probe used to select `--session-id` versus `--resume`. Do not add session state to pipeline jobs or stage handoffs, and do not infer repository identity from ambient process cwd.

8. **Keep provider boundaries intact.** Codex, Pi, and other direct-session providers should remain outside the Claude JSONL resolver unless their storage contracts independently require it.

9. **Preserve failure semantics.** Once resume/create mode is selected, allow invocation failures to propagate. Do not catch a failed `--resume` and retry with `--session-id`, because that turns transient failures into silent context loss.

### Regression Matrix

| Test | Setup | Required assertion |
| ------- | ------- | ------- |
| Registered family, root-created | Transcript exists under repo root; caller is worktree | Both callers resolve the root transcript |
| Registered family, worktree-created | Transcript exists under worktree; caller is repo root | Both callers resolve the worktree transcript |
| Same-slug unrelated checkout | Foreign checkout has same UUID; local family has none | Resolver returns local exact-cwd path and ignores foreign JSONL |
| Historical duplicates | Two same-family candidates exist | Every caller selects the same lexicographically first path |
| NUL parser | Mock `--porcelain -z` output with multiple `worktree ` records | All roots are parsed and sorted |
| Explicit Git scope | Ambient `GIT_DIR` / `GIT_WORK_TREE` are set | Command uses supplied `git -C` cwd and scrubbed environment |
| Git failure | `git` missing, non-repo cwd, nonzero exit, or timeout | Resolver returns exact cwd-encoded path |
| Real call paths | Repo-root reviewer turn creates; worktree worker turn follows | First argv has `--session-id`; second has `--resume` with the same UUID |
| Provider isolation | Codex/Pi direct-agent paths run | Existing session APIs remain unchanged |
| Resume failure | Existing transcript selected; Claude returns failure | Failure propagates; no create retry occurs |

For the real-path regression, invoke the actual repo-root review helper first and then submit the same key through the pipeline worker with `cwd=<registered-worktree>`. Mock only the external Claude process and worktree discovery. Assert the worker completion succeeds and inspect both argv lists.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ------- | ------- | ------- |
| Commit-scoped UUID | Included the live trunk SHA in the deterministic session tuple | Every trunk update minted a new UUID and abandoned the previous transcript | Key sessions to durable artifact identity, including model when model isolation matters |
| Same-cwd-only remediation | Required every caller sharing a session key to pass one identical cwd | It fixed known paths but recurred when a repo-root helper and worktree pipeline family diverged | Centralize transcript lookup at the Claude boundary; treat registered worktrees as one checkout family |
| Global UUID glob | Searched `~/.claude/projects/*/<uuid>.jsonl` for an existing transcript | Unrelated same-slug checkouts can share the deterministic UUID, exposing or resuming foreign context | Generate candidates only from `git -C <cwd> worktree list` roots |
| Ambient cwd or marker walk | Inferred repository family from process cwd or walked generic ancestor markers | Automation may run from another checkout, and nested worktrees/meta-repos make markers ambiguous | Seed discovery from the explicit invocation cwd and let Git identify registered roots |
| Changed the stable key to include cwd | Added cwd/worktree identity to avoid transcript collisions | Existing transcripts became unreachable and root/worktree turns could no longer share context | Keep artifact identity and storage lookup as separate concerns |
| Migrated or deleted duplicate JSONLs | Tried to canonicalize historical same-family transcripts | Destructive migration risks data loss and introduces races with active Claude sessions | Sort candidates deterministically and leave user data untouched |
| Resume-to-create fallback | Retried a failed `--resume` as `--session-id` | A transient failure silently forked context and caused repeated recreate cascades | Propagate failures after mode selection |

## Results & Parameters

### Stable identity versus storage lookup

```text
session UUID = f(repo slug, issue, agent role, model)
transcript path = g(session UUID, exact cwd)

Artifact identity remains stable.
Storage lookup expands only to registered worktrees of the explicit cwd's Git repository.
```

### Discovery contract

| Parameter | Value |
| ------- | ------- |
| Git command | `git -C <resolved-cwd> worktree list --porcelain -z` |
| Environment | Existing process environment with repository selectors (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_COMMON_DIR`, and object-directory overrides) removed |
| Timeout | 5 seconds |
| Candidate scope | Exact cwd plus roots registered to that Git repository |
| Duplicate selection | Lexicographically smallest existing candidate path |
| Failure fallback | Exact cwd-encoded path |
| Global search | Forbidden |
| Migration/deletion | None |
| Provider scope | Claude only |

### Focused verification commands

These commands are the intended acceptance gates; they have not yet been run for this proposal:

```bash
uv run pytest tests/unit/automation/test_session_cwd_resume.py -q
uv run pytest tests/unit/automation/test_session_naming.py \
  -k "registered_family or unrelated_checkout or registered_worktree or duplicate" -q
uv run pytest tests/unit/automation/test_claude_invoke_session.py -q
uv run pytest \
  tests/unit/automation/test_plan_reviewer.py \
  tests/unit/automation/pipeline/test_worker_pool.py -q
uv run pytest tests/unit/automation/test_agent_stage.py tests/unit/agents/test_runtime.py \
  -k "codex or pi" -q
uv run ruff check <modified-production-and-test-files>
uv run mypy <modified-production-modules>
```

### Rollback boundary

The change is reversible at one call site: restore Claude's probe from `resolve_session_jsonl_path(sid, cwd)` to `session_jsonl_path(sid, cwd)`. No transcript migration exists to undo, and the deterministic UUID remains unchanged.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | PR #845 | Verified in CI: removed live trunk SHA from session identity so artifact sessions survive main-branch movement |
| ProjectHephaestus | PR #1100 | Verified locally/pre-commit: exposed cwd-encoded transcript lookup and enforced one cwd in a two-turn path |
| ProjectHephaestus | Issue #2284 revised implementation plan, 2026-07-20 | Unverified proposal: checkout-family resolver, same-slug isolation regression, deterministic duplicate selection, real PlanReviewer-to-WorkerPool resume path, and Claude-only provider boundary |
