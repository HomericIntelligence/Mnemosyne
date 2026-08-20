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
