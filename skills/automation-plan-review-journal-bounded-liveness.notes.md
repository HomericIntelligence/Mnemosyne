# Notes: Automation Plan-Review Journal — Bounded Liveness

Supporting evidence for `automation-plan-review-journal-bounded-liveness.md`. Paths and
identifiers are generalized; no issue numbers, session identifiers, or host details appear
in this file.

## Run evidence (2026-10-28 wave, admission-time marker-identity failure)

A 50-issue wave of the queue-based plan/review loop ran across one repository's full open
backlog. One issue in the wave carried legacy comment history: several historical
comments, each actor-owned, each bearing the `issue-review` marker.

- Pipeline summary line (stage `pr_review`, lane time 27.0 s):
  `FAIL:plan admission failed: plan marker identity conflict: ambiguous actor-owned comment aliases for '<!-- <org>:issue-review -->'; manual recovery is required`
- The lane stopped before any review job ran. This is the fail-closed behavior the
  canonical rule requires: with two or more candidate canonical comments, the loop cannot
  select one, and no automated disambiguation exists.
- Context note: the same issue had already been closed by a different lane's merged PR
  earlier in the wave window. The admission failure surfaced when the loop re-touched the
  issue afterwards; the class is latent for any re-processing of a legacy comment-heavy
  issue, independent of the issue's open/closed state.
- Recovery followed in this wave: none — the issue was already closed, so the operator
  decision was report-only. The step-7 recovery procedure in the main entry is the
  designed path for an issue that still needs processing.
- Distinction from the migration context: the main entry's step 7 previously named only
  the migration dry-run/apply surface of the same guard ("a malformed marker or
  conflicting legacy identity fails only that issue"). This case is the admission and
  review-routing surface of the same guard, observed live outside any migration.

## Plan-size decomposition evidence (2026-11-23)

A documentation-only model-enablement plan was 12,479 payload characters after an
amendment. The plan review had one real NOGO. The stage requested lossless
decomposition with trigger `lossless-size` and posted a four-unit draft.

The draft used these verification commands:

- a formatter check on a Markdown file;
- a named documentation recipe in a repository that had no recipe runner.

The decomposition grammar accepts both command forms syntactically, so generation
passed. The independent review rejected the draft because the commands were not
executable for the work. Three generation rounds were rejected. The lane ended
`BLOCKED:plan_decomposition_generation_exhausted` with exit code 1.

Recovery: rewrite the canonical plan to 9,287 payload characters. The rewrite kept
every requirement and every review fix. The plan was then below the observed
12,000-character canonical-plan context limit, so the size check no longer requested
decomposition. Re-run planning and plan review; planning fast-forwards when a canonical
plan exists.
