---
name: process-metrics-pipeline-integration
description: "Use when: (1) emitting R_Prog, CFP, strategic_drift, or pr_revert_rate\
  \ from a stage-based E2E runner into run_result.json; (2) loading process_metrics\
  \ from run_result.json into the ProjectScylla loader → dataframes → figures stack;\
  \ (3) persisting progress_steps/change_results through crash-resume cycles; (4)\
  \ surfacing process metrics in per-run report.md and report.json; (5) exporting\
  \ mean_r_prog / mean_cfp / mean_pr_revert_rate to summary.json; (6) adding metric\
  \ aggregations to build_subtests_df() or model_comparison(); (7) adding figure functions\
  \ to process_metrics.py and wiring them into generate_figures.py; (8) extending\
  \ compute_statistical_results() with new per-run process metrics; (9) renaming\
  \ figure functions to the fig{NN}_description convention."
category: evaluation
date: 2026-05-19
version: 1.0.0
user-invocable: false
history: process-metrics-pipeline-integration.history
tags:
  - process-metrics
  - r-prog
  - cfp
  - strategic-drift
  - pr-revert-rate
  - run-result
  - analysis-pipeline
  - figures
  - statistical-tests
  - ProjectScylla
---
# process-metrics-pipeline-integration

Canonical skill for the full lifecycle of process-level run metrics (R_Prog, CFP,
strategic_drift, pr_revert_rate) through the ProjectScylla stack: emit → persist →
report → load → dataframes → figures → statistical export.

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-19 |
| **Project** | ProjectScylla |
| **Issues** | #1133, #1134, #1135, #1136, #1179, #1181, #1186, #1189, #1198, #1199 |
| **Objective** | End-to-end integration of process metrics from E2E runner through analysis pipeline |
| **Outcome** | Success — all nine sub-workflows verified across 13 merged PRs |

## When to Use

Use this skill when:

1. **Emitting process_metrics** — populating `process_metrics`, `progress_tracking`, and
   `changes` blocks in `run_result.json` from a stage-based E2E runner
2. **Resuming crashed runs** — reloading `progress_steps` / `change_results` when a run
   crashes between `DIFF_CAPTURED` and `RUN_FINALIZED`
3. **Surfacing in per-run report** — adding a `## Process Metrics` table to `report.md`
   and a `process_metrics` key to `report.json`
4. **Loader integration** — adding `r_prog`, `cfp`, `strategic_drift`, `pr_revert_rate`
   optional fields to `RunData` with two-path extraction (pre-computed block → raw tracking)
5. **Exporting to summary.json** — wiring `mean_r_prog`, `mean_cfp`, `mean_pr_revert_rate`
   into `overall_stats`, `by_model`, and `by_tier` sections
6. **Aggregation layer** — adding mean/median/std columns to `build_subtests_df()`,
   `tier_summary()`, and MultiIndex `.agg()` in `model_comparison()`
7. **Adding figures** — implementing a new figure function in
   `scylla/analysis/figures/process_metrics.py` and wiring it into `generate_figures.py`
8. **Statistical tests** — extending `compute_statistical_results()` with normality,
   omnibus, pairwise, and effect-size tests for process metrics
9. **Renaming figures** — standardizing ad-hoc figure names to the `fig{NN}_description`
   convention atomically across all four touch points

## Verified Workflow

### Quick Reference

```
Phase 1 (Emit):     stages.py — _get_diff_stat, _build_change_results,
                    _build_progress_steps, stage_capture_diff, stage_finalize_run
Phase 2 (Resume):   _load_process_metrics_from_run_result() + is None guard
Phase 3 (Report):   run_report.py — _generate_process_metrics_section() + NaN guard
Phase 4 (Load):     loader.py — RunData fields + two-path extraction (lazy import)
Phase 5 (Export):   export_data.py — dropna().empty pattern for overall/model/tier
Phase 6 (Agg):      dataframes.py — build_subtests_df / tier_summary / model_comparison
Phase 7 (Figures):  process_metrics.py + generate_figures.py FIGURES registry
Phase 8 (Stats):    export_data.py — extend metric_cols / metric_configs lists
Phase 9 (Rename):   4-file atomic rename: module → registry → test_figures → test_integration
```

### Phase 1: Emit process_metrics from E2E Runner

**Key architecture**: derive metrics **mechanically from git diff** output, not via LLM calls.

Two-phase population in the stage pipeline:

```
AGENT_COMPLETE → stage_capture_diff()   # populate ctx.progress_steps, ctx.change_results
JUDGE_COMPLETE → stage_finalize_run()   # finalize with judge score, write run_result.json
```

Add two optional fields to `RunContext` (use `None` sentinel, not `[]`):

```python
@dataclass
class RunContext:
    progress_steps: list[ProgressStep] | None = None
    change_results: list[ChangeResult] | None = None
```

`_get_diff_stat()` — exclude framework files, return `{}` on any error, parse marker
string (`++---`) by counting `+`/`-` chars for approximate relative weights.

`stage_finalize_run()` — extend the serialized dict after `to_dict()` (never modify the
frozen Pydantic model):

```python
result_dict = run_result.to_dict()
result_dict["process_metrics"] = {
    "r_prog": pm.r_prog, "strategic_drift": pm.strategic_drift,
    "cfp": pm.cfp, "pr_revert_rate": pm.pr_revert_rate,
}
result_dict["progress_tracking"] = [dataclasses.asdict(s) for s in final_progress_steps]
result_dict["changes"] = [dataclasses.asdict(c) for c in final_change_results]
```

`run_result.json` schema (fields are `float`, range `[0, 1]`):

```json
{
  "process_metrics": {"r_prog": 0.85, "strategic_drift": 0.15, "cfp": 0.0, "pr_revert_rate": 0.0},
  "progress_tracking": [{"step_id": "src/module.py", "weight": 0.7, "completed": true, "goal_alignment": 0.85}],
  "changes": [{"change_id": "src/module.py", "succeeded": true, "caused_failure": false, "reverted": false}]
}
```

### Phase 2: Resume Guard

When a run crashes between `DIFF_CAPTURED` and `RUN_FINALIZED`, `ctx.progress_steps` and
`ctx.change_results` are `None` on resume. Add a loader helper and guard at the top of
`stage_finalize_run()`:

```python
if ctx.progress_steps is None or ctx.change_results is None:
    loaded_steps, loaded_changes = _load_process_metrics_from_run_result(ctx.run_dir)
    if ctx.progress_steps is None:
        ctx.progress_steps = loaded_steps
    if ctx.change_results is None:
        ctx.change_results = loaded_changes
```

**Critical**: use `is None`, not `not ctx.field` — an empty list `[]` (agent made no
changes) must NOT be overwritten by disk data.

The loader helper returns `(None, None)` on any error, letting the `or []` fallbacks in
`stage_finalize_run` handle the graceful-empty case naturally.

### Phase 3: Surface in Per-Run Report

`stage_write_report()` reads `process_metrics` from the already-written `run_result.json`:

```python
process_metrics: dict[str, Any] | None = None
try:
    with open(ctx.run_dir / "run_result.json") as f:
        run_result_data = json.load(f)
    process_metrics = run_result_data.get("process_metrics")
except (OSError, json.JSONDecodeError, KeyError):
    pass
```

Add NaN-safe helpers in `run_report.py`:

```python
import math

def _format_process_metric_value(val: Any) -> str:
    if val is None:
        return "N/A"
    try:
        f = float(val)
        return "N/A" if math.isnan(f) else f"{f:.4f}"
    except (TypeError, ValueError):
        return "N/A"
```

**JSON serialization guard** — `json.dumps` will emit `NaN` for `float("nan")`, which is
invalid JSON. Guard with `math.isnan()` and replace with `None` before writing `report.json`.

Do **NOT** read `process_metrics` from `ctx.run_result` — the `E2ERunResult` dataclass
does not carry these fields; they live only in the JSON file.

### Phase 4: Loader Integration

Add optional fields to `RunData` (`float | None = None`) and extract with two-path fallback:

```python
process_metrics_data = result.get("process_metrics")
if process_metrics_data and isinstance(process_metrics_data, dict):
    # Path 1: pre-computed block (priority)
    r_prog_val = _extract_process_float("r_prog")
    ...
else:
    # Path 2: compute from raw tracking arrays (lazy import)
    from scylla.metrics.process import (  # noqa: PLC0415
        ChangeResult, ProgressStep, ProgressTracker,
        calculate_cfp, calculate_pr_revert_rate,
        calculate_r_prog, calculate_strategic_drift,
    )
    ...
```

Lazy import inside the `else` branch avoids startup overhead and circular import risk.
Use `# noqa: PLC0415` to suppress ruff's "import not at top of file" warning.

Pass nullable columns through to `build_runs_df()` unchanged — downstream code uses
`.dropna(subset=["r_prog"])` before analysis.

**TokenStats gotcha** in tests: `total_tokens` is a `@property`, not a constructor param.
Use `TokenStats(input_tokens=..., output_tokens=..., cache_creation_tokens=..., cache_read_tokens=...)`.
Import from `scylla.e2e.models`, not from `loader`.

### Phase 5: Export to summary.json

Columns already exist in `runs_df` — only `export_data.py` + fixtures + tests need changing.

Always use `dropna()` + empty guard + `float()` wrapping:

```python
"mean_r_prog": float(runs_df["r_prog"].dropna().mean())
               if not runs_df["r_prog"].dropna().empty else None,
```

Apply the same pattern in `by_model` and `by_tier` loops. Extract slices before the dict
literal to avoid repeated computation:

```python
model_r_prog = model_df["r_prog"].dropna()
"mean_r_prog": float(model_r_prog.mean()) if not model_r_prog.empty else None,
```

Never use bare `.mean()` without `dropna()` — if all rows are NaN the result is `np.nan`,
which is not JSON-serializable. Use `dropna().empty` (not `np.isnan`) since it works for
any dtype.

Pre-commit: ruff auto-reformats long lines on the **first** pass; run twice — first
reformats, second validates.

### Phase 6: Aggregation Layer (dataframes.py)

Add to `compute_subtest_stats()`, `compute_tier_stats()`, and `model_comparison()`.

**Flat column names** (subtests/tier): `mean_r_prog`, `median_r_prog`, `std_r_prog`, etc.
Use pandas' default `skipna=True` — no explicit NaN guards needed.

**MultiIndex columns** (model_comparison): `("r_prog", "mean")` tuples from `.agg()`.
Tests must check `(metric, agg) in list(result.columns)`.

Fixture density: `~70%` populated rows to exercise both real-value and NaN paths:

```python
r_prog = np.random.uniform(0.0, 1.0) if np.random.random() < 0.7 else np.nan
```

The `sample_subtests_df` fixture contains a **local copy** of `compute_subtest_stats()`
that must mirror production exactly — update both together.

### Phase 7: Adding Figures

Two chart patterns in `process_metrics.py`:

| Pattern | When | Examples |
| --------- | ----- | -------- |
| `mark_boxplot()` | Distribution value (bounded [0,1]) | `r_prog`, `strategic_drift` |
| `mark_bar()` + `mark_errorbar()` | Rate/frequency | `cfp`, `pr_revert_rate` |

All figure functions share the same signature and guards:

```python
def fig_<name>(runs_df: pd.DataFrame, output_dir: Path, render: bool = True) -> None:
    if "<col>" not in runs_df.columns:
        logger.warning("..."); return
    data = _filter_process_data(runs_df[["tier", "agent_model", "<col>"]], "<col>")
    if data.empty:
        return
    ...
    save_figure(chart, "fig_<name>", output_dir, render)
```

Register in `generate_figures.py` FIGURES dict under category `"tier"` (dispatches `runs_df`):

```python
"fig_r_prog_by_tier": ("tier", fig_r_prog_by_tier),
```

Three required smoke tests per figure: (1) output file exists, (2) missing column → no
file, (3) all-null column → no file.

**Known import quirk**: Tests in `test_figures.py` that import from `scripts.generate_figures`
fail with `ModuleNotFoundError` when run in isolation (need `PYTHONPATH=scripts`). Run as
`tests/unit/analysis/` or `tests/` to trigger the correct `sys.path` setup.

### Phase 8: Statistical Tests

Process metrics are added to all four sections of `compute_statistical_results()`:

```python
# Normality: extend metric_cols list + column-existence guard
metric_cols = ["score", "impl_rate", "cost_usd", "duration_seconds",
               "r_prog", "cfp", "pr_revert_rate"]
for metric in metric_cols:
    if metric not in tier_data.columns: continue  # backward compat

# Omnibus: conditionally append to metric_configs
for process_metric in ("r_prog", "cfp", "pr_revert_rate"):
    if process_metric in model_runs.columns:
        metric_configs.append((process_metric, [...]))

# Pairwise and effect_sizes: extend inner tuple + column guard
for metric in ("impl_rate", "duration_seconds", "r_prog", "cfp", "pr_revert_rate"):
    if metric not in model_runs.columns: continue
```

**`strategic_drift` is excluded from statistical tests** — it is a tier-level metric, not
per-run. Include only `r_prog`, `cfp`, `pr_revert_rate`.

Process metrics use **consecutive-tier pairs only** — do NOT add a first→last overall
contrast (that pattern is reserved for `pass_rate` only).

**Power simulation mock** (required for test speed):

```python
@pytest.fixture(autouse=True)
def mock_power_simulations():
    with (
        patch("scylla.analysis.stats.mann_whitney_power", return_value=0.8),
        patch("scylla.analysis.stats.kruskal_wallis_power", return_value=0.75),
    ):
        yield
```

Without this mock, Monte Carlo iterations run at ~2+ minutes per test.

### Phase 9: Renaming Figures to fig{NN} Convention

All figure names must match `fig{NN}_{description}`. Find the current ceiling:

```bash
grep -E '"fig[0-9]+_' scripts/generate_figures.py | grep -oE 'fig[0-9]+' | sort -V | tail -1
```

A rename touches exactly **4 files in a single commit**:

| File | What changes |
| ------ | ------------- |
| `scylla/analysis/figures/{module}.py` | Function def, `save_figure()` name arg, logger strings, docstring |
| `scripts/generate_figures.py` | Import names, FIGURES dict keys and values |
| `tests/unit/analysis/test_figures.py` | Registry assertions, smoke test names, imports, `.vl.json` filenames |
| `tests/unit/analysis/test_process_metrics_integration.py` | Smoke test names, imports, call sites, `.vl.json` filenames |

Do all four files atomically — partial renames cause import errors during test collection.

Verify zero stale references:

```bash
grep -rn "fig_r_prog_by_tier\|fig_cfp_by_tier" . --include="*.py"
# Expected: no matches
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| `patch("scylla.e2e.stages.detect_rate_limit")` | Patching detect_rate_limit at importing module | `AttributeError` — lazy import inside stage function body is not a module attribute | Patch the source module: `patch("scylla.e2e.rate_limit.detect_rate_limit")` |
| Counting insertions from stat number | Parsing the integer from `git diff --stat` (`5 ++---`) | `--stat` shows marker strings, not exact numbers | Count `+` / `-` chars in the marker string for relative weights |
| `not ctx.field` guard in resume check | Checking truthiness of list field | Empty list `[]` (no changes) is falsy → incorrectly triggers reload from disk | Always use `is None` to preserve valid `[]` from prior stage |
| `json.dumps(float("nan"))` | Serializing NaN process metrics to JSON | Emits literal `NaN` which is not valid JSON | Guard with `math.isnan()` and replace with `None` before `json.dumps` |
| Eager import of `scylla.metrics.process` | Module-level import in `loader.py` | Adds startup overhead and circular import risk | Lazy import inside the `else` branch with `# noqa: PLC0415` |
| `dict` without type params in helpers | Untyped `-> dict` return annotation | mypy `[type-arg]` error in strict mode | Use `dict[str, Any]` with `from typing import Any` |
| `TokenStats(total_tokens=...)` in tests | Passing `total_tokens` to constructor | It's a `@property`, not a constructor param | Only pass `input_tokens`, `output_tokens`, `cache_creation_tokens`, `cache_read_tokens` |
| Single pre-commit run on export_data.py | One `pre-commit run` pass | Ruff reformats long lines on first pass → exits with status 1 | Run twice: first reformats, second validates |
| Force push to fix branch name | `git push --force` to rename remote branch | Safety net blocks `--force` | Check branch name before push; never force-push |
| `_make_run_data()` returning `object` | Untyped test helper function | mypy: `"object" has no attribute "r_prog"` | Annotate with concrete return type `RunData` and import at module level |
| Partial figure rename across commits | Renaming function in source but not in `generate_figures.py` | Import error during test collection | Rename all 4 touch points in a single commit |
| `np.isnan()` to check all-NaN Series | `np.isnan(series)` | Raises `TypeError` on non-float dtype | Use `dropna().empty` — works for any dtype |

## Results & Parameters

### Pipeline Layer Map

| Layer | File | Purpose |
| ------- | ------ | --------- |
| Emit | `scylla/e2e/stages.py` | `_get_diff_stat`, `_build_change_results`, `_build_progress_steps`, `stage_capture_diff`, `stage_finalize_run` |
| Resume | `scylla/e2e/stages.py` | `_load_process_metrics_from_run_result()` |
| Report | `scylla/e2e/run_report.py` | `_format_process_metric_value`, `_generate_process_metrics_section` |
| Load | `scylla/analysis/loader.py` | `RunData` optional fields + `load_run()` two-path extraction |
| DataFrame | `scylla/analysis/dataframes.py` | `build_runs_df()`, `build_subtests_df()`, `tier_summary()`, `model_comparison()` |
| Figures | `scylla/analysis/figures/process_metrics.py` | `fig28_r_prog_by_tier`, `fig29_cfp_by_tier`, `fig30_pr_revert_by_tier`, `fig_strategic_drift_by_tier` |
| Pipeline | `scripts/generate_figures.py` | FIGURES registry + dispatch |
| Stats | `scripts/export_data.py` | `compute_statistical_results()` normality/omnibus/pairwise/effect-sizes |
| Export | `scripts/export_data.py` | `summary.json` overall_stats / by_model / by_tier |

### Metric Columns

```python
# build_runs_df() — nullable float | None
PROCESS_METRIC_COLS = ["r_prog", "strategic_drift", "cfp", "pr_revert_rate"]

# Statistical tests — excludes strategic_drift (tier-level, not per-run)
PROCESS_METRIC_COLS_STATS = ["r_prog", "cfp", "pr_revert_rate"]

# summary.json keys (dropna + float or None)
EXPORT_KEYS = ["mean_r_prog", "mean_cfp", "mean_pr_revert_rate"]
```

### Aggregation Column Names

`build_subtests_df()` / `tier_summary()` — flat strings:

```python
["mean_r_prog", "median_r_prog", "std_r_prog",
 "mean_cfp", "median_cfp", "std_cfp",
 "mean_pr_revert_rate", "median_pr_revert_rate", "std_pr_revert_rate",
 "mean_strategic_drift", "median_strategic_drift", "std_strategic_drift"]
```

`model_comparison()` — MultiIndex tuples `(metric, agg)` for all 4 metrics × 3 aggs.

### Statistical Test Configuration

```python
significance_level = 0.05
min_sample_normality = 3    # Shapiro-Wilk minimum N
min_sample_pairwise = 2     # Mann-Whitney minimum N per group
min_sample_effect = 2       # Cliff's delta minimum N per group
```

### Verification Commands

```bash
# Full test suite (required before PR)
pixi run python -m pytest tests/ -q --no-cov

# Analysis unit tests only (fast)
PYTHONPATH=scripts pixi run python -m pytest tests/unit/analysis/ -q --no-cov

# Pre-commit (run twice for ruff auto-format)
pre-commit run --files <changed-files>
pre-commit run --files <changed-files>

# Confirm no stale figure name references after rename
grep -rn "fig_r_prog_by_tier" . --include="*.py"
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectScylla | Issues #1133–#1199, PRs #1127–#1302 | Full pipeline from runner emit to statistical export |
