---
name: ruff-specific-rule-fixes
description: "Fix concrete Ruff violations and systemic lint-policy gaps. Use for S101 guards, C901 extraction, Ruff/isort autofixes, D413 docstrings, formatter-only failures, stale ignores after tool upgrades, or repeated violations that reveal a missing enforcement rule."
category: tooling
date: 2026-06-30
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
history: ruff-specific-rule-fixes.history
tags:
  - ruff
  - lint
  - formatting
  - S101
  - C901
  - RUF022
  - I001
  - RUF100
  - D413
  - E501
  - mypy
---

# Ruff-Specific Rule Fixes

## Overview

Reproduce the exact rule, choose a semantic fix before suppression, let Ruff perform its own safe
sorting and formatting, and run every CI lint surface—including tests and format checks. If the
same policy violation appears independently more than once, repair the enforcement boundary as
well as the instances.

Case provenance and detailed outcomes are in
[ruff-specific-rule-fixes.notes.md](ruff-specific-rule-fixes.notes.md). The complete superseded
content is in [ruff-specific-rule-fixes.history](ruff-specific-rule-fixes.history).

## When to Use

- `S101` flags a production assertion used as a runtime guard.
- `C901` flags a function whose branches represent separable responsibilities.
- `RUF022` or `I001` reports sorting that should be handled by Ruff/isort.
- `RUF100` reports an unused `noqa`, often because the cited rule is not selected.
- `D413` reports no blank line after the last Google-style docstring section.
- `E501`, `ruff format --check`, or mypy `unused-ignore` appears after a tool-floor bump.
- Added tests pass but CI fails because tests were omitted from local lint/format targets.
- The same policy defect appears in two or more independent files or configurations.

## Verified Workflow

### 1. Reproduce the repository gate

Read `pyproject.toml`, pre-commit configuration, and CI commands before choosing a fix. Then run
the narrow rule and both Ruff phases on every changed Python file:

```bash
ruff check --select S101,C901,RUF022,I001,RUF100,D413,E501 path/to/file.py
ruff check path/to/source.py path/to/test_file.py
ruff format --check path/to/source.py path/to/test_file.py
```

`ruff check` and `ruff format --check` are independent gates. Passing tests or one Ruff command
does not imply the other passes.

### 2. Apply the rule-specific repair

#### S101: replace production assertions with explicit failure

Assertions disappear under `python -O`; do not use them for runtime invariants.

```python
# Before
assert worker is not None, "worker required"

# After
if worker is None:
    raise RuntimeError("worker required")
```

Preserve exception type/message conventions and add tests for the failure path. Test assertions
remain appropriate unless repository policy says otherwise.

#### C901: extract cohesive decisions

Move independent parse, validation, rendering, or restoration steps to named helpers. Keep return
values and exception timing stable, then rerun focused tests and the complexity check:

```bash
ruff check --select C901 path/to/module.py
```

Do not merely move branches into one equally complex helper or add `# noqa: C901` without a
documented reason.

#### RUF022 and I001: use the autofixer

```bash
ruff check --select RUF022,I001 --fix path/to/module.py
ruff check --select RUF022,I001 path/to/module.py
```

Do not manually sort `__all__` or imports. Isort ordering may use an alias name rather than the
original symbol, so an intuitive manual order can still be wrong.

#### RUF100: remove dead suppression or select the intended rule

Inspect the active rule set:

```bash
ruff check --show-settings path/to/script.py
ruff check --select RUF100 path/to/script.py
```

If static argument construction is safe and no selected rule fires, remove the `noqa`. If the
policy truly requires the suppressed rule, enable that exact rule centrally and fix all newly
exposed violations. Avoid enabling broad families without reviewing their effect.

For new executable scripts, also run the repository's auto-discovered `--help`/version smoke
contract; lint success does not prove CLI construction is valid.

#### D413: add a blank line after the final docstring section

```python
def load(path: str) -> str:
    """Load text.

    Args:
        path: Input path.

    Returns:
        Loaded text.

    """
```

`ruff format` neither reports nor repairs this pydocstyle rule. Use:

```bash
ruff check --select D413 --fix path/to/module.py
```

#### E501 and formatter disagreements

For a long literal, extract a named constant or split data without changing bytes. For a construct
that Ruff intentionally collapses, accept the formatter's layout if it satisfies line length.
Never fight the formatter with hand wrapping that it immediately undoes.

Verify content-sensitive rewrites explicitly:

```python
assert rewritten_value == original_value
```

#### Stale type ignores after upgrades

An `unused-ignore` is evidence that inference changed. Remove the stale comment and add the correct
generic annotation if needed:

```python
completed: subprocess.CompletedProcess[str] = subprocess.run(
    argv, text=True, capture_output=True, check=False
)
```

Do not disable unused-ignore checks globally.

### 3. Decide whether the linter is the root cause

If the same policy defect occurs in at least two independent artifacts:

1. Identify the single validator or lint rule that should own the invariant.
2. Add or enable the narrow rule at error level.
3. Fix all violations discovered by the new rule.
4. Add behavior coverage for custom validators, not prose-pinning tests.
5. Run the same entry point CI uses.

One isolated violation usually needs a local fix. Recurrence across authors or directories signals
an enforcement gap.

### 4. Verify all changed surfaces

```bash
ruff check path/to/source.py path/to/test_file.py
ruff format --check path/to/source.py path/to/test_file.py
mypy path/to/package
pytest -q path/to/relevant_tests.py
pre-commit run --files path/to/source.py path/to/test_file.py
```

Also run the repository's complete required check when the PR changes configuration, tool floors,
or many files. Newly added tests are first-class lint inputs.

## Decision Rules

- Fix semantics before suppressing a rule.
- Use Ruff autofix for Ruff/isort-owned ordering and D413.
- A formatter check is separate from a lint check.
- Validate production and test files together.
- A tool-floor bump requires a repository-wide discovery pass.
- A repeated policy failure belongs in centralized enforcement.
- A `noqa` is valid only if the cited rule is selected and the suppression is narrowly justified.
- Preserve exact string bytes when repairing implicit concatenation or line wrapping.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Replace `assert` with another assertion form | Still disappears under optimization | Raise an explicit domain-appropriate exception |
| 2 | Add `# noqa: C901` immediately | Hides separable responsibilities and future growth | Extract cohesive helpers and retest behavior |
| 3 | Manually reorder `__all__` | Alias-aware isort order can differ | Run `ruff check --fix` |
| 4 | Run pytest and `ruff check` only | Formatter-only failures survive | Run `ruff format --check` too |
| 5 | Lint production but omit new tests | CI applies the same policy to tests | Pass every changed Python file |
| 6 | Keep a stale `type: ignore` | Strict unused-ignore mode rejects it | Remove it and correct the type |
| 7 | Add a `noqa` for an unselected rule | RUF100 reports the dead directive | Remove it or enable the exact rule centrally |
| 8 | Re-fix the same policy in many files | Recurrence continues | Repair the linter/validator boundary |

## Results & Parameters

- Run both `ruff check` and `ruff format --check` on every changed Python file.
- Prefer `ruff check --fix` for RUF022, I001, and D413.
- Treat recurrence in two or more independent artifacts as an enforcement-gap signal.
- Preserve exact runtime strings when formatting or concatenation changes.
- Keep per-case evidence levels from the notes index; do not infer CI status from a local fix.

The source C901 cases used a maximum complexity of 10. Treat that as repository policy, not a
universal constant, and keep custom complexity hooks aligned with Ruff's configured threshold.

For the recorded script-smoke case, only specific security rules were selected—not the broad `S`
family—and test functions still required D103 docstrings. Inspect the live select and per-file-ignore
sets before adding a suppression. Its auto-discovered help contract required exit status zero and
non-empty combined output for each `scripts/*.py` entry point.

## Verification Status

The patterns aggregate CI-verified S101, C901, sorting, policy-gate, test-format, and formatter-only
repairs. The D413 case is verified locally rather than in CI. Preserve that narrower boundary when
citing it; see the notes case index for links and individual status.
