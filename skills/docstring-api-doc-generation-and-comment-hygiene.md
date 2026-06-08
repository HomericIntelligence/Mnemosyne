---
name: docstring-api-doc-generation-and-comment-hygiene
description: "Use when: (1) updating, fixing, or extending docstrings and API documentation in source files to match current implementation semantics — changed signatures, memory semantics, orphaned fragments, undocumented methods; (2) creating API reference documentation from docstrings for a public module interface; (3) generating docstrings for undocumented functions and classes; (4) auditing and cleaning up inline NOTE/TODO/FIXME/placeholder comments — normalization, removal of shipped-feature placeholders, magic-number extraction; (5) using a package's public __version__ attribute in demo/example scripts rather than hardcoded strings, so version references stay in sync with releases."
category: documentation
date: 2026-06-07
version: "1.0.0"
user-invocable: false
history: docstring-api-doc-generation-and-comment-hygiene.history
tags:
  - docstring
  - api-docs
  - docstring-generation
  - comment-hygiene
  - note-cleanup
  - comment-normalization
  - placeholder
  - todo
  - copy-vs-view
  - module-docstring
  - error-handling-contract
  - POLA
  - version-management
  - demo-scripts
  - mojo
  - python
---

## Overview

| Attribute | Value |
| ----------- | ------- |
| **Skill Name** | docstring-api-doc-generation-and-comment-hygiene |
| **Category** | documentation |
| **Languages** | Mojo, Python, Markdown |
| **PR Type** | docs-only (no functional change) |
| **Risk** | Very low — docstring/comment prose only |
| **Verification** | verified-ci |

This skill consolidates the full lifecycle of source-level documentation hygiene:
authoring and updating docstrings, generating API reference docs from those docstrings,
cleaning up inline NOTE/TODO/FIXME/placeholder comments, and keeping version references in
demo scripts dynamic. All changes are docs-only and carry near-zero functional risk.

## When to Use

1. A function signature changed and the module docstring example still shows the old call
   (omits a required argument, references a removed helper, etc.)
2. Memory semantics (copy vs view, `_is_view` flag) are mislabeled in docstrings or
   inconsistent across sibling methods (`slice()`, `__getitem__(Slice)`, `__getitem__(*slices)`)
3. Inline `# NOTE` or `# Note:` comments in `__init__` files need to be promoted to proper
   module docstring `Note:` sections
4. A utility function (subprocess wrapper, file I/O helper) has an undocumented error-handling
   contract — it silently swallows exceptions and returns a special value (e.g., `(False, "")`)
   instead of raising, violating the Principle of Least Astonishment (POLA)
5. Module docstrings have orphaned lowercase continuation fragments, or a new trait-implementing
   dunder method (`__hash__`, `__eq__`) is undocumented
6. You need to create API reference documentation (HTML/Markdown) from docstrings for a public
   module interface
7. Undocumented functions and classes need docstrings written in a standard format (Google,
   NumPy, reStructuredText)
8. A cleanup issue targets `# NOTE:`/`# TODO:`/`# FIXME:`/placeholder markers for normalization,
   removal, magic-number extraction, or issue-reference tracing
9. Runtime `print("NOTE: ...")` statements confuse users into thinking something is broken
10. A demo/example script contains a hardcoded version string that should be the package's
    public `__version__` so example code stays in sync with releases

## Verified Workflow

### Quick Reference

| Step | Action | Tool |
| ------ | -------- | ------ |
| 1 | Read the issue and locate target files | `gh issue view`, `Glob`, `Grep` |
| 2 | Read ALL sibling methods / related files before writing | `Read`, `Grep -C 10` |
| 3 | Classify the change type (docstring update / API gen / comment cleanup / version) | — |
| 4 | Apply targeted `Edit` with unique `old_string` anchors | `Edit` |
| 5 | Verify (`py_compile`, script smoke-run, or grep audit) | `Bash` |
| 6 | Run pre-commit; stage only modified files | `Bash` |
| 7 | Commit with `docs(scope):` / `cleanup(scope):` prefix, push, open PR, auto-merge | `Bash`, `gh` |

| Cleanup Scenario | Detection Pattern | Action |
| -------- | ----------------- | ------ |
| Runtime NOTE print | `print.*NOTE\|print.*Note:` in examples/ | Reword to plain factual text; remove prefix |
| Mixed casing | `# Note:` in shared/ files | Normalize to `# NOTE:` |
| Unlinked workaround NOTE | `# NOTE:` without `#[0-9]{4,}` | Add `(#NNNN)` to marker |
| Inverted canonical order | `# NOTE (Mojo vX.Y, #NNNN):` | Swap to `# NOTE(#NNNN, Mojo vX.Y):` |
| TODO-style NOTE | future-tense prose ("could be added") | Convert to `# TODO:` |
| Magic-number NOTE | `# NOTE: epsilon=` | Extract to named module-level constant |
| Shipped-feature placeholder | `aliases to.*until.*supports` | Verify shipped, then remove stale comment |
| No-op placeholder test | `pass  # Placeholder`, zero assertions | Remove function and its `main()` call |
| Generator TODO in template string | `# TODO:` inside Python string literal | Replace with `# TEMPLATE:` |

### Detailed Steps

#### A. Generating docstrings for undocumented code

1. **Analyze the function**: understand purpose, parameters, and return value before writing.
2. **Choose a format** (Google recommended; NumPy or reStructuredText also acceptable). Be
   consistent across the module.
3. Write a one-line summary, then `Args:`, `Returns:`, `Raises:`, and an `Example:` block.

```python
# Google-style docstring format
def matrix_multiply(a: ExTensor, b: ExTensor) -> ExTensor:
    """Multiply two matrices using optimized Mojo kernels.

    Args:
        a: First matrix (shape: m x n)
        b: Second matrix (shape: n x k)

    Returns:
        Product matrix (shape: m x k)

    Raises:
        ValueError: If matrix dimensions don't align for multiplication

    Example:
        ```mojo
        >>> a = ExTensor([[1, 2], [3, 4]], DType.float32)
        >>> b = ExTensor([[1, 0], [0, 1]], DType.float32)
        >>> c = matrix_multiply(a, b)
        ```
    """
    ...
```

#### B. Generating API reference documentation from docstrings

1. **Ensure docstrings**: verify all public functions/classes have docstrings.
2. **Validate format**: confirm a consistent docstring style (Google, NumPy, or reST).
3. **Extract metadata**: parse signatures, parameter types, return types.
4. **Generate**: produce HTML or Markdown API reference.
5. **Validate output**: verify links work and examples are correct.

```bash
# Python with pdoc
pdoc --html module_name -o docs/

# Python with Sphinx
sphinx-quickstart docs/
make -C docs html

# Quick docstring extraction
python3 -c "import module; help(module.function)"
```

API doc output should include: module overview, signatures with type hints, parameter docs
(type/description/default), return docs, raises/exceptions, code examples, and cross-references.

#### C. Updating docstrings to match current implementation

**Stale example after signature change:** grep the current signature
(`grep "fn function_name" path -C 5`), verify every required parameter (no default) is passed,
then edit the docstring example to show all required imports and arguments.

**Copy vs view semantics:** run `grep -n "fn slice\|fn __getitem__\|_is_view" <file>`, read ALL
sibling methods together, classify each (true view / copy-with-view-flag / independent copy),
and update only the docstring. Use precise language ("zero-copy view", "pointer offset",
"independent copy"). For struct-level docs, insert a Memory Semantics ASCII table between
`Attributes:` and `Examples:` (Mojo-parser safe). Scalar overloads need an explicit N/A note.

**Promoting inline NOTE to docstring Note:** grep `# NOTE` in `__init__` files, read each fully
to check whether a `Note:` section already exists, then add/expand. Preferred section order:
`Modules:` → `Note:` → `Example:` (place `Note:` BEFORE `Example:`).

**Silent error-handling contracts (POLA):** when a utility function swallows exceptions and
returns a special value, add an explicit `Note:` section **immediately after the summary,
before `Args:`** documenting both the success shape and every failure shape.

```python
def run_command(cmd: str, timeout: int = 60) -> tuple[bool, str]:
    """Run a command and return stdout if successful.

    Note:
        This function has a silent error-handling contract:
        - On success (exit code 0): returns `(True, <stdout>)`
        - On non-zero exit / timeout / OSError: returns `(False, "")` — empty
          string, NOT stderr; no exception raised.
        All exceptions (TimeoutError, CalledProcessError, OSError) are swallowed.
        Use :func:`get_command_path` to verify availability first if early
        failure is preferred over a silent `(False, "")`.

    Args:
        cmd: Shell command to execute (must exist in PATH)
        timeout: Execution timeout in seconds (default 60)

    Returns:
        Tuple `(success, output)`:
        - `(True, stdout)` when exit code == 0
        - `(False, "")` when exit code != 0, timeout, or OSError
    """
```

After editing, confirm existing tests exercise the documented contract (e.g.,
`test_run_command_timeout()` asserts the `(False, "")` shape).

**Module docstring line-wrap audit:** an orphaned fragment is a line inside a module-level
docstring that starts with a lowercase coordinating conjunction and does not grammatically
continue the prior line. Delete those; keep legitimate sentence wraps.

```bash
grep -rn '^[a-z]' <package>/**/__init__.py <package>/**/runner.py
```

**Placeholder docstrings:** verify test/implementation exists, then replace
"Placeholder…require implementation" with "implemented and passing".

**Dunder / trait method docs:** grep with `-C 10`, update the method docstring (trait name,
algorithm note, expanded `Example:`), and update the package listing entry (append
`(ExTensor, implements Hashable via __hash__)`). Do NOT add dunders to the import list — they
are trait implementations, not importable symbols.

#### D. Inline comment / NOTE cleanup

1. **Discovery** — always grep before editing (issue plans go stale):

```bash
grep -rn "# NOTE" <scope>/ --include="*.mojo"
grep -rn 'print.*NOTE\|print.*TODO\|print.*FIXME\|print.*Note:' examples/ --include="*.mojo" -i
grep -rn "# NOTE:" --include="*.mojo" . | grep -v "#[0-9]\{4,\}"   # untracked workarounds
grep -rn "aliases to.*until\|Will use.*when available" . --include="*.mojo"  # shipped-feature
grep -rn "# TODO:" scripts/generators/ --include="*.py"            # generator template TODOs
```

2. **Categorize** each marker in context (decision tree): runtime print → plain status text;
   magic-number used 2+ places → named module constant; docstring NOTE → strip prefix to prose;
   shipped-feature placeholder → confirm landed then remove; no-op placeholder test → remove;
   generator TODO in template string → `# TEMPLATE:`; bare workaround NOTE → add `(#NNNN)`;
   non-canonical format → normalize to `# NOTE(#NNNN, Mojo vX.Y):`.

   **Always keep**: FP16/SIMD compiler-limitation notes, epsilon/tolerance justifications with
   issue refs, active Track/Phase blocker notes, Mojo language-limitation notes (`no __all__`).

3. **Apply edits** with `Edit` (`replace_all: false` for unique strings). Examples:

```mojo
# Normalize casing
old: # Note: This comment explains the workaround.
new: # NOTE: This comment explains the workaround.

# Convert runtime NOTE print to plain status
old: print("Note: Training requires batch_norm2d_backward implementation.")
new: print("Training requires batch_norm2d_backward (see GAP_ANALYSIS.md).")

# Extract magic-number NOTE to module-level constant
old: # NOTE: epsilon=3e-4 for float32 prevents precision loss in matmul (see #2704)
     var epsilon = 3e-4 if dtype == DType.float32 else 1e-3
new: alias GRADIENT_CHECK_EPSILON_FLOAT32: Float64 = 3e-4  # see #2704
     var epsilon = GRADIENT_CHECK_EPSILON_FLOAT32 if dtype == DType.float32 else 1e-3
```

4. **Verify** — re-run the discovery greps and confirm zero remaining hits for the targeted
   categories.

#### E. Dynamic version from package attribute in demo scripts

Demo/example scripts should consume the version the same way users should — by importing the
package's public `__version__`, not hardcoding a string or calling `importlib.metadata` directly.

```python
#!/usr/bin/env python3
"""Demo script showing how to use the package."""

from mypackage import __version__   # replaces: VERSION = "0.7.1"

print(f"Using mypackage version {__version__}")
```

Steps: (1) find demo scripts (`find scripts/ -name "*example*" -o -name "*demo*"`); (2) confirm
the package `__init__.py` exports `__version__` (typically
`__version__ = importlib.metadata.version("<dist>")`); (3) replace the hardcoded string with the
import; (4) smoke-run `python3 scripts/example_usage.py` to verify the real version prints. For a
one-line literal swap with no test suite, smoke-run verification is sufficient — no unit test
needed.

### Commit and PR Conventions

```bash
# docstring/doc updates
git commit -m "docs(scope): <what was documented>

<One sentence: why — what implicit behaviour is now explicit.>

Closes #<issue>"

# comment cleanup
git commit -m "cleanup(scope): normalize inline NOTE/TODO/placeholder comments

<markers linked, casing normalized, stale removed, etc.>

Closes #<issue>"

gh pr create --title "docs(scope): ..." --body "Closes #<issue>"
gh pr merge --auto --rebase <pr-number>
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Guessing signatures from memory | Wrote a function signature/docstring example without reading source | Line numbers and parameter names were wrong | Always read the actual source — grep for the signature, then Read the docstring |
| Copying old docstring example verbatim | Kept stale example after a signature change | Did not demonstrate the new required argument | Grep the actual signature; check every parameter with no default value |
| Treating all slice methods as identical | Assumed `__getitem__(Slice)` was a view like `slice()` | The 1D `__getitem__(Slice)` always copies | Read ALL sibling implementations before writing docstrings |
| Fixing implementation instead of docstring | Considered changing `__getitem__(*slices)` to a pointer offset | Multi-dim slices are non-contiguous; needs stride metadata | Decide whether the bug is in the docs or the code first |
| Adding `Note:` after `Example:` | Placed `Note:` section after the `Example:` block | Wrong order for module docstrings | Place `Note:` before `Example:` |
| Expanding `Note:` without reading first | Started editing an `__init__` that already had a `Note:` | Would have created a duplicate | Read the full file before adding/expanding a section |
| Documenting only the success return | Wrote `Returns: (bool, str)` without the failure shape | Callers unsure what `(False, "")` means | Document BOTH success `(True, stdout)` AND every failure `(False, "")` shape |
| Placing the error contract in a trailing Note: | Put the swallow-exception contract at the end of the docstring | Callers read `Returns:` first and miss it; POLA still violated | Place `Note:` immediately after the summary, before `Args:` |
| Trying to add `__hash__` to the import list | Considered re-exporting a dunder as a symbol | Dunders are trait implementations, not importable | Document dunders via docstrings/comments, not import lists |
| Trusting issue-plan line numbers | Edited at the plan's line numbers directly | Files were partially fixed; numbers had shifted | Always grep to discover the actual state — plans go stale |
| Case-sensitive grep only | Used `print.*NOTE` without `-i` | Missed mixed-case `Note:` variants | Use case-insensitive grep or include all case variants |
| Linking all NOTEs | Added issue refs to informational NOTEs too | Created unnecessary issue noise | Only link NOTEs describing temporary workarounds or blocked features |
| Creating new issues without searching | Opened a tracking issue per group immediately | Would have duplicated existing cleanup issues | `gh issue list --search` before creating |
| Editing main-repo file from a worktree session | Edited `/repo/...` instead of the worktree copy | File is tracked by `main`, not the feature branch | Always edit the worktree path |
| Use `importlib.metadata.version()` directly in demo | `print(version("MyPackage"))` in the demo | Teaches users to bypass the package's public interface | Demo code should import the package and use `__version__` |
| Keep hardcoded version, bump manually | `VERSION = "0.7.1"` updated each release PR | Doesn't scale; demo lags real version; teaches hardcoding | Never hardcode versions in demos; use `__version__` |
| Replace version with literal `"__version__"` placeholder | `VERSION = "__version__"` | Output shows the literal string, not a number | Replace with the actual imported `__version__` attribute |
| Using `just pre-commit-all` | Ran `just` for pre-commit | `just` not on PATH | Use `pixi run pre-commit run --all-files` |
| Running markdownlint via `pixi run npx` | `pixi run npx markdownlint-cli2 ...` | `npx: command not found` | Rely on pre-commit hooks instead |
| Staging with `git add -A` | Added all untracked files | Picked up `__pycache__/` | Stage specific files for docs-only changes |
| API doc / docstring gen treated as a one-shot | Assumed the direct approach always works | For greenfield docstrings the direct approach IS straightforward; the risk is skipping the read-first step | The pattern is simple, but still read existing code/docstrings before generating |

## Results & Parameters

### Key Docstring Patterns

**Copy-returning vs view-returning slice methods:**

```mojo
fn __getitem__(self, slice: Slice) raises -> Self:
    """Get slice of 1D tensor [start:end].

    Returns:
        New tensor containing a **copy** of the sliced data (`_is_view = False`).
    Notes:
        Always copies regardless of step. For zero-copy extraction use `slice()`.
    """

fn slice(self, start: Int, end: Int, axis: Int = 0) raises -> ExTensor:
    """Extract a slice along the specified axis.

    Returns:
        A new tensor **view** sharing memory with the original (`_is_view = True`).
    Notes:
        Data pointer is offset into the original buffer; refcount incremented.
    """
```

**Memory Semantics table (ASCII, Mojo-safe):**

```text
Memory Semantics:
    +----------------------------+----------+---------------------+---------------------------+
    | Method                     | Returns  | _is_view            | Memory                    |
    +----------------------------+----------+---------------------+---------------------------+
    | slice(start, end, axis)    | ExTensor | True  (view)        | Shared — zero-copy        |
    | __getitem__(Slice)         | ExTensor | False (copy)        | Independent — data copied |
    | __getitem__(*slices)       | ExTensor | False (copy)        | Independent — data copied |
    | __getitem__(Int)           | Float32  | N/A (scalar result) | Scalar value, not tensor  |
    +----------------------------+----------+---------------------+---------------------------+
```

**`__init__.mojo` re-export Note: template:**

```mojo
Note:
    Mojo v0.26.1+ automatically exports all imported symbols to package consumers.
    No ``__all__`` equivalent is needed. Callers may import directly from the parent:

    ```mojo
    from <package> import <Symbol1>, <Symbol2>
    ```
```

**Placeholder update pattern:**

```text
# BEFORE: Placeholder import tests in tests/.../test_imports.mojo require implementation.
# AFTER:  Import tests in tests/.../test_imports.mojo are implemented and passing.
```

### Canonical NOTE Format Reference (Mojo)

```mojo
# Plain limitation (no issue ref):
# NOTE (Mojo v0.26.1): <description>

# Limitation with issue reference (issue number FIRST):
# NOTE(#NNNN, Mojo v0.26.1): <description>
# Track resolution via #<parent>. Implement when <condition>.

# Wrong (fix by swapping):  # NOTE (Mojo v0.26.1, #3076): ...
# Wrong (append version):   # NOTE(#3076): ...
# Wrong (TODO disguised):   # NOTE: X could be added  →  # TODO: Add X if needed
```

### Gradient-Check / Tolerance Constants (cleanup reference)

| Constant | Value | Use Case |
| -------- | ----- | -------- |
| `GRADIENT_CHECK_EPSILON_FLOAT32` | `3e-4` | float32 matmul-heavy layers (conv2d, linear) |
| `GRADIENT_CHECK_EPSILON_OTHER` | `1e-3` | Non-float32 dtypes (BF16, FP16) |

| Layer | Tolerance | Rationale |
| ----- | --------- | --------- |
| Conv2d / BatchNorm backward | `1e-1` (10%) | Accumulated matmul / normalization errors |
| Linear backward | `0.10` wide + `0.01` abs | Matrix-op accumulated errors (#2704) |
| Activation backward | `1e-2` float32, `1e-1` other | Elementwise, less accumulation |

### Dynamic Version Pattern

| Aspect | Details |
| ------ | ------- |
| Import | `from <package> import __version__` at top of demo script |
| Definition | `__init__.py` sets `__version__ = importlib.metadata.version("<dist>")` |
| Synchronization | Automatic — reflects each released git tag |
| Verification | Smoke-run the script; expect the actual installed version printed |

### Validation Commands

```bash
python3 -m py_compile scripts/<script>.py            # Python syntax
python3 scripts/example_usage.py                     # demo smoke-run
SKIP=mojo-format pixi run pre-commit run --files <f> # Mojo (skip mojo-format if GLIBC < 2.34)
pixi run pre-commit run --all-files                  # full pre-commit
grep -rn '^[a-z]' <package>/**/__init__.py           # orphaned-fragment audit
```

`mojo-format` may be skipped locally on hosts with GLIBC < 2.34; it passes in CI Docker. All
other hooks (ruff, markdownlint, trailing-whitespace, end-of-file-fixer, check-yaml) must pass.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | Copy/view, catalog, fp16, re-export docstring updates | see history |
| ProjectScylla | Issue #1364, PR #1397 (module docstring line-wrap audit) | see history |
| ProjectHephaestus | Issue #797 (run_command POLA contract); Issue #787 (demo `__version__`) | see history |
| Multiple repos | NOTE/TODO/FIXME inline-comment cleanup passes | see history |
