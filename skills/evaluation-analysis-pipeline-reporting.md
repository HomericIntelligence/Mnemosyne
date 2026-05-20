---
name: evaluation-analysis-pipeline-reporting
description: >-
  Use when: (1) building or extending an end-to-end analysis pipeline that turns
  raw experiment results into publication-quality figures, statistical tables, and
  JSON/markdown reports; (2) adding new Altair/Vega-Lite figures or statistical
  comparison tables to an existing pipeline; (3) enhancing E2E report structure with
  token tracking, hierarchical reports, JSON links, or timing data; (4) reviewing or
  refactoring a large (~4 000-LOC) analysis pipeline for statistical correctness and
  DRY compliance; (5) fixing critical E2E evaluation report issues (crashes, broken
  links, workspace detection, judge validation).
category: evaluation
date: 2026-05-19
version: "1.0.0"
user-invocable: false
history: evaluation-analysis-pipeline-reporting.history
tags:
  - altair
  - vega-lite
  - statistical-analysis
  - publication-quality
  - e2e-reports
  - hierarchical-reports
  - token-stats
  - kruskal-wallis
  - mann-whitney
  - latex
  - figures
  - tables
  - dry-refactoring
---
# evaluation-analysis-pipeline-reporting

End-to-end guidance for building, extending, reviewing, and fixing analysis pipelines
that turn raw experiment data into publication-quality figures, statistical tables, and
hierarchical markdown/JSON reports.

## Overview

| Item | Details |
|------|---------|
| Date | 2026-05-19 |
| Objective | Synthesise 10 skills covering the full analysis-and-reporting layer |
| Outcome | Canonical reference for pipeline construction, figure/table extension, E2E report enhancement, and critical fixes |
| Members absorbed | add-comparison-table, skill-vega-lite-analysis-pipeline, multi-experiment-figure-pipeline, publication-pipeline-enhancement, skill-analysis-pipeline-code-review, token-stats-aggregation, adding-json-links-to-markdown-reports, e2e-agent-judge-timing, e2e-directory-flattening, skill-e2e-evaluation-report-fixes |

## When to Use

1. Building a fresh Altair/Vega-Lite analysis pipeline for experiment results.
2. Adding new figures or statistical comparison tables to an existing pipeline.
3. Enhancing E2E reports: token stats, agent/judge timing, JSON links, hierarchical reports.
4. Conducting a multi-priority code review (P0-P3) of a large analysis pipeline.
5. Fixing critical E2E report issues: UnboundLocalError crashes, broken links, workspace
   detection, invalid judge models, timing file overwrites.
6. Scaling a figure pipeline from a handful of experiments to 47+ tests with data-dependent guards.

## Verified Workflow

### Quick Reference

```bash
# Generate all pipeline outputs
pixi run python scripts/generate_all_results.py --data-dir <data-dir> --output-dir docs

# Individual steps
pixi run python scripts/export_data.py
pixi run python scripts/generate_figures.py
pixi run python scripts/generate_tables.py

# Run analysis test suite
pixi run pytest tests/unit/analysis/ -v

# Pre-commit
pre-commit run --all-files
```

```python
# Guard-set pattern for conditional figure generation
single_judge_figures = {"fig02_judge_variance", "fig14_judge_agreement"}
n_judges = int(judges_df["judge_model"].nunique())
for fig_name in figures_to_generate:
    if fig_name in single_judge_figures and n_judges < 2:
        print(f"{fig_name}: SKIPPED (requires >=2 judges, found {n_judges})")
        success_count += 1  # Not a failure — inapplicable
        continue

# Comparison table wrapper pattern
def table_<metric>_comparison(runs_df: pd.DataFrame) -> tuple[str, str]:
    if "<metric>" not in runs_df.columns:
        return ("*(data not yet collected)*", "% data not yet collected")
    return _generate_pairwise_comparison(
        runs_df,
        metric_column="<metric>",
        metric_name="<MetricDisplayName>",
        table_title="<Table Title>",
        table_label="<latex_label>",
    )
```

### 1. Pipeline Architecture

**Text-based outputs strategy** — use Vega-Lite JSON as primary figure format:

```python
import altair as alt

chart = alt.Chart(data).mark_bar().encode(x="tier:O", y="pass_rate:Q", color="model:N")
chart.save("figure.vl.json")   # Version-controllable
data.to_csv("figure.csv")      # Reproducible data
chart.save("figure.png", scale_factor=2.0)  # Optional 300 DPI PNG
```

**Four core DataFrames** (hierarchical granularity):

```python
runs_df      = build_runs_df(experiments)   # one row per run
judges_df    = build_judges_df(experiments) # one row per judge evaluation
criteria_df  = build_criteria_df(experiments)  # one row per criterion score
subtests_df  = build_subtests_df(runs_df)   # pre-aggregated subtest stats
```

**Master orchestrator structure**:

```
scripts/
├── export_data.py          # Step 1: Export CSVs + summary.json
├── generate_figures.py     # Step 2: Generate figures
├── generate_tables.py      # Step 3: Generate tables
└── generate_all_results.py # Master: runs 1→2→3 in sequence
```

**Gitignore**: Exclude all generated outputs — commit only source code.

### 2. Statistical Foundation

Non-parametric tests are required for bounded [0, 1] score data:

```python
# Bootstrap 95% CI (BCa method for small samples)
mean, ci_low, ci_high = bootstrap_ci(data, n_resamples=10000, method="BCa")

# Omnibus first, then pairwise only if significant
h_stat, p_omnibus = kruskal_wallis(*groups)
if p_omnibus < 0.05:
    u_stat, p_val = mann_whitney_u(group1, group2)
    p_corrected = holm_bonferroni_correction(p_values)

# Effect size with CI
delta, ci = cliffs_delta_ci(g1, g2, confidence=0.95)
# |δ| < 0.147 negligible, < 0.33 small, < 0.474 medium, ≥ 0.474 large

# Inter-rater reliability
alpha = krippendorff_alpha(ratings_matrix, level="ordinal")
```

**Key stats parameters**:

```python
BOOTSTRAP_ITERATIONS = 10000
CONFIDENCE_LEVEL     = 0.95
ALPHA                = 0.05
CORRECTION           = "holm"        # Less conservative than plain Bonferroni
NORMALITY_TEST       = "shapiro_wilk"  # For N < 50
```

### 3. Adding a New Comparison Table

1. Confirm the metric column exists in `build_runs_df()`.
2. Add a thin wrapper in `tables/comparison.py` calling `_generate_pairwise_comparison()`.
3. Add to `__all__` and re-export from `tables/__init__.py`.
4. Write 4 unit tests: format, missing-column guard, all-NaN, statistical-workflow labels.
5. Verify: `pixi run pytest tests/unit/analysis/test_tables.py -v`.

**NaN guard pattern**:

```python
if "cfp" not in runs_df.columns:
    return ("*(CFP data not yet collected)*", "% CFP data not yet collected")
```

### 4. Adding a New Figure

1. Create function in the appropriate `scylla/analysis/figures/` module.
   - Use `derive_tier_order(runs_df)` for consistent tier sorting.
   - Call `save_figure(chart, name, output_dir, render)` and export `.csv`.
   - Add early-return guards for missing columns or insufficient data.
2. Register in `FIGURES` dict in `scripts/generate_figures.py`.
3. Add guard set if figure has preconditions (multi-model, multi-judge, min-experiments).
4. Write smoke tests: happy path, edge case (insufficient data), registry check.

**Altair faceting — common pitfall**:

```python
# WRONG — fails with "Facet charts require data at the top level"
chart = alt.layer(zero_line, error_bars, points).facet(row="model:N")

# CORRECT
chart = alt.layer(zero_line, error_bars, points, data=effect_df).facet(row="model:N")
```

### 5. Publication Enhancement (WP1-WP6)

WP order: Stats Foundation → Hardcoded cleanup → New Tables → New Figures →
Enhanced Export → LaTeX Figure Support.

**LaTeX snippet generation**:

```python
# save_figure() writes *_include.tex when "pdf" in formats
\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{name.pdf}
\caption{...}
\label{fig:name}
\end{figure}
```

**Enhanced summary.json** exports: quartiles, tokens, duration, `statistical_results.json`
(normality, omnibus, pairwise, effect sizes, correlations).

### 6. Token Stats Aggregation

```python
@dataclass
class TokenStats:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    def __add__(self, other: TokenStats) -> TokenStats:
        return TokenStats(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_creation_tokens=self.cache_creation_tokens + other.cache_creation_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
        )

# Aggregate with functools.reduce
from functools import reduce
token_stats = reduce(lambda a, b: a + b, [r.token_stats for r in runs], TokenStats())
```

Add legacy properties when replacing individual fields (`tokens_input`, `tokens_output`)
to preserve backwards compatibility.

### 7. Agent/Judge Timing Separation

```python
@dataclass
class RunResult:
    duration_seconds: float         # Total (agent + judge)
    agent_duration_seconds: float   # Agent execution time
    judge_duration_seconds: float   # Judge evaluation time

# Timing semantics for cached results: set to 0.0 consistently
```

### 8. E2E Directory Flattening

Flatten `results/<exp>/tiers/T0/` → `results/<exp>/T0/`; share workspace at subtest
level; generate JSON + markdown reports at every level with relative links.

```python
# Flatten tier path
tier_dir = self.experiment_dir / tier_id.value  # not "tiers/" prefix

# Hierarchical reports
save_run_report_json(run_dir, ...)
save_subtest_report(subtest_dir, ...)
save_tier_report(tier_dir, ...)
save_experiment_report(experiment_dir, ...)
```

### 9. Critical E2E Report Fixes

| Fix | Root Cause | Solution |
|-----|-----------|----------|
| UnboundLocalError | `import json` inside `if` block | Move import to method top |
| Workspace detection | `git diff HEAD~1` misses uncommitted | Combine `git diff` + `git status --porcelain` |
| Invalid judge models | Wrong model IDs | Validate with small prompt before experiment |
| Timing file overwrites | Single file for all judges | Write to `judge/judge_01/timing.json` per judge |
| Broken result.json links | File never written | Remove link; keep only `judgment.json` |

**Model ID shortcuts**:

```python
shortcuts = {
    "opus-4-5": "claude-opus-4-5-20251101",
    "sonnet-4-5": "claude-sonnet-4-5-20250929",
    "haiku-4-5": "claude-haiku-4-5",
    "opus-4-0": "claude-opus-4-20250514",
    "sonnet-4-0": "claude-sonnet-4-20250514",
    "haiku-4-0": "claude-haiku-4-0-20250514",
}
```

### 10. Large-Pipeline Code Review (P0-P3)

Priority ladder: P0 wrong numbers/crashes → P1 methodology/robustness → P2 DRY/dead
code → P3 documentation.

Phase strategy: P0 fixes first → P1 statistical → P1 infrastructure → P2 DRY → P2 tests
→ P3 cleanup → architecture deferred.

```bash
# Detect DRY violations
rg "tier_order\s*=\s*\[.*T0.*T6.*\]" -A 1        # 17 duplications
rg "1\s*-\s*\(.*std.*mean\)" -A 1 -B 1            # formula duplications

# Validate with reference
pixi run pytest tests/unit/analysis/ -v
pixi run python scripts/generate_all_results.py    # Regenerate and compare
```

**Do not implement statistical functions from scratch** — wrap scipy/krippendorff and
test against authoritative packages.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|---------------|--------------|----------------|
| Altair faceting without top-level data | `alt.layer(...).facet(row="model:N")` | `ValueError: Facet charts require data at the top level` | Always pass `data=df` to `alt.layer()` before calling `.facet()` |
| Direct figure module patching in tests | `@patch("scylla.analysis.figures.variance.save_figure")` per test | Import path inconsistencies — patches not applying | Use `mock_save_figure` fixture in `conftest.py` with canonical import path |
| Importing scripts as modules in tests | `from scripts.export_data import ...` | `scripts/` has no `__init__.py` | `sys.path.insert(0, str(Path(__file__).parents[3] / "scripts"))` |
| Testing LaTeX generation with mocked save_figure | Used `mock_save_figure` fixture | Mock intercepts call; LaTeX snippet never written | Call `save_figure()` directly in that test, skip the mock |
| Strict Kendall's tau threshold for small N | `p < 0.01` for perfect rank correlation | `scipy.stats.kendalltau` returns `p=0.017` for n=5 even on perfect correlation | Use `p < 0.05` for small-sample rank correlation; Kendall p-values larger than Spearman for small N |
| Custom statistical implementations | Implemented Krippendorff's alpha from scratch | Formula matched Scott's pi, not Krippendorff | Wrap authoritative packages (scipy, krippendorff); validate against them |
| Single judge timing file | `judge/timing.json` overwritten by each judge | Parallel judges clobber file | Write `judge/judge_01/timing.json`, `judge/judge_02/timing.json`, etc. |

## Results & Parameters

### Output Formats

| Type | Formats | Location |
|------|---------|----------|
| Data exports | `.csv`, `summary.json`, `statistical_results.json` | `docs/data/` |
| Figures | `.vl.json`, `.csv`, `.png` (300 DPI), `.pdf` | `docs/figures/` |
| LaTeX snippets | `*_include.tex` | `docs/figures/` |
| Tables | `.md`, `.tex` | `docs/tables/` |
| E2E run reports | `report.json`, `report.md` | per-run, subtest, tier, experiment dirs |

### Pipeline Dependencies

```toml
[feature.analysis.dependencies]
matplotlib  = ">=3.8"
numpy       = ">=1.24"
pandas      = ">=2.0"
scipy       = ">=1.11"
altair      = ">=5.0"
vl-convert-python = ">=1.0"
statsmodels = ">=0.14"   # OLS regression, advanced diagnostics
```

### Test Fixture Pattern

```python
@pytest.fixture
def sample_runs_df() -> pd.DataFrame:
    """2 models × 3 tiers × 2 subtests × 5 runs = 60 rows."""
    rows = []
    for model in ["Sonnet 4.5", "Haiku 4.5"]:
        for tier in ["T0", "T1", "T2"]:
            for subtest in ["001", "002"]:
                for run in range(1, 6):
                    rows.append({
                        "agent_model": model, "tier": tier, "subtest": subtest,
                        "run_number": run,
                        "score": 0.0 if run == 1 else 0.5 if run <= 3 else 1.0,
                        "passed": run > 3,
                        "cost_usd": 0.1 * run,
                    })
    return pd.DataFrame(rows)
```

### Key Performance Benchmarks (ProjectScylla baseline)

| Step | Time |
|------|------|
| Load 2 238 runs (13 560 JSON files) | ~30 s |
| Generate 15 figures | ~60 s |
| Generate 7 tables | ~10 s |
| Full pipeline | ~2 min |

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectScylla | PR #213 — Vega-Lite pipeline (15 figures, 7 tables) | skill-vega-lite-analysis-pipeline |
| ProjectScylla | PRs #273-#278 — Publication enhancement WP1-WP6 | publication-pipeline-enhancement |
| ProjectScylla | PRs #241-#255 — 15-PR code review, 26 issues closed | skill-analysis-pipeline-code-review |
| ProjectScylla | PR #1298 — CFP/R_Prog comparison tables | add-comparison-table |
| ProjectScylla | Multi-experiment 47-test scaling (fig35-39) | multi-experiment-figure-pipeline |
| ProjectScylla | PR #125 — TokenStats dataclass + aggregation | token-stats-aggregation |
| ProjectScylla | PR #143 — Agent/judge timing separation | e2e-agent-judge-timing |
| ProjectScylla | PR #172 — E2E report fixes | skill-e2e-evaluation-report-fixes |
| ProjectScylla | JSON links + hierarchical reports | adding-json-links-to-markdown-reports, e2e-directory-flattening |
