# Release Workflow Planning Assumptions and Risks — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| First-release planning revisions R0 through R3: version lineage, root-SHA compare link, producer/validator parity, manifest/runtime/signing checks | [immutable source documenting ProjectOdyssey issue #189](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/release-workflow-planning-assumptions-and-risks.md) | `unverified`: planning/read-only discovery only | Reusable discovery and reviewer decisions retained in main |
| Canonical `release` status bootstrap in a never-tagged repository | [Mnemosyne issue #2913](https://github.com/HomericIntelligence/Mnemosyne/issues/2913) | `unverified`: plan-only | Retained as same-PR release-contract bootstrap guidance |
| Corpus compaction and evidence preservation | [Mnemosyne issue #3335](https://github.com/HomericIntelligence/Mnemosyne/issues/3335) | Verified by batch checks, not by release execution | Session-specific compaction details live in history/PR, not main guidance |

## Review worksheet

Record observed values rather than completing this table with assumptions:

| Question | Command or source | Observed result | Implementation consequence |
| --- | --- | --- | --- |
| Existing tags | `git tag --list --sort=-version:refname` | Fill during implementation | Establish real lineage |
| Published releases | `gh release list` | Fill during implementation | Distinguish tag from publication |
| Manifest version/table | Parse the live manifest | Fill during implementation | Select lookup and error contract |
| CHANGELOG sections/footer | Read live file | Fill during implementation | Define link and parity rules |
| Runner Python | Workflow setup plus project constraints | Fill during implementation | Decide `tomllib` or declared fallback |
| Signing capability | Git config and secret-key probe | Fill in tag-producing environment | Require signing or explicit alternate behavior |
| Required context | Workflow job names plus live ruleset | Fill during implementation | Attach real validation to pinned check |
| Action revision | Canonical action repository | Fill at planning time | Pin immutable SHA |

## Nuance preserved from the planning iterations

- An issue can be directionally correct while citing stale files or nonexistent commits. The
  contradiction itself is a planning finding and must be surfaced.
- A syntactically valid `/commits/main` link still violates a plan whose test requires
  `/compare/...HEAD`; artifact and validator must be executed together.
- In a never-tagged repository, a root commit is a real compare base. A made-up historical version
  tag is not.
- Required-check governance applies to emitted check-run names and actual reusable-workflow call
  paths. An orphan workflow or unrequired green job supplies no protection.
- Dry-run validation and publication are separate modes: pull requests verify without side effects;
  tag workflows prove parity before publishing.

## Evidence boundary

Both source cases are planning artifacts. They establish a checklist and known planning failure
modes, not working release automation. Keep `verification: unverified` until implementation and CI
evidence are linked.
