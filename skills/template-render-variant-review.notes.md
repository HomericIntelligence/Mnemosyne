# Template Render-Variant Review — Notes

Supporting evidence for `template-render-variant-review`. All identifiers are
generalized. Repository names, pull-request numbers, commit identifiers,
hostnames, and local paths stay out of the durable record.

## Source session evidence

An independent review of one small pull request supplied the evidence. The
change touched a Python render module, a Jinja2 job-scheduler batch template,
and two test files (additions only, no deletions). The change inserted
conditional blocks into the template: a wait step, a cache step with
permission hardening, and an array-driven step that used parallel arrays.

The review bound an exact base and head, materialized both render inputs at
the reviewed head, and applied the render-variant workflow:

- **Variant space.** One base variant and two conditional variants selected
  by template conditionals. Three rendered scripts in total, one per variant.
- **Parse.** Each rendered script passed a shell syntax check.
- **Diff against pre-change renders.** Invariant regions stayed
  byte-identical in every variant: trap definitions, kill order, permission
  bits on a privacy-sensitive log directory, and log redirection.
- **Parallel-array parity.** Declared and referenced array elements agreed in
  the base variant and in the variant whose conditional extended the arrays.
- **Placement.** The inserted blocks rendered at top level, after the helper
  function definitions they referenced, and outside every heredoc, in all
  variants.
- **Exit-status chain.** The status capture assignment and the final `exit`
  survived in every variant. No new statement after the capture point reset
  the status.

## Retired hypotheses

The review started from source-diff hypotheses. Rendered evidence retired
each one:

1. The inserted blocks could render inside an earlier function body or a
   heredoc in some variant. False once rendered: placement was top level in
   all variants.
2. The conditional extension of the parallel arrays could break positional
   parity in a non-default variant. False: counts agreed in every rendered
   variant.
3. The inserted steps could mask the exit status on a failure path. False:
   the capture and final `exit` were untouched in every rendered variant.

Each hypothesis looked plausible in the template source diff. Only the
rendered artifacts could settle them.

## Boundary probes

Small shell probes checked runtime semantics that the renders imply but do
not execute (status capture behavior, process reaping behavior). These probes
matched the rendered assumptions. Version-dependent scheduler flag claims
were checked against the scheduler's installed public documentation rather
than executed, because no scheduler environment was available. The review
reported that limit separately from the rendered evidence.

## Limits

- Evidence binds to one reviewed revision of one project. The workflow is
  the reusable part, not the specific variants.
- No scheduler environment executed the rendered scripts; parse checks and
  diff evidence stand in for execution.
- The lesson adds a review method. It does not change the reviewed project.
