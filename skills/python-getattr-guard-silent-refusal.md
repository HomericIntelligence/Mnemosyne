---
name: python-getattr-guard-silent-refusal
description: "Diagnose a validation guard that refuses every input because its getattr accessor chain reads the wrong attribute path. Use when a guard built from getattr(obj, 'x', None) defaults rejects all callers, or when guard tests exercise only the refusal path and never the accept path."
category: debugging
date: 2026-11-12
version: "1.0.0"
user-invocable: false
tags: [python, getattr, accessor-chain, default-value, guard, silent-failure, attribute-path, accept-path, probe, non-vacuous-test]
---

# Getattr Guard Chains Refuse Everything When the Accessor Path Is Wrong

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-12 |
| **Objective** | Find and fix a validation guard that rejects every input because its accessor chain resolves through the wrong attribute path. |
| **Outcome** | Successful. The real accessor path was found by probing the object the runtime passes, the guard was corrected, and a dual-path test now pins both outcomes. |

## When to Use

Use this skill when one or more of these conditions hold:

- A validation or authorization guard refuses every input, including inputs that are known to be valid.
- A guard reads configuration or context through a chain of `getattr(obj, "x", None)` calls, and no test asserts what the guard accepts.
- A new guard passes the existing test suite, yet a service-side round-trip test fails with the guard's refusal message.
- A refusal message names a valid entity as missing or unconfigured, while the same command succeeds for the refusal case alone.
- Code review of a guard looks correct because the chain handles `None` at every step, and the failure is invisible until the accept path runs.

## Verified Workflow

### Quick Reference

Probe the real object the runtime passes before trusting an accessor chain:

```python
# Run inside the failing test's environment (pytest), not in isolation.
import sys

ctx = service.context  # the object the guard actually receives
print(
    "type:", type(ctx).__name__,
    "| attrs:", [a for a in dir(ctx) if "model" in a.lower()],
    "| spec.policy.models:", sorted(getattr(getattr(getattr(ctx, "spec", None), "policy", None), "models", {}) or {}),
    file=sys.stderr, flush=True,
)
```

Then pin both guard outcomes in one parametrized test:

```python
@pytest.mark.parametrize("operation", [...])
def test_the_guard_accepts_and_refuses(...):
    accepted = _call_with_configured_model()
    assert accepted.error_code is None
    refused = _call_with_undeclared_model()
    assert refused.error_code is not None
```

### Suggested Approach

1. Reproduce the refusal for a known-valid input. If a valid entity is refused, the guard's data lookup is wrong, not the refusal logic. A refusal for every input means the lookup returned `None` for the membership set itself.
2. Read the accessor chain and write down the attribute path it assumes, for example `obj.policy.models`. Do not trust the chain because each step defaults `None` safely. Defaults make the chain never raise, which also makes it never reveal the wrong path.
3. Print the real object the runtime passes, inside the failing test or the service path, and list its attributes and the value at the assumed path. A probe outside the runtime can construct a different object shape and mislead. When a fixture needs pytest, run the probe as a temporary test instead of a script.
4. Correct the accessor path. Verify both directions directly: the configured input is accepted, the undeclared input is refused with the entity named in the message.
5. Add a dual-path test: one case through the accept path, one through the refusal path, asserting both the error code and that no record changed. Run the suite with the guard removed to prove the refusal case is non-vacuous.
6. When the guard runs inside a service or other out-of-process component, state plainly that a live check against an older deployment confirms the defect, not the fix. Unit tests carry the fix evidence until the deployment cuts.

A probe step can be unavailable when the fixture needs a harness context. Continue by running the probe as a temporary test inside that harness, and remove the temporary test after the value is recorded.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Implement the guard with the accessor path `context.policy.models`, wrapped in `getattr(..., None)` defaults. | The context object has no `policy` attribute; the policy hangs off `spec`. Every `getattr` returned `None`, so the membership check refused every model. It compiled, imported, and looked correct. | A getattr chain that defaults every step hides a wrong attribute path instead of raising on it. Defaults trade a loud error for a silent global refusal. |
| Attempt 2 | Diagnose from the code alone, by reading the module and the fixture setup. | Two inference passes reached two different wrong conclusions, and diagnostic prints placed in the guard never appeared because the failure came from the earlier call in the same round trip. | Static reading cannot resolve which object shape reaches a guard at runtime. Probe the object inside the executing test. |
| Attempt 3 | Print diagnostic values from a standalone script that builds the context. | The context construction needed the test harness and failed outside pytest with a root-override guard. | Probe inside the harness that produces the real object. A temporary test is the reliable vehicle. |
| Attempt 4 | Trust the new guard because its own test suite passed. | The suite only exercised refusal-shaped paths for unregistered models; no case walked the accept path for a configured model. | A guard is not verified until a test asserts what it accepts and what it refuses. The accept path is where a wrong accessor shows. |

## Results & Parameters

### Configuration

Guard shape after the fix, with the corrected accessor path:

```python
def _require_served_model(context: object, model: str) -> None:
    spec = getattr(context, "spec", None)
    policy = getattr(spec, "policy", None)
    models = getattr(policy, "models", None)
    if models is not None and model in models:
        return
    raise RefusalError(
        f"pool {model} is not configured for this deployment; "
        "select one model that the deployment serves"
    )
```

Test shape that pins both outcomes:

```python
@pytest.mark.parametrize("operation", ["status", "rollback"])
def test_the_commands_refuse_a_model_the_policy_omits(tmp_path, operation):
    service, _ = _service(tmp_path)
    intent = _intent(operation, "not-a-served-model")
    response = _execute(service, intent)
    assert response.error_code is not None
    assert "not-a-served-model" in (response.error or "")
    assert "not configured" in (response.error or "")
    assert _store(service).load("not-a-served-model") is None
```

### Expected Output

- The probe prints the object type, its model-related attributes, and the sorted membership set at the corrected path, for example `spec.policy.models -> ['model-a']`.
- The guard accepts every configured model and refuses an undeclared model with a message that names the model and the condition.
- The dual-path test passes with the guard in place, and its refusal cases fail when the guard call is removed (non-vacuity).
- Existing configured-path round trips pass again after the accessor correction.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A Python service CLI | A configured-model guard on a deployment context object | The wrong accessor chain refused every model; the service-side round-trip test caught it. See [notes](../skills/python-getattr-guard-silent-refusal.notes.md). |

## References

- [getattr delegate-collapse mypy regressions](architecture-getattr-delegate-collapse-mypy-regressions.md): adjacent guidance for dynamic `__getattr__` forwarding and its static-typing costs.
- [Python documentation: getattr](https://docs.python.org/3/library/functions.html#getattr): the three-argument form that returns a default instead of raising.
