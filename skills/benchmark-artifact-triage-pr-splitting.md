---
name: benchmark-artifact-triage-pr-splitting
description: "Triage and incrementally publish generated benchmark result artifacts. Use when: (1) benchmark/report runs leave many untracked files, (2) result PRs must include durable reports and exact current records without logs or scratch residue, (3) live sweeps need consistency-checked report snapshots with stable record identities, (4) Pareto/report assets need validation before staging, (5) large result sets need split into reviewable PRs."
category: tooling
date: 2026-07-30
version: "1.2.0"
user-invocable: false
verification: verified-local
tags: [benchmark, artifacts, triage, results, pareto, pr-splitting, git, reproducibility, concurrency, capacity, provenance, artifact-index, live-sweep, runner-compatibility]
---

# Benchmark Artifact Triage and PR Splitting

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-30 |
| **Objective** | Turn a messy or still-running benchmark campaign into reviewable, identity-stable result PRs that preserve useful data and exclude transient run residue. |
| **Outcome** | Operational. The workflow produced separate result PRs for endpoint reports, model reports, and complete structured benchmark records while leaving logs, placeholders, progress traces, orphan metadata, and partial records untracked. It preserves concurrency as a measurement dimension, reuses only exact current results, and publishes consistency-checked incremental snapshots without changing existing opaque record identities. |
| **Verification** | verified-local. The original artifact-triage and concurrency workflows were verified locally. The live-snapshot amendment was exercised on an active endpoint sweep: a canonical indexed-results root preserved 165 existing identities, added 8 records with no removals, and produced 173 complete records and 171 unique comparable coordinates. The resulting report and data commit separately passed 49 result-repository tests in CI; that CI did not exercise worker coordination or snapshot capture. |

## When to Use

- A benchmark or report-generation run leaves many visible untracked files and you need to decide what belongs in result PRs.
- Generated reports reference images, CSV summaries, markdown summaries, raw JSON records, or reproducibility scripts.
- Some backends or scenarios produced zero-row summaries, placeholders, partial results, interrupted rows, or failure-only evidence.
- You need to distinguish a single-client latency baseline from a measured concurrency or capacity result.
- A benchmark sweep is still running, but you need a reproducible incremental report snapshot without reading a moving index directly.
- Opaque result identifiers are derived from paths and must remain stable across worktrees, resumes, and report refreshes.
- A benchmark wrapper and runner may be at different revisions, so bulk submission must be gated on the exact interpreter and CLI contract.
- A large result set needs to be split by model family, backend, endpoint, or dataset so reviewers can inspect it without a huge all-in-one PR.
- You need to preserve durable benchmark information without committing logs, scratch directories, progress files, overlays, or build/runtime residue.

## Verified Workflow

### Quick Reference

```bash
# 1. Sync to current trunk before triage.
git fetch origin
git switch <trunk-branch>
git pull --ff-only origin <trunk-branch>

# 2. Record and preflight the exact runner before bulk submission.
runner_repo="/path/to/runner-repo"
runner_python="/path/to/runner-python"
runner_script="/path/to/runner-script"
git -C "$runner_repo" rev-parse HEAD
"$runner_python" "$runner_script" --help | rg -- '--required-runner-flag'

# 3. Select one canonical result root and a separate snapshot destination.
result_repo="/path/to/result-repo"
cluster="<cluster>"
campaign="<campaign>"
dataset="<dataset>"
result_root="$result_repo/inferencex/$cluster/endpoint"
snapshot_root="/tmp/$campaign-snapshot"

# 4. Snapshot visible candidates.
git status --short --untracked-files=all
git status --short --untracked-files=all | awk '$1=="??"{print $2}' > /tmp/benchmark-candidates.txt

# 5. Build reviewed file lists by logical PR.
rg -n "PARETO|summary.csv|summary.md|request_rate_pareto|throughput_pareto" "$result_root"
find "$result_root" -type f > "/tmp/$dataset-all.txt"

# 6. Stage only reviewed paths after rendering and auditing the snapshot.
git add --pathspec-from-file="/tmp/$dataset-commit-list.txt"

# 7. Verify staged content before every commit.
git diff --cached --stat
git diff --cached --name-only | wc -l
git diff --cached --name-only | rg -n '(^|/)(logs?|runtime|progress\.jsonl|preflight|overlay|.*\.pid|.*\.err|.*\.out)$|failure|metadata\.json' || true
git diff --cached --check
```

### Detailed Steps

1. **Sync trunk before analyzing artifacts.**
   Fetch, switch to the real trunk branch, and fast-forward it before inspecting branches or untracked files. Result triage depends on the current ignore rules and the current report layout.

2. **Inspect branch state separately from artifact state.**
   First decide whether old branches are merged, stale, or still carrying independent work. Do not mix branch cleanup with result artifact commits. If a branch contains a large unrelated archive or old experiment corpus, split that decision from the benchmark result PRs.

3. **Preflight the exact runner revision before bulk submission.**
   Record the immutable runner revision and interpreter that the workers will use. Inspect that exact runner's `--help` output for every wrapper-supplied flag, then execute the smallest representative live coordinate. A wrapper-compatible local checkout does not prove that a stale shared worktree or interpreter accepts the same flags. Fail before creating bulk scheduler jobs if either preflight fails.

4. **Give each live endpoint a single writer.**
   Run at most one benchmark worker or lease per independently capacity-isolated endpoint, while parallelizing across distinct endpoints. This worker limit is separate from the request concurrency measured inside each coordinate. Write endpoint results to distinct result and index shards; do not let overlapping workers mutate the same result index.

5. **Anchor indexing to one canonical result root.**
   Choose a stable indexed-results root from the result repository's logical hierarchy, independent of the runner worktree and current directory. Reuse that exact root for every resume and report refresh. Some report generators derive opaque record IDs from a result path relative to the selected root; choosing a different ancestor can churn every ID even when the metrics are unchanged.

6. **Reuse only exact current coordinates.**
   Accept an indexed result only when it is parseable, marked current by the repository's freshness contract, complete, has zero failed requests, and exactly matches the requested model, checkpoint, input tokens, output tokens, concurrency, and prompt count. Keep rejected or failed attempts as explicit non-comparable evidence when the result schema supports it, but never treat them as successful coverage or Pareto points.

7. **Freeze and verify an incremental snapshot.**
   Publish while workers continue only when the campaign provides a consistency boundary: a lock or immutable generation, or unchanged pre/post index digests plus validation that every indexed immutable result was captured. Otherwise, pause workers at a safe boundary before copying. Render the captured generation into a temporary snapshot directory rather than directly into the clean PR worktree. Compare the previous and candidate identity sets: existing IDs should remain unless a documented supersession rule applies, and unexpected removals or broad ID churn must stop publication. Reconcile complete, comparable, and non-comparable counts before copying only the validated generated artifacts into the clean PR worktree.

8. **Keep campaign execution separate from publication.**
   Leave raw results and live worker residue in the campaign worktree. Promote only the frozen aggregate, detailed reports, data bundles, and intentional generator changes into a clean result-PR worktree. This prevents runtime logs and a partially refreshed report tree from entering the publication diff.

9. **Create explicit candidate lists in `/tmp`.**
   Write one file list per intended PR, such as `/tmp/endpoint-reports.txt`, `/tmp/model-baseline.txt`, or `/tmp/inference-json-complete.txt`. Avoid `git add -A` and broad directory adds; generated benchmark directories often contain valuable reports next to useless runtime files.

10. **Classify artifacts by information value.**
   Keep durable information:
   - generated reports such as `PARETO.md`, backend reports, and README files that summarize results;
   - `summary.csv` and `summary.md` files with non-empty result rows;
   - Pareto or report images referenced by committed markdown;
   - reproducibility scripts used to generate the committed results;
   - complete structured benchmark JSON records.

   Exclude transient or low-information artifacts:
   - logs, process IDs, Slurm output, server output, progress traces, preflight scratch, and runtime directories;
   - overlay/build residue and generated config overlays;
   - zero-row backend placeholders for backends that did not run;
   - orphan metadata-only raw files without adjacent rows or result data;
   - empty failure logs;
   - partial or zero-completion JSON benchmark records unless the PR is explicitly a failure-analysis archive.

11. **Validate CSV report artifacts before staging.**
   For each summary, check row count, status values, profile/scenario coverage, and backend/model labels. A useful report PR should say exactly what it includes, such as "69 rows across short, medium, and long" or "TRT rows only, SGLang absent." If rows are marked interrupted but still plotted, put that caveat in the PR body.

12. **Validate report asset references.**
   Search markdown reports for referenced images and confirm each image exists. If a referenced image is untracked, include it with the report. A report without its referenced Pareto images is broken rendered documentation, not a clean text-only result.

13. **Validate structured JSON benchmark records by completion.**
   Parse JSON rather than relying on filenames. Require `completed == prompt_count` or `completed == num_prompts` and zero failed requests for result PRs that claim comparable records. Validate freshness separately from the canonical benchmark index; raw result JSON may not carry `freshness_status`. Leave zero-completion and partial records untracked unless the PR title and body are explicitly about failure evidence.

14. **Preserve concurrency coverage and scope capacity claims.**
   Treat concurrency as a first-class result dimension. Record the requested and observed concurrency for every retained result, and state the observed set in the report or PR body. A concurrency-one result is a latency baseline; it cannot establish saturation, largest supported concurrency, or maximum throughput. Make those claims only after an explicit sweep over higher concurrency values, and only select a capacity or maximum-performance point from a run with complete prompt accounting, zero failed requests, and finite non-negative throughput. Retain failed or partial sweep records only when they are deliberately included as failure evidence, and never use them as peak-performance candidates.

15. **Stage from the reviewed file lists.**
   Use `git add --pathspec-from-file=/tmp/<list>.txt` so the staged set exactly matches the reviewed set. After staging, compare `git diff --cached --name-only` to the list and investigate any mismatch.

16. **Run a pre-commit staged audit for every PR.**
   Before each commit, run staged stats, staged file count, a transient-pattern scan, `git diff --cached --check`, and data-specific validation. The transient scan is allowed to have false positives, but every match should be intentionally explained or removed from staging.

17. **Split PRs by dataset and review size.**
   Prefer one PR per endpoint/model family/report surface. For large structured JSON sets, split by model family or experiment group so each PR remains reviewable. State exact included counts and excluded categories in every PR body.

18. **Return to trunk and inspect leftovers.**
   After opening PRs, switch back to trunk and run `git status --short --untracked-files=all`. The remaining untracked files should all be intentionally excluded categories, not forgotten report assets.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Commit every visible untracked file | Treat the post-run worktree as if all generated artifacts were useful benchmark output | This would include progress traces, failure logs, zero-row placeholders, orphan metadata, overlays, and partial benchmark records | Build reviewed path lists and classify artifacts before staging. |
| Commit report markdown without referenced images | Stage only text reports and summary tables | Rendered Pareto reports break when referenced images are left untracked | Search report references and include missing images as durable report assets. |
| Treat metadata-only raw files as results | Keep lone `metadata.json` files without adjacent rows or summaries | Metadata alone usually cannot reproduce a metric and creates review noise | Only commit metadata when it is part of a coherent raw-result bundle or deliberate failure archive. |
| Include empty backend placeholders | Commit empty summaries for backends that did not run | Empty files imply coverage that does not exist and inflate reviews | Exclude zero-row placeholders unless documenting absence is the explicit objective. |
| Accept every JSON record in a result directory | Stage partial or zero-completion JSON next to complete records | Partial records contaminate result datasets and make counts misleading | Parse JSON and require complete prompt accounting before staging result records. |
| Treat concurrency one as a capacity result | Report a latency baseline as the largest supported concurrency or maximum-performance point | A single-client run contains no saturation evidence and conflates latency with capacity | Preserve concurrency in every record and require a higher-concurrency sweep with complete, zero-failure points before making capacity or peak-throughput claims. |
| Submit the full sweep with an unverified runner | Assume the runner worktree accepts every flag emitted by the wrapper | A stale runner rejected a required identity flag, creating immediate non-comparable failures instead of requests | Pin the exact runner revision, inspect its CLI, and pass a tiny representative live coordinate before bulk submission. |
| Change the indexed-results root during a refresh | Render once from the canonical result subtree and later from a higher repository ancestor | Path-relative opaque IDs changed for all existing records although their metrics were identical | Reuse one canonical indexed-results root and compare identity sets before publication. |
| Render directly into the PR worktree during a live sweep | Let the report generator consume mutating indexes while replacing published assets | The result can mix generations and leave reports, counts, and referenced data out of sync | Establish a lock, immutable generation, or stable pre/post index digests with referenced-result validation; render to a temporary snapshot, validate it, then promote it. |
| Run overlapping workers against one endpoint | Treat benchmark worker parallelism as equivalent to request concurrency | Workers contend for one capacity surface and can race on the same index, obscuring both performance and provenance | Use one writer per independently isolated endpoint; express load through the coordinate's request concurrency. |

## Results & Parameters

### Information-value Matrix

| Artifact Class | Default Action | Validation |
|----------------|----------------|------------|
| `PARETO.md`, backend reports, result README files | Keep | Check that referenced assets exist and caveats are documented. |
| `summary.csv`, `summary.md` | Keep if non-empty | Count rows and inspect status, profile, backend, model, and scenario fields. |
| Pareto/report images | Keep if referenced | Confirm every referenced image path exists and is staged. |
| Reproducibility scripts | Keep when tied to committed results | Confirm script names and paths are described in the PR body. |
| Complete structured JSON benchmark records | Keep | Require `completed == prompt_count` or `completed == num_prompts` and zero failed requests. |
| Exact current indexed coordinates | Reuse | Require current freshness, exact model/checkpoint/token/concurrency/prompt-count match, complete accounting, and zero failures. |
| Non-comparable attempt evidence | Keep only when deliberate | Label explicitly, exclude from coverage and Pareto lines, and separate it from successful performance records. |
| Stable canonical indexed-results root | Keep invariant | Do not change the path ancestor used to derive opaque record identities between snapshots. |
| Incremental live-sweep snapshot | Keep after consistency audit | Use a lock, immutable generation, or stable pre/post index digests with referenced-result validation; preserve prior IDs unless explicitly superseded and render outside the PR worktree first. |
| Benchmark workers | One per isolated endpoint | Parallelize across distinct endpoints; use request concurrency inside a coordinate to measure capacity. |
| Concurrency-one records | Keep as latency baselines | Label as `concurrency=1`; do not use for saturation or capacity claims. |
| Higher-concurrency sweep records | Keep when complete | Record the requested and observed set; use only complete, zero-failure records for capacity or peak-throughput selection. |
| Logs, Slurm output, PIDs, server output, progress traces | Exclude | Usually transient runtime evidence. |
| Preflight scratch, overlays, runtime directories | Exclude | Usually build or environment residue. |
| Zero-row backend summaries | Exclude | Unless the PR explicitly documents missing coverage. |
| Orphan metadata-only raw files | Exclude | Unless bundled with rows/results or archived as failure evidence. |
| Empty failure logs and partial JSON records | Exclude | Commit only in explicit failure-analysis PRs. |

### CSV Validation Examples

```bash
# Row count and status/profile counters.
python3 - <<'PY'
import csv
from collections import Counter
from pathlib import Path

for path in map(Path, ["<result-root>/vllm/data/summary.csv"]):
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    print(path, "rows", len(rows))
    for key in ("status", "profile", "scenario", "backend", "model"):
        if rows and key in rows[0]:
            print(key, Counter(row.get(key, "") for row in rows))
PY
```

### JSON Completion Validation Example

```bash
python3 - <<'PY'
import json
from pathlib import Path

bad = []
complete = 0
for path in Path("<json-result-root>").rglob("*.json"):
    data = json.loads(path.read_text())
    completed = data.get("completed")
    expected = data.get("prompt_count", data.get("num_prompts"))
    failed = data.get("failed_requests", data.get("failed", 0))
    if expected is None:
        bad.append((path, "missing expected prompt count"))
    elif failed:
        bad.append((path, f"failed_requests={failed}"))
    elif completed == expected:
        complete += 1
    else:
        bad.append((path, f"completed={completed} expected={expected}"))

print("complete", complete)
if bad:
    print("excluded", len(bad))
    for path, reason in bad[:20]:
        print(path, reason)
PY
```

### PR Body Checklist

- Exact row or JSON-record counts included.
- Which models, endpoints, backends, profiles, and scenarios are covered.
- Which artifact classes were intentionally excluded.
- Validation commands run before commit.
- Caveats such as interrupted rows, partial backend coverage, or local-only verification.
- Whether the PR is a result PR or a failure-analysis archive.
- Exact runner revision and interpreter used for new coordinates.
- Canonical indexed-results root and snapshot cutoff or generation.
- Prior, added, removed, comparable, and non-comparable record counts.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| PerformanceHarness | After benchmark artifact ignore-rule PR #31 merged, remaining result artifacts were triaged into five follow-up PRs | Produced PRs #32 through #36 locally: endpoint reports/assets, Qwen 9B baseline, Qwen 27B baseline with interrupted-row caveat, K2-family complete InferenceX JSON records, and Gemma/Qwen complete InferenceX JSON records. |
| PerformanceHarness | Incremental endpoint-matrix refresh while benchmark workers continued | A consistency-checked snapshot preserved all 165 prior opaque record IDs, added 8 with no removals, rendered 173 complete records and 171 unique comparable coordinates, and the resulting report/data commit passed 49 tests in CI. |
