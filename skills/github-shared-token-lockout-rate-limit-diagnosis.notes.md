# Notes: github-shared-token-lockout-rate-limit-diagnosis

## Observation

Several long-running automation jobs shared one GitHub user token on one host. Each job used its
own checkout directory, so the jobs did not share a checkout, but they did share the account.

Every job failed within minutes of its start. The failure text named a rate limit and gave no
usable reset value:

```text
GraphQL: API rate limit already exceeded for user <account-id>
```

A budget read taken at the same moment as a failing live call reported that most of the hourly
GraphQL quota was unused:

```text
graphql 4460/5000 remaining
```

A single manual call failed in the same way, at the same time, with the same result. The budget was
therefore not the constraint.

## Consequence inside the tool

The tool ran a dependency check before it started work on an item. Each check issued API calls.
When those calls failed, the tool could not confirm the dependency state. It marked the item as
failed and moved on. The effect was that the job made no progress, poisoned its items in seconds,
and exited. The log then showed a summary with no agent work completed.

Two error names looked the same in the log but had different causes:

- a failed dependency check, which appeared at item level; and
- a run-level start failure, which appeared with no items at all.

Both followed from the same account lockout.

## Recovery that worked

1. Stop the sibling jobs with a termination signal that lets each job record its state.
2. Wait for the account to stop receiving request pressure.
3. Confirm recovery with one live call.
4. Restart the target job with its own credential when possible.

The target job then made progress. The exact duration of the recovery was not measured.

## Limits of the evidence

- The observation used one user token. An organization or application token can report different
  fields and can carry its own secondary limits.
- The service did not name the limit class in the message. The classification in this skill rests on
  the contrast between the budget read and the live call, not on the message text.
- The duration of the lockout after the pressure stopped was not measured. A host that restarts the
  sibling jobs too early can return to the same state.