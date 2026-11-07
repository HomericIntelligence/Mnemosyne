---
name: ci-gha-dead-guard-removal
license: BSD-3-Clause
description: "Use when: (1) a GHA workflow has a detect step that checks file presence and emits skip=true/false, and the guarded files are always committed — the detect+guard pattern is dead code; (2) a workflow step has `if: steps.detect.outputs.skip == 'false'` but the detection can never emit skip=true for this repo; (3) a condition step emits an output that no step or job consumes, and the output must be removed or wired instead of pinned; (4) a one-step condition gate must stay, and you must choose between a step-level and a job-level `if:` — a step-level `if:` on a step that does not check out carries no repository code. Remove a dead condition output only after you check the sibling pin: a contract test may already assert that output, so the output removal and its pin must change in one commit."
category: ci-cd
date: 2026-11-07
version: "1.2.0"
verification: verified
user-invocable: false
tags:
  - github-actions
  - workflow-authoring
  - dead-code
  - kiss
  - yagni
  - detect-and-guard
  - file-presence
  - skip-flag
  - reusable-workflow
  - ci-cleanup
  - unconsumed-output
  - gate-step
  - guard-layer
  - contract-test-pin
---

# CI: GHA Dead Detect-and-Guard Removal

## Overview

| Field | Value |
| ------- | ------- |
| **Goal** | Identify and remove dead detect+guard scaffolding and dead condition outputs in GHA workflows, and choose the correct guard layer when a gate must stay |
| **Pattern** | Condition step + downstream `if:` guards → unconditional execution, or → one layer that classifies the steps without running repository code |
| **Output** | Simplified workflow YAML, plus the contract-test pin that matches the kept or removed output |
| **Language** | YAML (GHA workflow files) — no Python code changes |
| **Build required** | No — pure YAML edit; YAML syntax check is the only local verification needed |
| **Verification** | verified (PR #1287, CI passed); the condition-output and guard-layer rules are reasoned from current workflow files and not yet pinned by a merged change |

## When to Use

- A workflow contains a step like `detect-pixi` or `detect-justfile` that emits `skip=true` or `skip=false` based on file presence (`[ -f pixi.toml ] && echo "skip=false" || echo "skip=true"`), AND the target file is always committed in the repository.
- Downstream steps guard execution with `if: steps.detect.outputs.skip == 'false'` — making those guards dead (always entered).
- KISS/YAGNI applies: the scaffolding adds complexity with no benefit when the condition can never be false.
- You need to verify whether removing guards is safe (the file might be a reusable template copied to other repos).
- A condition step writes a value to `GITHUB_OUTPUT` for a label, flag, or event test, and no step reads `steps.<id>.outputs.<key>` in any workflow.
- A contract test pins the whole `GITHUB_OUTPUT` text of that step.

## Verified Workflow

### Quick Reference

```bash
# Step 1 — confirm files are committed (not just present on disk)
git ls-files pixi.toml justfile

# Step 2 — check if the workflow is called by other repos
grep -r "uses:.*_required.yml" .github/workflows/

# Step 3 — find every consumer of a condition output
grep -rn "steps.<id>.outputs" .github/workflows/

# Step 4 — find the contract test that pins the output
grep -rn "<output-key>\|id: <id>" tests/

# Step 5 — validate YAML syntax after edit
python3 -c "
import yaml
with open('.github/workflows/_required.yml') as f:
    yaml.safe_load(f)
print('YAML syntax OK')
"

# Step 6 — commit, push, PR
git commit -S -m "ci: remove dead detect+guard scaffolding from pixi-check and justfile-check"
gh pr create --title "ci: remove dead skip-if-absent guards in _required.yml" \
  --body "$(printf 'Remove dead file-presence detect steps and skip guards.\n\nCloses #<issue-number>\n')"
```

### Detailed Steps

#### Step 1 — Identify the dead pattern

The pattern is: a detect step emits `skip=true/false` based on file presence, and downstream steps are gated on `if: steps.<id>.outputs.skip == 'false'`.

```yaml
# DEAD PATTERN — detect step always emits skip=false when pixi.toml is committed
- name: Detect pixi
  id: detect-pixi
  run: |
    if [ -f pixi.toml ]; then
      echo "skip=false" >> "$GITHUB_OUTPUT"
    else
      echo "skip=true" >> "$GITHUB_OUTPUT"
    fi

- name: Install pixi
  if: steps.detect-pixi.outputs.skip == 'false'   # always true; guard is dead
  uses: prefix-dev/setup-pixi@v0.8.1

- name: Run lint
  if: steps.detect-pixi.outputs.skip == 'false'   # always true; guard is dead
  run: pixi run lint
```

#### Step 2 — Verify the guard is always-entered

The simplest proof — `ls` the target files AND confirm they are tracked by git:

```bash
ls pixi.toml justfile            # confirm they exist on disk
git ls-files pixi.toml justfile  # confirm they are committed (tracked)
```

If both commands show the files, the detect step's output is permanently `skip=false`. No need to trace CI logs or read run history — file presence on disk combined with `git ls-files` is sufficient evidence.

#### Step 3 — Critical: check if the workflow is a reusable template

**Before removing guards**, verify the workflow is NOT intended as a reusable template copied to other repos. If it is, the guards would be load-bearing for repos that lack the guarded files.

```bash
# Check if the workflow is called by other workflows in this repo
grep -r "uses:.*_required.yml" .github/workflows/

# Check for org-wide or cross-repo references
gh search code "uses: <org>/<repo>/.github/workflows/_required.yml" --limit 10

# Check if template/copying documentation mentions this file
grep -r "_required.yml" docs/ README.md CONTRIBUTING.md 2>/dev/null
```

If other repos call this workflow as a reusable workflow, do NOT remove the guards — they protect those repos from failing when the files are absent.

#### Step 4 — A live condition output with no consumer

Do not delete a condition output only because it looks unused. Two checks decide the action.

1. Enumerate the consumers across all workflow files. A consumer can be a step `if:`, a job `if:`, or a `with:` input.
   ```bash
   grep -rn "steps\.<id>\.outputs" .github/workflows/
   ```
   If the list is empty, the output carries no load. Delete the output writes and the `id:`. Keep the skip message and the success exit: they are the run record, not the contract.
2. Check the contract test before you delete. A workflow-contract test often pins the output as text, for example an assertion that the gate output equals `<key>=false` when the condition is absent.
   ```bash
   grep -rn "<output-key>" tests/
   ```
   If a pin exists, the step's output is no longer dead scaffolding. Two choices remain:
   - Wire one real consumer. This keeps the output load-bearing only while a guard reads it.
   - Delete the output and change its pin in the same commit. The pin then asserts the exit code and the skip message only.

   Do not keep an output that no step reads. A pin without a consumer locks dead data in place.

3. Do not add a new consumer only to justify the output. A consumer that repeats an existing guard adds a second authority for one decision.

#### Step 5 — Choose the guard layer, not both

When the gate step stays, its own `if:` decides which steps run. Use the layer that matches the scope of the condition.

- **Job-level `if:`** covers a whole job, including its checkout. Use it for every job that carries pull-request code and has no other reason to run.
- **Step-level `if:`** on a step that does not check out covers no repository code. A condition step that reads only event data in `env:` executes no repository code. Reverse `if:` expressions on steps inside one job, with a job that always runs, give one classification layer for the aggregate. Ten step-level guards that copy ten job-level expressions give two layers for one decision.

Inspect the current graph before you add a layer:

```bash
python3 - <<'EOF'
import yaml
from pathlib import Path
w = yaml.load(Path('.github/workflows/ci.yml').read_text(), Loader=yaml.BaseLoader)
for name, job in w['jobs'].items():
    print(name, '| job if:', job.get('if'))
    for i, step in enumerate(job.get('steps', [])):
        if step.get('if'):
            print('   step', i, '|', step['if'])
EOF
```

When the same expression appears at both layers, remove the copy that guards no repository code, and keep the one that does.

#### Step 6 — Note nuanced double-guards

Some detect steps check multiple file name variants. After removal, the downstream tool will pick up whichever variant exists:

```bash
# Double-guard: checks lowercase AND uppercase
[ ! -f justfile ] && [ ! -f Justfile ]
```

After removing the guard, `just --evaluate` and `just --list` run unconditionally; `just` picks up whichever filename exists (`justfile` or `Justfile`) automatically. This is fine behavior — note the nuance if both variants could coexist.

#### Step 7 — Apply the fix

Delete the entire detect step and remove all `if:` guards that reference it:

```yaml
# BEFORE
jobs:
  pixi-check:
    steps:
      - uses: actions/checkout@v4
      - name: Detect pixi
        id: detect-pixi
        run: |
          if [ -f pixi.toml ]; then
            echo "skip=false" >> "$GITHUB_OUTPUT"
          else
            echo "skip=true" >> "$GITHUB_OUTPUT"
          fi
      - name: Install pixi
        if: steps.detect-pixi.outputs.skip == 'false'
        uses: prefix-dev/setup-pixi@v0.8.1
      - name: Run lint
        if: steps.detect-pixi.outputs.skip == 'false'
        run: pixi run lint

# AFTER
jobs:
  pixi-check:
    steps:
      - uses: actions/checkout@v4
      - name: Install pixi
        uses: prefix-dev/setup-pixi@v0.8.1
      - name: Run lint
        run: pixi run lint
```

#### Step 8 — Verify YAML syntax

No `pixi run pytest` applies for pure CI workflow edits. YAML syntax check is the correct local verification:

```bash
python3 -c "
import yaml, sys
with open('.github/workflows/_required.yml') as f:
    yaml.safe_load(f)
print('YAML syntax OK')
"
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Guarding removal on CI log inspection | Tried to verify guard is dead by reading CI run history | Unnecessary — file presence + `git ls-files` is sufficient; CI logs do not add information | `ls` + `git ls-files` is the correct, minimal proof that a file-presence guard is dead |
| Removing guards from a reusable workflow without checking callers | Deleted detect steps in a `_required.yml` assumed to be local | If that file is called by other repos via `uses:`, those repos break when their guarded file is absent | Always `grep -r "uses:.*<filename>"` and `gh search code` before removing guards from any reusable/shared workflow |
| Assuming single filename variant | Removed double-guard `[ ! -f justfile ] && [ ! -f Justfile ]` without noting the uppercase form | Capital `Justfile` (which `just` also accepts) would be left unguarded | Note both filename variants; `just` handles either automatically, but document the nuance |
| Deleting a gate output while its contract pin stays | Removed the output writes but left the assertion on the output text | The pin then fails, and the change reverts or the pin gets weakened to pass | Read the pin before the edit; change the output and its pin in one commit |
| Adding a step consumer to justify a dead output | Added a second guard that repeated the existing job `if:` | Two layers for one decision, and the dead output stays in the workflow | Wire a consumer only when the output carries new information; otherwise delete the output |
| Scanning only changed lines for dead guards | Removed the duplicate guard from the diff region and used the other layer as the reason | The surviving layer still needed to classify the steps; an unguarded step then runs pull-request code | Map the full job/step graph before removal, and confirm each surviving guard covers the steps it claims |

## Results & Parameters

### Typical diff size

Removing detect+guard scaffolding for two jobs (`pixi-check` and `justfile-check`) produces a small, focused diff:

- Delete the entire detect step block (5–10 lines each)
- Remove `if: steps.<id>.outputs.skip == 'false'` from each guarded step (1 line each)
- Net result: 15–25 lines removed, 0 lines added

### YAML syntax verification command

```bash
python3 -c "
import yaml
with open('.github/workflows/_required.yml') as f:
    yaml.safe_load(f)
print('YAML syntax OK')
"
# Expected output: YAML syntax OK
```

### Reusable-workflow check commands

```bash
# Local callers
grep -r "uses:.*_required.yml" .github/workflows/
# Expected: no output (file is not called by other workflows in this repo)

# Org-wide callers
gh search code "uses: <org>/<repo>/.github/workflows/_required.yml" --limit 10
# Expected: no results (file is not a shared reusable workflow)
```

### Decision table for a condition output

| Consumers found | Pin found | Action |
| --- | --- | --- |
| One or more | Yes or no | Keep the output and the pin |
| None | No | Delete the output writes and the `id:`; keep the skip message and exit code |
| None | Yes | Wire one real consumer, or delete the output and its pin in one commit |
| None | Yes, in an open PR that asserts the output | Coordinate with that PR first; do not send two conflicting pins |

### Related patterns

- `gha-workflow-authoring-pitfalls` — broader GHA authoring traps (slash job IDs, expression injection, org policy)
- `ci-hygiene-and-validation-gates` — adding CI gates to catch regressions and config drift
- `stale-ci-pattern-removal` — removing stale test-file references from workflow pattern strings

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Issue #1200 — remove dead skip-if-absent guards in `_required.yml` (PR #1287, merged 2026-06-13) | Deleted both detect steps (`Skip if no pixi.toml` and `Skip if no justfile`) and all four downstream `if: steps.detect.outputs.skip == 'false'` guards. 22 lines removed, 0 added. CI passed. Atomic edit per job: delete detect step + strip all its `if:` guards in one operation. YAML syntax check (`python3 -c "import yaml; yaml.safe_load(...)"`) before commit. Post-deletion grep verified 0 remnants of `steps.detect.outputs.skip` and `Skip if no`. |
| ProjectHephaestus | Issue #3839 — planning the condition-output and guard-layer rules, 2026-11-07 | Reasoned from the current workflow files, not from a merged change. A two-workflow gate pair emits a skip output; one workflow reads it from later steps, and the other writes it with no consumer. The aggregate job carries a step-level label `if:` on ten steps plus a step-level reverse guard in one job. One open PR already asserts the unconsumed output, so its removal must change that pin in the same commit. |