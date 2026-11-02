---
name: handler-subclass-classification-order
license: BSD-3-Clause
description: "Split one broad except handler into cause-specific branches without breaking a pinned behavior. Use when a CLI or boundary handler catches a base error class and must name each refusing cause separately, when a subclass carries a distinct accepted-but-unanswered outcome, when an existing test pins the base-class message, or when a validation error is caught inside a request loop."
category: architecture
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - exception-handling
  - handler-ordering
  - subclass-first
  - isinstance-order
  - cause-specific-error
  - pola
  - pinned-test
  - cli-exit-code
  - validation-before-request
  - verified-local
---

# Broad Handler Split: Classify Subclasses First

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Make one generic boundary handler report a distinct, correct message for each refusing cause without a regression in an already pinned branch. |
| **Outcome** | Operational. A planning review rejected a first revision because the proposed branch order reported a request that reached the service as a transport failure, and because an existing pinned test would go red. |
| **Verification** | verified-local. The ordering rule and the pinned-test check were confirmed by reading the source and the test at one commit. No implementation run is part of this lesson. |

The central rule: one `except Base` handler can dispatch on `isinstance`, but the branch order must
follow the class hierarchy from the most specific class to the most general. A subclass check after
its base check is dead code that silently changes the meaning of an outcome.

## When to Use

- A boundary handler (`except (OSError, RuntimeError, ValueError)`, `except Exception`) prints one
  generic sentence, and each cause must now have its own sentence.
- A subclass gives a different outcome for the same request. A request that reached the service
  and got no reply is not a transport failure, even when both raise from the same base class.
- An existing test asserts both a diagnostic line and the exact generic tail.
- A typed validator raises inside the request loop, so local misuse takes the same path as a
  remote refusal.

## Verified Workflow

### Quick Reference

```python
# Order: most derived class first; the residual base branch last.
intent = parse_request(fields)                 # validated before the loop

try:
    result = client.execute(intent)
except (OSError, RuntimeError, ValueError) as error:
    typer.echo(describe_error(error), err=True)      # keep the existing diagnostic line
    if isinstance(error, RefusedError):              # derived from RuntimeError
        tail = "The service refused the request."
    elif isinstance(error, AcceptedNoReplyError):    # derived from TransportError
        tail = None                                  # keep its own diagnostic, no generic tail
    elif isinstance(error, TransportError):          # base of AcceptedNoReplyError
        tail = "The request did not reach the service."
    elif isinstance(error, PermissionError):
        tail = "The request was not authorized."
    else:
        tail = "The request did not complete. Check the selected inputs."
    if tail is not None:
        typer.echo(tail, err=True)
    raise typer.Exit(1) from None
```

### Suggested Approach

1. **Map the hierarchy before you write branches.** List each class, its base, and the outcome that
   the operator must see. Put every subclass above its base. Write a test for the subclass, not
   only for the base, because a base test passes with either order.
2. **Add a typed error only for the missing outcome.** A new subclass of an existing error keeps
   every existing `except` site working. Give it the fields that the generic message dropped, for
   example a machine-readable refusal code. Do not replace a sibling error that already carries the
   cause text.
3. **Keep the branch you did not change.** When one branch must stay byte-identical to a pinned
   message, leave the diagnostic line and its tail alone. Prove it with the existing test run,
   unmodified. Do not rewrite a passing test to match a new message when the old message is still
   correct for its cause. Add the test file to the verification set either way.
4. **Validate before the fallible call.** Parse the request once, before the retry loop, and turn a
   typed validation failure into the CLI usage error: a nonzero exit that differs from the runtime
   failure exit. Strip the validator library's message prefix (for example `Value error, `) so the
   operator sees the rule, not the library. Catch the validation error outside the handler that
   prints runtime diagnostics, or the local misuse gets a remote-failure message.
5. **Assert the classification, not the words.** For each cause, assert that the output contains
   the cause text, that it does not contain the generic tail, and that the caller marker ran or did
   not run (for example the fake client was never called).
6. **State the exposure delta before you surface new text.** List what is newly printed, name each
   redaction layer that applies, and name the trust boundary of the reader. Record that list in the
   change description.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Put the transport base-class branch before its "accepted, no reply" subclass | The message said the request did not reach the service for a request that arrived and produced no reply | Put the subclass branch first and assert that the transport tail is absent |
| Attempt 2 | Replace the generic tail for every cause, including the one that an existing test pins | A passing regression test would fail; the change looked complete but the tree went red | Keep the residual branch unchanged and run the pinned test in the verification set |
| Attempt 3 | Validate the request inside the `try` that prints runtime diagnostics | Local misuse printed the same sentence as a remote refusal | Validate before the loop and raise the usage error from the outer scope |
| Attempt 4 | Re-check only the handler and not the client layer | The plan named a cause that the client had already started to carry | Verify each layer separately and state only the remaining delta |

## Results & Parameters

### Configuration

Branch order, from the most specific class to the most general:

```text
1. refusal error            (subclass of the caught runtime base) -> refusal sentence with code
2. accepted, no reply       (subclass of the transport base)      -> own diagnostic, no tail
3. transport base           (subclass of the caught runtime base) -> transport sentence
4. permission error                                               -> authorization sentence
5. residual base                                            -> unchanged generic tail
```

Request validation runs once, before the retry loop, and raises the usage error.

### Expected Output

- Success: the bounded result on stdout, exit 0.
- Each failure: one diagnostic line with the exception type and the redacted message, then one
  cause-specific sentence on stderr, and a nonzero exit.
- Local misuse: the usage error and the rule, with no request sent to the service.
- No traceback for any of these paths.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Not applicable | Planning review of one boundary handler | No implementation run. See [notes](handler-subclass-classification-order.notes.md). |

## References

- [silent-boundary-observability-exception-classification.md](silent-boundary-observability-exception-classification.md)
- [exception-discriminator-enums-state-machine-pola.md](exception-discriminator-enums-state-machine-pola.md)
- [planning-follow-up-issue-line-number-drift.md](planning-follow-up-issue-line-number-drift.md)
