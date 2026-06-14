---
name: git-worktree-sys-path-precedence-issue
description: "Document the sys.path ordering issue in workspace-based git worktrees where the main project directory comes before the worktree in Python's module search path, causing subprocess-spawned entry points (console scripts) to import modules from the main repo instead of the worktree, even though the editable install (.pth file) correctly points to the worktree. Code changes work in direct Python imports but fail in subprocess invocations. Also covers the pixi console script stale-binary failure mode where the script shebang points to the main worktree's installed package. Use when: (1) running console scripts via subprocess that load stale code from the main repo, (2) debugging entry points that work in direct Python imports but fail via pixi run or subprocess.run(), (3) code changes in a git worktree work when imported directly but fail when invoked as a console script, (4) sys.path shows main project directory before worktree path, (5) VERIFYING a console-script fix from inside a worktree where the installed entry point emits empty/unpatched output and you might wrongly conclude 'the fix does not work' — re-verify via `python -m <module>` and probe `module.__file__` / `inspect.getsource(main)`."
category: tooling
date: 2026-06-13
version: "1.2.0"
history: git-worktree-sys-path-precedence-issue.history
user-invocable: false
verification: verified-local
tags:
  - git-worktree
  - sys-path
  - PYTHONPATH
  - editable-install
  - console-scripts
  - entry-points
  - subprocess
  - pixi
  - python-environment
  - monorepo
  - module-resolution
---

# Git Worktree sys.path Precedence Issue

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Understand why console script entry points load stale code from the main project repo instead of from the current git worktree, even though editable installs and direct imports work correctly |
| **Outcome** | Two distinct failure modes identified: (1) sys.path precedence issue where the main project directory is listed BEFORE the worktree path in Python's module search order — code changes work in direct Python imports but fail when invoked via subprocess entry points; (2) pixi console script stale-binary issue where the script shebang hardcodes the main worktree's Python interpreter, so `pixi run hephaestus-*` runs stale code even though `pixi run python -c "import ..."` loads the correct worktree files. |
| **Verification** | verified-local — (1) Discovered and validated locally during Issue #724 implementation (added -V/--version flag to 44 console scripts). (2) Confirmed during Issue #1189 python-version-consistency DRY refactor: `hephaestus-check-python-version --json` returned old JSON without new `ci_checks` key even after modifying `validation/python_version.py` in the worktree. |

## When to Use

- Running console scripts via `subprocess.run()` from a git worktree and observing stale code from the main repo being executed
- Code changes work correctly when imported directly (`python3 -c 'import mymodule; mymodule.func()'`) but fail when invoked as an entry point (`subprocess.run(['mymodule-cli', '--version'])`)
- Workspace-based git monorepos using pixi and editable installs (`pip install -e .`) where worktrees share `.pixi/envs/default` with the parent checkout
- Debugging why console scripts report old function behavior, old version strings, or missing recent code additions despite the worktree containing the updated files
- Building automation tools or test suites that spawn console scripts as subprocess commands from within a git worktree
- `pixi run hephaestus-*` returns old output after you edited Python source files in a git worktree

Do NOT use this skill when:

- The issue is a full env-resolve wipe (see [`pixi-env-resolve-drops-editable-install`](pixi-env-resolve-drops-editable-install.md)) — that's a different failure mode with `ModuleNotFoundError` at the top level
- The console script itself is stale (see [`tooling-pyproject-scripts-dev-install-after-merge`](tooling-pyproject-scripts-dev-install-after-merge.md)) — if the script entry point does not exist or is outdated
- Running tests directly via `pytest` or importing directly in the REPL — those don't exhibit the issue because they run in the same Python process with the current sys.path

## Verified Workflow

### Quick Reference

```bash
# 0. Diagnose which file is actually loaded (NEW — do this first)
pixi run python -c "import hephaestus.validation.python_version as m; import inspect; print(inspect.getfile(m))"
# If the path shown is NOT in the current worktree directory, the editable install is stale.
# Example bad output: /home/mvillmow/Projects/ProjectHephaestus/hephaestus/validation/python_version.py
# Example good output: /home/mvillmow/Projects/ProjectHephaestus/build/.worktrees/issue-1189/hephaestus/validation/python_version.py

# 1. Check what sys.path subprocess sees (run from worktree)
python3 -c 'import sys; print(sys.path)'
# Expected: Should show worktree path early, but often shows main project FIRST

# 2. Verify editable install location
ls -la .pixi/envs/default/lib/python*/site-packages/ | grep _editable_impl
cat .pixi/envs/default/lib/python*/site-packages/_editable_impl_*.pth
# Output should show: /path/to/worktree

# 3. Confirm direct import works (from worktree)
pixi run python -c "import hephaestus; print(hephaestus.__version__)"
# Works — loads from worktree

# 4. Test console script that may be stale (from worktree)
pixi run hephaestus-check-python-version --json
# May return old JSON from main worktree's installed package

# 5. Reliable alternative to console scripts in worktrees: invoke via python -c
pixi run python -c "from hephaestus.validation.python_version import main; main()" -- --json
# Bypasses the console script binary shebang entirely; always loads from current editable install

# 6. Alternative solution: Prepend worktree to PYTHONPATH (explicit)
export PYTHONPATH="/path/to/worktree:$PYTHONPATH"
pixi run hephaestus-agent-stage --version

# 7. Fix for worktree with its own pixi env: refresh the editable install
pixi run dev-install
```

### Console-Script Verification Probe

**The trap**: After applying a fix inside a worktree, you run the installed console-script to verify it — and it returns empty or unpatched output. You conclude "the fix is broken." It is not broken: the installed entry point loaded the OUTER repo's copy of the module, not your worktree's copy. The console-script shebang hardcodes the main worktree's Python interpreter, so `inspect.getfile()` will reveal a path outside your worktree.

**Probe to reveal which copy is loaded:**

```python
from hephaestus.validation import repo_analyze_skills as m
import inspect
print("MODFILE:", m.__file__)          # reveals WHICH copy is loaded
print("HAS_FIX:", "args.json" in inspect.getsource(m.main))
```

If `MODFILE` shows a path in the outer/main repo (not your worktree), the console-script binary is stale regardless of your edits.

**Authoritative local verification**: use `python -m <module>` or `from <module> import main; main([...])`, NOT the installed entry point:

```bash
# Wrong (may silently load outer repo):
pixi run hephaestus-repo-analyze-skills --json

# Correct (always loads from current editable install):
pixi run python -m hephaestus.validation.repo_analyze_skills -- --json
# OR:
pixi run python -c "from hephaestus.validation.repo_analyze_skills import main; main(['--json'])"
```

### Detailed Steps

**Step 0 — Diagnose which file is actually loaded (start here).**

Before investigating sys.path ordering, confirm whether `pixi run python -c` itself loads from the right file:

```bash
# Substitute your module path as appropriate
pixi run python -c "import hephaestus.validation.python_version as m; import inspect; print(inspect.getfile(m))"
```

- If the path shown is inside the current worktree directory: direct imports are fine; the problem is the console script binary specifically (Failure Mode 2 below).
- If the path shown is the main project directory: sys.path ordering is the issue (Failure Mode 1 below).

**Step 1 — Detect the symptom.**

Create a simple test: modify a function in the worktree, then invoke the console script:

```bash
# In worktree: edit hephaestus/__init__.py to change __version__ or add a marker function
cd /path/to/worktree
echo "print('MARKER FROM WORKTREE')" >> hephaestus/__init__.py

# Via subprocess, invoke the console script
pixi run hephaestus-agent-stage --version
# Output: Old version from main repo (not the worktree modification)
# If you see the old code, the console script binary is stale
```

**Step 2 — Inspect sys.path order in subprocess context.**

```bash
# From the worktree, print the full sys.path that a subprocess sees
python3 -c 'import sys; [print(i, path) for i, path in enumerate(sys.path)]'
```

Look for:
- `/home/mvillmow/Projects/ProjectHephaestus` (main repo) — appears EARLY
- `/home/mvillmow/Projects/ProjectHephaestus/build/.worktrees/issue-724` (worktree) — appears LATER

If main repo path comes BEFORE worktree path, that's Failure Mode 1.

**Step 3 — Verify the .pth file points to the worktree.**

```bash
# Check which editable install was registered
find .pixi/envs/default/lib/python*/site-packages/ -name '_editable_impl_*.pth' -exec cat {} \;
# Output should be: /home/mvillmow/Projects/ProjectHephaestus/build/.worktrees/issue-724
#                   (the worktree path, NOT the main repo)
```

If the .pth file is correct but sys.path still has main repo first, the issue is path precedence (Failure Mode 1). If the .pth file shows the MAIN repo path, the editable install was created in the main checkout and has not been refreshed for this worktree (Failure Mode 2).

**Step 4 — Understand why this happens.**

**Failure Mode 1 — sys.path ordering:**
When `pip install -e .` runs, it creates a `.pth` file that gets prepended to the Python path. However, if you are running Python from a directory context (worktree) while the parent repo is also in sys.path (from earlier setup), Python's import system may search the parent first depending on how the module search order is constructed.

The key insight: **The editable install .pth file is correct, but the main project directory is ALSO in sys.path due to environment inheritance or explicit path configuration.**

**Failure Mode 2 — Console script shebang points to main worktree:**
The `pixi run hephaestus-*` console script binary has a shebang that was generated when `pip install -e .` was run in the MAIN worktree. The shebang hardcodes `/path/to/main-worktree/.pixi/envs/default/bin/python`. Even though `pixi run python -c "import hephaestus ..."` loads from the current worktree (via the .pth file), the console script binary's Python interpreter starts with the main worktree's environment.

Diagnosis: The `inspect.getfile()` one-liner (Step 0) shows correct worktree path for direct `python -c` but the console script returns stale output.

**Step 5 — Apply Solution 1: Use pixi run python -c (preferred for worktrees).**

When testing changes in a worktree, bypass the console script binary entirely and invoke the module's main function directly:

```bash
# Instead of: pixi run hephaestus-check-python-version --json
# Use:
pixi run python -c "from hephaestus.validation.python_version import main; main()" -- --json
```

This always loads from the current editable install without being affected by the console script shebang.

In automation Python code:

```python
import subprocess
result = subprocess.run(
    ['pixi', 'run', 'python', '-c',
     'from hephaestus.validation.python_version import main; main()', '--', '--json'],
    cwd='/path/to/worktree',
    capture_output=True,
    text=True
)
print(result.stdout)  # Loads from worktree
```

**Step 6 — Apply Solution 2: Use pixi run <script> via subprocess (preferred for automation).**

When you invoke subprocess commands through `pixi run`, you preserve the same Python environment context (same sys.path, same .pixi/envs/default). This avoids the path precedence issue entirely:

```bash
# Instead of raw subprocess.run(['console-script', '--version']),
# use pixi run in your automation:
pixi run hephaestus-agent-stage --version
```

In Python:

```python
import subprocess
result = subprocess.run(
    ['pixi', 'run', 'hephaestus-agent-stage', '--version'],
    cwd='/path/to/worktree',
    capture_output=True,
    text=True
)
print(result.stdout)  # Loads from worktree
```

**Step 7 — Apply Solution 3: Explicit PYTHONPATH (if pixi run is not available).**

If you must use raw subprocess invocation (not pixi run), prepend the worktree to PYTHONPATH:

```bash
# From worktree or parent, set PYTHONPATH explicitly
export PYTHONPATH="/home/mvillmow/Projects/ProjectHephaestus/build/.worktrees/issue-724:$PYTHONPATH"
/path/to/bin/hephaestus-agent-stage --version
# Loads from worktree
```

In Python:

```python
import os
import subprocess

worktree_path = '/home/mvillmow/Projects/ProjectHephaestus/build/.worktrees/issue-724'
env = os.environ.copy()
env['PYTHONPATH'] = f"{worktree_path}:{env.get('PYTHONPATH', '')}"

result = subprocess.run(
    ['/path/to/bin/hephaestus-agent-stage', '--version'],
    cwd=worktree_path,
    env=env,
    capture_output=True,
    text=True
)
print(result.stdout)  # Loads from worktree
```

**Step 8 — Fix: Run dev-install in the worktree (if worktree has its own pixi env).**

If the worktree has (or can have) its own pixi environment, refreshing the editable install fixes the console script shebang:

```bash
cd /path/to/worktree
pixi run dev-install
# Regenerates the console script binary with the correct shebang for this worktree
```

**Step 9 — Verify the fix.**

After applying the solution, re-run the console script and check that it now loads from the worktree:

```bash
pixi run hephaestus-agent-stage --version
# Should now show the current git SHA or modified version (proof it's loading from worktree)
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|---|---|---|
| Reinstalling the package | Ran `pip uninstall hephaestus && pip install -e .` to refresh the editable install | sys.path still showed main project before worktree; the .pth file was refreshed but the path ordering was NOT reordered | Reinstalls don't fix path ordering; the issue is sys.path search precedence, not the editable install metadata. .pth file location is correct; the parent directory is also in the search path. |
| Deleting .pyc and __pycache__ | Removed all Python bytecode cache to force a fresh import | Subprocess still loaded stale code from main repo; caching was never the issue | Root cause is sys.path ordering at the module resolution layer, not compilation artifacts. Python doesn't cache the module search path itself. |
| Running console script directly without pixi | Executed `/path/to/.pixi/envs/default/bin/hephaestus-agent-stage` as a raw subprocess | Still loaded from main repo; the issue is that the Python interpreter inside that executable was started with a sys.path that included the main repo before the worktree | The problem is not the shell invocation; it's the Python process's environment and sys.path ordering. Pixi run context preserves the environment better. |
| Setting PYTHONPATH in shell before invoking subprocess | Exported `PYTHONPATH=/path/to/worktree:$PYTHONPATH` in bash, then called subprocess | subprocess.run() did NOT inherit the shell's exported PYTHONPATH; only env passed explicitly to subprocess gets it | When using subprocess.run() in Python, env vars are NOT inherited from the parent shell unless explicitly passed via the `env=` parameter; `os.environ.copy()` is required. |
| Checking only the main .pth file | Examined `.pth` file in main repo's site-packages | Missed that the worktree was using the SAME `.pixi/envs/default` and the .pth file there was also pointing to the worktree (correctly) | Both the main repo and worktree share `.pixi/envs/default`; the .pth file is correct in both cases. The issue is NOT the .pth target but the sys.path ordering. |
| Used `pixi run hephaestus-*` console script to test worktree changes | Ran `pixi run hephaestus-check-python-version --json` after modifying `validation/python_version.py` in a worktree; expected to see new `ci_checks` key in output | Console script shebang points to the MAIN worktree's installed Python; `pixi run python -c "import hephaestus.validation.python_version as m; import inspect; print(inspect.getfile(m))"` confirmed the file loaded was from the main repo, not the worktree | Use `pixi run python -c "from hephaestus.X import main; main()"` instead of console script binaries when testing changes inside a worktree. The console script binary itself is stale even when direct imports work. |
| Trusting empty console-script run as proof fix is broken | Ran the installed console-script entry point after patching code in a worktree; observed empty/unpatched output and concluded the fix did not take effect | Empty output from the installed script is not evidence the fix failed; `module.__file__` revealed the OUTER repo was loaded — the installed entry point's shebang hardcodes the main repo's Python interpreter | Probe with `import inspect; print(m.__file__)` before concluding a fix is broken. Empty or unpatched output from a console-script means the outer copy is loaded, not that the patch is wrong. |
| `pixi run dev-install` to fix the shadowing | Ran `pixi run dev-install` in the worktree hoping it would re-point `which <console-script>` to the worktree's code and eliminate the sys.path shadowing issue | Re-points `which <console-script>` to the worktree's bin directory but does NOT fix the script-execution `sys.path[0]` shadowing; direct Python imports remain the only reliable worktree verification path | `pixi run dev-install` fixes the entry-point binary location but not the deeper `sys.path[0]` precedence issue. Always verify with `python -m <module>` or `from <module> import main; main([...])` rather than the installed script. |

## Results & Parameters

### Diagnostic Commands (Copy-Paste Ready)

```bash
# Step 0: Diagnose which file is actually loaded (do this first)
pixi run python -c "import hephaestus.validation.python_version as m; import inspect; print(inspect.getfile(m))"
# Replace 'hephaestus.validation.python_version' with the module you changed.
# If the path is NOT in the current worktree directory, the editable install is stale.

# From a git worktree, check what sys.path subprocess sees
python3 -c 'import sys; [print(i, path) for i, path in enumerate(sys.path)]'
# Output example:
#   0
#   1 /home/mvillmow/Projects/ProjectHephaestus
#   2 /home/mvillmow/Projects/ProjectHephaestus/build/.worktrees/issue-724
#   3 /path/to/.pixi/envs/default/lib/python3.14t/site-packages
#   ...
# Main repo at [1], worktree at [2] = PROBLEM

# Check which directory the editable install .pth file points to
find .pixi/envs/default/lib/python*/site-packages/ -name '_editable_impl_*.pth' -exec cat {} \;
# Output should be: /home/mvillmow/Projects/ProjectHephaestus/build/.worktrees/issue-724

# Verify that direct imports work (same worktree context)
pixi run python3 -c "import hephaestus; print(hephaestus.__version__)"
# Output: 0.9.4.dev14+g3cc2f0fb (current worktree commit SHA)

# Test subprocess invocation (shows the problem)
pixi run hephaestus-agent-stage --version
# If this shows old version (from main repo), the issue is reproduced

# Test subprocess after PYTHONPATH fix
export PYTHONPATH="/home/mvillmow/Projects/ProjectHephaestus/build/.worktrees/issue-724:$PYTHONPATH"
pixi run hephaestus-agent-stage --version
# Should now show current version (if fix works)
```

### Example: Issue #724 Reproduction

During the implementation of Issue #724 (add -V/--version flag to 44 console scripts), the following pattern emerged:

```python
# Code added to cli/__init__.py (in worktree)
def add_version_arg(parser: argparse.ArgumentParser) -> None:
    """Add -V/--version flag to a console script."""
    version_str = importlib.metadata.version('hephaestus')
    parser.add_argument('-V', '--version', action='version', version=version_str)

# Test in the same Python process:
pixi run python -c "from hephaestus.cli import add_version_arg; print('Import works')"
# Output: Import works (code from worktree loaded)

# Test via subprocess console script:
pixi run hephaestus-agent-stage --version
# Output: ModuleNotFoundError: No module named 'cli' (stale code from main repo)
# OR: 0.9.3 (old version from main repo, not 0.9.4.devN+worktree-sha)
```

The fix applied: All console-script invocations in automation were changed from raw `subprocess.run()` to `pixi run <script>` to preserve the environment context.

### Example: Issue #1189 Reproduction

During the implementation of Issue #1189 (python-version-consistency DRY refactor), after editing `validation/python_version.py` to add a `ci_checks` key to the JSON output:

```bash
# In the worktree, ran the console script:
pixi run hephaestus-check-python-version --json
# Output: old JSON without 'ci_checks' key — stale code from main worktree

# Diagnosed with inspect.getfile():
pixi run python -c "import hephaestus.validation.python_version as m; import inspect; print(inspect.getfile(m))"
# Output: /home/mvillmow/Projects/ProjectHephaestus/hephaestus/validation/python_version.py
# (main worktree path — NOT the issue-1189 worktree)

# Workaround: invoke via python -c instead of console script:
pixi run python -c "from hephaestus.validation.python_version import main; main()" -- --json
# Output: new JSON with 'ci_checks' key — correct worktree code loaded
```

### sys.path Inspection Pattern

To diagnose in any Python subprocess context:

```python
import subprocess
import sys

# What does THIS process see?
print("=== Direct import (current process) ===")
print(sys.path[:3])

# What does a subprocess see?
result = subprocess.run(
    ['python3', '-c', 'import sys; print(sys.path[:3])'],
    capture_output=True,
    text=True
)
print("=== Subprocess invocation ===")
print(result.stdout)

# What does pixi run see?
result = subprocess.run(
    ['pixi', 'run', 'python3', '-c', 'import sys; print(sys.path[:3])'],
    capture_output=True,
    text=True
)
print("=== pixi run invocation ===")
print(result.stdout)
```

### Decision Tree: When to Use Which Solution

```
Does your code run subprocess commands from a git worktree?
├─ YES
│  ├─ Is the command a console script (entry point)?
│  │  ├─ YES
│  │  │  ├─ Are you testing changes and need the worktree's code?
│  │  │  │  ├─ YES → Use pixi run python -c "from hephaestus.X import main; main()"
│  │  │  │  │         (bypasses stale console script shebang entirely)
│  │  │  │  └─ NO (production automation, not testing)
│  │  │  │     ├─ Can you use `pixi run <script>` (in same directory context)?
│  │  │  │     │  ├─ YES → Solution 2: Use pixi run (PREFERRED for automation)
│  │  │  │     │  └─ NO → Solution 3: Export PYTHONPATH explicitly
│  │  │  │     └─ Does the worktree have its own pixi env?
│  │  │  │        ├─ YES → Run pixi run dev-install to regenerate console script binary
│  │  │  │        └─ NO → Accept limitation, test via python -c
│  │  │  └─ Is the script defined in [project.scripts]?
│  │  │     ├─ YES → Same issue applies
│  │  │     └─ NO → Check if it's a shell wrapper or compiled binary
│  │  └─ NO (raw Python invocation)
│  │     └─ Direct import in subprocess context — apply Solution 3 (PYTHONPATH)
│  └─ NO → Not affected by this issue
└─ NO → Not affected by this issue
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Issue #724: Add -V/--version flag to 44 console scripts | 2026-06-06 — Discovered during implementation that `pixi run hephaestus-agent-stage --version` loaded stale code from main repo in a git worktree. Direct imports worked correctly. Root cause: sys.path ordering with main repo before worktree. Solution: Use `pixi run` for all subprocess invocations of console scripts. Verified locally (pixi run works, direct subprocess fails). CI not examined in detail. |
| ProjectHephaestus | Issue #1189: python-version-consistency DRY refactor | 2026-06-13 — Discovered that `pixi run hephaestus-check-python-version --json` returned old JSON without the new `ci_checks` key even after modifying `validation/python_version.py` in the worktree. Diagnosed with `inspect.getfile()` — file path pointed to main worktree. Workaround: `pixi run python -c "from hephaestus.validation.python_version import main; main()" -- --json`. |
| ProjectHephaestus | Issue #1217: console-script verification trap (closed PR #2381) | 2026-06-12 — Observed that running the installed console-script after patching `hephaestus.validation.repo_analyze_skills` inside a worktree emitted empty/unpatched output. `module.__file__` confirmed the outer repo was loaded. Authoritative verification via `python -m hephaestus.validation.repo_analyze_skills` showed the fix was correct all along. `pixi run dev-install` re-pointed the binary but did not resolve `sys.path[0]` shadowing. |

## References

- [`pixi-env-resolve-drops-editable-install`](pixi-env-resolve-drops-editable-install.md) — Related but different: full env wipe after `pyproject.toml` edits, not path ordering
- [`tooling-pyproject-scripts-dev-install-after-merge`](tooling-pyproject-scripts-dev-install-after-merge.md) — Related but different: stale console-script entry points after branch merge, not path ordering
- [`git-worktree-parallel-execution-lifecycle`](git-worktree-parallel-execution-lifecycle.md) — Comprehensive worktree lifecycle guide
- [Python sys.path initialization](https://docs.python.org/3/library/sys.html#sys.path) — Official Python documentation
- [pip editable installs (.pth files)](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs) — How .pth files are created and used
