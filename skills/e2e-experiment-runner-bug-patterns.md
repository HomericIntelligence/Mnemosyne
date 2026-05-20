---
name: e2e-experiment-runner-bug-patterns
description: "Canonical reference for bugs in the E2E evaluation pipeline covering manage_experiment.py / SubTestExecutor state machines, checkpoint/resume, judge logic, rate limits, path resolution, and rerun scripts. Use when: (1) retry logic conflates infra crashes with bad-grade terminal states, (2) checkpoint resume crashes with AssertionError or FileNotFoundError, (3) judge returns empty responses or prose instead of JSON, (4) --until stepping executes one extra transition or Ctrl+C has no effect, (5) T5 baseline inheritance fails despite parent tiers completing, (6) path resolution causes 100% silent agent failures, (7) rate limits hide inside stdout JSON instead of stderr, (8) rerun scripts crash with SubTestExecutor constructor errors or invalid checkpoint status, (9) judge validity checks are inconsistent across live/regeneration paths."
category: debugging
date: 2026-05-19
version: "1.0.0"
user-invocable: false
history: e2e-experiment-runner-bug-patterns.history
tags:
  - e2e
  - state-machine
  - checkpoint
  - resume
  - judge
  - rate-limit
  - path-resolution
  - manage-experiment
  - subtest-executor
  - tier-manager
  - haiku
  - threading
  - until-stepping
  - json-parse
  - rerun
---

# E2E Experiment Runner Bug Patterns

## Overview

| Field | Value |
| ----- | ----- |
| **Theme** | Bugs in E2E evaluation framework: checkpoint/resume state machines, judge validity, rate limits, path resolution, rerun scripts |
| **Primary files** | `scripts/manage_experiment.py`, `scylla/e2e/subtest_executor.py`, `scylla/e2e/runner.py`, `scylla/e2e/tier_manager.py`, `scylla/e2e/llm_judge.py`, `scylla/e2e/checkpoint.py`, `scylla/e2e/state_machine.py`, `scylla/e2e/rerun.py`, `scylla/e2e/regenerate.py` |
| **Shared vocabulary** | `manage_experiment.py`, `SubTestExecutor`, judge, tier, checkpoint, `run_states`, `completed_runs`, `worktree_cleaned`, `JUDGE_COMPLETE`, `best_subtest` |
| **Projects** | ProjectScylla, ProjectHephaestus |

## When to Use

1. Retry logic bug: a flag-gated retry conflates infra crashes (`run_states="failed"`) with bad-grade terminal states (`completed_runs="failed"`), discarding valid judge results or retrying them.
2. Checkpoint/resume crash: `AssertionError: tier_ctx.tier_config is not None`, `FileNotFoundError` on checkpoint temp files, or `run_result must be set before write_report` when resuming.
3. Judge returns empty responses (`stdout_len=1`) or prose instead of JSON (Haiku especially), causing zero-score results.
4. `--until <state>` runs one extra transition beyond the target; Ctrl+C / SIGTERM has no effect.
5. T5/T6 baseline inheritance fails with `Cannot build merged baseline: all required tiers failed` even though parent tiers completed.
6. Path resolution bug causes 100% silent agent failures: `exit_code=1`, 0 tokens, $0.00 cost, `cd: No such file or directory` in agent stderr.
7. Rate limits (HTTP 429) hide inside stdout JSON (`is_error: true`, `result: "You're out of extra usage"`) instead of stderr; retry handler never fires.
8. Post-hoc diagnosis: experiment data shows a "cliff" — early tiers pass, later tiers all fail with zero tokens.
9. Rerun script crashes with `SubTestExecutor.__init__() got an unexpected keyword argument` or `Invalid status: completed`.
10. Judge validity checks diverge between live execution and `regenerate.py`, causing bimodal failure distributions.

## Verified Workflow

### Quick Reference

```
Bug category      | Symptom                                   | File / function to fix
------------------|--------------------------------------------|-----------------------------------------------
Retry semantics   | Flag retries valid bad-grade runs          | _checkpoint_has_retryable_runs(), _reset_non_completed_runs()
Thread-safety     | ENOENT on checkpoint.tmp.*.json            | save_checkpoint() — add threading.Lock + tid
Resume tier_config| AssertionError on resume                   | runner.py — preload tier_config before action
_restore_run_ctx  | "run_result must be set before write_report"| _restore_run_context() — load judgment + run_result
Progressive resume| Works 1st time, crashes Nth resume         | _load_judge_result() path must match _has_valid_judge_result()
--until off-by-one| Agent runs when --until replay_generated   | advance_to_completion() — check post-advance state
Signal handlers   | Ctrl+C has no effect                       | terminal_guard(request_shutdown) — pass shutdown fn
TierState naming  | "No sub-test results to select from"        | reset to config_loaded, NOT subtests_running
T5 elif fallthrough| All required tiers failed despite complete  | elif → second if not best_subtest_id
T5 partial failure| T5 ValueError on first missing parent       | warn+continue, raise only if ALL tiers fail
Path resolution   | 100% failures, 0 tokens, "cd: not found"   | cwd=workspace.resolve() in subprocess calls
Rate limit stdout | 429 in stdout JSON, retry never fires       | scan both streams; is not None not or-chaining
Rate limit post-hoc| Cliff: later tiers 0 tokens/cost           | reset_rate_limited_runs.py --apply
Judge JSON parse  | Prose/partial JSON from code-block regex    | extract full block; retry with JSON reminder
Judge empty resp  | stdout_len=1, result="" but output_tokens>0 | --output-format stream-json + _extract_response_from_stream()
Judge variadic flag| Empty response; "Input must be provided"   | pipe via stdin: subprocess.run(cmd, input=prompt)
Judge prompt reuse| Bimodal failures in regenerate.py           | reuse saved judge_prompt.md before rebuilding
Judge validity    | Invalid judges in consensus; fallback=true  | is_valid sole gate; filter before _compute_judge_consensus()
Rerun constructor | TypeError: unexpected keyword argument       | SubTestExecutor(config, tier_manager, workspace_manager) only
Rerun checkpoint  | ValueError: Invalid status: completed        | status = "passed" if judge_passed else "failed"
```

### Bug Group 1 — Retry State Machine Semantics

**Key invariants** (`manage_experiment.py` / `scylla/e2e/checkpoint.py`):

```
run_states values:
  "failed"           → unhandled exception (infra crash) → ALWAYS retry
  "rate_limited"     → RateLimitError → ALWAYS retry
  "worktree_cleaned" → pipeline completed (any grade)   → NEVER retry

completed_runs values:
  "passed"          → judge_passed=True  → valid result, never retry
  "failed"          → judge_passed=False → valid bad-grade, NEVER retry
  "agent_complete"  → agent ran, judge never ran → in-progress
```

**Fix `_checkpoint_has_retryable_runs()`** — delete the second pass over `completed_runs`:

```python
# CORRECT: only run_states non-worktree_cleaned = retryable
def _checkpoint_has_retryable_runs(checkpoint_path):
    for subtests in data.get("run_states", {}).values():
        for runs in subtests.values():
            for state in runs.values():
                if state != "worktree_cleaned":
                    return True
    return False
```

**Fix `_reset_non_completed_runs()`** — never reset `worktree_cleaned` runs:

```python
for run_num_str, state in list(runs.items()):
    if state == "worktree_cleaned":
        continue  # Completed (any grade) — never reset
```

**Remove `--retry-errors` flag** — make retry unconditional; infra failures should always be retried.

### Bug Group 2 — Checkpoint Thread-Safety Race Condition

**File**: `scylla/e2e/checkpoint.py`

Multiple threads share the same PID; use PID + thread ID for temp files:

```python
import threading
_checkpoint_write_lock = threading.Lock()

def save_checkpoint(checkpoint, path):
    tid = threading.get_ident()
    temp_path = path.parent / f"{path.stem}.tmp.{os.getpid()}.{tid}{path.suffix}"
    with _checkpoint_write_lock:
        with open(temp_path, "w") as f:
            json.dump(checkpoint.model_dump(), f, indent=2)
        temp_path.replace(path)
```

### Bug Group 3 — Resume AssertionError (tier_config = None)

**File**: `scylla/e2e/runner.py`

On resume, `TierContext` is freshly constructed with `tier_config=None`. Add before `_build_tier_actions()`:

```python
_tier_resume_state = tsm.get_state(tier_id.value)
if _tier_resume_state not in (TierState.PENDING, TierState.COMPLETE, TierState.FAILED):
    tier_ctx.tier_config = self.tier_manager.load_tier_config(tier_id, ...)
    tier_ctx.tier_dir = self.experiment_dir / tier_id.value
```

**Critical**: `TierID.T0.value` is `"T0"` (uppercase). Checkpoint keys must match.

### Bug Group 4 — `_restore_run_context()` Missing Fields

**File**: `scylla/e2e/subtest_executor.py`

`_restore_run_context()` must load all fields needed for later stages:

```python
# Load judgment for states past JUDGE_COMPLETE
if is_at_or_past_state(run_state, RunState.JUDGE_COMPLETE) and ctx.judgment is None:
    if _has_valid_judge_result(ctx.run_dir):
        ctx.judgment = _load_judge_result(get_judge_dir(ctx.run_dir))

# Load run_result for states past RUN_FINALIZED
if is_at_or_past_state(run_state, RunState.RUN_FINALIZED) and ctx.run_result is None:
    run_result_path = ctx.run_dir / "run_result.json"
    if run_result_path.exists():
        ctx.run_result = _load_run_result(run_result_path)

# _load_run_result helper — filter extra keys (E2ERunResult is frozen)
def _load_run_result(run_result_path):
    data = json.loads(run_result_path.read_text())
    known_fields = set(E2ERunResult.model_fields.keys())
    return E2ERunResult.model_validate({k: v for k, v in data.items() if k in known_fields})
```

### Bug Group 5 — Progressive Resume Failures (File Path Mismatch)

Validation and loading must use the **same** file path constant:

```python
# WRONG: different constants
def _has_valid_judge_result(run_dir): return get_judge_result_file(run_dir).exists()  # → judge/result.json
def _load_judge_result(judge_dir): return open(judge_dir / "judgment.json")           # → WRONG name

# CORRECT: use same constant
def _load_judge_result(judge_dir):
    with open(judge_dir / RESULT_FILE) as f:  # same constant as _has_valid_judge_result
        return json.load(f)
```

Diagnostic: run experiment 4+ times; progressive failures indicate path mismatch, not state sync.

### Bug Group 6 — `--until` Off-By-One and Signal Handlers

**State naming**: state names represent what has **just been completed**. The action registered for a state runs WHILE IN that state to produce the NEXT state.

```
REPLAY_GENERATED state → action: stage_execute_agent() ← runs agent!
```

So `--until replay_generated` must stop BEFORE `stage_execute_agent()` fires.

**Fix** (all 4 state machines: `state_machine.py`, `experiment_state_machine.py`, `tier_state_machine.py`, `subtest_state_machine.py`):

```python
# BUGGY — checks pre-advance state (off-by-one)
current = self.get_state(...)
self.advance(...)
if current == until_state: break

# CORRECT — checks post-advance state
new_state = self.advance(...)
if new_state == until_state: break
```

**Signal handlers** (`scripts/manage_experiment.py`): `terminal_guard()` only installs handlers when `shutdown_fn is not None`:

```python
# BUGGY
with terminal_guard(): ...

# CORRECT
from scylla.e2e.runner import request_shutdown
with terminal_guard(request_shutdown): ...
```

### Bug Group 7 — TierState Naming Confusion (`--until` Stepping)

`TierState.SUBTESTS_RUNNING` does **NOT** mean "subtests are running." It means "subtests have finished, now select best." Actual subtest execution happens in the `CONFIG_LOADED → SUBTESTS_RUNNING` action.

**Fix reset target** (`scylla/e2e/runner.py`):

```python
# WRONG — subtests_running = "select best" action, not "run subtests"
self.checkpoint.tier_states[tier_id_str] = "subtests_running"

# CORRECT — config_loaded triggers the run-subtests action
self.checkpoint.tier_states[tier_id_str] = "config_loaded"
```

Also add `"subtests_running"` to the set of states that get reset, and reset failed `run_states` (not just subtest/tier states) in the STEP 3 failed-experiment handler.

### Bug Group 8 — T5 Baseline Inheritance Bugs

**Bug A: `elif` fallthrough when `result.json` has null `best_subtest`** (`tier_manager.py:build_merged_baseline()`):

```python
# BROKEN — elif never fires when result.json exists but best_subtest is null
if result_file.exists():
    best_subtest_id = tier_result.get("best_subtest")  # returns None
elif best_subtest_file.exists():   # NEVER REACHED

# FIXED
if result_file.exists():
    best_subtest_id = json.load(open(result_file)).get("best_subtest")
if not best_subtest_id and best_subtest_file.exists():
    best_subtest_id = json.load(open(best_subtest_file)).get("winning_subtest")
```

**Bug B: Hard `ValueError` on first missing parent** — use warn + continue, raise only if ALL tiers failed:

```python
failed_tier_ids = []
if not best_subtest_id:
    logger.warning(f"Cannot inherit from {tier_id.value}: skipping.")
    failed_tier_ids.append(tier_id.value)
    continue
if failed_tier_ids and len(failed_tier_ids) == len(inherit_from_tiers):
    raise ValueError(f"Cannot build merged baseline: all required tiers failed ({', '.join(failed_tier_ids)})")
```

### Bug Group 9 — Path Resolution (100% Silent Agent Failures)

**File**: `scylla/e2e/subtest_executor.py`

Relative `workspace` paths fail when `cwd` of parent process differs:

```python
# BEFORE (buggy)
result = subprocess.run(["bash", str(replay_script.resolve())], cwd=workspace, ...)
command_logger.log_command(..., cwd=str(workspace))

# AFTER (correct)
result = subprocess.run(["bash", str(replay_script.resolve())], cwd=workspace.resolve(), ...)
command_logger.log_command(..., cwd=str(workspace.resolve()))
```

**Diagnosis**: `cat results/*/T*/*/run_*/agent/stderr.log` — look for `cd: No such file or directory`. Exit code 1, 0 tokens, $0.00 cost, 0.0s duration.

### Bug Group 10 — Rate Limit Detection (stdout JSON)

Claude CLI emits 429 errors in stdout JSON (`is_error: true`, `result: "…"`), not stderr. Two distinct regex patterns:

```python
RATE_LIMIT_RE = re.compile(          # gh CLI form (stderr)
    r"(?:Limit reached|rate limit).*?resets\s+"
    r"(?P<time>\d{1,2}(?::\d{2})?(?:am|pm)?)\s*\((?P<tz>[^)]+)\)", re.IGNORECASE)

CLAUDE_USAGE_CAP_RE = re.compile(    # Claude CLI form (stdout JSON, with optional date prefix)
    r"resets\s+(?:(?P<date>[A-Za-z]+\s+\d{1,2})\s*,?\s+)?"
    r"(?P<time>\d{1,2}(?::\d{2})?(?:am|pm)?)\s*\((?P<tz>[^)]+)\)", re.IGNORECASE)
```

**`or`-chaining trap**: detectors return `0` (rate-limited, time unknown) as a meaningful sentinel. `0 or X == X` silently swallows the sentinel:

```python
# WRONG — 0 sentinel treated as "no rate limit"
reset = detect_rate_limit(stderr) or detect_claude_usage_cap(stdout)

# CORRECT
def _scan_quota_reset(*texts):
    for text in texts:
        for detect in (detect_rate_limit, detect_claude_usage_cap):
            epoch = detect(text)
            if epoch is not None:   # load-bearing: not truthiness
                return epoch
    return None
```

**Two-path detection** — Claude CLI sometimes returns exit 0 with `is_error: true`:

```python
try:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
except subprocess.CalledProcessError as e:
    reset = _scan_quota_reset(e.stderr or "", e.stdout or "")
    if reset is not None: _wait_until(reset); return retry()
    raise

data = json.loads(result.stdout or "{}")
if data.get("is_error"):
    reset = _scan_quota_reset(result.stderr or "", result.stdout or "")
    if reset is not None: _wait_until(reset); return retry()
    raise ClaudeError(data.get("result", "<empty>"))
```

### Bug Group 11 — Rate Limit Post-Hoc Diagnosis and Reset

**Failure signature** in `agent/result.json`:

```json
{"is_error": true, "result": "You've hit your org's monthly usage limit", "api_error_status": 429, "total_cost_usd": 0, "usage": {"input_tokens": 0, "output_tokens": 0}}
```

**Pattern**: early tiers succeed; later tiers show `exit_code=1, total_tokens=0, cost=0, duration ~8-10s`.

```bash
# Diagnose
for tier in T0 T1 T2 T3 T4 T5 T6; do
  limited=$(grep -rl "api_error_status.*429" results/<exp>/$tier/*/run_*/agent/result.json 2>/dev/null | wc -l)
  echo "$tier: $limited rate-limited"
done

# Reset (dry run first)
pixi run python scripts/reset_rate_limited_runs.py --experiment-dir results/<exp>
pixi run python scripts/reset_rate_limited_runs.py --experiment-dir results/<exp> --apply

# Re-run affected tiers
pixi run python scripts/manage_experiment.py run --config <exp> --tiers T3 T4 T5 T6
```

**Pitfall**: `worktree_cleaned + completed_runs="failed"` looks like a valid bad-grade; the system does NOT auto-retry it. Monthly quota exhaustion requires manual reset.

### Bug Group 12 — Judge JSON Parse Failures

**Bug A: Code-block regex stops at first `}`** (`scylla/judge/utils.py`):

```python
# BEFORE (non-greedy — stops at first })
code_block = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", output)

# AFTER (extract full block, then parse)
code_block = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", output)
if code_block:
    block_text = code_block.group(1).strip()
    if block_text.startswith("{"):
        try: return cast(dict, json.loads(block_text))
        except json.JSONDecodeError: pass
```

**Bug B: Haiku prose responses** — retry with JSON reminder:

```python
_json_reminder = "\n\n**IMPORTANT**: Respond with ONLY a valid JSON object. Start with `{` and end with `}`."
for attempt in range(3):
    prompt = judge_prompt if attempt == 0 else judge_prompt + _json_reminder
    stdout, stderr, result = _call_claude_judge(prompt, model, workspace)
    try: judge_result = _parse_judge_response(result); break
    except ValueError as e: last_parse_error = e
else: raise last_parse_error
```

### Bug Group 13 — Judge Empty Responses (CLI Bugs)

**Bug A: Variadic `--allowedTools` consumes positional prompt arg** — always pipe via stdin:

```python
cmd = ["claude", "--model", model, "--print", "--output-format", "stream-json", "--verbose",
       "--dangerously-skip-permissions", "--allowedTools", "",
       "--system-prompt-file", str(JUDGE_SYSTEM_PROMPT_FILE)]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200,
                        env={k: v for k, v in os.environ.items() if k != "CLAUDECODE"},
                        input=evaluation_context)  # stdin, not positional arg
```

**Bug B: Claude CLI v2.1.83 `result` field always empty** (upstream: anthropics/claude-code#39028) — switch to stream-json and parse `type:assistant` events:

```python
def _extract_response_from_stream(stream_output: str) -> str:
    text_parts: list[str] = []
    result_text = ""
    for line in stream_output.strip().splitlines():
        try: event = json.loads(line.strip())
        except json.JSONDecodeError: continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "text": text_parts.append(block["text"])
        elif event.get("type") == "result":
            result_text = event.get("result", "")
    return result_text if result_text.strip() else "".join(text_parts)
```

### Bug Group 14 — Judge Prompt Reuse in Regeneration

**File**: `scylla/e2e/regenerate.py`

Always prefer saved `judge_prompt.md` over rebuilding from workspace (workspace may have changed):

```python
saved_prompt_path = run_dir / "judge_prompt.md"
if saved_prompt_path.exists():
    judge_prompt = saved_prompt_path.read_text()
    stdout, stderr, result = _call_claude_judge(judge_prompt, judge_model, workspace)
    judge_result = _parse_judge_response(result)
else:
    logger.warning(f"Saved judge_prompt.md not found, rebuilding from workspace (may be inaccurate)")
    judge_result = run_llm_judge(workspace=workspace, judge_model=judge_model, ...)
```

### Bug Group 15 — Judge Validity Unification

**`is_valid` is the sole gate.** Old data: map `fallback: true` → `is_valid: False`:

```python
def _is_valid_judgment(data):
    is_valid = data.get("is_valid", True) is not False
    if data.get("fallback", False) is True: is_valid = False  # compat
    return "score" in data and is_valid
```

**Filter before consensus**:

```python
valid = [j for j in judges if j.score is not None and j.is_valid]  # was: j.score is not None
```

**Validate required fields early** (`_parse_judge_response()`):

```python
if "score" not in data:
    raise ValueError(f"Judge response missing 'score'. Keys: {list(data.keys())}")
```

**Test directory structure**: `_has_valid_judge_result(run_dir)` expects `run_dir/judge/result.json`, not a direct file path.

### Bug Group 16 — Rerun Script Errors

**File**: `scylla/e2e/rerun.py`

**Constructor fix** — `SubTestExecutor.__init__()` accepts only 4 parameters:

```python
# CORRECT
executor = SubTestExecutor(config=config, tier_manager=tier_manager, workspace_manager=workspace_manager)
```

Per-execution args (`tier_id`, `baseline`, `run_dir`, etc.) go to `_execute_single_run()` (9 params; note `subtest=`, not `subtest_config=`).

**Checkpoint status fix**:

```python
status = "passed" if run_result.judge_passed else "failed"
checkpoint.mark_run_completed(tier_id=..., subtest_id=..., run_number=..., status=status)
# Valid statuses: "passed", "failed", "agent_complete" — NOT "completed"
```

**T5 graceful degradation**: wrap `build_merged_baseline()` in try/except; on error, clean workspace and return None to skip the run.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| `--retry-errors` flag with `completed_runs` second pass | Added flag to make retry opt-in; second pass over `completed_runs` to catch judge failures | `completed_runs="failed"` means bad grade (valid result), not an infra crash — was retrying valid completed runs | Always distinguish `run_states` (pipeline state) from `completed_runs` (judge outcome); they encode different semantics |
| PID-only temp file for checkpoint | `checkpoint.tmp.{pid}.json` | Multiple threads share the same PID; concurrent writes collide; Thread B overwrites Thread A's data, then ENOENT on rename | Use PID + thread ID; hold a module-level lock across write+rename |
| Not preloading `tier_config` on resume | Assumed state machine would reconstruct context | `action_config_loaded()` asserts `tier_ctx.tier_config is not None` — freshly constructed `TierContext` has `tier_config=None` | On resume, detect non-PENDING/COMPLETE/FAILED states and preload tier config before actions run |
| Lowercase checkpoint keys (`"t0"`) | Used `tier_id.value.lower()` for checkpoint keys | `TierID.T0.value` is `"T0"` (uppercase); `get_tier_state()` returns `"pending"` for unknown keys, silently skipping the preload | Always use `tier_id.value` (uppercase) as checkpoint keys |
| Direct `E2ERunResult.model_validate(data)` | Load `run_result.json` directly into Pydantic model | `ConfigDict(frozen=True)` without `extra="ignore"` rejects extra keys (`process_metrics`, `progress_tracking`) | Filter to known fields before `model_validate` |
| Checking `--until` state before `advance()` | Captured pre-advance state, called `advance()`, then checked | Check fires too late — the action for the next state already ran | Check post-advance state: `new_state = self.advance(); if new_state == until_state: break` |
| `terminal_guard()` with no arguments | Called `with terminal_guard():` — handlers exist in code | `terminal_guard(shutdown_fn=None)` only installs handlers when `shutdown_fn is not None` | Pass the shutdown function explicitly: `terminal_guard(request_shutdown)` |
| Resetting tier to `subtests_running` for re-execution | Reset incomplete tiers to `SUBTESTS_RUNNING` state | `SUBTESTS_RUNNING` maps to "select best subtest" action, not "run subtests"; `subtest_results` was empty | Always reset to `config_loaded`; the action for that state runs the subtests |
| `elif` for best-subtest fallback | `if result_file.exists(): ... elif best_subtest_file.exists()` | `elif` never fires when `result.json` exists but `best_subtest` is null | Change `elif` to `if not best_subtest_id and best_subtest_file.exists()` |
| Passing positional prompt arg after `--allowedTools` | `["claude", "--allowedTools", "", "prompt_content"]` | `--allowedTools` is variadic; consumes all subsequent non-flag args as tool names; prompt never delivered | Pipe prompt via `input=` to `subprocess.run()`, not as positional arg |
| `detect_rate_limit(stderr) or detect_claude_usage_cap(stdout)` chaining | Chained detectors with `or` | Detector returning `0` (rate-limited, time unknown) treated as falsy; `0 or X == X` skips the sentinel | Use `is not None` comparison; `0` is a meaningful "rate-limited, retry in 5s" sentinel |
| Only checking `CalledProcessError` branch for rate limits | Assumed 429 always raises exit != 0 | Claude CLI sometimes returns exit 0 with `is_error: true` in JSON for usage caps | Scan both the exception branch and the success-path JSON for `is_error` |
| Assuming tier design problem for "cliff" failures | Investigated T4-T6 tier configs when later tiers failed | Aggregate data alone does not reveal root cause | Always inspect `agent/result.json` for `api_error_status: 429` before hypothesizing |
| Assuming aggregation bug for zero reports | Launched agents to explore report generation pipeline | Needed the actual error traceback, not architecture exploration | For crashes, get the traceback first; zero values with correct `run_result.json` = loading/path bug |
| Using `--output-format json` with stdin piping | Expected JSON `result` field to work | Claude CLI v2.1.83 regression: `result` field is empty regardless of format; `output_tokens > 0` but content discarded | Use `stream-json` and parse `type:assistant` events; forward-compatible via fallback to `result` field |
| Rebuilding judge prompt from workspace in `regenerate.py` | Reconstructed prompt from current workspace state | Workspace may differ from original (git worktree recreation, file modifications); produces inaccurate evaluations | Save and reuse `judge_prompt.md`; workspace-rebuilt prompts cause bimodal failure distributions |
| Separate `fallback` check from `is_valid` | `data.get("is_valid", True) and not data.get("fallback")` | Two code paths (live execution, regeneration) diverged: one filtered, one did not | `is_valid` is the sole gate; map `fallback=True` → `is_valid=False` for backward compatibility |
| Passing 11 params to `SubTestExecutor()` constructor | Passed `tier_id`, `baseline`, `checkpoint`, etc. to constructor | Constructor only accepts 4: `config`, `tier_manager`, `workspace_manager`, `adapter` | Per-execution args belong in `_execute_single_run()`, not the constructor |

## Results & Parameters

### State Machine Semantics Summary

| Field | Meaning | Retryable |
| ----- | ------- | --------- |
| `run_states="failed"` | Unhandled exception (infra crash) | Yes — always |
| `run_states="rate_limited"` | RateLimitError | Yes — always |
| `run_states="worktree_cleaned"` | Pipeline completed (any grade) | No — never |
| `completed_runs="passed"` | Judge passed | Valid result |
| `completed_runs="failed"` | Bad grade (NOT a crash) | Valid result |
| `completed_runs="agent_complete"` | Agent ran, judge skipped | In-progress |

### `--until` Semantics

`--until <state>` has **inclusive** semantics: the action that transitions INTO `until_state` IS executed; no further transitions run; checkpoint is left at `until_state`.

### Rate Limit Detector Contract

| Return | Meaning | Caller behavior |
| ------ | ------- | --------------- |
| `None` | No rate limit detected | Continue / normal error |
| `int > 0` | Reset epoch (Unix seconds) | Sleep until then, retry |
| `0` | Rate-limited, time unknown | Sleep 5s, retry |

### Key File Index

| File | Bugs covered |
| ---- | ------------ |
| `scripts/manage_experiment.py` | Retry flag removal, signal handlers |
| `scylla/e2e/checkpoint.py` | Thread-safety race condition |
| `scylla/e2e/runner.py` | Resume tier_config preload, `--until` reset target |
| `scylla/e2e/subtest_executor.py` | `_restore_run_context()`, path resolution, rate-limit two-path detection |
| `scylla/e2e/state_machine.py` (×4) | `advance_to_completion()` off-by-one |
| `scylla/e2e/tier_manager.py` | T5 `elif` fallthrough, partial failure graceful skip |
| `scylla/e2e/llm_judge.py` | Haiku retry, code-block regex, `PYTHONPYCACHEPREFIX`, score field validation |
| `scylla/e2e/stage_finalization.py` | `_call_judge_with_retry()`, prompt reload defense |
| `scylla/e2e/regenerate.py` | Saved prompt reuse, `is_valid` unification |
| `scylla/e2e/rerun_judges.py` | `is_valid` unification, `_is_valid_judgment()` |
| `scylla/e2e/rerun.py` | Constructor fix, checkpoint status, T5 graceful skip |
| `scylla/judge/utils.py` | Code-block regex full block extraction |
| `hephaestus/github/rate_limit.py` | `CLAUDE_USAGE_CAP_RE`, `_parse_reset_with_date` |
| `scripts/reset_rate_limited_runs.py` | Post-hoc rate-limit diagnosis and checkpoint reset |

### Verification Commands

```bash
# Unit tests
pixi run python -m pytest tests/unit/e2e/ tests/unit/judge/ -v

# Rate limit detection
pixi run ruff check hephaestus/ tests/
pixi run mypy
pixi run pytest tests/unit -v

# E2E smoke test
pixi run python scripts/manage_experiment.py run \
  --config tests/fixtures/tests/test-NNN --runs 1 --max-subtests 1 \
  --filter-subtest 00 --tiers T0 --fresh -v

# Check resume multiple times (progressive failure test)
# Resume 1-4 times; crash on Nth = file path mismatch bug
```

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectScylla | PRs #126, #142, #476, #1080, #1102, #1469, #1476, #1491, #1543, #1544, #1546, #1558 | Multiple dryrun/fullrun experiments |
| ProjectHephaestus | `feat/hephaestus-tidy` branch — automation pipeline rate-limit retry path | v1.1.0 rate-limit detection |
