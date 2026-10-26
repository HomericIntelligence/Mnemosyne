# Notes: slurm-batch-job-result-verification

Supporting session evidence (privacy-safe summary; cluster names, account names, job
IDs, paths, and product names withheld). Observations are from one live benchmark sweep
on a Slurm-managed shared cluster.

## Case: strict-mode expansion abort masked as scheduler success

- A benchmark harness generated per-variant batch jobs through one wrapper script per
  job. The wrapper expanded variant parameters, ran the payload, and printed a status
  line at the end.
- One variant group carried a parameter whose expansion had no safe default under
  strict mode (`set -u`; the fix was a `${EXTRA_ARGS:-}`-style guarded expansion). The
  payload aborted at first reference. The wrapper still executed its trailing
  statements, so Slurm recorded State COMPLETED and ExitCode 0:0 for the group's jobs.
- The job output files contained no visible crash for a reader who only scanned for
  error text; the strict-mode abort message did not reach the logs that were checked.
- Detection came from the artifact side: the group's result directories had no summary
  artifacts at all, and no payload exit record existed.
- Repair: guard the expansion in the harness, resubmit the group, and verify the new
  jobs with the same artifact checks. The resubmitted jobs produced the required
  artifacts and exit records.

## Detection checklist that worked

1. Before the sweep, list the required artifacts per variant (names and a parse rule).
2. After completion, accept a variant only when the payload exit record is 0 AND every
   required artifact exists and parses.
3. Classify anything else as failed regardless of scheduler state; repair the wrapper,
   resubmit, and verify again rather than re-classifying the failed jobs as measured.

## Why scheduler fields were misleading here

- Slurm's ExitCode for a batch job is the batch script's exit code, which is the exit
  status of the script's last command. Any wrapper pattern that lets trailing
  statements (echo, cleanup, bookkeeping) run after a payload abort will record success.
- `sacct` State aggregation for swept or re-queued jobs compounds the problem for
  automation that consumes State alone.
