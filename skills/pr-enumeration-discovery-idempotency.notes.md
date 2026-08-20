# Notes: PR Enumeration, Discovery, and Idempotency

Supporting evidence for
[`pr-enumeration-discovery-idempotency`](./pr-enumeration-discovery-idempotency.md). Exact superseded
content is in [history](./pr-enumeration-discovery-idempotency.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Default-30 and finite-limit truncation | [immutable source at the #3335 base](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pr-enumeration-discovery-idempotency.md) | verified-ci | Kept paginated API rule and hard-cap warning |
| Bot PR synthetic issue-key union | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pr-enumeration-discovery-idempotency.md) | verified-ci | Kept `user.type`, stable-key union, and conflict handling |
| Duplicate creation and branch ownership | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pr-enumeration-discovery-idempotency.md) | verified-ci | Kept repeated mutation guard and re-query-after-error |
| Bulk status timeout and stale routing | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pr-enumeration-discovery-idempotency.md) | verified-ci | Kept lightweight enumeration, per-PR rollup, and BEHIND/BLOCKED distinction |
| Soft-fail subprocess exception symmetry | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pr-enumeration-discovery-idempotency.md) | verified-ci | Kept command/timeout/OS/parse boundary |
| Planner skip gate and merged closing PR | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pr-enumeration-discovery-idempotency.md) | verified-ci | Kept phase-symmetric discovery and zombie closure |
| Operator-side stale issue/branch triage | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pr-enumeration-discovery-idempotency.md) | verified-ci | Kept refetch/main proof, API head name, and add/add evidence |

## Case Details

### Enumeration and bot union

The original failures began with list defaults and later showed that merely increasing `--limit`
does not mean exhaustive. REST pagination provided stable page behavior. Dependency bots required a
second pass because issue-linked discovery had no closing reference; API account type was more
reliable than username spelling. Synthetic key and PR number had different roles, and confusing them
caused lookup errors.

### Bulk queue and subprocess contracts

Fetching `statusCheckRollup` across a large queue caused gateway timeouts. Separating lightweight PR
identity from bounded per-PR status avoided the all-or-nothing query. A top-level discovery error
must remain an error. Only helpers explicitly documented as soft-fail may return empty, and those
must handle timeout and missing executable as well as nonzero status and parse failure.

### Skip symmetry and zombies

The implementation phase once detected existing PRs only after the planner had already spent an
agent call. Moving the same lookup ahead of both phases established symmetric idempotency. Searching
only open PRs still missed merged closing PRs, leaving open zombie issues. The correction searched
all states, verified the merged content on main, and closed the issue with the PR reference.

### Stale local branches

An issue-named branch had a SHA mismatch and a large diff that effectively reversed current main.
The PR's actual head name came from GitHub, not convention. An `add/add` conflict during attempted
reuse was evidence that the target already existed on main, prompting verification rather than a
manual overwrite.

## Compaction Disposition

- Kept in main: pagination, union/idempotency, state verification, exception contracts, routing,
  zombie detection, and stale-branch safety.
- Moved here: incident narratives and why each routing rule was added.
- Archived only: implementation-specific helpers, long tables, and session transcripts.
