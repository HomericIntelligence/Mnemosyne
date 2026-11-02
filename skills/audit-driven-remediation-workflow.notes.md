# Notes: Audit-Driven Remediation Workflow

Supporting evidence for
[`audit-driven-remediation-workflow`](./audit-driven-remediation-workflow.md). The complete prior main
is in [history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/audit-driven-remediation-workflow.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Multi-repository audit, triage, issues, and batched PRs | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/audit-driven-remediation-workflow.md) | verified-ci | Retained verify/deduplicate/classify/batch/publish sequence |
| Documentation and count reconciliation | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/audit-driven-remediation-workflow.md) | verified-ci | Retained canonical-source counts and generated-artifact discipline |
| Producer-to-consumer drift | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/audit-driven-remediation-workflow.md) | verified-ci | Retained write/read transport table and integration path |
| Cross-module duplicate defect | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/audit-driven-remediation-workflow.md) | verified-ci | Retained structural sibling search and shared regression rule |
| Post-completion strict review | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/audit-driven-remediation-workflow.md) | verified-ci | Retained independent reviewer requirement and evidence synthesis |
| ProjectHephaestus epic #1809 stale-checkout review | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/audit-driven-remediation-workflow.md) | verified-ci | Retained fetch and `git show origin/main` source-of-truth rule |

## Case Details

The source combined audit workflows for code quality, hygiene, documentation, implementation
alignment, compatibility removal, and skill-corpus remediation. Durable commonality is finding
reproduction, ownership/severity classification, deduplication, coherent batches, and runnable
acceptance evidence; corpus-specific phrase lists and fleet push limits remain historical context.

A producer-side verdict was once emitted without all consumers reading it. Mock-heavy tests passed
because they bypassed the real transport. Searching reads independently and adding an integration
path exposed the gap. A related copy-paste defect in a sibling module motivated the structural search
step after each bug-pattern fix.

In a final strict review of freshly merged work, agents used a checkout behind `origin/main` and
reported missing or stale code. Binding all reviewers to one fetched SHA and reading with `git show`
corrected the evidence. Reviewer outputs still required deduplication and reproduction before issue
creation.

## Compaction Disposition

- Kept in main: authority freeze, triage matrix, deduplication, batch boundaries, testing,
  producer-consumer and sibling audits, independent review, and cross-repo evidence rules.
- Moved here: project-specific cases and why the later phases were added.
- Archived only: long issue/PR templates, corpus phrase lists, and operational fleet limits.

## 2026-11-01 amendment evidence

A repository-wide static-analysis sweep reported 862 findings in one checkout, with 61 of them
severity errors. Reading every error site showed three distinct populations: deliberate idioms the
detector could not model, text-level misfires, and a few real causes dropped from log output. The
remaining 676 findings were pre-existing size, parameter, and nesting measurements, deferred as
separate design work. Text-level rule disablement in repository configuration required reading all
hits for that rule first.

The suppression mechanism needed a probe. The detector reports the construct line, not the handler
line, so a directive above the `try` body suppressed nothing. Verification used a scratch file with
one finding, then a rescan, then a check that a plain trailing comment on the handler line cleared
it. A formatter then split one handler header, which moved a trailing directive onto a closing line
where it stopped applying; shortening the reason text restored the single-line form.
