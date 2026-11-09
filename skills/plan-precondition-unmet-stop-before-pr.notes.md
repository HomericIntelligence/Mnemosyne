# Notes: plan-precondition-unmet-stop-before-pr

Supporting evidence for the steps in the main entry. This file is not retrieved as guidance.

## v1.1.0 — pass-rule re-derivation (step 6)

Source: one session that implemented an approved operational plan.

Pattern, with repository identifiers removed:

- The plan said "no code change". Its steps ran one protected administrative
  command that wrote a generated record set into a release draft, then built,
  validated, checked artifacts, and diffed the result.
- The plan's stop rule said the diff may show only the two generated record
  families plus four derived identity fields.
- The release draft did not exist yet. The command itself needed an
  authenticated service socket. The session account got an access denial on
  the parent directory.
- The published prior artifact was readable as a release asset. The generator
  was a plain function that took the prior artifact, a registered context
  document, a cluster profile document, and the current source tree.

What the re-derivation showed:

- Every record in the refreshed set changed its contract digest, as intended.
- Each record also gained three provenance fields that the prior artifact did
  not carry. The source change made those values available for the first time.
  The prior generation ran before that change and could not emit them.
- Every record outside the refreshed set was unchanged.
- Both derived identity fields were dropped for the build step, as the plan
  described.
- An independent call of the digest function agreed with the generator for
  every record.

Decision: the session did not widen the stop rule. It reported the measured
field list, noted that the launch renderer compares the added fields (so the
fields are likely wanted), and asked the owner to either accept them and
revise the rule, or name a different change. The session made no write.

Why a dry run of the generator is the right probe:

- It uses the same code the operator command calls. A hand-written expectation
  would repeat the plan's prediction instead of testing it.
- It needs no privilege beyond read access to the prior artifact and the
  source tree.
- It produces a table the owner can settle in one reply, which a bare "the
  plan is blocked" cannot.

Boundaries:

- Do not run the generator when it would write. Call it, or a pure inner
  function, that returns a value.
- Do not treat an undeclared field as an error to fix. Judge it with the
  consumer that reads it, then report.
- A generated draft that the pass rule compares against an unpublished
  artifact is not a substitute for the operator step. This step only checks
  the rule.