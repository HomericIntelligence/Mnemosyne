---
name: runtime-resource-optimization-mojo-python
description: >-
  Runtime performance and resource management across Mojo SIMD/vectorisation
  and Python infrastructure. Use when: (1) SIMD-vectorizing element-wise tensor
  operations (NaN/Inf detection, gradient clipping, norm accumulation) in Mojo
  for 4-16x throughput; (2) validating Mojo language patterns (out self, mut,
  List, trait conformances, ownership transfer); (3) identifying SIMD
  optimization opportunities or checking memory safety in Mojo code; (4) fixing
  OOM crashes in multi-stage Claude CLI/NATS pipelines via session reuse and
  payload pruning; (5) preventing machine crashes from unbounded workspace
  accumulation or concurrent process limits in E2E runs; (6) adding
  module-level caching to eliminate redundant JSON schema file reads; (7)
  parallelizing I/O-bound subprocess loops with ThreadPoolExecutor; (8)
  validating checkpoint results before re-running expensive API calls; (9)
  deduplicating shared artifacts across E2E judge/run directories.
category: optimization
date: '2026-05-19'
version: '1.0.0'
user-invocable: false
history: runtime-resource-optimization-mojo-python.history
tags:
  - mojo
  - simd
  - vectorization
  - memory-safety
  - oom
  - nats
  - claude-cli
  - threadpoolexecutor
  - checkpoint
  - schema-cache
  - artifact-dedup
  - performance
  - python
  - wsl2
---

# Runtime Resource Optimization: Mojo and Python

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-19 |
| **Objective** | Synthesise 10 skills covering runtime efficiency at the compute layer (Mojo SIMD vectorization, memory safety) and system layer (OOM prevention, schema caching, artifact dedup, parallel I/O, checkpoint replay avoidance) |
| **Outcome** | Operational — all patterns verified across ProjectOdyssey and ProjectScylla |

## When to Use

1. SIMD-vectorizing element-wise tensor scanning in Mojo (NaN/Inf detection, gradient clipping, L2 norm)
2. Validating Mojo ownership, constructor, and trait-conformance patterns against project standards
3. Identifying SIMD optimization opportunities or reviewing memory safety in Mojo code
4. Fixing OOM crashes in multi-stage Claude CLI or NATS JetStream pipelines
5. Preventing machine crashes from unbounded workspace/process accumulation in parallel E2E runs
6. Eliminating redundant `json.load()` calls in `_validate_schema()` helpers via module-level cache
7. Converting sequential I/O-bound subprocess loops to `ThreadPoolExecutor` parallelism
8. Preventing wasted API spend by validating checkpoint results before expensive re-runs
9. Deduplicating shared artifacts (judge prompts, pipeline commands) across run/judge directories

## Verified Workflow

### Quick Reference

```mojo
# Mojo: SIMD NaN detection with early exit (manual loop — vectorize[] can't return early)
from sys import simd_width_of
from math import isnan
fn has_nan[dtype: DType](tensor: Tensor[dtype]) -> Bool:
    var ptr = tensor._data
    comptime simd_w = simd_width_of[dtype]()
    var i = 0
    while i + simd_w <= tensor.numel():
        if isnan(ptr.load[width=simd_w](i)).reduce_or():
            return True
        i += simd_w
    while i < tensor.numel():
        if isnan(ptr[i]): return True
        i += 1
    return False

# Mojo: SIMD counting (vectorize[] handles tail automatically)
from algorithm import vectorize
fn count_nan[dtype: DType](tensor: Tensor[dtype]) -> Int:
    var count = 0
    comptime simd_w = simd_width_of[dtype]()
    @parameter
    fn _count[width: Int](idx: Int) unified {mut}:
        count += Int(isnan(tensor._data.load[width=width](idx))
                     .cast[DType.uint8]().reduce_add())
    vectorize[simd_w](tensor.numel(), _count)
    return count

# Mojo: SIMD L2 norm (Float64 accumulator for numerical stability)
@always_inline
fn norm_sq_f32(tensor: AnyTensor) -> Float64:
    comptime simd_width = simd_width_of[DType.float32]()
    var ptr = tensor._data.bitcast[Float32]()
    var acc = Float64(0.0)
    @parameter
    fn _norm[width: Int](idx: Int) unified {mut}:
        var v = ptr.load[width=width](idx)
        acc += (v * v).reduce_add().cast[DType.float64]()
    vectorize[simd_width](tensor._numel, _norm)
    return acc

# Mojo: SIMD in-place scale and clamp
@always_inline
fn scale_f32(tensor: AnyTensor, scale: Float32):
    comptime w = simd_width_of[DType.float32]()
    var ptr = tensor._data.bitcast[Float32]()
    @parameter
    fn _scale[width: Int](idx: Int) unified {mut}:
        ptr.store[width=width](idx, ptr.load[width=width](idx)
                               * SIMD[DType.float32, width](scale))
    vectorize[w](tensor._numel, _scale)
```

```bash
# Mojo: find SIMD, ownership, and pattern violations
grep -n "for.*in.*range\|@unroll\|@vectorize" *.mojo     # SIMD candidates
grep -n "var .* = .*\^" *.mojo | head -20                  # ownership transfer
grep -n "fn __init__.*mut self\|fn __init__.*var self" *.mojo  # constructor violations
grep -n "inout\|@value\|DynamicVector" *.mojo              # deprecated patterns
mojo package shared                                         # validate full package
```

```python
# Python: session reuse for Claude CLI (avoids 500MB–1GB per-process footprint)
import uuid, subprocess
session_id = str(uuid.uuid4())
subprocess.run(["claude", "-p", prompt, "--session-id", session_id,
                "--output-format", "json"],
               capture_output=True, text=True, stdin=subprocess.DEVNULL)
# resume on subsequent iterations — never spawn a new process per loop
subprocess.run(["claude", "-p", prompt, "--resume", session_id,
                "--output-format", "json"],
               capture_output=True, text=True, stdin=subprocess.DEVNULL)

# Python: prune NATS payloads between pipeline stages
def prune_task_data(task_data: dict, next_stage: str) -> dict:
    core_keys = {"task_id", "repo", "issue", "branch"}
    pruned = {k: v for k, v in task_data.items() if k in core_keys}
    stage_key = f"{next_stage}_input"
    if stage_key in task_data:
        pruned[stage_key] = task_data[stage_key]
    return pruned

# Python: module-level schema cache
from pathlib import Path
from typing import Any
import json, jsonschema
_SCHEMAS_DIR = Path(__file__).parent.parent.parent / "schemas"
_SCHEMA_CACHE: dict[str, dict[str, Any]] = {}

def _validate_schema(data: dict[str, Any], schema_name: str, path: Path) -> None:
    key = f"{schema_name}.schema.json"
    if key not in _SCHEMA_CACHE:
        with open(_SCHEMAS_DIR / key) as f:
            _SCHEMA_CACHE[key] = json.load(f)
    jsonschema.validate(data, _SCHEMA_CACHE[key])

# Python: checkpoint validation before expensive re-run
def _has_valid_result(result_dir: Path) -> bool:
    f = result_dir / "result.json"
    if not f.exists(): return False
    try:
        data = json.loads(f.read_text())
        return all(k in data for k in ["exit_code", "token_stats", "cost_usd"])
    except (json.JSONDecodeError, KeyError, OSError):
        return False

# Python: ThreadPoolExecutor for I/O-bound parallel subprocess loops
import threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

@dataclass
class _TaskResult:
    task: object
    success: bool
    error: str | None = None

def _run_safe(task, *args, **kwargs) -> _TaskResult:
    try:
        return _TaskResult(task=task, success=_run_task(task, *args, **kwargs))
    except Exception as e:
        return _TaskResult(task=task, success=False, error=str(e))

def process_parallel(tasks, parallel: int = 1, *args, **kwargs):
    lock = threading.Lock()
    success = failed = 0
    if parallel <= 1 or len(tasks) <= 1:
        for t in tasks:
            if _run_task(t, *args, **kwargs): success += 1
            else: failed += 1
    else:
        start = time.time()
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            futures = {pool.submit(_run_safe, t, *args, **kwargs): t for t in tasks}
            for i, fut in enumerate(as_completed(futures), 1):
                r = fut.result()
                with lock:
                    if r.success: success += 1
                    else: failed += 1
```

### Mojo SIMD Vectorization

**Pattern selection**:

- Boolean detection (`has_nan`, `has_inf`): use **manual `while` loop** — `vectorize[]` closures
  cannot `return` from the outer function, so early exit requires a manual loop.
- Counting (`count_nan`, `count_inf`): use **`vectorize[]`** — no early exit needed, handles tail
  elements automatically.
- Arithmetic reduction (norm, scale, clamp): use **`vectorize[]`** with `unified {mut}` closure.

**SIMD width selection**:

- `comptime simd_w = simd_width_of[dtype]()` — `float32` → 8 (AVX-256), `float64` → 4 (AVX-256)
- Dispatch on `_dtype` in public function; scalar fallback for exotic dtypes.

**AnyTensor bitcast pattern** — `AnyTensor._data` is `UnsafePointer[UInt8]`; bitcast once outside
the loop: `var ptr = tensor._data.bitcast[Float32]()`. Eliminates per-element dtype dispatch and
offset calculation that `_get_float64(j)` / `_set_float64(j, val)` perform on every call.

### Mojo Language Pattern Validation

**Constructor patterns**:

- Correct: `fn __init__(out self, ...)`, `fn __moveinit__(out self, deinit existing: Self)`,
  `fn __copyinit__(out self, existing: Self)`
- Wrong: `fn __init__(mut self, ...)` or `fn __init__(var self, ...)`

**Ownership patterns**:

- Use `^` transfer operator: `return self.data^` (not `return self.data` for List/Dict)
- `fn take(var data: List[Int])` takes ownership explicitly

**Trait conformances**: `struct Data(Copyable, Movable)` — never omit `Movable` from `Copyable`;
`ImplicitlyCopyable` only for trivial types.

**Validation commands**: Use `mojo package shared` (not `mojo build` on individual library files —
relative imports are only valid inside package structure).

### Mojo Memory Safety Validation

Key checks: all pointers allocated and size-tracked before use; `List`/`Dict` initialized via
`append`/`insert`, not direct index assignment; no use-after-move (variable used after `^` transfer);
explicit bounds checks before pointer dereference; RAII — avoid manual `free()`.

### Python OOM / Resource Management

**Claude CLI pipeline OOM (NATS)**:

1. Session reuse: `--session-id <uuid>` on first call, `--resume <id>` on subsequent calls.
2. Always pass `stdin=subprocess.DEVNULL` — `capture_output=True` alone causes stdin blocking.
3. Prune NATS payloads between stages (see `prune_task_data` above).
4. Set NATS stream retention: `max_age=3600s`, `max_bytes=50MB`.
5. Set `max_reconnect_attempts` to 3–5 (not `-1` — infinite retries hang on initial connect).
6. Set `mem_limit` per container in `docker-compose.yml` (256M worker, 128M NATS).

**E2E workspace / process exhaustion**:

1. Eager workspace cleanup: remove `run_passed` guard from `stage_cleanup_worktree` — clean ALL
   workspaces after judging; add `--keep-failed-workspaces` debug flag.
2. Workspace semaphore: `threading.Semaphore(cpu_count * 2)` in create/cleanup stages.
3. Agent semaphore: `threading.Semaphore(min(threads, cpu_count))` around `stage_execute_agent`
   and `stage_execute_judge`.
4. Remove `--allowedTools Read,Glob,Grep` from judge CLI — all context is already in the prompt.
5. Log RAM/disk at startup; periodic checks in heartbeat thread.

**On WSL2**: memory exhaustion kills the VM silently — no OOM traces in `dmesg`. The Windows host
kills the VM before the Linux OOM killer runs.

### Python Schema Cache

Place `_SCHEMA_CACHE: dict[str, dict[str, Any]] = {}` immediately after `_SCHEMAS_DIR`. Use the
full filename as cache key (`f"{schema_name}.schema.json"`). In tests, clear
`loader_module._SCHEMA_CACHE` in `setup_method` to prevent ordering dependencies. Use
`additionalProperties: false` schemas carefully — read the schema before writing test fixtures.

### Python ThreadPoolExecutor Parallelism

- `parallel <= 1 or len(tasks) <= 1`: skip pool overhead for sequential case.
- Safe wrapper catches all exceptions: prevents one worker failure from poisoning the pool.
- `threading.Lock()` protects shared stats counters (minimize critical section).
- Post-processing AFTER `ThreadPoolExecutor.__exit__()` — guarantees all workers are done.
- Use `ThreadPoolExecutor` for I/O-bound ops (subprocesses, network); use `ProcessPoolExecutor`
  for CPU-bound.

### Python Checkpoint Validation

Validate **content**, not just **existence**: check required fields (`exit_code`, `token_stats`,
`cost_usd`) and catch all exceptions. Log `[SKIP]` prefix when skipping completed work.

### Python Artifact Deduplication

- Pipeline commands (`run_all.sh`, etc.) belong at run level, not per-judge directory.
- Judge prompt: write once to `run_XX/judge_prompt.md`, reference via `../../judge_prompt.md`.
- Agent prompt: extract to `prompt.md`, reference in replay script.
- Task prompt: copy to experiment directory (not symlink to source tree — symlinks to mutable
  sources break reproducibility).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| `vectorize[]` for `has_nan` | Used `vectorize[]` closure with a `found` flag | Cannot `return True` from inside a `vectorize[]` closure to exit the outer function | Use manual SIMD `while` loop when early exit is needed |
| `List[Int](2, 8)` constructor | Tried to construct List with positional args | Mojo 0.26.1 `List[Int]` has no multi-arg constructor | Use `var s = List[Int](); s.append(n)` or list literal `[n]` |
| Lowercase docstring in Mojo | `"""has_nan returns...` | `mojo --Werror` rejects docstrings not starting with capital or non-alpha | Always capitalize the first word of Mojo docstrings |
| `mojo format` on `comptime` | Ran formatter on files using `comptime` keyword | Formatter crashes: `'_python_symbols' object has no attribute 'comptime_assert_stmt'` | Use `mojo-format-compat.sh` wrapper; `comptime` not yet supported by formatter |
| `--no-input` flag on Claude CLI | Passed `--no-input` to prevent interactive prompts | Flag does not exist; all stages produced empty output | Use `stdin=subprocess.DEVNULL` instead |
| `capture_output=True` without `DEVNULL` | Captured stdout/stderr but did not redirect stdin | Subprocess blocks waiting for stdin indefinitely | Always pair `capture_output=True` with `stdin=subprocess.DEVNULL` |
| `{**task_data, "feedback": result}` dict unpack | Merged all previous stage data into NATS publish | Payload grows exponentially across 5 stages × 5 iterations | Prune payloads: carry only core keys + what next stage needs |
| No NATS retention policies | Used default JetStream stream config | Messages accumulate indefinitely, compounding memory pressure | Always set `max_age` + `max_bytes` on every JetStream stream |
| `max_reconnect_attempts=-1` | Set unlimited reconnect attempts for resilience | `-1` means unlimited during initial `connect()` — hangs forever when NATS is down | Use finite count (3–5) for initial connect |
| Running `--threads 15` unguarded | All 7 tests with unbounded concurrency | 7 concurrent `claude` processes + 2700+ workspaces exhausted 16GB RAM and 1TB disk | Limit concurrent subprocesses to `min(threads, cpu_count)` |
| Checking `dmesg` for OOM killer on WSL2 | Expected Linux OOM traces | WSL2 VM killed by Windows host silently — no kernel logs survive | On WSL2, memory exhaustion kills the VM; check Windows Event Log instead |
| `_pipeline_lock` only | Serialized build pipeline, assumed that was enough | Lock only covers `mojo build`, not `claude` CLI processes (main RAM consumers) | Need separate semaphores for different resource types |
| Keeping failed workspaces for debugging | `stage_cleanup_worktree` only cleaned passing runs | Failed runs (majority) accumulated 187GB of 1.2GB workspaces | Workspace diff is captured at `DIFF_CAPTURED` — workspace not needed after judging |
| Vectorizing `compute_gradient_statistics` | Considered SIMD for the statistics function | Mixed concerns (NaN/Inf checking requires per-element branches); function is called infrequently | Prioritize hot-path functions called every training step |
| Checking file existence only for checkpoint | `if agent_result_file.exists(): load()` | File may exist but be partial/corrupt from interrupted run | Validate required fields, catch all parse errors |

## Results & Parameters

### Mojo SIMD Performance

| Metric | Scalar | SIMD (width=8, float32) | Improvement |
| -------- | -------- | ------------------------- | ------------- |
| Iterations per 1M elements (detection) | ~1,000,000 | ~125,000 | ~8× fewer |
| Iterations per 10M elements (gradient) | ~10,000,000 | ~1,250,000 | ~8× fewer |
| Memory accesses per training step | 20M+ scalar | 2.5M SIMD | ~8× reduction |
| AVX-256 SIMD width — float32 | — | 8 lanes | — |
| AVX-256 SIMD width — float64 | — | 4 lanes | — |

### Python Resource Profiles

```yaml
# Claude CLI pipeline (NATS)
claude_cli_per_process:    "500MB – 1GB"
pipeline_stages_per_task:  16  # 1 plan + 5 test + 5 implement + 5 review + 1 ship
effective_processes_with_session_reuse: 5  # plan, test, implement, review, ship
nats_stream_max_age:       3600s
nats_stream_max_bytes:     50MB
docker_worker_mem_limit:   256M
docker_nats_mem_limit:     128M
dry_run_duration:          ~2 seconds
dry_run_memory:            26.9 MB (flat)

# E2E workspace / process limits (16GB WSL2)
threads:                   15
max_concurrent_agents:     6   # claude CLI process limit
max_concurrent_workspaces: auto (cpu_count * 2)
workspace_size_mojo_repo:  ~1.2 GB per git worktree
mojo_build_memory:         ~1–2 GB (serialized under _pipeline_lock)
```

### Artifact Deduplication Savings

| Optimization | Before | After | Savings per Run |
| ------------- | -------- | ------- | ----------------- |
| Judge prompts | 7KB × N judges | 7KB × 1 | ~7KB × (N-1) |
| Pipeline commands | 5 files × N judges | 5 files × 1 | ~5 files × (N-1) |
| Agent prompts | Inlined in replay.sh | Extracted to prompt.md | Cleaner diffs |

### Schema Cache

- Cache dict type: `dict[str, dict[str, Any]]`
- Cache key: `f"{schema_name}.schema.json"` (full filename)
- Test isolation: `loader_module._SCHEMA_CACHE.clear()` in `setup_method`
- Note: `ruff` auto-removes unused imports on first pre-commit run — expect one hook failure,
  re-run passes.

### ThreadPoolExecutor Speedup

| Workers | Expected Speedup | Use Case |
| --------- | ------------------ | ---------- |
| 1 | 1× (sequential, zero overhead) | Default, debugging |
| 3–6 | 3–6× | LLM API calls with rate limits |
| 10+ | 10×+ | High-throughput file I/O |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | Issue #4910 — SIMD-vectorize numerical safety hot path | PR #5119 |
| ProjectOdyssey | Issue #4911 — SIMD-vectorize gradient clipping | PR #5120 — 4 functions via 6 SIMD helpers, 13 tests |
| ProjectScylla | PR #1461, issue #1437 — module-level schema cache | `scylla/config/loader.py` |
| ProjectScylla | PR #138 — checkpoint result validation | Skip completed agent/judge runs |
| ProjectScylla | PR #176 — E2E artifact deduplication | `refactor/judge-prompt-consolidation` |
| Odysseus | 2026-04-04 — NATS pipeline OOM | Dry-run validated at 26.9 MB flat |
| ProjectScylla | haiku-2 experiment — E2E resource exhaustion | WSL2 16GB, 2,737 workspaces, 187GB |
