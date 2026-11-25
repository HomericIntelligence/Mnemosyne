# Agent Session Broadcast Delivery Verification — Notes

## Evidence from the batch that produced this lesson

- Candidate set: 74 top-level sessions in a 24-hour window across three agent hosts. The orchestrator session was excluded, which left 73 targets.
- Admission results: 57 local-server prompt admissions, 5 queue-and-resume admissions, and 11 background resumes.
- Verified delivery: 65 targets had the prompt as the latest user message and a new turn. 8 targets were discarded by authentication expiry.
- One session was already working and continued its own turn; a probe confirmed the model worked before the configuration change.

## Authentication discard

The failed turns reported these conditions in sequence:

1. The selected model was not available to the host.
2. The login had reached its time limit.
3. The host was not logged in.
4. The host asked to resend the message after the fix.

The prompt stayed in the input line but was not accepted. A retry before re-authentication failed with the same message. The host's integration files and model environment disappeared during the batch, at the same time as the failures. The batch did not modify that configuration.

## Fork behavior

A resume of a session that the host still considered running started a copy with a new session identifier. The copy then processed the prompt. The original session stayed at its failed state. Record the mapping before you send a retry, or two workers can write the same files.

## Verification queries

- Confirm the latest user message for each target in the session store.
- Confirm that a turn started after that message.
- Classify each target as running, completed, authentication discard, or prompt absent.
- Do not use the send command exit status as delivery evidence.