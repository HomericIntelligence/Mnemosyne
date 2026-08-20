# GitHub Labels as State Vocabulary — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Initial three-label workflow, provisioner, issue-open tagging, reviewer mutation, implementer gate, and legacy backfill | [ProjectHephaestus PR #707](https://github.com/HomericIntelligence/ProjectHephaestus/pull/707) | `verified-local`: 911 automation tests, Ruff, and mypy passed locally; CI was still running at capture | Core state contract and operational commands remain in the main skill |
| Missing no-go to needs-plan transition | [ProjectHephaestus issue #1857](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1857) | `unverified`: designed and unit-test-specified only | Retained as the rule that every diagrammed edge needs an owning writer |
| Bare-add and two-call re-plan fixes rejected during review | [ProjectHephaestus issue #1857](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1857) | `unverified`: review finding, not implemented | Retained as atomic swap and add-one/remove-siblings guidance |
| Strict payload, GraphQL unavailable sentinel, REST fallback, exclusive predicates, and fresh readback | [immutable v1.4.0 source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/architecture-github-labels-as-state-vocabulary.md) | `unverified`: design-stage additions | Kept concise in main; not promoted to verified behavior |

## Implementation notes

- The vocabulary is intentionally closed: `state:needs-plan`, `state:plan-no-go`, and
  `state:plan-go`.
- The durable invariant is an exclusive state after a successful strict read, not merely a
  successful mutation request.
- The self-healing comment scan is a migration path for legacy issues. It must not become the
  recurring source of truth.
- A batch cache needs three states: known labels, known empty labels, and unavailable. Collapsing
  the latter two changes authorization behavior.
- Transition ownership applies to ambient and standalone implementations as well as the primary
  state-machine path; raw `state:*` mutations outside the shared accessor are drift candidates.

## Detailed verification matrix

| Input or event | Required result |
| --- | --- |
| Exactly one known state label | Return that state |
| No labels from a successful read | Invalid for normal authorization; optional bounded backfill |
| Two known states | Invalid and fail closed |
| Unknown `state:*` sibling | Invalid and fail closed |
| Malformed sibling object | Entire payload invalid |
| GraphQL item absent or malformed | `None`; attempt strict per-item REST fallback |
| REST fallback unavailable | Remain unavailable; do not authorize |
| Mutation returns success but readback differs | Fail closed and retry idempotently |

## Evidence boundary

Only the initial PR #707 implementation carries local execution evidence. Issue #1857 material is
valuable architecture guidance but remains unverified until a linked implementation and CI run
exercise those refinements.
