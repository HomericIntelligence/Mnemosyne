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

## Burn attribution on an exhausted shared budget

A second incident class used the same failure message with the hourly GraphQL budget actually at
zero. Two `gh api rate_limit` reads, five minutes apart, measured the spend directly: the REST call
costs nothing against the GraphQL budget. The quiet-window spend was about one seventh of the
hourly GraphQL cap, yet the budget still reached zero repeatedly.

The measured consumers were concurrent automation loops on one token, each with worker fan-out.
Three mechanisms dominated:

- each agent worker issued its own CLI reads, so total calls scaled with worker count;
- whenever the budget died, guarded jobs deferred and then resumed at the same reset second, which
  re-exhausted the new budget within minutes;
- the same label, metadata, and scan reads repeated on every poll cycle with no local reuse.

Mitigations that directly follow from the mechanisms: a TTL read-through cache or query batching
for repeated reads, worker caps and client request rates set before a lockout, staggered restarts
past a reset, and one token per job for budget isolation. For a lasting fix inside the shared
client layer, a cache with local TTL storage and mutation-aware invalidation was filed as an
upstream enhancement request.

## REST fallback while GraphQL is exhausted

The REST primary rate limit is a separate budget from the GraphQL budget. During a confirmed
GraphQL exhaustion window, the same account completed required writes through `gh api` REST paths:

- issue creation through `POST /repos/{owner}/{repo}/issues`;
- pull-request creation through `POST /repos/{owner}/{repo}/pulls`.

`gh issue create` and `gh pr create` use GraphQL only; there is no fallback inside the commands.
Conditional (ETag) requests exist for REST and return 304 without spending the primary budget, but
GraphQL has no equivalent mechanism, so TTL caching is the only local reduction for GraphQL reads.