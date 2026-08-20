# Multi-Repo PR Automation Loop Notes

Supporting cases for
[`multi-repo-pr-automation-loop-orchestration.md`](multi-repo-pr-automation-loop-orchestration.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Honest driver success path | [ProjectHephaestus PR #833](https://github.com/HomericIntelligence/ProjectHephaestus/pull/833), [#837](https://github.com/HomericIntelligence/ProjectHephaestus/pull/837), and [#839](https://github.com/HomericIntelligence/ProjectHephaestus/pull/839) | verified-ci | Origin sync, pre/post HEAD guard, explicit push refspec, paginated done gate |
| Bounded terminal wait and blocked classification | [ProjectHephaestus PR #1090](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1090) | verified-ci | Exited stable protection blocks only after zero failing and zero pending checks |
| Scoped drive-green | [ProjectHephaestus PR #1110](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1110) | verified-ci | Excluded unrelated bot PRs and limited done/arming gates to requested issues |
| Target-repository direct scopes | [ProjectHephaestus PR #1854](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1854) | verified-ci | Removed ambient-repository leakage and paired interrupted checkpoint with live merge proof |
| Direct PR terminalization | [ProjectHephaestus PR #2024](https://github.com/HomericIntelligence/ProjectHephaestus/pull/2024) | verified-local | Terminal state precedes branch adoption; latest logical item controls final result |
| Bounded organization source | [ProjectHephaestus PR #2436](https://github.com/HomericIntelligence/ProjectHephaestus/pull/2436) | verified-local | Numeric target requires one repo and rejects ambiguous org-wide scope |
| Stale completed-sweep re-plan | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/multi-repo-pr-automation-loop-orchestration.md) | mixed | Live reads disproved several old states and one prescribed root cause; proposed replacements stayed unverified |

## Campaign Detail

The driver sequence evolved through independent guards because each caught a different false-green:
branch synchronization prevents editing main under a PR name, the HEAD delta proves work occurred,
the explicit refspec proves where it was pushed, and pagination proves repository completion.

The stale-report case is intentionally `mixed`. Live PR state, current file reads, failed logs, and
ruleset queries were verified locally. Report-prescribed replacement versions and some rebase
mechanics were not executed and therefore remain unverified.

The organization-wide results in the superseded main include repository counts, elapsed times, and
historical merge ratios. They are campaign observations, not default concurrency or correctness
thresholds; use current rate limits, rulesets, and repository merge settings.

## Provenance

- Superseded main SHA-256: `aec05f039fa9c5faaeb6f7819e105e82f70542dc0b4c0b3e5ecfb5443f3cd9b5`
- Issue #3335 base: `e7f342098c41f3d5fda1bf7c7fedf754abdaaad2`
- Old/new version: `1.7.0` → `2.0.0`
