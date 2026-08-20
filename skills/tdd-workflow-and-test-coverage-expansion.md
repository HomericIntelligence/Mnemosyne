---
name: tdd-workflow-and-test-coverage-expansion
description: "Use when writing tests before implementation, expanding coverage for scripts or subprocess-heavy modules, auditing whether requested tests already exist, repairing tests after a refactor, adding import-boundary guards, or coordinating isolated coverage shards. Audit first, preserve a red-green-refactor proof, mock where the code looks up dependencies, and verify CI actually discovers every new test."
category: testing
date: 2026-06-15
version: "2.0.0"
verification: verified-ci
license: BSD-3-Clause
user-invocable: false
history: tdd-workflow-and-test-coverage-expansion.history
tags:
  - tdd
  - pytest
  - coverage
  - mocking
  - subprocess
  - ast
  - import-boundary
  - test-discovery
---

# TDD Workflow and Test-Coverage Expansion

## Overview

Use this skill to turn a behavior contract or coverage finding into non-duplicative tests and a
verified implementation. It covers test-first work, coverage audits, mock-only tests, parsing bugs,
post-refactor fixture repair, architectural import guards, and multi-branch coverage campaigns.

Verification remains `verified-ci`. Project-specific cases and detailed outcomes are in the
[notes](./tdd-workflow-and-test-coverage-expansion.notes.md); the byte-preserved source and prior
changelog are in [history](./tdd-workflow-and-test-coverage-expansion.history).

## When to Use

- A behavior change or bug fix needs a failing test before implementation.
- A script, command handler, or subprocess-heavy module has little or no coverage.
- An issue says “add any missing tests”; determine whether any are actually missing.
- Single-line and multi-line input shapes behave differently.
- A configuration or directory-layout refactor broke fixtures and path discovery.
- A circular import was fixed and needs an executable architecture boundary.
- New nested tests pass locally but CI or pytest does not discover them.
- Coverage work is large enough to require isolated worktrees or shards.
- Strict typing now rejects unannotated test functions or imprecise fixture types.
- Extracted collaborator methods need exact mocks for return shape, `cwd`, and error boundaries.

## Decision Rules

1. **Audit before writing.** Search all tests for the target symbol, class, behavior, and likely
   sibling filename. Build a requirement-to-test matrix. If every requirement is covered, add only
   a concise coverage mapping when the repository consumes it; do not invent redundant tests.
2. **Prove red before green.** A new behavior test must fail for the expected reason before the
   implementation is changed. A test that began green does not prove the change.
3. **Patch the lookup binding.** Inspect how the target imports the dependency. Patch the consumer
   namespace when `from x import y` binds `y` there; patch a definition module only when the code
   performs the lookup there. Never guess from the dependency’s origin.
4. **Match the real interface.** A two-tuple producer needs a two-tuple mock; an object consumer
   needs attributes such as `.stdout`; a direct boolean return must not be wrapped. Assert keyword
   arguments through `call_args.kwargs`.
5. **Prefer deterministic boundaries.** Use `tmp_path`, module-scoped mocks, and explicit state.
   Do not rely on real subprocesses, curses timing, background threads, or warm `sys.modules`.
6. **Test shape variants.** For line-oriented parsers include single-line, multi-line, unicode,
   quoted, empty, and malformed inputs when material. Assert the desired value and the absence of
   the broken representation.
7. **Make architecture guards cold and complete.** Test both import orders in fresh subprocesses;
   use `ast.walk`, not only `tree.body`, so lazy and function-local imports are caught.
8. **Verify discovery and CI routing.** Mirror nested source layouts under tests, add required
   `__init__.py` files, and inspect workflows that enumerate test files manually.
9. **Isolate broad work.** Give each coverage shard its own branch/worktree and owned files. Base
   the manifest on the current tree, not a stale coverage report.
10. **Keep evidence honest.** Report the focused result, the full-suite result, and coverage scope
    separately. Module coverage with `--no-cov-on-fail` is not proof of repository-wide coverage.
11. **Type tests deliberately.** Add `-> None` to test methods and precise fixture types such as
    `pytest.CaptureFixture[str]`; do not use broad `object` annotations merely to silence mypy.

## Verified Workflow

### 1. Inventory behavior and existing evidence

```bash
rg -n "TargetClass|target_function|expected behavior" tests scripts src
rg --files tests | sort
python3 -m pytest tests/unit/<area> -v --tb=short
```

Read the implementation, imports, fixture layout, configuration, and CI workflow. Record a matrix:

| Requirement | Existing test | Missing boundary | Planned proof |
| --- | --- | --- | --- |
| Happy path | `test_happy_path` | none | retain |
| Missing input | none | error path | new failing test |
| Single-line form | none | whitespace shape | parameterized regression |

For bulk expansion, rank targets by **Testability × Impact** (high=3, medium=2, low=1). Pure,
frequently executed entry points come before obscure subprocess wrappers. A campaign-specific
numeric floor is a planning parameter, not a universal definition of adequate coverage.

### 2. Run red-green-refactor

```bash
python3 -m pytest tests/unit/test_component.py -v  # RED: expected assertion/import failure
# implement the smallest behavior change
python3 -m pytest tests/unit/test_component.py -v  # GREEN
# refactor without changing the contract, then rerun
```

Use Arrange-Act-Assert. Test normal, edge, and error behavior rather than private line structure.
When an audit is already fully covered, stop: update the requirement mapping only if it has a
consumer, run the relevant suite, and report zero new tests.

### 3. Select the correct test seam

- Pure function: call directly.
- Filesystem: build the exact expected hierarchy under `tmp_path`.
- Subprocess: patch `<consumer_module>.subprocess.run`; cover timeout, `OSError`, and nonzero exit.
- Availability: patch `<consumer_module>.shutil.which`.
- CLI: pass realistic arguments, capture constructed config, and exercise continue/error behavior.
- Module constant: `patch("pkg.mod._REPO_ROOT", tmp_path)` and reproduce expected subdirectories.
- Concurrent UI: set the already-running state explicitly rather than racing a thread.
- Multiprocessing manager semantics: use a real managed context when mocks cannot reproduce proxy
  event/dictionary behavior.

```python
from unittest.mock import MagicMock, patch

def test_timeout_is_reported() -> None:
    with patch("pkg.validator.subprocess.run") as run:
        run.side_effect = subprocess.TimeoutExpired(cmd="tool", timeout=5)
        result = Validator().validate()
    assert "timed out" in (result.error_message or "").lower()
```

For extracted session drivers, preserve contract shapes:

```python
module = "pkg.post_merge_processor"
with patch(f"{module}.invoke_session", return_value=("stdout", None)) as invoke:
    result = processor.run_step(issue=1, pr=2)
assert invoke.call_args.kwargs["cwd"] == expected_worktree
assert result is True
```

Use a named helper for exception injection and a dedicated factory for materially different option
sets. Do not mutate an ephemeral `MagicMock` returned by another helper.

### 4. Diagnose parsing and refactor regressions

For line-oriented formats, avoid whole-string trimming when leading characters carry meaning:

```python
# Broken for `git status --porcelain`: removes the significant leading space.
lines = stdout.strip().split("\n")

# Preserves each line’s leading status columns.
lines = stdout.splitlines()
```

If multiple unrelated branches fail after a config refactor:

1. Reproduce on the current base to classify pre-existing versus introduced.
2. Identify the changing commit and compare old/new layouts.
3. Trace every `.parent` and configured root.
4. Recreate the full production-relative tree inside `tmp_path`.
5. Extract one fixture builder and apply it to all affected tests.

### 5. Guard import layers

```python
def _run_import(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)

def test_packages_import_in_both_orders() -> None:
    for code in ("import pkg.low, pkg.high", "import pkg.high, pkg.low"):
        result = _run_import(code)
        assert result.returncode == 0, result.stderr

def test_low_layer_does_not_import_high_layer() -> None:
    offenders: list[str] = []
    for path in sorted(LOW_DIR.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("pkg.high"):
                offenders.append(f"{path}:{node.lineno}")
    assert not offenders, offenders
```

Also handle `ast.Import` aliases. Locate packages through `__file__` so the guard works in editable
and installed layouts.

### 6. Verify discovery, coverage, and CI

```bash
python3 -m pytest tests/unit/<focused-file>.py -v
python3 -m pytest tests/unit/<area> -v --tb=short
<package-manager> run python -m pytest
<package-manager> run python -m pytest tests/unit/<file>.py \
  --cov=pkg.module --cov-report=term-missing --no-cov-on-fail
git diff --check
```

For `scripts/agents/*.py`, mirror `tests/unit/scripts/agents/` and include `__init__.py` when that
repository’s discovery rules require a package. Inspect `.github/workflows/*.yml` for manual test
lists. If new tests require structured docstrings, apply `What:`/`Executes:`/`Why:` only to the new
tests, then use an AST audit rather than prose-string assertions.

## Examples

### Quoted single-line status regression

Parameterize porcelain lines such as ` M "path with spaces/file.py"`, unicode paths, and `??`.
Provide `stdout = line + "\n"`, inspect the staged argv, assert the unquoted path is present, and
assert the quoted form is absent. A multi-line-only fixture will miss the leading-space bug.

### All-covered request

If a hash-coverage issue’s requirements already map to existing equality and shape tests, create
no duplicate test. Record the mapping in the accepted project location, run the focused and full
suites, and close with evidence that the audit found no gap.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Failure 1 | Write before searching | Duplicates sibling tests and stale issue filenames | Search all tests and build the matrix first |
| Failure 2 | Patch `subprocess.run` globally | Misses or overreaches the consumer binding | Patch the namespace used at runtime |
| Failure 3 | Mock wrong return shape | Unpacking or attribute access fails for the mock, not the product | Mirror tuple/object/direct-return contracts exactly |
| Failure 4 | Assert `cwd` positionally | Keyword-only call data is absent from `args` | Use `call_args.kwargs["cwd"]` |
| Failure 5 | Depend on thread timing | Fast mocks finish before the assertion | Set the running state explicitly |
| Failure 6 | Re-import in-process | `sys.modules` hides cold-import cycles | Spawn a fresh interpreter for each order |
| Failure 7 | Walk only `tree.body` | Misses nested and lazy imports | Use `ast.walk` |
| Failure 8 | Add files only locally | Manual CI shards never execute them | Update the consuming workflow or manifest |
| Failure 9 | Share one checkout across workers | Branch and staging state collide | One worktree and explicit ownership per shard |
| Failure 10 | Apply new docstring rules retroactively | Produces unrelated prose churn | Gate only new tests unless policy says otherwise |
| Failure 11 | Use a generator-throw lambda | Obscures the intended exception boundary | Use a named raising helper |
## Results & Parameters

| Parameter | Contract |
| --- | --- |
| Red phase | Must fail for the expected missing behavior |
| Patch target | Namespace looked up by the code under test |
| Parser matrix | Include materially distinct line/input shapes |
| Import guard | Fresh interpreter, both orders, recursive AST walk |
| Coverage report | State focused module and repository-wide scope separately |
| Broad campaign | Current-tree manifest, isolated worktrees, explicit CI discovery |
| Historical script floor | Cover at least 50% only when the scoped campaign inherits that target |

## Output Contract

Return the audited requirement matrix, red/green evidence, files changed, exact focused and full
commands, test and coverage results with scope, any CI-discovery update, and remaining unverified
boundaries. Do not claim new coverage when existing tests were merely rediscovered.

## Companions

- [Case notes](./tdd-workflow-and-test-coverage-expansion.notes.md)
- [Version history and superseded snapshot](./tdd-workflow-and-test-coverage-expansion.history)
