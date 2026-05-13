# PR288 RL360 xLLM Launcher Review Notes

Source PR: `https://github.com/LLM360/RL360/pull/288`

Review:

- ID: `4284402017`
- State: `CHANGES_REQUESTED`
- Head SHA: `825525d73b24be56a444ffab90de5fc3164261ed`

Inline comments posted by `mvillmow`:

| Comment ID | Path | Line | Finding |
| --- | --- | ---: | --- |
| `3236617139` | `scripts/train/run-xllm-375B-bbq-r3-32k.sh` | 9 | Missing `final_logs/` parent directory for Slurm output before shell body starts |
| `3236617145` | `scripts/train/run-xllm-375B-bbq-r3-32k.sh` | 667 | `WANDB_API_KEY` written into Ray runtime env JSON, generated script, and argv |
| `3236617149` | `scripts/train/run-xllm-375B-bbq-r3-128k.sh` | 703 | Same W&B/runtime-env exposure in 128k launcher |
| `3236617153` | `scripts/train/run-xllm-375B-bbq-r3-32k.sh` | 381 | Unconditional fallback `xllm_sglang.py` overlay defeats native-first SGLang behavior |
| `3236617156` | `scripts/train/run-xllm-375B-bbq-r3-128k.sh` | 399 | Same native-first overlay concern in 128k launcher |

Raw review summary shape:

```markdown
Overall: NO-GO / CHANGES_REQUESTED

Per-file grading:
- 32k launcher: D / No-Go
- 128k launcher: D / No-Go

Blocking themes:
- Slurm output directory must exist before `sbatch`
- W&B secrets must not be placed in generated scripts or argv
- SGLang native bridge must remain preferred over fallback overlay
```
