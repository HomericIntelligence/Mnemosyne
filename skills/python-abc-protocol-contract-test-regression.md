---
name: python-abc-protocol-contract-test-regression
description: "Implementation-phase learnings when adding ABC/abstractmethod and runtime_checkable Protocol to an existing Python class hierarchy. Use when: (1) adding @abstractmethod to an existing base class that has contract tests with no-method subclasses, (2) designing a Protocol+ABC complementary enforcement strategy for a mixed-inheritance class family, (3) writing test functions in a project with ruff D103 enforcement."
category: architecture
date: 2026-06-13
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: ["abc", "abstractmethod", "protocol", "runtime_checkable", "contract-test", "pytest", "ruff", "d103", "ocp", "dip"]
---

# Python ABC + Protocol: Contract Test Regression and Enforcement Patterns

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Capture implementation-phase regressions and patterns when introducing `abc.ABC` + `typing.Protocol` to ProjectHephaestus automation reviewers (issue #1193) |
| **Outcome** | All 10 contract tests pass; pre-commit + mypy clean; CI green |
| **Verification** | verified-ci |

## When to Use

- Before committing after adding `@abstractmethod` to any base class that has existing contract tests
- When designing how `@runtime_checkable Protocol` and `ABC(abstractmethod)` should cover a class family where only a subset inherits a common base
- When writing test functions in ProjectHephaestus (or any project with ruff D103 enforced on test files)
- After converting a concrete base class to ABC, as a pre-commit checklist

## Verified Workflow

### Quick Reference

```bash
# 1. After adding @abstractmethod, grep test files for no-method subclasses
grep -n "class Bogus\|class Stub\|class Fake\|class Dummy" tests/unit/automation/test_*_contract.py

# 2. For each stub subclass found, verify it implements the new abstract method
grep -A10 "class BogusSubclass\|class StubReviewer" tests/unit/automation/test_*_contract.py

# 3. Run only the affected contract test to catch the regression before full suite
pixi run pytest tests/unit/automation/test_reviewer_base_contract.py -q --no-cov

# 4. After adding test functions, check D103 compliance
pixi run ruff check tests/unit/automation/test_interfaces.py --select D103

# 5. Full verification
pixi run pytest tests/unit/automation/ -v --no-cov
pixi run mypy hephaestus/automation/_interfaces.py hephaestus/automation/_reviewer_base.py
pre-commit run --files tests/unit/automation/test_interfaces.py
```

### Detailed Steps

1. **Before committing, grep contract test files for stub/bogus subclasses.**

   Any class in a test file that inherits the ABC base class WITHOUT implementing the new abstract method will raise `TypeError` at instantiation — BEFORE `__init__` runs. This silently swallows the error the test intended to verify.

2. **Add a minimal stub implementation to each no-method subclass.**

   ```python
   # BEFORE — broken after BaseReviewer gains @abstractmethod run()
   class BogusSubclass(BaseReviewer):
       pass

   # AFTER — instantiation proceeds to __init__ where the real TypeError fires
   class BogusSubclass(BaseReviewer):
       def run(self) -> None:
           pass
   ```

3. **Use `@runtime_checkable Protocol` for structural coverage, `@abstractmethod` for inheritance enforcement.**

   When a class family has 4 members but only 2 inherit a common base:
   - `@abstractmethod run()` on `BaseReviewer(ABC)` statically enforces the contract on the 2 inheritors (`PRReviewer`, `AddressReviewer`); mypy catches subclasses that forget `run()`.
   - `@runtime_checkable class ReviewerProtocol(Protocol)` covers ALL 4 reviewers structurally (including `AuditReviewer` and `PlanReviewer` that don't inherit `BaseReviewer`), enabling `isinstance`/`issubclass` conformance tests.

4. **Place Protocol in a private `_interfaces.py` module — do NOT add to lazy `__init__` exports.**

   In `hephaestus/automation/__init__.py` the lazy-load design uses `__getattr__`-based dispatch. Adding eager imports for new protocol types defeats this pattern. Keep `ReviewerProtocol` importable only via `from hephaestus.automation._interfaces import ReviewerProtocol`.

5. **Add a one-line docstring to EVERY test function.**

   ProjectHephaestus enforces ruff D103 (missing docstring in public function) on test files. A test function without a docstring fails pre-commit even if all tests pass.

   ```python
   # WRONG — fails D103
   def test_protocol_satisfied_by_stub():
       assert issubclass(StubReviewer, ReviewerProtocol)

   # CORRECT
   def test_protocol_satisfied_by_stub():
       """All concrete reviewer classes satisfy the ReviewerProtocol interface."""
       assert issubclass(StubReviewer, ReviewerProtocol)
   ```

6. **Verify with the full test file before pushing, not just a subset.**

   The regression was caught late because the initial verification ran a background task whose output wasn't checked before committing. Always run the full test file synchronously and confirm the exit code before moving on.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Background verification before commit | Ran `pytest tests/unit/automation/ -v` as a background task, then committed without checking output | Contract test regression (BogusSubclass missing `run()` stub) was already present in the commit | Never background the verification step before a commit; run synchronously and read the output |
| Test functions without docstrings | Wrote test functions in `test_interfaces.py` without docstrings — tests passed | ruff D103 caught missing docstrings in pre-commit, failing the hook post-commit | Every test function in ProjectHephaestus needs at least a one-line docstring; check with `ruff check --select D103` before committing |
| Assuming ABC enforcement covers all 4 reviewers | Initially planned to rely only on `@abstractmethod` on `BaseReviewer` | `AuditReviewer` and `PlanReviewer` don't inherit `BaseReviewer` — ABC can't enforce `run()` on them | Use a `@runtime_checkable Protocol` for structural coverage of the full class family; use ABC only for the inheritors |

## Results & Parameters

### Pattern: ABC + Protocol Complementary Enforcement

```python
# hephaestus/automation/_interfaces.py
from typing import Any, Protocol, runtime_checkable

@runtime_checkable
class ReviewerProtocol(Protocol):
    """Structural protocol covering all four reviewer classes."""
    def run(self) -> Any:
        ...


# hephaestus/automation/_reviewer_base.py
from abc import ABC, abstractmethod

class BaseReviewer(ABC):
    """Base class for reviewers that inherit this ABC."""

    @abstractmethod
    def run(self) -> Any:
        """Execute the review pipeline."""


# tests/unit/automation/test_reviewer_base_contract.py
class BogusSubclass(BaseReviewer):
    """Minimal stub to allow instantiation past ABC check."""
    def run(self) -> None:  # stub required — ABC blocks instantiation otherwise
        pass
```

### Contract test structure for Protocol conformance

```python
# tests/unit/automation/test_interfaces.py
import pytest
from hephaestus.automation._interfaces import ReviewerProtocol
from hephaestus.automation.pr_reviewer import PRReviewer
from hephaestus.automation.address_review import AddressReviewer
from hephaestus.automation.audit_reviewer import AuditReviewer
from hephaestus.automation.plan_reviewer import PlanReviewer


def test_pr_reviewer_satisfies_protocol():
    """PRReviewer conforms to ReviewerProtocol structurally."""
    assert issubclass(PRReviewer, ReviewerProtocol)


def test_audit_reviewer_satisfies_protocol():
    """AuditReviewer conforms to ReviewerProtocol despite not inheriting BaseReviewer."""
    assert issubclass(AuditReviewer, ReviewerProtocol)
```

### Verification command sequence (run synchronously, in order)

```bash
pixi run pytest tests/unit/automation/test_reviewer_base_contract.py -q --no-cov
pixi run pytest tests/unit/automation/test_interfaces.py -q --no-cov
pixi run mypy hephaestus/automation/_interfaces.py hephaestus/automation/_reviewer_base.py
pre-commit run --files hephaestus/automation/_interfaces.py tests/unit/automation/test_interfaces.py
```

### Expected Output

- `10 passed` on `test_reviewer_base_contract.py`
- `6 passed` on `test_interfaces.py`
- mypy: `Success: no issues found`
- pre-commit: all hooks pass (including ruff D103 on test files)

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #1193 — OCP/DIP ABC/Protocol implementation | PR merged; all 10 contract tests pass; CI green |

## References

- [architecture-ocp-dip-abc-protocol-planning-risks.md](architecture-ocp-dip-abc-protocol-planning-risks.md) — Pre-implementation planning risks
- [architecture-ocp-dip-verify-before-planning.md](architecture-ocp-dip-verify-before-planning.md) — Verification checklist before planning
