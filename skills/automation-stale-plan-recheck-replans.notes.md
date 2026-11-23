# Notes: Stale-Plan Recheck Re-Plans

Supporting evidence for
[automation-stale-plan-recheck-replans.md](automation-stale-plan-recheck-replans.md).

## Observed failure, one wave

An issue-queue automation loop owned 57 `plan-go` items. 43 of them reached the
implementation stage, found the accepted plan older than the 7-day threshold, and routed to a
one-shot plan review recheck. When the recheck returned NOGO against the current tree, the
item wrote a block comment and finished with a human-intervention block:

```text
stale-plan recheck failed: the accepted plan no longer applies to the current tree.
Human intervention is required.
```

No later stage re-planned those items. The wave opened zero pull requests for them, and every
item stayed `plan-go` with an unusable plan.

The implementation-stage log that arms the recheck reads:

```text
accepted plan is N days old (stale after 7); routing to plan_review for one stale-plan
recheck — the plan stays valid and is never redone
```

The wording shows the design intent: a GO keeps the plan. The NOGO handling contradicted that
intent by making drift terminal.

## Change that was verified

- The plan review stage now pops the one-shot flag on NOGO, logs the re-plan decision, and
  falls through to the ordinary NOGO path: write the plan-no-go label, publish the durable
  NOGO record, and continue with the amendment state while the review budget remains.
- The block marker constant and its renderer were removed with the routing change.
- A new stage test asserts `Continue(next_state="AMEND_WAIT")`, labels `{plan-no-go}`, the
  popped flag, and no block comment.

## Validation evidence

- Focused pytest on the plan review stage module and the recovery parser module: 182 passed.
- `ruff check` and `ruff format --check` clean on the changed files.
- `mypy` clean on the changed source modules.
- Required CI on the change PR: 26 passed, 5 skipped, 0 failed, including lint and PR policy.

## Live confirmation

A later rerun of four items armed the recheck on its first item, received a reviewer NOGO, and
logged:

```text
stale-plan recheck failed (NOGO); re-planning the accepted plan against the current tree
```

The item then entered the amendment and decomposition flow. It later failed decomposition
validation three times, which is a plan-content problem and is not covered by this rule.

## Limits

- The routing rule was verified on one queue implementation. The state names and budgets come
  from that implementation.
- The success case after amendment is not yet observed end to end: the sample item's amended
  plan failed validation, so the run ended at plan-no-go rather than at a merged change.