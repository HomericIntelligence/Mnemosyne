# Notes — shell-negation-exit-status-capture

Supporting evidence for the skill. The skill holds the rules; this file holds the observations
behind the v1.1.0 amendment.

## Why v1.1.0 was added

The original entry (v1.0.0) covered a test-harness counter bug: `if ! command; then rc=$?` stores the
negation's status, so failures counted as passes. The same underlying rule — *the exit status is the
signal, everything else is commentary* — was found to fail in a second shape that the original text
did not reach: a **retry wrapper that classified an attempt by matching the command's output text**.

That shape is more damaging than the counter bug because the wrapped command mutates remote state.

## Observation 1 — false-negative match duplicates a write

A retry wrapper posted a comment to a tracked item, then decided whether the attempt had succeeded by
testing the captured output for a key name. The command printed the comment's identifier as the
payload of a field selection, not as the key name being tested, so the match never fired.

Consequence: the wrapper treated a successful post as a failure and re-ran it. The target ended with
**two** comments carrying identical text.

Recovery that worked:

1. Stop the loop; do not run a third attempt.
2. List the target's comments through a read-only call.
3. Identify the duplicate by content and creation order.
4. Delete the later duplicate through the normal delete path.
5. Re-read the comment list to confirm exactly one remains.

The lesson generalizes because the marker/value mismatch is not unusual: any wrapper that greps for a
*field name* while the command prints a *field value* will fail the same way.

## Observation 2 — false-positive match reports a rejected write as success

The same session used a wrapper that classified a ref update with a pattern including an arrow token,
on the reasoning that a successful ref update prints `from -> to`.

A **rejected** update prints an arrow too, in its rejection line. The pattern matched, so the wrapper
reported success for an update the remote had refused.

Two things were wrong at once:

- The write did not happen, and the caller reported it as done.
- The loop exited instead of investigating the rejection, so the real cause stayed hidden until the
  next step queried the remote and found the ref unmoved.

The lesson generalizes because success and failure messages in the same tool commonly share tokens.
Matching on shared punctuation is the weakest form of output matching.

## Observation 3 — the ref guard that would have caught it

The push in Observation 2 was issued with a lease pinned to the expected current value. The remote had
moved, so the push was refused. The refusal was safe, but it was only noticed *after* the wrapper had
already reported success.

Reconciling first turned the ambiguous result into a definite one: fetch, compare the current ref to
the expected value, and only then push. Combined with exit-status capture, the outcome became
unambiguous without relying on message text.

## Counter-examples to keep in mind

- A wrapper that greps for a token the tool prints **only** on success is not the same defect. It is
  still output matching, but it fails toward a false negative (extra retry) rather than a false
  positive (silent no-op), and the recovery is the same read-back.
- A wrapper around an **idempotent** command can tolerate a duplicate run. The severity here came from
  a non-idempotent target where a second run is not equivalent to the first.

## Verification performed

Both defects were reproduced in one session and corrected in place. After replacing output matching
with exit-status capture and adding a read-back before retry, the wrapper's retry loop terminated on
the first success and reported rejections as rejections.

## Related guidance

`reconcile-before-retry-mutation-status-loss` addresses the case where the terminal status was never
observed at all — truncated output, or a delegated command whose contract forbids inspecting output.
This amendment covers the case where the status *was* available and the wrapper discarded it. The two
are complementary: one prevents creating the ambiguity, the other resolves it when it already exists.
