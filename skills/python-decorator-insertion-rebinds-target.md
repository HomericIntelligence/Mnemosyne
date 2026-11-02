---
name: python-decorator-insertion-rebinds-target
description: "Edit Python files that contain a decorator stacked above a function or class. Use when you insert, move, or delete a definition, so the decorator stays attached to its original target."
category: architecture
date: 2026-11-01
version: "1.0.0"
user-invocable: false
tags:
  - python
  - decorator
  - contextmanager
  - edit-anchor
  - silent-rebind
  - refactor
  - verification
---

# Python: a decorator binds to the next definition, not to a blank line

<!-- Use ASD-STE100 for prose. -->

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Add or move a Python definition without changing the binding of an adjacent decorator. |
| **Outcome** | Successful. |

## When to Use

- You insert a helper, class, or function near an existing decorated definition.
- You anchor an edit on a blank line, a `def` line, or a decorator line.
- You delete or move a definition that has a decorator above it.
- You review a diff that adds lines directly above `def` or `class`.

## Verified Workflow

### Quick Reference

A decorator applies to the **next definition**. Any comments and blank lines
between the decorator and the `def` line stay with the decorator. To insert a
new definition, put it on the **other side** of the decorator. Read the diff
before you trust the result.

```python
# Correct: the helper is above the decorator.
def helper(...):
    ...

@contextmanager
def original(...):
    ...

# Wrong: the helper silently takes the decorator. `original` loses it.
@contextmanager
def helper(...):      # helper is now a context manager
    ...

def original(...):    # original is no longer a context manager
    ...
```

### Suggested Approach

1. Choose an edit anchor that does not sit between a decorator and its target.
   Use the line above the decorator, or a line far from the definition.
2. After the edit, read the changed region. Confirm that every decorator is
   directly above the definition it belonged to before the edit.
3. Treat a decorated generator as the high-risk case. When a function that
   returns a context manager loses `@contextmanager`, or when a plain function
   gains `@contextmanager`, the call site does not fail. It receives an
   unentered context manager object instead of the result.
4. Follow the object. A deferred call returns a resource object. That object
   then fails later, far from the edit, with a type that does not name the
   cause. Examples are a serialization error for a context manager object in a
   payload, or a missing attribute on a yielded value.
5. Use each call site as evidence. When a `with` block stops suppressing or
   releasing, or when a value that should be a plain return becomes an object,
   suspect a lost or gained decorator before you suspect logic.
6. Run the type checker and the focused tests for the changed module. A clean
   type check does not prove correct binding, because the call is still
   well-typed. Confirm the behavior with a test that calls the function.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Anchor on the `def` line | Inserted a new helper directly above an existing decorated function | The new helper took the decorator. The original function lost it. | The anchor was between the decorator and its target. |
| Trust a clean type check | Ran the type checker after the edit | Both definitions stayed type-correct, so no diagnostic showed the change. | Check the binding in the diff, not only the types. |
| Trust a passing targeted test | Ran one test that exercised a path where the deferred body never ran | The call returned an object and did not raise at that point. | A no-op decorated function hides its own error. Call the function directly. |

## Results & Parameters

### Configuration

- The rule applies to all Python decorators, including `@contextmanager`,
  `@staticmethod`, `@property`, `@dataclass`, `@functools.cache`, and test
  markers.
- Comments and blank lines between the decorator and the target do not break
  the binding. A new definition does break it.

### Verification

- Read the complete changed hunk. Count the decorators and the definitions
  below them.
- Call each changed callable from a test that asserts its return value, not
  only its type.

### Source

- See [notes](./python-decorator-insertion-rebinds-target.notes.md) for the
  observed failure mode.