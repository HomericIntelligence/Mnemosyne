# Planning Unmerged Dependency Pure Classifier Extraction — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| CI drive-green and merge-wait stage plan | [ProjectHephaestus issue #1816](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1816) | `unverified`: plan never implemented; no tests or CI | Retained compatibility probe, pure classifier, timer parking, and transition requirements |
| Frozen pipeline contract | [ProjectHephaestus epic #1809](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1809) | `unverified` as implementation API | Treated only as temporary spec; all names require post-merge probing |
| Immediate dependency | [ProjectHephaestus issue #1815](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1815) | Unmerged during source planning session | Retained as explicit dependency gate rather than a presumed landed module |
| Immutable source record | [Mnemosyne base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/planning-unmerged-dep-pure-classifier-extraction.md) | Verified read at batch base; source guidance remains unverified | Supports provenance without duplicating the complete snapshot |

## Assumed API inventory from the source plan

The issue #1816 plan treated these as assumptions from unmerged prose, not landed facts:

- `WorkItem`, `Stage`, `StageOutcome`, `AgentJob`, `JobResult`, and route/disposition enums;
- `ctx.retry()`, `ctx.advance()`, `ctx.fail_back()`, and durable state methods;
- `Route(next=..., fail_routes=...)`, `ROUTES`, per-stage attempts, and work-item state;
- test fakes such as `FakeGitHub` and `FakeWorkerPool`;
- `on_job_done` signatures and job metadata.

Implementation must re-read the merged base, routing, work-item, job, and fake modules before
writing imports or fixtures.

## Outcome matrix

| Classifier outcome | Scheduler action | Deadline owner |
| --- | --- | --- |
| `GREEN` | Advance toward merge/next stage | Scheduler/work item |
| `FAILING` | Route to remediation or terminal failure per budget | Scheduler/work item |
| `PENDING` | Timer-park for bounded delay | Scheduler/work item |
| `NO_CHECKS` | Explicit product route, recorded in stage contract | Scheduler/work item |

The classifier never decides timeout from a poll count. Deadline expiry is computed from monotonic
elapsed time outside the classifier.

## Evidence boundary

Planning reads confirmed that the proposed package was absent and located legacy loop anchors. No
classifier, stage, timer-heap integration, or transition tests were implemented. Keep the entire
skill `unverified`.
