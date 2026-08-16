---
name: python-cli-dry-run-and-entrypoint-patterns
license: BSD-3-Clause
description: "Use when: (1) adding a --dry-run flag to a CLI script that exits 1 on errors, letting developers preview all violations without blocking pre-commit or CI during bulk migrations; (2) standardizing --dry-run help text across multiple CLIs using a shared constant and testable _build_parser() entrypoint helper; (3) smoke-testing Python CLI entry points declared in [project.scripts] with --help subprocess calls and import verification to prevent regressions; (4) refactoring CLI parsers to extract testable _build_parser() functions and adding parametrized help-text tests across CLI modules; (5) making a standalone analysis CLI report findings by default but fail only when an explicit --fail-on-* gate is supplied, with subprocess tests proving both exit-code modes."
category: tooling
date: 2026-08-06
version: "1.2.0"
user-invocable: false
verification: unverified
history: python-cli-dry-run-and-entrypoint-patterns.history
tags:
  - python
  - cli
  - argparse
  - dry-run
  - help-text
  - entry-points
  - smoke-tests
  - parametrized-tests
  - DRY-principle
  - refactoring
  - failure-gates
  - standalone-scripts
  - subprocess-testing
---

# Python CLI Advisory Modes and Entry-Point Patterns

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-06 |
| **Objective** | Capture the shared Python CLI developer-tooling surface: advisory output with explicit failure gates, the `--dry-run` flag idiom, testable parser construction, and realistic subprocess coverage |
| **Outcome** | MIXED — the original dry-run and packaged-entry-point patterns are verified in CI; the standalone `--fail-on-*` extension is a reviewed implementation design awaiting execution |
| **Verification** | unverified overall; Sections A–D retain their recorded `verified-ci` evidence, while Section E is unverified |
| **History** | [changelog](./python-cli-dry-run-and-entrypoint-patterns.history) |

## When to Use

- A validation/CLI script exits 1 on errors and you want a non-blocking preview mode that
  prints all violations but returns 0 — useful during bulk config migrations or refactors
- Multiple CLI modules each declare `--dry-run` with subtly different (drifting) help text
- Token-cost or behavioral caveats must be user-visible at `--help` time, not buried in docs
- CLI parsers are tightly coupled to arg parsing, making help-text testing difficult — you
  want a clean `_build_parser()` you can inspect without `sys.exit` side effects
- A package declares `[project.scripts]` entry points that need regression protection
  against import errors, missing dependencies, or broken `main()` signatures
- An issue asks for CLI importability / entry-point integration tests
- A standalone analysis script must always report detected problems, but a nonzero exit status
  should be opt-in for callers that deliberately enable a `--fail-on-*` policy gate
- A script-level contract needs executable tests for observable stdout/stderr and exit codes,
  rather than tests that only inspect `argparse` internals

Do NOT use when:

- Entry points require real credentials or network access just for `--help`
- The package doesn't use argparse/click (custom CLI parsing may not support `--help`)

## Verified Workflow

Sections A–D preserve their earlier `verified-ci` evidence.

### Quick Reference

```python
# 1. Non-blocking dry-run: check the flag AFTER the full loop, never inside it
if any_failure and dry_run:
    return 0          # all errors already printed; do not block
return 1 if any_failure else 0

# 2. DRY help text: one constant + one helper, never inline strings
DRY_RUN_HELP_CAVEAT = (
    "Do not create PR, file follow-up issues, or invoke /learn. "
    "Useful for testing without incurring token costs."
)
add_dry_run_arg(parser, prefix="Skip PR creation")

# 3. Testable entrypoint: split parser construction from parsing
def _build_parser() -> ArgumentParser: ...      # no side effects, inspectable
def _parse_args(args=None): return _build_parser().parse_args(args)

```

```bash
# Smoke-test entry points via sys.executable -m (no pip-installed scripts needed)
python -m hephaestus.git.changelog --help
pixi run pytest tests/integration/test_cli_entry_points.py -v --no-cov
```

### Detailed Steps

#### A. Add a non-blocking `--dry-run` flag to a validation script

1. **Add a `dry_run: bool = False` keyword parameter to the core function.** Keep the
   default `False` so existing callers are unaffected.

2. **Check the flag AFTER the full validation loop**, so all files are processed and all
   errors printed before the exit-code decision:

   ```python
   def check_files(
       files: list[Path],
       repo_root: Path,
       verbose: bool = False,
       dry_run: bool = False,
   ) -> int:
       """Validate each file against its matching schema.

       Args:
           files: List of file paths to check.
           repo_root: Repository root used for schema resolution.
           verbose: If True, print ``PASS:`` lines for valid files.
           dry_run: If True, print all errors but return 0 (do not block commits).

       Returns:
           0 if all files are valid or ``dry_run`` is True, 1 if any violations
           are found and ``dry_run`` is False.
       """
       # ... existing validation loop unchanged ...

       if any_failure and dry_run:
           return 0
       return 1 if any_failure else 0
   ```

   **Key**: putting the check inside the loop would early-return after the first failing
   file, defeating the purpose of dry-run (showing ALL violations).

3. **Add the `--dry-run` argparse flag in `main()`.** `argparse` converts `--dry-run` to
   `args.dry_run` (hyphen → underscore) automatically:

   ```python
   parser.add_argument(
       "--dry-run",
       action="store_true",
       help="Print all errors but exit 0 — useful for previewing violations without blocking commits",  # noqa: E501
   )
   args = parser.parse_args()
   return check_files(args.files, args.repo_root, verbose=args.verbose, dry_run=args.dry_run)
   ```

4. **Update the module docstring's exit-codes section** to document the dry-run path:

   ```python
   Exit codes:
       0: All files valid (or no matching schema found — warned, not failed)
       0: Violations found but --dry-run is set (errors printed, commit not blocked)
       1: One or more schema violations found (without --dry-run)
   ```

5. **Handle line-length lint** — the `--dry-run` help string typically exceeds the limit.
   Prefer `# noqa: E501` inline over splitting a single natural sentence across lines.

6. **Write tests covering all four combinations** of `dry_run × (violations / no-violations)`
   plus `main()` integration via `monkeypatch.setattr("sys.argv", [...])` (no subprocess):

   ```python
   class TestDryRun:
       def test_dry_run_with_violations_returns_zero(self, tmp_path: Path) -> None:
           assert check_files([bad], repo_root, dry_run=True) == 0

       def test_dry_run_false_with_violations_returns_one(self, tmp_path: Path) -> None:
           assert check_files([bad], repo_root, dry_run=False) == 1

       def test_dry_run_multiple_bad_files_all_reported(self, tmp_path, capsys) -> None:
           result = check_files([bad_a, bad_b], repo_root, dry_run=True)
           assert result == 0
           assert "bad_a.yaml" in capsys.readouterr().err
           assert "bad_b.yaml" in capsys.readouterr().err

       def test_main_dry_run_flag_with_violations_exits_zero(self, monkeypatch) -> None:
           monkeypatch.setattr(
               "sys.argv",
               ["validate.py", "--dry-run", "--repo-root", str(repo_root), str(bad)],
           )
           assert main() == 0
   ```

#### B. Standardize `--dry-run` help text across many CLIs (DRY)

1. **Identify all CLI modules declaring `--dry-run`** — `grep -r "add_argument.*dry.run"`
   to find every occurrence and inspect for drift.

2. **Create a canonical constant** in a shared module (e.g. `hephaestus/cli/utils.py`).
   Include a token-cost caveat so users see it at `--help` time:

   ```python
   DRY_RUN_HELP_CAVEAT = (
       "Do not create PR, file follow-up issues, or invoke /learn. "
       "Useful for testing without incurring token costs."
   )
   ```

3. **Create a helper with keyword-only `prefix` and auto-punctuation.** The `*` makes it
   impossible to pass `prefix` positionally and signals intent at the call site:

   ```python
   def add_dry_run_arg(parser: ArgumentParser, *, prefix: str | None = None) -> None:
       """Add --dry-run argument to parser with canonical help text.

       Args:
           parser: ArgumentParser to add --dry-run to.
           prefix: Optional prefix prepended to help text (auto-punctuated).
       """
       help_text = DRY_RUN_HELP_CAVEAT
       if prefix:
           if not prefix.endswith("."):
               prefix = prefix + "."
           help_text = f"{prefix} {help_text}"
       else:
           if help_text and not help_text[0].isupper():
               help_text = help_text[0].upper() + help_text[1:]
           if not help_text.endswith("."):
               help_text = help_text + "."
       parser.add_argument("--dry-run", action="store_true", help=help_text)
   ```

4. **Replace every inline `--dry-run` help string** with `add_dry_run_arg(parser, ...)`.

   **Ruff/pre-commit gotchas while refactoring** (see Failed Attempts): if the shared module
   declares an `__all__` export list, keep it alphabetically sorted (case-sensitive, lowercase
   before UPPERCASE) or ruff isort will fail — fix with `ruff check --select=I --fix`. And when
   writing the `add_dry_run_arg`/`_build_parser` docstrings, put the closing `"""` of a
   multi-line docstring on its own line; ruff's formatter rejects a closing `"""` that shares a
   line with content.

#### C. Extract a testable `_build_parser()` entrypoint

Split parser construction from parsing so tests can inspect parser metadata (help text,
defaults, option strings) without triggering `sys.exit`:

```python
def _build_parser() -> ArgumentParser:
    """Build and return the parser without parsing args (no side effects)."""
    parser = ArgumentParser(description="...")
    parser.add_argument("--verbose", "-v", action="store_true")
    add_dry_run_arg(parser, prefix="Skip PR creation")
    return parser

def _parse_args(args: list[str] | None = None) -> Namespace:
    return _build_parser().parse_args(args)
```

Then write a **parametrized** help-text test from the start (covering ALL modules, not
just one) so drift across the entire CLI surface is caught:

```python
@pytest.mark.parametrize("cli_module", [
    "hephaestus.automation.planner",
    "hephaestus.automation.plan_reviewer",
    "hephaestus.automation.pr_reviewer",
    "hephaestus.automation.address_review",
    "hephaestus.automation.implementer_cli",
    "hephaestus.cli.ci_driver",
    "hephaestus.automation.loop_runner",
])
def test_dry_run_help_text_consistent(cli_module: str) -> None:
    module = importlib.import_module(cli_module)
    parser = module._build_parser()
    action = next(
        (a for a in parser._actions if "--dry-run" in a.option_strings), None,
    )
    assert action is not None, f"{cli_module} has no --dry-run arg"
    assert action.help == expected_help_text
```

#### D. Smoke-test `[project.scripts]` entry points

1. **Find entry points** in `pyproject.toml`:

   ```bash
   grep -A10 '\[project.scripts\]' pyproject.toml
   ```

   ```toml
   [project.scripts]
   hephaestus-changelog = "hephaestus.git.changelog:main"
   hephaestus-merge-prs = "hephaestus.github.pr_merge:main"
   hephaestus-system-info = "hephaestus.system.info:main"
   hephaestus-download-dataset = "hephaestus.datasets.downloader:main"
   ```

2. **Verify each module has `def main()` and an `if __name__ == "__main__": main()` block**,
   and that `--help` exits cleanly (argparse calls `sys.exit(0)` before business logic, so
   it is safe as long as there are no module-level side effects at import time).

3. **Write a two-class test** — fast in-process import checks plus realistic out-of-process
   `--help` subprocess checks. Use `sys.executable -m module.path` (NOT installed script
   names) and assert `"usage:"` to confirm argparse actually ran:

   ```python
   import importlib, subprocess, sys
   import pytest

   ENTRY_POINTS = [
       ("hephaestus.git.changelog", "main"),
       ("hephaestus.github.pr_merge", "main"),
       ("hephaestus.system.info", "main"),
       ("hephaestus.datasets.downloader", "main"),
   ]

   class TestCLIEntryPointImports:
       @pytest.mark.parametrize("module_path,func_name", ENTRY_POINTS)
       def test_main_importable_and_callable(self, module_path, func_name) -> None:
           mod = importlib.import_module(module_path)
           main_func = getattr(mod, func_name, None)
           assert callable(main_func), f"{module_path}.{func_name} not callable"

   class TestCLIEntryPointHelp:
       @pytest.mark.parametrize("module_path", [ep[0] for ep in ENTRY_POINTS])
       def test_help_exits_cleanly(self, module_path) -> None:
           result = subprocess.run(
               [sys.executable, "-m", module_path, "--help"],
               capture_output=True, text=True, timeout=30,
           )
           assert result.returncode == 0, result.stderr
           assert "usage:" in result.stdout.lower()
   ```

4. **CRITICAL — install the package in every CI workflow that runs the subprocess test.**
   A freshly-spawned `python` subprocess does NOT inherit pytest's
   `[tool.pytest.ini_options] pythonpath` injection nor `conftest.py` `sys.path` tricks —
   those only help in-process tests. If the in-process import test passes while the
   subprocess `--help` test fails with `ModuleNotFoundError`, it is a missing-install /
   workflow-parity problem, NOT a code bug. Do NOT weaken the subprocess test to make it
   pass; add the editable-install step instead:

   ```yaml
   - name: Editable install (subprocess smoke tests import the package)
     run: pixi run dev-install   # = pip install -e . --no-deps
   - name: Run tests
     run: pixi run pytest tests/unit
   ```

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until
> implementation and CI confirm it.

### Quick Reference

```python
# Findings are always reported; only the explicit flag changes process status.
parser.add_argument(
    "--fail-on-regression",
    action="store_true",
    default=False,
    help="Exit 1 for critical regressions (default: report only)",
)
```

### Detailed Steps

#### E. Make strict failure opt-in for a standalone analysis script

This extension is **unverified**. It applies when a script should always render findings, but
its default use is advisory and only explicitly strict callers should receive a nonzero status.

1. **Keep the script a narrow adapter over the existing library.** Import loading,
   comparison, threshold, and report-formatting functions instead of copying their algorithms.
   If the command is intentionally standalone, restore only `scripts/<name>.py`; do not add a
   packaged console entry point or widen the public library API without a separate requirement.

2. **Make failure an explicit positive flag.** A `store_true` option with `default=False`
   makes the policy legible in both code and `--help`:

   ```python
   parser.add_argument(
       "--fail-on-regression",
       action="store_true",
       default=False,
       help="Exit 1 for critical regressions (default: report only)",
   )
   ```

   Avoid inverted names such as `--no-fail-on-regression` when advisory mode is the normal
   contract. Avoid `BooleanOptionalAction` when the requirement calls for one explicit opt-in
   switch; the generated negative spelling broadens the interface without adding value.

3. **Separate detection and reporting from exit policy.** Load inputs, select thresholds,
   detect changes, generate the report, and optionally write the output file exactly once.
   Decide the process status only after all reporting is complete:

   ```python
   if critical_count > 0:
       if args.fail_on_regression:
           print(
               f"\nFAIL: {critical_count} critical regressions detected",
               file=sys.stderr,
           )
           return 1
       print(
           f"\nWARN: {critical_count} critical regressions detected "
           "(failure disabled)",
           file=sys.stderr,
       )
   else:
       print("\nPASS: No critical regressions detected", file=sys.stderr)
   return 0
   ```

   This produces three truthful outcomes: findings with failure enabled, findings with
   failure disabled, and no critical findings. Never print `PASS: No critical regressions`
   merely because the failure gate is disabled—the findings still exist.

4. **Preserve existing input failure behavior.** If the historical adapter allowed
   `FileNotFoundError` and malformed JSON to reach the normal Python error path, do not silently
   translate or suppress them while changing only the regression-exit policy. The policy flag
   governs detected regressions, not invalid inputs.

5. **Exercise the real script as a subprocess.** Parser-unit tests can prove a default, but
   they cannot prove the shell-visible contract. Write deterministic temporary inputs that
   create the same critical finding in both modes, then assert the actual exit status and
   status text:

   ```python
   REPO_ROOT = Path(__file__).resolve().parents[3]
   SCRIPT = REPO_ROOT / "scripts" / "compare_benchmarks.py"

   def _run_compare(tmp_path: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
       baseline = tmp_path / "baseline.json"
       current = tmp_path / "current.json"
       baseline.write_text(
           json.dumps({"benchmarks": [{"name": "example", "duration_ms": 100}]}),
           encoding="utf-8",
       )
       current.write_text(
           json.dumps({"benchmarks": [{"name": "example", "duration_ms": 130}]}),
           encoding="utf-8",
       )
       return subprocess.run(
           [sys.executable, str(SCRIPT), str(current), str(baseline), *extra_args],
           cwd=REPO_ROOT,
           env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
           capture_output=True,
           text=True,
           check=False,
       )
   ```

   Assert that the default invocation returns `0` and includes both `critical` and
   `failure disabled` in stderr; assert that the otherwise-identical invocation with
   `--fail-on-regression` returns `1` and prints the exact `FAIL` summary. Invoke `--help`
   separately and assert that it says `default: report only`.

6. **Update the maintained script catalog.** When repository policy requires every tracked
   `scripts/` file to appear in `scripts/README.md`, document both default advisory behavior
   and the explicit nonzero-exit flag. Run the catalog guard alongside the script smoke tests.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Checking `dry_run` inside the validation loop | Early-returned 0 as soon as `dry_run` and a failure were seen | Stopped after the first failing file, so only one violation was printed | Check `if any_failure and dry_run: return 0` AFTER the full loop so ALL violations are reported |
| Leaving help text inline in each argparse call | Each CLI had its own `help="Do not create PR, ..."` string | Help text drifted: typos, missing token-cost caveat, copy-paste variations | Use a canonical constant + helper (`add_dry_run_arg`), never inline strings |
| Adding period/capitalization manually per CLI | Some added punctuation in the constant, others in the call | Inconsistent punctuation; updating canonical text meant editing 7 places | Encapsulate auto-punctuation inside the helper so formatting is consistent regardless of prefix |
| Declaring `__all__` in creation order in the shared module | Entries listed in the order helpers were defined, not alphabetically | ruff isort (`--select=I`) flagged `__all__` as unsorted and reordered it on `--fix`, failing pre-commit | Keep `__all__` alphabetically sorted, case-sensitive (lowercase before UPPERCASE); auto-fix with `ruff check --select=I --fix` |
| Closing a multi-line docstring with `"""` on the same line as content | `add_dry_run_arg`/`_build_parser` docstrings ended with text and `"""` on one line | The ruff formatter rejected the docstring shape as misaligned | Put the closing `"""` of a multi-line docstring on its own line — the formatter is strict about docstring shape |
| Accessing the parser in tests via `_parse_args(["--help"])` | Called `_parse_args` and caught `SystemExit` | `parse_args()` calls `sys.exit(2)` / exits on `--help`; unsafe to call in-process | Extract `_build_parser()` and inspect the returned parser object — no side effects |
| Testing only one CLI module | Wrote a test covering just `planner` | Missed drift in 6 other modules | Use `@pytest.mark.parametrize` from the start to cover the whole CLI surface |
| Using a per-module config dict for help text | Moved help text into a config file keyed by module | Config drifted from code; modules could forget to register; no type checking | Keep the constant + helper in Python code with type hints; no separate config file |
| Using installed script names in the smoke test | `subprocess.run(["hephaestus-changelog", "--help"])` | Requires pip-installed entry points; fails in pixi/dev environments | Use `sys.executable -m module.path` to exercise the same `main()` via the `__main__` block |
| Relying on pytest `pythonpath` for the subprocess test | Release workflow ran `pixi run pytest` with no editable-install; package excluded from the pixi lockfile | 15 `ModuleNotFoundError` failures — the spawned `python --help` did not inherit `pythonpath`; in-process import test passed, masking it | Subprocess smoke tests need the package installed in the env they spawn into; add the editable-install step to EVERY CI workflow; do not weaken the test |
| Defaulting `--fail-on-regression` to enabled | Reintroduced a restored analysis script with strict exit behavior even when callers omitted the option | The flag name promises opt-in strictness, but absence still failed CI and local callers | Use `action="store_true"` with `default=False`; only explicit presence returns 1 for detected regressions |
| Printing an unconditional no-regression `PASS` line | Used the same success message whenever the process returned 0 | Advisory mode returned 0 despite real critical findings, so the message contradicted the report | Use distinct `FAIL`, `WARN ... (failure disabled)`, and genuinely clean `PASS` summaries |
| Testing only parser defaults | Inspected the `argparse` action and namespace without launching the script | Did not prove the observable exit status, stderr wording, import path, or `__main__` wiring | Run the real script through `subprocess.run` with deterministic temporary input files |
| Copying benchmark comparison logic into the wrapper | Reimplemented threshold and report calculations in `scripts/` while restoring the command | Created two algorithms that could drift and expanded the review surface | Keep standalone scripts as narrow adapters over existing library functions |

## Results & Parameters

### Non-blocking dry-run

- Default `dry_run=False` preserves backward compatibility for all existing callers
- `argparse` hyphen-to-underscore: `--dry-run` → `args.dry_run` (built-in)
- 7 new tests in a `TestDryRun` class (4 `check_files` combinations, 2 `main()` integration,
  1 multi-file "all reported" case); no `.pre-commit-config.yaml` changes needed
- `--dry-run` help string exceeds the line limit → use `# noqa: E501` inline

### DRY help-text standardization

- `DRY_RUN_HELP_CAVEAT`: lowercase start (auto-capitalized standalone), no trailing period
  (auto-added), token-cost caveat explicit, fits one line in `--help`
- `add_dry_run_arg(parser, *, prefix=None)`: keyword-only `prefix`, auto-punctuation,
  `action="store_true"`, returns `None` (in-place per argparse convention)
- 7 CLI modules updated: planner, plan_reviewer, pr_reviewer, address_review,
  implementer_cli, ci_driver, loop_runner
- 11-test suite (`tests/unit/cli/test_dry_run_help.py`): parametrized help-text consistency,
  `store_true` check, `--dry-run` in `option_strings`, helper unit tests (with/without
  prefix, prefix-already-has-period, period-appended), `_build_parser()` returns a parser,
  `_parse_args` respects/defaults `dry_run`, all modules export `_build_parser`
- Expected `--help` line:

  ```text
  --dry-run   Do not create PR, file follow-up issues, or invoke /learn. Useful for testing without incurring token costs.
  ```

### Entry-point smoke tests

- Test file: `tests/integration/test_cli_entry_points.py`; 8 tests (4 import + 4 subprocess);
  ~0.39s total
- Key assertion: `"usage:"` in stdout confirms argparse ran (not a silent exit 0)
- Add a new entry point: append a tuple to `ENTRY_POINTS` and matching `ids=` strings
- Pre-flight for a new entry point: module has `def main()`, has `__main__` block, uses
  argparse/click with `--help`, no module-level side effects at import
- CI parity: every workflow running the subprocess test must `pixi run dev-install`
  (`pip install -e . --no-deps`) before pytest

### Opt-in failure gate for standalone analysis scripts

- Parser contract: `action="store_true"`, `default=False`, and help text explicitly says
  the default is report-only
- Critical finding without the flag: report remains complete, stderr says failure is disabled,
  exit status `0`
- Same critical finding with `--fail-on-regression`: report remains complete, stderr uses a
  `FAIL` summary, exit status `1`
- No critical finding in either mode: stderr truthfully says no critical regressions, exit `0`
- Test boundary: execute `sys.executable scripts/<name>.py ...`; do not substitute parser
  introspection for the command's observable behavior
- Architecture boundary: reuse existing library functions; no duplicate algorithm, packaged
  console registration, dependency, ADR, migration, or public API is implied
- Verification: `unverified` for this extension; the commands and expected outputs come from a
  reviewed ProjectHephaestus issue plan, not an executed implementation or passing CI run

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectScylla | PR #1463, issue #1442 | Non-blocking `--dry-run` added to `scripts/validate_config_schemas.py`; check placed after the loop; 7 `TestDryRun` tests; `# noqa: E501` for help string. Follow-up to precommit-schema-validation (#1382/#1439) |
| ProjectHephaestus | Issue #772, PR #974 | `--dry-run` help standardization: `DRY_RUN_HELP_CAVEAT` + `add_dry_run_arg(parser, *, prefix=None)` in `hephaestus/cli/utils.py`; `_build_parser()` extracted from `_parse_args()` in 7 CLI modules; 11-test parametrized suite; ruff/mypy/pre-commit all pass (verified-ci) |
| ProjectHephaestus | Issue #52, PR #95 | 4 CLI entry points smoke-tested (changelog, merge-prs, system-info, download-dataset); 8 tests (v1.0.0 pattern, verified-local) |
| ProjectHephaestus | PR #612 | Editable-install / workflow-parity fix: release.yml ran pytest without `pixi run dev-install`, causing 15 `ModuleNotFoundError` failures in subprocess `--help` tests (verified-ci) |
| ProjectHephaestus | Issue #2569 implementation plan | Proposed restoration of `scripts/compare_benchmarks.py` as a thin adapter over `hephaestus.benchmarks.compare`, with report-only default, explicit `--fail-on-regression`, subprocess behavior tests using 100 ms versus 130 ms fixtures, help-contract coverage, and script-catalog documentation. Not executed in this session; CI validation pending. |
