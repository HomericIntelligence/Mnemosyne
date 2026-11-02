---
license: BSD-3-Clause
target_skill: python-decorator-insertion-rebinds-target
date: 2026-11-01
---

# Supporting evidence: decorator insertion rebinds the decorator target

## Context

A change added a module-level helper to a Python supervisor module. The edit
anchor was the `def` line of an existing `@contextmanager`-decorated function.
The new helper was placed between the decorator line and that `def` line.

## Observed failure mode

1. The new helper took `@contextmanager`. It returned a generator, so calls to
   it returned an unentered context manager object instead of a value.
2. The object went into a payload that used JSON serialization. The report was
   `Object of type _GeneratorContextManager is not JSON serializable`, which
   does not name the module helper or the edit.
3. The original function lost `@contextmanager`. Every `with` statement that
   used it failed, because the generator was never entered.
4. The type checker and the linter passed. Both definitions stayed
   well-typed.
5. One selected test passed, because the deferred body never executed. The
   KeyError that the helper was written to prevent did not occur, and that
   pass looked like proof that the change worked.

## Recovery

- Restore the decorator line directly above its original `def` line.
- Move the new helper above the decorator.
- Re-run the tests with the helper body executing. The previously hidden
  KeyError then appeared, and the real fix was required.

## Diagnostic sequence that identified the cause

1. Reproduce the failing test on the pristine base revision in a separate
   worktree. The base passed, so the change caused the failure.
2. Inspect only the changed hunks of the touched module. Look for lines
   between a decorator and a `def`. The misplaced insertion was visible in the
   diff.
3. Read the error type. A deferred object type in a payload or a `with` block
   points to a decorator binding error before it points to a logic error.

## Limits

- This case did not show a failure that a static checker can detect. The rule
  is a review and edit-anchor rule, not a tool configuration.