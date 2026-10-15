# PR CI Failure Triage — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Force-push rollup showed cancelled old-head runs | [immutable source documenting ProjectOdyssey PR #5380](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/pr-ci-failure-triage-preexisting-vs-introduced.md) | `verified-local` readback | Retained exact-head filtering |
| Concurrency superseded failed-job rerun | [ProjectHephaestus PR #1073](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1073) | `verified-ci` | Retained newest-applicable-run rule |
| Markdownlint/security failures mislabeled pre-existing | [immutable source case index](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/pr-ci-failure-triage-preexisting-vs-introduced.md) | `verified-ci` | Retained execution evidence over diff intuition/labels |
| Coverage genuinely failed on main | [immutable source documenting ProjectKeystone PR #552](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/pr-ci-failure-triage-preexisting-vs-introduced.md) | `verified-ci` | Retained separate-fix/tracking governance path |
| Duplicate stale commit broke all sanitizers | [immutable source documenting ProjectKeystone PR #436](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/pr-ci-failure-triage-preexisting-vs-introduced.md) | `verified-local` | Retained branch reconstruction rather than tip amend |
| Generated Node harness exceeded hosted argv budget | [ProjectOdyssey PR #5762](https://github.com/HomericIntelligence/Odyssey/pull/5762) | `verified-ci`: failing 254-test run then passing 259-test run | Retained stdin transport and hosted-Linux regression |
| Base-updated long-lived branch: branch test asserted semantics trunk had retired, a lockstep workflow/validator pair was half-moved, and local-only host windows duplicated a pristine trunk failure set | monorepo merge-failure triage outside the host org; 32-way sharded pytest, signed-commit rulesets, staged shard planner | `verified-ci`: all required checks green after the ported test, atomic pair, and FYI dispositions | Retained file-provenance classes, atomic-pair rule, and pristine-base attribution oracle |
| Path-filtered required check failed on two PRs with exit 4 before any test count; identical sibling PRs on the same base that stayed outside the `paths:` filter showed no run | serving-stack repository outside the host org; fixed-selector ownership-policy job with an uploaded evidence directory | `verified-ci`: the rebased branches' path-filtered job (and its sibling job) went green with no diff change; the failing PRs' other ~50 checks were green throughout | Added trigger-filter audit, stale-plan-input classification, evidence-artifact diagnostic, and the main-repaired base-update resolution |

## Stale plan inputs detail

The check pinned a fixed case list in-repo. A rename on main left the base copy naming a
removed parametrized test, so collection aborted with a usage error (`UsageError`, pytest
exit 4, "no tests ran") before any test total. The failure log collapsed to that one line;
the uploaded evidence directory's selection record (source SHA, zero collected cases, full
pinned list) named the mismatch directly. `git log -S <missing-selector> -- <pinned-list>`
located the renaming change, and `git log -1 origin/main -- <pinned-list>` showed current
main already carried the corrected selector. The path filter had hidden the failure from
main and from every PR whose diff stayed outside the `paths:` list, so no run-based
comparison could classify it. Remediation was a recorded base update to the repaired main,
giving a green exact-head run with an unchanged PR diff.

## Classification record

| Check | PR head/run | Main head/run | Signature comparison | Class | Action |
| --- | --- | --- | --- | --- | --- |
| Fill per failure | Immutable SHA and URL | Immutable SHA and URL | Same/different/not applicable | Evidence-based label | Fix/rerun/follow-up/wait |

## E2BIG detail

`E2BIG` arises at `execve`: combined arguments and environment exceed the platform budget before the
child runtime executes. Moving generated JavaScript to stdin retains code semantics while shrinking
argv. Test the largest intended payload and verify stderr/stdout parsing still works.

## Evidence boundary

The cases establish the classification workflow on GitHub Actions. Live required contexts,
administrative policy, merge-preview semantics, and runner limits can change and must be re-read.
