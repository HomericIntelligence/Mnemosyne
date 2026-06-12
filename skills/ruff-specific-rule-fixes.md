---
name: ruff-specific-rule-fixes
description: "Patterns for fixing specific Ruff lint rule violations and addressing systemic linter policy failures. Use when: (1) fixing Ruff S101 violations in production code by replacing bare assert guards with explicit RuntimeError raises, (2) fixing Ruff C901 cyclomatic complexity violations by extracting helper functions, (3) fixing Ruff RUF022 (__all__ not sorted) or I001 (import block un-sorted) — both are [*]-fixable; never manually reorder because isort uses the alias name not the original symbol, always use `ruff check --fix`, (4) the same policy violation reappears in two or more independent documents or configs — indicating the linter/validator that should enforce the policy is absent or misconfigured (root-cause fix: add the lint rule, not re-fix every instance), (5) deciding between adding a noqa suppression, fixing the violation, or promoting the rule to error-level enforcement."
category: tooling
date: 2026-06-13
version: "1.2.0"
user-invocable: false
history: ruff-specific-rule-fixes.history
tags:
  - ruff
  - lint
  - S101
  - C901
  - assert
  - runtimeerror
  - cyclomatic-complexity
  - method-extraction
  - noqa
  - linter
  - policy-enforcement
  - root-cause
  - pre-commit
  - RUF022
  - I001
  - __all__
  - import-sort
  - isort
  - autofix
---

# Ruff Specific Rule Fixes

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-13 |
| **Objective** | Fix specific Ruff rule violations (S101 assert-in-production, C901 cyclomatic complexity, RUF022 `__all__`-sort, I001 import-sort) and recognize when repeated policy violations mean the linter itself is the root cause |
| **Outcome** | Verified — S101 guards converted across 20+ sites (PRs #1142, #1211), C901 extractions verified (PRs #1546, #1050), wrong-direction linter root-cause pattern verified-CI (PRs #863/#865/#866/#867) |
| **Verification** | verified-ci |

## When to Use

- Ruff reports **S101** (`use of assert`) in production code — `assert x is not None  # noqa: S101` precondition guards that must always run (Python's `-O` flag disables `assert`).
- Ruff or a custom hook reports **C901** (`<function> is too complex (N > 10)`) — adding conditional blocks pushed a function over the cyclomatic-complexity limit.
- Ruff reports **RUF022** (`__all__` is not sorted) or **I001** (import block is un-sorted) — both are marked `[*]` fixable by ruff itself.
- The **same policy violation** appears in 2+ independent files/configs — the linter that should enforce the policy is absent, misconfigured, or wrong-direction.
- You are deciding between a `# noqa` suppression, fixing the violation, or promoting the rule to error-level enforcement.
- You are tempted to open N parallel PRs to fix N violating files — pause and check the linter first.
description: "Patterns for fixing specific Ruff lint rule violations and addressing systemic linter policy failures. Use when: (1) fixing Ruff S101 violations in production code by replacing bare assert guards with explicit RuntimeError raises, (2) fixing Ruff C901 cyclomatic complexity violations by extracting helper functions, (3) the same policy violation reappears in two or more independent documents or configs — indicating the linter/validator that should enforce the policy is absent or misconfigured (root-cause fix: add the lint rule, not re-fix every instance), (4) deciding between adding a noqa suppression, fixing the violation, or promoting the rule to error-level enforcement, (5) a large multi-file feature PR passes functionally but fails CI on Ruff E501 line-length (>100 chars) or ruff format in NEWLY-ADDED test files — run ruff check AND ruff format --check on tests/ before pushing, and fix the two opposite shapes (too-long literal vs over-wrapped call expression)."

## Quick Reference

```bash
# E501 / format on a large feature PR — lint AND format-check BOTH prod + tests
pixi run ruff check  hephaestus/ tests/        # E501 line-length (limit = 100)
pixi run ruff format --check hephaestus/ tests/  # format wants some lines collapsed
# Newly-ADDED test files are just as subject to E501 + ruff format as production code.
```

```python
# S101: assert guard  ->  explicit RuntimeError
# BEFORE
assert self.experiment_dir is not None  # noqa: S101
return self.experiment_dir / "checkpoint.json"
# AFTER
if self.experiment_dir is None:
    raise RuntimeError("experiment_dir must be set before getting checkpoint path")
return self.experiment_dir / "checkpoint.json"
```

```python
# C901: inline branches  ->  extract helpers (each gets its own CC budget)
def _restore_run_context(ctx, state):
    if condition:
        _restore_judgment(ctx)        # CC counted in helper, not parent
    if condition:
        _restore_run_result(ctx)

def _restore_judgment(ctx): ...       # starts at CC=1
```

### Detailed Steps

#### Pattern A — Fix Ruff S101 (assert -> RuntimeError)

**Key insight**: `assert` is inappropriate in production code because Python's `-O` (optimize)
flag disables all `assert` statements. Legitimate runtime guards must use explicit `raise`.

1. **Find all violations** (current line numbers, not the stale ones in the issue):

   ```bash
   grep -rn "noqa: S101" <src-path>/          # production only
   grep -rn "noqa: S101" <src-path>/ <test-path>/   # full picture; tests may legitimately keep noqa
   ```

   The grep often finds MORE asserts than the issue lists (10 vs 6 reported in `runner.py`) — fix all of them if the deliverable is "no S101 in file X".

2. **Read context around each assert** to write a message describing *what operation is blocked*, not just restating the condition. Message format: `"<attribute> must be set before <operation>"`.

3. **Classify and replace**:

   | Assert pattern | Replacement |
   | --------------- | ----------- |
   | `assert x is not None  # noqa: S101` | `if x is None: raise RuntimeError("x must be set before <op>")` |
   | `assert x is not None, "msg"  # noqa: S101` | `if x is None: raise RuntimeError("msg")` (reuse the message verbatim) |
   | `assert condition  # noqa: S101` | `if not condition: raise RuntimeError("<condition description>")` |

   **For-else defensive guard** (e.g. retry loop in `llm_judge.py`): the `else` fires only if every attempt caught a `ValueError`, so `last_parse_error` is logically never `None`. Keep the guard — protect against future breakage — do not delete it:

   ```python
   else:
       if last_parse_error is None:
           raise RuntimeError("Judge retry loop exhausted but last_parse_error is None")
       raise last_parse_error
   ```

4. **Add regression tests** to the existing test class (no new files unless a guard has no home):

   ```python
   def test_method_raises_if_x_none(self, tmp_path: Path) -> None:
       obj = MyClass(attr=None, ...)
       with pytest.raises(RuntimeError, match="attr must be set before"):
           obj.method()
   ```

   For logically-unreachable guards (the for-else case), test the *observable adjacent behavior* — that the normal exhausted-retry path re-raises `ValueError` (not `RuntimeError`) — rather than contriving a path into the guard:

   ```python
   def test_raises_value_error_not_runtime_error_when_parse_fails(self, tmp_path: Path) -> None:
       bad = "Not valid JSON at all"
       with pytest.raises(ValueError):
           self._run_with_call_side_effects(tmp_path, [(bad, "", bad)] * 3)
   ```

   Coverage may stay flat — guard paths protect against impossible states and aren't exercised. That is expected.

5. **Verify and commit**:

   ```bash
   grep -rn "noqa: S101" <src-path>/    # must be empty
   pre-commit run --all-files           # run TWICE: ruff-format reflows long raise lines on pass 1
   pixi run python -m pytest <test-path>/ -q
   ```

#### Pattern B — Fix Ruff C901 (extract helpers)

1. **Identify the violation**: CI shows the function name and CC score, e.g. `_restore_run_context is too complex (11 > 10)`.

2. **Count branches**: each `if`/`elif`/`else`/`for`/`while`/`except`/`and`/`or` adds +1. The function starts at CC=1.

   | CC | Status | Action |
   | -- | ------ | ------ |
   | 1-7 | Safe | Can add 1-3 branches freely |
   | 8-9 | Warning | One more `if/else` hits the limit |
   | 10 | At limit | Any new branch fails CI |
   | 11+ | CI failure | Must extract helpers |

3. **Extract self-contained blocks** into module-level helpers or instance methods — blocks with their own imports, operating on a clear parameter subset, not sharing mutable state beyond `ctx`/`self`. Each helper gets its own CC budget starting at 1. Keep guard clauses in the parent:

   ```python
   if is_at_or_past_state(run_state, RunState.JUDGE_COMPLETE) and ctx.judgment is None:
       _restore_judgment(ctx)

   def _restore_judgment(ctx: Any) -> None:
       """Restore ctx.judgment from on-disk judge result."""
       from scylla.e2e.judge_runner import _has_valid_judge_result, _load_judge_result
       judge_dir = get_judge_dir(ctx.run_dir)
       if _has_valid_judge_result(ctx.run_dir):
           ctx.judgment = _load_judge_result(judge_dir)
   ```

4. **Multi-pass rendering — return-value threading**: when a method runs several sequential passes that each compute state feeding the next (workers -> separator -> logs), extract each pass as an instance method that takes and returns the running offset. No shared mutable state:

   ```python
   def _refresh_display(self, screen, height, width):
       start_row = 0
       start_row = self._draw_workers(start_row, height, width)
       start_row = self._draw_separator(start_row, height, width)
       start_row = self._draw_logs(start_row, height, width)

   def _draw_workers(self, start_row: int, height: int, width: int) -> int:
       ...
       return next_row   # next free row, threaded into the following pass
   ```

   Test each helper for return-value threading, boundary handling, and truncation independently.

5. **Verify**:

   ```bash
   pre-commit run --all-files                     # ruff C901 + custom "Check Cyclomatic Complexity" hook
   pixi run python -m pytest <test-path>/ -x -q
   ```

   Do NOT use `# noqa: C901` to suppress — extract-method is the correct fix. Many repos prohibit `--no-verify` and lint suppression.

#### Pattern C — Linter as root cause of repeated policy violations

When an audit flags the SAME rule violated in **2+ independent files**, the file count (not line
count) is the signal: two violations in one file are a localized bug; two in unrelated files are a
systemic one. The linter/validator that should enforce the policy is the FIRST suspect.

1. **Tally findings by rule ID**:

   ```bash
   jq -r '.findings[].rule' audit.json | sort | uniq -c | sort -rn   # JSON
   grep -oP 'Rule:\s*\K\S+' audit.md | sort | uniq -c | sort -rn      # text
   ```

2. **Locate the linter's rule definition** (read BOTH the good-pattern and bad-pattern sides):

   ```bash
   grep -rn "<rule-keyword>" <validation-module-path>/ <validation-tests-path>/ scripts/audit_*.py
   ```

3. **Locate the META source** the rule claims to enforce — `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, branch-protection rules. Read its statement verbatim.

4. **Diff linter assertion vs META source**:

   | Linter says | META says | Verdict |
   | ----------- | --------- | ------- |
   | Accept X, reject Y | Require X, prohibit Y | Linter correct — violations are real bugs; fix per-file |
   | Accept Y, reject X | Require X, prohibit Y | **Linter is WRONG-DIRECTION — fix linter FIRST** |
   | No assertion | Require X, prohibit Y | Linter has a gap — add the assertion, then fix files |

   If wrong-direction, the dependent files were written to COMPLY WITH the wrong linter — they are downstream consumers of a wrong contract, not independently buggy.

5. **Re-sequence PRs**: linter fix (validator + flipped test assertions, as ONE atomic PR) lands first; dependent file fixes land on top of main afterward. Opening per-file fixes first means CI rejects the correct pattern.

6. **Add pair-direction regression tests** so a future contributor with the same mental model can't flip the direction again:

   ```python
   def test_accepts_required_pattern(self):
       assert is_compliant("<required-pattern>")
   def test_rejects_prohibited_pattern(self):
       assert not is_compliant("<prohibited-pattern>")
   ```

7. **If META is also wrong** (e.g. CLAUDE.md says `--rebase` but branch protection disables rebase merge), the deployed config is ground truth — fix META first, then linter, then dependents. Confirm via `gh api repos/<owner>/<repo>/branches/<branch>/protection`.
```

## Verified Workflow

### Quick Reference

```bash
# S101 — find assert guards in production code (exclude tests)
grep -rn "noqa: S101\|assert.*is not None" <src-path>/

# C901 — locally reproduce the complexity check
pre-commit run --all-files            # ruff C901 + custom CC hook

# RUF022 (__all__ not sorted) / I001 (import block un-sorted) — both [*]-fixable
# NEVER manually reorder: isort sorts by the 'as' alias name, not the original symbol
pixi run ruff check --fix <file1> <file2>
# Running --fix on just the affected files is safe and idempotent.
# Three errors were fixed in one pass across two files (issue #1189).

# Linter-as-root-cause — count distinct files violating the SAME rule
audit_output | grep "Rule: <rule-id>" | awk '{print $2}' | sort -u | wc -l
# >= 2 distinct files  ->  fix the LINTER first, not each file
```

```python
# S101: assert guard  ->  explicit RuntimeError
# BEFORE
assert self.experiment_dir is not None  # noqa: S101
return self.experiment_dir / "checkpoint.json"
# AFTER
if self.experiment_dir is None:
    raise RuntimeError("experiment_dir must be set before getting checkpoint path")
return self.experiment_dir / "checkpoint.json"
```

```python
# C901: inline branches  ->  extract helpers (each gets its own CC budget)
def _restore_run_context(ctx, state):
    if condition:
        _restore_judgment(ctx)        # CC counted in helper, not parent
    if condition:
        _restore_run_result(ctx)

def _restore_judgment(ctx): ...       # starts at CC=1
```

### Detailed Steps

#### Pattern A — Fix Ruff S101 (assert -> RuntimeError)

**Key insight**: `assert` is inappropriate in production code because Python's `-O` (optimize)
flag disables all `assert` statements. Legitimate runtime guards must use explicit `raise`.

1. **Find all violations** (current line numbers, not the stale ones in the issue):

   ```bash
   grep -rn "noqa: S101" <src-path>/          # production only
   grep -rn "noqa: S101" <src-path>/ <test-path>/   # full picture; tests may legitimately keep noqa
   ```

   The grep often finds MORE asserts than the issue lists (10 vs 6 reported in `runner.py`) — fix all of them if the deliverable is "no S101 in file X".

2. **Read context around each assert** to write a message describing *what operation is blocked*, not just restating the condition. Message format: `"<attribute> must be set before <operation>"`.

3. **Classify and replace**:

   | Assert pattern | Replacement |
   | --------------- | ----------- |
   | `assert x is not None  # noqa: S101` | `if x is None: raise RuntimeError("x must be set before <op>")` |
   | `assert x is not None, "msg"  # noqa: S101` | `if x is None: raise RuntimeError("msg")` (reuse the message verbatim) |
   | `assert condition  # noqa: S101` | `if not condition: raise RuntimeError("<condition description>")` |

   **For-else defensive guard** (e.g. retry loop in `llm_judge.py`): the `else` fires only if every attempt caught a `ValueError`, so `last_parse_error` is logically never `None`. Keep the guard — protect against future breakage — do not delete it:

   ```python
   else:
       if last_parse_error is None:
           raise RuntimeError("Judge retry loop exhausted but last_parse_error is None")
       raise last_parse_error
   ```

4. **Add regression tests** to the existing test class (no new files unless a guard has no home):

   ```python
   def test_method_raises_if_x_none(self, tmp_path: Path) -> None:
       obj = MyClass(attr=None, ...)
       with pytest.raises(RuntimeError, match="attr must be set before"):
           obj.method()
   ```

   For logically-unreachable guards (the for-else case), test the *observable adjacent behavior* — that the normal exhausted-retry path re-raises `ValueError` (not `RuntimeError`) — rather than contriving a path into the guard:

   ```python
   def test_raises_value_error_not_runtime_error_when_parse_fails(self, tmp_path: Path) -> None:
       bad = "Not valid JSON at all"
       with pytest.raises(ValueError):
           self._run_with_call_side_effects(tmp_path, [(bad, "", bad)] * 3)
   ```

   Coverage may stay flat — guard paths protect against impossible states and aren't exercised. That is expected.

5. **Verify and commit**:

   ```bash
   grep -rn "noqa: S101" <src-path>/    # must be empty
   pre-commit run --all-files           # run TWICE: ruff-format reflows long raise lines on pass 1
   pixi run python -m pytest <test-path>/ -q
   ```

#### Pattern B — Fix Ruff C901 (extract helpers)

1. **Identify the violation**: CI shows the function name and CC score, e.g. `_restore_run_context is too complex (11 > 10)`.

2. **Count branches**: each `if`/`elif`/`else`/`for`/`while`/`except`/`and`/`or` adds +1. The function starts at CC=1.

   | CC | Status | Action |
   | -- | ------ | ------ |
   | 1-7 | Safe | Can add 1-3 branches freely |
   | 8-9 | Warning | One more `if/else` hits the limit |
   | 10 | At limit | Any new branch fails CI |
   | 11+ | CI failure | Must extract helpers |

3. **Extract self-contained blocks** into module-level helpers or instance methods — blocks with their own imports, operating on a clear parameter subset, not sharing mutable state beyond `ctx`/`self`. Each helper gets its own CC budget starting at 1. Keep guard clauses in the parent:

   ```python
   if is_at_or_past_state(run_state, RunState.JUDGE_COMPLETE) and ctx.judgment is None:
       _restore_judgment(ctx)

   def _restore_judgment(ctx: Any) -> None:
       """Restore ctx.judgment from on-disk judge result."""
       from scylla.e2e.judge_runner import _has_valid_judge_result, _load_judge_result
       judge_dir = get_judge_dir(ctx.run_dir)
       if _has_valid_judge_result(ctx.run_dir):
           ctx.judgment = _load_judge_result(judge_dir)
   ```

4. **Multi-pass rendering — return-value threading**: when a method runs several sequential passes that each compute state feeding the next (workers -> separator -> logs), extract each pass as an instance method that takes and returns the running offset. No shared mutable state:

   ```python
   def _refresh_display(self, screen, height, width):
       start_row = 0
       start_row = self._draw_workers(start_row, height, width)
       start_row = self._draw_separator(start_row, height, width)
       start_row = self._draw_logs(start_row, height, width)

   def _draw_workers(self, start_row: int, height: int, width: int) -> int:
       ...
       return next_row   # next free row, threaded into the following pass
   ```

   Test each helper for return-value threading, boundary handling, and truncation independently.

5. **Verify**:

   ```bash
   pre-commit run --all-files                     # ruff C901 + custom "Check Cyclomatic Complexity" hook
   pixi run python -m pytest <test-path>/ -x -q
   ```

   Do NOT use `# noqa: C901` to suppress — extract-method is the correct fix. Many repos prohibit `--no-verify` and lint suppression.

#### Pattern C — Linter as root cause of repeated policy violations

When an audit flags the SAME rule violated in **2+ independent files**, the file count (not line
count) is the signal: two violations in one file are a localized bug; two in unrelated files are a
systemic one. The linter/validator that should enforce the policy is the FIRST suspect.

1. **Tally findings by rule ID**:

   ```bash
   jq -r '.findings[].rule' audit.json | sort | uniq -c | sort -rn   # JSON
   grep -oP 'Rule:\s*\K\S+' audit.md | sort | uniq -c | sort -rn      # text
   ```

2. **Locate the linter's rule definition** (read BOTH the good-pattern and bad-pattern sides):

   ```bash
   grep -rn "<rule-keyword>" <validation-module-path>/ <validation-tests-path>/ scripts/audit_*.py
   ```

3. **Locate the META source** the rule claims to enforce — `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, branch-protection rules. Read its statement verbatim.

4. **Diff linter assertion vs META source**:

   | Linter says | META says | Verdict |
   | ----------- | --------- | ------- |
   | Accept X, reject Y | Require X, prohibit Y | Linter correct — violations are real bugs; fix per-file |
   | Accept Y, reject X | Require X, prohibit Y | **Linter is WRONG-DIRECTION — fix linter FIRST** |
   | No assertion | Require X, prohibit Y | Linter has a gap — add the assertion, then fix files |

   If wrong-direction, the dependent files were written to COMPLY WITH the wrong linter — they are downstream consumers of a wrong contract, not independently buggy.

5. **Re-sequence PRs**: linter fix (validator + flipped test assertions, as ONE atomic PR) lands first; dependent file fixes land on top of main afterward. Opening per-file fixes first means CI rejects the correct pattern.

6. **Add pair-direction regression tests** so a future contributor with the same mental model can't flip the direction again:

   ```python
   def test_accepts_required_pattern(self):
       assert is_compliant("<required-pattern>")
   def test_rejects_prohibited_pattern(self):
       assert not is_compliant("<prohibited-pattern>")
   ```

7. **If META is also wrong** (e.g. CLAUDE.md says `--rebase` but branch protection disables rebase merge), the deployed config is ground truth — fix META first, then linter, then dependents. Confirm via `gh api repos/<owner>/<repo>/branches/<branch>/protection`.

#### Pattern D — Ruff E501 / format failures in newly-added TEST code on a large feature PR

**Key insight**: A feature PR that touches many files (44 console-script entry points in
ProjectHephaestus PR #1035) can pass every unit + integration test locally yet fail CI on a
SINGLE category — Ruff **E501** (`line-too-long`, limit = 100) or `ruff format --check`. The
offending lines are almost always in the **newly-ADDED test files**, not the production change.
New test code is just as subject to the line-length limit and the formatter as production code;
"my code passes" is not enough when the test files you added are unformatted.

1. **Lint AND format-check BOTH trees before pushing** (this is the whole prevention):

   ```bash
   pixi run ruff check  hephaestus/ tests/
   pixi run ruff format --check hephaestus/ tests/
   ```

   For a large multi-file feature PR this is the single most common avoidable CI failure in
   this repo. Run it on `tests/` explicitly — it is easy to lint only the production package and
   forget the test files the feature added.

2. **Fix the TWO OPPOSITE shapes** — the same 100-char limit produces two failure modes that
   need opposite fixes:

   **Shape (a): a single-line literal that is too long → break into a multi-line assignment.**
   A long iterable literal inlined into a `for` header overflows 100 chars. Hoist it into a
   multi-line tuple assignment with one element per line, then iterate:

   ```python
   # BEFORE (105 chars — E501):
   for symbol in ("create_parser", "COMMAND_REGISTRY", "format_table", "Colors", "add_version_arg"):
       assert symbol in cli.__all__

   # AFTER (each line < 100):
   symbols = (
       "create_parser",
       "COMMAND_REGISTRY",
       "format_table",
       "Colors",
       "add_version_arg",
   )
   for symbol in symbols:
       assert symbol in cli.__all__
   ```

   **Shape (b): a manually wrapped call expression that ruff format wants on ONE line → let the
   formatter collapse it.** Do NOT hand-wrap a `subprocess.run(...)` / call that already fits
   under 100 chars when joined — `ruff format` will keep reporting "files were modified" until
   you collapse it:

   ```python
   # BEFORE (over-wrapped by hand — ruff format rewrites this):
   result = subprocess.run(
       [binary, "--version"],
       capture_output=True,
       text=True,
       timeout=30,
   )

   # AFTER (88 chars — what ruff format produces; let the formatter decide):
   result = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=30)
   ```

   Rule of thumb: never hand-wrap to satisfy E501 a line that already fits on one line — run
   `ruff format` and accept its layout. Only break lines that genuinely exceed 100 chars even
   when joined (Shape a).

3. **Positive convention worth reusing — composable arg-helper + parametrized entry-point test.**
   The change that triggered the E501 was the *correct* architecture: a cross-cutting CLI flag
   rolled out via a small composable helper (mirroring the repo's existing `add_json_arg()` /
   `add_logging_args()`), NOT a monolithic `create_parser()` every CLI must route through.

   ```python
   # hephaestus/cli/utils.py — one helper, sits next to add_json_arg()
   def add_version_arg(parser: argparse.ArgumentParser) -> None:
       """Add a -V/--version flag that prints '<prog> <version>' and exits 0."""
       parser.add_argument(
           "-V", "--version", action="version", version=f"%(prog)s {__version__}"
       )
   # action="version" gives exit code 0 automatically.

   # Each entry point opts in next to its other arg helpers:
   add_version_arg(parser)
   add_json_arg(parser)
   ```

   Guard the rollout with ONE parametrized integration test over every entry point, so a future
   CLI that forgets the convention fails CI loudly:

   ```python
   @pytest.mark.parametrize("command,module_path,attr", ENTRY_POINTS)
   def test_entry_point_responds_to_version(command, module_path, attr):
       for flag in ("--version", "-V"):
           result = subprocess.run([command, flag], capture_output=True, text=True, timeout=30)
           assert result.returncode == 0
   ```

4. **Verify and push:**

   ```bash
   pixi run ruff check  hephaestus/ tests/    # zero E501
   pixi run ruff format --check hephaestus/ tests/  # "X files already formatted"
   pixi run pytest tests/unit tests/integration -q
   ```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Suppress C901 with `# noqa: C901` | Considered suppressing the complexity warning instead of refactoring | Project prohibits `--no-verify` and lint-rule suppression | Extract-method is the correct fix, not suppression |
| Inline all restore logic in one function | Added judgment + run_result restore as new `if` blocks in a function already at CC~8 | CC went to 11, exceeding the C901 limit of 10 | Check the CC budget before adding branches to a function near the limit |
| Contrive a test into an unreachable guard | First S101 for-else test used a `StopIteration` trick to hit the logically-unreachable `RuntimeError` guard | The guard cannot fire in normal operation; the trick was brittle and abandoned | Test observable adjacent behavior (normal exhausted-retry path), not the unreachable guard path |
| Skip the second pre-commit run | Ran `pre-commit` once after converting asserts | ruff-format reflowed the longer `raise RuntimeError(...)` lines and reported "files were modified" | The `if ... raise` form is longer than the assert; run pre-commit twice (reflow, then confirm clean) |
| Open N parallel PRs to fix N violating files | 2 separate PRs to fix `--rebase`->`--squash` in two skill files | The validator enforced the WRONG direction (required `--rebase`, rejected `--squash`); the new PRs would fail CI on the correct pattern | When >=2 files violate the same rule, the linter is the first suspect — read its rule definition before per-file PRs |
| Fix linter and dependent files in one PR | Considered bundling validator + all doc fixes into one mega-PR | Linter and doc changes have different test surfaces; bundling makes CI feedback ambiguous | Keep the linter fix as its own atomic PR; dependent fixes land afterward |
| Flip only the validator, not its tests | Planned to update validator code but leave its test suite | Validator tests still asserted the wrong direction — the linter PR itself fails CI | Validator source + its tests are one atomic change; flip both together |
| Single-direction regression test | Wrote a test asserting only "accepts `--squash`" | A future agent with the same wrong-direction model could re-flip the assertion and ship it | Pair tests: assert correct accepted AND wrong rejected, to prevent silent drift |
| Manual reorder of `__all__` with `as` aliases | Tried to alphabetize `__all__` entries and import block by hand when ruff reported RUF022 + I001 | isort orders by the **alias** name (the `as <name>` part), not the original symbol — naive alphabetical order of original names produces a different sequence that ruff still rejects | Always use `pixi run ruff check --fix <files>` for RUF022 and I001; these are `[*]`-fixable and the sort order is non-obvious when `as` aliases are present |

| Push a 44-file feature PR after only running the tests | Ran the unit + integration suite (green) and pushed PR #1035 without ruff-checking the new test files | CI failed on E501 — a 105-char tuple literal in `test_utils.py` and over-wrapped `subprocess.run` calls in the integration test | New TEST code is subject to E501 + `ruff format` too; run `ruff check` AND `ruff format --check` on `tests/`, not just `hephaestus/`, before pushing |
| Hand-wrap the long `for` header to fit 100 chars | Tried to keep the symbol tuple inline and wrap the `for` line | A long iterable literal inlined in a `for` header still overflows; wrapping the statement does not shorten the literal | Hoist the literal into a multi-line `symbols = (...)` assignment (one element per line) and iterate over the name |
| Hand-wrap `subprocess.run(...)` across multiple lines to "be safe" | Manually broke the call onto 5 lines to avoid E501 | The joined call is only ~88 chars; `ruff format` wants it on ONE line and reported "files were modified" every run | Never hand-wrap a call that fits under 100 chars joined — let `ruff format` choose the layout; only break lines that exceed 100 even when joined |

## Results & Parameters

### S101 conversions (verified)

```text
Issue #1066 / PR #1142: 16 asserts replaced (10 in runner.py, 6 in stages.py),
                        16 noqa removed, 3185 tests pass, 78.09% coverage (>=75%)
Issue #1143 / PR #1211: 4 remaining sites converted (workspace_manager.py x2,
                        llm_judge.py for-else, runner.py _finalize_test_summary),
                        4 regression tests added, 3261 tests pass, 78.39% coverage,
                        zero S101 suppressions remain in scylla/
```

Representative replacement messages: `"experiment_dir must be set before getting checkpoint path"`,
`"agent_result must be set before finalize_run"`, `"commit must be set before calling _checkout_commit"`,
`"Judge retry loop exhausted but last_parse_error is None"`,
`"_state must be initialized before finalizing test summary"`.

### C901 configuration

- **Ruff C901**: `max-complexity = 10` (in `pyproject.toml` lint config).
- **Custom hook**: `Check Cyclomatic Complexity` — runs separately from ruff at the same threshold; both must pass for CI green.

### Linter-as-root-cause re-sequencing template

```text
WRONG ORDER (fails CI):           CORRECT ORDER:
  PR1: fix file_A   <- rejected     PR1: fix linter (validator + flipped tests)
  PR2: fix file_B   <- rejected     PR2: fix file_A (depends on PR1)
                                    PR3: fix file_B (depends on PR1)
                                    PR4: fix META source (only if META also wrong)
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectScylla | S101 bulk elimination — runner.py + stages.py (16 asserts) | PR #1142 (issue #1066) |
| ProjectScylla | S101 follow-up — 4 remaining production sites + regression tests | PR #1211 (issue #1143) |
| ProjectScylla | C901 — extracted `_restore_judgment()` / `_restore_run_result()` from `_restore_run_context()`, CC 11 -> ~7 | PR #1546 |
| ProjectHephaestus | C901 multi-pass — extracted `_draw_workers/_separator/_logs` from `_refresh_display()`, 69 lines -> 3 methods, 8 -> 23 tests, removed `# noqa: C901` | PR #1050 (issue #804) |
| ProjectHephaestus | Linter-as-root-cause — strict audit caught 2 skill files violating `--squash`-only merge policy; root cause was a wrong-direction validator | PRs #863, #865, #866, #867 |
| ProjectHephaestus | RUF022 + I001 — `__all__` sort and import-block sort in `hephaestus/validation/` after python-version-consistency DRY refactor; 3 errors fixed in one `ruff check --fix` pass across 2 files | Issue #1189 |
