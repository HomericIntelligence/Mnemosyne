# Session Batch Status Flag Lies — Notes

Supporting evidence for the main entry. Not part of normal retrieval.

## Observed failure signature

On a host that ran a large agent session fleet, the session status record kept a busy marker
after the turn had finished. The marker was set again at a later time than the recorded idle
point, so a naive "is busy" test answered true for a session that had stopped minutes earlier.

Measured gaps between the busy marker and the last idle point, on sessions that had no
messages for that whole period:

| Session sample | Busy minus idle |
| --- | --- |
| 1 | ≈7 hours |
| 2 | ≈9.5 hours |
| 3 | ≈3 days |
| 4 | ≈28 days |

A gap of days cannot be a running turn. It shows that the marker is written by more than one
code path and is not cleared on all of them.

## Effect on the batch loop

The loop sent a prompt to each session in a group of 20 and then waited for every session to
report not busy. One session with a stale marker held the group for the full wait window. The
other 19 replies were already written. The loop then reported a timeout for the whole group,
so finished work looked unfinished.

## The two completion signals that did work

- The recorded turn outcome, with its timestamp.
- The newest message timestamp for the session.

A session is finished when the recorded outcome is newer than the moment the prompt was sent.
A session is live when the newest message time keeps moving. A session is stalled when the
marker is still set and the newest message time has not moved for the threshold.

## Reply binding

Reading the newest assistant message in a session is unsafe for a fan-out loop. Observed
cases:

- A sub-agent wrote a short turn after the main reply, so the newest message was not the reply
  to the prompt.
- A different model wrote a later turn, so a check that filtered on the prompt's model found
  nothing and rejected a turn that had in fact finished.
- A tool call and a completion record arrived after the reply.

Read forward from your own prompt and take the first assistant message that carries text and
the expected model.

## Reply content still has to be checked

A finished turn is not a successful result. In the same run, finished turns held:

- a refusal, because the session agent was read-only and could not perform the task;
- an answer in an unrelated result schema, because the session carried its own structured
  output contract;
- a question back to the operator;
- a provider routing error, written as a finished turn with an error outcome.

Each of these was a finished turn and none was a success. The loop had to check for the
expected result text before it recorded the session as complete.

## Read-only agent sessions

A session started under a read-only agent can finish a turn and still do no work. In one run
every such session answered in its review schema and created nothing. Switching the session
agent before sending the prompt removed this failure mode for sessions that allow it.