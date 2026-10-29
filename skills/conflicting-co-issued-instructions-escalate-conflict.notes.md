# Supporting evidence: conflicting co-issued instructions — escalate the conflict

Privacy-safe session detail for `conflicting-co-issued-instructions-escalate-conflict`.
Source session: 2026-10-27. Organization, repository, issue, host, and person
identifiers are withheld.

## Source context

A coordinator orchestrated a session-scoped worker for a single tracker issue.
One turn delivered two messages:

1. An execution contract: mandatory ownership gate, plan phase, delivery phase
   with an isolated worktree, signed commits, pull request, review exchange,
   and merge automation. The contract carried explicit stop-and-report clauses
   (ownership evidence appearing mid-run, provider failure, requirement
   ambiguity).
2. A closure ritual: "this session has reached Done", mandatory closing action,
   no other action permitted, verdict format restricted to a lesson link or an
   empty-dismissal verdict.

Observable session evidence at receipt: zero. No probes, no pull request, no
merge, no labels, no worktree, no branches, no tests ran. The closure ritual's
premise was therefore unverifiable. Executing the contract would violate the
ritual's no-other-action clause; executing the ritual alone would discard the
contract's required pre-work and ownership reporting. Contradiction.

## What the worker did

1. Reported the conflict through the contract's own ambiguity stop clause, in
   BLOCKED-disposition form, with both demands and the zero-evidence finding.
   No labels, comments, branches, worktrees, or merges occurred.
2. Attempted escalation through the interactive question tool. The host
   returned the cancellation text recorded below.
3. Selected the closure ritual as controlling on explicit stated assumptions
   (final instruction; the only instruction completable without writes; the
   contract's reporting duty already discharged by the BLOCKED report), then
   completed the ritual: corpus discovery, dedupe, privacy screening, isolated
   worktree delivery.

## Escalation-channel error (verbatim, host-generic)

> This non-interactive run cannot ask the user questions, so the question was
> cancelled. Continue without an answer; make reasonable assumptions and state
> them.

## Corpus dedupe record

Discovery ran against the validated local checkout at delivery base revision
`90ce47e9` (refresh verified, no freshness limits). Candidates inspected for
intent overlap (main files; companion notes grepped for conflict, escalation,
and channel terms):

- `planning-verify-issue-premise-before-implementing` — converts artifact
  claims into deterministic checks before acting. No instruction-conflict
  branch; no escalation-channel constraint.
- `stale-plan-already-resolved` — staleness of plans and logs against a moving
  default branch. No co-issued-instruction conflict.
- `planning-audit-finding-premise-verification` — audit-finding premises
  against the current repository.
- `verify-issue-premise-against-code-before-planning` — premise-token
  enumeration against code.
- `async-user-decision-continuity` — duplicate questions and delayed,
  conflicting user answers across turns. Different trigger: conflicting
  answers, not conflicting instructions; cross-turn, not one turn.
- `background-agent-silent-lane-wait-or-replace` — contains the string
  "stop-and-report" only as a dispatch-template instruction for replacement
  lanes; not a doctrine entry for instruction conflicts.
- `sibling-pr-mutually-exclusive-design-conflict` — design conflict between two
  pull requests; not instructions.
- `rubric-conflict-detection` — data-loader weight conflicts.
- `automation-moot-issue-regression-guard-pattern` — moot issue premises to
  regression guards.

Corpus-wide greps at discovery: zero main-file hits for "question tool"; zero
hits for "non-interactive run"; zero hits for "conflicting instruction" or
"contradictory instruction" outside unrelated domains.

Open pull requests against the delivery corpus were enumerated read-only at
discovery; none changes an entry for this intent; no Existing-PR mode applied.

## Disposition rationale

`create` — the intent (instruction-level conflict escalation with a
non-interactive channel constraint) is materially distinct from the
premise-verification family: different trigger (co-issued instructions vs.
artifact claims), different outcome (BLOCKED report vs. deterministic check),
and different failure modes (silent last-instruction selection; fabricated
ritual verdict; interactive question in a headless host). Amending any single
premise entry would hide the branches that changed the decision.

## Privacy screening

Removed: organization names, repository names, issue and epic identifiers,
host paths, user names, and model identifiers. Generalized forms used: "a
coordinator-orchestrated worker host", "a single tracker issue", "the delivery
corpus". The host error string is runtime-generic and identifies no
organization.
