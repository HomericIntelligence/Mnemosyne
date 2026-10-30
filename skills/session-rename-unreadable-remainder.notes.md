# Notes: Session Rename With an Unreadable Remainder

Companion evidence for
[session-rename-unreadable-remainder](session-rename-unreadable-remainder.md).
Incident reconstruction and verification limits. Every rule the skill needs
for operation lives in the main file.

## Incident reconstruction (v1.0.0 source material)

One verified completion protocol on an internal agent harness. A standing
completion convention prescribes a session rename at the end of an assignment:
replace a leading in-progress status prefix with a done prefix and keep the
remainder of the title unchanged.

### Sequence

1. The completion steps ran in order. The learning and report steps
   completed. The rename step remained.
2. The available session tools offered a rename operation but no operation
   that returns the current title. The remainder was unreadable from tools.
3. A user-question call asked for the exact title. The runner cancelled the
   call because the run was non-interactive and returned the instruction:
   continue without an answer, make reasonable assumptions, and state them.
4. Local harness state stores could have contained the title, but the task's
   protected-path directive forbade reading them. The read was rejected.
5. The remainder was reconstructed from the assignment objective that drove
   the session. The rename executed and returned the new title.
6. The completion report stated the assumption explicitly and recorded the
   one-operation correction path: rename again from the true title, at no
   cost beyond the message.

### Observations that shaped the rules

- The cancellation callback of the question tool is itself a reliable
  interactivity signal. It arrived with an explicit continue-with-assumptions
  instruction from the runner.
- The rename operation echoes the applied title, so the result is verifiable
  after the fact even without a title-read operation.
- The correction path is cheap: a rename is idempotent and the title is the
  only affected artifact. That asymmetry justifies proceeding under a stated
  assumption rather than blocking a required completion step.
- The opposite asymmetry forbids fabrication without any durable source: an
  invented remainder permanently discards the true one from the tool-visible
  record.

### Verification limits

- Single-case evidence from one harness generation. The probe order is
  portable; the specific tool surface is not. Re-probe on each generation.
- The durable-source rule was exercised with one source class (the assignment
  objective). Protocol messages and prefix patterns are inferred-safe from
  the same property: they are part of the session record, not a guess.
