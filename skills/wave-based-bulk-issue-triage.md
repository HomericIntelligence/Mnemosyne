---
name: wave-based-bulk-issue-triage
description: "Fix 5+ independent GitHub issues in parallel waves using Task isolation:worktree.\
  \ No manual worktree setup \u2014 Claude Code auto-manages isolation. Also covers\
  \ bulk gh issue create via myrmidon swarm (plain Agent calls, no worktrees needed).\
  \ Includes verify-before-fix pass to catch ALREADY-DONE issues Haiku misses."
category: architecture
date: 2026-04-12
version: 1.2.0
user-invocable: false
verification: verified-ci
history: wave-based-bulk-issue-triage.history
---
# Skill: Wave-Based Bulk Issue Triage

| Attribute | Value |
|-----------|-------|
| **Date** | 2026-04-12 |
| **Objective** | Fix 64 GitHub issues (4 waves, 12 PRs) — full myrmidon swarm pass on ProjectScylla |
| **Outcome** | 12 PRs created, 11 merged CI-green; verify-before-fix pass caught 3 false negatives |
| **Key Innovation** | `Task(isolation="worktree")` + mandatory verify-before-fix pass after Haiku classification |
| **History** | [changelog](./wave-based-bulk-issue-triage.history) |

## When to Use

Use this skill when:

1. **Backlog of 5+ independent issues** to clear in one session
2. **Issues fall into categories** — e.g., simple doc/config fixes vs. test additions
3. **Issues modify different files** — no shared file conflicts
4. **Want maximum parallelism** with minimal orchestration overhead
5. **Filing 10+ GitHub issues from an audit or walkthrough report** — use myrmidon swarm (plain Agent calls, no worktrees needed)

**Don't use when:**
- Issues depend on each other (use sequential PRs)
- Any issue touches 20+ files (exclude from wave, file separately)
- Issues share modified files (risk of merge conflicts)
- An issue claims a new feature with zero grep matches in the codebase — that is a feature request (MEDIUM/HIGH), not a trivial fix
- An issue involves complex multi-type exception handling where each exception type requires different semantics — cannot be safely converted to a generic `@retry` decorator without redesigning the exception flow

## Verified Workflow

### Phase 1: Triage & Wave Planning

Group issues by **complexity and type** before running anything:

```
Wave A — Simple fixes (no new files, minimal change):
  - Doc/config changes
  - Single-line .gitignore tweaks
  - Adding one test method to existing class

Wave B — Test additions (new classes, more lines):
  - New test classes for untested methods
  - Integration test roundtrips
  - Multi-method test coverage

Excluded — Too complex for bulk:
  - 20+ file changes
  - Cross-repo changes
  - Architectural refactors
```

**Key decision:** Run Wave A first (faster, unblocks Wave B if needed), then Wave B.

**Critical: Run a verify-before-fix pass AFTER Haiku classification, BEFORE launching fix agents.** Haiku has a ~5% ALREADY-DONE miss rate. A separate grep pass in the main tree catches these before wasted implementation work.

### Phase 1b: Verify-Before-Fix Pass (REQUIRED after Haiku classification)

After Haiku classifies issues, run a manual verify-before-fix pass before launching any fix agents:

```bash
# For ALREADY-DONE candidates — grep ONLY in the main tree (not worktrees)
grep -rn "pattern" /path/to/repo/ \
  --include="*.py" --include="*.toml" --include="*.yml" \
  --exclude-dir=".git" \
  --exclude-dir=".worktrees" \
  --exclude-dir=".claude"

# For issues claiming "add X" — verify X doesn't already exist
# For issues claiming "remove Y" — verify Y still exists
# For issues claiming "pin version Z" — verify current version in config files
```

**Key signals that drop an issue from LOW to ALREADY-DONE:**
- "no existing code to modify" — zero grep matches for the claimed new feature → feature request, not trivial fix → move to MEDIUM/HIGH
- nats-server pin done via direct curl to pinned version (not in pixi.toml) — grep the full install path
- Stale `--cov` refs only appear in `.worktrees/` or `.claude/worktrees/` — not in the main tree

**Critical: always grep in the MAIN tree only.** Worktrees contain stale content from prior branches. Always use `--exclude-dir=".worktrees"` and `--exclude-dir=".claude"`.

**Haiku classification accuracy** (64-issue session): ~95% correct, ~5% ALREADY-DONE miss rate (3 false negatives out of 64). Always run this pass — don't trust Haiku classification as ground truth.

### Phase 2: Launch Parallel Agents (One Wave at a Time)

Use `Task` tool with `isolation: "worktree"` — **no manual worktree setup needed**:

```python
# Launch all Wave A agents in parallel (single message, multiple Task calls)
Task(
    subagent_type="Bash",
    isolation="worktree",     # ← Claude Code auto-creates isolated worktree
    description="Fix #NNN brief-description",
    prompt="""
    You are fixing GitHub issue #NNN.

    ## Steps
    1. Read target file(s) before editing
    2. Make minimal change
    3. pre-commit run --files <changed-files>
    4. pixi run python -m pytest <specific-test-file> -q --no-cov
    5. git checkout -b NNN-slug
    6. git add <specific-files>  # Never git add -A
    7. git commit -m "type(scope): description (Closes #NNN)"
    8. git push -u origin NNN-slug
    9. gh pr create --title "..." --body "Closes #NNN"
    10. gh pr merge --auto --rebase

    ## Rules
    - Read files before editing
    - Never git add -A or git add .
    - Never --no-verify
    - Tests must pass before pushing
    """
)
```

Wait for Wave A to complete, then launch Wave B agents the same way.

### Phase 3: Verify

After all agents return:

```bash
gh pr list --author "@me" --state open
```

Check each PR has:
- ✅ Auto-merge enabled
- ✅ CI queued or passing

### Prompt Template for Bash Agent

```
You are fixing GitHub issue #NNN in the ProjectScylla repository.

## Task
[One-sentence description of the fix]

## Steps
1. Read the relevant file(s): cat path/to/file
2. [Specific fix instructions]
3. Run pre-commit: pre-commit run --files <changed-files>
4. Run tests: pixi run python -m pytest tests/path/to/test.py -q --no-cov
5. Create branch: git checkout -b NNN-slug
6. Stage only changed files: git add path/to/changed/file
7. Commit: git commit -m "type(scope): description (Closes #NNN)"
8. Push: git push -u origin NNN-slug
9. Create PR: gh pr create --title "type(scope): description" --body "Closes #NNN"
10. Auto-merge: gh pr merge --auto --rebase

## Important Rules
- Read files before editing them
- Never use git add -A or git add .
- Never use --no-verify
- Pre-commit must pass before committing
- Tests must pass before pushing
```

## Overview

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD |
| **Objective** | Skill objective |
| **Outcome** | Success/Operational |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| N/A | Direct approach worked for code-fix waves | N/A | Solution was straightforward |
| Body quoting (2026-04-06) | Single-quoted `--body '...'` strings with apostrophes/single quotes embedded | Shell interprets `'` inside `'...'` as end of string, breaking the command | Use `--body-file /tmp/issue-body.md` for any body containing single quotes or apostrophes |
| Security feature flagged as LOW (2026-04-12) | Issue requesting `clear_failure` injection_id validation classified as LOW/trivial | Zero grep matches for the named function — no existing code to modify. This was a new feature, not a fix | "No existing code to modify" = feature request → MEDIUM/HIGH. Verify-before-fix pass catches this. |
| Generic `@retry` decorator for multi-exception handler (2026-04-12) | Tried to replace inline retry loop in `model_validation.py` with `@retry` decorator | The loop had TimeoutExpired, FileNotFoundError, and Exception branches each requiring different semantics — impossible to flatten into one decorator | "Different action per exception type" = not safe to narrow to generic retry. Keep as-is or file as refactor, not LOW fix. |
| Grepping without excluding worktrees (2026-04-12) | Plain `grep -rn pattern /repo/` to detect ALREADY-DONE status | Worktrees contain stale branch content — gave false "still present" signal for #1655 (nats-server pin) and #1671 (stale --cov refs) | Always pass `--exclude-dir=.worktrees --exclude-dir=.claude --exclude-dir=.git` when grepping for ALREADY-DONE verification |
## Results & Parameters

### Myrmidon Swarm Pattern for Bulk Issue Filing (2026-04-06)

When filing 10+ `gh issue create` calls (e.g., from a walkthrough or audit report), use the **myrmidon swarm** (plain Agent calls) instead of `Task(isolation="worktree")`. No file modifications means no worktrees needed.

**Pattern:**

```
Wave 1 (≤5 Haiku agents in parallel):
  Agent 1: gh issue create --repo ORG/REPO --title "..." --label "..." --body-file /tmp/issue-1.md
  Agent 2: gh issue create --repo ORG/REPO --title "..." --label "..." --body-file /tmp/issue-2.md
  ...

Wave 2 (≤5 Haiku agents):
  ...

Wave 3 (remainder):
  ...
```

**Rules:**
1. Each agent gets exactly one `gh issue create` command
2. Multi-line or apostrophe-containing bodies: write to a temp file first, then pass `--body-file /tmp/issue-N.md`
3. Labels: pass multiple `--label` flags (one per label), **not** comma-separated in a single flag
4. Wave limit: **≤5 agents per wave** to prevent GitHub API rate limiting
5. Model tier: **Haiku** — fully-specified `gh issue create` calls require no design decisions
6. No worktrees needed since no repository files are modified

**Verified performance:** 11 issues filed in ~30 seconds total (3 waves: 5+5+1 agents) on HomericIntelligence/Odysseus (issues #99–109, 2026-04-06).

#### Body-File Pattern for Complex Issue Bodies

```bash
# In each agent's prompt:
cat > /tmp/issue-body.md << 'EOF'
## Summary
...content with 'single quotes' and apostrophes freely...

## Steps to Reproduce
...
EOF
gh issue create \
  --repo ORG/REPO \
  --title "Issue title" \
  --label "bug" \
  --label "priority:high" \
  --body-file /tmp/issue-body.md
```

### Session Results (2026-02-22)

| Wave | Issue | Fix Type | PR | Tests Added |
|------|-------|----------|----|-------------|
| 6a | #930 | Add test method to existing class | #1051 | 1 |
| 6b | #959 | Update 3 phantom doc paths | #1052 | 0 |
| 6c | #920 | 1-char .gitignore fix | #1053 | 0 |
| 6d | #1042 | New filter_audit.py script + pixi.toml update | #1055 | 0 |
| 7a | #985 | 8 tests for _move_to_failed + _commit_test_config | #1056 | 8 |
| 7b | #986 | 5 tests for _run_subtest_in_process_safe | #1057 | 5 |
| 7c | #987 | 6 tests for CursesUI._refresh_display | #1058 | 6 |
| 7d | #898 | 3 integration tests for --update roundtrip | #1059 | 3 |

**Total**: 8 PRs, 23 new tests, ~2 minutes wall clock per wave

### Session Results (2026-04-12) — ProjectScylla 64-Issue Pass

| Metric | Value |
|--------|-------|
| Issues classified by Haiku | 64 |
| Waves | 4 |
| PRs created | 12 |
| PRs merged CI-green (at skill creation time) | 11 |
| ALREADY-DONE caught by verify-before-fix | 3 (including 2 Haiku false negatives: #1655, #1671) |
| Haiku ALREADY-DONE miss rate | 4.7% (3/64) |
| Wall-clock time per wave (Sonnet + pre-commit + unit tests) | ~3-4 min |
| Total 4-wave wall clock | ~16 min |
| CI unit test duration | ~4-5 min |
| CI integration test duration | ~2 min |

### Wave Sizing Guidelines

| Wave Size | Agents | Expected Duration (Python/pixi repo) |
|-----------|--------|--------------------------------------|
| 2-3 issues | 2-3 parallel | ~1-2 min |
| 4-5 issues | 4-5 parallel | ~3-4 min |
| 6+ issues | Split into sub-waves | Varies |

### Issue Complexity Thresholds

| Category | Fits in Wave? | Notes |
|----------|--------------|-------|
| 1-char config fix | ✅ Yes | Simplest possible |
| Add 1 test method | ✅ Yes | 15-30 lines |
| Add new test class (5-8 tests) | ✅ Yes | Wave B material |
| Update 2-3 doc files | ✅ Yes | Quick |
| New script + config update | ✅ Yes | borderline, but ok |
| 20+ file changes | ❌ No | Exclude, file separate issue |
| Cross-repo changes | ❌ No | Exclude, handle manually |

### Exclusion Criteria (Skip for Now)

Add a comment in the plan when excluding:
```
### Excluded from Wave N
- **#NNN** (brief reason) — [specific reason]. Skip for now.
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectScylla | Wave 6+7, PRs #1051-#1059 (2026-02-22) | 8 PRs, 23 new tests, ~2 min/wave |
| HomericIntelligence/Odysseus | Bulk issue filing, issues #99-#109 (2026-04-06) | 11 issues, 3 waves (5+5+1 Haiku agents), ~30s total |
| ProjectScylla | 64-issue myrmidon swarm, 4 waves, 12 PRs (2026-04-12) | Haiku classification + verify-before-fix pass, 11/12 PRs merged CI-green |
