# Notes: slurm-job-name-truncation-false-absence

Supporting evidence for the main entry. Generalized from a production
incident; all site identifiers removed.

## Evidence

- Setting: a production rollout on a Slurm cluster with several operators
  acting in parallel. Deployed job names follow a hierarchical pattern
  (`<org>-<cluster>-<role>-<detail>`) longer than 24 characters, so role
  and detail tokens sit beyond common column cuts.
- Failing probe: `squeue -u <user> -o "%.10i %.24j %.8T %.10M %.18R"`
  filtered with `grep` on a role token that starts after the 24-character
  cut. The command returned only an older, shorter-named job; the tracked
  job matched nothing and read as ended.
- Correct probe: `squeue -j <id>` returned the tracked job as `RUNNING`
  with over ninety minutes of elapsed time on its expected node.
- Impact: one provisional "job is gone" statement inside an active
  investigation, corrected in the same round and recorded in the rollout
  log. No external action was taken on the wrong conclusion.
- Companion hazard found in the same session: even with full-width names,
  a prefix pattern matched jobs from two generations that shared the
  leading name portion. Exact-token matching or identifier queries are the
  only safe selections.

## Prevention Options

- Prefer unbounded name output in operational aliases and scripts: `-o %j`
  with no width, or a cap such as `%.64j` that exceeds the longest
  deployed name.
- Publish the submitted job identifier in every status record the team
  maintains, so consumers never need name matching for lifecycle checks.
- If a fixed-width listing is unavoidable, match only tokens that lie
  fully inside the guaranteed-visible window, or switch to
  `squeue --noheader -o "%i %j %T" | awk '$2 == "exact-name"'`.

## Recovery Path Applied in the Session

1. A second data source (a live health probe) contradicted the listing
   conclusion.
2. Re-query by exact identifier; confirm state, node, and elapsed time.
3. Publish the correction with the by-identifier evidence in the shared
   rollout log.
4. Convert the case into this durable entry.

## Relation to Existing Entries

- `reconcile-before-retry-mutation-status-loss` covers the complementary
  case: an operation whose terminal status was never observed. This entry
  covers observed-but-misleading listing output. The two rules chain: a
  listing never settles a lifecycle claim, and an unobserved mutation
  never settles an effect claim.
