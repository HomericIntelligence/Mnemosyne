# Notes: Audit-Driven Remediation Workflow

Supporting evidence for
[`audit-driven-remediation-workflow`](./audit-driven-remediation-workflow.md). The complete prior main
is in [history](./audit-driven-remediation-workflow.history).

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
