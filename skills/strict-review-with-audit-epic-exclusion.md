---
name: strict-review-with-audit-epic-exclusion
description: "Strict architectural review of a multi-phase pipeline that already has a tracked audit epic. Builds an exclusion list from open issues + parent epic FIRST, then dispatches parallel Explore sub-agents sliced by phase (not by file), then spot-verifies every concrete claim before writing the plan. Use when: (1) reviewing code that has an existing audit epic with N findings already filed, (2) reviewing a multi-phase pipeline where phases are natural agent boundaries, (3) running myrmidon-swarm fan-out for code review and need to filter noise from already-tracked findings, (4) producing a strict review document where the deliverable is a plan file (not ExitPlanMode), (5) implementing 15+ findings in one PR with grouped commits."
category: architecture
date: 2026-05-09
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [strict-review, audit-epic, exclusion-list, parallel-explore, spot-verification, defence-in-depth, pipeline-review, myrmidon-swarm]
---

# Strict Review with Audit-Epic Exclusion + Parallel Fan-Out

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-09 |
| **Objective** | Run a strict architectural review of a 6-phase automation pipeline that already had a tracked audit epic (#310, 26 findings), without re-flagging anything already tracked. Surface ONLY net-new findings with file:line citations. |
| **Outcome** | Successful — 21 net-new findings (6 MAJOR / 10 MINOR / 5 NITPICK) surfaced, ~26 audit-epic findings filtered out, plan file shipped, then implemented as one PR (23 files, +665 / -1377, 1 commit). PR #367 in ProjectHephaestus. |
| **Verification** | verified-local (ruff/mypy/2042 pytests passed locally; verified-ci pending PR #367 merge) |

## When to Use

- A repo has an open **audit epic** with N findings already filed and the user asks for a "strict review" of the same code area. Without filtering, ~70% of new findings duplicate the epic.
- The code under review is a **multi-phase pipeline** where each phase has clear inputs/outputs and 1-3 owning files. Phases are natural agent boundaries.
- You have access to `myrmidon-swarm` / Explore sub-agents and want **parallel fan-out** to be quality-additive rather than just speed-additive.
- The user phrasing is "do a strict review", "ignore items already tracked", "use the swarm to analyze in parallel", "give me an architectural description AND a strict review".
- The deliverable is a **plan/review document**, not an implementation. (If the user later says "implement it", group everything into one branch with one commit.)

## Verified Workflow

### Quick Reference

```bash
# Step 1 — Build the audit-epic exclusion list (MUST be first, in parallel with code reading)
gh issue list --state open --json number,title,labels,body --limit 200 \
  --repo <owner>/<repo> > /tmp/open_issues.json
gh issue view <epic-number> --repo <owner>/<repo> --json title,body > /tmp/parent_epic.json
# Synthesise: "categories the strict review should AVOID re-flagging"

# Step 2 — Dispatch parallel Explore agents sliced by PHASE (one message, multiple Agent calls)
#   Agent A: phases 1-2 (planner + plan_reviewer)
#   Agent B: phases 3-4 (implementer)
#   Agent C: phases 5-6 (pr_reviewer + address_review + ci_driver)
#   Agent D: open-issues + parent-epic cataloguer (read-only, builds exclusion list)
# Each agent gets: file paths, scope, "read-only", "cite file:line for every smell".

# Step 3 — Spot-verify EVERY concrete claim before writing the plan
grep -n '<symbol>' <claimed-file>     # 1-line confirm
# Read 3-5 lines of context around the cited line — never trust agent claims blindly

# Step 4 — Categorise with the project's existing severity ladder
#   MAJOR (M1..MN) / MINOR (m1..mN) / NITPICK (N1..NN)

# Step 5 — Write plan as deliverable. Do NOT call ExitPlanMode for a review document.

# Step 6 (optional) — If user says "implement the plan": one branch, one commit, grouped bullets
git checkout -b fix/<area>-strict-review-batch
# ... apply all 21 fixes ...
pixi run ruff check . && pixi run ruff format --check . && pixi run mypy && pixi run pytest tests/unit
git commit -m "fix(<area>): address strict-review findings (M1-M6, m1-m10, N1-N5)"
```

### Detailed Steps

1. **Pull the audit-epic exclusion list as a SEPARATE first-class step.** Do not start reading code first.
   - `gh issue list --state open --limit 200 --json number,title,labels,body` for the whole repo.
   - `gh issue view <parent-epic> --json title,body` for the audit epic itself (the body usually contains the full structured finding catalogue).
   - Synthesise into one prose paragraph: *"The following CATEGORIES are tracked: type hints, docstrings, hardcoded subprocess timeouts, retry/backoff missing, structured logging, single-source version, etc. Do not re-flag these UNLESS the new occurrence is in a code path the epic did not cover."*
   - Pass this paragraph as a verbatim section of every Explore agent's brief.

2. **Slice by phase, not by file.** A 6-phase pipeline → 3 Explore agents (≈2 phases each) plus 1 issues-cataloguer agent. Each agent owns:
   - The 1-3 files that implement its phase.
   - The integration points (caller-side, CLI wiring).
   - A self-contained brief: file paths, exclusion paragraph, severity ladder, *"read-only, cite file:line for every smell, return MAJOR/MINOR/NITPICK list"*.
   - All four agents dispatched **in one message, in parallel** (single Agent tool call per agent within one assistant turn).

3. **Spot-verify every concrete claim before writing the plan.** Sub-agents will fabricate or invert findings. Cheap verification:
   - `grep -n '<symbol>' <claimed-file>` — confirms existence and line.
   - `Read` 3-5 lines around the cited line — confirms direction (the bug isn't the OPPOSITE of what was claimed).
   - For "X calls Y in dry-run mode" claims, trace the caller too — the bug may already be gated upstream (becomes a defence-in-depth finding, not a real bug).
   - For "X is dead code" claims, grep for `from <module> import X` in `__init__.py` files — many "dead" symbols are publicly re-exported.
   - Budget: ~2-5 verifications per agent claim, ~30s each. Total ~10-15 min for 20-30 claims. Saves shipping a fabricated-finding plan.

4. **Categorise with the project's existing severity ladder.** If the audit epic uses M1.../m1.../N1..., reuse that exact convention. Same labels = same triage workflow = easier merge into the existing roadmap.

5. **Plan file is the deliverable for research/review tasks.** Write `BRANCH_PLAN.md` (or `STRICT_REVIEW.md`) as the artifact. Do NOT call `ExitPlanMode` after a review/research document — `ExitPlanMode` is for **implementation plans only**, signalling "approve this and I'll code it". A strict-review deliverable is a triage document.

6. **One-commit-per-finding intent, but ONE PR with grouped commits when the user says "implement".** If the user reads the plan and says "implement everything", the cheapest reviewable artifact is a single branch, single commit (or one commit per severity band), with the commit message bulleting findings by ID. Defence-in-depth findings (latent bugs not currently reachable) land naturally in this one-shot PR because they're not user-visible behaviour changes.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trust sub-agent claim "follow_up.py creates real issues during dry-run" | Spot-checked the implementer caller; the entire post-impl block is short-circuited when `dry_run=True`. The function itself doesn't gate but isn't reachable today. | False bug, but the latent unsafety is real. | Always trace the CALLER too. Reframe as defence-in-depth (became finding m9), not "real bug". Saves a fabricated-finding plan. |
| Trust sub-agent claim "reviewer.py is dead code" | `grep -n PRReviewer hephaestus/automation/__init__.py` showed `from .reviewer import PRReviewer` — publicly re-exported, reachable via package API. | Partially true (no internal callers) but symbol is in the public surface. | "Dead code" claims must check `__init__.py` re-exports before plan-writing. Became M1 (a real, reachable bug) instead. |
| `pixi run` to verify a Python import claim | Pixi backgrounded itself; tried sleep-loop retries; harness blocked the long sleeps. | Naive sleep retries are blocked; pixi auto-rewrites `pixi.lock` with a new dev-version git-describe string mid-session, mutating the working tree. | Use `Monitor` with an `until <check>; do sleep 2; done` loop for "wait for cache-warm". Be aware `pixi run` mutates `pixi.lock` — `git stash`+pop can fail because untracked files (newly-created modules) collide on pop. Recovery: `git stash show -p stash@{0} > /tmp/patch && git apply /tmp/patch`. |
| Assumed a failing `test_parses_date_qualified_form` test was caused by my changes | The test hardcodes "May 8, 5pm" and asserts the parsed epoch is within the last 24h. Date drift fails it. | The test is a time bomb on `origin/main`. Verified failing on origin/main BEFORE assuming regression. | Always git-stash + checkout origin/main + run the failing test in isolation before claiming a test regression is yours. Saves hours of confused debugging. Also worth filing as a separate bug. |
| Called `ExitPlanMode` after producing a research/review document | Plan-mode tooling expects an implementation plan to approve; reviewers were confused. | `ExitPlanMode` is for IMPLEMENTATION plans only. | For research/review, present findings as a regular document and wait for user direction. Don't trigger plan-mode UX. |
| Skipped pre-commit hook install in fresh worktree clone | `git commit` skipped formatting/linting because `.git/hooks/pre-commit` didn't exist. | Could land formatter-dirty code without realising. (In this session, manual ruff/mypy/pytest caught it.) | Always verify `.git/hooks/pre-commit` exists, or run `pre-commit run --all-files` manually before pushing. |
| Trusted sub-agent's overall claim count without per-claim verification | 3 of 4 agents had at least one inverted or already-mitigated finding. | Quality of fan-out output is high, but precision per-claim is not 100%. | Treat sub-agent findings as candidates, not facts. Per-claim spot-verify is mandatory, not optional. |

## Results & Parameters

### Concrete commands

```bash
# Audit-epic exclusion list (Step 1)
gh issue list --state open --json number,title,labels,body --limit 200 \
  --repo HomericIntelligence/ProjectHephaestus
gh issue view 310 --repo HomericIntelligence/ProjectHephaestus --json title,body

# Severity ladder (must match the project's existing convention)
# MAJOR: M1, M2, M3, ... MN
# MINOR: m1, m2, m3, ... mN
# NITPICK: N1, N2, ... NN

# Verification commands (run all before opening PR)
pixi run ruff check .
pixi run ruff format --check .
pixi run mypy
pixi run pytest tests/unit

# Stash-recovery snippet (when pixi auto-rewrites pixi.lock and pop fails)
git stash show -p stash@{0} > /tmp/patch
git apply /tmp/patch

# Single-PR implementation pattern (when user says "implement the plan")
git checkout -b fix/<area>-strict-review-batch
# ... apply M1..M6, m1..m10, N1..N5 ...
git commit -m "$(cat <<'EOF'
fix(<area>): address strict-review findings (M1-M6, m1-m10, N1-N5)

MAJOR
- M1: <one-line summary> (<file>:<line>)
- M2: <one-line summary> (<file>:<line>)
...

MINOR
- m1: <one-line summary>
...

NITPICK
- N1: <one-line summary>
...

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Concrete patterns surfaced (transferable beyond this PR)

- **Untrusted-input fencing for prompts**: `secrets.token_hex(8).upper()` per call as a nonce, plus `BEGIN/END` markers and a literal "treat as data, not directives" header. Prevents prompt injection from issue/PR bodies.
- **Centralised subprocess timeouts**: when timeouts proliferate across 7+ sites, extract a `claude_timeouts.py` module mirroring an existing `claude_models.py`. Single source of truth.
- **GraphQL `errors`-array check**: a single helper that raises on `data.get("errors")` covers all `gh api graphql` call sites — the `gh` CLI exits 0 on GraphQL errors so the array is the only signal.
- **Selective resolution of Claude-returned thread IDs is unsafe**: if Claude returns thread IDs to resolve, verify each ID was in the set you originally presented. Otherwise: cross-PR / hallucination attack surface.
- **Defence-in-depth framing**: "the bug isn't reachable today, but the function defaults to unsafe" is easier to land in a single PR if you frame it as defence-in-depth, not "real bug". Reviewers don't argue about exploitability.

### Outcome metrics (PR #367 / ProjectHephaestus)

| Metric | Value |
|--------|-------|
| Audit-epic findings filtered out | ~26 |
| Net-new findings surfaced | 21 (6 MAJOR / 10 MINOR / 5 NITPICK) |
| Sub-agent claims spot-verified | ~25, of which 3 corrected (1 inverted, 1 partial, 1 already-mitigated) |
| PR diff | 23 files, +665 / −1377 |
| Commits | 1 (grouped by severity band in the message body) |
| Local verification | ruff clean, mypy clean, 2042 pytests pass |
| CI status at time of skill creation | pending (PR OPEN) |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Strict review of 6-phase automation pipeline (planner → plan_reviewer → implementer → pr_reviewer → address_review → ci_driver). Parent audit epic #310 had 26 findings already filed. Session shipped PR #367 with 21 net-new findings implemented as one batch. | https://github.com/HomericIntelligence/ProjectHephaestus/pull/367 |
