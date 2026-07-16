---
name: slurm-wrap-shell-contract
description: "Submit reliable Slurm --wrap commands. Use when: (1) a wrapped job fails before its payload starts, (2) Bash-only shell options such as pipefail are needed, or (3) a container build is submitted through sbatch --wrap."
category: tooling
date: 2026-07-16
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: ["slurm", "sbatch", "wrap", "shell", "sh", "bash", "pipefail", "container-build"]
---

# Slurm Wrap Shell Contract

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-16 |
| **Objective** | Submit manifest-defined container builds through Slurm without a wrapper-shell failure. |
| **Outcome** | A wrapped job containing `set -euo pipefail` failed before the container command ran; a direct command wrapper was accepted and started normally. |
| **Verification** | verified-local |

## When to Use

- A job submitted with `sbatch --wrap` exits immediately with an illegal shell-option error.
- A command needs Bash semantics but is being passed through a Slurm wrapper.
- A short, single-command Slurm build or validation job does not require a standalone script.

## Verified Workflow

### Quick Reference

For a one-command job, pass the command directly and let its exit status become the Slurm job status:

```bash
sbatch --parsable \
  --partition=<PARTITION> \
  --qos=<QOS> \
  --account=<ACCOUNT> \
  --chdir=<REPO_ROOT> \
  --wrap='uv run inference360 container vllm'
```

When Bash-only syntax is required, submit a Bash script file rather than relying on the shell used by `--wrap`:

```bash
#!/usr/bin/env bash
set -euo pipefail
uv run inference360 container vllm
```

```bash
sbatch <BASH_SCRIPT_PATH>
```

### Detailed Steps

1. Inspect the Slurm output before changing the payload command. An immediate failure that names `set -o pipefail` occurred in the wrapper shell, not in the build tool.
2. Treat `--wrap` as a POSIX-shell context. Do not put Bash-only options, arrays, or other Bash syntax in the wrapper string.
3. For a single command, use a direct wrapper with no shell setup.
4. For a multi-step command, put `#!/usr/bin/env bash` and `set -euo pipefail` in a submitted script file, then submit that file with `sbatch`.
5. Confirm the new job advances past its first second and emits the payload command's logs before diagnosing the payload itself.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Bash strict mode in `--wrap` | Submitted `set -euo pipefail; uv run ...` through `sbatch --wrap` | Slurm executed the wrapper with `/bin/sh`, which rejected `pipefail`; the job exited before the build command started | `--wrap` is not a Bash context. Use a direct command or submit an explicit Bash script. |

## Results & Parameters

Observed failure shape:

```text
/var/spool/slurmd/job<JOB_ID>/slurm_script: <LINE>: set: Illegal option -o pipefail
```

The failed job ended in approximately one second with a non-zero exit code and no container-build output. The corrected direct wrapper advanced into the manifest-driven build, proving the failure was limited to Slurm's wrapper shell contract.

Keep the scheduler parameters explicit (`partition`, `qos`, `account`, CPU, memory, time limit, output path, and working directory). They are independent of the shell choice and should continue to come from the reviewed job or manifest workflow.
