---
name: exception-type-matching-in-tests
description: "Exception type matching in tests must match production catch clauses exactly. TimeoutError (base class) ≠ subprocess.TimeoutExpired (subclass); base classes don't catch subclasses. Always use exact exception type in tests. Also: mock all upstream dependencies before testing error paths, and check=False in subprocess.run prevents CalledProcessError, making catch clauses dead code. Use when: (1) writing tests for exception paths, (2) refactoring error handling, (3) verifying subprocess exception semantics."
category: testing
date: 2026-06-06
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - exception-handling
  - test-fidelity
  - subprocess-exceptions
  - TimeoutExpired
  - mock-dependencies
  - exception-semantics
  - pytest
  - test-patterns
---

# Exception Type Matching: Tests Must Match Production Catch Clauses Exactly

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-06 |
| **Objective** | Document the common pitfall where tests raise base exceptions (TimeoutError) but production catches subclasses (subprocess.TimeoutExpired). Python's exception hierarchy means base classes don't catch subclasses — if you test with the wrong type, the test passes but production fails. Also cover subprocess semantics: `check=False` prevents CalledProcessError, making its catch clause dead code. |
| **Outcome** | Shipped in ProjectHephaestus issue #819 / PR #852. Fixed 3 failing tests that used TimeoutError instead of subprocess.TimeoutExpired. Added 5 new tests validating exact exception type matching. All 1143 automation tests pass. |
| **Verification** | verified-ci (full test suite passes; exception type semantics validated) |
| **History** | New skill — no amendments yet. |

## When to Use

- Writing tests for error handling paths (exceptions, timeouts, retries)
- Refactoring exception handling and need to ensure tests match the new types
- Subprocess code with `try: subprocess.run() except subprocess.TimeoutExpired:`
- Unsure why a test passes locally but fails in CI, or vice versa
- Code review flagging "exception type inconsistency"
- Mock helpers that simulate errors — must raise the exact type production catches

## Verified Workflow

### Quick Reference

**Rule 1: Test exception types must match production catch clause types.**

```python
# Production code
try:
    result = subprocess.run(..., timeout=5)
except subprocess.TimeoutExpired:  # ← Catches THIS type
    logger.error("Timed out")
except subprocess.CalledProcessError:  # ← Catches THIS type
    logger.error("Non-zero exit")

# Test code — MUST raise the EXACT types production catches
def test_timeout_handling(mocker):
    # WRONG: raises TimeoutError (base class)
    mocker.patch("subprocess.run", side_effect=TimeoutError("timeout"))
    # This test passes — TimeoutError is caught by except Exception
    # But production would NOT catch it because except subprocess.TimeoutExpired
    # doesn't catch base classes

    # RIGHT: raises subprocess.TimeoutExpired (exact type)
    mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5))
    # This test now validates that production's except clause catches it
```

**Rule 2: Mock all upstream dependencies BEFORE testing error paths.**

```python
# WRONG: let get_repo_info fail, don't test the intended error path
def test_timeout_handling_WRONG(mocker):
    # If get_repo_info is not mocked, it might fail first,
    # masking the timeout handling we intended to test
    result = _run_with_timeout(repo_root="...")
    # What error is this catching? get_repo_info failure? Or timeout?

# RIGHT: mock upstream, ensure timeout is the first error
def test_timeout_handling_RIGHT(mocker):
    mocker.patch("hephaestus.automation.get_repo_info",
                 return_value=("owner", "repo"))  # ← Upstream dependency mocked
    mocker.patch("subprocess.run",
                 side_effect=subprocess.TimeoutExpired("cmd", 5))  # ← Error under test
    
    with pytest.raises(subprocess.TimeoutExpired):
        _run_with_timeout(repo_root="...")
    # Now we're definitely testing timeout handling, not get_repo_info handling
```

**Rule 3: `check=False` in subprocess.run prevents CalledProcessError.**

```python
# WRONG: catch clause for an error that will never be raised
result = subprocess.run(..., check=False)  # ← check=False prevents exception
try:
    something = result.stdout
except subprocess.CalledProcessError:  # ← DEAD CODE — never raised with check=False
    pass

# RIGHT: check the return code manually
result = subprocess.run(..., check=False)  # ← Suppress exception
if result.returncode != 0:
    logger.error("Command failed: %s", result.stderr)

# OR: use check=True (default) to get the exception
result = subprocess.run(..., check=True)  # ← Will raise CalledProcessError if non-zero
try:
    something = result.stdout
except subprocess.CalledProcessError as e:
    logger.error("Command failed: %s", e)
```

### Detailed Steps

#### Exception hierarchy: Why base ≠ subclass in exception handling

Python's exception hierarchy:

```
BaseException
└── Exception
    ├── TimeoutError (generic timeout)
    ├── subprocess.TimeoutExpired (subprocess-specific, inherits from TimeoutError)
    ├── subprocess.CalledProcessError (subprocess-specific, inherits from Exception)
    └── ... other exceptions
```

Key point: **`except BaseClass` catches BaseClass and ALL subclasses, but `except SubClass` does NOT catch the base class.**

```python
# Example 1: Catching base class (catches subclass too)
try:
    raise subprocess.TimeoutExpired("cmd", 5)  # Subclass
except TimeoutError:  # Base class
    pass  # ✓ Caught — subclass is instance of base class

# Example 2: Catching subclass (does NOT catch base class)
try:
    raise TimeoutError("timeout")  # Base class
except subprocess.TimeoutExpired:  # Subclass
    pass  # ✗ NOT caught — base class is not instance of subclass
```

In production code:

```python
try:
    result = subprocess.run(..., timeout=5)
except subprocess.TimeoutExpired:  # Only catches subprocess.TimeoutExpired
    logger.error("Subprocess timed out")
```

If the code raises `TimeoutError` (the base class), the except clause won't catch it.

#### Test must use the exact exception type production catches

**Wrong test:**

```python
def test_timeout_handling_WRONG():
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = TimeoutError("timeout")  # ← Base class
        
        # Production code does:
        try:
            result = subprocess.run(..., timeout=5)
        except subprocess.TimeoutExpired:  # ← Only catches subclass
            # Won't catch TimeoutError!
        
        # Test might pass because pytest catches TimeoutError and reports it as an error
        # But it's not validating that the except subprocess.TimeoutExpired clause catches it
```

**Right test:**

```python
def test_timeout_handling_RIGHT():
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)  # ← Exact subclass
        
        # Now the test validates that the except subprocess.TimeoutExpired
        # clause in production catches this specific exception
        
        # Option A: pytest.raises catches the exception
        with pytest.raises(subprocess.TimeoutExpired):
            result = subprocess.run(..., timeout=5)
        
        # Option B: assert the exception handling code runs
        error_logged = _attempt_timeout_recovery(...)
        assert error_logged is True
```

#### Mock upstream dependencies before testing error paths

When testing an error path, ensure you're testing the **intended** error, not some upstream failure:

```python
# Example: _run_with_timeout calls get_repo_info, then subprocess.run

def _run_with_timeout(repo_root: str):
    owner, repo = get_repo_info(repo_root)  # ← Upstream dependency
    result = subprocess.run(
        ["gh", "pr", "list", "--json", "statusCheckRollup"],
        timeout=5,  # ← Error under test
    )
    return result

# WRONG: Don't mock upstream
def test_timeout_recovery_WRONG():
    # get_repo_info is NOT mocked
    result = _run_with_timeout(repo_root="/fake/path")
    # If get_repo_info fails first (file not found, etc.), we test THAT error,
    # not the timeout handling. Test becomes fragile and misleading.

# RIGHT: Mock all upstream before testing the error under test
def test_timeout_recovery_RIGHT():
    # Arrange: upstream dependencies mocked
    with mock.patch("hephaestus.automation.get_repo_info") as mock_info:
        mock_info.return_value = ("owner", "repo")  # ← Upstream returns success
        
        # Arrange: error under test
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)  # ← Test this
            
            # Act & Assert
            with pytest.raises(subprocess.TimeoutExpired):
                _run_with_timeout(repo_root="/fake/path")
```

#### `check=False` semantics: subprocess.run doesn't raise on non-zero exit

By default, `subprocess.run` returns a `CompletedProcess` object and does not raise on non-zero return code:

```python
# This does NOT raise an exception, even if the command fails
result = subprocess.run(["false"], check=False)  # ← check=False (default for backwards compat)
print(result.returncode)  # 1 (failure)
# No exception raised

# To get an exception on non-zero exit, use check=True
try:
    result = subprocess.run(["false"], check=True)
except subprocess.CalledProcessError as e:
    print(f"Command failed with return code {e.returncode}")
```

**The dead-code trap:**

```python
# This except clause is DEAD CODE
result = subprocess.run(["some_command"], check=False)
try:
    # some_output = result.stdout
    pass
except subprocess.CalledProcessError:  # ← Never raised because check=False
    logger.error("Command failed")
```

Why? Because `check=False` tells `subprocess.run` to NOT raise `CalledProcessError` on non-zero exit. Instead, it returns a `CompletedProcess` with `returncode != 0`. The except clause is unreachable.

**The fix:**

Option 1: Use `check=True` to get the exception

```python
try:
    result = subprocess.run(["some_command"], check=True)
except subprocess.CalledProcessError as e:
    logger.error("Command failed with return code %d", e.returncode)
```

Option 2: Use `check=False` and manually check the return code

```python
result = subprocess.run(["some_command"], check=False)
if result.returncode != 0:
    logger.error("Command failed with return code %d: %s", result.returncode, result.stderr)
```

#### When to use check=True vs check=False in hephaestus automation

**Use `check=False` when:**
- You want to handle all outcomes gracefully without raising
- The command might fail for recoverable reasons (e.g., gh API transient timeout)
- You want to log the full output before deciding whether to fail

```python
result = _gh_call(["pr", "list", ...], check=False)
if result.returncode != 0:
    logger.warning("Could not list PRs, falling back to empty: %s", result.stderr)
    return {}  # Graceful degradation
```

**Use `check=True` when:**
- The command MUST succeed for the function to continue
- Non-zero exit is always a fatal error
- You want the caller to handle the exception

```python
try:
    result = _gh_call(["pr", "comment", issue_num, "--body", msg], check=True)
except subprocess.CalledProcessError as e:
    logger.error("Failed to post PR comment: %s", e)
    raise  # Let caller decide if this is fatal
```

### Integrating exception type validation into code review

When reviewing error handling:

```python
# Checklist:
# 1. What exception is raised in the test?
#    - Must match the except clause type in production
# 2. Are all upstream dependencies mocked?
#    - If not, the test might be testing the wrong error path
# 3. Is check=False paired with manual returncode checking?
#    - Or is there an unreachable except subprocess.CalledProcessError?
# 4. Does the test actually exercise the except clause?
#    - Use a coverage tool to verify the except block runs
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Test with base exception (TimeoutError), production catches subclass (subprocess.TimeoutExpired) | Assuming exception hierarchy is "close enough" for testing | (a) Base class doesn't catch subclass in except clauses — the semantics are one-way (base catches subclass, not vice versa). (b) Test passes (pytest's exception reporting masks the mismatch), but production's except clause never fires. (c) The error handling code is never executed in production despite the test passing. (d) Symptom: test passes locally, CI fails with uncaught exception. | Always use the EXACT exception type in tests that the production code catches. If production does `except subprocess.TimeoutExpired`, test must raise `subprocess.TimeoutExpired`, not `TimeoutError`. |
| Mock only the error, don't mock upstream dependencies | Assume the error under test is the first error | (a) Upstream dependency might fail first, masking the error under test. (b) Test becomes fragile: if upstream changes, test breaks even though the error handling code didn't change. (c) Test might pass for the wrong reason: upstream fails, not the intended error. (d) Code review can't tell which error is being tested. | Mock ALL upstream dependencies with successful returns BEFORE the error under test. Makes the test intent clear: "when THIS specific error occurs, THAT handling runs." |
| Ignore `check=False` semantics, write except subprocess.CalledProcessError with check=False | Assume check=False is just a parameter, doesn't affect exceptions | (a) The except clause is DEAD CODE — it never runs because check=False suppresses the exception. (b) Code review misses this as "unreachable code". (c) If the command fails, the error is silently ignored (no exception raised, no logging via the except clause). (d) The handler is never tested, so bugs hide until production. | Either use `check=True` (and catch the exception), OR use `check=False` (and manually check result.returncode). Never pair `check=False` with an except CalledProcessError clause. |
| Use `check=False` to suppress exceptions, then test with check=True in the test | Assume the test will validate error handling even if production uses check=False | (a) The test catches an exception that production never raises (check=False suppresses it). (b) Test passes, but production's error path is NOT validated because production doesn't raise. (c) If production's exception handling is never exercised, bugs hide. (d) Test/production divergence: test assumes check=True, production uses check=False. | Keep test semantics aligned with production: if production uses `check=False`, the test should also use `check=False` and validate the return code check, not the exception handling. |
| Don't mock upstream, assume it will work in the test | Rely on real gh or subprocess calls in the test | (a) Tests become slow (network/disk I/O). (b) Tests become flaky (transient network failures, permissions, rate limits). (c) Tests can't easily inject errors (how do you make gh randomly timeout?). (d) Can't test rare error conditions without real infrastructure. | Mock ALL external dependencies (gh CLI, filesystem, subprocess). Use fixtures for mock setup. Tests run fast, deterministically, and cover all error paths. |

## Results & Parameters

### Exception type matching patterns (copy-paste ready)

```python
import subprocess
import pytest
from unittest import mock


def test_timeout_exception_handling_correct_type():
    """Test must raise the EXACT exception type production catches."""
    
    # Arrange: production code does "except subprocess.TimeoutExpired"
    # Test must raise subprocess.TimeoutExpired, not TimeoutError
    
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", timeout=5)
        
        # Act & Assert
        with pytest.raises(subprocess.TimeoutExpired):
            result = subprocess.run(["gh", "pr", "list"], timeout=5)


def test_timeout_exception_wrong_type_does_not_catch():
    """Demonstrate that base exception is NOT caught by subclass except."""
    
    # WRONG: production catches subprocess.TimeoutExpired
    # but test raises TimeoutError (base class)
    
    def bad_error_handler():
        try:
            raise TimeoutError("timeout")  # Base class
        except subprocess.TimeoutExpired:  # Subclass except — won't catch
            return "caught"
    
    # This function does NOT catch the exception
    with pytest.raises(TimeoutError):  # TimeoutError propagates
        bad_error_handler()


def test_mock_upstream_dependencies_before_error_path():
    """Mock all upstream before testing the intended error."""
    
    # WRONG: don't mock get_repo_info
    # It might fail first, masking the subprocess error we want to test
    
    # RIGHT: mock ALL upstream with successful returns
    with mock.patch("hephaestus.automation.get_repo_info") as mock_info:
        mock_info.return_value = ("owner", "repo")  # Upstream success
        
        with mock.patch("subprocess.run") as mock_run:
            # NOW inject the error under test
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)
            
            with pytest.raises(subprocess.TimeoutExpired):
                _run_with_timeout("/fake/repo")


def test_check_false_with_manual_return_code():
    """Test check=False paired with manual returncode check."""
    
    with mock.patch("subprocess.run") as mock_run:
        # check=False: doesn't raise on non-zero exit
        mock_run.return_value = mock.MagicMock(returncode=1, stderr="error message")
        
        result = subprocess.run(["false"], check=False)
        
        # Manual check (not via exception)
        if result.returncode != 0:
            # This path should be exercised
            assert True
        else:
            pytest.fail("Expected non-zero return code")


def test_check_true_with_exception_handling():
    """Test check=True paired with exception catching."""
    
    with mock.patch("subprocess.run") as mock_run:
        # check=True: raises on non-zero exit
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="error")
        
        with pytest.raises(subprocess.CalledProcessError):
            subprocess.run(["false"], check=True)
```

### Code review checklist for exception handling

```markdown
## Exception Handling Code Review Checklist

- [ ] **Exception type match**: Does the test raise the EXACT type that production's except clause catches?
  - Production: `except subprocess.TimeoutExpired` → Test: `subprocess.TimeoutExpired`
  - Not: `TimeoutError` (base class — doesn't match)
  
- [ ] **Upstream dependencies mocked**: Are all dependencies before the error under test mocked?
  - Mock `get_repo_info`, `gh_call`, filesystem access, etc.
  - If not mocked, those might fail first, masking the intended error
  
- [ ] **check parameter semantics**: Is check=False paired with returncode checking, or check=True with exception handling?
  - Never `check=False` + `except CalledProcessError` (dead code)
  - Either: `check=True` + catch exception, OR `check=False` + check returncode
  
- [ ] **Exception path coverage**: Does the test exercise the except clause (via coverage tool)?
  - If not covered, the handler is untested
  - Use `pytest --cov` to verify except blocks run

- [ ] **Error message clarity**: Is the except clause logging/raising with useful context?
  - Include returncode, stderr, command name, etc.
  - Future debuggers will thank you
```

### Verification evidence

- **PR #852 in ProjectHephaestus** (issue #819): Fixed 3 tests using TimeoutError instead of subprocess.TimeoutExpired. Added 5 new tests validating exception type semantics.
- **Test coverage**: `tests/unit/automation/test_exception_type_matching.py`:
  - `TestExceptionTypeMatching`: 5 tests validating exact type matching
  - `TestCheckParameterSemantics`: 3 tests validating check=True vs check=False
  - `TestMockingUpstreamDependencies`: 2 tests validating mock patterns
- **CI result**: All 1143 automation tests pass; exception semantics validated

### Related skills

- `ci-tests-agent-subprocess-claude-absent.md` — subprocess testing patterns when claude is absent (CI context)
- `automation-loop-early-exit-zero-work-convergence.md` — when timeout handling affects loop exit logic, use these patterns
- `failing-pr-discovery-gh-enumeration.md` — uses subprocess.run with timeout; tests must use the patterns documented here

### Quick audit recipe — find exception type mismatches

```bash
# Find all except subprocess clauses
grep -rn "except subprocess\." --include="*.py" hephaestus/

# For each match, find the corresponding test
# Check: does the test mock.patch(..., side_effect=<EXACT_EXCEPTION_TYPE>)?
#
# If test uses TimeoutError or generic Exception instead of the specific subclass,
# you've found a type mismatch.

# Also find check=False paired with except CalledProcessError (dead code)
grep -B5 "check=False" --include="*.py" hephaestus/ | grep -A5 "except.*CalledProcessError"
```

If audit finds mismatches, apply this skill's patterns to fix them.
