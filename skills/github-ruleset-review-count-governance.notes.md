# GitHub Ruleset Review-Count Governance — Case Notes

These notes retain applied policy cases, live values, and project-specific outcomes. The complete
superseded main is archived only in history.

## Case Index

| Case | Source | Verification |
| --- | --- | --- |
| Odysseus human-review gap across four variants | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/github-ruleset-review-count-governance.md) | verified-local |
| Organization-wide automation self-review deadlock | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/github-ruleset-review-count-governance.md) | verified-ci |
| Committed-vs-live ruleset drift and runner backlog | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/github-ruleset-review-count-governance.md) | verified-ci |
| CI/CD-only merge-contract documentation | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/github-ruleset-review-count-governance.md) | verified-ci |

## Human-Review Regime

Odysseus issue #178 / PR #308 found count zero in four canonical files: org/repo and each active
variant. The active apply path meant fixing only the two files named by the issue would not close
the deployed gap. Each count changed from zero to one, a CI guard was added, JSON parsed, and other
pull-request/enforcement fields remained unchanged. Local verification passed; the archived row
classified the v1.0 case `verified-local`.

Recorded bypass actor IDs came from committed JSON and were not independently confirmed against
live GitHub in that case. They remain case evidence, not portable constants or proof of bypass
semantics.

## Automation-Author Regime

Across 17 active HomericIntelligence repositories, automation authored PRs as the sole operator.
GitHub disallowed self-approval, so a nonzero count made green auto-merge PRs unsatisfiable. The
approved remediation set the count to zero on both classic protection (where present) and repository
rulesets while preserving required checks and thread resolution. Three already-green PRs merged as
soon as the review gate was removed.

This result depends on the actor topology. It is not evidence that all single-maintainer or automated
repositories should use zero approvals.

## Live-Drift Diagnosis

Odysseus PR #394 corrected a repeated false diagnosis. Committed repository JSON said one approval
and eight required checks, while the live `homeric-main-baseline` repository ruleset required zero
approvals and eleven contexts. PRs #388 and #390 merged without review, proving review was not the
gate; queued hosted runners were the delay.

The committed files were synchronized only after field-by-field comparison. The schema guard changed
from a universal `>=1` assertion to exact per-scope policy: organization files one, repository files
zero. An accidental full-file JSON reformat was reverted so reviewers could see the policy delta.

The recorded live ruleset ID and context count were observations from 2026-07-13. Always query them
again; neither is a stable reusable parameter.

## Documentation Contract

ProjectHephaestus PR #2533 aligned `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, and the architecture
document with an intentional zero-review single-maintainer regime. Required GitHub checks became the
merge-eligibility contract. Human confirmations for force updates, tags, or swarm deployment remained
agent-safety controls rather than GitHub approving reviews. Focused docs checks and the recorded
6,874-test pre-push suite passed.

## API and Diff Discipline

- Read classic protection and rulesets separately; a classic 404 is not a ruleset result.
- Find the branch-applicable live ruleset rather than assuming the first list entry enforces main.
- Fetch the full ruleset before an authorized PUT and preserve every unrelated rule.
- Compare required-check sets as sets, not just counts.
- Keep activation/enforcement out of a review-count-only change.
- Treat `mergeStateStatus: BLOCKED` as a prompt to inspect checks and reviews, not a diagnosis.

## Compaction Disposition

- Kept in main: two-regime decision, live-first diagnosis, dual layers, variant scope, exact guard,
  API workflow, safety boundaries, and named failures.
- Moved here: organization size, PR outcomes, live IDs/context counts, and documentation metrics.
- Archived only: repeated shell transcripts, verbose file-by-file results, and the complete prior
  main.
