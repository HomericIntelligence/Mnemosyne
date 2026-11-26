# External Quota Budget Wait — Notes

Supporting evidence for
[external-quota-budget-wait](external-quota-budget-wait.md). The main entry holds the
rules. This file holds the measurements and the review history.

## Source evidence

A shared automation client used a cross-process token bucket to pace calls to a
public code host. Operators set the refill rate to 0.2 calls per second to stay below
the account quota.

Observed effects:

- Each acquire call waited about 5 seconds. The spacing was constant across 59
  samples.
- The throttle wrote the same scope and root debug line once per acquire call.
- The run log contained no rate-limit error, no HTTP 403 or 429 response, and no
  secondary-limit message.
- The host quota showed enough remaining budget for the work.

The fixed pace was a workaround for an unread budget. The repeated line was a second
defect in the same path.

## Budget facts

- The rate-limit endpoint does not consume account quota. A short-TTL probe is
  therefore cheap.
- The GraphQL budget and the REST budget are separate resource objects. A shared
  client that spends GraphQL points must watch the GraphQL object.
- The reported reset is an epoch value. The window is one hour.
- A `remaining` count and a `reset` epoch are meaningful only as a pair from one
  response. A mixed pair can describe two windows.

## Defects found in review and their fixes

| Defect | Effect | Fix |
| ------- | ------ | --- |
| Probe ignored the deadline and shutdown | A healthy probe returned after the operation deadline | Pass both values to the probe, cap its timeout, and re-check after it |
| Two caches for one budget | A stale `remaining` paired with a fresh `reset` | One `(remaining, reset, fetched_at)` tuple |
| No wait limit | A bad reset produced an 86,400,005-second sleep | Reject a reset beyond one window and use the bucket |
| No probe lock | Eight threads started eight probes on a cold cache | Single-flight under a lock with one atomic write |
| Past reset returned healthy | The caller skipped the wait and the bucket | Warn once, return unhealthy, and use the bucket |
| Invalidated cache on a bad reset | One probe and one warning per call | Keep the tuple until the TTL ends and cache the warning per value |
| Datetime format on a bad epoch | A millisecond epoch raised `ValueError`; a huge epoch raised `OSError` | Guard the format call and fall back to the raw value |

## Verification evidence

- Five independent review rounds. Each round used a fresh review context.
- The final round reported GO after it reproduced the wrong-unit cases with
  `1_700_000_000_000`, `10**18`, `2**63`, and `10**40`.
- Client package: 242 tests passed.
- Caller suites: 661 tests passed.
- Focused runs: 130, 190, 192, and 194 tests passed across the rounds.
- Ruff check, ruff format check, and mypy reported no issues on the changed files.
- One pre-existing test failure came from a live process that held the machine-wide
  state lock. A private runtime root for every test removed the failure.

## Residual risks

- The account budget is global. The reserve is per host. Two hosts can spend the
  same reserve at the same time.
- A healthy budget returns before the cross-process bucket. Parallel processes can
  spend the reserve together. The 30-second probe limits the overshoot.
- A host clock ahead of the provider can make a valid reset look past. The warning
  names the clock check, and the bucket keeps the call paced.
- The reset wait applies to the resource that the client watches. A caller that
  spends a different resource can still wait on a depleted watched resource.
- A cached wrong-unit reset can still reach a separate client-level wait path. That
  path needs its own plausibility check.