---
name: debugging-silent-pipeline-stage-via-argparse-required-grep
description: "Diagnose silent stages in fan-out orchestrators (shell driving N Python CLIs, Makefile driving N tools, CI workflow driving N jobs) via a 3-command source-grep that compares argparse `required=True` flags against the flags the orchestrator actually passes, OR via a 2-command grep that identifies unguarded infrastructure commands in a backgrounded orchestrator function running under `set -euo pipefail`. Use when: (1) a multi-stage pipeline reports success but a downstream stage produced no visible output, (2) only the first phase of run_automation_loop.sh / similar orchestrator runs, (3) orchestrator logs show generic `Warning: ... exited non-zero` with no underlying error detail, (4) you are tempted to re-run with `tee` + banner greps to reproduce a silent-stage bug, (5) the orchestrator uses `|| echo`, `|| true`, `set +e`, or `continue-on-error: true` to swallow exit codes, (6) the symptom returned AFTER a prior fix to a different silent-stage cause in the same orchestrator — there is often a SECOND silent-stage cause hiding behind the first."
category: debugging
date: 2026-05-25
version: "1.1.0"
user-invocable: false
verification: verified-local
history: debugging-silent-pipeline-stage-via-argparse-required-grep.history
tags:
  - argparse
  - orchestrator
  - silent-failure
  - source-grep
  - debugging-methodology
  - fan-out
  - exit-code-swallowing
  - shell
  - python
  - cli-contract
  - set-e
  - errexit
  - backgrounded
  - subshell
  - process-repo
  - second-cause
---

# Debugging Silent Pipeline Stages via argparse `required=True` Grep

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-24 (v1.0.0) / 2026-05-25 (v1.1.0 amendment) |
| **Objective** | Localize silent-stage bugs in fan-out orchestrators in under 60 seconds via source review, instead of re-running the orchestrator with `tee` + banner instrumentation |
| **Outcome** | SUCCESS — methodology applied in ProjectHephaestus session identified root cause (orchestrator invoking 4 phase CLIs without `--issues`, all 4 required it) in ~60 seconds; fix shipped as PR #543. v1.1.0 extends the methodology to a second cause (set -e abort in backgrounded subshell) discovered when the symptom returned in the same orchestrator on 2026-05-25. |
| **Verification** | verified-local — methodology applied in two real sessions on the same orchestrator |

## When to Use

- A multi-stage orchestrator (shell, Makefile, CI workflow) reports success or only generic warnings, but a stage produced no visible output
- Only the first phase of a multi-phase pipeline appears to run (e.g., "planning ran but PR review didn't")
- Orchestrator stdout shows lines like `Warning: repo job exited non-zero` with no underlying cause
- You are about to set up `tee` + grep banners + a long dry-run to reproduce — STOP and try this first
- Orchestrator contains exit-code suppressors: `|| echo`, `|| true`, `set +e`, `continue-on-error: true`, `ignore_errors: yes`
- The failing CLI is argparse-based (Python), click-based, typer-based, or any framework that exits before any of the CLI's own logging fires
- The orchestrator function is backgrounded with `&` and inherits `set -euo pipefail` from the script header — any unguarded non-zero return inside the function will silently abort it. Symptom looks identical to v1.0.0's argparse-required cause.

## Verified Workflow

### Cause A: argparse `required=True` missing (v1.0.0)

#### Quick Reference

```bash
# 1. List the orchestrator's outbound CLI calls and their flags
grep -nE '\$(PYTHON|.*_BIN)\b.*\.(py)?' scripts/run_automation_loop.sh | head -20

# 2. For each invoked CLI, check argparse required flags
for cli in hephaestus/automation/{plan_reviewer,pr_reviewer,address_review,ci_driver}.py; do
  echo "=== $cli ==="
  grep -n -B1 -A3 'required=True' "$cli" | head
done

# 3. Find the orchestrator's swallow points (these mask the real exit code)
grep -nE '\|\| echo|\|\| true|set \+e|continue-on-error' scripts/run_automation_loop.sh
```

Any flag the orchestrator does NOT pass that the CLI marks `required=True` = root cause. The CLI exited at argparse-time (exit 2) before producing any output the orchestrator could log.

#### Detailed Steps

1. **Enumerate outbound calls from the orchestrator.** One grep over the orchestrator script for the binary or interpreter variable (`$PYTHON`, `$NODE_BIN`, `$PR_REVIEW_BIN`, etc.) and the file extensions of CLIs it invokes. Read the exact flag list for each call — copy it down.

2. **For each invoked CLI, locate the argparse setup.** Search the CLI's source for:
   - Python argparse: `required=True`
   - Python click: `@click.argument` (positional, implicitly required), `required=True` on `@click.option`
   - Python typer: positional parameters without `= None` default
   - Go cobra: `cmd.MarkFlagRequired(`
   - Node commander: `.requiredOption(`
   - Rust clap: `.required(true)`

3. **Diff the required-by-CLI set against the passed-by-orchestrator set.** Any flag in (required ∩ ¬passed) is a contract violation. The CLI will exit at parse-time before its own logging or banners run. This is decidable from source — do not run anything.

4. **Locate the swallow point in the orchestrator.** The orchestrator MUST be suppressing the failing exit code, or you would have seen the failure directly. Common patterns:

   | Pattern | Effect |
   |---------|--------|
   | `cmd \|\| echo "Warning: ..."` | Replaces exit 2 with a generic warning line, exit 0 |
   | `cmd \|\| true` | Replaces any non-zero with exit 0, silently |
   | `set +e` | Disables errexit for the block — non-zero is ignored |
   | `continue-on-error: true` (GitHub Actions) | Job continues regardless of step exit |
   | `ignore_errors: yes` (Ansible) | Task failure does not abort the play |
   | `2>/dev/null` on stderr | argparse error message is discarded — operator sees nothing |

   Confirm at least one is present at the call site of the failing stage. This explains why the operator only saw a vague warning.

5. **Verify the fix is in the orchestrator, not the CLI.** The CLI is behaving correctly (rejecting invalid input). The orchestrator must either:
   - Pass the missing required flag, OR
   - Stop suppressing the exit code so the operator sees the real error.

   Both are typically warranted: pass the flag AND remove `|| echo` so future contract drift is loud.

### Cause B: `set -e` abort in backgrounded subshell (added v1.1.0)

When the Cause A grep methodology clears (no required flag missing, no `|| echo` swallow at the phase-CLI call site), but the symptom persists, the second-most-common cause is `set -euo pipefail` aborting a backgrounded orchestrator function on an unguarded infrastructure command.

#### Quick Reference

```bash
# Detect: is process_repo (or your equivalent) backgrounded under set -e with no local set +e?
ORCH=scripts/run_automation_loop.sh
FUNC=process_repo
grep -n 'set -.*\(e\|errexit\)' "$ORCH" | head -5         # script has errexit?
grep -n "$FUNC .*&" "$ORCH"                                # function is backgrounded?
sed -n "/^$FUNC()/,/^}/p" "$ORCH" | grep -n 'set +e'       # function disables errexit locally?
sed -n "/^$FUNC()/,/^}/p" "$ORCH" \
  | grep -nvE '^\s*#|^\s*$|\|\| echo|\|\| true|\|\| return|^\s*(echo|local|return|trap|if|fi|else|done|for|while|do|cd|export|local) ' \
  | head -20                                               # candidate unguarded statements
```

#### Detailed Steps

1. Confirm the script header sets `set -euo pipefail` (or `set -e`).
2. Confirm the orchestrator function is backgrounded with `&` (job control).
3. Grep for any local `set +e` inside the function — if absent, errexit propagates.
4. List unguarded statements between the last visible banner (phase 1 START) and the first invisible one (phase 2 START missing). Common culprits:
   - `git fetch origin --quiet` (returns non-zero on network failure, no remote, etc.)
   - `mapfile -t OPEN_ISSUES < <(gh ... 2>/dev/null)` — process substitution exit-status under `set -m` (rare but documented bash quirk)
   - `local X=$(cmd)` where `cmd` returns non-zero — the local assignment masks errexit ONLY if `local` is itself the command, otherwise it propagates
   - `HEPH_TRUNK_GITHASH=$(git rev-parse ... || echo unknown); export HEPH_TRUNK_GITHASH` — the `export` itself can interact with `set -u` if the var is unset

5. Fix shape (preferred — minimum blast radius):

   ```bash
   <function>() {
     set +e
     trap 'set -e' RETURN
     local rc t0
     ...
   }
   ```

   The function-scope `set +e` disables errexit only inside the function. The `trap 'set -e' RETURN` is harmless-but-redundant when the function is always backgrounded (the subshell exits anyway); keep it for future synchronous call sites.

6. Diagnostic shape (add per-phase START/done banners so a future silent abort is immediately visible):

   ```bash
   phase_start() { echo "  [$1] phase $2/$N $3 START" >&2; date +%s; }
   phase_done()  { local now=$(date +%s); echo "  [$1] phase $2/$N $3 done in $((now - $4))s (rc=${5:-0})"; }
   ```

   START → stderr (operator-facing diagnostic). Capture timestamp via stdout for `t0=$(phase_start …)`. The `done` banner missing = phase aborted inside. The `done` AND `start` banner both missing for phase N+1 = unguarded statement aborted the function between phases.

7. Verify the regression with a test that intentionally makes one phase exit non-zero and asserts subsequent phases STILL run. See [[bash-script-and-jq-failure-modes]] for related shell-test patterns.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Re-run with tee + banner grep | Plan to capture a full dry-run log via `tee`, then grep for banner lines from each phase | Slow (5+ min orchestrator run × N repos), and the bug is upstream of stdout — banners would only confirm the symptom, not the cause. argparse exits before the CLI's own logging runs | Do not reproduce when the bug is decidable from source. Run repros only after source review fails to localize the failure |
| Hypothesize `--phases` env was set to a subset | Theory: orchestrator's `PHASES` env variable filtered out the missing stages | Possible but only explains one of two observable symptoms (the missing banner). Does not explain the `Warning: repo job exited non-zero` line the user pasted — that line proves the stage WAS invoked and exited non-zero | Multi-symptom triage: a hypothesis must explain ALL observed symptoms, not just the loudest one. A single observation can mislead; the warning line was the load-bearing clue |
| Read orchestrator logs for warnings/errors | Scrub orchestrator stdout for ERROR/WARN lines | The orchestrator was actively suppressing the very signal needed: `\|\| echo "Warning: ..."` collapses exit code 2 from argparse into a generic warning identical to per-issue runtime failures. Logs cannot show what the logger refuses to record | When the system actively suppresses error detail, source review is the only reliable path. Logs lie when the logger is the perp. Always grep for `\|\| echo`, `\|\| true`, and `set +e` before trusting orchestrator logs |
| Assume the CLI's own logging would show the failure | Expected the failing CLI to log "missing required argument" somewhere | argparse exits via `parser.error()` → writes to stderr → `sys.exit(2)`. This happens BEFORE any user-defined logging setup runs. If the orchestrator discards stderr or wraps the call in `\|\| echo`, the operator never sees the message | argparse failures are upstream of application logging. The only place the message lands is the orchestrator's captured stderr — if that is suppressed, source review is mandatory |
| Assume PR #543 (argparse-required cause) was the only silent-stage cause | After v1.0.0 shipped, the silent-stage symptom was treated as resolved. | A different bug — `set -e` abort on an unguarded infrastructure command — produced the same operator-visible symptom (`Warning: repo job pid=... exited non-zero` + missing phase banners). Same orchestrator, same effect, different root cause. | When a silent-stage symptom resurfaces in the SAME orchestrator, do NOT assume the prior fix is sufficient. Run BOTH the v1.0.0 argparse grep AND the v1.1.0 set-e/backgrounded grep before concluding "it's the same bug as last time". |
| Trust that `set -euo pipefail` is safe inside a backgrounded function | Original orchestrator structure: `set -euo pipefail` at script top, function backgrounded with `&`, no local `set +e`. | The function inherits errexit. An unguarded non-zero return aborts the function silently. The outer `wait` reports non-zero but the orchestrator's `\|\| echo` swallow at the call site collapses it into a generic warning. Operator sees only the warning, never the underlying failure line. | Backgrounded functions under `set -e` are silent-abort traps. Use a local `set +e` + explicit `rc=$?` per phase + structured warning logging (NOT generic `\|\| echo`). |

## Results & Parameters

### Decision Rule

```text
IF orchestrator stage produces no output AND orchestrator reports success/generic warning:
  # Cause A check first
  required_flags := grep required=True in CLI source
  passed_flags   := grep CLI invocation in orchestrator
  IF required_flags - passed_flags ≠ ∅:
    ROOT CAUSE = contract violation at <flag>
    FIX = pass the flag, AND remove the swallow at the call site
  ELSE:
    # Cause B check
    IF orchestrator function is backgrounded AND script uses set -e AND no local set +e:
      ROOT CAUSE = errexit abort on unguarded infrastructure command
      FIX = `set +e` + `trap 'set -e' RETURN` inside function;
            add per-phase START/done banners for observability
    ELSE:
      fall back to dry-run with tee + banners (now justified)
```

### Time Budget Comparison

| Approach | Wall-clock | Sensitivity | When to Use |
|----------|------------|-------------|-------------|
| Source-grep (this skill) | ~60 seconds | Catches all argparse-time failures, missed flags, removed flags, set -e silent aborts in backgrounded functions | Always try first |
| Dry-run with tee + banners | 5+ minutes per repo × N repos | Catches runtime failures inside the CLI body | Only after source-grep clears |
| Read orchestrator logs | Seconds, but unreliable | Useless when orchestrator suppresses exit codes | Never trust alone if `\|\| echo` is present |

### Concrete Example (ProjectHephaestus PR #543 — Cause A)

**Symptom**: `scripts/run_automation_loop.sh` appeared to only run the planning phase. User reported "why is run_automation_loop.sh only running the planning phase?"

**Diagnostic** (~60 seconds):
- 4 phase CLIs in `hephaestus/automation/`: `plan_reviewer.py`, `pr_reviewer.py`, `address_review.py`, `ci_driver.py`
- All 4 had `--issues` declared with `required=True`
- Orchestrator invoked all 4 WITHOUT `--issues`
- Orchestrator wrapped each call in `|| echo "Warning: repo job exited non-zero"`

**Root cause**: Missing `--issues` flag → argparse exit 2 → swallowed by `|| echo` → operator saw only generic warning + missing banner.

**Fix shape**: Pass `--issues "$issues"` to each phase invocation; replace `|| echo` with a structured failure that preserves the exit code.

### Concrete Example (ProjectHephaestus 2026-05-25 — Cause B)

**Symptom**: After PR #543 landed, `scripts/run_automation_loop.sh` STILL only showed phase 1 per repo. Operator saw `Warning: repo job pid=NNN exited non-zero (continuing)`. Cause A grep cleared — all phase CLIs now received `--issues`.

**Diagnostic** (~60 seconds):
- Script header: `set -euo pipefail`
- `process_repo` function backgrounded with `process_repo "$repo" "$loop" &`
- No local `set +e` inside `process_repo`
- Unguarded statements between phase 1 and phase 2 included `git fetch origin --quiet` (line 257) and `mapfile -t OPEN_ISSUES < <(gh issue list ...)`

**Root cause**: An unguarded infrastructure command returned non-zero, errexit aborted the backgrounded subshell silently, outer `wait` reported non-zero, `|| echo` swallow collapsed it to a generic warning.

**Fix shape**: `set +e` + `trap 'set -e' RETURN` inside `process_repo`; add `phase_start`/`phase_done` banners around each phase block; let each phase's `rc=$?` + structured warning be the authoritative error handler.

### Generalization Across Stacks

| Stack | "Required flag" pattern (Cause A) | "Swallow" pattern | "set -e abort" analog (Cause B) |
|-------|-----------------------------------|-------------------|---------------------------------|
| Python argparse | `add_argument(..., required=True)` | shell `\|\| echo`, `\|\| true` | Backgrounded shell function under `set -e` |
| Python click | `@click.option(..., required=True)`, `@click.argument` | shell `\|\| echo`, `\|\| true` | Backgrounded shell function under `set -e` |
| Python typer | Positional param without default | shell `\|\| echo`, `\|\| true` | Backgrounded shell function under `set -e` |
| Go cobra | `cmd.MarkFlagRequired("name")` | shell `\|\| echo`, `errcheck` ignored | goroutine without recover() / errgroup |
| Node commander | `.requiredOption("--name <value>")` | shell `\|\| echo`, `.catch(() => {})` | unhandled promise rejection in worker |
| Make targets | `$(error ...)` on missing var | `-` prefix on recipe line | recursive `$(MAKE)` without `+` propagation |
| GitHub Actions | `inputs.<name>.required: true` | `continue-on-error: true` | matrix job killed by `fail-fast: true` |
| Ansible | `required: true` in arg_spec | `ignore_errors: yes` | async task timeout silently dropping |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PR #543 — `scripts/run_automation_loop.sh` invoking 4 automation CLIs without `--issues` (Cause A) | Methodology localized root cause in ~60s; fix shipped as PR #543 |
| ProjectHephaestus | 2026-05-25 follow-up — same orchestrator, `process_repo` aborting under `set -euo pipefail` (Cause B) | Cause A grep cleared after PR #543; Cause B grep identified errexit + backgrounded function as new root cause; fix shape: `set +e` + `trap 'set -e' RETURN` + per-phase START/done banners |
