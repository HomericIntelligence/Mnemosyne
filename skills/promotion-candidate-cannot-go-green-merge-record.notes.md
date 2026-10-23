# Notes: promotion-candidate-cannot-go-green-merge-record

Supporting evidence for the main skill. All details are generalized from the
capture session; no repository names, pull-request numbers, commit hashes,
hostnames, or product identifiers are retained.

## Chronology of the capture case

1. A gate-observation promotion ran the full production gate set against a
   pinned candidate commit. Its stated purpose was measurement only, with
   close-as-read or supersession as the default disposition.
2. The umbrella gate resolved red. A written interpretation comment on the
   pull request recorded: total check set green except one umbrella failing
   on a small number of test shards and exactly one error class; each failing
   shard named; the class identified as fixture drift (a test fixture rebuilt
   its context without the test-root override, so specification revalidation
   rejected the temporary root at setup); the root cause already cured on the
   source branch by a merged fix with error-to-pass reproduction evidence;
   and the conclusion that these checks cannot pass on the candidate branch
   because the candidate pins pre-cure vintage.
3. The automated recommendation was supersession or close-as-read. The
   operator directed a force merge instead.
4. The observation promotion merged with elevated authority (single-parent,
   host-created commit; squash ceremony). Twelve minutes later the dependent
   release-label promotion, whose candidate was already at post-cure vintage,
   merged on top. Its pull-request body recorded supersession of an earlier
   closed candidate.

## Verification evidence (lineage trap)

After delivery, the observation merge object recorded by the host was checked
against the current base branch:

- `git merge-base --is-ancestor <observation-merge-oid> <base>` → NO.
- The base first-parent history contains the rewrite-created merge of the
  dependent promotion (two parents, same tree as the host-recorded squash
  object) and no entry for the observation merge.
- The host merge record for the observation promotion still reports merged
  state and keeps the recorded commit object identity.

Conclusion: the observation merge happened and is durably recorded by the
host, but the commit object is not on the base ancestry. Any lineage citation
must come from the host record plus an ancestry query, never from branch
listings.

## Record-comment structure that made the force merge safe

1. Total gate verdict: how many checks green, which umbrella red.
2. Per-failing-check enumeration: shard or check name → error class.
3. Class diagnosis: root cause, curing change on the source branch, and
   error-to-pass reproduction evidence on the curing change.
4. Boundary statement: the class is not a production blocker (fixture drift,
   not behavior).
5. Old-branch verdict: these checks cannot pass on this branch because the
   candidate pins pre-cure vintage.
6. Disposition recommendation with named options (supersede with a
   post-cure candidate, or close-as-read; operator may override with a
   recorded decision).

## Boundary of the verification

- The exact elevated-permission mechanism of the observation merge (admin
  flag versus direct host flow) was not re-verified; the durable fact is the
  merged state under a red umbrella plus the host-created commit.
- The later base rewrite that removed the observation merge from ancestry was
  observed from repository evidence only; its actor and authorization trail
  were not inspected.
- The skill governs the operator ceremony. Tool-side merge helpers stay
  fail-closed independently of this rule.
