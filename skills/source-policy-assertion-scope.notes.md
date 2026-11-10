# Source Policy Assertion Scope — Evidence Notes

## Source case

- A source-text policy test rendered a shell launch template and sliced the
  body of the recorded-removal function.
- The assertion was `assert "|| return 1" not in removal`, where `removal`
  covered the whole function body.
- A correct change added an adoption branch for an unrecorded leftover. That
  branch kept its own failure path, so it used the forbidden form for a
  different purpose.
- The removal policy did not change: the removal invocation warned and
  continued.
- Two consecutive nightly shards selected the test and failed at the
  whole-function assertion. The pull-request gate did not select that module,
  so the stale pin reached the mainline.

## Repair

- The slice starts at the removal invocation and ends at the terminal
  bookkeeping line that completes the removal.
- The scoped slice asserts that the forbidden form is absent and that the
  warning marker is present.
- The sibling cleanup assertion (the cleanup handler must exit zero) stayed.
- The product did not change. The policy was correct; the test scope was
  stale.

## Verification

- The scoped test passed in the affected shards, and the nightly run completed
  green.
- A mutant with the forbidden form in the removal step failed the scoped
  assertion.
- A change to the adoption branch did not affect the scoped assertion.
- `ruff format --check` and `ruff check` passed on the changed test file.

## Commands

```text
uv run --locked --extra dev pytest -q <node> -p no:randomly --no-cov
uv run --locked --extra dev ruff format --check <file>
uv run --locked --extra dev ruff check <file>
```

## Limits

- The exact source form is the contract in this case. A behavior harness for
  the rendered shell fragment was not available at the time.
- The evidence comes from one rendered shell template. The decision rule
  generalizes to source-text policy pins in other artifacts.
- The module is selected only by the nightly tier, so a pull-request run can
  pass while the stale pin remains. The scope repair does not fix the tier
  selection gap.