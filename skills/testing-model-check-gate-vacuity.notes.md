# testing-model-check-gate-vacuity — supporting notes

Evidence for the main entry. The notes hold commands, measurements, and the
authoring failure that appeared while the gate was built. The main entry holds
the rule.

## Environment

- Model checker: TLC 2.19, pinned from the public release archive.
- Java: OpenJDK 11.
- Models: bounded state machines written by hand for this work. No refinement
  proof connects a model to the implementation.

## Guard matrix, as run

The runner was tested by replacing `subprocess.run` with a fake that returns a
chosen exit code and text.

| Case | Exit | Text | Required | Observed |
|------|------|------|----------|----------|
| Marker plus crash | 255 | marker and `Error: division by zero` | fail | fail |
| Marker plus error line | 0 | marker and `Error: boom` | fail | fail |
| Collapsed safe run | 0 | marker and 10 distinct states | fail | fail |
| Clean mutant | 0 | marker | fail | fail |
| Wrong invariant | 12 | `Invariant OtherThing is violated` | fail | fail |
| Expected violation | 12 | `Invariant Exclusive is violated` | pass | pass |

## Progress-line parse defect

The first parser searched the whole output for `(\d+) distinct states found`.
TLC prints two forms:

- progress: `Progress(9) at ...: 203,542 states generated (203,542 s/min), 40,598 distinct states found, ...`
- summary: `712237 states generated, 52562 distinct states found, 0 states left on queue.`

The progress counts use a thousands separator above 999. The summary counts do
not. When the first progress line held a value below 1000, the parser reported
that value. Two runs of the same model reported 46 and 838 distinct states
instead of 52562. The floor then failed the safe run, which is how the defect
appeared.

Fix: remove lines whose stripped form starts with `Progress(` before the
search. Violation and clean-marker detection still read the full output.

## Distinct-state floors

Floors were set at 57 percent of the observed count:

| Model | Observed distinct | Floor |
|-------|-------------------|-------|
| Port lease | 3084 | 2000 |
| Capacity credit | 3108 | 2000 |
| Batch commit | 52562 | 30000 |

A one-writer variant of the batch model reached 984 distinct states, and a
smaller generation bound reached 8735. The floor sits above both.

## Mutation cases that shaped the rule

- Removing the per-port exclusion guard from a lease model produced a
  counterexample in 109 distinct states, at depth 7.
- Repeating a terminal debit produced a violation of the negative-counter
  invariant in 34 distinct states, at depth 4.
- A charge-only mutation, which leaves the reservation set consistent, is the
  only case that exercises the charge identity. The wider mutation stopped at
  the negative-counter invariant first.
- A mutation that removes the atomic name claim of a commit protocol produced
  a duplicate publication in 396 distinct states, at depth 5.
- A mutation that proposes a status outside the transition table first used a
  name that the implementation cannot produce. That value also made the type
  invariant violable. Restricting the mutation to the declared status set still
  produced a violation, at depth 5.

## TLA+ authoring failure seen while building the gate

An action written with a leading disjunction in the conjunct chain:

```tla
Commit(w) ==
    /\ guardOne
    /\ A \/ B
    /\ published' = ...
```

parses as `(guardOne /\ A) \/ (B /\ published' = ...)`. TLC then reports:

```text
Error: Successor state is not completely specified by action Commit of the
next-state relation. The following variable is not assigned: conflict.
```

Parentheses around the disjunction alone were not enough. The reliable form is
an `IF` in the conjunct position:

```tla
    /\ (IF A THEN TRUE ELSE B)
```

and a flattened action with no nested `LET` around the assignments. The same
symptom also appears when an action reads a function outside its domain, for
example `published[loaded + 1]` when `loaded` can equal the bound. Keep the
index inside the bound before the read.

## Review finding that changed the rule

A review of the merged first version found that one mutant reported only the
first of three claimed invariants. The fix was one configuration per invariant
that the claim names. The rule in the main entry comes from that finding: a
broad expected set hides the properties that did not fire.

## Size and structure

- Main entry: concise rules and five failure rows.
- Notes: measurements and the authoring failure. Not part of retrieval.