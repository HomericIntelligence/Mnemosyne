---
name: tooling-cli-batch-terminal-outcome-contracts
description: "Design honest batch CLI outcomes. Use when: (1) a command returns success after blocked, failed, unmapped, or unprocessed work, (2) malformed mapping/config inputs or invalid JSON Schema definitions escape as exceptions, (3) human and JSON diagnostics diverge, (4) requested, validated, failed, and diagnostic counts are conflated, or (5) dry-run and interruption need explicit semantics."
category: tooling
date: 2026-08-06
version: "1.2.0"
user-invocable: false
verification: unverified
history: tooling-cli-batch-terminal-outcome-contracts.history
tags:
  - python
  - cli
  - batch-processing
  - exit-codes
  - json
  - keyboard-interrupt
  - terminal-outcomes
  - dry-run
  - github
  - schema-validation
  - unmapped-inputs
  - outcome-accounting
  - diagnostics
  - draft7
  - schema-map
  - structured-diagnostics
---

# Batch CLI Terminal Outcome Contracts

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-06 (v1.2.0; originally 2026-08-01) |
| **Objective** | Give every requested or discovered batch item an explicit terminal outcome, distinguish work counters from diagnostic counts, derive the command exit code from those outcomes, and emit one stable structured summary on every path |
| **Outcome** | Proposed design for manual batch drivers and file validators, including per-item failure isolation, atomic map validation, invalid Draft 7 definition diagnostics, human/JSON error parity, unmapped-input policy, interruption handling, domain-specific dry-run semantics, complete aggregation, compatibility aliases, and single-line untrusted details |
| **Verification** | unverified — derived from reviewed ProjectHephaestus implementation plans for `hephaestus-merge-prs` and schema validation; the implementations, focused tests, and CI validation are pending |
| **History** | [changelog](./tooling-cli-batch-terminal-outcome-contracts.history) |

## When to Use

- A CLI discovers multiple pull requests, jobs, files, or other items and currently processes them with fire-and-forget returns.
- A file validator warns and skips an explicitly requested file when no schema or policy mapping matches it.
- A summary reports requested files as checked files, or treats multiple diagnostics from one file as multiple failed files.
- A decoded schema or policy map is destructured before its root, entry arity, field types, regexes, or paths are validated.
- A JSON Schema validator accepts an invalid schema definition and later leaks `SchemaError`, `UnknownType`, or another raw exception.
- Human mode prints useful failures but JSON mode emits only a generic status, or JSON stdout is contaminated by verbose/pass output.
- A per-item exception aborts the whole batch, or an exception is logged but the command still exits `0`.
- Some discovered items can be blocked or accidentally left unprocessed, and those conditions must make the command fail.
- A dry-run must distinguish operation suppression (an intentional skip) from validation preview (preserve observed failures but suppress the process failure code).
- `KeyboardInterrupt` must be distinguished from ordinary failures, stop later work, and return conventional exit code `130`.
- Machine consumers require the same JSON fields for success, partial failure, setup failure, and interruption before discovery.
- Provider text or exception messages may contain newlines or control characters that would split log records.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

### Quick Reference

```python
from dataclasses import dataclass
from enum import Enum


class _ItemStatus(str, Enum):
    SUCCEEDED = "succeeded"
    QUEUED = "queued"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


def _escape_detail(value: object) -> str:
    return ascii(str(value))[1:-1]


@dataclass(frozen=True)
class _ItemOutcome:
    item_id: int | None
    status: _ItemStatus
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "detail", _escape_detail(self.detail))


def _exit_code(outcomes: list[_ItemOutcome], requested: int) -> int:
    statuses = {outcome.status for outcome in outcomes}
    if _ItemStatus.INTERRUPTED in statuses:
        return 130
    if len(outcomes) != requested:
        return 1
    if statuses & {_ItemStatus.BLOCKED, _ItemStatus.FAILED}:
        return 1
    return 0
```

For a schema-driven validator, validate the control inputs before validating instances and
return diagnostics to the renderer:

```python
def load_mapping(path: Path) -> list[tuple[re.Pattern[str], Path]]:
    data: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("schema map root must be a list")

    mapping: list[tuple[re.Pattern[str], Path]] = []
    errors: list[str] = []
    for index, entry in enumerate(data):
        if not isinstance(entry, list) or len(entry) != 2:
            errors.append(f"entry {index}: expected a two-item list")
            continue
        # Validate both fields independently; append only fully valid entries.
        # Compile regexes here and reject empty or NUL-containing paths.

    if errors:
        raise ValueError("invalid schema map:\n" + "\n".join(f"- {e}" for e in errors))
    return mapping


def validate_instance(path: Path, schema: object) -> list[str]:
    validator_type = jsonschema.Draft7Validator
    try:
        validator_type.check_schema(schema)
    except jsonschema.exceptions.SchemaError as exc:
        location = ".".join(str(part) for part in exc.absolute_path) or "<root>"
        return [f"Invalid JSON Schema at [{location}]: {exc.message}"]
    return [
        f"[{'.'.join(map(str, error.absolute_path)) or '<root>'}] {error.message}"
        for error in sorted(
            validator_type(schema).iter_errors(load_yaml(path)),
            key=lambda item: list(item.path),
        )
    ]


def check_files(...) -> tuple[int, list[str]]:
    """Return one diagnostic list; do not print failures here."""
    ...
```

For a file validator that aggregates counts instead of retaining item records:

```python
@dataclass(frozen=True)
class CheckResult:
    exit_code: int
    error_count: int
    requested: int
    validated: int
    skipped: int
    passed: int
    failed: int
```

```text
requested = passed + failed + skipped
validated = files for which the validator actually ran
error_count = emitted diagnostics, not failed files
files_checked = validated  # compatibility alias, when required
```

Stable JSON envelope on every path:

```json
{
  "status": "error",
  "exit_code": 1,
  "message": "batch complete",
  "results": [],
  "totals": {
    "succeeded": 0,
    "queued": 0,
    "skipped": 0,
    "blocked": 0,
    "failed": 0,
    "interrupted": 0
  },
  "requested": 0,
  "processed": 0
}
```

### Detailed Steps

1. **Keep outcome tracking private unless consumers require a public API.** Define a private string enum and frozen dataclass in the command module. The result object should carry the item identifier, one terminal status, and normalized detail text.

2. **Classify provider responses at the provider boundary.** Convert dict responses and legacy response objects into outcomes immediately. For a merge driver, useful statuses are `merged`, `queued`, `skipped`, `blocked`, `failed`, and `interrupted`; do not force merge-queue enrollment into the same label as a synchronous merge.

3. **Return an outcome on every ordinary item path.** Missing required metadata is `failed`; unmet eligibility is `blocked`; an intentional operation suppression may be `skipped`; a confirmed operation is `succeeded` or its domain-specific equivalent. Let unexpected operational exceptions reach the batch boundary. For explicit file validation, a missing schema or policy mapping is `failed` by default and becomes `skipped` only behind a narrow flag such as `--allow-unmapped`.

4. **Preserve side-effect order before refactoring return values.** When an option such as `--push-all` requires a side effect even for blocked items, retain the sequence: validate identity, evaluate eligibility, perform the unconditional option-owned side effect, return `blocked` if needed, otherwise avoid duplicate side effects and perform the terminal operation.

5. **Catch failures at the per-item batch boundary.** Catch `Exception`, append `failed` with the exception type and text, and continue to later items. Catch `KeyboardInterrupt` separately, append `interrupted` for the current discovered item, stop the loop, and do not process later items.

6. **Detect incomplete batches independently of named failures.** Exit `1` when `processed != requested`, even if no recorded outcome is explicitly `blocked` or `failed`. This closes silent-success paths caused by premature loop termination or future control-flow regressions.

7. **Use deterministic exit precedence.** Return `130` if setup or item processing was interrupted. Otherwise return `1` for blocked, failed, or incomplete work. Return `0` only when every requested item is in an allowed terminal set such as merged, queued, or intentionally skipped. A validation dry-run may suppress the final failure code, but it must preserve observed `failed`, `skipped`, and diagnostic counts; dry-run changes enforcement, not facts.

8. **Build totals from the complete enum.** Initialize every status to zero before counting. Stable keys matter: a status with no occurrences must still appear in machine-readable output, including failures before discovery. When the aggregate exposes multiple axes, define each by its triggering event: `requested` at input receipt, `validated` only when the validator runs, terminal file outcomes exactly once, and diagnostic counts by emitted diagnostics.

9. **Emit one result record per item and one aggregate record.** Normalize details once with `ascii(str(value))[1:-1]` before both logging and serialization. This escapes newlines and control characters so untrusted provider or exception text cannot create extra physical log records.

10. **Route every JSON path through one summary emitter.** Always include `status`, `exit_code`, `message`, `results`, `totals`, `requested`, and `processed`. Setup/access/listing failures use an empty complete envelope. A pre-discovery interruption has no item to own an `interrupted` result, so represent it with exit code `130`, an interruption message, empty results, zero totals, and `requested=processed=0`. Preserve legacy names additively: a file validator may keep `files_checked`, but it must alias `validated` rather than the number requested.

11. **Test behavior and sequencing, not only helpers.** Cover all success, partial failure with continuation, domain-correct dry-run behavior, blocked items, missing metadata or mappings, provider exceptions, queue enrollment, item interruption, setup/listing interruption, incomplete-batch detection, exact JSON dictionaries, zero-valued totals, and multiline detail escaping. For validators, add mixed mapped/unmapped inputs, schema-load failure, one invalid file with multiple diagnostics, explicit permissive skipping, zero-input output, and a proof that dry-run changes only `exit_code`. Record side-effect calls in a list to assert exact order and exactly-once behavior.

12. **Document the public command contract.** State the meanings of exit codes `0`, `1`, and `130`, plus the invariant JSON keys. Users and wrappers should not need to infer semantics from implementation details.

13. **Choose item records or a typed aggregate deliberately.** Retain item records when callers need identifiers, details, or heterogeneous statuses. For a local helper that only needs summary counts, return a frozen dataclass with named fields. Do not grow a positional `(exit_code, diagnostic_count, ...)` tuple as the contract expands.

14. **Assert accounting invariants directly.** Every requested occurrence must reach exactly one terminal outcome, so assert `requested == passed + failed + skipped`. Do not assert `validated == passed + failed`: failures that occur before validation, such as an unmapped input or unreadable schema, are failed but not validated.

15. **Validate decoded maps before destructuring.** Treat JSON decoding as only the first input boundary. Require the expected root container, entry container and arity, string field types, compilable regexes, and non-empty/NUL-free paths. Accumulate index-qualified entry errors and reject the entire map atomically; never return a partially usable mapping.

16. **Validate schema definitions before instances.** Keep optional validator imports lazy, then call the selected validator class's `check_schema()` before loading or validating an instance. Translate `SchemaError` at that boundary into the same diagnostic-list contract as instance errors, including a stable absolute path such as `<root>`.

17. **Collect once and render twice.** A checker should return diagnostics instead of printing failures. Human mode prefixes and writes the returned strings to stderr. JSON mode passes the same strings to the structured emitter, suppresses verbose success output, and writes exactly one parseable document to stdout with an empty stderr.

18. **Catch expected text-input failures completely.** Schema and map reads should translate `OSError`, `UnicodeDecodeError`, and `JSONDecodeError`. A UTF-8 decoding failure is an input diagnostic, not an internal traceback.

19. **Test the control plane as thoroughly as instances.** Parameterize wrong roots, entry shapes, field types, invalid regexes, empty/NUL paths, and invalid schema definitions. Assert aggregated entry indexes, multiple independent instance errors, nonzero human and JSON exits, parsed JSON diagnostic content, channel isolation, and absence of `Traceback`.

## Verified Workflow

_Not applicable._ This skill was captured from a planning session and is
`unverified`: no implementation was applied, no targeted tests were run, and CI
was not confirmed. The actionable methodology is under **Proposed Workflow**
above and must remain hypothesis-level until those checks pass. This placeholder
exists because `scripts/validate_plugins.py` requires the literal
`## Verified Workflow` heading; it makes no verification claim.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ---------------- | ------------- | -------------- |
| Fire-and-forget item processing | Per-item helpers returned `None` after logging, and the command returned success after the loop | Logs are not a machine-checkable terminal ledger; blocked and failed work can collapse into exit `0` | Return typed outcomes and derive status from the complete batch ledger |
| Catch exceptions around the whole batch | One ordinary provider or push failure aborted later items | Independent items never received outcomes, so the summary was incomplete | Catch ordinary `Exception` at the per-item boundary and continue |
| Treat `KeyboardInterrupt` like an ordinary exception | Interruption could continue later work or become generic exit `1` | Operator cancellation has distinct stop and exit semantics | Catch it separately, record the current item when discovered, stop, and return `130` |
| Emit special-case JSON for early failures | Setup and listing errors returned only `status`, `exit_code`, and `message` | Consumers needed path-dependent parsing and could not rely on aggregate fields | Use one additive summary emitter and an empty complete envelope before discovery |
| Count only observed statuses | Totals omitted keys when a status count was zero | The schema changed from run to run | Initialize totals from the enum so all keys are always present |
| Log raw provider or exception details | Newlines and control characters created multiple physical log lines | Untrusted text could forge or corrupt summary records | Normalize once with `ascii(str(value))[1:-1]` before logs and JSON |
| Infer completeness only from failure statuses | A prematurely stopped loop could contain no explicit failure yet process fewer items than requested | Missing outcomes remained invisible | Make `processed != requested` an independent exit-`1` condition |
| Warn and skip every unmapped explicit file | Absence of a schema or policy mapping was treated as a warning and successful continuation | A typo or stale mapping could make an operator believe a requested file was validated | Fail closed for explicit requests; preserve skipping only behind a narrow opt-in flag |
| Report requested files as `files_checked` | JSON populated the compatibility field from the input-list length | Unmapped inputs and schema-load failures never reached validation, so the field overstated actual checks | Define `files_checked` as an alias for `validated` |
| Use diagnostic count as failed-file count | Every validation diagnostic was counted like a separate failed file | One invalid file can emit multiple diagnostics, so failure cardinality was inflated | Keep diagnostic volume and terminal file outcomes in separate fields |
| Rewrite failures during validation dry-run | Dry-run converted observed failures into passes or skips | The preview no longer described what enforcement would find | Preserve classifications and suppress only the final process failure code |
| Destructure decoded map entries immediately | A non-list root, wrong-length entry, non-string field, bad regex, or NUL path raised `TypeError`, `ValueError`, or `re.error` outside the CLI contract | JSON syntax validity does not imply application-level structure validity | Validate every structural layer, aggregate index-qualified errors, and reject the map atomically |
| Instantiate a Draft 7 validator without checking its schema | An invalid schema definition survived loading and later raised a raw validator exception | Instance validation assumes a valid control schema | Call `Draft7Validator.check_schema()` first and translate `SchemaError` into a normal diagnostic |
| Print failures inside the batch checker | Human mode had details, while JSON mode either lost them or mixed prose with the JSON document | Two rendering paths did not share one source of truth | Return diagnostic strings and let `main()` choose stderr or the JSON envelope |
| Catch file and JSON errors but omit text decoding | Invalid UTF-8 escaped the expected input-error boundary | `Path.read_text(encoding="utf-8")` can fail before JSON decoding begins | Include `UnicodeDecodeError` with other expected schema-file input failures |

## Results & Parameters

Recommended outcome semantics for a pull-request merge driver:

| Status | Meaning | Success for command exit? |
| ------ | ------- | ------------------------- |
| `merged` | Provider confirms synchronous merge | Yes |
| `queued` | Provider confirms merge-queue enrollment | Yes |
| `skipped` | Dry-run intentionally suppresses an otherwise eligible merge | Yes |
| `blocked` | Checks or legacy status do not permit merging | No |
| `failed` | Metadata, push, provider API, or ordinary per-item operation failed | No |
| `interrupted` | Operator interrupted current batch item | No; exit `130` |

Exit-code truth table:

| Condition | Exit code |
| --------- | --------- |
| Setup or batch interruption | `130` |
| Any `blocked` or `failed` result | `1` |
| `processed != requested` without interruption | `1` |
| Every requested item is merged, queued, or intentionally skipped | `0` |

Required structured fields:

```text
status, exit_code, message, results, totals, requested, processed
```

For a pre-discovery failure or interruption:

```text
results=[]
requested=0
processed=0
totals=<every declared status mapped to 0>
```

Schema-validation specialization:

| Event | `validated` | Terminal outcome | Diagnostic count |
| ------- | ----------- | ---------------- | ---------------- |
| Matching schema loads; validation passes | +1 | `passed` +1 | Unchanged |
| Matching schema loads; validation returns N diagnostics | +1 | `failed` +1 | +N |
| No mapping, default policy | Unchanged | `failed` +1 | +1 |
| No mapping, `--allow-unmapped` | Unchanged | `skipped` +1 | Unchanged |
| Matching schema cannot be loaded | Unchanged | `failed` +1 | +1 |

Schema control-input contract:

| Input failure | Diagnostic behavior | Partial work allowed? |
| ------- | ------------------- | --------------------- |
| Map root is not a list | `schema map root must be a list` | No |
| Map entry has wrong shape or field types | Aggregate every `entry N` explanation | No |
| Regex cannot compile | Include index, pattern representation, and `re.error` text | No |
| Schema path is empty or contains NUL | Include an index-qualified stable explanation | No |
| Schema file is unreadable, invalid UTF-8, or invalid JSON | Return `Could not load schema ...` | Other files may continue if the command's batch contract permits it |
| Draft 7 schema definition is invalid | Return `Invalid JSON Schema at [path]: ...` | The affected instance is not validated |

Human/JSON rendering parity for a validation failure:

```python
exit_code, errors = check_files(..., dry_run=args.dry_run)
if args.json:
    emit_json_status(
        exit_code,
        message="schema validation failed" if exit_code else None,
        errors=errors,
        error_count=len(errors),
        files_checked=<preserved public meaning>,
        dry_run=args.dry_run,
    )
else:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
```

Preserve the command's established `files_checked` meaning during a diagnostic-hardening
change. For a new contract, prefer `files_checked == validated`; migrate an existing public
counter only as a deliberate, separately tested compatibility change.

Required invariants:

```python
assert result.requested == result.passed + result.failed + result.skipped
assert result.validated <= result.requested
assert json_output["files_checked"] == json_output["validated"]

dry_run_result = check_files(files, dry_run=True)
normal_result = check_files(files, dry_run=False)
assert dry_run_result.failed == normal_result.failed
assert dry_run_result.skipped == normal_result.skipped
assert dry_run_result.error_count == normal_result.error_count
```

For one valid mapped file and one unmapped file under the default fail-closed policy, the human summary should be:

```text
Summary: requested=2, validated=1, skipped=0, passed=1, failed=1
```

The JSON payload should carry the same values, set `error_count` and `files_checked` to `1`, and preserve `error_count` as the diagnostic-volume compatibility field. A zero-input path should emit every counter with value `0` rather than changing the output shape.

Suggested focused verification:

```bash
pytest tests/unit/path/to/test_batch_cli.py -k "outcome or incomplete or interrupt or json_summary or multiline" -v
ruff check path/to/batch_cli.py tests/unit/path/to/test_batch_cli.py
ruff format --check path/to/batch_cli.py tests/unit/path/to/test_batch_cli.py
mypy path/to/batch_cli.py tests/unit/path/to/test_batch_cli.py
```

For schema-boundary hardening, the focused matrix should also include:

```bash
pytest tests/unit/path/to/test_schema.py \
  -k "schema_map or invalid_schema or multiple_validation_errors" -v
```

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Reviewed implementation plan for hardening `hephaestus-merge-prs` | Unverified until implementation tests and CI pass |
| ProjectHephaestus | Reviewed schema-validation plan for failing unmapped explicit files and separating five file counters | Unverified until implementation tests, lint, type checking, and CI pass |
| ProjectHephaestus | Reviewed plan for malformed schema-map inputs, invalid Draft 7 definitions, and equivalent human/JSON diagnostics | Unverified until focused tests, Ruff, mypy, and CI pass |

## References

- [Fail-closed validators](cli-validator-fail-closed-tool-policy-separation.md) — separates incomplete inspection from policy violations when public helper compatibility is more important than an aggregate result object.
- [Explicit config paths](config-explicit-path-fail-closed.md) — adjacent explicit-path versus discovery fallback semantics.
- [CLI dry-run patterns](python-cli-dry-run-and-entrypoint-patterns.md) — adjacent guidance for suppressing side effects and process failure without hiding observed state.
