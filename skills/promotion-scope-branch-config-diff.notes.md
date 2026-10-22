# Notes: promotion-scope-branch-config-diff

Supporting evidence for the main entry. Generalized; identifiers withheld per
the privacy rules.

## Session evidence (2026-10)

Context: promotion-campaign scoping for a serving platform with two protected
branches, a source branch and a deployed branch. Deployed model rosters,
routing policy, tenant accounting weights, capacity policy, and scheduler
accounts are declared in repository configuration that ships inside the release
artifact (compiled-in data files).

Actions and observations:

- Enumerated every open issue (several hundred) and filtered them against the
  campaign's acceptance requirements. This produced the tracked scope.
- Ran `git diff origin/<deployed> origin/<source> -- deployment-contexts/` as a
  completeness check. The diff showed four deployed model entries removed on
  the source branch, together with their routing policies, tenant accounting
  weights, capacity/queue policy blocks, and a queue-evidence list. The
  deployed branch still declared all of them.
- `git rev-list --left-right --count origin/<source>...origin/<deployed>`
  showed the source branch far ahead and containing the deployed history.
  The ahead/behind signal said nothing about the missing declarations.
- `git log -S'<removed-model-name>' --oneline origin/<source> -- <path>`
  identified the removing commit: a large root-repair change whose message
  documents only the root migration. The removal was unrecorded collateral,
  consistent with a later change's statement that production serving was kept
  down during a bootstrap.
- Keyword searches over issue bodies ("removed", "restore", "missing", entry
  names) confirmed no open issue tracked the removal. One issue about
  scheduler-account drift on the same paths proved the same failure class was
  known in one place but did not cover the roster.
- Filed one restoration issue (removed content, consequence at promotion,
  restoration requirements, derived-identity churn) and linked it as a blocker
  of the promotion epic.

## Why the derived-identity warning matters

In this platform, editing a deployment context changes the computed context,
release, and component identities. Golden-render digests in the test suite are
bound to those identities, so a roster restoration forces digest regeneration
in the same change and must land as its own reviewed change before the
promotion. Any roster-like configuration that participates in content
addressing has the same property.

## Failure mode the diff catches

A promotion adopts the source branch's embedded configuration verbatim. When
the source branch declares less than the deployed branch runs, the promotion
itself removes production capability even if every tracked issue is fixed.
Diff-based gating makes that removal visible before the promotion request
opens.
