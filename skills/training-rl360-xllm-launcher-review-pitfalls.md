---
name: training-rl360-xllm-launcher-review-pitfalls
description: "Review RL360 xLLM Slurm/Ray/SGLang training launchers for launch-time log path failures, W&B secret exposure through Ray runtime envs, and native-first SGLang overlay regressions. Use when: (1) reviewing RL360 training launcher PRs, (2) scripts use Slurm #SBATCH output/error paths, (3) Ray job submit passes runtime env JSON with secrets, (4) xLLM/SGLang bridge files are copied or overlaid."
category: training
date: 2026-05-13
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [rl360, xllm, slurm, ray, wandb, sglang, training-launchers, security]
---

# RL360 xLLM Launcher Review Pitfalls

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-13 |
| **Objective** | Review RL360 xLLM Slurm/Ray/SGLang launchers for failures that occur before training starts or expose training secrets |
| **Outcome** | PR288 review on `LLM360/RL360` submitted as `CHANGES_REQUESTED` with five inline findings |
| **Verification** | verified-local - findings were posted to GitHub and read back via API |

Use this when reviewing RL360 training launcher scripts, especially long shell launchers that
combine Slurm directives, Ray job submission, W&B setup, and SGLang/xLLM bridge installation.

## When to Use

- Reviewing `scripts/train/run-xllm-*.sh` or similar RL360 launchers
- Slurm directives use `#SBATCH --output` or `#SBATCH --error`
- A launcher builds Ray `runtime-env-json`
- W&B credentials or other secrets are injected into training jobs
- SGLang/xLLM bridge files are copied, overlaid, patched, or selected by install mode
- A PR claims a local overlay is only a fallback for older images

## Verified Workflow

### Quick Reference

```bash
# Find Slurm output/error directives
rg -n '#SBATCH --(output|error)=' scripts/train

# Find runtime env and W&B secret surfaces
rg -n 'WANDB_API_KEY|runtime-env-json|RUNTIME_ENV_JSON|ray job submit' scripts/train

# Find SGLang/xLLM bridge overlays
rg -n 'xllm_sglang|xllm.py|install-mode|native|overlay|sglang' scripts/train

# Static validation for shell and generated helpers
bash -n scripts/train/run-xllm-*.sh
python3 -m py_compile path/to/generated_or_modified.py
git diff --check
```

### Review Steps

1. **Check Slurm log directories before script body**

   Slurm opens `#SBATCH --output` and `#SBATCH --error` paths before the shell body runs.
   A `mkdir -p final_logs` inside the script cannot fix a missing parent directory. The PR
   must either track the directory, use an existing directory, or document a launch wrapper
   that creates the directory before `sbatch`.

2. **Trace W&B secrets through every generated surface**

   Search beyond exported environment variables. Check generated scripts, heredocs, Ray
   runtime env JSON, argv, logs, and long-running submit processes. Passing
   `WANDB_API_KEY` through `ray job submit --runtime-env-json=...` can expose it in argv
   and in generated files that persist for the full training run.

3. **Verify native-first SGLang behavior**

   If the image already has a native SGLang xLLM bridge, the launcher should prefer it.
   Local RL360 fallback overlays should run only when the image lacks native support or
   when an explicit overlay mode is selected. Unconditional copy-over can regress current
   source-built SGLang images.

4. **Run static checks before posting**

   Use `bash -n` for launch scripts, `python3 -m py_compile` for generated Python files,
   and `git diff --check` for whitespace. These do not prove the launcher is correct, but
   they quickly eliminate syntax-level noise before the deeper review.

5. **Post findings as inline blockers**

   Launcher issues are easiest to fix when comments attach to the exact directive,
   runtime-env construction, or overlay copy line. Use `REQUEST_CHANGES` for launch-time
   failure, secret exposure, or native-first regressions.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Relying on script-body `mkdir -p final_logs` | Assumed the launcher could create Slurm log dirs after start | Slurm opens output/error paths before the script body executes | Track the directory or create it before `sbatch` |
| Treating Ray runtime env JSON as secret-safe | Put `WANDB_API_KEY` into `RUNTIME_ENV_JSON` and passed it via `ray job submit --runtime-env-json` | The key can remain in generated scripts and argv for the training run | Use a private `0600` file or another mechanism that never writes the key to generated executable scripts or argv |
| Unconditional `xllm_sglang.py` overlay | Copied RL360 fallback over SGLang native bridge | It defeats native-first behavior and can regress newer images | Preserve native bridge by default and use overlay only as an explicit fallback |

## Results & Parameters

PR288 evidence from `LLM360/RL360`:

- Review ID: `4284402017`
- Review state: `CHANGES_REQUESTED`
- PR head SHA: `825525d73b24be56a444ffab90de5fc3164261ed`
- Slurm log-dir blocker:
  - Comment `3236617139` on `scripts/train/run-xllm-375B-bbq-r3-32k.sh:9`
- W&B/Ray runtime-env blockers:
  - Comment `3236617145` on `scripts/train/run-xllm-375B-bbq-r3-32k.sh:667`
  - Comment `3236617149` on `scripts/train/run-xllm-375B-bbq-r3-128k.sh:703`
- SGLang native-first overlay concerns:
  - Comment `3236617153` on `scripts/train/run-xllm-375B-bbq-r3-32k.sh:381`
  - Comment `3236617156` on `scripts/train/run-xllm-375B-bbq-r3-128k.sh:399`

Suggested strict review grades for these findings:

- Slurm log path missing parent directory: blocker / No-Go
- W&B secret in generated script or argv: blocker / No-Go
- Unconditional fallback overlay over native bridge: concern or blocker depending on PR claim and runtime impact

## References

- `review-pr-changes` for the strict GitHub review posting workflow
- PR288 review: `https://github.com/LLM360/RL360/pull/288#pullrequestreview-4284402017`
