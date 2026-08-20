---
name: error-message-consistency-optional-dependency-pola
description: "Resolve POLA findings involving misleading optional-dependency errors or silent invalid-input fallback. Use to choose raise versus document, reconcile exception-type callers, prove absence tests are non-vacuous, or centralize repeated lazy capability resolution."
category: architecture
date: 2026-08-05
version: "4.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
history: error-message-consistency-optional-dependency-pola.history
tags:
  - pola
  - error-message
  - optional-dependency
  - exception-consistency
  - fallback
  - lazy-import
  - capability-resolver
  - testing
---

# Error Consistency and Optional-Dependency POLA

## Overview

First classify the contract defect. A supported format whose optional parser is missing should raise
an actionable capability error; an unsupported format is a value error; an intentionally documented
fallback may remain non-raising. Reuse sibling contracts, audit every caller before changing an
exception type, and centralize repeated capability policy behind a lazy resolver.

The misleading-error and documented-fallback repairs are verified locally. The shared resolver
design is plan-only and remains unverified. Case evidence is indexed in
[error-message-consistency-optional-dependency-pola.notes.md](error-message-consistency-optional-dependency-pola.notes.md),
with the complete prior version in
[error-message-consistency-optional-dependency-pola.history](error-message-consistency-optional-dependency-pola.history).

## When to Use

- A catch-all branch reports “unsupported format” when the real failure is a missing dependency.
- Sibling public functions expose the same capability with inconsistent exception messages/types.
- An audit says invalid input is silently ignored and offers “raise or document” as remedies.
- Existing sibling documentation and tests already establish a fallback contract.
- Changing `ValueError` to `RuntimeError` may bypass type-specific caller handlers.
- Missing-dependency tests monkeypatch a flag that production code may not read at call time.
- Multiple YAML entry points duplicate availability flags, eager imports, or raw `ImportError`.
- Failure after opening a destination can leave an empty or partial file.

## Verified Workflow

### 1. Separate input classification from capability availability

Detect the requested format first. Check the optional dependency only inside its supported branch:

```python
if format_name in {"yaml", "yml"}:
    if not YAML_AVAILABLE:
        raise RuntimeError(
            "YAML support requires the optional dependency; install the YAML extra"
        )
    return yaml.safe_load(text)
if format_name == "json":
    return json.loads(text)
raise ValueError(f"Unsupported config format: {format_name}")
```

Reuse an existing sibling's actionable message verbatim when it represents the same failure. Avoid
a new enum or custom exception when one branch correction aligns the public API.

### 2. Audit callers before changing exception type

```bash
rg -n 'load_config\(' src tests
rg -n 'except .*ValueError|except .*RuntimeError|except .*FileNotFoundError' src tests
```

Trace wrappers and command boundaries, not only direct calls. If several exception arms perform the
same contextual wrapping, add the new type and collapse them:

```python
except (FileNotFoundError, ValueError, RuntimeError) as exc:
    raise ConfigurationError(f"could not load {path}") from exc
```

Preserve exception chaining and the caller's stable public message.

### 3. Decide raise versus document from evidence

Before converting a fallback to an error:

1. Search all callers and determine whether inputs are literals or runtime values.
2. Search tests for the invalid value and its asserted output.
3. Compare sibling docstrings and public documentation.
4. Identify unnamed secondary fallthroughs, such as table rendering on an incompatible value.

An existing passing test that explicitly asserts fallback is strong contract evidence. If callers
use only valid literals and a sibling already documents the fallback, prefer documentation parity
plus regression coverage over a breaking exception change.

### 4. Make absence tests non-vacuous

Verify production reads the patched capability at call time. Exercise both `.yaml` and `.yml`, and
prove unsupported formats remain `ValueError`:

```python
def test_yaml_missing_dependency(monkeypatch):
    monkeypatch.setattr(config_module, "YAML_AVAILABLE", False)
    with pytest.raises(RuntimeError, match="install the YAML extra"):
        config_module.load_config("settings.yaml")


def test_unknown_format_is_value_error():
    with pytest.raises(ValueError, match="Unsupported config format"):
        config_module.load_config("settings.unknown")
```

A test that patches an unused flag can pass without reaching the intended branch. Add a mutation
check during development: restoring the collapsed branch should make the regression fail.

### 5. Centralize repeated capability policy lazily

When several entry points duplicate import and error behavior, one resolver owns the contract:

```python
def import_yaml():
    try:
        return importlib.import_module("yaml")
    except ImportError as exc:
        raise RuntimeError(
            "YAML support requires the optional dependency; install the YAML extra"
        ) from exc
```

Consumers resolve capability before opening a save target. Do not retain parallel flags or direct
imports once the resolver owns the policy.

Deterministic absence tests must account for `sys.modules`: mask or remove the module and patch the
import boundary so a dependency already loaded by another test cannot make the test vacuous.

### 6. Verify no partial side effects

For write paths, fail before creating/truncating files. Test that the target remains absent when the
capability resolver fails. Then run focused callers, the optional-dependency matrix, lint, type
checks, and the full affected suite.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Collapse unsupported format and missing dependency | Message reports the wrong cause | Classify format before checking capability |
| 2 | Change exception type without auditing callers | Existing `except ValueError` stops handling it | Reconcile every direct and wrapped caller |
| 3 | Always raise on invalid input | Breaks a documented and tested fallback | Let existing public evidence decide raise versus document |
| 4 | Add a custom enum/exception for one branch | Expands API without resolving inconsistency | Reuse the sibling contract |
| 5 | Patch an availability flag without tracing reads | Test may never affect production behavior | Patch the call-time lookup and mutation-check the test |
| 6 | Test only `.yaml` | Alias branch can keep wrong behavior | Cover both supported suffixes and unknown formats |
| 7 | Duplicate lazy import logic in each consumer | Messages, timing, and flags drift | Centralize one capability resolver |
| 8 | Resolve dependency after opening output | Failure leaves an empty file | Resolve before side effects |

## Results & Parameters

- Missing supported capability: actionable `RuntimeError` with installation guidance.
- Unsupported input value: `ValueError` unless a deliberate fallback contract exists.
- Reused caller handler: tuple of exception types only when bodies are identical.
- Absence test: patches the actual call-time import/flag path and proves the regression fails without
  the fix.
- Write path: capability resolution precedes destination creation.
- Local source evidence: 140 tests for issue #1510/PR #1608 and 77 tests for issue #1509 fallback
  documentation; CI was pending at capture.

## Evidence Boundary

Issue #1510's exception repair and issue #1509's fallback documentation are `verified-local`, not
CI-verified. The shared `import_yaml()` resolver and Python-floor cleanup are unimplemented planning
guidance. Keep those statuses distinct when applying this skill.
