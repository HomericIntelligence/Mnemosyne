# Notes: external-benchmark-config-match-adoption

Privacy-safe provenance. Recorded from an inference-serving engine adoption
evaluation completed 2026-10. The evaluation concerned adding a third
serving engine to a tracked GPU fleet that serves a large mixture-of-experts
model, with a public inference benchmark as the reference corpus. All
project, repository, issue, and model identifiers are withheld per the
privacy rules. Public reasoning sources were public benchmark dashboards
and configuration namespaces, plus vendor GPU product documentation for
precision-support matrices.

Decision branches that generalize:

- The strongest published results for the candidate engine were measured
  on the next GPU generation (hardware acceleration for the quantized
  format) while the fleet runs the previous generation (emulated path).
  This single mismatch sufficed to treat the published numbers as
  hypotheses rather than targets.
- The requester declined a pre-committed adoption threshold and chose a
  data review. This session supplied the evidence pattern: measured
  variance and measured operational costs make early thresholds unstable.
- The published configurations were owned by an official benchmark
  pipeline; local reproductions carry an unofficial label by policy of
  that pipeline. Cite the official pipeline when comparing.

Corpus comparison for this creation (bound to the local delivery revision):
no existing entry covers the intent

- nearest neighbors and why they do not cover it:
  - `inference-benchmark-warmup-regime`: measures run-internal validity
    (warmup, cache state, baseline traceability) of experiments you run
    yourself. It does not cover a priori transfer of an external
    published result onto a different deployment configuration.
  - `benchmark-artifact-triage-pr-splitting`: publication hygiene for
    benchmark result artifacts, not adoption gating.
  - `ci-release-gate-stricter-than-branch-green-not-transferable`: CI
    gate transfer, different domain.

Disposition: create. No open pull request targeted the corpus area at
publication time.
