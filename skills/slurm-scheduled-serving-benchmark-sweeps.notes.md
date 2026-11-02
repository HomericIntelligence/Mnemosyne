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
- Re-verified on 2026-10-31 through 2026-11-01 in a second campaign on a
  different cluster. The transfer measurements below come from real job
  evidence there, not from scheduler documentation.

## Measured environment transfer (second cluster)

Each row was observed in a real job's log or environment:

- Inline comma and space forms of `sbatch --export`: `/proc/self/environ`
  inside the job step was empty; the payload gate failed on the first
  contract variable.
- `--export-file` with six `NAME=value` lines: only the first line became an
  environment variable. The remaining five lines appeared as literal text in
  the step's stdout, immediately above the gate failure, which looked like a
  correct contract echo until `/proc/self/environ` was checked.
- `--export=ALL` with the variables exported in the submitting shell: all
  values arrived.
- Derived per-variant scripts: six `printf %q` assignments inlined after the
  strict-mode line; the gate passed on every submission.

## Container boundary (second cluster)

A `srun --container-image` step did not inherit any batch-shell variable.
The working pattern:

```bash
# batch shell: pass the contract as positional arguments
srun --container-image=... bash payload.sh "$VARIANT_ID" "$GPUS" "$MEMFRAC"

# payload.sh: require positionals, then export for child processes
VARIANT_ID="${1:?submission arguments missing}"
export VARIANT_ID
```

The same campaign exposed a `set -u` hazard in that pattern: a function
called with fewer arguments than its signature reads failed on the bare `$2`.
Read optional positionals as `"${2:-}"` in every payload that uses strict
mode.

## User-site shadow inside a container (second cluster)

The home directory was mounted into the container. A three-release-old
user-site copy of a pydantic helper package under `$HOME` shadowed the
image's newer copy; the engine failed with `AttributeError` on a symbol that
the image's own package does define. Diagnosis required one CPU probe job:
print `module.__file__` inside the container and compare it with the image
path. The fix was payload-local: `PYTHONNOUSERSITE=1` plus a shared overlay
directory prepended to `PYTHONPATH` that carries the newer package. Newer
symbol presence was verified with `grep` on the staged overlay before the
next submission, not assumed from the version string: the PyPI release that
the image pinned did NOT contain the symbol; only a later release did.

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
