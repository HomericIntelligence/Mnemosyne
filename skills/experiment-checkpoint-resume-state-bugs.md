---
name: experiment-checkpoint-resume-state-bugs
description: "Diagnose and fix experiment checkpoint resume failures. Use when: (1) checkpoint shows intermediate states (e.g. `judge_prompt_built`, `report_written`) but on-disk artifacts confirm completion, (2) `--retry-errors` appears to do nothing or skips runs that need re-running, (3) experiment is marked `complete` but has stuck or orphaned intermediate runs, (4) dryrun NOGO with fixable blockers (stuck checkpoints, missing subtests, leftover workspace dirs), (5) Liza planning handoff is stalled after checkpoint/resume, (6) `.liza/state.yaml` timestamps were rewritten by PyYAML breaking `liza validate`/`liza resume`."
category: debugging
date: 2026-05-19
version: "1.0.0"
user-invocable: false
history: experiment-checkpoint-resume-state-bugs.history
tags:
  - checkpoint
  - resume
  - intermediate-state
  - disk-reconciliation
  - retry-errors
  - liza
  - stale-state
---

# Experiment Checkpoint Resume State Bugs

## Overview

| Field | Value |
| ------- | ------- |
| **Theme** | Checkpoint persistence, disk reconciliation, intermediate state recovery, and cleanup of stale checkpoint files after interrupted or partially-complete experiment runs |
| **Root Causes** | ProcessPool save races (concurrent forked workers overwrite each other's state), save-guard counting only a subset of reset runs, resume logic skipping `complete`-family experiments, orphaned subtest state, uppercase `"INTERRUPTED"` literal, ephemeral `max_subtests` not cleared on resume, Liza wake detection requiring all-planned-tasks-terminal, PyYAML timestamp serialization |
| **Scope** | ProjectScylla `manage_experiment.py` / `resume_manager.py` / `runner.py`; Liza `workdetection.go`, `mode_change.go`, `state.yaml` |
| **Key Invariant** | Disk artifact truth (`run_result.json`) always wins over in-memory or checkpoint state; reconciliation only advances states — never regresses |

## When to Use

1. `--retry-errors` skips tests that should be re-run (checkpoint shows `worktree_cleaned` but `completed_runs` has `status: "failed"`)
2. Experiment interrupted mid-run; checkpoint has intermediate states but `run_result.json` exists on disk
3. Experiment is marked `complete` but `analyze_dryrun3.py` reports intermediate or missing runs
4. `subtest_states` has `aggregated`/`runs_complete` entries with no corresponding `run_states` key
5. `--retry-errors` appears to do nothing — checkpoint on disk does not reflect in-memory state changes
6. Resumed experiment with different `--max-subtests` doesn't execute new subtests
7. A Ctrl+C interrupted experiment doesn't reset properly on next run (uppercase `"INTERRUPTED"` bug)
8. Dryrun analysis shows NOGO with fixable blockers (INTERMEDIATE runs, workspace dirs, superseded dirs)
9. Liza coders are idle despite completed merged planning outputs; `PLANNING_COMPLETE` is absent
10. `liza validate` / `liza resume` fail with `cannot parse ... as "T"` after PyYAML touched `.liza/state.yaml`

## Verified Workflow

### Quick Reference

```python
# Disk inference priority for reconciliation (highest wins):
# run_result.json + report.md + no workspace/  → worktree_cleaned
# run_result.json + report.md                  → report_written
# run_result.json only                         → run_finalized
# judge/result.json valid                      → judge_complete
# agent/result.json valid                      → agent_complete
# nothing                                      → leave as-is
```

```bash
# Liza timestamp repair (PyYAML-mangled state.yaml)
python3 - <<'PY'
from pathlib import Path; import re
path = Path(".liza/state.yaml")
text = re.sub(
    r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}(?:\.\d+)?)(Z|[+-]\d{2}:\d{2})',
    r'\1T\2\3', path.read_text())
path.write_text(text)
PY
liza validate && liza resume
```

### 1. Diagnose the problem class

Run the analyzer and classify which failure mode applies:

```bash
pixi run python scripts/analyze_dryrun3.py --results-dir ~/dryrun3
```

| Symptom | Failure Mode | Fix Section |
| --------- | ------------- | ------------- |
| Intermediate states with valid on-disk results | Disk reconciliation | §2 |
| Judge-failed runs at `worktree_cleaned` not re-run | Save guard / `--retry-errors` | §2, §3 |
| `complete` experiment with intermediate/orphaned runs | Resume logic gap | §4 |
| `--retry-errors` does nothing (no checkpoint save) | Save-guard counting bug | §3 |
| New subtests not picked up on resume | Ephemeral `max_subtests` / tier reset | §5 |
| Uppercase `"INTERRUPTED"` blocks step 3 reset | State casing bug | §5 |
| Workspace dirs / superseded experiment dirs | Manual cleanup | §6 |
| Liza planning handoff stalled | Liza wake detection | §7 |
| `liza validate` timestamp parse error | PyYAML serialization | §8 |

### 2. Implement `_reconcile_checkpoint_with_disk()`

Add to `scripts/manage_experiment.py` after `_reset_non_completed_runs`:

```python
def _reconcile_checkpoint_with_disk(checkpoint: Any, experiment_dir: Path) -> int:
    """Advance stale checkpoint states to match on-disk reality.
    Only moves states forward — never regresses. Returns correction count."""
    from scylla.e2e.agent_runner import _has_valid_agent_result
    from scylla.e2e.judge_runner import _has_valid_judge_result

    _STATE_ORDER = [
        "pending", "dir_structure_created", "symlinks_applied",
        "baseline_captured", "replay_generated", "agent_complete",
        "diff_captured", "judge_pipeline_run", "judge_prompt_built",
        "judge_complete", "run_finalized", "report_written",
        "checkpointed", "worktree_cleaned",
    ]
    _STATE_RANK = {s: i for i, s in enumerate(_STATE_ORDER)}
    corrected = 0

    for tier_id, subtests in checkpoint.run_states.items():
        for subtest_id, runs in subtests.items():
            for run_num_str, current_state in list(runs.items()):
                run_num = int(run_num_str)
                run_dir = (experiment_dir / tier_id / subtest_id
                           / f"run_{run_num:02d}")
                if not run_dir.exists():
                    continue

                run_result_file = run_dir / "run_result.json"
                report_md = run_dir / "report.md"
                workspace_dir = run_dir / "workspace"
                inferred_state: str | None = None
                inferred_status: str | None = None

                if run_result_file.exists():
                    try:
                        import json as _json
                        data = _json.loads(run_result_file.read_text())
                        inferred_status = (
                            "passed" if data.get("judge_passed") else "failed"
                        )
                    except (OSError, ValueError, KeyError):
                        inferred_status = None
                    if report_md.exists() and not workspace_dir.exists():
                        inferred_state = "worktree_cleaned"
                    elif report_md.exists():
                        inferred_state = "report_written"
                    else:
                        inferred_state = "run_finalized"
                elif _has_valid_judge_result(run_dir):
                    inferred_state = "judge_complete"
                elif _has_valid_agent_result(run_dir):
                    inferred_state = "agent_complete"

                if inferred_state is None:
                    continue
                if _STATE_RANK.get(inferred_state, 0) > _STATE_RANK.get(current_state, 0):
                    checkpoint.set_run_state(
                        tier_id, subtest_id, run_num, inferred_state
                    )
                    if inferred_status is not None:
                        checkpoint.mark_run_completed(
                            tier_id, subtest_id, run_num, status=inferred_status
                        )
                    corrected += 1
    return corrected
```

Also extend `_reset_non_completed_runs()` to reset judge-failed runs and extend
`_checkpoint_has_retryable_runs()` to check `completed_runs` for `"failed"` entries.
Integrate reconcile before reset in both batch and single `--retry-errors` handlers.

### 3. Fix the save-guard counting bug

The root cause: `_reset_non_completed_runs()` returned a count of only
terminal (`failed`/`rate_limited`) resets; callers gated `save_checkpoint()` on
`reset_count > 0`. For intermediate-only cases, tier/subtest states were cascaded
to `pending` in memory but the count stayed zero so checkpoint was never saved.

**Fix (one line in `scripts/manage_experiment.py:351`)**: move `reset_count += 1`
_before_ the terminal-state check so every non-completed run increments the counter.

### 4. Fix resume logic for `complete`-family experiments

`reset_failed_states()` had a guard: `if experiment_state not in ("failed", "interrupted"): return`.
This skipped `complete` experiments with intermediate runs.

Add three detection methods to `scylla/e2e/resume_manager.py`:

```python
_COMPLETE_FAMILY_STATES = ("complete", "tiers_complete", "reports_generated")
_COMPLETE_TIER_STATES = ("complete", "subtests_complete", "best_selected",
                         "reports_generated")

def _find_tiers_with_intermediate_runs(self): ...
def _find_orphaned_subtest_states(self): ...  # aggregated/runs_complete with no run_states
def _reset_intermediate_runs_in_complete_experiment(self): ...
def _reset_orphaned_subtest_states(self): ...
def _reset_failed_and_interrupted(self): ...

def reset_failed_states(self):          # becomes simple dispatch
    self._reset_infra_error_runs()
    self._reset_intermediate_runs_in_complete_experiment()
    self._reset_orphaned_subtest_states()
    self._reset_failed_and_interrupted()
```

Extract each concern into its own method to stay under C901 complexity limit (10).

### 5. Fix runner resume bugs (`runner.py`)

**Bug A — uppercase `"INTERRUPTED"`**: `_handle_experiment_interrupt` set
`experiment_state = "INTERRUPTED"` (uppercase literal). STEP 3 in
`_initialize_or_resume_experiment` only matched lowercase. Fix: use
`ExperimentState.INTERRUPTED.value`.

**Bug B — `max_subtests` not cleared on resume**: `--max-subtests` omitted on
resume should mean "no limit". Restore ephemeral fields explicitly:

```python
# STEP 2: always restore max_subtests (None clears saved limit)
self.config = self.config.model_copy(
    update={"max_subtests": _cli_ephemeral["max_subtests"]}
)
```

**Bug C — missing-subtest detection invisible**: `_check_tiers_need_execution()`
only checked `run_states` (existing runs). Extend to compare config vs checkpoint
subtest sets. When missing subtests are found, reset tier to `"pending"` (not
`"subtests_running"`) so `action_pending()` reloads the full subtest list.

### 6. Clean up workspace and superseded experiment dirs

```bash
# 1. Analyze
pixi run python scripts/analyze_dryrun3.py --results-dir ~/dryrun3

# 2. Generate deletion lists via cleanup script, then delete manually
#    (Safety Net blocks rm -rf outside cwd even from Python subprocess)
rm -rf <workspace-dirs>
rm -rf <superseded-dirs>

# 3. Retry and verify
bash retry_dryrun3.sh
pixi run python scripts/analyze_dryrun3.py --results-dir ~/dryrun3
```

Safe to delete: workspace dirs at `worktree_cleaned`, orphan subtests beyond
`max_subtests`, superseded experiment dirs (older timestamp, same test name).

### 7. Fix Liza planning handoff starvation

When merged planning tasks have `output[]` but no implementation children exist:

1. Fix `DetectOrchestratorWakeTriggers` (`internal/agent/workdetection.go`) to emit
   `PLANNING_COMPLETE` as soon as any merged planning outputs with unconsumed `output[]`
   exist — do not wait for all planned tasks to become terminal.
2. Fix `liza resume` (`internal/ops/mode_change.go`) to execute available transitions
   immediately when resuming from a `PLANNING_COMPLETE` checkpoint and clear the trigger.
3. After installing the patched binary: `liza sprint-checkpoint && liza resume && liza validate --json`.

### 8. Repair PyYAML-mangled `.liza/state.yaml`

When `liza validate` fails with `cannot parse " 17:21:30..." as "T"`:

```bash
python3 - <<'PY'
from pathlib import Path; import re
path = Path(".liza/state.yaml")
text = re.sub(
    r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}(?:\.\d+)?)(Z|[+-]\d{2}:\d{2})',
    r'\1T\2\3', path.read_text())
path.write_text(text)
PY
liza validate
```

Always run `liza validate` before `liza resume`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Reset all non-`worktree_cleaned` states to `pending` without reading disk | Simple reset skipping disk scan | Re-ran agent from scratch when judge already completed | Infer state from disk artifacts to resume at the right point |
| Only fix `_checkpoint_has_retryable_runs` for batch skip | Updated skip detection but not the actual reset logic | Batch entered retry but `_reset_non_completed_runs` still skipped judge-failed runs | Both detection AND reset must handle the judge-failed pattern |
| Read `run_result.json` `judge_passed` without error handling | Used field directly | Malformed JSON or missing field caused crash | Wrap in try/except; default `inferred_status = None` if parse fails |
| Only reset `failed`/`interrupted` experiment states in `reset_failed_states()` | Early return for non-failed/interrupted states | `complete` experiments with intermediate runs skipped entirely | Must also check for intermediate runs in `complete`-family states |
| Monolithic `reset_failed_states()` with inline intermediate/orphan detection | All logic inlined | C901 complexity exceeded limit (19 > 10), SIM102 nested-if lint failure | Extract each concern into its own method; use shared helper constants |
| Relying on state machine log as proof of completion | Log showed `checkpointed -> worktree_cleaned` | Checkpoint file on disk still had `report_written` (ProcessPool save race) | Always verify on-disk checkpoint file; verify from `run_result.json` |
| Existing tests asserting `"INTERRUPTED"` (uppercase) | Test documented buggy behavior | Test passed but bug was invisible | When a test documents seemingly wrong behavior, check if it's documenting a bug |
| Fixing ephemeral `max_subtests` only (not tier reset target) | Cleared limit but reset tier to `subtests_running` | `action_pending()` never re-ran so full subtest list not reloaded | Must reset to `"pending"` for missing-subtest cases, not `"subtests_running"` |
| Repairing agent pool before generating implementation tasks | `liza repair-agent-pool --dry-run` showed no missing roles | Implementation tasks had not been generated yet | Diagnose planning output handoff before changing the pool |
| Normalizing only `+00:00` Liza timestamps | Replaced `YYYY-MM-DD HH:MM:SS+00:00` only | Local timestamps like `...11:38:50.820435-07:00` still broke the parser | Use a single regex covering both UTC `Z` and signed offsets |
| Round-tripping `.liza/state.yaml` through `yaml.safe_dump()` | Convenient way to clear a stale field | PyYAML changed timestamp formatting across the whole file | For live Liza state, use minimal text edits; avoid whole-file serializer round-trips |
| `rm -rf` in Python cleanup script via Bash tool | `shutil.rmtree()` in script | Safety Net blocks `rm -rf` outside cwd even through Python subprocess | Provide manual deletion commands; Safety Net inspects the command string |
| Glob-based workspace deletion in shell | `rm -rf /path/T*/0[3-7]/run_01/workspace` | Safety Net blocked shell glob expansion outside cwd | Same constraint — user must run deletions manually |

## Results & Parameters

### State inference priority (disk artifacts)

| Disk Artifacts Present | Inferred State |
| ------------------------ | ---------------- |
| `run_result.json` + `report.md` + no `workspace/` | `worktree_cleaned` |
| `run_result.json` + `report.md` + `workspace/` present | `report_written` |
| `run_result.json` only | `run_finalized` |
| `judge/result.json` valid (no `run_result.json`) | `judge_complete` |
| `agent/result.json` valid (no `judge/result.json`) | `agent_complete` |
| Nothing | leave as-is |

### Key checkpoint state transitions for patching

| From State | To State | When |
| ------------ | ---------- | ------ |
| `report_written` | `pending` | Run stuck after report but before worktree cleanup |
| `aggregated` | `pending` | Orphaned subtest needs re-run |
| `complete` (tier) | `config_loaded` | Tier has incomplete subtests |
| `complete` (experiment) | `tiers_running` | Experiment has incomplete tiers |
| `complete` (tier) | `pending` | Tier needs new subtests discovered |

### Run directory structure

```
experiment_dir/
  {tier_id}/          # e.g., T0, T6
    {subtest_id}/     # e.g., 00, 01
      run_{NN:02d}/   # e.g., run_01
        run_result.json
        report.md
        workspace/    # deleted at worktree_cleaned stage
        agent/result.json
        judge/result.json
```

### Key checkpoint API

```python
checkpoint.run_states["T0"]["00"]["1"]          # e.g., "judge_prompt_built"
checkpoint.completed_runs["T0"]["00"][1]        # "passed", "failed"
checkpoint.set_run_state(tier_id, subtest_id, run_num, state)
checkpoint.mark_run_completed(tier_id, subtest_id, run_num, status="passed")
checkpoint.unmark_run_completed(tier_id, subtest_id, run_num)
checkpoint.get_run_status(tier_id, subtest_id, run_num)
```

### Reference PRs

- ProjectScylla PR #1480: disk reconciliation before retrying
- ProjectScylla PR #1474: intermediate-state save-guard fix
- ProjectScylla PR #1490: always retry infra failures / orphaned subtest detection
- ProjectScylla PR #1109: resume casing, ephemeral fields, missing subtest detection
- `https://github.com/liza-mas/liza/pull/70`: Liza planning handoff fix

## Verified On

| Project | Context |
| --------- | --------- |
| ProjectScylla | PRs #1480, #1474, #1490, #1109 — dryrun3 experiment (47 tests, 1196 runs) |
| liza-mas/liza | PR #70 — planning handoff fix; Metrics Service workspace recovery |
