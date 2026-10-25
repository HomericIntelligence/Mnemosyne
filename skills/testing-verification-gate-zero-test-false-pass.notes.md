# Notes: Verification Gate Zero-Test False Pass

Supporting evidence for
[`testing-verification-gate-zero-test-false-pass`](./testing-verification-gate-zero-test-false-pass.md).
Prior versions are in Git history.

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Plan-named selector with no matching tests (automation lane, 2026-10) | this amendment | verified-local; command output observed, substitution applied and disclosed | Added the plan-command triage branch, the wrong-selector-versus-nonexistent-check distinction, and the disclosure rule |

## Case Details

### Plan-named selector with no matching tests

An approved implementation plan named a verification command of the form
`pytest -k "word_a and word_b"`. The suite had about 15,000 tests; the run deselected all of them
and exited with code 5. A suite-wide search for each token found no test that carried either: the
plan referenced checks that did not exist rather than mis-selecting real ones. The invariant the
command guarded (no cited line numbers moved by the change) was then verified by diff inspection:
the only hunk replaced one line in place, so every earlier line kept its number. The delivery
record kept the original command, the exit 5 result, the token search result, and the substitute
evidence as a named gap instead of a pass.

Recovery order that worked: classify by token search first, name the invariant second, verify with
the smallest bounded alternative third, disclose fourth. Silent acceptance would have hidden the
plan defect; silent blocking would have stopped correct work whose invariant had direct evidence.
