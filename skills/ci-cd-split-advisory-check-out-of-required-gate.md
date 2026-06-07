---
name: ci-cd-split-advisory-check-out-of-required-gate
description: "Split a timing-sensitive / orchestration sub-check out of a REQUIRED CI gate (e.g. pr-policy) into its own non-required advisory job so it reports status but never blocks merge. Use when: (1) a required gate bundles a timing-sensitive/orchestration check that fails a correct PR (e.g. `::error::Auto-merge is enabled before implementation review GO.`) and blocks merge; (2) you want a CI check to report status but never block merge (make a check non-blocking / advisory); (3) move the auto-merge ↔ state:implementation-go state machine out of the pr-policy gate; (4) a required job's sub-check is flaky/timing-dependent and shouldn't gate merge."
category: ci-cd
date: 2026-06-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [github-actions, branch-protection, required-checks, pr-policy, auto-merge, advisory-check, ruleset, implementation-go, non-blocking, workflow-split]
---

# CI/CD — Split an Advisory Check Out of a Required Gate

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-07 |
| **Objective** | Stop a timing-sensitive sub-check (auto-merge ↔ `state:implementation-go` state machine) inside the REQUIRED `pr-policy` gate from blocking merge on a correct PR, by moving it into its own non-required advisory job |
| **Outcome** | Workflow YAML schema-validates and all 107 `tests/unit/ci` tests pass locally; PR #1081 open (closes #1080), not yet merged/CI-confirmed |
| **Verification** | verified-local (YAML schema-validates + unit tests pass locally; end-to-end merge outcome pending CI) |

## When to Use

- A REQUIRED CI gate bundles a **timing-sensitive / orchestration** check that fails even when the code is correct — e.g. `pr-policy` failing `::error::Auto-merge is enabled before implementation review GO.` because the PR armed auto-merge before the `state:implementation-go` label workflow ran.
- You want a check to **report status but never block merge** — i.e. make an existing required sub-check advisory / non-blocking.
- You need to **move the auto-merge ↔ `state:implementation-go` state machine out of `pr-policy`** while keeping it as a visible signal.
- A required job's sub-check is **flaky or timing-dependent** and should not gate merge, but you don't want to silently delete it.

## Verified Workflow

The required `pr-policy` job bundled THREE checks: (1) the `Closes #N` body line, (2) the auto-merge ↔ `state:implementation-go` state machine, (3) signed commits. Check 2 is timing-sensitive (it depends on a label-triggered workflow arming auto-merge) and it BLOCKED merge. Coupling that orchestration concern to a hard gate is wrong. The fix splits Check 2 into its own non-required job.

### Quick Reference

```bash
# 1. In .github/workflows/_required.yml, keep pr-policy REQUIRED with only the HARD gates
#    (Closes #N + signed commits). Trim its metadata fetch to just what it still needs:
#      before: gh pr view "$PR" --json body,autoMergeRequest,labels,state
#      after:  gh pr view "$PR" --json body
#
# 2. Add a NEW job `auto-merge-policy` (NOT in the required-checks ruleset) that:
#      - copies pr-policy's  if: / runs-on: / permissions: / env:
#      - copies the SAME triggers (no `needs:`; re-runs on auto_merge_enabled /
#        auto_merge_disabled / labeled / unlabeled so it converges on PR true state)
#      - does its OWN fetch:  gh pr view "$PR" --json autoMergeRequest,labels,state
#      - runs the SAME convergence wait/retry loop + verdict, and FAILS ITS OWN JOB ONLY
#        on a mismatch (advisory: visible signal, never blocks merge).

# 3. Validate the workflow YAML against the vendored GitHub schema:
check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/_required.yml
#   -> expect:  ok -- validation done

# 4. Confirm BOTH jobs exist:
python3 -c "import yaml; print(list(yaml.safe_load(open('.github/workflows/_required.yml'))['jobs']))"
#   -> expect both 'pr-policy' and 'auto-merge-policy' present

# 5. Update any text-based workflow tests that asserted the OLD bundled fetch string
#    (e.g. tests/unit/ci/test_workflows.py), then:
pytest tests/unit/ci -q   # expect all green (107 passed locally)
```

### Detailed Steps

1. **Identify the sub-check to extract.** It must be a concern that should *report* but not *gate* — typically timing-sensitive (depends on another label/workflow firing) or orchestration-related, not a hard correctness invariant.
2. **Keep the parent gate REQUIRED with only hard gates.** In `pr-policy`, retain Check 1 (`Closes #N`) and Check 3 (signed commits). **Renumber** the remaining checks and **trim the now-unused data fetch** — `--json body,autoMergeRequest,labels,state` → `--json body`, since the parent no longer needs auto-merge/labels/state.
3. **Create the extracted job with its OWN identity.** Give it its own job name (`auto-merge-policy`). It must NOT reuse the parent's step outputs — it does its own `gh pr view --json autoMergeRequest,labels,state` fetch. Copy the parent's `if:` / `runs-on:` / `permissions:` / `env:` and the SAME triggers (no `needs:`; re-run on `auto_merge_enabled`, `auto_merge_disabled`, `labeled`, `unlabeled`) so it converges on the PR's true state via the same wait/retry loop.
4. **Make it advisory by failing only its own job.** On a verdict mismatch, the job fails ITSELF (so the check shows red as a signal) but, because its name is NOT in the branch-protection required-checks ruleset, it does not block merge.
5. **Understand the ruleset boundary.** The REQUIRED-checks list lives in GitHub repo settings / ruleset, OUTSIDE the workflow file. A new job is **non-required BY DEFAULT** until an operator adds its name to the ruleset. The workflow YAML change alone can never make something required — the ruleset does. So "split into a new job name" + "keep that name out of the ruleset" = advisory.
6. **Fix text-based workflow tests.** A repo unit test that asserts workflow *text* (e.g. `assert "--json body,autoMergeRequest,labels,state" in text`) will break the moment you split the fetch. Update it to follow the moved content: assert the combined `--json autoMergeRequest,labels,state` now lives near the new `auto-merge-policy` job, and that `pr-policy`'s fetch is body-only.
7. **Validate.** `check-jsonschema --builtin-schema vendor.github-workflows ...` → `ok -- validation done`; confirm both jobs via `yaml.safe_load(...)['jobs']`; run `pytest tests/unit/ci`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | Kept the auto-merge ↔ `state:implementation-go` check INSIDE the required `pr-policy` gate (the operator-side workaround: don't pre-arm auto-merge, `gh pr merge --disable-auto`, rerun) | The check is timing-sensitive — it depends on a label-triggered workflow arming auto-merge — so a correct PR that armed auto-merge before the GO label still failed `::error::Auto-merge is enabled before implementation review GO.` and BLOCKED merge | Don't couple an orchestration / timing-sensitive concern to a hard required gate; split it into its own non-required advisory job so it reports but never blocks |
| 2 | Let the new `auto-merge-policy` job reuse the parent `pr-policy` job's step outputs / shared metadata fetch | Sharing the parent's fetch couples the two jobs and breaks once `pr-policy`'s fetch is trimmed to `--json body`; the new job needs `autoMergeRequest,labels,state` which the parent no longer fetches | Give the extracted job its OWN `gh pr view --json ...` fetch and its own `if:`/`runs-on:`/`permissions:`/`env:`/triggers — don't share step outputs across jobs |
| 3 | Assumed adding the new job to the workflow YAML would automatically make it a required check (or keep it required) | Required-status-check membership lives in the GitHub ruleset / branch-protection settings, OUTSIDE the workflow file; a new job is non-required by default and the YAML can't change that | To make a check advisory: split it into a NEW job name and keep that name OUT of the ruleset. To make it required later, an operator must add the name to the ruleset |
| 4 | Split the fetch and ran the existing `tests/unit/ci/test_workflows.py` unchanged | A text-based assertion `assert "--json body,autoMergeRequest,labels,state" in text` matched the OLD bundled fetch string, which no longer exists after the split | When refactoring workflow YAML, update text-based workflow tests to follow the MOVED content (assert `--json autoMergeRequest,labels,state` near the new job, and `pr-policy`'s fetch is body-only) |

## Results & Parameters

**Before — one required job bundling three checks:**

```yaml
# .github/workflows/_required.yml  (BEFORE)
jobs:
  pr-policy:                       # REQUIRED (name in ruleset)
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    permissions: { pull-requests: read }
    steps:
      - run: |
          gh pr view "$PR" --json body,autoMergeRequest,labels,state > pr.json
          # Check 1: Closes #N in body            (HARD gate)
          # Check 2: auto-merge <-> state:implementation-go   (TIMING-SENSITIVE -> blocked merge)
          # Check 3: signed commits               (HARD gate)
```

**After — required gate keeps only hard gates; advisory job carries the timing-sensitive check:**

```yaml
# .github/workflows/_required.yml  (AFTER)
jobs:
  pr-policy:                       # STILL REQUIRED (name in ruleset)
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    permissions: { pull-requests: read }
    steps:
      - run: |
          gh pr view "$PR" --json body > pr.json   # trimmed: body-only
          # Check 1: Closes #N in body     (HARD gate)
          # Check 2: signed commits        (HARD gate)   # renumbered

  auto-merge-policy:               # NOT in ruleset -> ADVISORY, never blocks merge
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    permissions: { pull-requests: read }
    # no `needs:`  +  re-run on auto_merge_enabled / auto_merge_disabled / labeled / unlabeled
    steps:
      - run: |
          gh pr view "$PR" --json autoMergeRequest,labels,state > pr.json   # own fetch
          # same convergence wait/retry loop + verdict
          # FAILS THIS JOB ONLY on mismatch (visible signal, never gates merge)
```

**Validation commands & expected output:**

```bash
check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/_required.yml
# ok -- validation done

python3 -c "import yaml; print(list(yaml.safe_load(open('.github/workflows/_required.yml'))['jobs']))"
# [... 'pr-policy', 'auto-merge-policy', ...]

pytest tests/unit/ci -q
# 107 passed
```

**Ruleset note (critical):** The branch-protection REQUIRED-checks list lives in GitHub repo settings / ruleset, OUTSIDE the workflow file. Adding `auto-merge-policy` to the workflow does NOT make it required — it is non-required by default. The split is what makes it advisory; the ruleset (not the YAML) is the only place that promotes a job back to required.

**Source:** HomericIntelligence/ProjectHephaestus PR #1081 (closes #1080), `.github/workflows/_required.yml`, `tests/unit/ci/test_workflows.py`. Verification: verified-local — YAML schema-validates and all 107 `tests/unit/ci` tests pass locally; the end-to-end merge outcome is **pending CI** (PR open, not yet merged/observed in CI).
