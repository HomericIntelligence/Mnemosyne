# Goal Defer Error Notification Fallback — Notes

Supporting evidence for the main entry. Not part of normal retrieval.

## Observed sequence (single live case, generalized)

An engine bring-up session ran under goal mode with a token budget. Its work depended on a
multi-hour cluster validation job, so it launched a self-contained background watcher shell
(wait for the scheduler job, then print the result and the log tail) and called the goal
deferral tool with the watcher's shell identifier.

1. The deferral call returned an error state. The session transcript shows the tool state as
   `error` with no registered binding.
2. Across the following turns the goal moved to a budget-limited state more than once. Each
   time, the session ended the turn with a summary that named the pending watcher, the
   delivered work so far (review fixes pushed, plan-of-record updated), and the next action
   for the resume turn.
3. The watcher stayed self-contained: it printed the job identifier, the wait loop, and the
   final result location to its own output.
4. The session later reached a successful terminal outcome, consistent with the native
   completion notification resuming it after the limited turns.

## Why one failed deferral is terminal

The deferral registers a binding between the goal and the shell identifier. An error state
means the binding did not register. Repeating the call in the same turn reproduces the same
error and consumes the turns that the limit state has not already consumed.

## Resume contract contents

The resume summary that worked carried four items: the shell identifier, the scheduler job
identifier, the pending condition (job finish plus probe result), and the next action (act
on PASS/FAIL from the watcher output). A resume turn with fresh context could reconstruct
the whole plan from that summary plus the watcher output.

## Boundary

This entry does not relax the deferral rule. When the deferral call works, register it.
The fallback covers the error and limit cases only. It also does not certify that a
lost notification never happens; if the shell is gone and no notification arrives, the goal
state query exposes the stale awaited-shell record for the release call.
