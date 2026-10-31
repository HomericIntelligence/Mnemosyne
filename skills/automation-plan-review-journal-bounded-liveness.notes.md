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
