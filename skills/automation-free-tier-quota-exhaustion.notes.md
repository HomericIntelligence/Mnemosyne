# Automation Loop Free-Tier Quota Exhaustion — Notes

Supporting evidence for
[automation-free-tier-quota-exhaustion](automation-free-tier-quota-exhaustion.md).
The main file holds the rules. This file holds the observed run and its limits.

## Source evidence

A queue-owned automation run processed a backlog of about two dozen items on a
public code host. Three free-tier models from one hosted inference provider were
assigned to the planning, implementation, and review roles. The run lasted about
74 minutes and completed two discovery passes.

Observed signatures:

- The first `free usage limit reached` message appeared about 41 minutes into the
  run, on an implementation job.
- After that point, planning, implementation, and review jobs all reported the
  free-limit message.
- When the loop tried the provider-default fallback, the message changed to a
  quota or pre-paid-credits requirement.
- The structured log contained 25 free-limit messages and 16 fallback quota
  messages.
- Final dispositions: 3 pass, 14 fail, 7 blocked, and 1 pending, over 64 agent
  jobs.
- The summary had terminal dispositions and no traceback. The coordinator exited
  with status 1 because passing items were fewer than total items.

Separate defects also appeared in the same log: worktree creation failures,
poisoned durable plan records, and a plan rejected for stale source references.
These failures do not depend on quota and need separate repair.

## Decision record

The operator classified the run as quota-limited and chose to wait for the
provider reset before relaunch. The harness exposed no quota-status command, so
the reset time could not be measured locally. No relaunch was attempted while the
limit was active.

## Limits

- The evidence comes from one run on one host. Treat the timing figures as
  observations, not as predicted reset windows.
- The provider reset time was not verified. The main rule asks the operator for
  that value rather than guessing it.
- Local paths, host names, repository names, issue numbers, and run-specific
  identifiers are intentionally omitted from this record.
