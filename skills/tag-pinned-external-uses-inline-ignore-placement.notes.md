# Notes: tag-pinned-external-uses-inline-ignore-placement

Supporting evidence for
[tag-pinned-external-uses-inline-ignore-placement.md](tag-pinned-external-uses-inline-ignore-placement.md).
This file is not part of normal retrieval.

## Provenance

- Source: one governance-adoption session that added seven read-only reusable-workflow calls to a
  shared tooling repository, plus one durable learning pass over that session.
- Recorded: 2026-11-01.
- Verification class: `verified-local`. The failure and the repair were reproduced on the local
  enforced scan command and on the repository's own required workflows.

## Scan evidence

The enforced command, before the repair:

```bash
uv run zizmor --no-online-audits --min-severity medium .github/workflows/ .github/actions/
```

Result before the repair:

- exit status: 14;
- nine high `unpinned-uses` findings, one per new reusable-workflow call plus two pre-existing
  workflow-level `excessive-permissions` findings;
- the counts line already read a nonzero ignored count, which made the failure easy to misread.

Result after the repair:

- exit status: 0;
- no unignored finding;
- the ignored count increased by the number of annotated sites.

A baseline run of the same command against the unmodified workflow tree, in a separate directory,
reported no findings. This shows that the change introduced every high finding, and that the
suppression did not hide a pre-existing defect.

## Why the comment placement matters

The scanner reports a position for each finding. The position for an unpinned reference is the
`uses:` value line. Inline suppression applies to the reported line. A comment on the job key, the
`uses:` key, the `permissions:` block, or the lines above the job does not reach that line.

The guarded edit is small and testable:

1. Move one comment to the end of the `uses:` value line.
2. Add a short rationale block above it.
3. Re-run the enforced command and keep the exit status.

## Permission-scope detail

A read-only job declares `permissions: contents: read` for itself. A job-level declaration replaces
the workflow-level grant for that job. Thus, the new job does not inherit the write grants that a
tag-push job needs. The scanner reports the workflow-level grant, not the new job. Annotate only the
grant that a job needs, and name the job in the rationale.

## Test interaction

One structural contract test read the workflow file with a YAML loader that maps comments to data
keys. A comment-only edit can therefore change the loaded shape. Re-run the workflow tests after
each comment edit, and prefer functional assertions on the resolved values over assertions on the
raw text.

## Reviewable warning signs

- A gate result is judged by counts text, not by exit status.
- A suppression is added above a block instead of on the reported line.
- A suppression covers a rule class, a severity, or a whole file instead of one line.
- A read-only job omits its own `permissions` block, or relies on inheritance.

## Evidence limits

- The source repository is private to the session. The numbers above are retained; internal paths,
  names, and identifiers are not.
- The finding counts apply to this workflow layout. A different set of call sites changes the
  counts, but not the placement rule.

## Related corpus entries

- `gha-security-scanning-supply-chain` owns the scan configuration, the command parity between the
  required and scheduled roots, and the fail-closed policy. This entry covers the suppression
  placement for a policy-approved tag pin and does not replace it.