---
name: testing-module-patch-target-after-extraction
license: BSD-3-Clause
description: "Patch mocks at every module import binding after extracting collaborators, including direct and delegated dual call paths. Use when: (1) a refactor moves code from a god-class to collaborators, (2) tests have unexpected mock call counts or exhausted side effects, (3) the same symbol is called by both a driver and a collaborator, (4) resolving rebase conflicts in patch targets, (5) distinguishing shared stdlib module-object patches from named-function bindings that must move, (6) retargeting object-form `monkeypatch.setattr(module, \"name\", ...)` patches that string greps do not find, or (7) proving with an executable hasattr sweep that no test still patches a moved symbol at its old home."
category: testing
date: 2026-07-17
version: "2.2.0"
user-invocable: false
verification: verified-ci
tags:
  - python
  - testing
  - mock
  - patch
  - module-extraction
  - god-class
  - collaborator
  - refactoring
  - pytest
  - unittest-mock
  - subprocess
  - stdlib
  - rebase
  - cluster-extraction
  - dual-patch
  - call-paths
  - monkeypatch
  - ci-tiering
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/testing-module-patch-target-after-extraction.history"
history-cleanup-date: "2026-09-20"
---

# Testing: Module-Level Patch Target After Extraction

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Fix failing unit tests after extracting collaborator modules from a god-class |
| **Outcome** | Successful — CI gate passes with correct patch targets |
| **Verification** | verified-ci |

## When to Use

- After any module extraction refactor (god-class → collaborators)
- When tests fail with `StopIteration` or `AssertionError: Expected call not found` after a refactor
- When mock `side_effect` lists are consumed fewer times than expected
- When patches that "worked before the refactor" no longer intercept calls
- When `assert_called_once_with` shows 0 calls despite the code path executing
- During rebase conflict resolution on test files after parallel cluster extraction — HEAD (main's version) already has correct patch targets for the new module; prefer HEAD for patch target conflicts
- When a patch at `old_module.stdlib_function` still works after extraction (stdlib module-object exception) but `old_module.named_helper` does NOT (named-function patches must follow the symbol to its new namespace)
- When tests patch with the object form `monkeypatch.setattr(old_module, "some_function", stub)` — string greps for `@patch("...")` do not find these targets, and a stale one raises `AttributeError` when the test sets up its mocks
- When PR CI is green but a nightly or path-gated test tier fails after merge with `AttributeError: module 'X' has no attribute 'Y'` at mock-setup time — tests outside the PR CI tier kept stale patch targets

## Verified Workflow

### Quick Reference

```bash
# After extracting new_module.py from old_module.py:
# WRONG - patches the old binding
@patch("old_module.some_function")
monkeypatch.setattr(old_module, "some_function", stub)

# CORRECT - patches where the symbol is actually bound
@patch("new_module.some_function")
monkeypatch.setattr(new_module, "some_function", stub)
```

**Core rule**: Python binds a symbol in the module that imports it at import time. `patch("module.symbol")` intercepts lookups of `symbol` in `module`'s namespace — not in the module where `symbol` was originally defined.

### Detailed Steps

1. **Identify all symbols moved to the new module** — list every `from x import y` in the new collaborator file.

2. **Audit tests for the old module** — search for `@patch("old_module.<symbol>")` where `<symbol>` now lives in `new_module`. Also search for object-form `setattr` targets, which string greps for `@patch` do not find:

   ```bash
   grep -rn 'patch("hephaestus.automation.ci_driver\.' tests/unit/automation/
   grep -rnE 'setattr\([A-Za-z_][A-Za-z0-9_.]*,\s*"' tests/
   ```

3. **Check for split call paths** — a symbol may be called from BOTH the old module (still imported there) AND the new collaborator. Each import site requires its own patch:
   - `@patch("old_module.symbol")` — for calls made through the old module's namespace
   - `@patch("new_module.symbol")` — for calls made through the collaborator's namespace

4. **Pre-agent vs post-agent paths** — when a driver has pre-agent setup code AND post-agent cleanup code that call the same underlying function, each may import it at a different binding:

   ```python
   # ci_fix_orchestrator.py imports run() at module level
   from subprocess import run  # → bind: ci_fix_orchestrator.run

   # ci_driver.py also imports run() at module level
   from subprocess import run  # → bind: ci_driver.run

   # Tests for pre-agent calls must patch ci_fix_orchestrator.run
   # Tests for post-agent calls must patch ci_driver.run
   ```

5. **Direct vs delegated call paths** — when the driver delegates to a collaborator (`self._pr_discovery.discover_bot_prs()`), the collaborator's methods use symbols imported in the collaborator module, not the driver module:

   ```python
   # WRONG: patches driver binding, misses collaborator calls
   @patch("hephaestus.automation.ci_driver.get_repo_info")

   # CORRECT: patches where collaborator actually bound the symbol
   @patch("hephaestus.automation.pr_discovery.get_repo_info")
   ```

6. **Logger patches** — when a class moves to a new module, its logger is bound in the new module:

   ```python
   # WRONG after extracting PRDiscovery to pr_discovery.py:
   @patch("hephaestus.automation.ci_driver.logger")

   # CORRECT:
   @patch("hephaestus.automation.pr_discovery.logger")
   ```

7. **Run tests** with verbose output to confirm all call counts match expected:

   ```bash
   pixi run pytest tests/unit/automation/test_pr_discovery.py -v
   pixi run pytest tests/unit/automation/test_ci_driver.py -v
   ```

### Worked Example — Dual-patch pattern for split call paths

When a method chain splits across modules (e.g., pre-agent SHA snapshot moved to a collaborator while post-agent SHA read stays on the host):

```python
# WRONG — only patches the orchestrator's run:
with patch("hephaestus.automation.ci_fix_orchestrator.run", ...):
    driver._run_ci_fix_session(...)

# RIGHT — patches both lookup sites:
with (
    patch("hephaestus.automation.ci_fix_orchestrator.run", return_value=pre_sha),
    patch("hephaestus.automation.ci_driver.run", return_value=post_sha),
):
    driver._run_ci_fix_session(...)
```

### Stdlib module-object exception (patches that still work across extraction)

Not all patches need retargeting after extraction. **Stdlib module patches** continue to intercept calls from the new module without change:

```python
# STILL WORKS after extracting calls to new_module.py:
@patch("old_module.subprocess.run")   # patches the subprocess MODULE OBJECT in old_module's namespace
# → new_module imports 'import subprocess' and calls subprocess.run()
# → both reference the SAME underlying subprocess module object
# → the patch intercepts calls from new_module too
```

**Named-function patches** do NOT survive extraction:

```python
# BROKEN after extracting calls to new_module.py:
@patch("old_module.resilient_call")   # patches the 'resilient_call' name in old_module's namespace
# → new_module imported 'from old_module import resilient_call' at module load time
# → the name 'resilient_call' in new_module's namespace is a DIFFERENT binding
# → the patch at old_module.resilient_call does not intercept calls from new_module

# CORRECT — retarget to the new module:
@patch("new_module.resilient_call")
```

**Decision rule**:

| Patch form | Survives extraction? | Why |
|------------|---------------------|-----|
| `@patch("old_mod.subprocess.run")` | YES (usually) | Patches the `subprocess` module object; `new_mod` accesses the same object via `import subprocess` |
| `@patch("old_mod.named_function")` | NO | Patches a name binding in `old_mod`'s namespace; `new_mod` has its own binding created at import time |
| `@patch("old_mod.SomeClass")` | NO | Same as named-function — a class is a name binding |
| `@patch("old_mod.CONSTANT")` | NO | Module-level constants are bound by name at import |

**Audit command** — distinguish the two patterns:

```bash
# Find all patches in test files and classify:
grep -rn '@patch\|with patch' tests/ | grep -oP '"[^"]+"' | while read target; do
    # If it matches old_module.stdlib_module.method → likely safe
    # If it matches old_module.function_name → must retarget after extraction
    echo "$target"
done
```

### Object-form setattr targets and the executable hasattr proof sweep

The object form binds the mock by module object and attribute name, not by a patch string:

```python
# WRONG after moving some_function to new_module.py:
monkeypatch.setattr(old_module, "some_function", stub)   # AttributeError at mock-setup time

# CORRECT - follow the symbol to its new namespace:
monkeypatch.setattr(new_module, "some_function", stub)
```

Two properties change the audit:

- Grep audits for `@patch("module.symbol")` do not find object-form targets. The audit must also parse `setattr(<module>, "<name>"`.
- A stale object-form target fails fast: with the default `raising=True`, `monkeypatch.setattr` raises `AttributeError` when the test sets up its mocks. A `raising=False` target is different — it creates a missing attribute silently and is usually a deliberate trap that asserts a retired seam stays unused.

**Tiered CI failure mode**: a green PR run is not tier coverage. When a repository runs test tiers, tests outside the PR tier keep stale targets and fail after merge at mock-setup time with `AttributeError: module 'X' has no attribute 'Y'`. After every module move, run the sweep below over the complete test tree, not only over the tests that PR CI runs.

**Executable hasattr sweep** — parse both patch forms across the test tree, import each target module, and check each patched name. Run it from the repository root with the project environment active, because the targets import project modules:

```python
# sweep_patch_targets.py -- run from the repository root:
#   python sweep_patch_targets.py [tests-dir]
# Prints every test patch target that no longer resolves on current code.
# Zero STALE lines after a module move is the proof that no test still
# patches a moved symbol at its old home.
import ast
import importlib
import os
import pathlib
import sys

# Patch targets are imported relative to the repository root, so make the
# directory the sweep runs from importable even when the script lives elsewhere.
sys.path.insert(0, os.getcwd())

def dotted_path(node, aliases):
    """Resolve a Name or Attribute chain to an importable dotted module path."""
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    if isinstance(node, ast.Attribute):
        base = dotted_path(node.value, aliases)
        return f"{base}.{node.attr}" if base else None
    return None  # dynamic expressions are out of scope

def import_best(parts):
    """Import the longest importable module prefix of a dotted target."""
    for i in range(len(parts) - 1, 0, -1):
        try:
            return importlib.import_module(".".join(parts[:i])), parts[i:]
        except ImportError:
            continue
    return None, None

def kwarg_value(call, name):
    """Return the constant value of a keyword argument, or None."""
    for k in call.keywords:
        if k.arg == name and isinstance(k.value, ast.Constant):
            return k.value.value
    return None

def record_import(node, scope):
    """Bind one import statement into the current scope."""
    if isinstance(node, ast.Import):
        for a in node.names:
            if a.asname:
                scope[a.asname] = a.name  # alias binds the full dotted path
            else:
                top = a.name.split(".")[0]
                scope[top] = top  # plain import binds the top-level package
    elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
        for a in node.names:
            if a.name != "*":
                scope[a.asname or a.name] = f"{node.module}.{a.name}"

def check_call(node, scope, path, stale, unknown):
    """Classify one patch or setattr call against the current module state."""
    if not node.args:
        return
    func, arg0 = node.func, node.args[0]
    # Object form: setattr(<module>, "<name>", <stub>)
    if ((isinstance(func, ast.Name) and func.id == "setattr")
            or (isinstance(func, ast.Attribute) and func.attr == "setattr")):
        if kwarg_value(node, "raising") is False:
            return  # a deliberate trap on a retired seam, not a stale target
        if not (len(node.args) >= 2 and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)):
            return
        module = dotted_path(arg0, scope)
        if not module:
            return
        try:
            obj = importlib.import_module(module)
        except ImportError:
            unknown.append(f"{path}: cannot import {module}")
            return
        if not hasattr(obj, name := node.args[1].value):
            stale.append(f'STALE {path}: setattr({module}, "{name}")')
    # String form: patch("pkg.module.symbol")
    elif (isinstance(arg0, ast.Constant) and isinstance(arg0.value, str)
          and (isinstance(func, ast.Name) and func.id == "patch"
               or isinstance(func, ast.Attribute) and func.attr == "patch")):
        if kwarg_value(node, "create") is True:
            return  # a deliberate trap on a retired seam, not a stale target
        obj, rest = import_best(arg0.value.split("."))
        if obj is not None and rest and not hasattr(obj, rest[0]):
            stale.append(f'STALE {path}: patch("{arg0.value}")')

def scan_scope(node, inherited, path, stale, unknown):
    """Walk one scope; nested functions and lambdas get their own alias map."""
    scope = dict(inherited)
    calls, nested = [], []
    pending = list(ast.iter_child_nodes(node))
    while pending:
        child = pending.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            nested.append(child)
            continue
        if isinstance(child, (ast.Import, ast.ImportFrom)):
            record_import(child, scope)
        elif isinstance(child, ast.Call):
            calls.append(child)
        pending.extend(ast.iter_child_nodes(child))
    for call in calls:
        check_call(call, scope, path, stale, unknown)
    for fn in nested:
        scan_scope(fn, scope, path, stale, unknown)

stale, unknown = [], []
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "tests")
for path in sorted(root.rglob("*.py")):
    if any(part.startswith(".") for part in path.parts):
        continue
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except SyntaxError as exc:
        unknown.append(f"{path}: parse error: {exc}")
        continue
    scan_scope(tree, {}, path, stale, unknown)

print("\n".join(stale) if stale else "OK: zero stale patch targets")
if unknown:
    print(f"{len(unknown)} unresolvable target(s):", file=sys.stderr)
    print("\n".join(unknown), file=sys.stderr)
sys.exit(1 if stale else 0)
```

Read the result:

- Exit status 0 and `OK: zero stale patch targets` is the proof that no test still patches a moved symbol at its old home.
- Each `STALE` line is a candidate. Confirm it, then retarget the patch to the module that now owns the symbol.
- The `unresolvable target(s)` list on stderr is not a failure. It collects dynamic expressions and modules that the environment cannot import. Treat an empty `STALE` list with a large unresolvable list as weaker evidence.

The sweep resolves imports per function scope, so the same alias can bind different modules in different test functions. For string-form targets it checks the first name after the module.

### Preferred patch targets during rebase conflict resolution

When rebasing a test file after parallel cluster extraction, you may encounter a conflict where:
- `HEAD` (main) uses `@patch("new_module.resilient_call")` (correct)
- `REBASE_HEAD` (your branch) uses `@patch("old_module.resilient_call")` (stale)

**Resolve each patch target against the combined code.** The base branch may contain updated targets after extraction, while the incoming branch can add new call paths. Follow the actual lookup binding rather than selecting one side for all conflicts.

```bash
# Inspect both versions without overwriting the conflicted test file:
git show HEAD:tests/unit/automation/test_new_module.py
git show REBASE_HEAD:tests/unit/automation/test_new_module.py
```

Resolve individual bindings against the combined implementation. Preserve intended
changes to existing tests, functions, imports, and fixtures as well as new classes.
The branch name alone does not establish the correct lookup target.

### Systematic audit after any extraction

```bash
# 1. List all symbols imported in the new collaborator module
grep "^from\|^import" new_module.py

# 2. Find all test patches that reference the old module for those symbols
grep -rn 'patch("pkg.old_module\.' tests/

# 3. For each match, determine if the symbol now lives in new_module
#    If yes → retarget the patch

# 4. Also check for patches targeting the new module that reference symbols
#    still imported directly in old_module (dual-binding case)

# 5. Prove the result: run the executable hasattr sweep over the complete
#    test tree (see "Object-form setattr targets" above). It covers both
#    string-form and object-form targets, including tests that PR CI
#    does not run.
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Patch only `ci_driver.get_repo_info` | Patched at driver namespace after extracting `pr_discovery.py` | `pr_discovery.py` imported `get_repo_info` at its own module level; driver patch never intercepted collaborator calls | Python binds symbols at import time in the importing module's namespace |
| Patch only `ci_driver.run` for pre-agent path | Assumed all `run()` calls go through `ci_driver` namespace | `ci_fix_orchestrator.py` imports `run` independently; pre-agent call uses `ci_fix_orchestrator.run` binding | Each module that imports a symbol creates an independent binding |
| Single `side_effect` list for one patch | Assumed one `@patch` covers all call sites | Collaborator module had its own binding; side_effect consumed by only one path, leaving the other to call the real function | Count distinct import sites, not call sites |
| Left `@patch("ci_driver.logger")` after extraction | Assumed logger patch target unchanged | Logger is instantiated at module level in the new collaborator; the old binding was no longer the one emitting the warning | After extracting a class/function, grep all test patches for module-level logger, constant, and utility patches and retarget them |
| Retargeted `subprocess.run` patches after extraction | Moved `@patch("old_module.subprocess.run")` to `@patch("new_module.subprocess.run")` assuming all patches need moving | Both reference the same underlying `subprocess` module object; the original patch still intercepted calls from the new module | Apply the module-object exception: `import subprocess; subprocess.run()` patches work across module boundaries; only named-function patches (`from old_module import named_fn`) require retargeting |
| Took branch's patch targets during rebase conflict on test file | During an add/add rebase conflict, took REBASE_HEAD's version of patch targets instead of HEAD's | Branch's version used stale `old_module.*` targets; HEAD (main's already-merged PR) had already corrected them to `new_module.*` | Inspect the combined lookup binding and both versions; preserve intended test changes while correcting stale targets |
| Kept object-form `monkeypatch.setattr(old_module, "moved_symbol", ...)` targets after a module move | The audit grepped only for `@patch("module.symbol")` strings, so object-form targets at the old binding survived every string audit | Tests outside the PR CI tier kept the stale targets; after merge they raised `AttributeError` at mock-setup time | Audit object-form `setattr(<module>, "<name>"` targets together with string-form patches, and prove zero stale targets with the executable hasattr sweep |

## Results & Parameters

After applying correct patches, the pattern for extracted collaborators is:

```python
# Before extraction (god-class, all calls go through ci_driver):
@patch("hephaestus.automation.ci_driver.get_repo_info")
@patch("hephaestus.automation.ci_driver._gh_call")
def test_discover_bot_prs(self, mock_gh, mock_repo):
    ...

# After extraction (collaborator pr_discovery.py):
@patch("hephaestus.automation.pr_discovery.get_repo_info")   # collaborator binding
@patch("hephaestus.automation.pr_discovery._gh_call")         # collaborator binding
def test_discover_bot_prs(self, mock_gh, mock_repo):
    ...

# When BOTH driver and collaborator call the same symbol (dual-binding):
@patch("hephaestus.automation.ci_driver.gh_pr_checks")              # driver's poll loop
@patch("hephaestus.automation.ci_check_inspector.gh_pr_checks")     # collaborator's binding
def test_poll_loop(self, mock_inspector, mock_driver):
    ...
```

### Grep commands for the audit

```bash
# Find all patches in test files for a given module
grep -rn '@patch.*ci_driver\.' tests/unit/automation/ | grep -v "\.pyc"

# Find where a symbol is imported in the new collaborator modules
grep -rn "^from.*import.*get_repo_info\|^import.*get_repo_info" hephaestus/automation/*.py

# Identify dual-binding cases — symbol imported in both old and new module
grep -l "import get_repo_info\|from.*import.*get_repo_info" hephaestus/automation/*.py
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | PR #1292 (issue #1179) — decompose CIDriver into 4 collaborators (`pr_discovery.py`, `ci_check_inspector.py`, `ci_fix_orchestrator.py`, `post_merge_processor.py`) | verified-ci — 146 existing tests + 22 new tests pass |
| ProjectHephaestus | PR #1360 (issue #1360) — parallel cluster extraction of `loop_repo_manager.py` from `loop_runner.py`. During rebase after #1361 merged: `subprocess.run` patches at `loop_runner.subprocess.run` still intercepted calls from `loop_repo_manager.py` (stdlib module-object exception); `loop_runner.resilient_call` patches did NOT intercept calls from `loop_repo_manager.py` (named-function, must retarget to `loop_repo_manager.resilient_call`). HEAD's test targets were already correct — preferred HEAD during conflict resolution. | verified-ci — 1747 tests passed after rebase |
| A large Python service monorepo | Follow-up fix after a scheduler-symbol module move: three stale patch targets in a test tier that PR CI does not run | verified — executable hasattr sweep over the complete test tree reported zero stale targets after retargeting; the affected test passed |
