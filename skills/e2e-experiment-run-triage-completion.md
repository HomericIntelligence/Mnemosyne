---
name: e2e-experiment-run-triage-completion
description: "Use when: (1) a batch E2E experiment run has completed and needs result
  triage (framework bugs vs model failures); (2) experiments are broken/partial and
  need repair, fresh re-runs, or stale-worktree cleanup; (3) checkpoint states appear
  inconsistent or misleading and need validation; (4) analysis scripts report wrong
  counts due to regex, multiplier, or subtest-ID numbering bugs; (5) a FAILED checkpoint
  causes immediate exit on resume or --retry-errors is silently ignored; (6) new benchmark
  test cases need to be created from PR history or real-world tasks; (7) A/B sub-tests
  for experimental features need to be added to existing evaluation tiers."
category: evaluation
date: 2026-05-19
version: "1.0.0"
user-invocable: false
history: e2e-experiment-run-triage-completion.history
tags:
  - e2e
  - evaluation
  - dryrun
  - checkpoint
  - triage
  - ablation
  - swe-bench
  - experiment-lifecycle
---
# E2E Experiment Run, Triage, and Completion

Full lifecycle skill for getting a batch of E2E experiments from launched to
fully-completed-and-validated: task/benchmark design, batch triage, stale-checkpoint
repair, failure classification, readiness assessment, and A/B sub-test setup.

## Overview

| Date | Objective | Outcome |
| ---- | --------- | ------- |
| 2026-01-01 | Design T2+ eval tasks from real PRs with patchfile evaluation | Pattern established; PR #107 merged |
| 2026-01-02 | Create 45 SWE-bench-style tests; run T0-T6 ablation (114 sub-tests) | Tier infrastructure validated; T6 CLI-arg bug found and fixed |
| 2026-02-05 | Add A/B agent-teams sub-tests to T4; validate dryrun2 reproducibility | PR #350; 100% pass rate validated against baseline |
| 2026-02-12 | Triage 5 failures — framework bug vs model hallucination | Model hallucination confirmed; upstream bug report filed |
| 2026-02-19 | Analyse 47-test dry run (Haiku/T0); generate GitHub issue script | All analysis files written; `file_issues.sh` syntax-clean |
| 2026-02-25 | Fix FAILED-checkpoint resume: 3 compounding bugs | PRs #1104, #1105; retry-errors + tier-merge now work |
| 2026-03-14 | Complete dryrun3: 47 experiments, 7 tiers; Go/NoGo script | 329 runs, $148.64, 34.3% pass-rate; analysis pipeline done |
| 2026-03-15 | Fix analysis-script patterns (regex, multiplier, exit codes) | 4 bugs fixed; shell retry script made resilient |
| 2026-03-16 | Fix 1-based subtest ID misclassification; correct 0→44 complete | Sort-and-slice fix; 60.6% overall pass rate confirmed |
| 2026-03-21 | Triage experiment dataset for paper readiness; phased resume plan | 4-level state hierarchy documented; stale checkpoints identified |

## When to Use

- (1) A batch E2E run has completed and `batch_summary.json` exists; need to triage
  framework bugs vs model failures.
- (2) Some experiments have 0 or partial `run_result.json` files; `--retry-errors`
  says "All tests already completed" despite `--max-subtests` expansion.
- (3) Stale git worktrees in `~/dryrun/repos/<hash>/` block `--fresh` re-runs.
- (4) Analysis script discovers 0 experiments, reports wrong run totals, or shows
  all tests incomplete because of a subtest-ID numbering assumption.
- (5) Resuming a checkpoint with `experiment_state=failed` exits immediately with
  "Experiment complete" after <1 second.
- (6) Need to assess which experiments in a results directory are paper-ready, or
  detect inconsistencies between `experiment_state=complete` and actual run states.
- (7) Creating new SWE-bench-style test cases from PR history, or adding A/B
  parallel sub-tests for an experimental feature within existing tiers.

## Verified Workflow

### Quick Reference

| Situation | Action |
| --------- | ------ |
| Triage batch failures | §1 — cross-ref `total_cost` vs `status` in `batch_summary.json` |
| Broken experiments (0 runs) | §2 — clean stale worktrees → `--fresh` re-run |
| Partial experiments | §3 — `--retry-errors` targeting missing tier only |
| Verify completion | §4 — count `run_result.json`; do NOT trust checkpoint alone |
| Analysis finds 0 experiments | §5 — fix timestamp regex `T\d{6}` → `T[\d-]+` |
| Analysis subtest counts wrong | §6 — fix 1-based ID: sort-and-slice instead of `>=` |
| FAILED checkpoint exits immediately | §7 — three-bug fix: terminal-state reset + retry-errors single mode + CLI tier merge |
| Dataset not paper-ready | §8 — scan 4-level state hierarchy; plan phased `--until` |
| New benchmark tasks | §9 — SWE-bench pattern from PR history |
| A/B experimental sub-tests | §10 — boolean flag + mirror numbering + env-var feature flag |

### §1 Batch Result Triage

Read `batch_summary.json` and thread logs in parallel:

```bash
# Structured results
cat <results-dir>/batch_summary.json

# Error patterns in thread logs
grep -n "ValidationError\|criteria_scores\|is_error\|Error" \
  <results-dir>/thread_logs/thread_0.log | head -100

# Find EXPERIMENT COMPLETE blocks (first vs re-run sessions)
grep -A5 "EXPERIMENT COMPLETE" <results-dir>/thread_logs/thread_0.log | head -200
```

**Failure classification by cost:**

| `total_cost` | `status` | Category | Action |
| ------------ | -------- | -------- | ------ |
| 0.0 | fail | Framework Bug (zero API calls) | Re-run after fixing bug |
| 0.0 + 100-200s | fail | Framework Bug (after repo clone) | Re-run after fixing bug |
| > 0.0 | fail | Model Failure | Investigate rubric/prompt |

Common framework bug: `criteria_scores=None` causes `ValidationError` on resume.
Fix: `judgment.get("criteria_scores") or {}` (not `.get(..., {})`).

Generate per-test issue files with Python from `batch_summary.json`, then produce
`file_issues.sh` with `--dry-run` support. Syntax-check before running.

### §2 Clean Stale Worktrees and Re-run Broken Experiments

**Always clean before any `--fresh` re-run:**

```bash
# Identify stale worktrees
for repo_dir in <results-dir>/repos/*/; do
  git -C "$repo_dir" worktree list 2>/dev/null | grep -v "bare"
done

# Remove stale worktrees for broken tests
BROKEN="test-001|test-003"
for repo_dir in <results-dir>/repos/*/; do
  git -C "$repo_dir" worktree list 2>/dev/null | \
    grep -E "($BROKEN)/" | awk '{print $1}' | while read wt; do
      git -C "$repo_dir" worktree remove --force "$wt" 2>/dev/null || true
    done
  git -C "$repo_dir" worktree prune 2>/dev/null || true
  git -C "$repo_dir" branch 2>/dev/null | grep -E "($BROKEN)_" | \
    sed 's/[+* ]*//' | while read b; do
      git -C "$repo_dir" branch -D "$b" 2>/dev/null || true
    done
done

# Re-run broken experiments
pixi run python scripts/manage_experiment.py run \
  --config tests/fixtures/tests \
  --model <model-id> --judge-model <judge-id> \
  --tiers T0 T1 T2 T3 T4 T5 T6 \
  --runs 1 --max-subtests 1 \
  --results-dir <results-dir> \
  --fresh --threads 2
```

**Key**: `--fresh` creates a new timestamped dir but does NOT clear shared repos.
Full-ablation tests must omit `--max-subtests` (T3 has 41 subtests; capping at 24
leaves T3/25-41 uncreated).

### §3 Repair Partial Experiments

Serialize: finish `--fresh` re-runs before starting `--retry-errors` repairs.
Overlapping API calls cause exponential-backoff retries (~8 min per validation).

```bash
# Identify missing tier
for tier in T0 T1 T2 T3 T4 T5 T6; do
  count=$(find <exp-dir>/$tier -name run_result.json 2>/dev/null | wc -l)
  echo "$tier: $count"
done

# Repair missing tier only
pixi run python scripts/manage_experiment.py run \
  --config tests/fixtures/tests/test-NNN \
  --tiers T4 --runs 1 --max-subtests 1 \
  --results-dir <results-dir> --retry-errors
```

### §4 Verify Completion (Do Not Trust Checkpoint Alone)

```bash
# Count run_result.json files (ground truth)
for dir in <results-dir>/2026-*-test-*/; do
  count=$(find "$dir" -name run_result.json 2>/dev/null | wc -l)
  echo "$(basename $dir): $count"
done

# Build loader-compatible symlink tree
mkdir -p ~/fullruns/<dataset>
for dir in <results-dir>/2026-*-test-*/; do
  test_name=$(basename "$dir" | grep -oE 'test-[0-9]+$')
  [ -n "$test_name" ] && mkdir -p ~/fullruns/<dataset>/$test_name && \
    ln -sf "$dir" ~/fullruns/<dataset>/$test_name/$(basename "$dir")
done

# Generate analysis pipeline
pixi run python scripts/generate_all_results.py \
  --data-dir ~/fullruns/<dataset> \
  --output-dir docs/arxiv/<dataset>
```

### §5 Fix Analysis Script: Regex and Multiplier

```python
# WRONG: T\d{6} fails for dirs named 2026-02-23T18-56-10-test-017
pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{6})-(\w+)-(test-\d{3})$")

# CORRECT: T[\d-]+ handles HH-MM-SS with dashes
pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}T[\d-]+)-(test-\d{3})$")
# group(1)=timestamp, group(2)=test-NNN
```

Confirm runs-per-subtest before hardcoding multiplier:
```bash
ls <results-dir>/2026-*/T0/00/ | grep "^run_" | wc -l
```
Update every `* 3` to `* 1` if dryrun uses 1 run/subtest.

Shell retry script: replace `set -e` with explicit failure capture so one failing
test does not abort the whole suite. Add pre-run `|| true` analysis call and
post-run analysis call whose exit code propagates (0=GO, 1=NOGO).

### §6 Fix 1-Based Subtest ID Misclassification

T0 uses 0-based IDs (00, 01, …); T1-T6 use 1-based (01, 02, …).
`int(sub_id) >= effective_max` mis-classifies T1-T6 highest valid ID as orphan.

```python
# BROKEN — assumes 0-based
is_orphan = int(sub_id) >= effective_max

# FIXED — sort-and-slice, ID-scheme-agnostic
sorted_ids = sorted(subtests.keys(), key=lambda s: int(s))
active_ids = set(sorted_ids[:effective_max])
is_orphan = sub_id not in active_ids
```

Same fix for coverage counting:
```python
# BROKEN
active = sum(1 for sub_id in subtests if int(sub_id) < effective_max)
# FIXED
active = min(len(sorted(subtests.keys(), key=lambda s: int(s))), effective_max)
```

### §7 Fix FAILED-Checkpoint Resume (Three Compounding Bugs)

**Bug 1**: `FAILED` is in `_EXPERIMENT_TERMINAL_STATES`; `advance_to_completion()`
exits immediately on first `while not self.is_complete()` check.

**Bug 2**: `--retry-errors` is batch-only; silently a no-op in single mode.

**Bug 3**: `_load_checkpoint_and_config()` replaces `self.config` with saved
`experiment.json`; CLI `--tiers` additions are discarded.

**Fixes** (in `scylla/e2e/runner.py` and `scripts/manage_experiment.py`):

```python
# runner.py — capture CLI tiers BEFORE config is overwritten
_cli_tiers = list(self.config.tiers_to_run)
# ... load checkpoint ...
if self.checkpoint.experiment_state in ("failed", "interrupted"):
    self.checkpoint.experiment_state = "tiers_running"
    for tier_id, state in self.checkpoint.tier_states.items():
        if state == "failed":
            self.checkpoint.tier_states[tier_id] = "pending"
    # Merge CLI tiers not already saved
    existing = {t.value for t in self.config.tiers_to_run}
    new_tiers = [t for t in _cli_tiers if t.value not in existing]
    if new_tiers:
        self.config = self.config.model_copy(
            update={"tiers_to_run": self.config.tiers_to_run + new_tiers}
        )
        self._save_config()
        self.checkpoint.config_hash = compute_config_hash(self.config)
    save_checkpoint(self.checkpoint, checkpoint_path)
```

```python
# manage_experiment.py cmd_run() — single-mode --retry-errors
if args.retry_errors and not (from_run_state or from_tier_state):
    checkpoint_path = args.results_dir / experiment_id / "checkpoint.json"
    if checkpoint_path.exists():
        checkpoint = load_checkpoint(checkpoint_path)
        reset_count = reset_runs_for_from_state(
            checkpoint, from_state="pending", status_filter=["failed"])
        if reset_count > 0:
            save_checkpoint(checkpoint, checkpoint_path)
```

**Workaround** (no code change): `--from replay_generated --filter-status failed`.

### §8 Assess Dataset for Paper Readiness

Scan 4-level state hierarchy; do not trust `experiment_state=complete` alone:

```bash
for dir in ~/fullruns/<dataset>/*/; do
  python3 -c "
import json
with open('$dir/checkpoint.json') as f: cp = json.load(f)
print('$(basename $dir)', cp['experiment_state'])
for tier, state in cp.get('run_states', {}).items():
    counts = {}
    for sub in state:
        for rnum, s in state[sub].items():
            counts[s] = counts.get(s, 0) + 1
    print(' ', tier, counts)
"
done
```

| Pattern | Meaning | Action |
| ------- | ------- | ------ |
| `experiment_state=complete`, all runs `worktree_cleaned` | Truly complete | Paper-ready |
| `experiment_state=complete`, runs at `agent_complete` | Stale | Resume — resets on restart |
| `experiment_state=complete`, runs at `replay_generated` | Never executed | Full re-run needed |
| `experiment_state=tiers_running`, mixed states | Interrupted | Resumable as-is |

For large datasets use phased `--until`:
```bash
# Phase 1: agents (5 threads)
pixi run python scripts/manage_experiment.py run --threads 5 --until agent_complete ...
# Phase 2: diffs (2 threads)
pixi run python scripts/manage_experiment.py run --threads 2 --until diff_captured ...
# Phase 3: judging + finalize (5 threads)
pixi run python scripts/manage_experiment.py run --threads 5 ...
```

Note: `--parallel` CLI flag does not exist; only `--threads` controls batch parallelism.

### §9 Create SWE-Bench-Style Benchmark Tasks

```bash
# Get merged PRs with metadata
gh pr list --state merged --limit 500 --json number,title,labels,additions,deletions

# Get parent commit (state before PR)
merge_commit=$(gh pr view <num> --json mergeCommit --jq '.mergeCommit.oid')
parent_commit=$(git rev-parse $merge_commit^)

# Get reference patch
gh pr diff <num> --repo owner/repo > expected/reference/reference.patch
```

Test directory structure:
```
tests/fixtures/tests/test-XXX/
├── test.yaml          # id, name, source.repo, source.hash (BEFORE PR), tiers, timeout
├── prompt.md          # From PR description
├── expected/
│   ├── criteria.md
│   ├── rubric.yaml    # pass_threshold: 0.70
│   └── reference/reference.patch
├── constraints/forbidden.md   # No git-log, no gh-api, no web-search for solution
└── t{0..6}/           # Tier configs (copy from existing test)
```

For T2+ complex tasks: `max_turns: 50`, `timeout_seconds: 7200`, patchfile comparison.
Judge evaluates semantic equivalence, NOT exact match against reference.

### §10 Add A/B Experimental Feature Sub-Tests

Pattern: add boolean flag to `SubTestConfig`, parse from YAML, inject as env var in
`settings.json`, create mirror-numbered variants, add CLI `--skip-<feature>` filter.

```yaml
# tests/.../t4/08-feature-variant.yaml
name: chief-architect-teams
agent_teams: true   # enables CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 in settings.json
extends_previous: true
```

Number variants sequentially after baselines (01-07 baseline → 08-14 variants).
Verify with: `pixi run python verify_subtests.py`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| `criteria_scores=judgment.get("criteria_scores", {})` | Default `{}` when key absent | Key exists but value is `None`; `.get(k, default)` only fires when key is missing | Use `or {}`: `judgment.get("criteria_scores") or {}` |
| `--fresh` without cleaning repos | Assumed `--fresh` resets everything | Only creates new timestamped dir; stale worktrees/branches in `repos/<hash>/` remain | Always prune worktrees before any `--fresh` re-run |
| Overlapping `--retry-errors` with active `--fresh` runs | Started partial repairs while broken re-runs were consuming API | Rate-limit cascades caused 4× retries with ~60s backoff each (~8 min/validation) | Serialize Phase 2 (broken) and Phase 3 (partial); never overlap |
| `--max-subtests 24` on full-ablation tests | Cap set to match T0 subtest count | T3 has 41 subtests; subtests 25-41 were never created in checkpoint | Full ablation = no `--max-subtests` flag |
| `int(sub_id) >= effective_max` for orphan classification | Assumed 0-based IDs across all tiers | T1-T6 use 1-based IDs; highest valid ID equals `effective_max` and is wrongly classified as orphan | Use sort-and-slice; never assume numbering scheme |
| Trusting `experiment_state=complete` | 12 experiments showed complete state | Runs were at `replay_generated` (never executed); state was written prematurely | Always cross-reference run_states at all 4 levels |
| Regex `T\d{6}` for timestamp matching | Expected `T185610` (6 contiguous digits) | Actual dirs use `T18-56-10` (dashes between HH, MM, SS) | Inspect actual dir names (`ls \| head`) before writing regex |
| `* 3` run multiplier | Assumed 3 runs/subtest (standard config) | dryrun3 used 1 run/subtest | Check actual artifact count (`ls T0/00/ \| grep run_`) |
| `set -e` in retry shell script | Standard safety setting | Any single test failure aborted entire N-test suite | Use explicit failure capture; `set -e` incompatible with retry workflows |
| Short model aliases (`--model sonnet`) | Convenience shorthand | Analysis loader uses regex on full model IDs for display-name generation | Always use full model IDs (e.g., `claude-sonnet-4-5-20250929`) |
| `--exclude` omitted from `generate_all_results.py` | Ran without filtering | Loader scans all subdirs in `~/fullruns/`; mixed data from unrelated experiments | Always `--exclude` unrelated experiments |
| `--from` flag not sufficient alone for FAILED resume | Attempted `--from` workaround | Worked for run resets but didn't resolve terminal-state exit or tier-merge | Three-bug fix in runner.py + manage_experiment.py is the proper fix |
| Merge old 1-run data into new 3-run experiment | Copy artifacts, update checkpoint | Config hashes differed; runs-per-subtest incompatible | Check `config_hash` and `runs_per_subtest` before any merge attempt |
| Framework assumed guilty for missing files | Searched error logs for cleanup code | No cleanup between agent and judge; agent hallucinated success without tool calls | Check `server_tool_use` stats; zero tool calls = model hallucination, not framework bug |

## Results & Parameters

### Tier Structure Reference

| Tier | Name | Sub-tests | Description |
| ---- | ---- | --------- | ----------- |
| T0 | Prompts | 24 | System prompt ablation (0-based IDs: 00-23) |
| T1 | Skills | 10 | Skill category ablation (1-based IDs: 01-10) |
| T2 | Tooling | 15 | Tool categories + MCP servers |
| T3 | Delegation | 41 | Agent ablation (non-orchestrators) |
| T4 | Hierarchy | 7+7 | Orchestrator ablation + optional agent-teams variants |
| T5 | Hybrid | 15 | Best combinations + permutations |
| T6 | Super | 1 | Everything at maximum capability |

### Go/NoGo Criteria (all 4 must pass)

1. All N tests have checkpoints
2. `infra_error + intermediate == 0`
3. No missing subtests per tier (coverage check)
4. ≥ 95% of complete runs have valid `run_result.json`

### Run Classification

| State | Classification | Action |
| ----- | -------------- | ------ |
| `worktree_cleaned` | COMPLETE | Never retry |
| `failed` / `rate_limited` | INFRA_ERROR | Reset to `pending` |
| any other | INTERMEDIATE | Resume from current |
| `sub_index >= effective_max` (0-based) or outside active set | ORPHAN | Exclude from metrics |

### Analysis Script Template

```bash
#!/usr/bin/env bash
set -uo pipefail
RESULTS_DIR=~/dryrun3
FAILED_TESTS=()

pixi run python scripts/analyze_dryrun3.py --results-dir "$RESULTS_DIR" || true

for test in "${ALL_TESTS[@]}"; do
  if ! pixi run python scripts/manage_experiment.py run \
      --config "tests/fixtures/tests/$test" \
      --results-dir "$RESULTS_DIR" --threads 2 -v; then
    FAILED_TESTS+=("$test")
    echo "WARNING: $test non-zero exit"
  fi
done

[ ${#FAILED_TESTS[@]} -gt 0 ] && echo "ERRORS: ${FAILED_TESTS[*]}"
pixi run python scripts/analyze_dryrun3.py --results-dir "$RESULTS_DIR"
# exit code propagates: 0=GO, 1=NOGO
```

### Key Files

| File | Role |
| ---- | ---- |
| `scripts/manage_experiment.py` | Batch runner; single+batch mode; `--retry-errors`, `--fresh`, `--from`, `--until` |
| `scylla/e2e/runner.py` | `_initialize_or_resume_experiment()`; terminal-state reset; tier merge |
| `scylla/e2e/experiment_state_machine.py` | `_EXPERIMENT_TERMINAL_STATES`; `advance_to_completion()` |
| `scripts/analyze_dryrun3.py` | Go/NoGo script; run classification; subtest coverage check |
| `scripts/generate_all_results.py` | Analysis pipeline: figures, tables, CSVs, JSONs |
| `scylla/analysis/loader.py` | Requires full model IDs; expects `data_dir/<exp>/<ts>/T*/NN/run_*/run_result.json` |
| `checkpoint.json` | v3.1: experiment_state, tier_states, subtest_states, run_states |

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectScylla | dryrun3 (47 tests, T0-T6, Haiku), PRs #1104 #1105 #1404 #1491 | Consolidated from 13 member skills |
