---
name: cli-input-file-prevalidation
description: "Pre-validate file-path CLI arguments at parse time so a missing or wrong-type input file produces a controlled parser.error diagnostic instead of an uncaught FileNotFoundError/IsADirectoryError traceback. Use when: (1) an argparse CLI reads a --file argument with a bare read_text/open and crashes with a traceback on a nonexistent path, (2) adding a required or optional file-path flag to a CLI entrypoint, (3) an audit flags 'uncaught traceback for nonexistent input file' on a command-line tool."
category: tooling
date: 2026-07-17
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - argparse
  - cli
  - input-validation
  - file-path
  - parser-error
  - traceback
  - diagnostics
  - fail-closed
---

# CLI Input-File Pre-Validation - Traceback to Diagnostic

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-17 |
| **Objective** | Convert uncaught `FileNotFoundError`/`IsADirectoryError` tracebacks from file-path CLI arguments into controlled parse-time diagnostics (`parser.error`, exit code 2, one line on stderr). |
| **Outcome** | Planned for ProjectHephaestus issue #2171 (`hephaestus-agent-stage`): `validate_input_files(parser, args)` gate in `main()` mirrors the existing `validate_agent_flags` pattern from issue #773. Plan reviewed; marked unverified until the implementation PR merges green. |
| **Verification** | unverified - grounded in direct code inspection and a reviewed implementation plan, not yet a merged CI-green PR |

## When to Use

- An argparse-based CLI accepts a file path (`--prompt-file`, `--config`, `--input`) and reads it
  with a bare `Path.read_text()` or `open()`, so a typo'd path surfaces as a full Python traceback.
- You are adding a new required or optional file-path flag to a CLI entrypoint and want
  fail-closed behavior with a clear operator-facing message.
- An audit or issue reports "uncaught traceback for nonexistent input file" against a
  command-line tool (e.g. ProjectHephaestus #2171, Section 14 MINOR).
- A directory is passed where a file is expected and the tool dies with `IsADirectoryError`.

## Verified Workflow

### Quick Reference

Add a parse-time gate in `main()`, next to any existing flag-compatibility validation:

```python
def validate_input_files(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Reject missing prompt/skill files with a CLI diagnostic instead of a traceback."""
    prompt_file = Path(args.prompt_file).expanduser().resolve()
    if not prompt_file.is_file():
        parser.error(f"--prompt-file does not exist or is not a file: {prompt_file}")
    if args.skill_file:
        skill_file = Path(args.skill_file).expanduser().resolve()
        if not skill_file.is_file():
            parser.error(f"--skill-file does not exist or is not a file: {skill_file}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_agent_flags(parser, args)
    validate_input_files(parser, args)
    ...
```

### Detailed Steps

1. Find every file-path argument the CLI reads eagerly (`grep -n "read_text\|open(" <module>`).
   Include optional flags: an optional `--skill-file` read with the same bare `read_text` has the
   identical traceback failure mode - fixing only the required flag leaves half the bug.
2. Resolve paths exactly the way the runtime code does (`Path(...).expanduser().resolve()`) so the
   diagnostic prints the same absolute path the read would have used.
3. Check `.is_file()`, not `.exists()`: `.is_file()` also rejects a directory passed where a file
   is expected, converting `IsADirectoryError` into the same one-line diagnostic.
4. Report via `parser.error(f"--flag does not exist or is not a file: {path}")`. This reuses
   argparse's canonical diagnostic shape (usage line + `error: ...` on stderr, `SystemExit(2)`) -
   no new error-reporting convention, no try/except wrapping needed.
5. Gate only the CLI entrypoint (`main()`), not the programmatic function it calls: library
   callers keep exception semantics; operators get diagnostics.
6. Test with the standard argparse-rejection pattern - one test per flag plus the directory edge:

```python
def test_main_rejects_missing_prompt_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = ["--prompt-file", str(tmp_path / "missing.md"), ...]
    with pytest.raises(SystemExit) as excinfo:
        module.main(argv)
    assert excinfo.value.code == 2
    assert "--prompt-file does not exist" in capsys.readouterr().err
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Considered try/except around the read call | Wrap `read_text` in `try/except FileNotFoundError` inside the runner function | Changes exception semantics for programmatic callers and duplicates error plumbing; the runner returns int exit codes, so it would need its own printing convention | Gate at parse time in `main()` with `parser.error`; keep the library function's contract untouched |
| Considered `.exists()` for the check | `path.exists()` before reading | A directory passes `.exists()` and still crashes later with `IsADirectoryError` | Use `.is_file()` so both missing-path and directory-as-file collapse into one diagnostic |
| Considered validating only the flag named in the issue | Fix `--prompt-file` alone | The optional `--skill-file` is read with the same bare `read_text` two lines later - identical traceback remains reachable | Sweep the module for every eagerly-read path argument before scoping the fix |

## Results & Parameters

### Configuration

Reference implementation target (ProjectHephaestus issue #2171):

```yaml
module: hephaestus/automation/agent_stage.py
crash_site: read_prompt() bare read_text (line 59), called from run_agent (line 198)
gate: validate_input_files(parser, args) called in main() after validate_agent_flags
sibling_pattern: validate_agent_flags (issue #773) - same parser.error shape
tests: tests/unit/automation/test_agent_stage.py (SystemExit(2) + capsys.err)
```

### Expected Output

- Before: `Traceback (most recent call last): ... FileNotFoundError: [Errno 2] No such file or directory: '/bad/path.md'`
- After: `usage: ...` then `hephaestus-agent-stage: error: --prompt-file does not exist or is not a file: /bad/path.md`, exit code 2, no traceback.
- Valid paths pass the gate unchanged; existing happy-path tests double as regression coverage.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Issue #2171 implementation plan (reviewed); pattern lifted from merged issue #773 `validate_agent_flags` | Amend to verified-ci once the #2171 PR merges green |

## References

- [cli-flag-validation-prevent-silent-noop.md](cli-flag-validation-prevent-silent-noop.md) - same parse-time `parser.error` gate, for backend-incompatible flag values (silent no-op intent)
- [config-explicit-path-fail-closed.md](config-explicit-path-fail-closed.md) - fail-closed cousin for layered config resolvers (explicit path missing vs auto-discovery)
- [Python argparse error handling](https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.error)
