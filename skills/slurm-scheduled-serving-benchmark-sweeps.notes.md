# Notes: Slurm-Scheduled Serving Benchmark Sweeps

Supporting detail for `slurm-scheduled-serving-benchmark-sweeps.md`. All
identifiers are generalized under the privacy rules.

## Provenance

- Consolidated on 2026-10-27 from an operating-constraints handoff inside an
  internal long-context serving benchmark campaign, and re-checked in a
  follow-up delivery session on the same date.
- The comma-form export failure cost two complete job batches. The failure
  signature was an application-level error in the payload log; the submission
  environment was only found missing after an in-job echo was added.
- The warmup/parser constraint was recorded after engine startup failures
  that went away only with the engine warmup-skip flag.
- The per-level file rule was validated across a queue preemption: levels
  with files survived, and the resume re-ran only the missing level.

## Environment gate pattern

```bash
# First statements of the batch script.
for var in CFG MODEL_PATH SEED LEVEL; do
  eval "val=\${$var:-}"
  if [ -z "$val" ]; then
    echo "MISSING SUBMISSION VARIABLE: $var" >&2
    exit 2
  fi
  echo "$var=$val"
done
```

The gate fails before any GPU is occupied, which keeps the error cheap on a
shared queue.

## Trailing-block parse

```bash
awk '/^###?$|^Serving Benchmark Result/{found=1} found{print}' "$f" | \
  tail -n 40
```

Per-level files from common serving harnesses end with a summary block and
carry no in-file concurrency marker. Take the level from the filename or the
submission record, never from file position.

## Boundary against existing entries

- Measurement hygiene (cache state, warmup samples, variance, baseline
  resolution): use `inference-benchmark-warmup-regime`. This entry covers
  only scheduler submission, engine startup, and artifact layout.
- Payload success verification after completion: use
  `slurm-batch-job-result-verification`. This entry covers the state claim
  before and during the run and defers to that entry after completion.
- Publication triage of the retained artifacts: use
  `benchmark-artifact-triage-pr-splitting`.
