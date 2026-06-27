---
name: testing-subprocess-helper-mocks-during-refactor
description: "After refactoring code that calls subprocess helpers (run_subprocess, subprocess.check_output, etc.), unit tests must update mocks to match the ACTUAL return type of the helper being tested. Use when: (1) refactoring code that changes which subprocess helper is used (run_subprocess vs subprocess.check_output), (2) test mocks fail with AttributeError on stdout/stderr/returncode after extraction, (3) tests expect CompletedProcess with specific attributes but the helper returns a different type, (4) test side_effect mocks don't match the actual return type of the helper being called, (5) extracting small helper functions from larger modules that call subprocess — verify helpers match their callsites' expectations."
category: testing
date: 2026-06-27
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - python
  - testing
  - mock
  - subprocess
  - refactoring
  - CompletedProcess
  - test-mocks
  - unittest-mock
  - helper-functions
  - function-extraction
---

# Testing: Subprocess Helper Mocks During Refactoring

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-27 |
| **Objective** | Fix unit test failures when refactoring code that uses subprocess helpers — ensure mock return types match the actual helper's return type |
| **Outcome** | Successful — PR #1633 CI tests pass after updating mock patterns to match subprocess helper return types |
| **Verification** | verified-ci (335 github module tests passing) |
| **Issue** | ProjectHephaestus#1633 (refactor github CLI subcommand handlers) |

## When to Use

- After extracting helper functions that call subprocess helpers (run_subprocess, subprocess.check_output, etc.)
- When tests fail with `AttributeError: MagicMock object has no attribute 'stdout'` or similar
- When test mocks expect `CompletedProcess` but the helper returns a string or different type
- When refactoring code changes which subprocess helper is used
- When existing mock patterns don't match the actual return type of the helper being tested
- When function signatures change during extraction (e.g., removing `args` parameter) and the extraction breaks test calls

## Root Cause Pattern

During refactoring, a helper function's implementation detail (which subprocess helper it uses) may change:

```python
# ORIGINAL: uses run_subprocess, returns CompletedProcess-like object
def local_branch_exists(branch_name: str) -> bool:
    result = run_subprocess(["git", "branch", "--list", branch_name])
    return bool(result.stdout.strip())  # expects .stdout attribute

# REFACTORED: changed to subprocess.check_output, returns bytes
def local_branch_exists(branch_name: str) -> bool:
    out = subprocess.check_output(["git", "branch", "--list", branch_name])
    return bool(out.strip())  # expects bytes with .strip()
```

If the test still mocks the old `run_subprocess` pattern, the mock will be wrong for the new implementation.

## Verified Workflow

### Quick Reference

```bash
# 1. After refactoring a function, read the ACTUAL implementation
sed -n '150,160p' hephaestus/github/pr_merge.py  # check what subprocess helper is used

# 2. Find the test that mocks this function
grep -rn "local_branch_exists" tests/unit/github/test_pr_merge.py

# 3. Read the test's mock setup
# WRONG: mocks run_subprocess, expects CompletedProcess
@patch("hephaestus.github.pr_merge.run_subprocess")
def test_local_branch_exists(mock_run):
    mock_run.return_value = MagicMock(stdout="main")  # ← expects CompletedProcess

# 4. Check what the actual implementation calls
# If implementation changed to subprocess.check_output, update mock:
@patch("hephaestus.github.pr_merge.subprocess.check_output")
def test_local_branch_exists(mock_check_output):
    mock_check_output.return_value = b"main"  # ← matches check_output return type
```

### Detailed Steps

1. **Read the refactored helper function** — identify WHICH subprocess helper it calls:
   - `run_subprocess(...)` → returns `CompletedProcess`-like object with `.stdout`, `.stderr`, `.returncode`
   - `subprocess.check_output(...)` → returns `bytes`
   - `subprocess.run(...)` → returns `CompletedProcess` with `.stdout`, `.stderr`, `.returncode`
   - `subprocess.Popen(...)` → returns `Popen` object, must call `.communicate()` or read `.stdout`

   ```bash
   grep -A5 "def local_branch_exists" hephaestus/github/pr_merge.py
   ```

2. **Find all tests that mock this helper** — search for the helper name in test files:

   ```bash
   grep -n "local_branch_exists" tests/unit/github/test_pr_merge.py
   grep -n "patch.*run_subprocess\|patch.*subprocess" tests/unit/github/test_pr_merge.py
   ```

3. **Identify which subprocess helper the test currently mocks** — read the `@patch` decorator:

   ```python
   # ORIGINAL test mocks run_subprocess
   @patch("hephaestus.github.pr_merge.run_subprocess")
   def test_local_branch_exists(self, mock_run):
       mock_run.return_value = MagicMock(stdout="main")
   ```

4. **Compare the test's mock helper to the implementation** — if they don't match, update the mock:

   ```python
   # REFACTORED function uses subprocess.check_output
   def local_branch_exists(branch_name: str) -> bool:
       out = subprocess.check_output([...], stderr=subprocess.DEVNULL)
       return bool(out.strip())

   # UPDATED test must patch subprocess.check_output instead
   @patch("hephaestus.github.pr_merge.subprocess.check_output")
   def test_local_branch_exists(self, mock_check_output):
       mock_check_output.return_value = b"main"  # bytes, not CompletedProcess
   ```

5. **Verify the mock return type matches the helper's return type**:

   | Helper | Return Type | Mock Pattern |
   |--------|-------------|--------------|
   | `run_subprocess(...)` | `CompletedProcess` | `MagicMock(stdout="...", stderr="...", returncode=0)` |
   | `subprocess.check_output(...)` | `bytes` | `b"..."` |
   | `subprocess.run(...)` | `CompletedProcess` | `MagicMock(stdout="...", stderr="...", returncode=0)` |
   | `subprocess.Popen(...)` | `Popen` object | `MagicMock(communicate=MagicMock(return_value=(b"out", b"err")))` |

6. **Update test function calls to match new signatures** — if helper extraction changed the function signature, update the test calls:

   ```python
   # ORIGINAL: function took args dict
   def _process_pr(args: argparse.Namespace, repo_name: str, pr: dict) -> None:
       # ... uses args.push_all, args.dry_run

   # Test call:
   _process_pr(args_mock, repo_name, pr)

   # REFACTORED: extracted individual parameters
   def _process_pr(repo_name: str, pr: dict, push_all: bool, dry_run: bool) -> None:
       # ... uses push_all, dry_run directly

   # Updated test call:
   _process_pr(repo_name, pr, push_all=True, dry_run=False)
   ```

7. **Run the updated tests** to verify they pass:

   ```bash
   pixi run pytest tests/unit/github/test_pr_merge.py::TestLocalBranchExists -v
   pixi run pytest tests/unit/github/test_tidy.py::TestTidyHandlers -v
   ```

### Common Failure Patterns

**Failure 1: AttributeError on mock object**

```
AttributeError: MagicMock object has no attribute 'stdout'
```

**Root cause**: Test mocks `subprocess.check_output` but expects `CompletedProcess.stdout`.
**Fix**: Change mock return value to `bytes`:

```python
@patch("module.subprocess.check_output")
def test_x(self, mock_check):
    # WRONG:
    # mock_check.return_value = MagicMock(stdout=b"data")

    # CORRECT:
    mock_check.return_value = b"data"
```

**Failure 2: TypeError when calling helper with wrong signature**

```
TypeError: _process_pr() got an unexpected keyword argument 'args'
```

**Root cause**: Test still calls with old `args` parameter, but extraction removed it.
**Fix**: Update test call to use individual parameters:

```python
# WRONG:
# _process_pr(args, repo_name, pr)

# CORRECT:
_process_pr(repo_name, pr, push_all=args.push_all, dry_run=args.dry_run)
```

**Failure 3: Mock side_effect list consumed incorrectly**

```
StopIteration: generator raised StopIteration
```

**Root cause**: Mock `side_effect` list expects N calls, but test makes M calls (N ≠ M).
**Fix**: Verify the mock is set up with the correct number of expected call sequences and adjust test to match actual behavior.

## Key Learnings from PR #1633

**Case Study: GitHub CLI refactoring (ProjectHephaestus#1633)**

5 distinct CI failure classes and their fixes:

1. **Subprocess implementation rollback** (pr_merge.py):
   - Initial refactor changed `local_branch_exists()` from `run_subprocess()` to `subprocess.check_output()`
   - Tests expected `CompletedProcess` with `stdout` attribute
   - **Fix**: Reverted to `run_subprocess()` and updated test mocks to use `MagicMock(stdout="...")`

2. **Constants import removal** (tidy.py):
   - Refactor removed import of `agent_rebase_timeout` from `hephaestus.constants`
   - Code tried to call undefined `agent_rebase_timeout()`
   - **Fix**: Hardcoded timeout to 2400 seconds (the original default value)

3. **Function signature changes** (both files):
   - Extracted handlers changed from `_process_pr(args, ...)` to `_process_pr(..., push_all: bool, dry_run: bool)`
   - Tests still used old signatures
   - **Fix**: Updated all test calls to use new individual parameters

4. **New helper functions without test coverage**:
   - Refactor introduced new extracted functions with no tests
   - **Fix**: Added new test classes (`TestProcessPr`, `TestTidyHandlers`) with explicit coverage

5. **Function renaming** (tidy.py):
   - `_handle_tidy_problem_branches()` renamed to `_handle_problem_branches()`
   - Test calls used old name
   - **Fix**: Updated test calls to use new name

**Files changed**: `hephaestus/github/pr_merge.py` (128 +/- lines), `hephaestus/github/tidy.py` (104 +/- lines), `tests/unit/github/test_pr_merge.py` (56+ lines), `tests/unit/github/test_tidy.py` (39+ lines)

**Outcome**: All 335 GitHub module tests passing after fixes.

## Prevention Strategies

1. **Read the implementation before mocking** — don't assume which subprocess helper is used; grep the actual source
2. **Test small, extracted helpers separately** — create dedicated test classes for new extracted functions
3. **Use integration tests for subprocess calls** — when possible, avoid mocking subprocess helpers; test end-to-end
4. **Document helper return types in docstrings** — make the return type explicit so refactorers know what to mock
5. **Run tests immediately after extraction** — don't wait until CI to discover mock mismatches

## Failed Attempts

### Attempt 1: Continuing with run_subprocess after refactoring to subprocess.check_output
- **Problem**: Assumed the original subprocess helper would continue to work after the refactoring changed to `subprocess.check_output`
- **Outcome**: Tests failed with `AttributeError` because mocks expected `CompletedProcess.stdout` but `check_output` returns `bytes`
- **Resolution**: Reverted the implementation change and stuck with `run_subprocess` for consistency with test expectations

### Attempt 2: Keeping old function signatures after extraction
- **Problem**: Extracted handlers from `_process_pr(args, ...)` to `_process_pr(..., push_all, dry_run)` without updating all test calls
- **Outcome**: Tests failed with `TypeError: unexpected keyword argument 'args'` because they still used the old signature
- **Resolution**: Updated all test calls to use the new individual parameter signatures

## Results & Parameters

### Test Coverage Results

After implementing the fixes:
- **test_pr_merge.py**: Added `TestProcessPr` class with 2 new test methods for extracted functions
- **test_tidy.py**: Added `TestTidyHandlers` class with 2 new test methods for extracted handler functions
- **Total tests passing**: 335 GitHub module tests (all green after fixes)

### Mock Pattern Reference Table

| Subprocess Helper | Return Type | Mock Setup | When Used |
|-------------------|-------------|-----------|-----------|
| `run_subprocess([...])` | `CompletedProcess`-like | `MagicMock(stdout="data", stderr="", returncode=0)` | Hephaestus utility helper with logging |
| `subprocess.check_output([...])` | `bytes` | `b"data"` | Raw Python stdlib for simple string output |
| `subprocess.run([...])` | `CompletedProcess` | `MagicMock(stdout="data", stderr="", returncode=0)` | Python stdlib with pipe options |
| `subprocess.Popen([...])` | `Popen` object | `MagicMock(communicate=MagicMock(return_value=(b"out", b"err")))` | Long-running processes with streams |

### Parametrization for Different Scenarios

**Scenario 1**: Testing a helper that calls `run_subprocess`
```python
@patch("module.run_subprocess")
def test_helper(self, mock_run):
    mock_run.return_value = MagicMock(stdout="main\n", stderr="")
    assert helper_function("branch") == True
```

**Scenario 2**: Testing a helper that calls `subprocess.check_output`
```python
@patch("module.subprocess.check_output")
def test_helper(self, mock_check):
    mock_check.return_value = b"main\n"
    assert helper_function("branch") == True
```

**Scenario 3**: Testing extracted helper with new signature
```python
def test_extracted_handler(self):
    # Call with new individual parameters, not old args dict
    result = _process_pr(
        repo_name="owner/repo",
        pr={"number": 123},
        push_all=False,
        dry_run=True,
    )
    assert result is None  # handler returns None
```
